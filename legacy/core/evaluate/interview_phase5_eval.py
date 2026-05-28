"""
精神科访谈评估模块 - 第五阶段：Treatment Planning Evaluation

评估：
- 主观评估：Treatment Appropriateness（治疗合理性）
  使用 Rubric Format 模板 + Treatment Appropriateness 量表
  测试内容：[BEGIN_TREATMENT_PLAN] 和 [END_TREATMENT_PLAN] 包裹的治疗建议
"""

import json
from pathlib import Path
from typing import Dict, Any, Union


def evaluate_phase5(
    model_name: str = None,
    case_id: str = None,
    output_file: Union[str, Path] = None,
    phase5_data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """评估第五阶段访谈（Treatment Planning）"""
    if phase5_data is None:
        if output_file is None:
            if model_name is None or case_id is None:
                raise ValueError("必须提供 model_name+case_id 或 output_file 或 phase5_data")
            from core.output_manager import get_phase_output_file
            output_file = get_phase_output_file(model_name, case_id, 5)

        output_file = Path(output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            phase5_data = json.load(f)

    model_name = phase5_data.get("model_name", model_name)
    case_id = phase5_data.get("case_id", case_id)

    if model_name is None or case_id is None:
        raise ValueError("无法确定 model_name 或 case_id")

    treatment_plan = phase5_data.get('treatment_plan', '')
    status = phase5_data.get('status', 'unknown')

    evaluation_data = {
        "status": status,
        "treatment_plan_length": len(treatment_plan),
    }

    # ========== 主观评估：Treatment Appropriateness ==========
    treatment_subjective = None
    if treatment_plan and treatment_plan.strip():
        try:
            from core.evaluate.subjective_assessment.subjective_evaluator import SubjectiveEvaluator
            from core.evaluate.subjective_assessment.prompt import PROMPTS as SUBJECTIVE_PROMPTS

            print(f"\n开始主观评估：治疗合理性（5 评估器并行）...")
            rubric = SUBJECTIVE_PROMPTS["Treatment Appropriateness"]

            treatment_subjective = SubjectiveEvaluator.evaluate_multi(
                rubric_content=rubric,
                test_context=treatment_plan
            )

            evaluation_data["treatment_subjective"] = treatment_subjective

            try:
                from core.evaluate.trajectory_collector import collect_from_evaluation_result
                evaluation_data["treatment_trajectory"] = collect_from_evaluation_result(
                    "Treat", treatment_subjective, case_id, test_model=model_name
                )
            except Exception as e:
                print(f"  治疗合理性轨迹收集失败: {e}")

            score = treatment_subjective.get('score', 'N/A')
            scores = treatment_subjective.get('scores', [])
            print(f"  治疗合理性均分: {score}/5 (各评分: {scores}) (成功解析: {treatment_subjective.get('parsed_count')}/5)")

            eval_output_file = save_evaluation_result_with_data(model_name, case_id, 5, evaluation_data)
            print(f"  评估结果保存: {eval_output_file}")
        except Exception as e:
            print(f"  治疗合理性主观评估失败: {e}")
            import traceback
            traceback.print_exc()
            eval_output_file = save_evaluation_result_with_data(model_name, case_id, 5, evaluation_data)
    else:
        print(f"\nPhase 5 (Treatment Planning) 评估结果:")
        print(f"  状态: {status}")
        print(f"  治疗建议为空，跳过评估")
        eval_output_file = save_evaluation_result_with_data(model_name, case_id, 5, evaluation_data)

    return {
        "treatment_subjective": treatment_subjective,
        "status": status,
        "output_file": str(eval_output_file),
        "model_name": model_name,
        "case_id": case_id
    }


def save_evaluation_result_with_data(
    model_name: str,
    case_id: str,
    phase: int,
    evaluation_data: Dict[str, Any]
) -> Path:
    """保存评估结果到文件"""
    from core.evaluate.interview_phase1_eval import save_evaluation_result
    return save_evaluation_result(model_name, case_id, phase, evaluation_data)


if __name__ == "__main__":
    print("Phase 5 评估模块：治疗合理性主观评估")

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

                    result = evaluate_phase5(model_name=model_name, case_id=case_id)

                    print("\n" + "=" * 60)
                    print("测试完成")
                    print("=" * 60)
                else:
                    print("未找到病例数据，请先运行 interview_phase5")
            else:
                print("未找到模型数据，请先运行 interview_phase5")
        else:
            print("输出目录不存在，请先运行 interview_phase5")

    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
