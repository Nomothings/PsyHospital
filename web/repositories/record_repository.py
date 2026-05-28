"""
Consultation record data repository - responsible for persistent storage of consultation process records
Each consultation session uses one JSON file, all phase data from the same session merged into one file
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from utils.sanitize import sanitize_case_id as _sanitize_case_id

logger = logging.getLogger(__name__)


class RecordRepository:
    """Consultation record data repository - uses JSON file persistent storage"""

    def __init__(self, records_dir: Path):
        self.records_dir = records_dir
        self.records_dir.mkdir(parents=True, exist_ok=True)

    def _get_record_path(self, case_id: str) -> Path:
        """Get case record file path (with path traversal protection)"""
        safe_id = _sanitize_case_id(case_id)
        return self.records_dir / f"{safe_id}.json"

    def save_record(self, case_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update consultation record. One file per consultation session, all phase data from the same session merged into one file.

        Args:
            case_id: Consultation record ID (record_id, e.g. 1009904_20260415_143022, used as filename)
            record: Record data, containing caseInfo, conversation, exams, caseForm, diagnosis, treatment, etc.

        Returns:
            Result dictionary containing record_id
        """
        try:
            record_path = self._get_record_path(case_id)

            # If file already exists, merge update (all phase data merged into one file)
            existing = {}
            if record_path.exists():
                with open(record_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)

            # Merge data (new data overwrites old data)
            merged = {**existing, **record}
            merged["case_id"] = case_id
            merged["updated_at"] = datetime.now().isoformat()

            # If first creation, add creation time
            if "created_at" not in merged:
                merged["created_at"] = merged["updated_at"]

            # Extract original case_id from record_id (format: {case_id}_{YYYYMMDD}_{HHMMSS}_{suffix} or legacy format)
            if "original_case_id" not in merged:
                parts = case_id.rsplit("_", 2)
                # New format: {case_id}_{YYYYMMDD}_{HHMMSS}_{suffix} -> 3+ parts
                if len(parts) >= 3 and len(parts[1]) == 8:
                    merged["original_case_id"] = parts[0]
                else:
                    merged["original_case_id"] = case_id

            with open(record_path, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)

            logger.info(f"Record {case_id} saved (merge mode)")
            return {"status": "ok", "record_id": case_id}

        except Exception as e:
            logger.error(f"Failed to save record for case {case_id}: {e}")
            return {"status": "error", "message": str(e)}

    def get_record(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get consultation record for a case

        Args:
            case_id: Case ID

        Returns:
            Record data, returns None if not found
        """
        record_path = self._get_record_path(case_id)
        if not record_path.exists():
            return None

        try:
            with open(record_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read record for case {case_id}: {e}")
            return None

    def get_records_by_case(self, case_id: str) -> List[Dict[str, Any]]:
        """Get all consultation records for a patient (current implementation has one file per case)"""
        record = self.get_record(case_id)
        if record:
            return [record]
        return []

    def delete_record(self, case_id: str) -> bool:
        """Delete consultation record"""
        record_path = self._get_record_path(case_id)
        if record_path.exists():
            try:
                record_path.unlink()
                logger.info(f"Record for case {case_id} deleted")
                return True
            except Exception as e:
                logger.error(f"Failed to delete record for case {case_id}: {e}")
                return False
        return False

    def list_all_records(self) -> List[Dict[str, str]]:
        """List basic info of all records"""
        records = []
        for record_file in self.records_dir.glob("*.json"):
            try:
                with open(record_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                records.append({
                    "record_id": data.get("record_id", record_file.stem),
                    "case_id": data.get("case_id", ""),
                    "created_at": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", ""),
                    "has_diagnosis": bool(data.get("diagnosis")),
                    "has_conversation": bool(data.get("conversation")),
                })
            except Exception as e:
                logger.warning(f"Failed to read record file {record_file}: {e}")
        # Sorted by update time descending
        records.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return records
