"""
精神科访谈完整流程 - 联合运行 Phase 1-5

使用方法:
    # 默认 test 模式：随机抽取一个 case 测试
    python run_interview.py

    # 指定 case 测试
    python run_interview.py --mode test --case-id 01343170

    # 全量评估：按顺序测试所有 cases
    python run_interview.py --mode eval

    # 批量并发：32路并发（默认）
    python run_interview.py --mode batch

    # 批量并发：自定义并发数
    python run_interview.py --mode batch --concurrency 8

流程:
    Phase 1: Clinical History Collection (医患对话收集病史)
    Phase 1 Eval: 评估病史采集效果
    Phase 2: Examination Recommendation (推荐辅助检查)
    Phase 2 Eval: 评估检查推荐效果
    Phase 3: Clinical Formulation (整理临床病历)
    Phase 3 Eval: 评估临床病历质量
    Phase 4: Definitive Diagnosis (最终诊断)
    Phase 4 Eval: 评估最终诊断效果
    Phase 5: Treatment Planning (治疗建议)
    Phase 5 Eval: 评估治疗建议效果
"""

import sys
import json
import argparse
import contextlib
import os
import io
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import threading

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from core.interview.interview_phase1 import run_interview_phase1, load_random_case
from core.interview.interview_phase2 import run_interview_phase2
from core.interview.interview_phase3 import run_interview_phase3
from core.interview.interview_phase4 import run_interview_phase4
from core.interview.interview_phase5 import run_interview_phase5
from core.evaluate.interview_phase1_eval import evaluate_phase1
from core.evaluate.interview_phase2_eval import evaluate_phase2
from core.evaluate.interview_phase3_eval import evaluate_phase3
from core.evaluate.interview_phase4_eval import evaluate_phase4
from core.evaluate.interview_phase5_eval import evaluate_phase5
from core.output_manager import get_output_dir

CASES_FILE = Path(__file__).parent / "data" / "cases.jsonl"

# ────────────────────── Evaluator Model Names ──────────────────────

_EVALUATOR_MODEL_NAMES = {}

def _get_evaluator_model_names() -> Dict[int, str]:
    """获取各评估器的模型名称（带缓存）"""
    if _EVALUATOR_MODEL_NAMES:
        return _EVALUATOR_MODEL_NAMES
    for i in range(1, 6):
        name = os.environ.get(f"EVALUATOR_{i}_MODEL", f"evaluator{i}")
        _EVALUATOR_MODEL_NAMES[i] = name
    return _EVALUATOR_MODEL_NAMES


def _extract_individual_scores(subj_result: Dict) -> Dict[str, Any]:
    """从主观评估结果中提取每个评估器的评分

    Returns:
        {"evaluator_models": {model_name: score, ...}, "average": float}
    """
    if subj_result is None:
        return None

    individual = subj_result.get("individual_results", [])
    if not individual:
        return {"evaluator_models": {}, "average": subj_result.get("score")}

    eval_models = _get_evaluator_model_names()
    model_scores = {}
    for item in individual:
        eid = item.get("evaluator_id")
        score = item.get("score")
        model_name = eval_models.get(eid, f"evaluator{eid}")
        model_scores[model_name] = score

    return {
        "evaluator_models": model_scores,
        "average": subj_result.get("score"),
        "parsed_count": subj_result.get("parsed_count", 0),
    }


# ────────────────────── Case Loading ──────────────────────

def _load_all_case_ids() -> List[str]:
    """从 cases.jsonl 读取所有 case ID"""
    ids = []
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                case = json.loads(line)
                if "id" in case:
                    ids.append(case["id"])
            except json.JSONDecodeError:
                continue
    return ids


# ────────────────────── Evaluation Helpers ──────────────────────

