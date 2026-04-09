"""
输出文件管理模块 - 统一管理各阶段的输出文件路径

文件结构:
    data/output/interview/{model_name}/{case_id}/
        ├── interview_phase1_output.json
        ├── interview_phase2_output.json
        ├── interview_phase3_output.json
        ├── interview_phase4_output.json
        ├── interview_phase5_output.json
        └── interview_phase6_output.json
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


def get_output_dir(model_name: str, case_id: str) -> Path:
    """获取输出目录路径
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        
    Returns:
        输出目录路径
    """
    output_dir = Path(__file__).parent.parent / "data" / "output" / "interview" / model_name / case_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_phase_output_file(model_name: str, case_id: str, phase: int) -> Path:
    """获取指定阶段的输出文件路径
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        phase: 阶段编号 (1-6)
        
    Returns:
        输出文件路径
    """
    output_dir = get_output_dir(model_name, case_id)
    return output_dir / f"interview_phase{phase}_output.json"


def init_phase_output(
    model_name: str,
    case_id: str,
    phase: int,
    initial_data: Dict[str, Any]
) -> Path:
    """初始化阶段输出文件
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        phase: 阶段编号 (1-6)
        initial_data: 初始数据
        
    Returns:
        输出文件路径
    """
    output_file = get_phase_output_file(model_name, case_id, phase)
    
    # 添加元数据
    data = {
        "phase": phase,
        "case_id": case_id,
        "model_name": model_name,
        "timestamp": datetime.now().isoformat(),
        "status": "running",
        **initial_data
    }
    
    # 立即写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return output_file


def update_phase_output(
    output_file: Path,
    updates: Dict[str, Any],
    status: str = None
):
    """更新阶段输出文件（即时写入）
    
    Args:
        output_file: 输出文件路径
        updates: 要更新的数据
        status: 可选，更新状态
    """
    # 读取现有数据
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 更新数据
    data.update(updates)
    
    # 更新时间戳
    data["last_update"] = datetime.now().isoformat()
    
    # 更新状态
    if status:
        data["status"] = status
    
    # 立即写回文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_conversation(
    output_file: Path,
    role: str,
    content: str,
    chief_complaint_used: List[str] = None,
    mental_status_used: List[str] = None
):
    """追加对话记录（Phase 1专用，即时写入）
    
    Args:
        output_file: 输出文件路径
        role: 角色 (doctor/patient/system)
        content: 对话内容
        chief_complaint_used: 本轮使用的主诉条目
        mental_status_used: 本轮使用的精神状态条目
    """
    # 读取现有数据
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 确保 conversation 字段存在
    if "conversation" not in data:
        data["conversation"] = []
    
    # 追加对话
    data["conversation"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })
    
    # 更新使用的主诉和精神状态（去重）
    if chief_complaint_used:
        if "chief_complaint_used" not in data:
            data["chief_complaint_used"] = []
        existing = set(data["chief_complaint_used"])
        existing.update(chief_complaint_used)
        data["chief_complaint_used"] = list(existing)
    
    if mental_status_used:
        if "mental_status_used" not in data:
            data["mental_status_used"] = []
        existing = set(data["mental_status_used"])
        existing.update(mental_status_used)
        data["mental_status_used"] = list(existing)
    
    # 更新时间戳
    data["last_update"] = datetime.now().isoformat()
    
    # 立即写回文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_phase_output(model_name: str, case_id: str, phase: int) -> Optional[Dict[str, Any]]:
    """加载指定阶段的输出数据
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        phase: 阶段编号 (1-6)
        
    Returns:
        输出数据，如果文件不存在返回None
    """
    output_file = get_phase_output_file(model_name, case_id, phase)
    
    if not output_file.exists():
        return None
    
    with open(output_file, "r", encoding="utf-8") as f:
        return json.load(f)
