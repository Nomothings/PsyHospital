"""Phase 2: Examination Recommendation — doctor recommends, instrument returns."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

from mental_hospital.agents.examiner import create_examiner
from mental_hospital.data.output import init_phase_output, update_phase_output
from mental_hospital.llm.client import LLMClient
from mental_hospital.prompts.phases import EXAMINATION_RECOMMENDATION

logger = logging.getLogger(__name__)


def parse_examinations(response: str) -> List[str]:
    """Extract examination list from a doctor's response."""
    match = re.search(r'\[BEGIN_EXAMINATIONS\](.*?)\[END_EXAMINATIONS\]', response, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    try:
        parsed = json.loads(match.group(1).strip())
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if item]
    except (json.JSONDecodeError, AttributeError):
        pass
    return []


def run(
    doctor: LLMClient, model_name: str, case_id: str,
    case_data: Dict[str, Any] | None = None, *, instrument_backup: bool = False,
) -> Dict[str, Any]:
    """Run Phase 2: Examination Recommendation."""
    output_file = init_phase_output(
        model_name=model_name, case_id=case_id, phase=2,
        initial_data={"examinations": [], "examination_results": {}, "raw_response": ""},
    )
    doctor_response = doctor.chat(EXAMINATION_RECOMMENDATION)
    examinations = parse_examinations(doctor_response)
    logger.info("Phase 2 — %d examination(s) recommended", len(examinations))
    update_phase_output(output_file, {"examinations": examinations, "raw_response": doctor_response})

    examination_results: Dict[str, Any] = {}
    if case_data and examinations:
        aux = case_data.get("auxiliaryExamination", {})
        if aux:
            try:
                examiner = create_examiner(
                    examination_query=json.dumps(examinations, ensure_ascii=False),
                    auxiliary_examinations=json.dumps(aux, ensure_ascii=False),
                    backup=instrument_backup,
                )
                raw = examiner.chat("Please return the examination results based on the above information.")
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(parsed, dict):
                    examination_results = parsed
                update_phase_output(output_file, {"examination_results": examination_results}, status="completed")
            except Exception:
                logger.exception("Examiner call failed")
                update_phase_output(output_file, {}, status="completed_with_error")
        else:
            update_phase_output(output_file, {}, status="completed_no_gold")
    else:
        update_phase_output(output_file, {}, status="completed")

    return {
        "examinations": examinations, "examination_results": examination_results,
        "raw_response": doctor_response, "output_file": str(output_file),
        "doctor": doctor, "model_name": model_name, "case_id": case_id,
    }