def _extract_scores(final_result: Dict[str, Any]) -> Dict[str, Any]:
    """从完整结果中提取关键评分指标（含每个主观评估的逐评估器分数）"""
    scores = {}

    # Phase 1: 覆盖率（3项）
    p1 = final_result.get("phase1", {}).get("evaluation", {})
    cov = p1.get("coverage_stats", {})
    scores["phase1_cc"] = cov.get("chief_complaint_coverage")
    scores["phase1_ms"] = cov.get("mental_status_coverage")
    scores["phase1_overall"] = cov.get("overall_coverage")
    empathy = p1.get("empathy_evaluation")
    if empathy:
        scores["phase1_empathy"] = empathy.get("score")
        scores["phase1_empathy_detail"] = _extract_individual_scores(empathy)
    profession = p1.get("profession_evaluation")
    if profession:
        scores["phase1_profession"] = profession.get("score")
        scores["phase1_profession_detail"] = _extract_individual_scores(profession)

    # Phase 2: 检查推荐（4项）
    p2 = final_result.get("phase2", {}).get("evaluation", {}).get("metrics", {})
    scores["phase2_precision"] = p2.get("precision")
    scores["phase2_recall"] = p2.get("recall")
    scores["phase2_f1"] = p2.get("f1")
    scores["phase2_jaccard"] = p2.get("jaccard")

    # Phase 3: 临床病历
    p3 = final_result.get("phase3", {}).get("evaluation", {})
    scores["phase3_total"] = p3.get("total_percentage")
    subj = p3.get("clinical_note_subjective")
    if subj:
        scores["phase3_subjective"] = subj.get("score")
        scores["phase3_subjective_detail"] = _extract_individual_scores(subj)

    # Phase 4: 最终诊断（类别集合匹配 + 排序指标 + 主观）
    p4 = final_result.get("phase4", {}).get("evaluation", {})
    dis_m = p4.get("disorder_metrics", {})
    scores["phase4_disorder_precision"] = dis_m.get("precision")
    scores["phase4_disorder_recall"] = dis_m.get("recall")
    scores["phase4_disorder_f1"] = dis_m.get("f1")
    scores["phase4_disorder_jaccard"] = dis_m.get("jaccard")
    cat_m = p4.get("category_metrics", {})
    scores["phase4_cat_precision"] = cat_m.get("precision")
    scores["phase4_cat_recall"] = cat_m.get("recall")
    scores["phase4_cat_f1"] = cat_m.get("f1")
    scores["phase4_cat_jaccard"] = cat_m.get("jaccard")
    primary_m = p4.get("primary_metrics", {})
    scores["phase4_exact_match"] = primary_m.get("primary_exact_match")
    scores["phase4_hit3"] = primary_m.get("primary_hit_at_k")
    scores["phase4_rr"] = primary_m.get("primary_reciprocal_rank")
    rank_m = p4.get("ranking_metrics", {})
    scores["phase4_ndcg"] = rank_m.get("ndcg")
    if rank_m.get("poa") is not None:
        scores["phase4_poa"] = rank_m.get("poa")
    diag_subj = p4.get("diagnostic_rigor_subjective")
    if diag_subj:
        scores["phase4_subjective"] = diag_subj.get("score")
        scores["phase4_subjective_detail"] = _extract_individual_scores(diag_subj)

    # Phase 5: 治疗建议
    p5 = final_result.get("phase5", {}).get("evaluation", {})
    t_subj = p5.get("treatment_subjective")
    if t_subj:
        scores["phase5_subjective"] = t_subj.get("score")
        scores["phase5_subjective_detail"] = _extract_individual_scores(t_subj)
    # 文本长度
    phase5_data = final_result.get("phase5", {})
    treatment_plan = phase5_data.get("treatment_plan", "")
    if treatment_plan:
        scores["phase5_length"] = len(treatment_plan)

    return scores


def _print_subjective(label: str, subj_result: Dict):
    """打印多评估器主观评分（均值 + 各评分）"""
    if subj_result is None or subj_result.get("score") is None:
        return
    score = subj_result["score"]
    scores = subj_result.get("scores", [])
    print(f"  [主观] {label}: {score}/5 (各评分: {scores})")


def _print_single_result(final_result: Dict[str, Any]):
    """打印单个 case 的评估结果"""
    scores = _extract_scores(final_result)
    print("\n" + "=" * 70)
    print(" " * 25 + "评估结果")
    print("=" * 70)
    print(f"病例ID: {final_result['case_id']}")
    print(f"模型: {final_result['model_name']}")
    print(f"\nPhase 1 (病史采集):")
    if scores.get("phase1_coverage") is not None:
        print(f"  整体覆盖率: {scores['phase1_coverage']:.2f}%")
    p1_eval = final_result.get("phase1", {}).get("evaluation", {})
    _print_subjective("沟通共情", p1_eval.get("empathy_evaluation"))
    _print_subjective("对话专业", p1_eval.get("profession_evaluation"))
    print(f"\nPhase 2 (检查推荐):")
    if scores.get("phase2_precision") is not None:
        print(f"  Precision: {scores['phase2_precision']:.4f}")
    if scores.get("phase2_recall") is not None:
        print(f"  Recall: {scores['phase2_recall']:.4f}")
    if scores.get("phase2_f1") is not None:
        print(f"  F1: {scores['phase2_f1']:.4f}")
    print(f"\nPhase 3 (临床病历):")
    if scores.get("phase3_total") is not None:
        print(f"  总分: {scores['phase3_total']}%")
    p3_eval = final_result.get("phase3", {}).get("evaluation", {})
    _print_subjective("病历质量", p3_eval.get("clinical_note_subjective"))
    print(f"\nPhase 4 (最终诊断):")
    print(f"  [病症诊断] Precision: {scores.get('phase4_disorder_precision', 0):.4f}")
    print(f"  [病症诊断] Recall: {scores.get('phase4_disorder_recall', 0):.4f}")
    print(f"  [病症诊断] F1: {scores.get('phase4_disorder_f1', 0):.4f}")
    print(f"  [类别诊断] Precision: {scores.get('phase4_category_precision', 0):.4f}")
    print(f"  [类别诊断] Recall: {scores.get('phase4_category_recall', 0):.4f}")
    print(f"  [类别诊断] F1: {scores.get('phase4_category_f1', 0):.4f}")
    if scores.get("phase4_primary_match") is not None:
        print(f"  Primary Exact Match: {scores['phase4_primary_match']}")
    p4_eval = final_result.get("phase4", {}).get("evaluation", {})
    _print_subjective("诊断严谨", p4_eval.get("diagnostic_rigor_subjective"))
    print(f"\nPhase 5 (治疗建议):")
    p5_eval = final_result.get("phase5", {}).get("evaluation", {})
    _print_subjective("治疗合理", p5_eval.get("treatment_subjective"))
    print("=" * 70)


