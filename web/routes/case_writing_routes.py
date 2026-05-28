"""
Case writing routes — Phase 3 case record submission (validation only, data merged by frontend saveCaseRecord)
"""
import json
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)


def register_case_writing_routes(record_service):
    """Register case writing routes"""
    writing_bp = Blueprint("case_writing", __name__, url_prefix="/api/case-writing")

    @writing_bp.route("/submit", methods=["POST"])
    def api_case_writing_submit():
        """Submit Phase 3 case writing — validation only, no separate file writing"""
        data = request.get_json() or {}
        case_id = data.get("case_id")
        case_text = data.get("case_text", "")

        if not case_id or not case_text:
            return jsonify({"error": "case_id and case_text required"}), 400

        # Validate whether case_text is valid JSON
        try:
            case_form = json.loads(case_text)
            if not isinstance(case_form, dict):
                return jsonify({"error": "case_text must be a JSON object"}), 400
        except json.JSONDecodeError:
            return jsonify({"error": "case_text must be valid JSON"}), 400

        # Data persistence handled by frontend saveCaseRecord, ensuring merge into the same consultation record
        logger.info(f"Case {case_id} case writing validation passed")
        return jsonify({"status": "ok", "case_id": case_id})

    return writing_bp
