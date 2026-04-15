"""
病例业务服务 - 处理病例相关的业务逻辑
"""
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from repositories.case_repository import CaseRepository

logger = logging.getLogger(__name__)


class CaseService:
    """病例业务服务"""

    def __init__(self, data_dir: Path):
        self.repository = CaseRepository(data_dir)

    def list_cases(self, keyword: str = "") -> List[Dict[str, str]]:
        """获取病例列表（支持搜索）

        Args:
            keyword: 搜索关键词

        Returns:
            病例列表
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
        """获取所有病例（加载所有病例用于兼容旧接口）"""
        return self.repository.get_all_cases()

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """获取单个病例详情"""
        return self.repository.get_case_by_id(case_id)

    def get_random_case(self, mode: str) -> Optional[Dict[str, str]]:
        """从指定模式随机抽取一个病例

        Args:
            mode: "common" 或 "rare"

        Returns:
            病例基本信息，无可用病例时返回 None
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
        """获取各模式的病例数量"""
        return self.repository.get_mode_counts()

    def get_case_for_interview(self, case_id: str) -> Optional[Dict[str, Any]]:
        """获取用于访谈的病例数据

        Returns:
            包含访谈所需字段的病例数据
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
