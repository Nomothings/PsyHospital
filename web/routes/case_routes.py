"""
Case-related routes
"""
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)


def register_case_routes(case_service):
    """Register case routes"""
    case_bp = Blueprint("case", __name__, url_prefix="/api/cases")

    # Note: specific paths must be registered before parameterized paths to avoid /random being captured by /<case_id>

    @case_bp.route("/random", methods=["GET"])
    def get_random_case():
        """Randomly select a case

        Query params:
            mode: "common" (common mode) or "rare" (rare disease mode)
        """
        try:
            mode = request.args.get("mode", "common")
            if mode not in ("common", "rare"):
                return jsonify({"error": "mode must be 'common' or 'rare'"}), 400

            case = case_service.get_random_case(mode)
            if not case:
                return jsonify({"error": f"No available cases in {mode} mode"}), 404
            return jsonify({"case": case, "mode": mode})
        except Exception as e:
            logger.error(f"Failed to randomly select case (mode={mode}): {e}")
            return jsonify({"error": str(e)}), 500

    @case_bp.route("/counts")
    def get_mode_counts():
        """Get case counts by mode"""
        try:
            counts = case_service.get_mode_counts()
            return jsonify({"counts": counts})
        except Exception as e:
            logger.error(f"Failed to get case counts: {e}")
            return jsonify({"error": str(e)}), 500

    @case_bp.route("/<case_id>")
    def get_case(case_id):
        """Get single case details"""
        try:
            case = case_service.get_case(case_id)
            if not case:
                return jsonify({"error": "Case not found"}), 404
            return jsonify(case)
        except Exception as e:
            logger.error(f"Failed to get case {case_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @case_bp.route("/<case_id>/interview")
    def get_case_for_interview(case_id):
        """Get case data for interview"""
        try:
            case = case_service.get_case_for_interview(case_id)
            if not case:
                return jsonify({"error": "Case not found"}), 404
            return jsonify(case)
        except Exception as e:
            logger.error(f"Failed to get interview data for case {case_id}: {e}")
            return jsonify({"error": str(e)}), 500

    return case_bp
