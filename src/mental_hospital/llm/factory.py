"""Factory functions for creating role-specific LLM clients."""

from mental_hospital.config import settings
from mental_hospital.llm.client import LLMClient


def create_psychiatrist_client(system_message: str = "") -> LLMClient:
    """LLM client configured for the psychiatrist (doctor) agent."""
    return LLMClient(config=settings.doctor, system_message=system_message)


def create_patient_client(system_message: str = "", *, backup: bool = False) -> LLMClient:
    """LLM client for the patient agent.  Pass ``backup=True`` for batch
    load-balancing via the backup API config."""
    cfg = settings.patient_backup if backup and settings.patient_backup else settings.patient
    return LLMClient(config=cfg, system_message=system_message)


def create_examiner_client(system_message: str = "", *, backup: bool = False) -> LLMClient:
    """LLM client for the examiner (instrument) agent."""
    cfg = (
        settings.instrument_backup
        if backup and settings.instrument_backup
        else settings.instrument
    )
    return LLMClient(config=cfg, system_message=system_message)


def create_evaluator_client(system_message: str = "", *, evaluator_id: int = 1) -> LLMClient:
    """LLM client for one of the five evaluator judges (1-indexed)."""
    cfg = settings.get_evaluator_config(evaluator_id)
    return LLMClient(config=cfg, system_message=system_message)
