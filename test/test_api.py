"""
LLM API 测试

前置说明:
    - 确保项目根目录有.env文件且配置正确
    - 确保网络连接正常

使用方法:
    python test/test_api.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_api import LLMService, get_patient_llm, get_doctor_llm, get_evaluator_llm


def test_basic_chat():
    """测试单轮对话"""
    print("\n[测试] 单轮对话")
    
    llm = LLMService(role="patient")
    response = llm.chat("你好，请介绍一下自己")
    
    print(f"用户: 你好，请介绍一下自己")
    print(f"助手: {response[:60]}...")
    
    assert len(response) > 0
    print("✓ 单轮对话测试通过")
    return True


def test_multi_turn_chat():
    """测试多轮对话（自动维护上下文）"""
    print("\n[测试] 多轮对话（上下文记忆）")
    
    llm = LLMService(role="doctor")
    
    # 第一轮
    r1 = llm.chat("2+2等于几？")
    print(f"用户: 2+2等于几？")
    print(f"助手: {r1}")
    
    # 第二轮（应该记住上下文）
    r2 = llm.chat("再加3等于多少？")
    print(f"\n用户: 再加3等于多少？")
    print(f"助手: {r2}")
    
    assert "7" in r2, f"模型应计算出7，实际回复: {r2}"
    print("✓ 多轮对话测试通过")
    return True


def test_name_memory():
    """测试名字记忆"""
    print("\n[测试] 名字记忆")
    
    llm = LLMService(role="patient")
    
    llm.chat("你好，我叫小明")
    print(f"用户: 你好，我叫小明")
    
    r = llm.chat("我叫什么名字？")
    print(f"用户: 我叫什么名字？")
    print(f"助手: {r}")
    
    assert "小明" in r, f"模型应记住名字，实际回复: {r}"
    print("✓ 名字记忆测试通过")
    return True


def test_new_instance_new_context():
    """测试新实例 = 新上下文"""
    print("\n[测试] 新实例新上下文")
    
    # 第一个实例
    llm1 = LLMService(role="doctor")
    llm1.chat("我的密码是123456")
    
    # 第二个实例（应该是全新的）
    llm2 = LLMService(role="doctor")
    r = llm2.chat("我的密码是多少？")
    
    print(f"实例1: 我的密码是123456")
    print(f"实例2: 我的密码是多少？")
    print(f"助手: {r}")
    
    assert "123456" not in r, "新实例不应知道旧实例的上下文"
    print("✓ 新实例新上下文测试通过")
    return True


def test_system_message():
    """测试系统提示词"""
    print("\n[测试] 系统提示词")
    
    llm = LLMService(
        role="evaluator",
        system_message="你是一个数学专家，只回答数学问题。"
    )
    
    r = llm.chat("你好")
    print(f"系统: 你是一个数学专家...")
    print(f"用户: 你好")
    print(f"助手: {r[:60]}...")
    
    assert len(r) > 0
    print("✓ 系统提示词测试通过")
    return True


def test_get_history():
    """测试获取对话历史"""
    print("\n[测试] 获取对话历史")
    
    llm = LLMService(role="patient")
    llm.chat("你好")
    llm.chat("今天天气怎么样？")
    
    history = llm.get_history()
    print(f"历史记录条数: {len(history)}")
    
    assert len(history) == 4  # user + assistant + user + assistant
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    print("✓ 获取历史测试通过")
    return True


def test_clear_history():
    """测试清空历史"""
    print("\n[测试] 清空历史")
    
    llm = LLMService(role="doctor", system_message="你是医生")
    llm.chat("你好")
    
    history_before = llm.get_history()
    print(f"清空前: {len(history_before)} 条")
    
    llm.clear_history()
    history_after = llm.get_history()
    print(f"清空后: {len(history_after)} 条")
    
    assert len(history_after) == 1  # 只保留system消息
    assert history_after[0]["role"] == "system"
    print("✓ 清空历史测试通过")
    return True


def test_roles():
    """测试三个角色的独立配置"""
    print("\n[测试] 三个角色配置")
    
    patient = get_patient_llm()
    doctor = get_doctor_llm()
    evaluator = get_evaluator_llm()
    
    print(f"Patient:   {patient.config.model} @ {patient.config.api_base[:35]}...")
    print(f"Doctor:    {doctor.config.model} @ {doctor.config.api_base[:35]}...")
    print(f"Evaluator: {evaluator.config.model} @ {evaluator.config.api_base[:35]}...")
    
    # 简单测试
    r = patient.chat("测试")
    print(f"\nPatient测试: {r[:40]}...")
    
    print("✓ 角色配置测试通过")
    return True


def print_usage():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                    LLM API 使用指南                              ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  配置: 项目根目录 .env 文件                                      ║
║                                                                  ║
║  PATIENT_API_BASE=xxx     PATIENT_API_KEY=xxx     PATIENT_MODEL  ║
║  DOCTOR_API_BASE=xxx      DOCTOR_API_KEY=xxx      DOCTOR_MODEL   ║
║  EVALUATOR_API_BASE=xxx   EVALUATOR_API_KEY=xxx   EVALUATOR_MODEL║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  使用方法:                                                       ║
║                                                                  ║
║  from services.llm_api import LLMService, get_patient_llm        ║
║                                                                  ║
║  # 创建实例（自动维护上下文）                                    ║
║  llm = LLMService(role="patient")                                ║
║                                                                  ║
║  # 多轮对话                                                      ║
║  response = llm.chat("你好")                                     ║
║  response = llm.chat("我叫小明")  # 自动包含上一轮               ║
║  response = llm.chat("我叫什么？") # 模型知道是小明              ║
║                                                                  ║
║  # 查看历史                                                      ║
║  print(llm.get_history())                                        ║
║                                                                  ║
║  # 新实例 = 新对话                                               ║
║  llm2 = LLMService(role="patient")  # 全新上下文                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    print_usage()
    
    tests = [
        test_roles,
        test_basic_chat,
        test_multi_turn_chat,
        test_name_memory,
        test_new_instance_new_context,
        test_system_message,
        test_get_history,
        test_clear_history,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print(f"\n{'='*50}")
    print(f"结果: {sum(results)}/{len(results)} 通过")
    sys.exit(0 if all(results) else 1)
