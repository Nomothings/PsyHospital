"""
Web application configuration module — centrally manages all path constants

All paths are derived from the project root directory, avoiding hardcoding in multiple files.
"""
from pathlib import Path

# ============================================================
# Project root directory
# ============================================================
PROJECT_ROOT = Path(__file__).parent.parent

# ============================================================
# Backend data directory (used by core module)
# ============================================================
BASE_DIR = PROJECT_ROOT
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
INTERVIEW_DIR = OUTPUT_DIR / "interview"
EVALUATION_DIR = OUTPUT_DIR / "evaluation"

# ============================================================
# Web application data directory
# ============================================================
WEB_DATA_DIR = Path(__file__).parent / "data"
WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = WEB_DATA_DIR / "logs"
RECORDS_DIR = WEB_DATA_DIR / "records"
DIAGNOSES_DIR = WEB_DATA_DIR / "diagnoses"
HISTORY_DIR = WEB_DATA_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Treatment categories (shared between frontend and backend)
# ============================================================
TREATMENT_CATEGORIES = [
    "Pharmacotherapy",
    "Psychotherapy",
    "Neuromodulation & Somatic Therapy",
    "Psychosocial Intervention & Rehabilitation",
    "Adjuvant Therapy",
]

# ============================================================
# Phase name mapping (new 5-phase pipeline)
# ============================================================
PHASE_NAMES = {
    1: "History Taking",
    2: "Examination Recommendation",
    3: "Clinical Formulation",
    4: "Definitive Diagnosis",
    5: "Treatment Planning",
}

# Backward-compatible phase names for the legacy /api/evaluate/N endpoints
# (the old frontend sends phase numbers 1-4; internally we map to the new 5-phase system)
API_PHASE_NAMES = {
    1: "History Taking",
    2: "Examination Recommendation",
    3: "Clinical Formulation & Diagnosis",
    4: "Treatment Planning",
}
