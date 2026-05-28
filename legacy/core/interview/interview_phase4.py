"""
精神科访谈执行模块 - 第四阶段：Definitive Diagnosis

使用方法:
    # 方式1：单独测试第四阶段（需要传入phase3的结果）
    python core/interview/interview_phase4.py

    # 方式2：作为完整流程的一部分
    from core.interview.interview_phase4 import run_interview_phase4

    result = run_interview_phase4(
        doctor=phase3_result['doctor'],
        model_name=phase3_result['model_name'],
        case_id=phase3_result['case_id']
    )

    # 结果包含:
    # - definitive_diagnosis: 最终诊断列表
    # - diagnosis_reasoning: 诊断理由与依据
    # - raw_response: 医生的原始响应
    # - output_file: 保存的文件路径
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from core.interview.prompts import PROMPTS
from core.output_manager import init_phase_output, update_phase_output

load_dotenv(Path(__file__).parent.parent.parent / ".env")


def parse_definitive_diagnosis(response: str) -> tuple[List[str], str]:
    """解析医生生成的最终诊断

    Args:
        response: 医生的响应内容

    Returns:
        (diagnosis_list, reasoning) — 诊断列表和诊断理由
    """
    reasoning = ""
    diagnoses = []

    try:
        # 提取标记外的内容作为诊断理由
        match = re.search(
            r'(.*?)\[BEGIN_DEFINITIVE_DIAGNOSIS\]',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if match:
            reasoning = match.group(1).strip()

        # 提取诊断列表
        diag_match = re.search(
            r'\[BEGIN_DEFINITIVE_DIAGNOSIS\](.*?)\[END_DEFINITIVE_DIAGNOSIS\]',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if diag_match:
            content = diag_match.group(1).strip()
            diagnoses = json.loads(content)
            if not isinstance(diagnoses, list):
                diagnoses = []
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass

    return diagnoses, reasoning


def run_interview_phase4(
    doctor,
    model_name: str,
    case_id: str
) -> Dict[str, Any]:
    """运行第四阶段访谈：Definitive Diagnosis

    基于前三阶段的对话上下文，让医生生成最终诊断。

    Args:
        doctor: 医生LLMService实例（从phase3传递过来，保持对话上下文）
        model_name: 医生模型名称
        case_id: 病例ID

    Returns:
        结果字典，包含：
        - definitive_diagnosis: 最终诊断列表
        - diagnosis_reasoning: 诊断理由与依据
        - raw_response: 医生的原始响应
        - output_file: 保存的文件路径
        - doctor: 医生LLMService实例（保持对话上下文）
        - model_name: 医生模型名称
        - case_id: 病例ID
    """
    print("\n" + "=" * 60)
    print("开始第四阶段：Definitive Diagnosis")
    print("=" * 60)

    output_file = init_phase_output(
        model_name=model_name,
        case_id=case_id,
        phase=4,
        initial_data={
            "definitive_diagnosis": [],
            "diagnosis_reasoning": "",
            "raw_response": ""
        }
    )
    print(f"  输出文件: {output_file}")

    print("\n" + "-" * 60)
    print("医生生成最终诊断")
    print("-" * 60)

    prompt = PROMPTS["Definitive Diagnosis"]

    print(f"\nPrompt长度: {len(prompt)} 字符")

    print(f"\n医生思考中...")
    doctor_response = doctor.chat(prompt)

    print(f"\n医生原始响应:")
    print(f"  {doctor_response[:500]}...")

    definitive_diagnosis, diagnosis_reasoning = parse_definitive_diagnosis(doctor_response)

    print(f"\n解析结果:")
    if definitive_diagnosis:
        print(f"  最终诊断数量: {len(definitive_diagnosis)}")
        for i, diagnosis in enumerate(definitive_diagnosis, 1):
            print(f"    {i}. {diagnosis}")
    else:
        print(f"  （未能解析出最终诊断）")

    update_phase_output(
        output_file,
        {
            "definitive_diagnosis": definitive_diagnosis,
            "diagnosis_reasoning": diagnosis_reasoning,
            "raw_response": doctor_response
        },
        status="completed"
    )

    print(f"\n结果已保存: {output_file}")

    print("\n" + "=" * 60)
    print("第四阶段完成 - 整个访谈流程结束")
    print("=" * 60)

    return {
        "definitive_diagnosis": definitive_diagnosis,
        "diagnosis_reasoning": diagnosis_reasoning,
        "raw_response": doctor_response,
        "output_file": str(output_file),
        "doctor": doctor,
        "model_name": model_name,
        "case_id": case_id
    }


if __name__ == "__main__":
    print("=" * 60)
    print("单独测试：第四阶段 Definitive Diagnosis")
    print("=" * 60)
    print("\n注意：第四阶段需要先运行前三阶段获取医生实例")
    print("建议直接使用 run_interview.py 运行完整流程")
    print("\n" + "=" * 60)
