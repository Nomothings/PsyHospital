"""
病例数据仓库 - 负责病例数据的加载和缓存
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class CaseRepository:
    """病例数据仓库"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._cases_cache: Optional[List[Dict[str, Any]]] = None
        self._cases_by_id: Optional[Dict[str, Dict[str, Any]]] = None

    def _load_cases(self) -> List[Dict[str, Any]]:
        """从 cases.jsonl 加载所有病例"""
        cases_file = self.data_dir / "cases.jsonl"
        if not cases_file.exists():
            logger.error(f"病例文件不存在: {cases_file}")
            return []

        cases = []
        with open(cases_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    case = json.loads(line)
                    cases.append(case)
                except json.JSONDecodeError as e:
                    logger.warning(f"病例文件第 {line_num} 行解析失败: {e}")
        return cases

    def get_all_cases(self) -> List[Dict[str, Any]]:
        """获取所有病例（带缓存）"""
        if self._cases_cache is None:
            self._cases_cache = self._load_cases()
            logger.info(f"已加载 {len(self._cases_cache)} 个病例")
        return self._cases_cache

    def get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取病例"""
        if self._cases_by_id is None:
            self._cases_by_id = {c.get("id"): c for c in self.get_all_cases()}
        return self._cases_by_id.get(case_id)

    def get_case_basic_info(self, case_id: str) -> Optional[Dict[str, str]]:
        """获取病例的基本展示信息"""
        case = self.get_case_by_id(case_id)
        if not case:
            return None
        return {
            "id": case.get("id", ""),
            "basicInfomation": case.get("basicInfomation", ""),
            "physicalExamination": case.get("physicalExamination", ""),
        }

    def invalidate_cache(self):
        """清除缓存（用于数据更新后）"""
        self._cases_cache = None
        self._cases_by_id = None
        logger.info("病例缓存已清除")
