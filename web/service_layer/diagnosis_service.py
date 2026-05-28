"""
Diagnosis business service - handles diagnosis-related business logic
"""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from repositories.diagnosis_repository import DiagnosisRepository

logger = logging.getLogger(__name__)


class DiagnosisService:
    """Diagnosis business service"""

    def __init__(self, diagnoses_dir: Path):
        self.repository = DiagnosisRepository(diagnoses_dir)

    def submit_diagnosis(self, case_id: str, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """Submit diagnosis result

        Args:
            case_id: Case ID
            diagnosis: Diagnosis data, containing category, disease, reason

        Returns:
            Operation result
        """
        # Validate required fields
        required_fields = ["category", "disease", "reason"]
        for field in required_fields:
            if not diagnosis.get(field):
                return {"status": "error", "message": f"Missing required field: {field}"}

        success = self.repository.save_diagnosis(case_id, diagnosis)
        if success:
            return {"status": "ok", "case_id": case_id}
        return {"status": "error", "message": "Save failed"}

    def get_diagnosis(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get diagnosis result"""
        return self.repository.get_diagnosis(case_id)

    def get_all_diagnoses(self) -> List[Dict[str, Any]]:
        """Get all diagnosis results"""
        return self.repository.get_all_diagnoses()
