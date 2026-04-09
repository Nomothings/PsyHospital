"""
精神科访谈执行模块 - 第三阶段：Clinical Formulation

使用方法:
    # 方式1：单独测试第三阶段（需要传入phase2的结果）
    python core/interview/interview_phase3.py
    
    # 方式2：作为完整流程的一部分
    from core.interview.interview_phase3 import run_interview_phase3
    
    result = run_interview_phase3(
        doctor=phase2_result['doctor'],
        model_name=phase2_result['model_name'],
        case_id=phase2_result['case_id'],
        examination_results=phase2_result['examination_results']
    )
    
    # 结果包含:
    # - syntactic_formulation: 临床病历正文
    # - raw_response: 医生的原始响应
    # - output_file: 保存的文件路径
    # - doctor: 医生LLM实例（用于传递到下一阶段）
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


def parse_clinical_formulation(response: str) -> str:
    """解析医生生成的临床病历
    
    Args:
        response: 医生的响应内容
        
    Returns:
        临床病历正文，如果解析失败返回空字符串
    """
    try:
        match = re.search(
            r'\[BEGIN_CLINICAL_FORMULATION\](.*?)\[END_CLINICAL_FORMULATION\]',
            response,
            re.DOTALL | re.IGNORECASE
        )
        
        if match:
            return match.group(1).strip()
        
        return ""
    except (AttributeError, TypeError):
        return ""


def format_examination_results(examination_results: Dict[str, Any]) -> str:
    """格式化检查结果为字符串
    
    Args:
        examination_results: 检查结果字典
        
    Returns:
        格式化后的检查结果字符串
    """
    if not examination_results:
        return "无辅助检查结果"
    
    lines = []
    for exam_name, result in examination_results.items():
        lines.append(f"- {exam_name}: {result}")
    
    return "\n".join(lines)


def run_interview_phase3(
    doctor,
    model_name: str,
    case_id: str,
    examination_results: Dict[str, Any]
) -> Dict[str, Any]:
    """运行第三阶段访谈：Clinical Formulation
    
    基于前两阶段的对话上下文和检查结果，让医生整理生成临床病历。
    
    Args:
        doctor: 医生LLMService实例（从phase2传递过来，保持对话上下文）
        model_name: 医生模型名称
        case_id: 病例ID
        examination_results: Instrument返回的检查结果
        
    Returns:
        结果字典，包含：
        - syntactic_formulation: 临床病历正文
        - raw_response: 医生的原始响应
        - output_file: 保存的文件路径
        - doctor: 医生LLMService实例（保持对话上下文，用于传递到下一阶段）
        - model_name: 医生模型名称
        - case_id: 病例ID
        
    使用示例:
        phase3_result = run_interview_phase3(
            doctor=phase2_result['doctor'],
            model_name=phase2_result['model_name'],
            case_id=phase2_result['case_id'],
            examination_results=phase2_result['examination_results']
        )
    """
    print("\n" + "=" * 60)
    print("开始第三阶段：Clinical Formulation")
    print("=" * 60)
    
    output_file = init_phase_output(
        model_name=model_name,
        case_id=case_id,
        phase=3,
        initial_data={
            "syntactic_formulation": "",
            "raw_response": ""
        }
    )
    print(f"  输出文件: {output_file}")
    
    print("\n" + "-" * 60)
    print("医生生成临床病历")
    print("-" * 60)
    
    prompt = PROMPTS["Clinical Formulation"]
    
    examinations_results_str = format_examination_results(examination_results)
    prompt = prompt.replace("<EXAMINATIONS_RESULTS>", examinations_results_str)
    
    print(f"\n检查结果:")
    print(f"  {examinations_results_str[:200]}...")
    print(f"\nPrompt长度: {len(prompt)} 字符")
    
    print(f"\n医生思考中...")
    doctor_response = doctor.chat(prompt)
    
    print(f"\n医生原始响应:")
    print(f"  {doctor_response[:500]}...")
    
    syntactic_formulation = parse_clinical_formulation(doctor_response)
    
    print(f"\n解析结果:")
    if syntactic_formulation:
        print(f"  临床病历长度: {len(syntactic_formulation)} 字符")
        print(f"  临床病历预览: {syntactic_formulation[:200]}...")
    else:
        print(f"  （未能解析出临床病历）")
    
    update_phase_output(
        output_file,
        {
            "syntactic_formulation": syntactic_formulation,
            "raw_response": doctor_response
        },
        status="completed"
    )
    
    print(f"\n结果已保存: {output_file}")
    
    print("\n" + "=" * 60)
    print("第三阶段完成")
    print("=" * 60)
    
    return {
        "syntactic_formulation": syntactic_formulation,
        "raw_response": doctor_response,
        "output_file": str(output_file),
        "doctor": doctor,
        "model_name": model_name,
        "case_id": case_id
    }


if __name__ == "__main__":
    print("=" * 60)
    print("单独测试：第三阶段 Clinical Formulation")
    print("=" * 60)
    print("\n注意：第三阶段需要先运行第一、二阶段获取医生实例和检查结果")
    print("建议直接使用 run_interview.py 运行完整流程")
    print("\n或者按以下方式测试：")
    print("  1. from core.interview.interview_phase1 import run_interview_phase1")
    print("  2. from core.interview.interview_phase2 import run_interview_phase2")
    print("  3. phase1_result = run_interview_phase1()")
    print("  4. phase2_result = run_interview_phase2(")
    print("         doctor=phase1_result['doctor'],")
    print("         model_name=phase1_result['model_name'],")
    print("         case_id=phase1_result['case_id'],")
    print("         case_data=phase1_result['case_data']")
    print("     )")
    print("  5. from core.interview.interview_phase3 import run_interview_phase3")
    print("  6. phase3_result = run_interview_phase3(")
    print("         doctor=phase2_result['doctor'],")
    print("         model_name=phase2_result['model_name'],")
    print("         case_id=phase2_result['case_id'],")
    print("         examination_results=phase2_result['examination_results']")
    print("     )")
    print("\n" + "=" * 60)
