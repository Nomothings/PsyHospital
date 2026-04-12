"""
诊断业务服务 - 处理诊断相关的业务逻辑
"""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from repositories.diagnosis_repository import DiagnosisRepository

logger = logging.getLogger(__name__)


class DiagnosisService:
    """诊断业务服务"""

    def __init__(self, diagnoses_dir: Path):
        self.repository = DiagnosisRepository(diagnoses_dir)

    def submit_diagnosis(self, case_id: str, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """提交诊断结果

        Args:
            case_id: 病例 ID
            diagnosis: 诊断数据，包含 category, disease, reason

        Returns:
            操作结果
        """
        # 验证必填字段
        required_fields = ["category", "disease", "reason"]
        for field in required_fields:
            if not diagnosis.get(field):
                return {"status": "error", "message": f"缺少必填字段: {field}"}

        success = self.repository.save_diagnosis(case_id, diagnosis)
        if success:
            return {"status": "ok", "case_id": case_id}
        return {"status": "error", "message": "保存失败"}

    def get_diagnosis(self, case_id: str) -> Optional[Dict[str, Any]]:
        """获取诊断结果"""
        return self.repository.get_diagnosis(case_id)

    def get_all_diagnoses(self) -> List[Dict[str, Any]]:
        """获取所有诊断结果"""
        return self.repository.get_all_diagnoses()
