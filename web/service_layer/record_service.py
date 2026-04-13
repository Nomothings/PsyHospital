"""
问诊记录业务服务 - 处理问诊过程记录的业务逻辑
"""
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from repositories.record_repository import RecordRepository

logger = logging.getLogger(__name__)


class RecordService:
    """问诊记录业务服务"""

    def __init__(self, records_dir: Path):
        self.repository = RecordRepository(records_dir)

    def save_record(self, case_id: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """保存问诊记录

        Args:
            case_id: 病例 ID
            record_data: 记录数据

        Returns:
            操作结果，包含 record_id
        """
        result = self.repository.save_record(case_id, record_data)
        return result

    def get_record(self, case_id: str) -> Optional[Dict[str, Any]]:
        """获取问诊记录"""
        return self.repository.get_record(case_id)
