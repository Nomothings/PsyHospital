"""Psychiatrist agent — the interviewing clinician."""

from mental_hospital.llm.client import LLMClient
from mental_hospital.llm.factory import create_psychiatrist_client
from mental_hospital.prompts.agents import PSYCHIATRIST_PROFILE


def create_psychiatrist() -> LLMClient:
    """Create a psychiatrist agent with the standard system prompt.

    Configured via ``DOCTOR_*`` environment variables.
    """
    return create_psychiatrist_client(system_message=PSYCHIATRIST_PROFILE)
