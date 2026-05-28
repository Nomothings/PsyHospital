"""
精神科访谈执行模块 - 第五阶段：Treatment Planning

使用方法:
    # 方式1：单独测试第五阶段（需要传入phase4的结果）
    python core/interview/interview_phase5.py

    # 方式2：作为完整流程的一部分
    from core.interview.interview_phase5 import run_interview_phase5

    result = run_interview_phase5(
        doctor=phase4_result['doctor'],
        model_name=phase4_result['model_name'],
        case_id=phase4_result['case_id']
    )

    # 结果包含:
    # - treatment_plan: 治疗建议正文
    # - raw_response: 医生的原始响应
    # - output_file: 保存的文件路径
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from core.interview.prompts import PROMPTS
from core.output_manager import init_phase_output, update_phase_output

load_dotenv(Path(__file__).parent.parent.parent / ".env")


def parse_treatment_plan(response: str) -> str:
    """解析医生生成的治疗建议

    Args:
        response: 医生的响应内容

    Returns:
        治疗建议正文，如果解析失败返回空字符串
    """
    try:
        match = re.search(
            r'\[BEGIN_TREATMENT_PLAN\](.*?)\[END_TREATMENT_PLAN\]',
            response,
            re.DOTALL | re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

        return ""
    except (AttributeError, TypeError):
        return ""


def run_interview_phase5(
    doctor,
    model_name: str,
    case_id: str
) -> Dict[str, Any]:
    """运行第五阶段访谈：Treatment Planning

    基于前四阶段的对话上下文，让医生生成治疗建议。

    Args:
        doctor: 医生LLMService实例（从phase4传递过来，保持对话上下文）
        model_name: 医生模型名称
        case_id: 病例ID

    Returns:
        结果字典，包含：
        - treatment_plan: 治疗建议正文
        - raw_response: 医生的原始响应
        - output_file: 保存的文件路径
        - doctor: 医生LLMService实例（保持对话上下文）
        - model_name: 医生模型名称
        - case_id: 病例ID
    """
    print("\n" + "=" * 60)
    print("开始第五阶段：Treatment Planning")
    print("=" * 60)

    output_file = init_phase_output(
        model_name=model_name,
        case_id=case_id,
        phase=5,
        initial_data={
            "treatment_plan": "",
            "raw_response": ""
        }
    )
    print(f"  输出文件: {output_file}")

    print("\n" + "-" * 60)
    print("医生生成治疗建议")
    print("-" * 60)

    prompt = PROMPTS["Treatment Planning"]

    print(f"\nPrompt长度: {len(prompt)} 字符")

    print(f"\n医生思考中...")
    doctor_response = doctor.chat(prompt)

    print(f"\n医生原始响应:")
    print(f"  {doctor_response[:500]}...")

    treatment_plan = parse_treatment_plan(doctor_response)

    print(f"\n解析结果:")
    if treatment_plan:
        print(f"  治疗建议长度: {len(treatment_plan)} 字符")
        print(f"  治疗建议预览: {treatment_plan[:200]}...")
    else:
        print(f"  （未能解析出治疗建议）")

    update_phase_output(
        output_file,
        {
            "treatment_plan": treatment_plan,
            "raw_response": doctor_response
        },
        status="completed"
    )

    print(f"\n结果已保存: {output_file}")

    print("\n" + "=" * 60)
    print("第五阶段完成 - 整个访谈流程结束")
    print("=" * 60)

    return {
        "treatment_plan": treatment_plan,
        "raw_response": doctor_response,
        "output_file": str(output_file),
        "doctor": doctor,
        "model_name": model_name,
        "case_id": case_id
    }


if __name__ == "__main__":
    print("=" * 60)
    print("单独测试：第五阶段 Treatment Planning")
    print("=" * 60)
    print("\n注意：第五阶段需要先运行前四阶段获取医生实例")
    print("建议直接使用 run_interview.py 运行完整流程")
    print("\n" + "=" * 60)
