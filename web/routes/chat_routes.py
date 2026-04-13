"""
聊天会话路由 — 管理问诊会话（创建/发送/结束）
"""
import os
import json
import time
import logging
import re
from pathlib import Path
from flask import Blueprint, request, jsonify

from agents.patient.patient import create_patient

# 项目根目录（web/routes/../../ = project_root）
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 问诊记录目录
RECORDS_DIR = PROJECT_ROOT / "web" / "data" / "records"

logger = logging.getLogger(__name__)

# 会话 TTL：30 分钟无活动自动过期
SESSION_TTL_SECONDS = 1800

# In-memory: session_id -> { patient, case_id, record_id, messages, last_active }
chat_sessions = {}


def _cleanup_expired_sessions():
    """清理过期的会话"""
    now = time.time()
    expired = [sid for sid, s in chat_sessions.items() if now - s["last_active"] > SESSION_TTL_SECONDS]
    for sid in expired:
        del chat_sessions[sid]
        logger.info(f"会话 {sid} 已过期，自动清理")


def _generate_record_id(case_id: str) -> str:
    """为同一病例生成递增的 record_id（如 1009904_1, 1009904_2）"""
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    # 统计已有以 case_id 开头的记录文件数
    pattern = re.escape(case_id) + r"(?:_\d+)?\.json$"
    existing = 0
    for f in RECORDS_DIR.glob("*.json"):
        if re.match(pattern, f.name):
            existing += 1
    return f"{case_id}_{existing + 1}"


def register_chat_routes(case_service):
    """注册聊天路由"""
    chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

    @chat_bp.route("/start", methods=["POST"])
    def api_chat_start():
        """开始一段新的问诊会话"""
        _cleanup_expired_sessions()

        data = request.get_json() or {}
        case_id = data.get("case_id")
        if not case_id:
            return jsonify({"error": "case_id required"}), 400

        case_data = case_service.get_case_for_interview(case_id)
        if not case_data:
            return jsonify({"error": "Case not found"}), 404

        try:
            # 查找 skill 文件
            patient_skill_file = None
            skill_path = PROJECT_ROOT / "data" / f"patient_{case_id}" / "skill.md"
            if skill_path.exists():
                patient_skill_file = str(skill_path)
                logger.info(f"找到患者 Skill 文件: {skill_path}")

            patient = create_patient(
                basic_info=case_data.get("basicInfomation", ""),
                chief_complaint=case_data.get("chiefComplaint", []),
                mental_status=case_data.get("mentalStatus", []),
                skill_file=patient_skill_file,
            )

            session_id = os.urandom(16).hex()
            record_id = _generate_record_id(case_id)
            chat_sessions[session_id] = {
                "patient": patient,
                "case_id": case_id,
                "record_id": record_id,
                "messages": [],
                "last_active": time.time(),
            }

            opening_response = patient.chat("请根据患者的主诉，主动自我介绍并描述主要不适。请用中文回复，回复格式为JSON：{\"utterance\": \"患者的话\", \"presentation\": \"外显表现\"}")
            opening = opening_response
            try:
                parsed = json.loads(opening_response)
                opening = parsed.get("utterance", opening_response)
            except json.JSONDecodeError:
                opening = opening_response

            logger.info(f"会话 {session_id} 已创建，病例 {case_id}，记录 {record_id}")
            return jsonify({
                "session_id": session_id,
                "case_id": case_id,
                "record_id": record_id,
                "opening": opening,
            })
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return jsonify({"error": str(e)}), 500

    @chat_bp.route("/send", methods=["POST"])
    def api_chat_send():
        """发送医生消息，获取患者回复"""
        _cleanup_expired_sessions()

        data = request.get_json() or {}
        session_id = data.get("session_id")
        doctor_message = data.get("message", "")

        if not session_id or not doctor_message:
            return jsonify({"error": "session_id and message required"}), 400

        chat_session = chat_sessions.get(session_id)
        if not chat_session:
            return jsonify({"error": "Session not found"}), 404

        chat_session["last_active"] = time.time()
        patient = chat_session["patient"]
        try:
            response = patient.chat(doctor_message)

            utterance = response
            presentation = ""
            try:
                parsed = json.loads(response)
                utterance = parsed.get("utterance", response)
                presentation = parsed.get("presentation", "")
            except json.JSONDecodeError:
                pass

            chat_session["messages"].append({
                "role": "doctor",
                "content": doctor_message,
            })
            chat_session["messages"].append({
                "role": "patient",
                "content": utterance,
                "presentation": presentation,
            })

            return jsonify({
                "response": utterance,
                "presentation": presentation,
                "turn": len(chat_session["messages"]) // 2,
            })
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return jsonify({"error": str(e)}), 500

    @chat_bp.route("/end", methods=["POST"])
    def api_chat_end():
        """结束问诊会话"""
        data = request.get_json() or {}
        session_id = data.get("session_id")
        if session_id and session_id in chat_sessions:
            del chat_sessions[session_id]
            logger.info(f"会话 {session_id} 已结束")
        return jsonify({"status": "ok"})

    @chat_bp.route("/sessions", methods=["GET"])
    def api_chat_sessions_list():
        """查看当前活跃会话（调试用）"""
        now = time.time()
        sessions = []
        for sid, s in chat_sessions.items():
            sessions.append({
                "session_id": sid,
                "case_id": s["case_id"],
                "record_id": s.get("record_id", ""),
                "turns": len(s["messages"]) // 2,
                "last_active_ago": round(now - s["last_active"]),
            })
        return jsonify({"sessions": sessions, "total": len(sessions)})

    return chat_bp
