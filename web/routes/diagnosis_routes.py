"""
诊断相关路由
"""
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)


def register_diagnosis_routes(diagnosis_service):
    """注册诊断路由"""
    diagnosis_bp = Blueprint("diagnosis", __name__, url_prefix="/api/diagnosis")

    @diagnosis_bp.route("/submit", methods=["POST"])
    def submit_diagnosis():
        """提交诊断结果"""
        try:
            data = request.get_json() or {}
            case_id = data.get("case_id")
            if not case_id:
                return jsonify({"error": "case_id required"}), 400

            diagnosis = {
                "category": data.get("category", ""),
                "disease": data.get("disease", ""),
                "reason": data.get("reason", ""),
            }

            result = diagnosis_service.submit_diagnosis(case_id, diagnosis)
            return jsonify(result)
        except Exception as e:
            logger.error(f"提交诊断失败: {e}")
            return jsonify({"error": str(e)}), 500

    @diagnosis_bp.route("/<case_id>")
    def get_diagnosis(case_id):
        """获取诊断结果"""
        try:
            diagnosis = diagnosis_service.get_diagnosis(case_id)
            if not diagnosis:
                return jsonify({"error": "Diagnosis not found"}), 404
            return jsonify(diagnosis)
        except Exception as e:
            logger.error(f"获取诊断 {case_id} 失败: {e}")
            return jsonify({"error": str(e)}), 500

    return diagnosis_bp
