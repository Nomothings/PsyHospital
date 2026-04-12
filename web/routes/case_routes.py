"""
病例相关路由
"""
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)


def register_case_routes(case_service):
    """注册病例路由"""
    case_bp = Blueprint("case", __name__, url_prefix="/api/cases")

    # 注意：具体路径必须在参数路径之前注册，避免 /random 被 /<case_id> 捕获

    @case_bp.route("/random", methods=["GET"])
    def get_random_case():
        """随机抽取一个病例

        Query params:
            mode: "common" (常规模式) 或 "rare" (罕见病模式)
        """
        try:
            mode = request.args.get("mode", "common")
            if mode not in ("common", "rare"):
                return jsonify({"error": "mode 必须为 common 或 rare"}), 400

            case = case_service.get_random_case(mode)
            if not case:
                return jsonify({"error": f"{mode} 模式下没有可用病例"}), 404
            return jsonify({"case": case, "mode": mode})
        except Exception as e:
            logger.error(f"随机抽取病例失败 (mode={mode}): {e}")
            return jsonify({"error": str(e)}), 500

    @case_bp.route("/counts")
    def get_mode_counts():
        """获取各模式的病例数量"""
        try:
            counts = case_service.get_mode_counts()
            return jsonify({"counts": counts})
        except Exception as e:
            logger.error(f"获取病例数量失败: {e}")
            return jsonify({"error": str(e)}), 500

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
