"""
精神科访谈评估模块 - 第一阶段：Clinical History Collection Evaluation

使用方法:
    from core.evaluate.interview_phase1_eval import evaluate_phase1
    
    # 从interview_phase1的输出文件中读取数据并评估
    result = evaluate_phase1(
        model_name="qwen-flash",
        case_id="1009904"
    )
    
    # 或者直接传入数据
    result = evaluate_phase1(
        output_file="/path/to/interview_phase1_output.json"
    )
    
    # 结果包含:
    # - coverage_stats: 覆盖率统计
    # - conversation_stats: 对话统计
    # - empathy_evaluation: 共情度评估（可选）
    # - profession_evaluation: 专业度评估（可选）
    # - output_file: 评估结果保存路径
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


def get_evaluation_dir(model_name: str, case_id: str) -> Path:
    """获取评估输出目录路径
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        
    Returns:
        评估输出目录路径
    """
    output_dir = Path(__file__).parent.parent.parent / "data" / "output" / "evaluation" / model_name / case_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_evaluation_output_file(model_name: str, case_id: str, phase: int) -> Path:
    """获取指定阶段的评估输出文件路径
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        phase: 阶段编号 (1-6)
        
    Returns:
        评估输出文件路径
    """
    output_dir = get_evaluation_dir(model_name, case_id)
    return output_dir / f"evaluation_phase{phase}_output.json"


def calculate_coverage_stats(
    chief_complaint_all: List[str],
    mental_status_all: List[str],
    chief_complaint_used: List[str],
    mental_status_used: List[str]
) -> Dict[str, Any]:
    """计算覆盖率统计
    
    Args:
        chief_complaint_all: 所有主诉条目
        mental_status_all: 所有精神状态条目
        chief_complaint_used: 使用的主诉条目
        mental_status_used: 使用的精神状态条目
        
    Returns:
        覆盖率统计字典
    """
    cc_coverage = (len(chief_complaint_used) / len(chief_complaint_all) * 100) if chief_complaint_all else 0.0
    ms_coverage = (len(mental_status_used) / len(mental_status_all) * 100) if mental_status_all else 0.0
    
    total_items = len(chief_complaint_all) + len(mental_status_all)
    total_used = len(chief_complaint_used) + len(mental_status_used)
    overall_coverage = (total_used / total_items * 100) if total_items else 0.0
    
    return {
        'chief_complaint_coverage': round(cc_coverage, 2),
        'mental_status_coverage': round(ms_coverage, 2),
        'overall_coverage': round(overall_coverage, 2),
        'chief_complaint_used_count': len(chief_complaint_used),
        'chief_complaint_total_count': len(chief_complaint_all),
        'mental_status_used_count': len(mental_status_used),
        'mental_status_total_count': len(mental_status_all)
    }


def calculate_conversation_stats(conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算对话统计
    
    Args:
        conversation: 对话记录列表
        
    Returns:
        对话统计字典
    """
    patient_turns = len([c for c in conversation if c['role'] == 'patient'])
    doctor_turns = len([c for c in conversation if c['role'] == 'doctor'])
    
    return {
        'total_turns': patient_turns,
        'patient_turns': patient_turns,
        'doctor_turns': doctor_turns,
        'conversation_length': len(conversation)
    }


def format_conversation_text(conversation: List[Dict[str, Any]]) -> str:
    """将对话列表格式化为文本
    
    Args:
        conversation: 对话记录列表
        
    Returns:
        格式化后的对话文本
    """
    lines = []
    for turn in conversation:
        role = turn.get('role', 'unknown')
        content = turn.get('content', '')
        
        if role == 'doctor':
            lines.append(f"医生：{content}")
        elif role == 'patient':
            lines.append(f"患者：{content}")
        else:
            lines.append(f"[{role}]：{content}")
    
    return "\n\n".join(lines)


