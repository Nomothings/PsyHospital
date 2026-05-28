"""
Treatment routes — Phase 4 treatment plan submission (validation only, data merged by frontend saveCaseRecord)
"""
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)


def register_treatment_routes(record_service):
    """Register treatment routes"""
    treatment_bp = Blueprint("treatment", __name__, url_prefix="/api/treatment")

    @treatment_bp.route("/submit", methods=["POST"])
    def api_treatment_submit():
        """Submit Phase 4 treatment plan — validation only, no separate file writing"""
        data = request.get_json() or {}
        case_id = data.get("case_id")
        treatment = data.get("treatment", {})

        if not case_id:
            return jsonify({"error": "case_id required"}), 400

        if not treatment:
            return jsonify({"error": "treatment data required"}), 400

        # Data persistence handled by frontend saveCaseRecord, ensuring merge into the same consultation record
        logger.info(f"Case {case_id} treatment plan validation passed")
        return jsonify({"status": "ok", "case_id": case_id})

    return treatment_bp
