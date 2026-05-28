"""
Consultation record business service - handles consultation record business logic
"""
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from repositories.record_repository import RecordRepository

logger = logging.getLogger(__name__)


class RecordService:
    """Consultation record business service"""

    def __init__(self, records_dir: Path):
        self.repository = RecordRepository(records_dir)

    def save_record(self, case_id: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save consultation record

        Args:
            case_id: Case ID
            record_data: Record data

        Returns:
            Operation result, containing record_id
        """
        result = self.repository.save_record(case_id, record_data)
        return result

    def get_record(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get consultation record"""
        return self.repository.get_record(case_id)
