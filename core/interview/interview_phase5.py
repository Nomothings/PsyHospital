"""
精神科访谈执行模块 - 第五阶段：Diagnostic Hypotheses

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
    # - diagnostic_hypotheses: 诊断假设列表
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


def parse_diagnostic_hypotheses(response: str) -> List[str]:
    """解析医生生成的诊断假设
    
    Args:
        response: 医生的响应内容
        
    Returns:
        诊断假设列表，如果解析失败返回空列表
    """
    try:
        match = re.search(
            r'\[BEGIN_DIAGNOSTIC_HYPOTHESES\](.*?)\[END_DIAGNOSTIC_HYPOTHESES\]',
            response,
            re.DOTALL | re.IGNORECASE
        )
        
        if match:
            content = match.group(1).strip()
            hypotheses = json.loads(content)
            if isinstance(hypotheses, list):
                return hypotheses
            return []
        
        return []
    except (json.JSONDecodeError, AttributeError, TypeError):
        return []


def run_interview_phase5(
    doctor,
    model_name: str,
    case_id: str
) -> Dict[str, Any]:
    """运行第五阶段访谈：Diagnostic Hypotheses
    
    基于前四阶段的对话上下文，让医生生成当前最可能的诊断假设列表。
    
    Args:
        doctor: 医生LLMService实例（从phase4传递过来，保持对话上下文）
        model_name: 医生模型名称
        case_id: 病例ID
        
    Returns:
        结果字典，包含：
        - diagnostic_hypotheses: 诊断假设列表
        - raw_response: 医生的原始响应
        - output_file: 保存的文件路径
        - doctor: 医生LLMService实例（保持对话上下文，用于传递到下一阶段）
        - model_name: 医生模型名称
        - case_id: 病例ID
        
    使用示例:
        phase5_result = run_interview_phase5(
            doctor=phase4_result['doctor'],
            model_name=phase4_result['model_name'],
            case_id=phase4_result['case_id']
        )
    """
    print("\n" + "=" * 60)
    print("开始第五阶段：Diagnostic Hypotheses")
    print("=" * 60)
    
    output_file = init_phase_output(
        model_name=model_name,
        case_id=case_id,
        phase=5,
        initial_data={
            "diagnostic_hypotheses": [],
            "raw_response": ""
        }
    )
    print(f"  输出文件: {output_file}")
    
    print("\n" + "-" * 60)
    print("医生生成诊断假设")
    print("-" * 60)
    
    prompt = PROMPTS["Diagnostic Hypotheses"]
    
    print(f"\nPrompt长度: {len(prompt)} 字符")
    
    print(f"\n医生思考中...")
    doctor_response = doctor.chat(prompt)
    
    print(f"\n医生原始响应:")
    print(f"  {doctor_response[:500]}...")
    
    diagnostic_hypotheses = parse_diagnostic_hypotheses(doctor_response)
    
    print(f"\n解析结果:")
    if diagnostic_hypotheses:
        print(f"  诊断假设数量: {len(diagnostic_hypotheses)}")
        for i, hypothesis in enumerate(diagnostic_hypotheses, 1):
            print(f"    {i}. {hypothesis}")
    else:
        print(f"  （未能解析出诊断假设）")
    
    update_phase_output(
        output_file,
        {
            "diagnostic_hypotheses": diagnostic_hypotheses,
            "raw_response": doctor_response
        },
        status="completed"
    )
    
    print(f"\n结果已保存: {output_file}")
    
    print("\n" + "=" * 60)
    print("第五阶段完成")
    print("=" * 60)
    
    return {
        "diagnostic_hypotheses": diagnostic_hypotheses,
        "raw_response": doctor_response,
        "output_file": str(output_file),
        "doctor": doctor,
        "model_name": model_name,
        "case_id": case_id
    }


if __name__ == "__main__":
    print("=" * 60)
    print("单独测试：第五阶段 Diagnostic Hypotheses")
    print("=" * 60)
    print("\n注意：第五阶段需要先运行前四阶段获取医生实例")
    print("建议直接使用 run_interview.py 运行完整流程")
    print("\n" + "=" * 60)