def _print_avg_results(results: List[Dict[str, Any]], model_name: str):
    """打印所有 case 的平均评估结果"""
    if not results:
        print("无有效结果")
        return

    all_scores = []
    for r in results:
        s = _extract_scores(r)
        all_scores.append({k: v for k, v in s.items() if v is not None})

    keys = set()
    for s in all_scores:
        keys.update(s.keys())

    print("\n" + "=" * 70)
    print(" " * 20 + "平均评估结果 (All Cases)")
    print("=" * 70)
    print(f"模型: {model_name}")
    print(f"有效 Case 数: {len(all_scores)}")

    for key in sorted(keys):
        if key.endswith("_detail"):
            continue
        values = [s[key] for s in all_scores if key in s]
        if not values:
            continue
        avg = sum(values) / len(values)
        label = key.replace("phase", "P").replace("_", " ")
        if any(k in key for k in ("coverage", "total", "precision", "recall", "f1", "percentage")):
            print(f"  {label}: {avg:.2f}")
        elif "match" in key:
            print(f"  {label}: {avg:.4f}")
        else:
            print(f"  {label}: {avg:.2f}")

    print("=" * 70)


# ────────────────────── Metrics decimal precision ──────────────────────

# Metrics whose max value is 1.0 → 4 decimal places
_METRICS_4DEC = {
    "phase2_precision", "phase2_recall", "phase2_f1",
    "phase4_disorder_precision", "phase4_disorder_recall",
    "phase4_disorder_f1", "phase4_disorder_jaccard",
    "phase4_category_precision", "phase4_category_recall",
    "phase4_category_f1", "phase4_category_jaccard",
    "phase4_primary_match", "phase4_primary_reciprocal_rank",
    "phase4_poa", "phase4_ndcg",
}


def _avg_precision(key: str) -> int:
    """根据指标名决定保留几位小数"""
    if key in _METRICS_4DEC:
        return 4
    return 2


# Quiet context manager: suppress stdout when quiet=True
@contextlib.contextmanager
def _quiet_context(quiet: bool):
    if quiet:
        with contextlib.redirect_stdout(io.StringIO()):
            yield
    else:
        yield


# ────────────────────── Core Pipeline ──────────────────────

