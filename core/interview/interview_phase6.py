"""
精神科访谈执行模块 - 第六阶段：Differential Diagnosis

使用方法:
    # 方式1：单独测试第六阶段（需要传入phase5的结果）
    python core/interview/interview_phase6.py
    
    # 方式2：作为完整流程的一部分
    from core.interview.interview_phase6 import run_interview_phase6
    
    result = run_interview_phase6(
        doctor=phase5_result['doctor'],
        model_name=phase5_result['model_name'],
        case_id=phase5_result['case_id']
    )
    
    # 结果包含:
    # - differential_diagnosis: 最终诊断序列
    # - raw_response: 医生的原始响应
    # - output_file: 保存的文件路径
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from core.interview.prompts import PROMPTS
from core.output_manager import init_phase_output, update_phase_output

load_dotenv(Path(__file__).parent.parent.parent / ".env")


def parse_differential_diagnosis(response: str) -> List[str]:
    """解析医生生成的最终诊断序列
    
    Args:
        response: 医生的响应内容
        
    Returns:
        最终诊断列表，如果解析失败返回空列表
    """
    try:
        match = re.search(
            r'\[BEGIN_DIFFERENTIAL_DIAGNOSIS\](.*?)\[END_DIFFERENTIAL_DIAGNOSIS\]',
            response,
            re.DOTALL | re.IGNORECASE
        )
        
        if match:
            content = match.group(1).strip()
            diagnoses = json.loads(content)
            if isinstance(diagnoses, list):
                return diagnoses
            return []
        
        return []
    except (json.JSONDecodeError, AttributeError, TypeError):
        return []


def run_interview_phase6(
    doctor,
    model_name: str,
    case_id: str
) -> Dict[str, Any]:
    """运行第六阶段访谈：Differential Diagnosis
    
    基于前五阶段的对话上下文，让医生在诊断假设列表中进行鉴别诊断，
    输出最终诊断序列。
    
    Args:
        doctor: 医生LLMService实例（从phase5传递过来，保持对话上下文）
        model_name: 医生模型名称
        case_id: 病例ID
        
    Returns:
        结果字典，包含：
        - differential_diagnosis: 最终诊断序列
        - raw_response: 医生的原始响应
        - output_file: 保存的文件路径
        - doctor: 医生LLMService实例（保持对话上下文）
        - model_name: 医生模型名称
        - case_id: 病例ID
        
    使用示例:
        phase6_result = run_interview_phase6(
            doctor=phase5_result['doctor'],
            model_name=phase5_result['model_name'],
            case_id=phase5_result['case_id']
        )
    """
    print("\n" + "=" * 60)
    print("开始第六阶段：Differential Diagnosis")
    print("=" * 60)
    
    output_file = init_phase_output(
        model_name=model_name,
        case_id=case_id,
        phase=6,
        initial_data={
            "differential_diagnosis": [],
            "raw_response": ""
        }
    )
    print(f"  输出文件: {output_file}")
    
    print("\n" + "-" * 60)
    print("医生进行鉴别诊断")
    print("-" * 60)
    
    prompt = PROMPTS["Differential Diagnosis"]
    
    print(f"\nPrompt长度: {len(prompt)} 字符")
    
    print(f"\n医生思考中...")
    doctor_response = doctor.chat(prompt)
    
    print(f"\n医生原始响应:")
    print(f"  {doctor_response[:500]}...")
    
    differential_diagnosis = parse_differential_diagnosis(doctor_response)
    
    print(f"\n解析结果:")
    if differential_diagnosis:
        print(f"  最终诊断数量: {len(differential_diagnosis)}")
        for i, diagnosis in enumerate(differential_diagnosis, 1):
            print(f"    {i}. {diagnosis}")
    else:
        print(f"  （未能解析出最终诊断）")
    
    update_phase_output(
        output_file,
        {
            "differential_diagnosis": differential_diagnosis,
            "raw_response": doctor_response
        },
        status="completed"
    )
    
    print(f"\n结果已保存: {output_file}")
    
    print("\n" + "=" * 60)
    print("第六阶段完成 - 整个访谈流程结束")
    print("=" * 60)
    
    return {
        "differential_diagnosis": differential_diagnosis,
        "raw_response": doctor_response,
        "output_file": str(output_file),
        "doctor": doctor,
        "model_name": model_name,
        "case_id": case_id
    }


if __name__ == "__main__":
    print("=" * 60)
    print("单独测试：第六阶段 Differential Diagnosis")
    print("=" * 60)
    print("\n注意：第六阶段需要先运行前五阶段获取医生实例")
    print("建议直接使用 run_interview.py 运行完整流程")
    print("\n" + "=" * 60)
