"""
病历书写路由 — Phase 3 病历提交
"""
import json
import logging
from flask import Blueprint, request, jsonify

from service_layer.record_service import RecordService

logger = logging.getLogger(__name__)


def register_case_writing_routes(record_service: RecordService):
    """注册病历书写路由"""
    writing_bp = Blueprint("case_writing", __name__, url_prefix="/api/case-writing")

    @writing_bp.route("/submit", methods=["POST"])
    def api_case_writing_submit():
        """提交 Phase 3 病历书写"""
        data = request.get_json() or {}
        case_id = data.get("case_id")
        case_text = data.get("case_text", "")

        if not case_id or not case_text:
            return jsonify({"error": "case_id and case_text required"}), 400

        # 通过 record_service 持久化病历
        existing = record_service.get_record(case_id) or {}

        # 尝试解析 case_text 是否为 caseForm JSON
        try:
            case_form = json.loads(case_text)
            if isinstance(case_form, dict):
                existing["case_form"] = case_form
                # 兼容旧字段：将表单内容拼接为文本
                existing["case_text"] = (
                    f"姓名: {case_form.get('name', '')}\n"
                    f"年龄: {case_form.get('age', '')}\n"
                    f"性别: {case_form.get('gender', '')}\n"
                    f"主诉: {case_form.get('chiefComplaint', '')}\n"
                    f"家族史: {case_form.get('familyHistory', '')}\n"
                    f"既往史: {case_form.get('pastHistory', '')}\n"
                    f"体格检查: {case_form.get('physicalExam', '')}\n"
                    f"精神检查: {case_form.get('mentalExam', '')}\n"
                    f"辅助检查: {case_form.get('auxiliaryExam', '')}"
                )
            else:
                existing["case_text"] = case_text
        except json.JSONDecodeError:
            existing["case_text"] = case_text

        record_service.save_record(case_id, existing)

        logger.info(f"病例 {case_id} 病历书写已提交并持久化")
        return jsonify({"status": "ok", "case_id": case_id})

    return writing_bp
