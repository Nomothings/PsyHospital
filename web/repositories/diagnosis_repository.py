"""
Diagnosis data repository - responsible for storing diagnosis results
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from utils.sanitize import sanitize_case_id as _sanitize_case_id

logger = logging.getLogger(__name__)


class DiagnosisRepository:
    """Diagnosis data repository"""

    def __init__(self, diagnoses_dir: Path):
        self.diagnoses_dir = diagnoses_dir
        self.diagnoses_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.diagnoses_dir / "index.json"

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load diagnosis index"""
        if self._index_file.exists():
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load diagnosis index: {e}")
        return {}

    def _save_index(self, index: Dict[str, Dict[str, Any]]):
        """Save diagnosis index"""
        try:
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save diagnosis index: {e}")

    def save_diagnosis(self, case_id: str, diagnosis: Dict[str, Any]) -> bool:
        """Save diagnosis result"""
        try:
            safe_id = _sanitize_case_id(case_id)
            index = self._load_index()

            diagnosis_record = {
                "case_id": safe_id,
                "category": diagnosis.get("category", ""),
                "disease": diagnosis.get("disease", ""),
                "reason": diagnosis.get("reason", ""),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            index[safe_id] = diagnosis_record
            self._save_index(index)
            logger.info(f"Diagnosis for case {safe_id} saved")
            return True

        except Exception as e:
            logger.error(f"Failed to save diagnosis for case {case_id}: {e}")
            return False

    def get_diagnosis(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get diagnosis result"""
        index = self._load_index()
        return index.get(case_id)

    def get_all_diagnoses(self) -> List[Dict[str, Any]]:
        """Get all diagnosis results"""
        index = self._load_index()
        return list(index.values())
