"""
Routes for auxiliary examinations and category evidence matching.
"""
import logging

from flask import Blueprint, jsonify, request

from service_layer.category_keywords import CATEGORY_KEYWORDS

logger = logging.getLogger(__name__)

EXAM_ALIAS_GROUPS = {
    "Complete Blood Count (CBC)": ["CBC", "全血细胞计数", "血常规"],
    "Urinalysis": ["尿检", "尿液检查", "尿常规"],
    "Stool Routine": ["大便常规", "便常规", "粪便常规"],
    "Liver Function": ["肝功", "肝功能检查", "肝功能"],
    "Renal Function": ["肾功", "肾功能检查", "肾功能"],
    "Electrolytes": ["血电解质", "电解质检查", "电解质"],
    "Thyroid Function": ["甲功", "甲状腺功能检查", "甲状腺功能"],
    "ECG": ["EKG", "心电图"],
    "EEG": ["脑电图"],
    "Head CT": ["头颅CT", "颅脑CT", "CT", "脑CT"],
    "Head MRI": ["头颅MRI", "颅脑MRI", "MRI", "脑MRI"],
    "Chest X-ray": ["胸部X线", "X线胸片", "X光", "胸片"],
    "Abdominal Ultrasound": ["B超", "腹部超声", "腹部B超"],
    "SCL-90": ["症状自评量表", "SCL90", "scl-90"],
    "MMSE": ["简易精神状态检查", "mmse"],
}


def _normalize_exam_text(text: str) -> str:
    return (text or "").replace(" ", "").replace("\uFF08", "(").replace("\uFF09", ")").strip().lower()


def _canonical_exam_name(exam_name: str) -> str:
    normalized_exam = _normalize_exam_text(exam_name)
    for canonical, aliases in EXAM_ALIAS_GROUPS.items():
        if normalized_exam == _normalize_exam_text(canonical):
            return canonical
        for alias in aliases:
            if normalized_exam == _normalize_exam_text(alias):
                return canonical
    return (exam_name or "").strip()


def register_check_routes(case_service):
    check_bp = Blueprint("check", __name__, url_prefix="/api/check")

    @check_bp.route("/exam", methods=["POST"])
    def api_check_exam():
        data = request.get_json() or {}
        case_id = data.get("case_id")
        exam_name = data.get("exam_name")

        if not exam_name:
            return jsonify({"error": "exam_name required"}), 400

        case_data = case_service.get_case(case_id)
        if not case_data:
            return jsonify({"error": "Case not found"}), 404

        aux_exam = case_data.get("auxiliaryExamination", {})
        canonical_exam_name = _canonical_exam_name(exam_name)
        normalized_exam_name = _normalize_exam_text(exam_name)
        normalized_canonical_exam_name = _normalize_exam_text(canonical_exam_name)

        result = None
        if exam_name in aux_exam:
            result = aux_exam[exam_name]
        elif canonical_exam_name in aux_exam:
            result = aux_exam[canonical_exam_name]
        else:
            for key, value in aux_exam.items():
                normalized_key = _normalize_exam_text(key)
                if normalized_key in {normalized_exam_name, normalized_canonical_exam_name}:
                    result = value
                    break
                if _canonical_exam_name(key) == canonical_exam_name:
                    result = value
                    break

        payload = {"exam_name": exam_name, "result": result if result is not None else "None"}
        return jsonify(payload)

    @check_bp.route("/category", methods=["POST"])
    def api_check_category():
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

        for complaint in case_data.get("chiefComplaint", []):
            search_texts.append({"source": "chiefComplaint", "role": "patient", "content": complaint.strip()})
        for mental_status in case_data.get("mentalStatus", []):
            search_texts.append({"source": "mentalStatus", "role": "patient", "content": mental_status.strip()})
        for msg in messages:
            search_texts.append({"source": "conversation", "role": msg.get("role", "unknown"), "content": msg.get("content", "")})

        evidence = []
        seen_contents = set()
        for item in search_texts:
            content = item["content"]
            content_lower = content.lower()
            for keyword in keywords:
                if keyword.lower() in content_lower and content not in seen_contents:
                    evidence.append({"role": item["role"], "content": content})
                    seen_contents.add(content)
                    break

        if evidence:
            payload = {
                "category": category,
                "result": {"status": "positive", "evidence": evidence},
            }
            return jsonify(payload)

        return jsonify({"category": category, "result": "None"})

    return check_bp
