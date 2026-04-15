"""
问诊记录数据仓库 - 负责问诊过程记录的持久化存储
每次问诊会话使用一个 JSON 文件，同一次会话的所有阶段数据合并到同一文件
"""
import re
import os
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


class RecordRepository:
    """问诊记录数据仓库 - 使用 JSON 文件持久化存储"""

    def __init__(self, records_dir: Path):
        self.records_dir = records_dir
        self.records_dir.mkdir(parents=True, exist_ok=True)

    def _get_record_path(self, case_id: str) -> Path:
        """获取病例记录文件路径（带路径穿越防护）"""
        safe_id = _sanitize_case_id(case_id)
        return self.records_dir / f"{safe_id}.json"

    def save_record(self, case_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """保存或更新问诊记录。每次问诊会话一个文件，同一次会话的所有阶段数据合并到同一文件。

        Args:
            case_id: 问诊记录 ID（record_id，如 1009904_20260415_143022，用作文件名）
            record: 记录数据，包含 caseInfo, conversation, exams, caseForm, diagnosis, treatment 等

        Returns:
            包含 record_id 的结果字典
        """
        try:
            record_path = self._get_record_path(case_id)

            # 如果文件已存在，合并更新（所有阶段数据合并到同一文件）
            existing = {}
            if record_path.exists():
                with open(record_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)

            # 合并数据（新数据覆盖旧数据）
            merged = {**existing, **record}
            merged["case_id"] = case_id
            merged["updated_at"] = datetime.now().isoformat()

            # 如果是首次创建，添加创建时间
            if "created_at" not in merged:
                merged["created_at"] = merged["updated_at"]

            # 从 record_id 提取原始 case_id（格式：{case_id}_{YYYYMMDD}_{HHMMSS}_{suffix} 或旧格式）
            if "original_case_id" not in merged:
                parts = case_id.rsplit("_", 2)
                # 新格式：{case_id}_{YYYYMMDD}_{HHMMSS}_{suffix} -> 3+ parts
                if len(parts) >= 3 and len(parts[1]) == 8:
                    merged["original_case_id"] = parts[0]
                else:
                    merged["original_case_id"] = case_id

            with open(record_path, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)

            logger.info(f"记录 {case_id} 已保存（合并模式）")
            return {"status": "ok", "record_id": case_id}

        except Exception as e:
            logger.error(f"保存病例 {case_id} 记录失败: {e}")
            return {"status": "error", "message": str(e)}

    def get_record(self, case_id: str) -> Optional[Dict[str, Any]]:
        """获取病例的问诊记录

        Args:
            case_id: 病例 ID

        Returns:
            记录数据，不存在则返回 None
        """
        record_path = self._get_record_path(case_id)
        if not record_path.exists():
            return None

        try:
            with open(record_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取病例 {case_id} 记录失败: {e}")
            return None

    def get_records_by_case(self, case_id: str) -> List[Dict[str, Any]]:
        """获取某患者的所有问诊记录（当前实现每个病例只有一个文件）"""
        record = self.get_record(case_id)
        if record:
            return [record]
        return []

    def delete_record(self, case_id: str) -> bool:
        """删除问诊记录"""
        record_path = self._get_record_path(case_id)
        if record_path.exists():
            try:
                record_path.unlink()
                logger.info(f"病例 {case_id} 记录已删除")
                return True
            except Exception as e:
                logger.error(f"删除病例 {case_id} 记录失败: {e}")
                return False
        return False

    def list_all_records(self) -> List[Dict[str, str]]:
        """列出所有记录的基本信息"""
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
                logger.warning(f"读取记录文件 {record_file} 失败: {e}")
        # 按更新时间倒序
        records.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return records
