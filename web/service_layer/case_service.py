"""
Case business service - handles case-related business logic
"""
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from repositories.case_repository import CaseRepository

logger = logging.getLogger(__name__)


class CaseService:
    """Case business service"""

    def __init__(self, data_dir: Path):
        self.repository = CaseRepository(data_dir)

    def list_cases(self, keyword: str = "") -> List[Dict[str, str]]:
        """Get case list (supports search)

        Args:
            keyword: Search keyword

        Returns:
            Case list
        """
        all_cases = self.repository.get_all_cases()

        if keyword:
            keyword_lower = keyword.lower()
            filtered = []
            for case in all_cases:
                basic_info = case.get("basicInfomation", "").lower()
                physical_exam = case.get("physicalExamination", "").lower()
                if keyword_lower in basic_info or keyword_lower in physical_exam:
                    filtered.append(case)
            all_cases = filtered

        return [
            {
                "id": case.get("id", ""),
                "basicInfomation": case.get("basicInfomation", ""),
                "physicalExamination": case.get("physicalExamination", ""),
            }
            for case in all_cases
        ]

    def get_all_cases(self) -> List[Dict[str, Any]]:
        """Get all cases (loads all cases for legacy API compatibility)"""
        return self.repository.get_all_cases()

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get single case details"""
        return self.repository.get_case_by_id(case_id)

    def get_random_case(self, mode: str) -> Optional[Dict[str, str]]:
        """Randomly select a case from specified mode

        Args:
            mode: "common" or "rare"

        Returns:
            Case basic info, returns None if no available cases
        """
        case = self.repository.get_random_case(mode)
        if not case:
            return None
        return {
            "id": case.get("id", ""),
            "basicInfomation": case.get("basicInfomation", ""),
            "physicalExamination": case.get("physicalExamination", ""),
        }

    def get_mode_counts(self) -> Dict[str, int]:
        """Get case counts by mode"""
        return self.repository.get_mode_counts()

    def get_case_for_interview(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get case data for interview

        Returns:
            Case data containing fields needed for interview
        """
        case = self.repository.get_case_by_id(case_id)
        if not case:
            return None

        return {
            "id": case.get("id", ""),
            "basicInfomation": case.get("basicInfomation", ""),
            "chiefComplaint": case.get("chiefComplaint", []),
            "mentalStatus": case.get("mentalStatus", []),
            "physicalExamination": case.get("physicalExamination", ""),
            "auxiliaryExamination": case.get("auxiliaryExamination", {}),
        }
