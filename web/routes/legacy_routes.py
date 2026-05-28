"""
Legacy API routes — case queries, model queries, history records, evaluation, etc.

These routes were originally inlined in app.py, now extracted as an independent Blueprint.
All route paths and return formats remain unchanged.
"""
import json
import logging

from flask import Blueprint, jsonify, request

from config import (
    INTERVIEW_DIR, EVALUATION_DIR, DATA_DIR, RECORDS_DIR,
)
from utils.json_utils import read_json_safe
from utils.sanitize import is_valid_record_id

logger = logging.getLogger(__name__)


def register_legacy_routes(case_service, evaluation_service_phase_fn, evaluation_service_phase2_accuracy_fn):
    """Register legacy API routes

    Args:
        case_service: Case service instance
        evaluation_service_phase_fn: evaluate_phase function from evaluation service
        evaluation_service_phase2_accuracy_fn: evaluate_phase2_accuracy function from evaluation service
    """
    legacy_bp = Blueprint("legacy", __name__)

    # ============================================================
    # Case / Model queries
    # ============================================================

    @legacy_bp.route("/api/cases")
    def api_cases():
        """Get all case list"""
        cases = case_service.get_all_cases()
        return jsonify({"cases": cases, "total": len(cases)})

    @legacy_bp.route("/api/models")
    def api_models():
        """Get list of models with existing output results"""
        if not INTERVIEW_DIR.exists():
            return jsonify({"models": [], "total": 0})
        models = sorted([d.name for d in INTERVIEW_DIR.iterdir() if d.is_dir()])
        return jsonify({"models": models, "total": len(models)})

    @legacy_bp.route("/api/models/<model_name>/cases")
    def api_model_cases(model_name):
        """Get case IDs with existing results for specified model"""
        model_dir = INTERVIEW_DIR / model_name
        if not model_dir.exists():
            return jsonify({"model": model_name, "cases": [], "total": 0})
        case_ids = sorted([d.name for d in model_dir.iterdir() if d.is_dir()])
        return jsonify({"model": model_name, "cases": case_ids, "total": len(case_ids)})

    @legacy_bp.route("/api/case/<case_id>/info")
    def api_case_info(case_id):
        """Get basic case information"""
        case = case_service.get_case(case_id)
        if not case:
            return jsonify({"error": "Case not found"}), 404
        return jsonify(case)

    @legacy_bp.route("/api/case/<case_id>/summary/<model_name>")
    def api_case_summary(case_id, model_name):
        """Get full process summary"""
        summary_file = INTERVIEW_DIR / model_name / case_id / "interview_summary.json"
        data = read_json_safe(summary_file)
        if data is None:
            return jsonify({"error": "Summary not found"}), 404
        return jsonify(data)

    @legacy_bp.route("/api/case/<case_id>/phase/<int:phase>/<model_name>")
    def api_phase(case_id, phase, model_name):
        """Get output and evaluation results for a single phase"""
        interview_file = INTERVIEW_DIR / model_name / case_id / f"interview_phase{phase}_output.json"
        eval_file = EVALUATION_DIR / model_name / case_id / f"evaluation_phase{phase}_output.json"

        result = {"phase": phase, "case_id": case_id, "model_name": model_name}

        interview_data = read_json_safe(interview_file)
        result["interview"] = interview_data

        eval_data = read_json_safe(eval_file)
        result["evaluation"] = eval_data

        return jsonify(result)

    @legacy_bp.route("/api/ground_truth/<case_id>")
    def api_ground_truth(case_id):
        """Get ground truth for specified case"""
        ground_truth_file = DATA_DIR / "ground_truth.jsonl"
        if not ground_truth_file.exists():
            return jsonify({"error": "Ground truth file not found"}), 404
        try:
            with open(ground_truth_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            if data.get("id") == case_id:
                                return jsonify(data)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Failed to read ground truth: {e}")
        return jsonify({"error": "Case not found in ground truth"}), 404

    # ============================================================
    # History API
    # ============================================================

    @legacy_bp.route("/api/history/list")
    def api_history_list():
        """List all consultation history records"""
        histories = []
        for f in sorted(RECORDS_DIR.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                conversation = data.get("conversation", [])
                turns = len(conversation) // 2 if conversation else 0
                case_info = data.get("caseInfo", {})
                basic_info = case_info.get("basicInfomation", "")
                has_diagnosis = bool(data.get("diagnosis"))
                record_id = f.stem
                raw_case_id = data.get("original_case_id") or data.get("case_id", f.stem)
                histories.append({
                    "record_id": record_id,
                    "case_id": raw_case_id,
                    "saved_at": data.get("updated_at") or data.get("created_at", ""),
                    "created_at": data.get("created_at", ""),
                    "turns": turns,
                    "has_diagnosis": has_diagnosis,
                    "basic_info": basic_info,
                })
            except Exception as e:
                logger.warning(f"Failed to read record file {f}: {e}")
        return jsonify({"histories": histories, "total": len(histories)})

    @legacy_bp.route("/api/history/<record_id>")
    def api_history_detail(record_id):
        """View detail of a single consultation history record"""
        if not is_valid_record_id(record_id):
            return jsonify({"error": "Invalid record_id"}), 400

        record_file = RECORDS_DIR / f"{record_id}.json"
        if not record_file.exists():
            return jsonify({"error": "History not found"}), 404
        data = read_json_safe(record_file)
        if data is None:
            return jsonify({"error": "Failed to read history"}), 500
        data["messages"] = data.get("conversation", [])
        return jsonify(data)

    @legacy_bp.route("/api/history/<record_id>", methods=["DELETE"])
    def api_history_delete(record_id):
        """Delete a single consultation history record"""
        if not is_valid_record_id(record_id):
            return jsonify({"error": "Invalid record_id"}), 400

        record_file = RECORDS_DIR / f"{record_id}.json"
        if not record_file.exists():
            return jsonify({"error": "History not found"}), 404
        try:
            record_file.unlink()
            logger.info(f"Consultation history deleted: {record_id}")
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Failed to delete consultation history: {e}")
            return jsonify({"error": str(e)}), 500

    # ============================================================
    # Evaluation API
    # ============================================================

    @legacy_bp.route("/api/evaluate/<int:phase>", methods=["POST"])
    def api_evaluate(phase):
        """Evaluate the current consultation session for a phase"""
        try:
            body = request.get_json(silent=True) or {}
            if not isinstance(body, dict):
                body = {}

            case_id = str(body.get("case_id", "") or "").strip()

            if not case_id:
                return jsonify({"error": "Missing case_id"}), 400

            result = evaluation_service_phase_fn(phase, case_id, body, case_service)
            return jsonify(result)

        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Failed to evaluate phase {phase}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @legacy_bp.route("/api/evaluate/phase2-accuracy", methods=["POST"])
    def api_evaluate_phase2_accuracy():
        """Phase 2 examination selection — return accuracy only (Jaccard)"""
        try:
            body = request.get_json()
            case_id = body.get("case_id", "")
            exam_results = body.get("exam_results", {})

            if not case_id:
                return jsonify({"error": "Missing case_id"}), 400

            accuracy = evaluation_service_phase2_accuracy_fn(case_id, exam_results, case_service)
            return jsonify({"accuracy": accuracy})

        except Exception as e:
            logger.error(f"Phase 2 accuracy endpoint error: {e}")
            return jsonify({"error": str(e)}), 500

    return legacy_bp
