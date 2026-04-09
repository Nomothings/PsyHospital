"""
精神科访谈执行模块 - 第一阶段：Clinical History Collection

使用方法:
    # 方式1：单独测试第一阶段
    python core/interview_phase1.py
    
    # 方式2：导入并运行（供完整流程调用）
    from core.interview_phase1 import run_interview_phase1
    
    result = run_interview_phase1()
    
    # 结果包含:
    # - case_id: 病例ID
    # - conversation: 对话记录
    # - chief_complaint_used: 使用的主诉条目（去重）
    # - mental_status_used: 使用的精神状态条目（去重）
    # - coverage_stats: 覆盖率统计
    # - output_file: 保存的文件路径
    # - status: 完成状态
    # - doctor: 医生LLM实例（用于传递到下一阶段，保持对话上下文）
    # - case_data: 完整病例数据（用于后续阶段）
"""

import sys
import json
import random
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from agents.doctor.doctor import create_doctor
from agents.patient.patient import create_patient
from core.interview.prompts import PROMPTS
from core.output_manager import (
    init_phase_output,
    append_conversation,
    update_phase_output,
    get_phase_output_file
)

# 尝试导入json_repair
try:
    from json_repair import repair_json
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False
    repair_json = None

# 加载.env
load_dotenv(Path(__file__).parent.parent / ".env")

# 读取配置
MAX_TURNS = int(os.getenv("MAX_TURNS", "50"))


