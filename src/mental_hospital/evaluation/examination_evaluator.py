"""Phase 2 evaluation: examination recommendation P/R/F1/Jaccard."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mental_hospital.data.output import get_phase_output_file, save_evaluation_result
from mental_hospital.utils.json_utils import parse_json_array, parse_json_object

logger = logging.getLogger(__name__)


def calculate_metrics(
    response: Union[str, Dict[str, str]],
    examination_query: Union[str, List[str]],
    auxiliary_examinations: Union[str, Dict[str, str]],
) -> Dict[str, Any]:
    response_dict = parse_json_object(response, "response")
    query_list = parse_json_array(examination_query, "examination_query")
    gold_dict = parse_json_object(auxiliary_examinations, "auxiliary_examinations")

    predicted_count = len(query_list)
    gold_count = len(gold_dict)
    gold_keys = set(gold_dict.keys())
    recommended_keys = set(query_list)

    tp = len(recommended_keys & gold_keys)
    fp = len(recommended_keys - gold_keys)
    fn = len(gold_keys - recommended_keys)
    none_count = sum(1 for v in response_dict.values() if isinstance(v, str) and v.strip().upper() == "NONE")

    if predicted_count == 0 and gold_count == 0:
        precision = recall = f1 = jaccard = 1.0
    else:
        precision = tp / predicted_count if predicted_count > 0 else 0.0
        recall = tp / gold_count if gold_count > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        jaccard = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0

    warnings: list[str] = []
    if len(response_dict) != predicted_count:
        warnings.append(f"Response keys ({len(response_dict)}) != requested ({predicted_count})")

    return {
        "counts": {"gold_count": gold_count, "predicted_count": predicted_count, "response_count": len(response_dict), "tp": tp, "fp": fp, "fn": fn, "none_count": none_count, "correct_count": tp, "redundant_count": fp, "missed_count": fn},
        "metrics": {"precision": round(precision, 6), "recall": round(recall, 6), "f1": round(f1, 6), "jaccard": round(jaccard, 6)},
        "response": response_dict, "warnings": warnings,
    }


def evaluate(
    model_name: Optional[str] = None, case_id: Optional[str] = None,
    output_file: Optional[Union[str, Path]] = None,
    phase2_data: Optional[Dict[str, Any]] = None,
    case_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if phase2_data is None:
        if output_file is None:
            if model_name is None or case_id is None:
                raise ValueError("Provide model_name+case_id, output_file, or phase2_data")
            output_file = get_phase_output_file(model_name, case_id, 2)
        output_file = Path(output_file)
        phase2_data = json.loads(output_file.read_text(encoding="utf-8"))
    model_name = phase2_data.get("model_name", model_name or "")
    case_id = phase2_data.get("case_id", case_id or "")

    examinations = phase2_data.get("examinations", [])
    examination_results = phase2_data.get("examination_results", {})
    status = phase2_data.get("status", "unknown")

    evaluation_metrics: Dict[str, float] = {}
    counts: Dict[str, Any] = {}
    warnings: list[str] = []

    if case_data:
        aux = case_data.get("auxiliaryExamination", {})
        if aux:
            try:
                res = calculate_metrics(response=examination_results, examination_query=json.dumps(examinations, ensure_ascii=False), auxiliary_examinations=json.dumps(aux, ensure_ascii=False))
                evaluation_metrics, counts, warnings = res["metrics"], res["counts"], res["warnings"]
            except (ValueError, TypeError) as exc:
                logger.warning("Phase 2 metric calc failed: %s", exc)
                evaluation_metrics = {"precision": 0.0, "recall": 0.0, "f1": 0.0, "jaccard": 0.0}
                warnings = [f"Parse error: {exc}"]
        else:
            evaluation_metrics = {"precision": 1.0, "recall": 1.0, "f1": 1.0, "jaccard": 1.0} if not examinations else {"precision": 0.0, "recall": 0.0, "f1": 0.0, "jaccard": 0.0}
    else:
        evaluation_metrics = {"precision": 0.0, "recall": 0.0, "f1": 0.0, "jaccard": 0.0}

    eval_data = {"metrics": evaluation_metrics, "counts": counts, "status": status, "examinations": examinations, "examination_results": examination_results, "warnings": warnings}
    path = save_evaluation_result(model_name, case_id, 2, eval_data)
    return {"metrics": evaluation_metrics, "counts": counts, "status": status, "output_file": str(path), "model_name": model_name, "case_id": case_id, "warnings": warnings}
