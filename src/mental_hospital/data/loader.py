"""Case and patient-data loading utilities."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

CASES_FILE = _PROJECT_ROOT / "data" / "cases.jsonl"
DATA_PATIENT_DIR = _PROJECT_ROOT / "data" / "data_patient"
MAPPING_FILE = _PROJECT_ROOT / "data" / "mapping.json"


def load_all_cases() -> List[Dict[str, Any]]:
    cases: list[Dict[str, Any]] = []
    if not CASES_FILE.exists():
        return cases
    with open(CASES_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return cases


def load_case_by_id(case_id: str) -> Optional[Dict[str, Any]]:
    for case in load_all_cases():
        if case.get("id") == case_id:
            return case
    return None


def load_random_case(case_id: Optional[str] = None) -> Dict[str, Any]:
    cases = load_all_cases()
    if not cases:
        raise FileNotFoundError(f"No cases found in {CASES_FILE}")
    if case_id is not None:
        for c in cases:
            if c.get("id") == case_id:
                return _normalize(c)
        raise ValueError(f"Case ID not found: {case_id}")
    return _normalize(random.choice(cases))


def _normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    rf = raw.get("realFormulation")
    if isinstance(rf, dict):
        return {
            "id": raw.get("id", "unknown"),
            "basicInfomation": raw.get("basicInfomation", ""),
            "chiefComplaint": rf.get("chiefComplaint", []),
            "mentalStatus": rf.get("mentalStatus", []),
            "physicalExamination": rf.get("physicalExamination", []),
            "auxiliaryExamination": rf.get("auxiliaryExamination", []),
            "pastHistory": rf.get("pastHistory", []),
            "familyHistory": rf.get("familyHistory", []),
            "medicationHistory": rf.get("medicationHistory", []),
            "realCategory": raw.get("realCategory", []),
            "realDisorder": raw.get("realDisorder", []),
        }
    return raw


def get_patient_dirs(case_id: str) -> tuple[Path, Path]:
    base = DATA_PATIENT_DIR / case_id
    return base / "skill.md", base / "experience"


def load_mapping() -> Dict[str, List[str]]:
    if not MAPPING_FILE.exists():
        return {}
    with open(MAPPING_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)
