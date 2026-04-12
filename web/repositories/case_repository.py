"""
病例数据仓库 - 负责病例数据的加载和缓存

数据分层结构:
    data/cases/common/  - 常规病例库
    data/cases/rare/    - 罕见病例库
"""
import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# 病例模式常量
MODE_COMMON = "common"
MODE_RARE = "rare"

# 目录 -> 文件模式映射
CASE_DIR_MAP = {
    MODE_COMMON: "common",
    MODE_RARE: "rare",
}


class CaseRepository:
    """病例数据仓库"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.cases_dir = data_dir / "cases"
        self._cases_cache: Optional[List[Dict[str, Any]]] = None
        self._cases_by_id: Optional[Dict[str, Dict[str, Any]]] = None

    def _load_cases_from_dir(self, subdir: str) -> List[Dict[str, Any]]:
        """从指定子目录加载所有病例"""
        dir_path = self.cases_dir / subdir
        if not dir_path.exists():
            logger.warning(f"病例目录不存在: {dir_path}")
            return []

        cases = []
        for cases_file in sorted(dir_path.glob("*.jsonl")):
            with open(cases_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        case = json.loads(line)
                        cases.append(case)
                    except json.JSONDecodeError as e:
                        logger.warning(f"{cases_file.name} 第 {line_num} 行解析失败: {e}")
        return cases

    def _load_cases(self) -> List[Dict[str, Any]]:
        """从 common/ 和 rare/ 子目录加载所有病例"""
        all_cases = []
        for subdir in CASE_DIR_MAP.values():
            cases = self._load_cases_from_dir(subdir)
            all_cases.extend(cases)
        return all_cases

    def get_cases_by_mode(self, mode: str) -> List[Dict[str, Any]]:
        """获取指定模式的病例列表"""
        subdir = CASE_DIR_MAP.get(mode)
        if not subdir:
            logger.error(f"未知病例模式: {mode}")
            return []
        return self._load_cases_from_dir(subdir)

    def get_random_case(self, mode: str) -> Optional[Dict[str, Any]]:
        """从指定模式随机抽取一个病例"""
        cases = self.get_cases_by_mode(mode)
        if not cases:
            logger.warning(f"{mode} 模式下没有可用病例")
            return None
        return random.choice(cases)

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

    def get_mode_counts(self) -> Dict[str, int]:
        """获取各模式的病例数量"""
        counts = {}
        for mode, subdir in CASE_DIR_MAP.items():
            cases = self._load_cases_from_dir(subdir)
            counts[mode] = len(cases)
        return counts

    def invalidate_cache(self):
        """清除缓存（用于数据更新后）"""
        self._cases_cache = None
        self._cases_by_id = None
        logger.info("病例缓存已清除")
