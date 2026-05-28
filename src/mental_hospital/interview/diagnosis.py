"""Phase 4: Definitive Diagnosis — select from ICD-11 candidate list."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Tuple

from mental_hospital.data.output import init_phase_output, update_phase_output
from mental_hospital.llm.client import LLMClient
from mental_hospital.prompts.diagnoses import format_diagnosis_list
from mental_hospital.prompts.phases import DEFINITIVE_DIAGNOSIS

logger = logging.getLogger(__name__)


def parse_diagnosis(response: str) -> Tuple[List[str], str]:
    """Extract (diagnosis_list, reasoning) from a doctor's response."""
    reasoning = ""
    diagnoses: List[str] = []
    try:
        m = re.search(r'(.*?)\[BEGIN_DEFINITIVE_DIAGNOSIS\]', response, re.DOTALL | re.IGNORECASE)
        if m:
            reasoning = m.group(1).strip()
        m = re.search(r'\[BEGIN_DEFINITIVE_DIAGNOSIS\](.*?)\[END_DEFINITIVE_DIAGNOSIS\]', response, re.DOTALL | re.IGNORECASE)
        if m:
            parsed = json.loads(m.group(1).strip())
            if isinstance(parsed, list):
                diagnoses = parsed
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass
    return diagnoses, reasoning


def run(doctor: LLMClient, model_name: str, case_id: str) -> Dict[str, Any]:
    """Run Phase 4: Definitive Diagnosis."""
    output_file = init_phase_output(
        model_name=model_name, case_id=case_id, phase=4,
        initial_data={"definitive_diagnosis": [], "diagnosis_reasoning": "", "raw_response": ""},
    )
    prompt = DEFINITIVE_DIAGNOSIS.replace("<ICD11_DIAGNOSIS_LIST>", format_diagnosis_list())
    doctor_response = doctor.chat(prompt)
    diagnoses, reasoning = parse_diagnosis(doctor_response)
    logger.info("Phase 4 — %d diagnosis(es)", len(diagnoses))
    update_phase_output(output_file, {
        "definitive_diagnosis": diagnoses, "diagnosis_reasoning": reasoning, "raw_response": doctor_response,
    }, status="completed")
    return {
        "definitive_diagnosis": diagnoses, "diagnosis_reasoning": reasoning,
        "raw_response": doctor_response, "output_file": str(output_file),
        "doctor": doctor, "model_name": model_name, "case_id": case_id,
    }
