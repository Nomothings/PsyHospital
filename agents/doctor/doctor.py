"""
虚拟医生启动模块

使用方法:
    from agents.doctor.doctor import create_doctor
    
    # 启动虚拟医生（仅使用Doctor Profile作为system prompt）
    doctor = create_doctor()
    
    # 开始问诊对话
    response = doctor.chat("你好，请问有什么不舒服？")
    print(response)
    
    # 继续对话（自动维护上下文）
    response = doctor.chat("这种情况持续多久了？")
    print(response)
    
    # 查看完整对话历史
    history = doctor.get_history()
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.llm_api import LLMService
from agents.doctor.prompts import PROMPTS


def create_doctor() -> LLMService:
    """启动虚拟医生
    
    通过.env中的DOCTOR_API配置实例化医生Agent。
    自动加载医生prompt（PROMPTS["Doctor Profile"]），支持多轮对话上下文。
    
    Returns:
        LLMService实例（role="doctor"，已设置系统prompt）
        
    Example:
        >>> doctor = create_doctor()
        >>> response = doctor.chat("你好，请描述一下你的症状")
        >>> print(response)
    """
    # 获取医生系统prompt（仅使用Doctor Profile，不添加任何额外信息）
    system_prompt = PROMPTS["Doctor Profile"]
    
    # 实例化医生（使用doctor角色的API配置）
    doctor = LLMService(
        role="doctor",
        system_message=system_prompt
    )
    
    return doctor


if __name__ == "__main__":
    # 测试启动虚拟医生
    print("=" * 50)
    print("测试启动虚拟医生")
    print("=" * 50)
    
    # 启动医生
    doctor = create_doctor()
    
    print(f"使用模型: {doctor.config.model}")
    print(f"API地址: {doctor.config.api_base}")
    
    # 测试对话
    print("\n" + "-" * 50)
    print("开始问诊对话")
    print("-" * 50)
    
    # 第一轮
    user_input = "医生你好，我最近心情很差"
    print(f"\n患者: {user_input}")
    response = doctor.chat(user_input)
    print(f"医生: {response}")
    
    # 第二轮（测试上下文）
    user_input = "这种情况大概持续多久了？"
    print(f"\n患者: {user_input}")
    response = doctor.chat(user_input)
    print(f"医生: {response}")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