def run_full_interview(case: Dict[str, Any] = None, quiet: bool = False, use_backup: bool = False) -> Dict[str, Any]:
    """运行完整的五阶段访谈流程

    Args:
        case: 可选，指定病例数据。如果不提供，则随机加载一个病例
        quiet: 静默模式，仅保留关键输出（用于 eval/batch）
        use_backup: 患者和仪器使用备用API（PATIENT_BACKUP_*/INSTRUMENT_BACKUP_* 配置）

    Returns:
        完整流程的结果字典
    """
    if not quiet:
        print("\n" + "=" * 70)
        print(" " * 20 + "精神科访谈完整流程")
        print("=" * 70)

    # 使用本地变量保存所有结果，再统一处理
    _result = {"phase1": None, "phase1_eval": None, "phase2": None,
               "phase2_eval": None, "phase3": None, "phase3_eval": None,
               "phase4": None, "phase4_eval": None, "phase5": None, "phase5_eval": None}

    def _run_pipeline():
        _result["phase1"] = run_interview_phase1(case=case, patient_backup=use_backup)
        _result["phase1_eval"] = evaluate_phase1(
            model_name=_result["phase1"]["model_name"],
            case_id=_result["phase1"]["case_id"]
        )
        _result["phase2"] = run_interview_phase2(
            doctor=_result["phase1"]["doctor"],
            model_name=_result["phase1"]["model_name"],
            case_id=_result["phase1"]["case_id"],
            case_data=_result["phase1"]["case_data"],
            instrument_backup=use_backup
        )
        _result["phase2_eval"] = evaluate_phase2(
            model_name=_result["phase2"]["model_name"],
            case_id=_result["phase2"]["case_id"],
            case_data=_result["phase1"]["case_data"]
        )
        _result["phase3"] = run_interview_phase3(
            doctor=_result["phase2"]["doctor"],
            model_name=_result["phase2"]["model_name"],
            case_id=_result["phase2"]["case_id"],
            examination_results=_result["phase2"]["examination_results"]
        )
        _result["phase3_eval"] = evaluate_phase3(
            model_name=_result["phase3"]["model_name"],
            case_id=_result["phase3"]["case_id"]
        )
        _result["phase4"] = run_interview_phase4(
            doctor=_result["phase3"]["doctor"],
            model_name=_result["phase3"]["model_name"],
            case_id=_result["phase3"]["case_id"]
        )
        _result["phase4_eval"] = evaluate_phase4(
            model_name=_result["phase4"]["model_name"],
            case_id=_result["phase4"]["case_id"]
        )
        _result["phase5"] = run_interview_phase5(
            doctor=_result["phase4"]["doctor"],
            model_name=_result["phase4"]["model_name"],
            case_id=_result["phase4"]["case_id"]
        )
        _result["phase5_eval"] = evaluate_phase5(
            model_name=_result["phase5"]["model_name"],
            case_id=_result["phase5"]["case_id"]
        )

    if quiet:
        with _quiet_context(quiet):
            _run_pipeline()
    else:
        # ========== Phase 1: Clinical History Collection ==========
        print("\n" + "-" * 70)
        print("Phase 1/5: Clinical History Collection")
        print("-" * 70)
        _result["phase1"] = run_interview_phase1(case=case, patient_backup=use_backup)
        print(f"\nPhase 1 完成:")
        print(f"  对话轮数: {len([c for c in _result['phase1']['conversation'] if c['role'] == 'patient'])}")
        print(f"  输出文件: {_result['phase1']['output_file']}")

        # ========== Phase 1 Evaluation ==========
        print("\n" + "-" * 70)
        print("Phase 1 Evaluation: Clinical History Collection Evaluation")
        print("-" * 70)
        _result["phase1_eval"] = evaluate_phase1(
            model_name=_result["phase1"]["model_name"],
            case_id=_result["phase1"]["case_id"]
        )

        # ========== Phase 2: Examination Recommendation ==========
        print("\n" + "-" * 70)
        print("Phase 2/5: Examination Recommendation")
        print("-" * 70)
        _result["phase2"] = run_interview_phase2(
            doctor=_result["phase1"]["doctor"],
            model_name=_result["phase1"]["model_name"],
            case_id=_result["phase1"]["case_id"],
            case_data=_result["phase1"]["case_data"],
            instrument_backup=use_backup
        )
        print(f"\nPhase 2 完成:")
        print(f"  推荐检查项目: {len(_result['phase2']['examinations'])} 项")
        if _result["phase2"]["examinations"]:
            for i, exam in enumerate(_result["phase2"]["examinations"], 1):
                print(f"    {i}. {exam}")
        else:
            print(f"    （无需辅助检查）")
        print(f"  输出文件: {_result['phase2']['output_file']}")

        # ========== Phase 2 Evaluation ==========
        print("\n" + "-" * 70)
        print("Phase 2 Evaluation: Examination Recommendation Evaluation")
        print("-" * 70)
        _result["phase2_eval"] = evaluate_phase2(
            model_name=_result["phase2"]["model_name"],
            case_id=_result["phase2"]["case_id"],
            case_data=_result["phase1"]["case_data"]
        )

        # ========== Phase 3: Clinical Formulation ==========
        print("\n" + "-" * 70)
        print("Phase 3/5: Clinical Formulation")
        print("-" * 70)
        _result["phase3"] = run_interview_phase3(
            doctor=_result["phase2"]["doctor"],
            model_name=_result["phase2"]["model_name"],
            case_id=_result["phase2"]["case_id"],
            examination_results=_result["phase2"]["examination_results"]
        )
        print(f"\nPhase 3 完成:")
        print(f"  临床病历长度: {len(_result['phase3']['syntactic_formulation'])} 字符")
        print(f"  输出文件: {_result['phase3']['output_file']}")

        # ========== Phase 3 Evaluation ==========
        print("\n" + "-" * 70)
        print("Phase 3 Evaluation: Clinical Formulation Evaluation")
        print("-" * 70)
        _result["phase3_eval"] = evaluate_phase3(
            model_name=_result["phase3"]["model_name"],
            case_id=_result["phase3"]["case_id"]
        )

        # ========== Phase 4: Definitive Diagnosis ==========
        print("\n" + "-" * 70)
        print("Phase 4/5: Definitive Diagnosis")
        print("-" * 70)
        _result["phase4"] = run_interview_phase4(
            doctor=_result["phase3"]["doctor"],
            model_name=_result["phase3"]["model_name"],
            case_id=_result["phase3"]["case_id"]
        )
        print(f"\nPhase 4 完成:")
        print(f"  最终诊断数量: {len(_result['phase4']['definitive_diagnosis'])}")
        if _result["phase4"]["definitive_diagnosis"]:
            for i, diagnosis in enumerate(_result["phase4"]["definitive_diagnosis"], 1):
                print(f"    {i}. {diagnosis}")
        else:
            print(f"    （未能生成最终诊断）")
        print(f"  输出文件: {_result['phase4']['output_file']}")

        # ========== Phase 4 Evaluation ==========
        print("\n" + "-" * 70)
        print("Phase 4 Evaluation: Definitive Diagnosis Evaluation")
        print("-" * 70)
        _result["phase4_eval"] = evaluate_phase4(
            model_name=_result["phase4"]["model_name"],
            case_id=_result["phase4"]["case_id"]
        )

        # ========== Phase 5: Treatment Planning ==========
        print("\n" + "-" * 70)
        print("Phase 5/5: Treatment Planning")
        print("-" * 70)
        _result["phase5"] = run_interview_phase5(
            doctor=_result["phase4"]["doctor"],
            model_name=_result["phase4"]["model_name"],
            case_id=_result["phase4"]["case_id"]
        )
        print(f"\nPhase 5 完成:")
        print(f"  治疗建议长度: {len(_result['phase5']['treatment_plan'])} 字符")
        print(f"  输出文件: {_result['phase5']['output_file']}")

        # ========== Phase 5 Evaluation ==========
        print("\n" + "-" * 70)
        print("Phase 5 Evaluation: Treatment Planning Evaluation")
        print("-" * 70)
        _result["phase5_eval"] = evaluate_phase5(
            model_name=_result["phase5"]["model_name"],
            case_id=_result["phase5"]["case_id"]
        )

    phase1_result = _result["phase1"]
    phase1_eval_result = _result["phase1_eval"]
    phase2_result = _result["phase2"]
    phase2_eval_result = _result["phase2_eval"]
    phase3_result = _result["phase3"]
    phase3_eval_result = _result["phase3_eval"]
    phase4_result = _result["phase4"]
    phase4_eval_result = _result["phase4_eval"]
    phase5_result = _result["phase5"]
    phase5_eval_result = _result["phase5_eval"]

    # ========== 汇总结果 ==========
    if not quiet:
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
                "empathy_evaluation": phase1_eval_result.get('empathy_evaluation'),
                "profession_evaluation": phase1_eval_result.get('profession_evaluation'),
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
                "clinical_note_subjective": phase3_eval_result.get('clinical_note_subjective'),
                "output_file": phase3_eval_result['output_file']
            }
        },
        "phase4": {
            "definitive_diagnosis": phase4_result['definitive_diagnosis'],
            "diagnosis_reasoning": phase4_result['diagnosis_reasoning'],
            "output_file": phase4_result['output_file'],
            "evaluation": {
                "disorder_metrics": phase4_eval_result['disorder_metrics'],
                "category_metrics": phase4_eval_result['category_metrics'],
                "primary_metrics": phase4_eval_result['primary_metrics'],
                "ranking_metrics": phase4_eval_result['ranking_metrics'],
                "diagnostic_rigor_subjective": phase4_eval_result.get('diagnostic_rigor_subjective'),
                "predicted_diagnoses": phase4_eval_result['predicted_diagnoses'],
                "true_disorders": phase4_eval_result['true_disorders'],
                "predicted_categories": phase4_eval_result.get('predicted_categories'),
                "true_categories": phase4_eval_result.get('true_categories'),
                "output_file": phase4_eval_result['output_file']
            }
        },
        "phase5": {
            "treatment_plan": phase5_result['treatment_plan'],
            "output_file": phase5_result['output_file'],
            "evaluation": {
                "treatment_subjective": phase5_eval_result.get('treatment_subjective'),
                "output_file": phase5_eval_result['output_file']
            }
        }
    }

    if not quiet:
        print(f"\n病例ID: {final_result['case_id']}")
        print(f"模型: {final_result['model_name']}")

        print(f"\nPhase 1 (病史采集):")
        print(f"  状态: {final_result['phase1']['status']}")
        print(f"  对话轮数: {final_result['phase1']['conversation_turns']}")
        print(f"  主诉覆盖率: {final_result['phase1']['evaluation']['coverage_stats']['chief_complaint_coverage']:.2f}%")
        print(f"  精神状态覆盖率: {final_result['phase1']['evaluation']['coverage_stats']['mental_status_coverage']:.2f}%")
        empathy = final_result['phase1'].get('evaluation', {}).get('empathy_evaluation')
        if empathy and empathy.get("score") is not None:
            e_scores = empathy.get("scores", [])
            print(f"  [主观] 沟通共情: {empathy['score']}/5 (各评分: {e_scores})")
        profession = final_result['phase1'].get('evaluation', {}).get('profession_evaluation')
        if profession and profession.get("score") is not None:
            p_scores = profession.get("scores", [])
            print(f"  [主观] 对话专业: {profession['score']}/5 (各评分: {p_scores})")

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
        clinical_note_subj = final_result['phase3'].get('evaluation', {}).get('clinical_note_subjective')
        if clinical_note_subj and clinical_note_subj.get("score") is not None:
            cn_scores = clinical_note_subj.get("scores", [])
            print(f"  [主观] 病历质量: {clinical_note_subj['score']}/5 (各评分: {cn_scores})")

        print(f"\nPhase 4 (最终诊断):")
        print(f"  预测诊断: {final_result['phase4']['definitive_diagnosis']}")
        print(f"  真实诊断: {final_result['phase4']['evaluation']['true_disorders']}")
        if final_result['phase4']['evaluation'].get('predicted_categories'):
            print(f"  预测类别: {final_result['phase4']['evaluation']['predicted_categories']}")
        if final_result['phase4']['evaluation'].get('true_categories'):
            print(f"  真实类别: {final_result['phase4']['evaluation']['true_categories']}")
        dis_metrics = final_result['phase4']['evaluation']['disorder_metrics']
        cat_metrics = final_result['phase4']['evaluation']['category_metrics']
        primary_metrics = final_result['phase4']['evaluation']['primary_metrics']
        ranking_metrics = final_result['phase4']['evaluation']['ranking_metrics']
        print(f"  [病症诊断] 集合匹配:")
        print(f"    Precision: {dis_metrics.get('precision', 0):.4f}")
        print(f"    Recall: {dis_metrics.get('recall', 0):.4f}")
        print(f"    F1: {dis_metrics.get('f1', 0):.4f}")
        print(f"    Jaccard: {dis_metrics.get('jaccard', 0):.4f}")
        print(f"  [类别诊断] 集合匹配:")
        print(f"    Precision: {cat_metrics.get('precision', 0):.4f}")
        print(f"    Recall: {cat_metrics.get('recall', 0):.4f}")
        print(f"    F1: {cat_metrics.get('f1', 0):.4f}")
        print(f"    Jaccard: {cat_metrics.get('jaccard', 0):.4f}")
        print(f"  主诊断排序指标:")
        print(f"    Primary Exact Match: {primary_metrics.get('primary_exact_match', 0)}")
        print(f"    Primary Hit@3: {primary_metrics.get('primary_hit_at_k', 0)}")
        print(f"    Primary Reciprocal Rank: {primary_metrics.get('primary_reciprocal_rank', 0):.4f}")
        print(f"  排序一致性指标:")
        print(f"    POA: {ranking_metrics.get('poa', 'N/A')}")
        print(f"    nDCG: {ranking_metrics.get('ndcg', 0):.4f}")
        diagnostic_rigor_subj = final_result['phase4'].get('evaluation', {}).get('diagnostic_rigor_subjective')
        if diagnostic_rigor_subj and diagnostic_rigor_subj.get("score") is not None:
            dr_scores = diagnostic_rigor_subj.get("scores", [])
            print(f"  [主观] 诊断严谨: {diagnostic_rigor_subj['score']}/5 (各评分: {dr_scores})")

        print(f"\nPhase 5 (治疗建议):")
        print(f"  治疗建议长度: {len(final_result['phase5']['treatment_plan'])} 字符")
        treatment_subj = final_result['phase5'].get('evaluation', {}).get('treatment_subjective')
        if treatment_subj and treatment_subj.get("score") is not None:
            t_scores = treatment_subj.get("scores", [])
            print(f"  [主观] 治疗合理: {treatment_subj['score']}/5 (各评分: {t_scores})")
        else:
            print(f"  [主观] 治疗合理: （未获取评估结果）")

        output_dir = get_output_dir(phase1_result['model_name'], phase1_result['case_id'])
        summary_file = output_dir / "interview_summary.json"

        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)

        print(f"\n完整结果已保存: {summary_file}")
        print(f"\n所有阶段输出目录: {output_dir}")

        print("\n" + "=" * 70)

    else:
        # quiet 模式：仍然保存结果
        output_dir = get_output_dir(phase1_result['model_name'], phase1_result['case_id'])
        summary_file = output_dir / "interview_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)

    # ── 提取精简指标并追加到 results/<model>.jsonl（每 case 即时写入） ──
    model_name = phase1_result['model_name']
    case_id = phase1_result['case_id']
    scores = _extract_scores(final_result)
    _append_per_case_result(model_name, case_id, scores)

    return final_result


