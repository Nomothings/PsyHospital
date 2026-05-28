"""Unified configuration loaded from environment variables.

Usage::

    from mental_hospital.config import settings
    print(settings.doctor.model)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from mental_hospital.config.constants import (
    DEFAULT_CONCURRENCY,
    DEFAULT_MAX_TURNS,
    MAX_HISTORY_MESSAGES,
    NUM_EVALUATORS,
)

_ENV_PATH = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _env_int(key: str, default: int) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(_env(key, str(default)))
    except ValueError:
        return default


# ---------------------------------------------------------------------------
# Agent API config
# ---------------------------------------------------------------------------

@dataclass
class AgentConfig:
    """API credentials + model parameters for one LLM-backed agent."""

    api_base: str
    api_key: str
    model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 1.0
    timeout: float = 30.0

    @classmethod
    def from_env(cls, role: str) -> "AgentConfig":
        prefix = role.upper()
        return cls(
            api_base=_env(f"{prefix}_API_BASE"),
            api_key=_env(f"{prefix}_API_KEY"),
            model=_env(f"{prefix}_MODEL", "gpt-4o"),
            max_tokens=_env_int(f"{prefix}_MAX_TOKENS", _env_int("MAX_TOKENS", 4096)),
            temperature=_env_float(f"{prefix}_TEMPERATURE", _env_float("TEMPERATURE", 1.0)),
            timeout=_env_float(f"{prefix}_TIMEOUT", _env_float("TIMEOUT", 30.0)),
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_base and self.api_key)

    @property
    def uses_baichuan(self) -> bool:
        return "baichuan" in self.model.lower()

    @property
    def uses_qwen(self) -> bool:
        return self.model.lower().startswith("qwen")


# ---------------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------------

@dataclass
class Settings:
    """Top-level configuration aggregating all agent configs."""

    doctor: AgentConfig
    patient: AgentConfig
    patient_backup: Optional[AgentConfig]
    instrument: AgentConfig
    instrument_backup: Optional[AgentConfig]
    evaluators: list[AgentConfig] = field(default_factory=list)
    fallback_evaluator: AgentConfig = field(default_factory=lambda: AgentConfig("", "", "gpt-4o"))

    max_turns: int = DEFAULT_MAX_TURNS
    max_history_messages: int = MAX_HISTORY_MESSAGES
    num_evaluators: int = NUM_EVALUATORS
    concurrency: int = DEFAULT_CONCURRENCY

    @classmethod
    def from_env(cls) -> "Settings":
        doctor = AgentConfig.from_env("DOCTOR")
        patient = AgentConfig.from_env("PATIENT")
        pb = AgentConfig.from_env("PATIENT_BACKUP")
        instrument = AgentConfig.from_env("INSTRUMENT")
        ib = AgentConfig.from_env("INSTRUMENT_BACKUP")

        evaluators: list[AgentConfig] = []
        for i in range(1, 6):
            ec = AgentConfig.from_env(f"EVALUATOR_{i}")
            if not ec.is_configured:
                ec = AgentConfig.from_env("EVALUATOR")
            evaluators.append(ec)

        return cls(
            doctor=doctor,
            patient=patient,
            patient_backup=pb if pb.is_configured else None,
            instrument=instrument,
            instrument_backup=ib if ib.is_configured else None,
            evaluators=evaluators,
            fallback_evaluator=AgentConfig.from_env("EVALUATOR"),
            max_turns=_env_int("MAX_TURNS", DEFAULT_MAX_TURNS),
        )

    def get_evaluator_config(self, evaluator_id: int) -> AgentConfig:
        idx = evaluator_id - 1
        if 0 <= idx < len(self.evaluators):
            return self.evaluators[idx]
        return self.fallback_evaluator

    def get_evaluator_model_name(self, evaluator_id: int) -> str:
        return self.get_evaluator_config(evaluator_id).model


# Singleton — import this everywhere.
settings = Settings.from_env()
