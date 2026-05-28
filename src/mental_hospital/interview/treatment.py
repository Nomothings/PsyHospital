"""Phase 5: Treatment Planning — generate complete treatment recommendations."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict

from mental_hospital.data.output import init_phase_output, update_phase_output
from mental_hospital.llm.client import LLMClient
from mental_hospital.prompts.phases import TREATMENT_PLANNING

logger = logging.getLogger(__name__)


def parse_treatment_plan(response: str) -> str:
    """Extract the treatment plan body from a doctor's response."""
    match = re.search(r'\[BEGIN_TREATMENT_PLAN\](.*?)\[END_TREATMENT_PLAN\]', response, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def run(doctor: LLMClient, model_name: str, case_id: str) -> Dict[str, Any]:
    """Run Phase 5: Treatment Planning."""
    output_file = init_phase_output(
        model_name=model_name, case_id=case_id, phase=5,
        initial_data={"treatment_plan": "", "raw_response": ""},
    )
    doctor_response = doctor.chat(TREATMENT_PLANNING)
    treatment_plan = parse_treatment_plan(doctor_response)
    logger.info("Phase 5 — treatment plan: %d chars", len(treatment_plan))
    update_phase_output(output_file, {"treatment_plan": treatment_plan, "raw_response": doctor_response}, status="completed")
    return {
        "treatment_plan": treatment_plan, "raw_response": doctor_response,
        "output_file": str(output_file), "doctor": doctor,
        "model_name": model_name, "case_id": case_id,
    }