# ────────────────────── Mode Runners ──────────────────────

def run_test(case_id: str = None):
    """Test 模式：随机或指定一个 case，测试并输出结果"""
    if case_id:
        case = load_random_case(case_id=case_id)
        print(f"\n[测试模式] 指定病例: {case_id}")
    else:
        case = load_random_case()
        print(f"\n[测试模式] 随机抽取病例: {case['id']}")

    result = run_full_interview(case=case)
    _print_single_result(result)


def _get_results_json_path(model_name: str) -> Path:
    return Path(__file__).parent / "data" / "output" / "results" / f"{model_name}.json"


_results_write_lock = threading.Lock()


def _append_per_case_result(model_name: str, case_id: str, scores: Dict[str, Any]):
    """将单个 case 的指标即时追加到 results/<model>.json

    采用 read-modify-write 模式：读取已有 per_case 列表，追加新 case 并写回。
    线程安全，支持并发场景。
    """
    path = _get_results_json_path(model_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"case_id": case_id, "scores": {k: v for k, v in scores.items() if not k.endswith("_detail")}}

    with _results_write_lock:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {"model": model_name, "num_cases": 0, "averages": {}, "evaluator_averages": {}, "per_case": []}
        else:
            data = {"model": model_name, "num_cases": 0, "averages": {}, "evaluator_averages": {}, "per_case": []}

        # 如果该 case 已存在，替换；否则追加
        existing = {r["case_id"]: i for i, r in enumerate(data.get("per_case", []))}
        if case_id in existing:
            data["per_case"][existing[case_id]] = record
        else:
            data["per_case"].append(record)

        data["num_cases"] = len(data["per_case"])

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def _find_completed_cases(model_name: str, all_ids: List[str]) -> set:
    """从 results/<model>.json 的 per_case 中读取已完成的 case

    判定规则：case_id 存在 且 scores 中所有值均不为 None → 视为已完成。
    """
    results_path = Path(__file__).parent / "data" / "output" / "results" / f"{model_name}.json"
    if not results_path.exists():
        return set()

    completed = set()
    try:
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for rec in data.get("per_case", []):
            cid = rec.get("case_id")
            if cid is None:
                continue
            scores = rec.get("scores", {})
            if not scores:
                continue
            # 检查 scores 中所有值：有任何一个为 None → 不算完成
            if all(v is not None for v in scores.values()):
                completed.add(cid)
    except (json.JSONDecodeError, OSError, KeyError):
        pass

    if completed:
        print(f"[断点续传] 从 results/{model_name}.json 发现 {len(completed)} 个已完成 case")
    return completed


