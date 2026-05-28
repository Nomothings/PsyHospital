"""Phase 5 evaluation: treatment appropriateness (subjective rubric only)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from mental_hospital.data.output import get_phase_output_file, save_evaluation_result
from mental_hospital.evaluation.scorer import Scorer
from mental_hospital.prompts.rubrics import TREATMENT_APPROPRIATENESS

logger = logging.getLogger(__name__)


def evaluate(
    model_name: Optional[str] = None, case_id: Optional[str] = None,
    output_file: Optional[Union[str, Path]] = None,
    phase5_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if phase5_data is None:
        if output_file is None:
            if model_name is None or case_id is None:
                raise ValueError("Provide model_name+case_id, output_file, or phase5_data")
            output_file = get_phase_output_file(model_name, case_id, 5)
        output_file = Path(output_file)
        phase5_data = json.loads(output_file.read_text(encoding="utf-8"))
    model_name = phase5_data.get("model_name", model_name or "")
    case_id = phase5_data.get("case_id", case_id or "")
    if not model_name or not case_id:
        raise ValueError("Cannot determine model_name or case_id")

    treatment_plan = phase5_data.get("treatment_plan", "")
    status = phase5_data.get("status", "unknown")

    eval_data: Dict[str, Any] = {"status": status, "treatment_plan_length": len(treatment_plan)}
    treatment_subjective = None
    if treatment_plan and treatment_plan.strip():
        try:
            treatment_subjective = Scorer.evaluate_multi(rubric_content=TREATMENT_APPROPRIATENESS, test_context=treatment_plan)
            eval_data["treatment_subjective"] = treatment_subjective
        except Exception:
            logger.exception("Phase 5 subjective evaluation failed")

    path = save_evaluation_result(model_name, case_id, 5, eval_data)
    return {"treatment_subjective": treatment_subjective, "status": status, "output_file": str(path), "model_name": model_name, "case_id": case_id}