def save_evaluation_result(
    model_name: str,
    case_id: str,
    phase: int,
    evaluation_data: Dict[str, Any]
) -> Path:
    """保存评估结果到文件
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        phase: 阶段编号
        evaluation_data: 评估数据
        
    Returns:
        评估结果文件路径
    """
    output_file = get_evaluation_output_file(model_name, case_id, phase)
    
    result = {
        "phase": phase,
        "case_id": case_id,
        "model_name": model_name,
        "timestamp": datetime.now().isoformat(),
        **evaluation_data
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return output_file


def evaluate_phase1(
    model_name: str = None,
    case_id: str = None,
    output_file: Union[str, Path] = None,
    phase1_data: Dict[str, Any] = None,
    enable_empathy_eval: bool = True,
    enable_profession_eval: bool = True,
    parallel_eval: bool = True
) -> Dict[str, Any]:
    """评估第一阶段访谈
    
    可以通过以下方式之一提供数据：
    1. 提供 model_name 和 case_id（从默认路径读取）
    2. 提供 output_file（直接读取指定文件）
    3. 提供 phase1_data（直接使用数据）
    
    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        output_file: interview_phase1输出文件路径
        phase1_data: interview_phase1数据字典
        enable_empathy_eval: 是否启用共情度评估（默认 True）
        enable_profession_eval: 是否启用专业度评估（默认 True）
        parallel_eval: 是否并行评估共情度和专业度（默认 True）
        
    Returns:
        评估结果字典，包含：
        - coverage_stats: 覆盖率统计
        - conversation_stats: 对话统计
        - status: 访谈状态
        - empathy_evaluation: 共情度评估结果（如果启用）
        - profession_evaluation: 专业度评估结果（如果启用）
        - output_file: 评估结果保存路径
    """
    if phase1_data is None:
        if output_file is None:
            if model_name is None or case_id is None:
                raise ValueError("必须提供 model_name+case_id 或 output_file 或 phase1_data")
            from core.output_manager import get_phase_output_file
            output_file = get_phase_output_file(model_name, case_id, 1)
        
        output_file = Path(output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            phase1_data = json.load(f)
    
    model_name = phase1_data.get("model_name", model_name)
    case_id = phase1_data.get("case_id", case_id)
    
    if model_name is None or case_id is None:
        raise ValueError("无法确定 model_name 或 case_id")
    
    chief_complaint_all = phase1_data.get('chief_complaint_all', [])
    mental_status_all = phase1_data.get('mental_status_all', [])
    chief_complaint_used = phase1_data.get('chief_complaint_used', [])
    mental_status_used = phase1_data.get('mental_status_used', [])
    conversation = phase1_data.get('conversation', [])
    status = phase1_data.get('status', 'unknown')
    
    coverage_stats = calculate_coverage_stats(
        chief_complaint_all,
        mental_status_all,
        chief_complaint_used,
        mental_status_used
    )
    
    conversation_stats = calculate_conversation_stats(conversation)
    
    evaluation_data = {
        "coverage_stats": coverage_stats,
        "conversation_stats": conversation_stats,
        "status": status,
        "chief_complaint_all": chief_complaint_all,
        "mental_status_all": mental_status_all,
        "chief_complaint_used": chief_complaint_used,
        "mental_status_used": mental_status_used
    }
    
    empathy_eval_result = None
    profession_eval_result = None
    
    if enable_empathy_eval or enable_profession_eval:
        print("\n开始 LLM 评估...")
        conversation_text = format_conversation_text(conversation)
        
        try:
            from core.evaluate.utils.phase1 import evaluate_empathy, evaluate_profession
            
            if enable_empathy_eval and enable_profession_eval:
                from core.evaluate.utils.phase1 import evaluate_both
                
                print("  并行评估共情度和专业度...")
                both_results = evaluate_both(conversation_text, parallel=parallel_eval)
                empathy_eval_result = both_results["empathy"]
                profession_eval_result = both_results["profession"]
            elif enable_empathy_eval:
                print("  评估共情度...")
                empathy_eval_result = evaluate_empathy(conversation_text)
            elif enable_profession_eval:
                print("  评估专业度...")
                profession_eval_result = evaluate_profession(conversation_text)
            
            if empathy_eval_result:
                evaluation_data["empathy_evaluation"] = {
                    "empathy_level": empathy_eval_result.get("empathy_level"),
                    "why_this_level": empathy_eval_result.get("why_this_level", ""),
                    "why_not_higher_levels": empathy_eval_result.get("why_not_higher_levels", ""),
                    "why_not_lower_levels": empathy_eval_result.get("why_not_lower_levels", ""),
                    "evidence": empathy_eval_result.get("evidence", ""),
                    "level_count": empathy_eval_result.get("level_count", 0)
                }
            
            if profession_eval_result:
                evaluation_data["profession_evaluation"] = {
                    "total_score": profession_eval_result["total_score"],
                    "average_score": profession_eval_result["average_score"],
                    "question_count": profession_eval_result["question_count"],
                    "parsed_scores": profession_eval_result["parsed_scores"],
                    "raw_response": profession_eval_result.get("raw_response", "")  # 保存原始响应
                }
            
            print("  LLM 评估完成")
            
        except Exception as e:
            print(f"  LLM 评估失败: {e}")
            import traceback
            traceback.print_exc()
    
    eval_output_file = save_evaluation_result(model_name, case_id, 1, evaluation_data)
    
    print(f"\nPhase 1 评估结果:")
    print(f"  状态: {status}")
    print(f"  对话轮数: {conversation_stats['total_turns']}")
    print(f"  主诉覆盖率: {coverage_stats['chief_complaint_coverage']:.2f}%")
    print(f"  精神状态覆盖率: {coverage_stats['mental_status_coverage']:.2f}%")
    print(f"  整体覆盖率: {coverage_stats['overall_coverage']:.2f}%")
    
    if empathy_eval_result:
        print(f"\n  共情度评估:")
        empathy_level = empathy_eval_result.get('empathy_level', 'N/A')
        print(f"    共情等级: {empathy_level}")
        why_this = empathy_eval_result.get('why_this_level', '')
        if why_this:
            print(f"    评级理由: {why_this[:100]}...")
    
    if profession_eval_result:
        print(f"\n  专业度评估:")
        print(f"    总分: {profession_eval_result['total_score']}/{profession_eval_result['question_count'] * 2}")
        print(f"    平均分: {profession_eval_result['average_score']:.2f}")
    
    print(f"\n  评估结果保存: {eval_output_file}")
    
    return {
        "coverage_stats": coverage_stats,
        "conversation_stats": conversation_stats,
        "status": status,
        "empathy_evaluation": empathy_eval_result,
        "profession_evaluation": profession_eval_result,
        "output_file": str(eval_output_file),
        "model_name": model_name,
        "case_id": case_id
    }


if __name__ == "__main__":
    print("=" * 60)
    print("测试：Phase 1 评估模块")
    print("=" * 60)
    
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    try:
        from core.output_manager import get_output_dir
        
        output_base = Path(__file__).parent.parent.parent / "data" / "output" / "interview"
        
        if output_base.exists():
            model_dirs = list(output_base.iterdir())
            if model_dirs:
                model_dir = model_dirs[0]
                case_dirs = list(model_dir.iterdir())
                if case_dirs:
                    case_dir = case_dirs[0]
                    model_name = model_dir.name
                    case_id = case_dir.name
                    
                    print(f"\n使用现有数据测试:")
                    print(f"  模型: {model_name}")
                    print(f"  病例: {case_id}")
                    
                    result = evaluate_phase1(model_name=model_name, case_id=case_id)
                    
                    print("\n" + "=" * 60)
                    print("测试完成")
                    print("=" * 60)
                else:
                    print("未找到病例数据，请先运行 interview_phase1")
            else:
                print("未找到模型数据，请先运行 interview_phase1")
        else:
            print("输出目录不存在，请先运行 interview_phase1")
            
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
