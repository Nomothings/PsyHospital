"""
评估结果收集器 - 为每个 case 收集客观指标和主观评分，
在 eval 结束时生成模型级别汇总报告。

输出: data/output/results/{model_name}.json
"""

import os
import math
from pathlib import Path
from typing import Dict, Any, List, Optional

RESULTS_DIR = Path(__file__).parent.parent.parent / "data" / "output" / "results"


# ────────────────────── Evaluator Model Names ──────────────────────

def _get_evaluator_model_names() -> Dict[int, str]:
    """从环境变量读取各评估器的模型名称"""
    names = {}
    for i in range(1, 6):
        key = f"EVALUATOR_{i}_MODEL"
        names[i] = os.environ.get(key, f"evaluator_{i}")
    return names


_EVALUATOR_NAMES = _get_evaluator_model_names()


# ────────────────────── Subjective Score Extraction ──────────────────────

def extract_subjective_scores(subj_result: Dict) -> Optional[Dict]:
    """从主观评估结果中提取标准化分数结构

    Returns:
        {
            "avg": 均值 (保留2位小数),
            "evaluators": {"model_name": score_or_null, ...}
        }
    """
    if not subj_result or subj_result.get("score") is None:
        return None

    avg = subj_result["score"]
    scores = subj_result.get("scores", [])  # 按 evaluator_id 1-5 排序
    individual = subj_result.get("individual_results", [])

    evaluator_scores = {}
    for i in range(1, 6):
        model_name = _EVALUATOR_NAMES.get(i, f"evaluator_{i}")
        # 从 individual 中找对应的分数
        score = None
        for ind in individual:
            if ind.get("evaluator_id") == i:
                score = ind.get("score")
                break
        if score is not None and i <= len(scores):
            score = scores[i - 1]  # scores 也是按 id 排序
        evaluator_scores[model_name] = score

    return {"avg": round(avg, 2), "evaluators": evaluator_scores}


# ────────────────────── Per-Case Result ──────────────────────

def build_case_result(
    case_id: str,
    model_name: str,
    status: str,
    phase1_eval: Dict,
    phase2_eval: Dict,
    phase3_eval: Dict,
    phase4_eval: Dict,
    phase5_eval: Dict,
) -> Dict[str, Any]:
    """为单个 case 构建标准化结果字典"""

    result = {
        "case_id": case_id,
        "model_name": model_name,
        "status": status,
    }

    # ── Phase 1 ──
    cov = phase1_eval.get("coverage_stats", {})
    result["phase1"] = {
        "coverage": {
            "chief_complaint": cov.get("chief_complaint_coverage"),
            "mental_status": cov.get("mental_status_coverage"),
            "overall": cov.get("overall_coverage"),
        },
        "empathy": extract_subjective_scores(phase1_eval.get("empathy_evaluation")),
        "profession": extract_subjective_scores(phase1_eval.get("profession_evaluation")),
    }

    # ── Phase 2 ──
    m2 = phase2_eval.get("metrics", {})
    result["phase2"] = {
        "precision": m2.get("precision"),
        "recall": m2.get("recall"),
        "f1": m2.get("f1"),
        "jaccard": m2.get("jaccard"),
    }

    # ── Phase 3 ──
    dims = phase3_eval.get("dimensions", {})
    dim_scores = {}
    for dim_name, dim_data in dims.items():
        dim_scores[dim_name] = {
            "percentage": dim_data.get("percentage"),
            "weight": dim_data.get("dimension_weight"),
        }
    result["phase3"] = {
        "total_percentage": phase3_eval.get("total_percentage"),
        "total_weighted_score": phase3_eval.get("total_weighted_score"),
        "dimensions": dim_scores,
        "clinical_note": extract_subjective_scores(phase3_eval.get("clinical_note_subjective")),
    }

    # ── Phase 4 ──
    dis_m = phase4_eval.get("disorder_metrics", {})
    cat_m = phase4_eval.get("category_metrics", {})
    pri_m = phase4_eval.get("primary_metrics", {})
    rank_m = phase4_eval.get("ranking_metrics", {})
    result["phase4"] = {
        "disorder": {
            "precision": dis_m.get("precision"),
            "recall": dis_m.get("recall"),
            "f1": dis_m.get("f1"),
            "jaccard": dis_m.get("jaccard"),
        },
        "category": {
            "precision": cat_m.get("precision"),
            "recall": cat_m.get("recall"),
            "f1": cat_m.get("f1"),
            "jaccard": cat_m.get("jaccard"),
        },
        "primary": {
            "exact_match": pri_m.get("primary_exact_match"),
            "hit_at_3": pri_m.get("primary_hit_at_k"),
            "reciprocal_rank": pri_m.get("primary_reciprocal_rank"),
        },
        "ranking": {
            "poa": rank_m.get("poa"),
            "ndcg": rank_m.get("ndcg"),
        },
        "diagnostic_rigor": extract_subjective_scores(phase4_eval.get("diagnostic_rigor_subjective")),
    }

    # ── Phase 5 ──
    result["phase5"] = {
        "treatment": extract_subjective_scores(phase5_eval.get("treatment_subjective")),
    }

    return result