def _get_doctor_model() -> Optional[str]:
    """从环境变量 DOCTOR_MODEL 获取当前医生模型名称"""
    return os.environ.get("DOCTOR_MODEL")


def run_eval():
    """Eval 模式：按顺序测试所有 cases，tqdm 进度条，支持断点续传"""
    all_ids = _load_all_case_ids()

    # 从 .env 中获取医生模型名
    model_name = _get_doctor_model()

    # 从 results/<model>.json 读取已完成 case（scores 中有 None 不算完成）
    completed = _find_completed_cases(model_name, all_ids) if model_name else set()

    # 过滤出需要执行的 case
    pending_ids = [cid for cid in all_ids if cid not in completed]

    if not pending_ids:
        print("[评估完成] 所有 case 均已完成，无需运行")
        return

    new_count = 0
    for cid in tqdm(pending_ids, desc="Evaluating", unit="case"):
        try:
            case = load_random_case(case_id=cid)
            run_full_interview(case=case, quiet=True)
            new_count += 1
        except Exception as e:
            print(f"\n[失败] Case {cid}: {e}")

    print(f"\n[评估完成] 新增 {new_count} 个 case，跳过 {len(completed)} 个已完成的 case")


def _run_single_case(cid: str, use_backup: bool = False) -> tuple:
    """并发执行单个 case（供 batch 模式调用）

    返回 (case_id, result_or_error)
    """
    try:
        case = load_random_case(case_id=cid)
        result = run_full_interview(case=case, quiet=True, use_backup=use_backup)
        return (cid, result, None)
    except Exception as e:
        return (cid, None, str(e))


