"""
问诊记录相关路由
"""
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)


def register_record_routes(record_service):
    """注册记录路由"""
    record_bp = Blueprint("record", __name__, url_prefix="/api/record")

    @record_bp.route("/save", methods=["POST"])
    def save_record():
        """保存问诊记录"""
        try:
            data = request.get_json() or {}
            case_id = data.get("case_id")
            if not case_id:
                return jsonify({"error": "case_id required"}), 400

            result = record_service.save_record(case_id, data)
            return jsonify(result)
        except Exception as e:
            logger.error(f"保存记录失败: {e}")
            return jsonify({"error": str(e)}), 500

    @record_bp.route("/<case_id>")
    def get_record(case_id):
        """获取问诊记录"""
        try:
            record = record_service.get_record(case_id)
            if not record:
                return jsonify({"error": "Record not found"}), 404
            return jsonify(record)
        except Exception as e:
            logger.error(f"获取记录 {case_id} 失败: {e}")
            return jsonify({"error": str(e)}), 500

    return record_bp
