"""
Record routes.
"""
import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)


def register_record_routes(record_service):
    record_bp = Blueprint("record", __name__, url_prefix="/api/record")

    @record_bp.route("/save", methods=["POST"])
    def save_record():
        try:
            data = request.get_json() or {}
            case_id = data.get("case_id")
            if not case_id:
                return jsonify({"error": "case_id required"}), 400

            result = record_service.save_record(case_id, data)
            return jsonify(result)
        except Exception as exc:
            logger.error("Failed to save record: %s", exc)
            return jsonify({"error": str(exc)}), 500

    @record_bp.route("/<record_id>")
    def get_record(record_id):
        try:
            record = record_service.get_record(record_id)
            if not record:
                return jsonify({"error": "Record not found"}), 404
            return jsonify(record)
        except Exception as exc:
            logger.error("Failed to get record %s: %s", record_id, exc)
            return jsonify({"error": str(exc)}), 500

    return record_bp
