"""
诊疗路由 — Phase 4 治疗方案提交（仅验证，数据由前端 saveCaseRecord 统一合并）
"""
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)


def register_treatment_routes(record_service):
    """注册诊疗路由"""
    treatment_bp = Blueprint("treatment", __name__, url_prefix="/api/treatment")

    @treatment_bp.route("/submit", methods=["POST"])
    def api_treatment_submit():
        """提交 Phase 4 治疗方案 — 仅做验证，不单独写文件"""
        data = request.get_json() or {}
        case_id = data.get("case_id")
        treatment = data.get("treatment", {})

        if not case_id:
            return jsonify({"error": "case_id required"}), 400

        if not treatment:
            return jsonify({"error": "treatment data required"}), 400

        # 数据持久化由前端 saveCaseRecord 统一处理，确保合并到同一次问诊记录
        logger.info(f"病例 {case_id} 治疗方案验证通过")
        return jsonify({"status": "ok", "case_id": case_id})

    return treatment_bp