def run_batch(concurrency: int = 32):
    """Batch 模式：多路并发，tqdm 进度条，支持断点续传

    患者和仪器负载拆分：
    - 按顺序交替分配：第 0、2、4...个 case 走主 API，第 1、3、5...个走备用 API
    - 每个批次内主备各占一半，始终保持负载均衡
    """
    all_ids = _load_all_case_ids()
    total_all = len(all_ids)

    # 从 .env 中获取医生模型名 & 从 results/<model>.json 读取已完成 case
    model_name = _get_doctor_model()
    completed = _find_completed_cases(model_name, all_ids) if model_name else set()

    # 过滤出需要执行的 case
    pending_ids = [cid for cid in all_ids if cid not in completed]
    total = len(pending_ids)

    if total == 0:
        print("[批量完成] 所有 case 均已完成，无需运行")
        return

    pbar = tqdm(total=total, desc="Batch", unit="case")

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        running = set()  # 当前在跑的 futures
        idx = 0  # 下一个要提交的 case 索引
        submit_counter = 0  # 全局提交计数器：偶数=主API，奇数=备份API

        # 当前在跑的主/备任务计数（用于均衡分配）
        primary_in_flight = 0
        backup_in_flight = 0

        def _submit(cid: str):
            nonlocal primary_in_flight, backup_in_flight, submit_counter
            use_b = (submit_counter % 2 == 1)
            submit_counter += 1
            fut = executor.submit(_run_single_case, cid, use_b)
            fut._mh_cid = cid
            fut._mh_use_b = use_b
            if use_b:
                backup_in_flight += 1
            else:
                primary_in_flight += 1
            running.add(fut)
            # 立即注册完成回调
            fut.add_done_callback(_on_done)

        def _on_done(fut):
            """future 完成后的回调"""
            nonlocal idx, primary_in_flight, backup_in_flight
            cid = getattr(fut, "_mh_cid", "unknown")
            use_b = getattr(fut, "_mh_use_b", False)

            # 释放 in_flight 计数
            if use_b:
                backup_in_flight -= 1
            else:
                primary_in_flight -= 1

            # 获取结果（_run_single_case 已经在 run_full_interview 内部写入了 results/<model>.json）
            try:
                cid_r, result, error = fut.result()
            except Exception as e:
                cid_r, result, error = cid, None, str(e)

            if error:
                print(f"\n[失败] Case {cid}: {error}")

            pbar.update(1)

            # 还有未提交的 case，立即补上
            if idx < total:
                _submit(pending_ids[idx])
                idx += 1

        # 提交初始批次
        for _ in range(min(concurrency, total)):
            _submit(pending_ids[idx])
            idx += 1

        # 等待所有 future 完成（包括回调中新提交的）
        while running:
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            # 从 running 中移除已完成的
            running.difference_update(done)

    pbar.close()

    # 从 results/<model>.json 读取最终聚合结果
    if model_name:
        results_path = _get_results_json_path(model_name)
        if results_path.exists():
            try:
                with open(results_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                per_case = data.get("per_case", [])
                if per_case:
                    # 打印平均分
                    _print_avg_from_per_case(per_case, model_name)
                    # 计算并更新聚合指标
                    _update_aggregates(model_name)
                    print(f"\n完整结果已保存: {results_path}")
            except (json.JSONDecodeError, OSError):
                pass


def _print_avg_from_per_case(per_case: List[Dict], model_name: str):
    """从 per_case 列表打印平均指标"""
    scores_list = [r.get("scores", {}) for r in per_case]
    n = len(scores_list)
    if n == 0:
        return

    all_keys = set()
    for s in scores_list:
        all_keys.update(s.keys())

    print(f"\n{'=' * 70}")
    print(f"  平均评估结果 (All Cases)")
    print(f"{'=' * 70}")
    print(f"  模型: {model_name}")
    print(f"  有效 Case 数: {n}")
    for key in sorted(all_keys):
        if key.endswith("_detail"):
            continue
        values = [s[key] for s in scores_list if s.get(key) is not None]
        if not values:
            continue
        avg = sum(values) / len(values)
        label = key.replace("phase", "P").replace("_", " ")
        dec = 4 if key in _METRICS_4DEC else 2
        print(f"  {label}: {avg:.{dec}f}")
    print(f"{'=' * 70}")


def _update_aggregates(model_name: str):
    """读取 results/<model>.json 并重新计算 averages 写回"""
    path = _get_results_json_path(model_name)
    if not path.exists():
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    per_case = data.get("per_case", [])
    scores_list = [r.get("scores", {}) for r in per_case]
    n = len(scores_list)
    if n == 0:
        return

    # 计算 averages
    all_keys = set()
    for s in scores_list:
        all_keys.update(s.keys())
    averages = {}
    for key in sorted(all_keys):
        if key.endswith("_detail"):
            continue
        values = [s[key] for s in scores_list if s.get(key) is not None]
        if not values:
            continue
        averages[key] = round(sum(values) / len(values), _avg_precision(key))

    # 计算主观评估的逐评估器平均分（需要 *_detail 数据）
    # 由于 per_case 只存精简分数（去掉了 *_detail），需要从原始 interview_summary.json 读取
    evaluator_avg = {}

    data["averages"] = averages
    data["evaluator_averages"] = evaluator_avg
    data["num_cases"] = n

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ────────────────────── CLI ──────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="精神科访谈完整流程运行器")
    parser.add_argument(
        "--mode",
        choices=["test", "eval", "batch"],
        default="test",
        help="运行模式: test(随机单例) | eval(全量顺序) | batch(全量并发). 默认: test"
    )
    parser.add_argument(
        "--case-id",
        type=str,
        default=None,
        help="指定测试的病例ID (仅在 test 模式下有效)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=32,
        help="批量并发数 (仅在 batch 模式下有效). 默认: 32"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    try:
        if args.mode == "test":
            run_test(case_id=args.case_id)
        elif args.mode == "eval":
            run_eval()
        elif args.mode == "batch":
            run_batch(concurrency=args.concurrency)

        print("\n流程执行成功！")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
