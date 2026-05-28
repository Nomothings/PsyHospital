"""Phase 3: Clinical Formulation — synthesise a structured clinical note."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict

from mental_hospital.data.output import init_phase_output, update_phase_output
from mental_hospital.llm.client import LLMClient
from mental_hospital.prompts.phases import CLINICAL_FORMULATION
from mental_hospital.utils.text_utils import format_examination_results

logger = logging.getLogger(__name__)


def parse_formulation(response: str) -> str:
    """Extract the clinical note body from a doctor's response."""
    match = re.search(r'\[BEGIN_CLINICAL_FORMULATION\](.*?)\[END_CLINICAL_FORMULATION\]', response, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def run(
    doctor: LLMClient, model_name: str, case_id: str, examination_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Run Phase 3: Clinical Formulation."""
    output_file = init_phase_output(
        model_name=model_name, case_id=case_id, phase=3,
        initial_data={"syntactic_formulation": "", "raw_response": ""},
    )
    prompt = CLINICAL_FORMULATION.replace("<EXAMINATIONS_RESULTS>", format_examination_results(examination_results))
    doctor_response = doctor.chat(prompt)
    formulation = parse_formulation(doctor_response)
    logger.info("Phase 3 — clinical note: %d chars", len(formulation))
    update_phase_output(output_file, {"syntactic_formulation": formulation, "raw_response": doctor_response}, status="completed")
    return {
        "syntactic_formulation": formulation, "raw_response": doctor_response,
        "output_file": str(output_file), "doctor": doctor,
        "model_name": model_name, "case_id": case_id,
    }
