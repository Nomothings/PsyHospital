"""
精神科访谈执行模块 - 第四阶段：Diagnostic Category Identification

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
    # - diagnostic_categories: 诊断类别列表
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


def parse_diagnostic_category(response: str) -> List[str]:
    """解析医生生成的诊断类别
    
    Args:
        response: 医生的响应内容
        
    Returns:
        诊断类别列表，如果解析失败返回空列表
    """
    try:
        match = re.search(
            r'\[BEGIN_DIAGNOSTIC_CATEGORY\](.*?)\[END_DIAGNOSTIC_CATEGORY\]',
            response,
            re.DOTALL | re.IGNORECASE
        )
        
        if match:
            content = match.group(1).strip()
            categories = json.loads(content)
            if isinstance(categories, list):
                return categories
            return []
        
        return []
    except (json.JSONDecodeError, AttributeError, TypeError):
        return []


def run_interview_phase4(
    doctor,
    model_name: str,
    case_id: str
) -> Dict[str, Any]:
    """运行第四阶段访谈：Diagnostic Category Identification
    
    基于前三阶段的对话上下文，让医生判断当前病例最可能涉及的诊断类别。
    
    Args:
        doctor: 医生LLMService实例（从phase3传递过来，保持对话上下文）
        model_name: 医生模型名称
        case_id: 病例ID
        
    Returns:
        结果字典，包含：
        - diagnostic_categories: 诊断类别列表
        - raw_response: 医生的原始响应
        - output_file: 保存的文件路径
        - doctor: 医生LLMService实例（保持对话上下文，用于传递到下一阶段）
        - model_name: 医生模型名称
        - case_id: 病例ID
        
    使用示例:
        phase4_result = run_interview_phase4(
            doctor=phase3_result['doctor'],
            model_name=phase3_result['model_name'],
            case_id=phase3_result['case_id']
        )
    """
    print("\n" + "=" * 60)
    print("开始第四阶段：Diagnostic Category Identification")
    print("=" * 60)
    
    output_file = init_phase_output(
        model_name=model_name,
        case_id=case_id,
        phase=4,
        initial_data={
            "diagnostic_categories": [],
            "raw_response": ""
        }
    )
    print(f"  输出文件: {output_file}")
    
    print("\n" + "-" * 60)
    print("医生判断诊断类别")
    print("-" * 60)
    
    prompt = PROMPTS["Diagnostic Category Identification"]
    
    print(f"\nPrompt长度: {len(prompt)} 字符")
    
    print(f"\n医生思考中...")
    doctor_response = doctor.chat(prompt)
    
    print(f"\n医生原始响应:")
    print(f"  {doctor_response[:500]}...")
    
    diagnostic_categories = parse_diagnostic_category(doctor_response)
    
    print(f"\n解析结果:")
    if diagnostic_categories:
        print(f"  诊断类别数量: {len(diagnostic_categories)}")
        for i, category in enumerate(diagnostic_categories, 1):
            print(f"    {i}. {category}")
    else:
        print(f"  （未能解析出诊断类别）")
    
    update_phase_output(
        output_file,
        {
            "diagnostic_categories": diagnostic_categories,
            "raw_response": doctor_response
        },
        status="completed"
    )
    
    print(f"\n结果已保存: {output_file}")
    
    print("\n" + "=" * 60)
    print("第四阶段完成")
    print("=" * 60)
    
    return {
        "diagnostic_categories": diagnostic_categories,
        "raw_response": doctor_response,
        "output_file": str(output_file),
        "doctor": doctor,
        "model_name": model_name,
        "case_id": case_id
    }


if __name__ == "__main__":
    print("=" * 60)
    print("单独测试：第四阶段 Diagnostic Category Identification")
    print("=" * 60)
    print("\n注意：第四阶段需要先运行前三阶段获取医生实例")
    print("建议直接使用 run_interview.py 运行完整流程")
    print("\n" + "=" * 60)
