"""
Case data repository — loads cases via the mental_hospital package and
normalises them to the format expected by the frontend service layer.
"""
from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from mental_hospital.data.loader import load_all_cases, load_random_case as _load_random_from_pkg

logger = logging.getLogger(__name__)

MODE_COMMON = "common"
MODE_RARE = "rare"


def _flatten_raw_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten ``realFormulation`` fields to top-level keys, matching the
    behaviour of ``mental_hospital.data.loader._normalize()`` (which is
    only called by ``load_random_case``, not ``load_all_cases``)."""
    raw = dict(case)
    rf = raw.get("realFormulation")
    if isinstance(rf, dict):
        raw.setdefault("chiefComplaint", rf.get("chiefComplaint", []))
        raw.setdefault("mentalStatus", rf.get("mentalStatus", []))
        raw.setdefault("physicalExamination", rf.get("physicalExamination", []))
        raw.setdefault("auxiliaryExamination", rf.get("auxiliaryExamination", []))
        raw.setdefault("pastHistory", rf.get("pastHistory", []))
        raw.setdefault("familyHistory", rf.get("familyHistory", []))
        raw.setdefault("medicationHistory", rf.get("medicationHistory", []))
    return raw


def _normalize_case_format(case: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise new-format case data to the format expected by the frontend.

    The mental_hospital loader already flattens ``realFormulation`` fields
    to top-level keys.  This function additionally converts:

    * ``physicalExamination``: list → semicolon-joined string
    * ``auxiliaryExamination``: list → dict  (parses ``"name: result"`` lines)
    """
    result = dict(case)

    pe = result.get("physicalExamination")
    if isinstance(pe, list):
        result["physicalExamination"] = "；".join(str(item).strip() for item in pe)

    aux = result.get("auxiliaryExamination")
    if isinstance(aux, list):
        aux_dict: Dict[str, str] = {}
        for item in aux:
            item_str = str(item).strip()
            if ":" in item_str:
                k, v = item_str.split(":", 1)
                aux_dict[k.strip()] = v.strip()
            elif "：" in item_str:
                k, v = item_str.split("：", 1)
                aux_dict[k.strip()] = v.strip()
            else:
                aux_dict[item_str] = "unlabeled"
        result["auxiliaryExamination"] = aux_dict

    return result


class CaseRepository:
    """Case data repository backed by ``mental_hospital.data.loader``."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._cases_cache: Optional[List[Dict[str, Any]]] = None
        self._cases_by_id: Optional[Dict[str, Dict[str, Any]]] = None

    # ------------------------------------------------------------------
    # Public API (same signatures as the old repository)
    # ------------------------------------------------------------------

    def get_all_cases(self) -> List[Dict[str, Any]]:
        if self._cases_cache is None:
            raw = load_all_cases()
            self._cases_cache = [_normalize_case_format(_flatten_raw_case(c)) for c in raw]
            logger.info("Loaded %d cases via mental_hospital.data.loader", len(self._cases_cache))
        return self._cases_cache

    def get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        if self._cases_by_id is None:
            self._cases_by_id = {c.get("id"): c for c in self.get_all_cases()}
        return self._cases_by_id.get(case_id)

    def get_cases_by_mode(self, mode: str) -> List[Dict[str, Any]]:
        """Return cases for the given *mode*.

        The new dataset does not have a common / rare split, so all cases
        are returned regardless of mode.
        """
        return self.get_all_cases()

    def get_random_case(self, mode: str) -> Optional[Dict[str, Any]]:
        cases = self.get_cases_by_mode(mode)
        if not cases:
            logger.warning("No cases available (mode=%s)", mode)
            return None
        return random.choice(cases)

    def get_case_basic_info(self, case_id: str) -> Optional[Dict[str, str]]:
        case = self.get_case_by_id(case_id)
        if not case:
            return None
        return {
            "id": case.get("id", ""),
            "basicInfomation": case.get("basicInfomation", ""),
            "physicalExamination": case.get("physicalExamination", ""),
        }

    def get_mode_counts(self) -> Dict[str, int]:
        total = len(self.get_all_cases())
        return {MODE_COMMON: total, MODE_RARE: 0}

    def invalidate_cache(self) -> None:
        self._cases_cache = None
        self._cases_by_id = None
        logger.info("Case cache cleared")
