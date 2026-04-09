"""
虚拟患者启动模块

使用方法:
    from agents.patient.patient import create_patient
    
    # 启动虚拟患者（直接传入病例信息）
    patient = create_patient(
        basic_info="患者男，19 岁",
        chief_complaint=["3 + 月前起病", "敏感多疑", "自诉电话被监听"],
        mental_status=["面无表情", "精神检查不合作"]
    )
    
    # 开始对话（患者根据医生提问回答）
    response = patient.chat("你好，请问你哪里不舒服？")
    print(response)
    
    # 解析JSON响应
    import json
    data = json.loads(response)
    print(data["utterance"])  # 患者说的话
    print(data["presentation"])  # 外显表现
    
    # 查看完整对话历史
    history = patient.get_history()
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.llm_api import LLMService
from agents.patient.prompts import PROMPTS


def create_patient(
    basic_info: str,
    chief_complaint: List[str],
    mental_status: List[str]
) -> LLMService:
    """启动虚拟患者
    
    直接使用传入的病例信息实例化患者Agent，
    使用PATIENT_API配置。
    
    Args:
        basic_info: 基本信息字符串，如"患者男，19 岁"
        chief_complaint: 主诉列表，如["3 + 月前起病", "敏感多疑", ...]
        mental_status: 精神状态列表，如["面无表情", "精神检查不合作", ...]
        
    Returns:
        LLMService实例（role="patient"，已设置系统prompt和病例信息）
        
    Example:
        >>> patient = create_patient(
        ...     basic_info="患者男，19 岁",
        ...     chief_complaint=["3 + 月前起病", "敏感多疑"],
        ...     mental_status=["面无表情"]
        ... )
        >>> response = patient.chat("你好，请问有什么不舒服？")
        >>> import json
        >>> data = json.loads(response)
        >>> print(data["utterance"])
    """
    # 将列表转为JSON字符串
    chief_complaint_json = json.dumps(chief_complaint, ensure_ascii=False)
    mental_status_json = json.dumps(mental_status, ensure_ascii=False)
    
    # 获取患者prompt并替换占位符
    system_prompt = PROMPTS["Patient Profile"]
    system_prompt = system_prompt.replace("<BASIC_INFO>", basic_info)
    system_prompt = system_prompt.replace("<CHIEF_COMPLAINT>", chief_complaint_json)
    system_prompt = system_prompt.replace("<MENTAL_STATUS>", mental_status_json)
    
    # 实例化患者（使用patient角色的API配置）
    patient = LLMService(
        role="patient",
        system_message=system_prompt
    )
    
    # 保存病例信息到实例（方便后续使用）
    patient.case_info = {
        "basic_info": basic_info,
        "chief_complaint": chief_complaint,
        "mental_status": mental_status
    }
    
    return patient


# 便捷函数别名
init_patient = create_patient
start_patient = create_patient


if __name__ == "__main__":
    # 测试启动虚拟患者
    print("=" * 50)
    print("测试启动虚拟患者")
    print("=" * 50)
    
    # 测试数据
    test_basic_info = "患者男，19 岁"
    test_chief_complaint = [
        "3 + 月前起病",
        "敏感多疑",
        "自诉电话被监听",
        "感觉有人跟踪",
        "觉得周围不安全",
        "晚上睡眠差"
    ]
    test_mental_status = [
        "面无表情",
        "精神检查不合作",
        "敏感多疑",
        "自知力缺乏"
    ]
    
    try:
        # 启动患者
        patient = create_patient(
            basic_info=test_basic_info,
            chief_complaint=test_chief_complaint,
            mental_status=test_mental_status
        )
        
        print(f"\n基本信息: {patient.case_info['basic_info']}")
        print(f"主诉数量: {len(patient.case_info['chief_complaint'])}")
        print(f"精神状态数量: {len(patient.case_info['mental_status'])}")
        print(f"使用模型: {patient.config.model}")
        
        # 测试对话
        print("\n" + "-" * 50)
        print("开始问诊对话")
        print("-" * 50)
        
        # 第一轮：医生问候
        doctor_input = "你好，请问你哪里不舒服？"
        print(f"\n医生: {doctor_input}")
        response = patient.chat(doctor_input)
        print(f"患者原始响应: {response[:200]}...")
        
        # 尝试解析JSON
        try:
            data = json.loads(response)
            print(f"\n解析结果:")
            print(f"  表现: {data.get('presentation', '')}")
            print(f"  话语: {data.get('utterance', '')}")
            print(f"  grounding: {data.get('grounding', {})}")
        except json.JSONDecodeError:
            print("  (响应不是标准JSON格式)")
        
        # 第二轮：继续问诊
        doctor_input = "这种情况持续多久了？"
        print(f"\n医生: {doctor_input}")
        response = patient.chat(doctor_input)
        print(f"患者响应: {response[:200]}...")
        
        print("\n" + "=" * 50)
        print("测试完成")
        print("=" * 50)
        
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
