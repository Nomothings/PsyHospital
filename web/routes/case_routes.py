"""
病例相关路由
"""
from flask import Blueprint, jsonify
import logging

logger = logging.getLogger(__name__)


def register_case_routes(case_service):
    """注册病例路由"""
    case_bp = Blueprint("case", __name__, url_prefix="/api/cases")

    @case_bp.route("/<case_id>")
    def get_case(case_id):
        """获取单个病例详情"""
        try:
            case = case_service.get_case(case_id)
            if not case:
                return jsonify({"error": "病例不存在"}), 404
            return jsonify(case)
        except Exception as e:
            logger.error(f"获取病例 {case_id} 失败: {e}")
            return jsonify({"error": str(e)}), 500

    @case_bp.route("/<case_id>/interview")
    def get_case_for_interview(case_id):
        """获取用于访谈的病例数据"""
        try:
            case = case_service.get_case_for_interview(case_id)
            if not case:
                return jsonify({"error": "病例不存在"}), 404
            return jsonify(case)
        except Exception as e:
            logger.error(f"获取病例 {case_id} 访谈数据失败: {e}")
            return jsonify({"error": str(e)}), 500

    return case_bp
