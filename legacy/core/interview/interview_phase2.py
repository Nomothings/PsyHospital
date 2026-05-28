"""
精神科访谈执行模块 - 第二阶段：Examination Recommendation

使用方法:
    # 方式1：单独测试第二阶段（需要传入phase1的结果）
    python core/interview_phase2.py
    
    # 方式2：作为完整流程的一部分
    from core.interview_phase2 import run_interview_phase2
    
    # 传入phase1的结果和病例数据
    result = run_interview_phase2(
        doctor=phase1_result['doctor'],
        model_name=phase1_result['model_name'],
        case_id=phase1_result['case_id'],
        case_data=phase1_result['case_data']
    )
    
    # 结果包含:
    # - examinations: 推荐的检查项目列表
    # - examination_results: Instrument返回的检查结果
    # - evaluation_metrics: 评估指标 (Precision/Recall/F1/Jaccard)
    # - raw_response: 医生的原始响应
    # - output_file: 保存的文件路径
    # - doctor: 医生LLM实例（用于传递到下一阶段）
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from core.interview.prompts import PROMPTS
from core.output_manager import init_phase_output, update_phase_output, get_phase_output_file
from agents.instrument.instrument import create_instrument, chat_and_evaluate_instrument

# 加载.env
load_dotenv(Path(__file__).parent.parent / ".env")


def parse_examinations(response: str) -> List[str]:
    """解析医生推荐的检查项目
    
    Args:
        response: 医生的响应内容
        
    Returns:
        检查项目列表，如果解析失败返回空列表
    """
    try:
        # 提取 [BEGIN_EXAMINATIONS] 和 [END_EXAMINATIONS] 之间的内容
        match = re.search(
            r'\[BEGIN_EXAMINATIONS\](.*?)\[END_EXAMINATIONS\]',
            response,
            re.DOTALL | re.IGNORECASE
        )
        
        if match:
            content = match.group(1).strip()
            # 尝试解析JSON数组
            examinations = json.loads(content)
            if isinstance(examinations, list):
                return [str(item).strip() for item in examinations if item]
        
        return []
    except (json.JSONDecodeError, AttributeError):
        return []


def run_interview_phase2(
    doctor,
    model_name: str,
    case_id: str,
    case_data: Dict[str, Any] = None,
    instrument_backup: bool = False
) -> Dict[str, Any]:
    """运行第二阶段访谈：Examination Recommendation
    
    基于第一阶段的对话上下文，让医生推荐辅助检查项目，
    然后使用Instrument进行评估。
    
    Args:
        doctor: 医生LLMService实例（从phase1传递过来，保持对话上下文）
        model_name: 医生模型名称
        case_id: 病例ID
        case_data: 病例数据，包含auxiliaryExamination字段
        
    Returns:
        结果字典，包含：
        - examinations: 推荐的检查项目列表
        - examination_results: Instrument返回的检查结果
        - evaluation_metrics: 评估指标 (Precision/Recall/F1/Jaccard)
        - raw_response: 医生的原始响应
        - output_file: 保存的文件路径
        - doctor: 医生LLMService实例（保持对话上下文，用于传递到下一阶段）
        
    使用示例:
        # 从phase1获取医生实例
        phase1_result = run_interview_phase1()
        
        # 运行phase2
        phase2_result = run_interview_phase2(
            doctor=phase1_result['doctor'],
            model_name=phase1_result['model_name'],
            case_id=phase1_result['case_id'],
            case_data=phase1_result['case_data']
        )
        
        # 获取推荐的检查项目
        examinations = phase2_result['examinations']
        # 获取评估指标
        metrics = phase2_result['evaluation_metrics']
    """
    print("\n" + "=" * 60)
    print("开始第二阶段：Examination Recommendation")
    print("=" * 60)
    
    # 初始化输出文件
    output_file = init_phase_output(
        model_name=model_name,
        case_id=case_id,
        phase=2,
        initial_data={
            "examinations": [],
            "examination_results": {},
            "evaluation_metrics": {},
            "raw_response": ""
        }
    )
    print(f"  输出文件: {output_file}")
    
    # ========== 1. 医生推荐检查项目 ==========
    print("\n" + "-" * 60)
    print("步骤1：医生推荐检查项目")
    print("-" * 60)
    
    # 获取prompt
    prompt = PROMPTS["Examination Recommendation"]
    
    print(f"\n[System -> Doctor] 发送第二阶段prompt...")
    print(f"  Prompt长度: {len(prompt)} 字符")
    
    # 医生生成检查推荐
    print(f"\n医生思考中...")
    doctor_response = doctor.chat(prompt)
    
    print(f"\n医生原始响应:")
    print(f"  {doctor_response[:500]}...")
    
    # 解析检查项目
    examinations = parse_examinations(doctor_response)
    
    print(f"\n解析结果:")
    print(f"  推荐检查项目数: {len(examinations)}")
    if examinations:
        for i, exam in enumerate(examinations, 1):
            print(f"    {i}. {exam}")
    else:
        print(f"    （无需辅助检查）")
    
    # 即时更新输出文件（医生推荐部分）
    update_phase_output(
        output_file,
        {
            "examinations": examinations,
            "raw_response": doctor_response
        }
    )
    
    # ========== 2. Instrument获取检查结果（如果有病例数据） ==========
    examination_results = {}
    
    if case_data and examinations:
        print("\n" + "-" * 60)
        print("步骤2：Instrument获取检查结果")
        print("-" * 60)
        
        auxiliary_examination = case_data.get("auxiliaryExamination", {})
        
        if auxiliary_examination:
            examination_query = json.dumps(examinations, ensure_ascii=False)
            auxiliary_examinations_str = json.dumps(auxiliary_examination, ensure_ascii=False)
            
            print(f"\n医生请求的检查项目:")
            print(f"  {examination_query}")
            print(f"\n病例中的辅助检查信息:")
            print(f"  {auxiliary_examinations_str[:200]}...")
            
            try:
                print(f"\n启动Instrument服务...")
                instrument = create_instrument(
                    examination_query=examination_query,
                    auxiliary_examinations=auxiliary_examinations_str,
                    backup=instrument_backup
                )
                
                print(f"\n调用Instrument获取检查结果...")
                instrument_result = chat_and_evaluate_instrument(instrument)
                
                examination_results = instrument_result.get("response", {})
                
                print(f"\nInstrument返回结果:")
                for key, value in examination_results.items():
                    print(f"  {key}: {value}")
                
                update_phase_output(
                    output_file,
                    {
                        "examination_results": examination_results
                    },
                    status="completed"
                )
                
            except Exception as e:
                print(f"\n[!] Instrument获取检查结果失败: {e}")
                update_phase_output(output_file, {}, status="completed_with_error")
        else:
            print(f"\n[!] 病例中没有辅助检查信息，跳过Instrument")
            update_phase_output(output_file, {}, status="completed_no_gold")
    else:
        if not case_data:
            print(f"\n[!] 未提供病例数据，跳过Instrument评估")
        elif not examinations:
            print(f"\n[!] 医生未推荐任何检查项目，跳过Instrument评估")
        update_phase_output(output_file, {}, status="completed")
    
    print(f"\n结果已保存: {output_file}")
    
    print("\n" + "=" * 60)
    print("第二阶段完成")
    print("=" * 60)
    
    return {
        "examinations": examinations,
        "examination_results": examination_results,
        "raw_response": doctor_response,
        "output_file": str(output_file),
        "doctor": doctor,
        "model_name": model_name,
        "case_id": case_id
    }


if __name__ == "__main__":
    """单独测试第二阶段（需要先运行第一阶段获取doctor实例）"""
    print("=" * 60)
    print("单独测试：第二阶段 Examination Recommendation")
    print("=" * 60)
    print("\n注意：第二阶段需要先运行第一阶段获取医生实例")
    print("建议直接使用 run_interview.py 运行完整流程")
    print("\n或者按以下方式测试：")
    print("  1. from core.interview_phase1 import run_interview_phase1")
    print("  2. phase1_result = run_interview_phase1()")
    print("  3. from core.interview_phase2 import run_interview_phase2")
    print("  4. phase2_result = run_interview_phase2(")
    print("         doctor=phase1_result['doctor'],")
    print("         model_name=phase1_result['model_name'],")
    print("         case_id=phase1_result['case_id'],")
    print("         case_data=phase1_result['case_data']")
    print("     )")
    print("\n" + "=" * 60)
