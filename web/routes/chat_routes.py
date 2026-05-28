"""
Chat session routes for Phase 1 interview.
"""
import json
import logging
import os
import random
import re
import string
import time
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request

from mental_hospital.agents.patient import create_patient
from mental_hospital.data.loader import get_patient_dirs
from web.config import PROJECT_ROOT
from web.service_layer.session_store import SQLiteChatSessionStore

logger = logging.getLogger(__name__)

SESSION_TTL_SECONDS = 1800
SESSION_STORE = SQLiteChatSessionStore(PROJECT_ROOT / "run" / "mentalhospital_sessions.sqlite3")


def _parse_patient_response(response: str):
    utterance = response
    presentation = ""
    grounding = {}

    candidates = [response]
    json_match = re.search(r"\{[\s\S]*\}", response or "")
    if json_match:
        candidates.insert(0, json_match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(parsed, dict):
            utterance = parsed.get("utterance", response)
            presentation = parsed.get("presentation", "")
            grounding = parsed.get("grounding", {})
            break

    if utterance == response and isinstance(response, str):
        normalized_response = re.sub(r"^\s*\[[^\]\r\n]{1,20}\]\s*", "", response).strip()
        normalized_response = re.sub(r"^\s*patient\b[:\s-]*", "", normalized_response, flags=re.IGNORECASE).strip()

        presentation_match = re.search(
            r"presentation\s*:\s*(.*?)\s+utterance\s*:",
            normalized_response,
            re.IGNORECASE | re.DOTALL,
        )
        utterance_match = re.search(
            r"utterance\s*:\s*(.*?)(?:\s+grounding\s*:|$)",
            normalized_response,
            re.IGNORECASE | re.DOTALL,
        )

        if presentation_match:
            presentation = presentation_match.group(1).strip()
        if utterance_match:
            utterance = utterance_match.group(1).strip()

        if utterance == response:
            cleaned = re.sub(
                r"\s+grounding\s*:\s*\{[\s\S]*\}\s*$",
                "",
                normalized_response,
                flags=re.IGNORECASE,
            ).strip()
            cleaned = re.sub(r"^\s*presentation\s*:\s*", "", cleaned, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r"^\s*utterance\s*:\s*", "", cleaned, flags=re.IGNORECASE).strip()
            if cleaned:
                utterance = cleaned

    return utterance, presentation, grounding


def _strip_patient_internal_tags(text: str) -> str:
    if not text:
        return text
    cleaned = re.sub(r"\s*\[SEARCH_[^\]\r\n]+\]\s*", " ", str(text))
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _normalize_patient_emotion_tag(text: str) -> str:
    if not text:
        return text

    allowed = {"calm", "sad", "anxious", "angry", "excited", "flat"}
    alias_map = {
        "calm": "calm",
        "neutral": "calm",
        "quiet": "calm",
        "sad": "sad",
        "depressed": "sad",
        "down": "sad",
        "tired": "sad",
        "hopeless": "sad",
        "anxious": "anxious",
        "confused": "anxious",
        "afraid": "anxious",
        "fearful": "anxious",
        "nervous": "anxious",
        "worried": "anxious",
        "uneasy": "anxious",
        "alert": "anxious",
        "angry": "angry",
        "irritable": "angry",
        "hostile": "angry",
        "defensive": "angry",
        "excited": "excited",
        "agitated": "excited",
        "eager": "excited",
        "talkative": "excited",
        "flat": "flat",
        "apathetic": "flat",
        "indifferent": "flat",
        "mute": "flat",
        "reserved": "flat",
        "numb": "flat",
        "平静": "calm",
        "中性": "calm",
        "安静": "calm",
        "悲伤": "sad",
        "沮丧": "sad",
        "低落": "sad",
        "疲惫": "sad",
        "绝望": "sad",
        "伤心": "sad",
        "焦虑": "anxious",
        "困惑": "anxious",
        "害怕": "anxious",
        "恐惧": "anxious",
        "紧张": "anxious",
        "担心": "anxious",
        "不安": "anxious",
        "警惕": "anxious",
        "愤怒": "angry",
        "烦躁": "angry",
        "敌意": "angry",
        "易怒": "angry",
        "防御": "angry",
        "激动": "excited",
        "兴奋": "excited",
        "亢奋": "excited",
        "急切": "excited",
        "话多": "excited",
        "淡漠": "flat",
        "冷漠": "flat",
        "冷淡": "flat",
        "木僵": "flat",
        "少语": "flat",
        "无感": "flat",
    }

    match = re.match(r"^\s*\[([^\]\r\n]{1,20})\]", str(text))
    if not match:
        return f"[calm] {str(text).lstrip()}"

    tag = match.group(1).strip().lower()
    if tag in allowed:
        return text

    normalized = alias_map.get(tag, "calm")
    return re.sub(r"^\s*\[[^\]\r\n]{1,20}\]", f"[{normalized}]", str(text), count=1)


def _contains_cjk(text: str) -> bool:
    if not text:
        return False
    return bool(re.search("[\u4e00-\u9fff]", str(text)))


def _build_opening_prompt() -> str:
    return (
        "Respond as the patient and briefly introduce the main current complaint in 1-2 natural sentences. "
        "Return strict JSON only. Both presentation and utterance must be English only. "
        "{\"utterance\": \"patient speech in English\", \"presentation\": \"observable behavior in English\"}"
    )


def _build_search_followup_prompt(search_content: str, doctor_message: str) -> str:
    return (
        f"{search_content}\n\n"
        "Now continue answering as the patient based on the recalled information above. "
        "Return strict JSON only. Both presentation and utterance must be English only. "
        f"Doctor question: {doctor_message}"
    )


def _build_english_rewrite_prompt(response: str, doctor_message: str) -> str:
    return (
        "Rewrite the same patient response in English only. "
        "Keep exactly the same meaning and do not add new facts. "
        "Return strict JSON only with keys presentation, utterance, grounding. "
        "Both presentation and utterance must be English only.\n\n"
        f"Doctor question: {doctor_message}\n"
        f"Previous patient response: {response}"
    )


def _ensure_english_patient_response(patient, response: str, doctor_message: str) -> str:
    utterance, presentation, _ = _parse_patient_response(response)
    if not _contains_cjk(utterance) and not _contains_cjk(presentation):
        return response

    try:
        rewritten = patient.chat(_build_english_rewrite_prompt(response, doctor_message))
        rewritten_utterance, rewritten_presentation, _ = _parse_patient_response(rewritten)
        if not _contains_cjk(rewritten_utterance) and not _contains_cjk(rewritten_presentation):
            return rewritten
    except Exception as exc:
        logger.warning("[chat_send] English rewrite failed: %s", exc)

    return response


def _resolve_patient_search_if_needed(patient, response: str, case_id: str, doctor_message: str):
    utterance, _, _ = _parse_patient_response(response)
    search_match = re.search(r"\[SEARCH_([^\]\r\n]+)\]", utterance or "")
    if not search_match:
        return response, None

    event = search_match.group(1).strip()
    search_debug = {
        "code": search_match.group(0),
        "event": event,
        "status": "triggered",
    }

    # Direct file lookup (new backend behaviour — no fuzzy matching)
    _, experience_dir = get_patient_dirs(case_id)
    file_path = experience_dir / f"{event}.md"
    if not file_path.exists():
        logger.warning("[chat_send] Experience file not found: %s", event)
        search_debug["status"] = "empty"
        search_debug["message"] = f"Experience file not found: {event}"
        return response, search_debug

    search_content = file_path.read_text(encoding="utf-8")
    search_debug["status"] = "resolved"
    combined_prompt = _build_search_followup_prompt(search_content, doctor_message)
    return patient.chat(combined_prompt), search_debug


def _cleanup_expired_sessions():
    deleted = SESSION_STORE.delete_expired_sessions(SESSION_TTL_SECONDS)
    if deleted:
        logger.info("Expired chat sessions cleaned up: %s", deleted)


def _generate_record_id(case_id: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"{case_id}_{timestamp}_{suffix}"


def _get_patient_skill_file(case_id: str):
    skill_path, _ = get_patient_dirs(case_id)
    if skill_path.exists():
        return str(skill_path)
    return None


def _create_patient_for_case(case_data: dict, case_id: str):
    return create_patient(
        basic_info=case_data.get("basicInfomation", ""),
        chief_complaint=case_data.get("chiefComplaint", []),
        mental_status=case_data.get("mentalStatus", []),
        skill_file=_get_patient_skill_file(case_id),
    )


def _restore_patient_history(patient, llm_history):
    if isinstance(llm_history, list):
        patient._history = [
            message for message in llm_history
            if isinstance(message, dict) and "role" in message and "content" in message
        ]


def register_chat_routes(case_service):
    chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

    @chat_bp.route("/start", methods=["POST"])
    def api_chat_start():
        _cleanup_expired_sessions()

        data = request.get_json() or {}
        case_id = data.get("case_id")
        if not case_id:
            return jsonify({"error": "case_id required"}), 400

        case_data = case_service.get_case_for_interview(case_id)
        if not case_data:
            return jsonify({"error": "Case not found"}), 404

        try:
            patient = _create_patient_for_case(case_data, case_id)
            session_id = os.urandom(16).hex()
            record_id = _generate_record_id(case_id)
            SESSION_STORE.create_session(
                session_id=session_id,
                case_id=case_id,
                record_id=record_id,
                messages=[],
                llm_history=patient.get_history(),
            )

            return jsonify({
                "session_id": session_id,
                "case_id": case_id,
                "record_id": record_id,
                "opening": "",
                "opening_presentation": "",
            })
        except Exception as exc:
            logger.exception("Failed to create chat session")
            return jsonify({"error": str(exc)}), 500

    @chat_bp.route("/send", methods=["POST"])
    def api_chat_send():
        _cleanup_expired_sessions()

        data = request.get_json() or {}
        session_id = data.get("session_id")
        doctor_message = data.get("message", "")

        if not session_id or not doctor_message:
            return jsonify({"error": "session_id and message required"}), 400

        chat_session = SESSION_STORE.get_session(session_id)
        if not chat_session:
            return jsonify({"error": "Session not found"}), 404

        case_data = case_service.get_case_for_interview(chat_session["case_id"])
        if not case_data:
            return jsonify({"error": "Case not found"}), 404

        patient = _create_patient_for_case(case_data, chat_session["case_id"])
        _restore_patient_history(patient, chat_session.get("llm_history", []))

        try:
            response = patient.chat(doctor_message)
            response, search_debug = _resolve_patient_search_if_needed(
                patient=patient,
                response=response,
                case_id=chat_session["case_id"],
                doctor_message=doctor_message,
            )
            response = _ensure_english_patient_response(patient, response, doctor_message)

            utterance, presentation, _ = _parse_patient_response(response)
            utterance = _strip_patient_internal_tags(utterance)
            utterance = _normalize_patient_emotion_tag(utterance)

            chat_session["messages"].append({"role": "doctor", "content": doctor_message})
            chat_session["messages"].append({
                "role": "patient",
                "content": utterance,
                "presentation": presentation,
            })
            SESSION_STORE.update_session_messages(
                session_id=session_id,
                messages=chat_session["messages"],
                llm_history=patient.get_history(),
            )

            return jsonify({
                "response": utterance,
                "presentation": presentation,
                "search_debug": search_debug,
                "turn": len(chat_session["messages"]) // 2,
            })
        except Exception as exc:
            logger.exception("Failed to send chat message")
            return jsonify({"error": str(exc)}), 500

    @chat_bp.route("/end", methods=["POST"])
    def api_chat_end():
        data = request.get_json() or {}
        session_id = data.get("session_id")
        if session_id:
            SESSION_STORE.delete_session(session_id)
        return jsonify({"status": "ok"})

    @chat_bp.route("/sessions", methods=["GET"])
    def api_chat_sessions_list():
        now = time.time()
        sessions = []
        for session in SESSION_STORE.list_sessions():
            sessions.append({
                "session_id": session["session_id"],
                "case_id": session["case_id"],
                "record_id": session.get("record_id", ""),
                "turns": len(session["messages"]) // 2,
                "last_active_ago": round(now - session["last_active"]),
            })
        return jsonify({"sessions": sessions, "total": len(sessions)})

    return chat_bp