# ────────────────────── Averaging ──────────────────────

def _avg(values: List, decimals: int) -> Optional[float]:
    """计算均值，过滤 None"""
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), decimals)


def _avg_level(values: List) -> Optional[float]:
    """Level 评分均值，保留 2 位小数"""
    return _avg(values, 2)


def _avg_metric(values: List) -> Optional[float]:
    """指标均值 (Precision/Recall/F1 等 0-1 范围)，保留 4 位小数"""
    return _avg(values, 4)


def compute_summary(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """从多个 case 结果中计算汇总统计

    返回包含所有指标平均值和方差的结构化字典。
    """
    if not cases:
        return {}

    n = len(cases)
    summary = {"num_cases": n}

    # ── Phase 1 ──
    p1_cov_overall = [c["phase1"]["coverage"]["overall"] for c in cases]
    p1_cov_cc = [c["phase1"]["coverage"]["chief_complaint"] for c in cases]
    p1_cov_ms = [c["phase1"]["coverage"]["mental_status"] for c in cases]
    summary["phase1"] = {
        "coverage": {
            "overall": _avg_metric(p1_cov_overall),
            "chief_complaint": _avg_metric(p1_cov_cc),
            "mental_status": _avg_metric(p1_cov_ms),
        },
        "empathy": _compute_subjective_summary(
            [c["phase1"]["empathy"] for c in cases if c["phase1"].get("empathy")]
        ),
        "profession": _compute_subjective_summary(
            [c["phase1"]["profession"] for c in cases if c["phase1"].get("profession")]
        ),
    }

    # ── Phase 2 ──
    p2_prec = [c["phase2"]["precision"] for c in cases if c["phase2"]["precision"] is not None]
    p2_rec = [c["phase2"]["recall"] for c in cases if c["phase2"]["recall"] is not None]
    p2_f1 = [c["phase2"]["f1"] for c in cases if c["phase2"]["f1"] is not None]
    p2_jac = [c["phase2"]["jaccard"] for c in cases if c["phase2"]["jaccard"] is not None]
    summary["phase2"] = {
        "precision": _avg_metric(p2_prec),
        "recall": _avg_metric(p2_rec),
        "f1": _avg_metric(p2_f1),
        "jaccard": _avg_metric(p2_jac),
    }

    # ── Phase 3 ──
    p3_total = [c["phase3"]["total_percentage"] for c in cases if c["phase3"]["total_percentage"] is not None]
    # 各维度
    p3_dims = {}
    for c in cases:
        for dim_name, dim_data in c["phase3"].get("dimensions", {}).items():
            if dim_name not in p3_dims:
                p3_dims[dim_name] = []
            p3_dims[dim_name].append(dim_data.get("percentage"))

    dim_summary = {}
    for dim_name, vals in p3_dims.items():
        dim_summary[dim_name] = {
            "percentage": _avg_metric(vals),
            "std": _std(vals, 2),
            "count": len([v for v in vals if v is not None]),
        }

    summary["phase3"] = {
        "total_percentage": _avg_metric(p3_total),
        "dimensions": dim_summary,
        "clinical_note": _compute_subjective_summary(
            [c["phase3"]["clinical_note"] for c in cases if c["phase3"].get("clinical_note")]
        ),
    }

    # ── Phase 4 ──
    dis_prec = [c["phase4"]["disorder"]["precision"] for c in cases if c["phase4"]["disorder"]["precision"] is not None]
    dis_rec = [c["phase4"]["disorder"]["recall"] for c in cases if c["phase4"]["disorder"]["recall"] is not None]
    dis_f1 = [c["phase4"]["disorder"]["f1"] for c in cases if c["phase4"]["disorder"]["f1"] is not None]
    dis_jac = [c["phase4"]["disorder"]["jaccard"] for c in cases if c["phase4"]["disorder"]["jaccard"] is not None]

    cat_prec = [c["phase4"]["category"]["precision"] for c in cases if c["phase4"]["category"]["precision"] is not None]
    cat_rec = [c["phase4"]["category"]["recall"] for c in cases if c["phase4"]["category"]["recall"] is not None]
    cat_f1 = [c["phase4"]["category"]["f1"] for c in cases if c["phase4"]["category"]["f1"] is not None]
    cat_jac = [c["phase4"]["category"]["jaccard"] for c in cases if c["phase4"]["category"]["jaccard"] is not None]

    em_vals = [c["phase4"]["primary"]["exact_match"] for c in cases if c["phase4"]["primary"]["exact_match"] is not None]
    h3_vals = [c["phase4"]["primary"]["hit_at_3"] for c in cases if c["phase4"]["primary"]["hit_at_3"] is not None]
    rr_vals = [c["phase4"]["primary"]["reciprocal_rank"] for c in cases if c["phase4"]["primary"]["reciprocal_rank"] is not None]
    poa_vals = [c["phase4"]["ranking"]["poa"] for c in cases if c["phase4"]["ranking"]["poa"] is not None]
    ndcg_vals = [c["phase4"]["ranking"]["ndcg"] for c in cases if c["phase4"]["ranking"]["ndcg"] is not None]

    summary["phase4"] = {
        "disorder": {
            "precision": _avg_metric(dis_prec),
            "recall": _avg_metric(dis_rec),
            "f1": _avg_metric(dis_f1),
            "jaccard": _avg_metric(dis_jac),
        },
        "category": {
            "precision": _avg_metric(cat_prec),
            "recall": _avg_metric(cat_rec),
            "f1": _avg_metric(cat_f1),
            "jaccard": _avg_metric(cat_jac),
        },
        "primary": {
            "exact_match": _avg_metric(em_vals),
            "hit_at_3": _avg_metric(h3_vals),
            "reciprocal_rank": _avg_metric(rr_vals),
        },
        "ranking": {
            "poa": _avg_metric(poa_vals),
            "ndcg": _avg_metric(ndcg_vals),
        },
        "diagnostic_rigor": _compute_subjective_summary(
            [c["phase4"]["diagnostic_rigor"] for c in cases if c["phase4"].get("diagnostic_rigor")]
        ),
    }

    # ── Phase 5 ──
    summary["phase5"] = {
        "treatment": _compute_subjective_summary(
            [c["phase5"]["treatment"] for c in cases if c["phase5"].get("treatment")]
        ),
    }

    return summary


def _std(values: List, decimals: int = 2) -> Optional[float]:
    """计算标准差"""
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return None
    mean = sum(vals) / len(vals)
    variance = sum((x - mean) ** 2 for x in vals) / len(vals)
    return round(math.sqrt(variance), decimals)


def _compute_subjective_summary(subj_list: List[Optional[Dict]]) -> Dict[str, Any]:
    """计算主观评分的汇总统计

    包括：
    - 均值 (avg) 和标准差 (std)
    - 每个 evaluator 的均值和标准差
    """
    if not subj_list:
        return {}

    # 总体均值
    avgs = [s["avg"] for s in subj_list if s is not None and "avg" in s]
    result = {"avg": _avg_level(avgs), "std": _std(avgs), "count": len(avgs)}

    # 各 evaluator 的均值和标准差
    evaluator_avgs = {}  # model_name -> [scores]
    for s in subj_list:
        if not s or "evaluators" not in s:
            continue
        for model, score in s["evaluators"].items():
            if model not in evaluator_avgs:
                evaluator_avgs[model] = []
            if score is not None:
                evaluator_avgs[model].append(score)

    evaluator_summary = {}
    for model, scores in evaluator_avgs.items():
        evaluator_summary[model] = {
            "avg": _avg_level(scores),
            "std": _std(scores),
            "count": len(scores),
        }
    result["evaluators"] = evaluator_summary

    return result


# ────────────────────── Save ──────────────────────

def save_results(
    model_name: str,
    cases: List[Dict[str, Any]],
    summary: Dict[str, Any],
) -> Path:
    """保存结果到 data/output/results/{model_name}.json"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{model_name}.json"

    output = {
        "model_name": model_name,
        "num_cases": len(cases),
        "summary": summary,
        "cases": cases,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return out_path


# Need json import
import json
