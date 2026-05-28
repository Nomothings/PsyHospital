"""Prompt templates — agent profiles, interview phases, rubrics, data."""

from mental_hospital.prompts.agents import PSYCHIATRIST_PROFILE, PATIENT_PROFILE, EXAMINER_RULE
from mental_hospital.prompts.phases import (
    HISTORY_COLLECTION,
    EXAMINATION_RECOMMENDATION,
    CLINICAL_FORMULATION,
    DEFINITIVE_DIAGNOSIS,
    TREATMENT_PLANNING,
)
from mental_hospital.prompts.rubrics import (
    RUBRIC_FORMAT,
    COMMUNICATION_EMPATHY,
    INTERVIEWING_PROFESSIONALISM,
    CLINICAL_NOTE_QUALITY,
    DIAGNOSTIC_RIGOR,
    TREATMENT_APPROPRIATENESS,
)
from mental_hospital.prompts.diagnoses import ICD11_DIAGNOSES, format_diagnosis_list

__all__ = [
    "PSYCHIATRIST_PROFILE",
    "PATIENT_PROFILE",
    "EXAMINER_RULE",
    "HISTORY_COLLECTION",
    "EXAMINATION_RECOMMENDATION",
    "CLINICAL_FORMULATION",
    "DEFINITIVE_DIAGNOSIS",
    "TREATMENT_PLANNING",
    "RUBRIC_FORMAT",
    "COMMUNICATION_EMPATHY",
    "INTERVIEWING_PROFESSIONALISM",
    "CLINICAL_NOTE_QUALITY",
    "DIAGNOSTIC_RIGOR",
    "TREATMENT_APPROPRIATENESS",
    "ICD11_DIAGNOSES",
    "format_diagnosis_list",
]
