"""
诊断数据仓库 - 负责诊断结果的存储
"""
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _sanitize_case_id(case_id: str) -> str:
    """防止路径穿越：只允许字母、数字、下划线、连字符、点"""
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', case_id):
        raise ValueError(f"非法的 case_id: {case_id}")
    return case_id


class DiagnosisRepository:
    """诊断数据仓库"""

    def __init__(self, diagnoses_dir: Path):
        self.diagnoses_dir = diagnoses_dir
        self.diagnoses_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.diagnoses_dir / "index.json"

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """加载诊断索引"""
        if self._index_file.exists():
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"诊断索引加载失败: {e}")
        return {}

    def _save_index(self, index: Dict[str, Dict[str, Any]]):
        """保存诊断索引"""
        try:
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"诊断索引保存失败: {e}")

    def save_diagnosis(self, case_id: str, diagnosis: Dict[str, Any]) -> bool:
        """保存诊断结果"""
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
            logger.info(f"病例 {safe_id} 诊断已保存")
            return True

        except Exception as e:
            logger.error(f"保存病例 {case_id} 诊断失败: {e}")
            return False

    def get_diagnosis(self, case_id: str) -> Optional[Dict[str, Any]]:
        """获取诊断结果"""
        index = self._load_index()
        return index.get(case_id)

    def get_all_diagnoses(self) -> List[Dict[str, Any]]:
        """获取所有诊断结果"""
        index = self._load_index()
        return list(index.values())