def load_random_case(cases_file: Path = None) -> Dict[str, Any]:
    """从cases.jsonl随机加载一个病例
    
    Returns:
        病例字典，包含所有字段
    """
    if cases_file is None:
        cases_file = Path(__file__).parent.parent.parent / "data" / "cases.jsonl"
    
    cases = []
    with open(cases_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                case = json.loads(line)
                cases.append(case)
            except json.JSONDecodeError:
                continue
    
    if not cases:
        raise ValueError("未找到任何病例数据")
    
    return random.choice(cases)


def parse_patient_response(response: str) -> Tuple[str, List[str], List[str]]:
    """解析患者响应（增强容错）
    
    Args:
        response: 患者的JSON格式响应
        
    Returns:
        (patient_response, chief_complaint_list, mental_status_list)
        - patient_response: presentation + utterance 拼接的字符串
        - chief_complaint_list: 使用的主诉条目列表
        - mental_status_list: 使用的精神状态条目列表
    """
    # 尝试解析JSON
    data = None
    
    # 1. 首先尝试直接解析
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # 2. 如果失败且json_repair可用，尝试修复
    if data is None and HAS_JSON_REPAIR and repair_json:
        try:
            repaired = repair_json(response)
            if repaired:
                data = json.loads(repaired) if isinstance(repaired, str) else repaired
        except Exception:
            pass
    
    # 3. 如果仍然失败，尝试用正则提取关键字段
    if data is None:
        data = _extract_patient_fields(response)
    
    # 提取数据
    if data:
        presentation = data.get("presentation", "").strip() if isinstance(data, dict) else ""
        utterance = data.get("utterance", "").strip() if isinstance(data, dict) else ""
        grounding = data.get("grounding", {}) if isinstance(data, dict) else {}
        
        # 拼接患者响应
        if presentation:
            patient_response = f"{presentation} {utterance}".strip()
        else:
            patient_response = utterance
        
        # 提取使用的主诉和精神状态
        chief_complaint_used = grounding.get("chief_complaint", []) if isinstance(grounding, dict) else []
        mental_status_used = grounding.get("mental_status", []) if isinstance(grounding, dict) else []
        
        return patient_response, chief_complaint_used, mental_status_used
    
    # 4. 最终兜底：直接返回原文
    return response.strip(), [], []


def _extract_patient_fields(response: str) -> Dict[str, Any]:
    """使用正则表达式从非JSON响应中提取关键字段
    
    Args:
        response: 原始响应字符串
        
    Returns:
        提取的数据字典
    """
    result = {"presentation": "", "utterance": "", "grounding": {"chief_complaint": [], "mental_status": []}}
    
    # 提取presentation（通常在引号中，以括号开头）
    presentation_match = re.search(r'"presentation"\s*:\s*"([^"]*)"', response, re.DOTALL)
    if presentation_match:
        result["presentation"] = presentation_match.group(1)
    
    # 提取utterance
    utterance_match = re.search(r'"utterance"\s*:\s*"([^"]*)"', response, re.DOTALL)
    if utterance_match:
        result["utterance"] = utterance_match.group(1)
    
    # 提取grounding中的chief_complaint数组
    cc_match = re.search(r'"chief_complaint"\s*:\s*(\[[^\]]*\])', response, re.DOTALL)
    if cc_match:
        try:
            cc_list = json.loads(cc_match.group(1))
            result["grounding"]["chief_complaint"] = cc_list
        except json.JSONDecodeError:
            # 尝试手动解析数组元素
            cc_str = cc_match.group(1)
            cc_items = re.findall(r'"([^"]*)"', cc_str)
            result["grounding"]["chief_complaint"] = cc_items
    
    # 提取grounding中的mental_status数组
    ms_match = re.search(r'"mental_status"\s*:\s*(\[[^\]]*\])', response, re.DOTALL)
    if ms_match:
        try:
            ms_list = json.loads(ms_match.group(1))
            result["grounding"]["mental_status"] = ms_list
        except json.JSONDecodeError:
            # 尝试手动解析数组元素
            ms_str = ms_match.group(1)
            ms_items = re.findall(r'"([^"]*)"', ms_str)
            result["grounding"]["mental_status"] = ms_items
    
    return result


def check_end_interview(response: str) -> bool:
    """检查医生响应是否包含结束访谈标记
    
    严格匹配：[END_INTERVIEW]
    
    Args:
        response: 医生响应内容
        
    Returns:
        是否包含结束标记
    """
    # 检查多种可能的结束标记变体
    end_markers = ["[END_INTERVIEW]", "[end_interview]", "END_INTERVIEW", "end_interview", "[END_INTERVIEW", "END_INTERVIEW]"]
    return any(marker in response for marker in end_markers)


def init_phase1_output(
    model_name: str,
    case_id: str,
    basic_info: str,
    chief_complaint: List[str],
    mental_status: List[str]
) -> Path:
    """初始化Phase 1输出文件
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        basic_info: 患者基本信息
        chief_complaint: 主诉列表
        mental_status: 精神状态列表
        
    Returns:
        输出文件路径
    """
    initial_data = {
        "basic_info": basic_info,
        "chief_complaint_all": chief_complaint,
        "mental_status_all": mental_status,
        "conversation": [],
        "chief_complaint_used": [],
        "mental_status_used": []
    }
    
    return init_phase_output(model_name, case_id, 1, initial_data)


def run_interview_phase1(case: Dict[str, Any] = None) -> Dict[str, Any]:
    """运行第一阶段访谈：Clinical History Collection
    
    流程:
    1. 加载病例（随机或指定）
    2. 初始化医生和患者
    3. 初始化输出文件
    4. 医生启动对话（使用Clinical History Collection prompt）
    5. 医患多轮对话（每轮实时保存）
    6. 检测到[END_INTERVIEW]或达到MAX_TURNS时结束
    
    Args:
        case: 可选，指定病例数据。如果不提供，则随机加载一个病例
        
    Returns:
        结果字典，包含：
        - case_id: 病例ID
        - conversation: 对话记录
        - chief_complaint_used: 使用的主诉条目（去重）
        - mental_status_used: 使用的精神状态条目（去重）
        - coverage_stats: 覆盖率统计
        - output_file: 保存的文件路径
        - status: 完成状态（completed/max_turns_reached）
        - doctor: 医生LLMService实例（保持对话上下文，用于传递到下一阶段）
        - case_data: 完整病例数据（用于后续阶段）
        
    使用示例:
        # 单独测试Phase 1
        result = run_interview_phase1()
        
        # 作为完整流程的一部分（从指定case开始）
        result = run_interview_phase1(case=case_data)
        doctor = result['doctor']  # 复用医生实例到Phase 2
    """
    print("=" * 60)
    print("开始第一阶段访谈：Clinical History Collection")
    print(f"MAX_TURNS = {MAX_TURNS}")
    print("=" * 60)
    
    # ========== 1. 加载病例 ==========
    print("\n[1/5] 加载病例数据...")
    if case is None:
        case = load_random_case()
    case_id = case.get("id", "unknown")
    basic_info = case.get("basicInfomation", "")
    chief_complaint = case.get("chiefComplaint", [])
    mental_status = case.get("mentalStatus", [])
    physical_examination = case.get("physicalExamination", "")
    
    print(f"  患者ID: {case_id}")
    print(f"  基本信息: {basic_info}")
    print(f"  主诉数量: {len(chief_complaint)}")
    print(f"  精神状态数量: {len(mental_status)}")
    
    # ========== 2. 初始化医生和患者 ==========
    print("\n[2/5] 初始化医生和患者...")
    
    # 初始化医生（仅使用Doctor Profile作为system prompt，不传入任何病例信息）
    doctor = create_doctor()
    doctor_model = doctor.config.model
    print(f"  医生模型: {doctor_model}")
    
    # 初始化患者
    patient = create_patient(
        basic_info=basic_info,
        chief_complaint=chief_complaint,
        mental_status=mental_status
    )
    print(f"  患者模型: {patient.config.model}")
    
    # ========== 3. 初始化输出文件 ==========
    print("\n[3/5] 初始化输出文件...")
    output_file = init_phase1_output(
        model_name=doctor_model,
        case_id=case_id,
        basic_info=basic_info,
        chief_complaint=chief_complaint,
        mental_status=mental_status
    )
    print(f"  输出文件: {output_file}")
    
    # ========== 4. 准备启动prompt ==========
    print("\n[4/5] 准备启动prompt...")
    
    # 获取Clinical History Collection prompt并替换占位符
    start_prompt = PROMPTS["Clinical History Collection"]
    start_prompt = start_prompt.replace("<BASIC_INFO>", basic_info)
    start_prompt = start_prompt.replace("<PHYSICAL_EXAMINATION>", physical_examination)
    
    print(f"  Prompt长度: {len(start_prompt)} 字符")
    
    # ========== 5. 开始对话 ==========
    print("\n[5/5] 开始医患对话...")
    print("-" * 60)
    
    # 医生启动对话
    print(f"\n[System -> Doctor] 发送启动prompt...")
    doctor_response = doctor.chat(start_prompt)
    print(f"\n医生: {doctor_response[:200]}...")
    
    # 实时保存医生回复
    append_conversation(output_file, "doctor", doctor_response)
    
    # 检查是否直接结束（理论上不应该）
    if check_end_interview(doctor_response):
        print("\n[!] 医生直接结束了访谈")
        append_conversation(output_file, "system", "医生直接结束访谈")
        update_phase_output(output_file, {}, status="completed")
    else:
        # 医患多轮对话
        for turn in range(MAX_TURNS):
            current_turn = turn + 1
            print(f"\n--- 第 {current_turn}/{MAX_TURNS} 轮对话 ---")
            
            # 患者回复
            patient_raw_response = patient.chat(doctor_response)
            patient_response, cc_used, ms_used = parse_patient_response(patient_raw_response)
            print(f"\n患者: {patient_response[:200]}...")
            
            # 实时保存患者回复
            append_conversation(
                output_file, 
                "patient", 
                patient_response,
                chief_complaint_used=cc_used,
                mental_status_used=ms_used
            )
            
            # 准备发送给医生的消息（40轮时添加提醒）
            message_to_doctor = patient_response
            if current_turn == 30 or current_turn == 40:
                reminder = f"""
-----
提醒：当前对话已进行至第 {current_turn} 轮。请合理规划后续轮次，持续聚焦于临床相关问询。这并不表示你需要立即结束访谈；如果你判断当前信息仍不足，请继续进行必要且有效的临床提问。只有当你认为现有信息已足够时，才输出 [END_INTERVIEW] 以结束当前访谈并进入下一阶段。本条为系统提示，无需回复，请继续与患者对话。
-----"""
                message_to_doctor = patient_response + reminder
                print(f"\n[System] 已添加第{current_turn}轮提醒")
            
            # 医生回复
            doctor_response = doctor.chat(message_to_doctor)
            print(f"\n医生: {doctor_response[:200]}...")
            
            # 检查是否结束
            if check_end_interview(doctor_response):
                print(f"\n[!] 医生结束访谈（第 {current_turn} 轮）")
                # 保存医生结束标记
                append_conversation(output_file, "doctor", doctor_response)
                update_phase_output(output_file, {}, status="completed")
                break
            else:
                # 实时保存医生回复
                append_conversation(output_file, "doctor", doctor_response)
        else:
            # 达到最大轮次
            print(f"\n[!] 达到最大轮次限制（{MAX_TURNS}轮）")
            append_conversation(output_file, "system", f"达到最大轮次限制 {MAX_TURNS}")
            update_phase_output(output_file, {}, status="max_turns_reached")
    
    # ========== 6. 完成 ==========
    print("\n" + "-" * 60)
    print("\n[完成] 访谈结束")
    
    # 读取最终结果
    with open(output_file, "r", encoding="utf-8") as f:
        final_data = json.load(f)
    
    # 统计基本信息
    total_turns = len([c for c in final_data['conversation'] if c['role'] == 'patient'])
    
    print(f"  总对话轮数: {total_turns}")
    print(f"  最终状态: {final_data['status']}")
    print(f"  输出文件: {output_file}")
    
    print("\n" + "=" * 60)
    print("第一阶段访谈完成")
    print("=" * 60)
    
    return {
        "case_id": case_id,
        "model_name": doctor_model,
        "conversation": final_data["conversation"],
        "chief_complaint_used": final_data["chief_complaint_used"],
        "mental_status_used": final_data["mental_status_used"],
        "output_file": str(output_file),
        "status": final_data["status"],
        "doctor": doctor,
        "case_data": case
    }


if __name__ == "__main__":
    """单独测试第一阶段访谈"""
    print("=" * 60)
    print("单独测试：第一阶段 Clinical History Collection")
    print("=" * 60)
    
    try:
        # 运行第一阶段
        result = run_interview_phase1()
        
        # 打印结果摘要（不显示 doctor 和 case_data 的详细内容）
        print(f"\n访谈结果摘要:")
        print(f"  患者ID: {result['case_id']}")
        print(f"  对话轮数: {len([c for c in result['conversation'] if c['role'] == 'patient'])}")
        print(f"  主诉覆盖率: {result['coverage_stats']['chief_complaint_used_count']}/{result['coverage_stats']['chief_complaint_total_count']} ({result['coverage_stats']['chief_complaint_coverage']:.2f}%)")
        print(f"  精神状态覆盖率: {result['coverage_stats']['mental_status_used_count']}/{result['coverage_stats']['mental_status_total_count']} ({result['coverage_stats']['mental_status_coverage']:.2f}%)")
        print(f"  整体覆盖率: {result['coverage_stats']['overall_coverage']:.2f}%")
        print(f"  最终状态: {result['status']}")
        print(f"  输出文件: {result['output_file']}")
        print(f"  医生实例: 已创建（可用于下一阶段）")
        print(f"  病例数据: 已加载")
        
        print("\n" + "=" * 60)
        print("第一阶段测试完成！")
        print("=" * 60)
        print("\n提示：如需运行完整流程（1-6阶段），请使用 run_interview.py")
        
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
