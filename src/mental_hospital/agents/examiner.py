"""Examiner agent — the virtual clinical examination instrument."""

from __future__ import annotations

from mental_hospital.llm.client import LLMClient
from mental_hospital.llm.factory import create_examiner_client
from mental_hospital.prompts.agents import EXAMINER_RULE


def create_examiner(
    examination_query: str,
    auxiliary_examinations: str,
    *,
    backup: bool = False,
) -> LLMClient:
    """Create a virtual examination instrument agent.

    Parameters
    ----------
    examination_query : str
        JSON array of examinations requested by the doctor,
        e.g. ``'["Brain CT", "CBC"]'``.
    auxiliary_examinations : str
        JSON object of all available examination results,
        e.g. ``'{"Brain CT": "normal", "EEG": "normal"}'``.
    backup : bool
        Use the backup API for batch-mode load balancing.
    """
    system_prompt = EXAMINER_RULE
    system_prompt = system_prompt.replace("<EXAMINATION_QUERY>", examination_query)
    system_prompt = system_prompt.replace("<AUXILIARY_EXAMINATIONS>", auxiliary_examinations)

    client = create_examiner_client(system_message=system_prompt, backup=backup)
    client.exam_info = {  # type: ignore[attr-defined]
        "examination_query": examination_query,
        "auxiliary_examinations": auxiliary_examinations,
    }
    return client
