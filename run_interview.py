"""
精神科访谈完整流程 - 联合运行 Phase 1-6

使用方法:
    python run_interview.py
    
流程:
    Phase 1: Clinical History Collection (医患对话收集病史)
    Phase 1 Eval: 评估病史采集效果
    Phase 2: Examination Recommendation (推荐辅助检查)
    Phase 2 Eval: 评估检查推荐效果
    Phase 3: Clinical Formulation (整理临床病历)
    Phase 3 Eval: 评估临床病历质量
    Phase 4: Diagnostic Category Identification (诊断类别识别)
    Phase 4 Eval: 评估诊断类别识别效果
    Phase 5: Diagnostic Hypotheses (生成诊断假设)
    Phase 5 Eval: 评估诊断假设效果
    Phase 6: Differential Diagnosis (鉴别诊断)
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from core.interview.interview_phase1 import run_interview_phase1, load_random_case
from core.interview.interview_phase2 import run_interview_phase2
from core.interview.interview_phase3 import run_interview_phase3
from core.interview.interview_phase4 import run_interview_phase4
from core.interview.interview_phase5 import run_interview_phase5
from core.interview.interview_phase6 import run_interview_phase6
from core.evaluate.interview_phase1_eval import evaluate_phase1
from core.evaluate.interview_phase2_eval import evaluate_phase2
from core.evaluate.interview_phase3_eval import evaluate_phase3
from core.evaluate.interview_phase4_eval import evaluate_phase4
from core.evaluate.interview_phase5_eval import evaluate_phase5
from core.evaluate.interview_phase6_eval import evaluate_phase6


def run_full_interview(case: Dict[str, Any] = None) -> Dict[str, Any]:
    """运行完整的六阶段访谈流程
    
    Args:
        case: 可选，指定病例数据。如果不提供，则随机加载一个病例
        
    Returns:
        完整流程的结果字典
    """
    print("\n" + "=" * 70)
    print(" " * 20 + "精神科访谈完整流程")
    print("=" * 70)
    
    # ========== Phase 1: Clinical History Collection ==========
    print("\n" + "-" * 70)
    print("Phase 1/6: Clinical History Collection")
    print("-" * 70)
    
    phase1_result = run_interview_phase1(case=case)
    
    print(f"\nPhase 1 完成:")
    print(f"  对话轮数: {len([c for c in phase1_result['conversation'] if c['role'] == 'patient'])}")
    print(f"  输出文件: {phase1_result['output_file']}")
    
    # ========== Phase 1 Evaluation ==========
    print("\n" + "-" * 70)
    print("Phase 1 Evaluation: Clinical History Collection Evaluation")
    print("-" * 70)
    
    phase1_eval_result = evaluate_phase1(
        model_name=phase1_result['model_name'],
        case_id=phase1_result['case_id']
    )
    
    # ========== Phase 2: Examination Recommendation ==========
    print("\n" + "-" * 70)
    print("Phase 2/6: Examination Recommendation")
    print("-" * 70)
    
    phase2_result = run_interview_phase2(
        doctor=phase1_result['doctor'],
        model_name=phase1_result['model_name'],
        case_id=phase1_result['case_id'],
        case_data=phase1_result['case_data']
    )
    
    print(f"\nPhase 2 完成:")
    print(f"  推荐检查项目: {len(phase2_result['examinations'])} 项")
    if phase2_result['examinations']:
        for i, exam in enumerate(phase2_result['examinations'], 1):
            print(f"    {i}. {exam}")
    else:
        print(f"    （无需辅助检查）")
    print(f"  输出文件: {phase2_result['output_file']}")
    
    # ========== Phase 2 Evaluation ==========
    print("\n" + "-" * 70)
    print("Phase 2 Evaluation: Examination Recommendation Evaluation")
    print("-" * 70)
    
    phase2_eval_result = evaluate_phase2(
        model_name=phase2_result['model_name'],
        case_id=phase2_result['case_id'],
        case_data=phase1_result['case_data']
    )
    
    # ========== Phase 3: Clinical Formulation ==========
    print("\n" + "-" * 70)
    print("Phase 3/6: Clinical Formulation")
    print("-" * 70)
    
    phase3_result = run_interview_phase3(
        doctor=phase2_result['doctor'],
        model_name=phase2_result['model_name'],
        case_id=phase2_result['case_id'],
        examination_results=phase2_result['examination_results']
    )
    
    print(f"\nPhase 3 完成:")
    print(f"  临床病历长度: {len(phase3_result['syntactic_formulation'])} 字符")
    print(f"  输出文件: {phase3_result['output_file']}")
    
    # ========== Phase 3 Evaluation ==========
    print("\n" + "-" * 70)
    print("Phase 3 Evaluation: Clinical Formulation Evaluation")
    print("-" * 70)
    
    phase3_eval_result = evaluate_phase3(
        model_name=phase3_result['model_name'],
        case_id=phase3_result['case_id']
    )
    
    # ========== Phase 4: Diagnostic Category Identification ==========
    print("\n" + "-" * 70)
    print("Phase 4/6: Diagnostic Category Identification")
    print("-" * 70)
    
    phase4_result = run_interview_phase4(
        doctor=phase3_result['doctor'],
        model_name=phase3_result['model_name'],
        case_id=phase3_result['case_id']
    )
    
    print(f"\nPhase 4 完成:")
    print(f"  诊断类别数量: {len(phase4_result['diagnostic_categories'])}")
    if phase4_result['diagnostic_categories']:
        for i, category in enumerate(phase4_result['diagnostic_categories'], 1):
            print(f"    {i}. {category}")
    else:
        print(f"    （未能识别诊断类别）")
    print(f"  输出文件: {phase4_result['output_file']}")
    
    # ========== Phase 4 Evaluation ==========
    print("\n" + "-" * 70)
    print("Phase 4 Evaluation: Diagnostic Category Identification Evaluation")
    print("-" * 70)
    
    phase4_eval_result = evaluate_phase4(
        model_name=phase4_result['model_name'],
        case_id=phase4_result['case_id']
    )
    
    # ========== Phase 5: Diagnostic Hypotheses ==========
    print("\n" + "-" * 70)
    print("Phase 5/6: Diagnostic Hypotheses")
    print("-" * 70)
    
    phase5_result = run_interview_phase5(
        doctor=phase4_result['doctor'],
        model_name=phase4_result['model_name'],
        case_id=phase4_result['case_id']
    )
    
    print(f"\nPhase 5 完成:")
    print(f"  诊断假设数量: {len(phase5_result['diagnostic_hypotheses'])}")
    if phase5_result['diagnostic_hypotheses']:
        for i, hypothesis in enumerate(phase5_result['diagnostic_hypotheses'], 1):
            print(f"    {i}. {hypothesis}")
    else:
        print(f"    （未能生成诊断假设）")
    print(f"  输出文件: {phase5_result['output_file']}")
    
    # ========== Phase 5 Evaluation ==========
    print("\n" + "-" * 70)
    print("Phase 5 Evaluation: Diagnostic Hypotheses Evaluation")
    print("-" * 70)
    
    phase5_eval_result = evaluate_phase5(
        model_name=phase5_result['model_name'],
        case_id=phase5_result['case_id']
    )
    
    # ========== Phase 6: Differential Diagnosis ==========
    print("\n" + "-" * 70)
    print("Phase 6/6: Differential Diagnosis")
    print("-" * 70)
    
    phase6_result = run_interview_phase6(
        doctor=phase5_result['doctor'],
        model_name=phase5_result['model_name'],
        case_id=phase5_result['case_id']
    )
    
    print(f"\nPhase 6 完成:")
    print(f"  最终诊断数量: {len(phase6_result['differential_diagnosis'])}")
    if phase6_result['differential_diagnosis']:
        for i, diagnosis in enumerate(phase6_result['differential_diagnosis'], 1):
            print(f"    {i}. {diagnosis}")
    else:
        print(f"    （未能生成最终诊断）")
    print(f"  输出文件: {phase6_result['output_file']}")
    
    # ========== Phase 6 Evaluation ==========
    print("\n" + "-" * 70)
    print("Phase 6 Evaluation: Differential Diagnosis Evaluation")
    print("-" * 70)
    
    phase6_eval_result = evaluate_phase6(
        model_name=phase6_result['model_name'],
        case_id=phase6_result['case_id']
    )
    
    # ========== 汇总结果 ==========
    print("\n" + "=" * 70)
    print(" " * 25 + "流程完成汇总")
    print("=" * 70)
    
    final_result = {
        "case_id": phase1_result['case_id'],
        "model_name": phase1_result['model_name'],
        "phase1": {
            "status": phase1_result['status'],
            "conversation_turns": len([c for c in phase1_result['conversation'] if c['role'] == 'patient']),
            "output_file": phase1_result['output_file'],
            "evaluation": {
                "coverage_stats": phase1_eval_result['coverage_stats'],
                "conversation_stats": phase1_eval_result['conversation_stats'],
                "output_file": phase1_eval_result['output_file']
            }
        },
        "phase2": {
            "examinations": phase2_result['examinations'],
            "examination_results": phase2_result['examination_results'],
            "output_file": phase2_result['output_file'],
            "evaluation": {
                "metrics": phase2_eval_result['metrics'],
                "counts": phase2_eval_result['counts'],
                "output_file": phase2_eval_result['output_file']
            }
        },
        "phase3": {
            "syntactic_formulation": phase3_result['syntactic_formulation'],
            "output_file": phase3_result['output_file'],
            "evaluation": {
                "total_percentage": phase3_eval_result['total_percentage'],
                "total_weighted_score": phase3_eval_result['total_weighted_score'],
                "dimensions": phase3_eval_result['dimensions'],
                "output_file": phase3_eval_result['output_file']
            }
        },
        "phase4": {
            "diagnostic_categories": phase4_result['diagnostic_categories'],
            "output_file": phase4_result['output_file'],
            "evaluation": {
                "metrics": phase4_eval_result['metrics'],
                "predicted_categories": phase4_eval_result['predicted_categories'],
                "true_categories": phase4_eval_result['true_categories'],
                "output_file": phase4_eval_result['output_file']
            }
        },
        "phase5": {
            "diagnostic_hypotheses": phase5_result['diagnostic_hypotheses'],
            "output_file": phase5_result['output_file'],
            "evaluation": {
                "metrics": phase5_eval_result['metrics'],
                "predicted_hypotheses": phase5_eval_result['predicted_hypotheses'],
                "true_disorders": phase5_eval_result['true_disorders'],
                "output_file": phase5_eval_result['output_file']
            }
        },
        "phase6": {
            "differential_diagnosis": phase6_result['differential_diagnosis'],
            "output_file": phase6_result['output_file'],
            "evaluation": {
                "set_metrics": phase6_eval_result['set_metrics'],
                "primary_metrics": phase6_eval_result['primary_metrics'],
                "ranking_metrics": phase6_eval_result['ranking_metrics'],
                "predicted_diagnoses": phase6_eval_result['predicted_diagnoses'],
                "true_disorders": phase6_eval_result['true_disorders'],
                "output_file": phase6_eval_result['output_file']
            }
        }
    }
    
    print(f"\n病例ID: {final_result['case_id']}")
    print(f"模型: {final_result['model_name']}")
    
    print(f"\nPhase 1 (病史采集):")
    print(f"  状态: {final_result['phase1']['status']}")
    print(f"  对话轮数: {final_result['phase1']['conversation_turns']}")
    print(f"  主诉覆盖率: {final_result['phase1']['evaluation']['coverage_stats']['chief_complaint_coverage']:.2f}%")
    print(f"  精神状态覆盖率: {final_result['phase1']['evaluation']['coverage_stats']['mental_status_coverage']:.2f}%")
    
    print(f"\nPhase 2 (检查推荐):")
    print(f"  推荐项目数: {len(final_result['phase2']['examinations'])}")
    if final_result['phase2']['evaluation']['metrics']:
        metrics = final_result['phase2']['evaluation']['metrics']
        print(f"  评估指标:")
        print(f"    Precision: {metrics.get('precision', 0):.4f}")
        print(f"    Recall: {metrics.get('recall', 0):.4f}")
        print(f"    F1: {metrics.get('f1', 0):.4f}")
        print(f"    Jaccard: {metrics.get('jaccard', 0):.4f}")
    
    print(f"\nPhase 3 (临床病历):")
    print(f"  病历长度: {len(final_result['phase3']['syntactic_formulation'])} 字符")
    print(f"  总分: {final_result['phase3']['evaluation']['total_percentage']}%")
    if final_result['phase3']['evaluation']['dimensions']:
        for dim_name, dim_data in final_result['phase3']['evaluation']['dimensions'].items():
            percentage = dim_data.get('percentage', 0)
            weight = dim_data.get('dimension_weight', 0)
            print(f"    {dim_name}: {percentage}% (权重{weight*100:.0f}%)")
    
    print(f"\nPhase 4 (诊断类别):")
    print(f"  预测类别: {final_result['phase4']['diagnostic_categories']}")
    print(f"  真实类别: {final_result['phase4']['evaluation']['true_categories']}")
    metrics = final_result['phase4']['evaluation']['metrics']
    print(f"  评估指标:")
    print(f"    Precision: {metrics.get('precision', 0):.4f}")
    print(f"    Recall: {metrics.get('recall', 0):.4f}")
    print(f"    F1: {metrics.get('f1', 0):.4f}")
    print(f"    Jaccard: {metrics.get('jaccard', 0):.4f}")
    
    print(f"\nPhase 5 (诊断假设):")
    print(f"  预测诊断: {final_result['phase5']['diagnostic_hypotheses']}")
    print(f"  真实诊断: {final_result['phase5']['evaluation']['true_disorders']}")
    metrics = final_result['phase5']['evaluation']['metrics']
    print(f"  评估指标:")
    print(f"    Precision: {metrics.get('precision', 0):.4f}")
    print(f"    Recall: {metrics.get('recall', 0):.4f}")
    print(f"    F1: {metrics.get('f1', 0):.4f}")
    print(f"    Jaccard: {metrics.get('jaccard', 0):.4f}")
    
    print(f"\nPhase 6 (鉴别诊断):")
    print(f"  预测诊断: {final_result['phase6']['differential_diagnosis']}")
    print(f"  真实诊断: {final_result['phase6']['evaluation']['true_disorders']}")
    set_metrics = final_result['phase6']['evaluation']['set_metrics']
    primary_metrics = final_result['phase6']['evaluation']['primary_metrics']
    ranking_metrics = final_result['phase6']['evaluation']['ranking_metrics']
    print(f"  集合匹配指标:")
    print(f"    Precision: {set_metrics.get('precision', 0):.4f}")
    print(f"    Recall: {set_metrics.get('recall', 0):.4f}")
    print(f"    F1: {set_metrics.get('f1', 0):.4f}")
    print(f"    Jaccard: {set_metrics.get('jaccard', 0):.4f}")
    print(f"  主诊断排序指标:")
    print(f"    Primary Exact Match: {primary_metrics.get('primary_exact_match', 0)}")
    print(f"    Primary Hit@3: {primary_metrics.get('primary_hit_at_k', 0)}")
    print(f"    Primary Reciprocal Rank: {primary_metrics.get('primary_reciprocal_rank', 0):.4f}")
    print(f"  排序一致性指标:")
    print(f"    POA: {ranking_metrics.get('poa', 'N/A')}")
    print(f"    nDCG: {ranking_metrics.get('ndcg', 0):.4f}")
    
    from core.output_manager import get_output_dir
    output_dir = get_output_dir(phase1_result['model_name'], phase1_result['case_id'])
    summary_file = output_dir / "interview_summary.json"
    
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n完整结果已保存: {summary_file}")
    print(f"\n所有阶段输出目录: {output_dir}")
    print(f"  Interview 输出:")
    print(f"    - interview_phase1_output.json")
    print(f"    - interview_phase2_output.json")
    print(f"    - interview_phase3_output.json")
    print(f"    - interview_phase4_output.json")
    print(f"    - interview_phase5_output.json")
    print(f"    - interview_phase6_output.json")
    print(f"    - interview_summary.json")
    
    eval_output_dir = Path(__file__).parent / "data" / "output" / "evaluation" / phase1_result['model_name'] / phase1_result['case_id']
    print(f"  Evaluation 输出:")
    print(f"    - evaluation_phase1_output.json")
    print(f"    - evaluation_phase2_output.json")
    print(f"    - evaluation_phase3_output.json")
    print(f"    - evaluation_phase4_output.json")
    print(f"    - evaluation_phase5_output.json")
    print(f"    - evaluation_phase6_output.json")
    
    print("\n" + "=" * 70)
    
    return final_result


if __name__ == "__main__":
    """运行完整的精神科访谈流程"""
    try:
        result = run_full_interview()
        print("\n✓ 流程执行成功！")
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
