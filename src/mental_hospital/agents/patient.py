"""Patient agent — the standardised psychiatric patient."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from mental_hospital.llm.client import LLMClient
from mental_hospital.llm.factory import create_patient_client
from mental_hospital.prompts.agents import PATIENT_PROFILE


def create_patient(
    basic_info: str,
    chief_complaint: List[str],
    mental_status: List[str],
    skill_file: str | None = None,
    *,
    backup: bool = False,
) -> LLMClient:
    """Create a standardised patient agent.

    Parameters
    ----------
    basic_info : str
        Patient demographic / basic information.
    chief_complaint : list[str]
        Chief complaint items forming the factual basis for answers.
    mental_status : list[str]
        Mental-status items controlling observable presentation.
    skill_file : str or None
        Path to a ``skill.md`` file with background narrative.
    backup : bool
        Use the backup API for batch-mode load balancing.
    """
    chief_complaint_json = json.dumps(chief_complaint, ensure_ascii=False)
    mental_status_json = json.dumps(mental_status, ensure_ascii=False)

    system_prompt = PATIENT_PROFILE
    system_prompt = system_prompt.replace("<BASIC_INFO>", basic_info)
    system_prompt = system_prompt.replace("<CHIEF_COMPLAINT>", chief_complaint_json)
    system_prompt = system_prompt.replace("<MENTAL_STATUS>", mental_status_json)

    skill_content = "(No skill file provided)"
    if skill_file:
        skill_path = Path(skill_file)
        if skill_path.exists():
            skill_content = skill_path.read_text(encoding="utf-8")
    system_prompt = system_prompt.replace("<PATIENT_SKILL>", skill_content)

    client = create_patient_client(system_message=system_prompt, backup=backup)
    client.case_info = {  # type: ignore[attr-defined]
        "basic_info": basic_info,
        "chief_complaint": chief_complaint,
        "mental_status": mental_status,
    }
    return client
