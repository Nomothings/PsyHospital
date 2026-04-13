"""
病历书写路由 — Phase 3 病历提交（仅验证，数据由前端 saveCaseRecord 统一合并）
"""
import json
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)


def register_case_writing_routes(record_service):
    """注册病历书写路由"""
    writing_bp = Blueprint("case_writing", __name__, url_prefix="/api/case-writing")

    @writing_bp.route("/submit", methods=["POST"])
    def api_case_writing_submit():
        """提交 Phase 3 病历书写 — 仅做验证，不单独写文件"""
        data = request.get_json() or {}
        case_id = data.get("case_id")
        case_text = data.get("case_text", "")

        if not case_id or not case_text:
            return jsonify({"error": "case_id and case_text required"}), 400

        # 验证 case_text 是否为有效 JSON
        try:
            case_form = json.loads(case_text)
            if not isinstance(case_form, dict):
                return jsonify({"error": "case_text must be a JSON object"}), 400
        except json.JSONDecodeError:
            return jsonify({"error": "case_text must be valid JSON"}), 400

        # 数据持久化由前端 saveCaseRecord 统一处理，确保合并到同一次问诊记录
        logger.info(f"病例 {case_id} 病历书写验证通过")
        return jsonify({"status": "ok", "case_id": case_id})

    return writing_bp
