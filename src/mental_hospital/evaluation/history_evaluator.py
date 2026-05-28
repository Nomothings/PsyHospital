"""Phase 1 evaluation: coverage statistics + empathy/professionalism scoring."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mental_hospital.data.output import get_phase_output_file, save_evaluation_result
from mental_hospital.evaluation.scorer import Scorer
from mental_hospital.prompts.rubrics import COMMUNICATION_EMPATHY, INTERVIEWING_PROFESSIONALISM
from mental_hospital.utils.text_utils import format_conversation_text

logger = logging.getLogger(__name__)


def calculate_coverage(
    chief_complaint_all: List[str], mental_status_all: List[str],
    chief_complaint_used: List[str], mental_status_used: List[str],
) -> Dict[str, Any]:
    cc_all = [item.strip() if isinstance(item, str) else item for item in chief_complaint_all]
    ms_all = [item.strip() if isinstance(item, str) else item for item in mental_status_all]
    cc_used = [item.strip() if isinstance(item, str) else item for item in chief_complaint_used]
    ms_used = [item.strip() if isinstance(item, str) else item for item in mental_status_used]
    cc_all_set, ms_all_set = set(cc_all), set(ms_all)
    cc_used = [i for i in cc_used if i in cc_all_set]
    ms_used = [i for i in ms_used if i in ms_all_set]
    cc_cov = (len(cc_used) / len(cc_all) * 100) if cc_all else 0.0
    ms_cov = (len(ms_used) / len(ms_all) * 100) if ms_all else 0.0
    total = len(cc_all) + len(ms_all)
    used = len(cc_used) + len(ms_used)
    overall = (used / total * 100) if total else 0.0
    return {
        "chief_complaint_coverage": round(cc_cov, 2),
        "mental_status_coverage": round(ms_cov, 2),
        "overall_coverage": round(overall, 2),
        "chief_complaint_used_count": len(cc_used),
        "chief_complaint_total_count": len(cc_all),
        "mental_status_used_count": len(ms_used),
        "mental_status_total_count": len(ms_all),
    }


def calculate_conversation_stats(conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
    patient = sum(1 for c in conversation if c.get("role") == "patient")
    doctor = sum(1 for c in conversation if c.get("role") == "doctor")
    return {"total_turns": patient, "patient_turns": patient, "doctor_turns": doctor, "conversation_length": len(conversation)}


def evaluate(
    model_name: Optional[str] = None, case_id: Optional[str] = None,
    output_file: Optional[Union[str, Path]] = None,
    phase1_data: Optional[Dict[str, Any]] = None,
    *, enable_empathy: bool = True, enable_profession: bool = True, parallel: bool = True,
) -> Dict[str, Any]:
    if phase1_data is None:
        if output_file is None:
            if model_name is None or case_id is None:
                raise ValueError("Provide model_name+case_id, output_file, or phase1_data")
            output_file = get_phase_output_file(model_name, case_id, 1)
        output_file = Path(output_file)
        phase1_data = json.loads(output_file.read_text(encoding="utf-8"))
    model_name = phase1_data.get("model_name", model_name or "")
    case_id = phase1_data.get("case_id", case_id or "")
    if not model_name or not case_id:
        raise ValueError("Cannot determine model_name or case_id")

    coverage = calculate_coverage(
        phase1_data.get("chief_complaint_all", []), phase1_data.get("mental_status_all", []),
        phase1_data.get("chief_complaint_used", []), phase1_data.get("mental_status_used", []),
    )
    conv_stats = calculate_conversation_stats(phase1_data.get("conversation", []))

    eval_data: Dict[str, Any] = {"coverage_stats": coverage, "conversation_stats": conv_stats, "status": phase1_data.get("status", "unknown")}
    empathy_result = None
    profession_result = None

    if enable_empathy or enable_profession:
        conv_text = format_conversation_text(phase1_data.get("conversation", []))

        def _emp(): return Scorer.evaluate_multi(rubric_content=COMMUNICATION_EMPATHY, test_context=conv_text) if enable_empathy else None
        def _pro(): return Scorer.evaluate_multi(rubric_content=INTERVIEWING_PROFESSIONALISM, test_context=conv_text) if enable_profession else None

        if enable_empathy and enable_profession and parallel:
            with ThreadPoolExecutor(max_workers=2) as ex:
                f1, f2 = ex.submit(_emp), ex.submit(_pro)
                empathy_result, profession_result = f1.result(), f2.result()
        else:
            empathy_result = _emp()
            profession_result = _pro()

        if empathy_result:
            eval_data["empathy_evaluation"] = empathy_result
        if profession_result:
            eval_data["profession_evaluation"] = profession_result

    path = save_evaluation_result(model_name, case_id, 1, eval_data)
    return {"coverage_stats": coverage, "conversation_stats": conv_stats, "status": eval_data["status"], "empathy_evaluation": empathy_result, "profession_evaluation": profession_result, "output_file": str(path), "model_name": model_name, "case_id": case_id}
