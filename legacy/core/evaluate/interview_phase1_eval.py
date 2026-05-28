"""
精神科访谈评估模块 - 第一阶段：Clinical History Collection Evaluation

使用方法:
    from core.evaluate.interview_phase1_eval import evaluate_phase1

    result = evaluate_phase1(model_name="qwen-flash", case_id="1009904")
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_evaluation_dir(model_name: str, case_id: str) -> Path:
    """获取评估输出目录路径"""
    output_dir = Path(__file__).parent.parent.parent / "data" / "output" / "evaluation" / model_name / case_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_evaluation_output_file(model_name: str, case_id: str, phase: int) -> Path:
    """获取指定阶段的评估输出文件路径"""
    output_dir = get_evaluation_dir(model_name, case_id)
    return output_dir / f"evaluation_phase{phase}_output.json"


def save_evaluation_result(
    model_name: str,
    case_id: str,
    phase: int,
    evaluation_data: Dict[str, Any]
) -> Path:
    """保存评估结果到文件"""
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


def calculate_coverage_stats(
    chief_complaint_all: List[str],
    mental_status_all: List[str],
    chief_complaint_used: List[str],
    mental_status_used: List[str]
) -> Dict[str, Any]:
    """计算覆盖率统计"""
    chief_complaint_all = [item.strip() if isinstance(item, str) else item for item in chief_complaint_all]
    mental_status_all = [item.strip() if isinstance(item, str) else item for item in mental_status_all]
    chief_complaint_used = [item.strip() if isinstance(item, str) else item for item in chief_complaint_used]
    mental_status_used = [item.strip() if isinstance(item, str) else item for item in mental_status_used]

    # 过滤：只保留在 gold all 中存在的 used 条目
    cc_all_set = set(chief_complaint_all)
    ms_all_set = set(mental_status_all)
    chief_complaint_used = [item for item in chief_complaint_used if item in cc_all_set]
    mental_status_used = [item for item in mental_status_used if item in ms_all_set]

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
    """计算对话统计"""
    patient_turns = len([c for c in conversation if c['role'] == 'patient'])
    doctor_turns = len([c for c in conversation if c['role'] == 'doctor'])

    return {
        'total_turns': patient_turns,
        'patient_turns': patient_turns,
        'doctor_turns': doctor_turns,
        'conversation_length': len(conversation)
    }


def format_conversation_text(conversation: List[Dict[str, Any]]) -> str:
    """将对话列表格式化为文本"""
    lines = []
    for idx, turn in enumerate(conversation, 1):
        role = turn.get('role', 'unknown')
        content = turn.get('content', '')

        if role == 'doctor':
            lines.append(f"[第{idx}轮] 医生：{content}")
        elif role == 'patient':
            lines.append(f"[第{idx}轮] 患者：{content}")
        else:
            lines.append(f"[第{idx}轮] [{role}]：{content}")

    return "\n\n".join(lines)


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

    Args:
        model_name: 医生模型名称
        case_id: 病例ID
        output_file: interview_phase1输出文件路径
        phase1_data: interview_phase1数据字典
        enable_empathy_eval: 是否启用共情度评估（默认 True）
        enable_profession_eval: 是否启用专业度评估（默认 True）
        parallel_eval: 是否并行评估共情度和专业度（默认 True）
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
        chief_complaint_all, mental_status_all,
        chief_complaint_used, mental_status_used
    )

    conversation_stats = calculate_conversation_stats(conversation)

    evaluation_data = {
        "coverage_stats": coverage_stats,
        "conversation_stats": conversation_stats,
        "status": status,
    }

    empathy_eval_result = None
    profession_eval_result = None

    if enable_empathy_eval or enable_profession_eval:
        print("\n开始主观 Rubric 评估（5 评估器并行）...")
        conversation_text = format_conversation_text(conversation)

        try:
            from core.evaluate.subjective_assessment.subjective_evaluator import SubjectiveEvaluator
            from core.evaluate.subjective_assessment.prompt import PROMPTS as SUBJECTIVE_PROMPTS

            def run_empathy_multi():
                if not enable_empathy_eval:
                    return None
                print("  评估沟通共情程度...")
                rubric = SUBJECTIVE_PROMPTS["Communication Empathy"]
                return SubjectiveEvaluator.evaluate_multi(
                    rubric_content=rubric, test_context=conversation_text
                )

            def run_profession_multi():
                if not enable_profession_eval:
                    return None
                print("  评估对话专业程度...")
                rubric = SUBJECTIVE_PROMPTS["Interviewing Professionalism"]
                return SubjectiveEvaluator.evaluate_multi(
                    rubric_content=rubric, test_context=conversation_text
                )

            if enable_empathy_eval and enable_profession_eval and parallel_eval:
                print("  并行评估共情度和专业度...")
                with ThreadPoolExecutor(max_workers=2) as executor:
                    future_empathy = executor.submit(run_empathy_multi)
                    future_profession = executor.submit(run_profession_multi)
                    empathy_eval_result = future_empathy.result()
                    profession_eval_result = future_profession.result()
            else:
                empathy_eval_result = run_empathy_multi()
                profession_eval_result = run_profession_multi()

            if empathy_eval_result:
                evaluation_data["empathy_evaluation"] = empathy_eval_result
                try:
                    from core.evaluate.trajectory_collector import collect_from_evaluation_result
                    evaluation_data["empathy_trajectory"] = collect_from_evaluation_result(
                        "Emp", empathy_eval_result, case_id, test_model=model_name
                    )
                except Exception as e:
                    print(f"  共情度轨迹收集失败: {e}")

            if profession_eval_result:
                evaluation_data["profession_evaluation"] = profession_eval_result
                try:
                    from core.evaluate.trajectory_collector import collect_from_evaluation_result
                    evaluation_data["profession_trajectory"] = collect_from_evaluation_result(
                        "Pro", profession_eval_result, case_id, test_model=model_name
                    )
                except Exception as e:
                    print(f"  专业度轨迹收集失败: {e}")

            print("  主观评估完成")

        except Exception as e:
            print(f"  主观评估失败: {e}")
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
        score = empathy_eval_result.get('score', 'N/A')
        scores = empathy_eval_result.get('scores', [])
        print(f"\n  共情度评估 (5 评估器均值):")
        print(f"    均分: {score}/5 (各评分: {scores}) (成功解析: {empathy_eval_result.get('parsed_count')}/5)")

    if profession_eval_result:
        score = profession_eval_result.get('score', 'N/A')
        scores = profession_eval_result.get('scores', [])
        print(f"\n  专业度评估 (5 评估器均值):")
        print(f"    均分: {score}/5 (各评分: {scores}) (成功解析: {profession_eval_result.get('parsed_count')}/5)")

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
