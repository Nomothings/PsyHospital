"""
检查匹配路由 — 辅助检查结果查询 + ICD-11 分类关键词匹配
"""
import logging
from flask import Blueprint, request, jsonify

from service_layer.category_keywords import CATEGORY_KEYWORDS

logger = logging.getLogger(__name__)


def register_check_routes(case_service):
    """注册检查路由"""
    check_bp = Blueprint("check", __name__, url_prefix="/api/check")

    @check_bp.route("/exam", methods=["POST"])
    def api_check_exam():
        """查询患者病例中的辅助检查结果"""
        data = request.get_json() or {}
        case_id = data.get("case_id")
        exam_name = data.get("exam_name")

        if not exam_name:
            return jsonify({"error": "exam_name required"}), 400

        case_data = case_service.get_case(case_id)
        if not case_data:
            return jsonify({"error": "Case not found"}), 404

        aux_exam = case_data.get("auxiliaryExamination", {})

        if exam_name in aux_exam:
            return jsonify({"exam_name": exam_name, "result": aux_exam[exam_name]})

        for key, value in aux_exam.items():
            if key.replace(" ", "").lower() == exam_name.replace(" ", "").lower():
                return jsonify({"exam_name": exam_name, "result": value})

        return jsonify({"exam_name": exam_name, "result": "无"})

    @check_bp.route("/category", methods=["POST"])
    def api_check_category():
        """检查某个 ICD-11 疾病分类是否在患者病例中有相关证据"""
        data = request.get_json() or {}
        case_id = data.get("case_id")
        category = data.get("category")
        messages = data.get("messages", [])

        if not category:
            return jsonify({"error": "category required"}), 400

        case_data = case_service.get_case(case_id)
        if not case_data:
            return jsonify({"error": "Case not found"}), 404

        keywords = CATEGORY_KEYWORDS.get(category, [])

        search_texts = []
        for cc in case_data.get("chiefComplaint", []):
            search_texts.append({"source": "chiefComplaint", "role": "patient", "content": cc.strip()})
        for ms in case_data.get("mentalStatus", []):
            search_texts.append({"source": "mentalStatus", "role": "patient", "content": ms.strip()})
        for msg in messages:
            search_texts.append({"source": "conversation", "role": msg.get("role", "unknown"), "content": msg.get("content", "")})

        evidence = []
        seen_contents = set()
        for item in search_texts:
            content = item["content"]
            content_lower = content.lower()
            for kw in keywords:
                if kw.lower() in content_lower and content not in seen_contents:
                    evidence.append({"role": item["role"], "content": content})
                    seen_contents.add(content)
                    break

        if evidence:
            return jsonify({
                "category": category,
                "result": {"status": "positive", "evidence": evidence},
            })
        else:
            return jsonify({"category": category, "result": "无"})

    return check_bp
