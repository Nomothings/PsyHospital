"""
诊疗路由 — Phase 4 治疗方案提交
"""
import logging
from flask import Blueprint, request, jsonify

from service_layer.record_service import RecordService

logger = logging.getLogger(__name__)


def register_treatment_routes(record_service: RecordService):
    """注册诊疗路由"""
    treatment_bp = Blueprint("treatment", __name__, url_prefix="/api/treatment")

    @treatment_bp.route("/submit", methods=["POST"])
    def api_treatment_submit():
        """提交 Phase 4 治疗方案"""
        data = request.get_json() or {}
        case_id = data.get("case_id")
        treatment = data.get("treatment", {})

        if not case_id:
            return jsonify({"error": "case_id required"}), 400

        existing = record_service.get_record(case_id) or {}
        existing["treatment"] = treatment

        record_service.save_record(case_id, existing)

        logger.info(f"病例 {case_id} 治疗方案已提交并持久化")
        return jsonify({"status": "ok", "case_id": case_id})

    return treatment_bp
