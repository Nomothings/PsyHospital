"""
疾病难度分析报告

按两个维度分组对比各模型在各评估指标上的表现:
1. 病例复杂度: 单病症 vs 共病(多病症)
2. 疾病稀有度: 最常见疾病(Top-3) vs 最罕见疾病(Bottom-3)

数据源:
    - 真实诊断: 从 evaluation_phase4_output.json 提取(跨模型100%一致)
    - 评估指标: 从各模型的 evaluation/ 目录提取
"""

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

EVAL_BASE = Path(__file__).parent / "data" / "output" / "evaluation"

MODELS = [
    "deepseek-v4-pro",
    "qwen3-4b",
    "qwen3-14b",
    "qwq-32b",
    "claude-sonnet-4-6",
    "gpt-5.5",
]

OBJECTIVE_METRICS = [
    ("P1 整体覆盖", "phase1_overall", "pct"),
    ("P2 F1", "phase2_f1", "dec4"),
    ("P2 Jaccard", "phase2_jaccard", "dec4"),
    ("P3 总分", "phase3_total", "pct"),
    ("P4 类别 F1", "phase4_cat_f1", "dec4"),
    ("P4 Exact Match", "phase4_exact_match", "dec4"),
    ("P4 nDCG", "phase4_ndcg", "dec4"),
    ("P4 Reciprocal Rank", "phase4_rr", "dec4"),
]

SUBJECTIVE_METRICS = [
    ("P1 共情", "phase1_empathy", "score5"),
    ("P1 专业", "phase1_profession", "score5"),
    ("P3 病历质量", "phase3_subjective", "score5"),
    ("P4 诊断严谨", "phase4_subjective", "score5"),
    ("P5 治疗合理", "phase5_subjective", "score5"),
]

ALL_KEYS = [m[1] for m in OBJECTIVE_METRICS + SUBJECTIVE_METRICS]


def _fmt(value: Optional[float], fmt: str) -> str:
    if value is None:
        return "N/A"
    if fmt == "pct":
        return f"{value:.1f}%"
    if fmt == "dec4":
        return f"{value:.4f}"
    if fmt == "score5":
        return f"{value:.2f}"
    return str(value)


def _avg(values: List[float]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def load_true_disorders() -> Dict[str, List[str]]:
    disorders = {}
    ref_dir = EVAL_BASE / MODELS[0]
    for f in ref_dir.glob("*/evaluation_phase4_output.json"):
        d = json.loads(f.read_text())
        disorders[d["case_id"]] = d.get("true_disorders", [])
    return disorders


def load_model_scores(model_name: str) -> Dict[str, Dict]:
    scores = {}
    eval_dir = EVAL_BASE / model_name
    if not eval_dir.exists():
        return scores
    for case_dir in sorted(eval_dir.iterdir()):
        if not case_dir.is_dir():
            continue
        cid = case_dir.name
        s = {}
        p1_file = case_dir / "evaluation_phase1_output.json"
        if p1_file.exists():
            try:
                p1 = json.loads(p1_file.read_text())
                cov = p1.get("coverage_stats", {})
                s["phase1_overall"] = cov.get("overall_coverage")
                emp = p1.get("empathy_evaluation")
                if emp:
                    s["phase1_empathy"] = emp.get("score")
                pro = p1.get("profession_evaluation")
                if pro:
                    s["phase1_profession"] = pro.get("score")
            except (json.JSONDecodeError, OSError):
                pass
        p2_file = case_dir / "evaluation_phase2_output.json"
        if p2_file.exists():
            try:
                p2 = json.loads(p2_file.read_text())
                met = p2.get("metrics", {})
                if met:
                    s["phase2_f1"] = met.get("f1")
                    s["phase2_jaccard"] = met.get("jaccard")
            except (json.JSONDecodeError, OSError):
                pass
        p3_file = case_dir / "evaluation_phase3_output.json"
        if p3_file.exists():
            try:
                p3 = json.loads(p3_file.read_text())
                s["phase3_total"] = p3.get("total_percentage")
                subj = p3.get("clinical_note_subjective")
                if subj:
                    s["phase3_subjective"] = subj.get("score")
            except (json.JSONDecodeError, OSError):
                pass
        p4_file = case_dir / "evaluation_phase4_output.json"
        if p4_file.exists():
            try:
                p4 = json.loads(p4_file.read_text())
                cat_m = p4.get("category_metrics", {})
                s["phase4_cat_f1"] = cat_m.get("f1")
                primary_m = p4.get("primary_metrics", {})
                s["phase4_exact_match"] = primary_m.get("primary_exact_match")
                s["phase4_rr"] = primary_m.get("primary_reciprocal_rank")
                rank_m = p4.get("ranking_metrics", {})
                s["phase4_ndcg"] = rank_m.get("ndcg")
                diag_subj = p4.get("diagnostic_rigor_subjective")
                if diag_subj:
                    s["phase4_subjective"] = diag_subj.get("score")
            except (json.JSONDecodeError, OSError):
                pass
        p5_file = case_dir / "evaluation_phase5_output.json"
        if p5_file.exists():
            try:
                p5 = json.loads(p5_file.read_text())
                subj = p5.get("treatment_subjective")
                if subj:
                    s["phase5_subjective"] = subj.get("score")
            except (json.JSONDecodeError, OSError):
                pass
        if s:
            scores[cid] = s
    return scores


def classify_cases(
    true_disorders: Dict[str, List[str]],
    top_n: int = 3,
    bottom_n: int = 3,
):
    all_disorders = Counter()
    for disorders in true_disorders.values():
        for d in disorders:
            all_disorders[d] += 1

    single_ids = [cid for cid, d in true_disorders.items() if len(d) == 1]
    multi_ids = [cid for cid, d in true_disorders.items() if len(d) > 1]

    top_diseases = [d for d, _ in all_disorders.most_common(top_n)]
    bottom_diseases = [d for d, _ in all_disorders.most_common()[-bottom_n:]]

    top_ids = []
    bottom_ids = []
    for cid, disorders in true_disorders.items():
        if any(d in top_diseases for d in disorders):
            top_ids.append(cid)
        if any(d in bottom_diseases for d in disorders):
            bottom_ids.append(cid)

    # 稀有度分组互斥: 只保留仅含top或仅含bottom的case
    pure_top = [c for c in top_ids if c not in set(bottom_ids)]
    pure_bottom = [c for c in bottom_ids if c not in set(top_ids)]

    return (
        ("单病症", single_ids),
        ("共病(多病症)", multi_ids),
    ), (
        (f"常见(Top-3): {', '.join(d for d in top_diseases)}", pure_top),
        (f"罕见(Bottom-3): {', '.join(d for d in bottom_diseases)}", pure_bottom),
    ), all_disorders


def analyze_group(scores: Dict[str, Dict], case_ids: List[str]) -> Dict[str, Optional[float]]:
    result = {}
    for key in ALL_KEYS:
        values = [scores[cid][key] for cid in case_ids if cid in scores and scores[cid].get(key) is not None]
        result[key] = _avg(values)
    return result


def print_table(title: str, label_a: str, stats_a: Dict, label_b: str, stats_b: Dict, n_a: int, n_b: int):
    name_col = 14
    a_col = max(12, len(label_a) + 2)
    b_col = max(12, len(label_b) + 2)
    diff_col = 10
    total_w = name_col + a_col + b_col + diff_col + 4
    width = max(80, total_w + 4)

    print(f"\n{'─' * width}")
    print(f"  {title}")
    print(f"  {label_a} (n={n_a}) vs {label_b} (n={n_b})")
    print(f"{'─' * width}")

    hdr = f"  {'指标':<{name_col}}{label_a:^{a_col}}{label_b:^{b_col}}{'差距':^{diff_col}}"
    print(hdr)
    print(f"  {'─' * (total_w - 2)}")

    for label, key, fmt in OBJECTIVE_METRICS:
        v_a = stats_a.get(key)
        v_b = stats_b.get(key)
        if v_a is not None and v_b is not None:
            diff = v_b - v_a
            if fmt == "pct":
                diff_str = f"{diff:+.1f}%"
            elif fmt == "dec4":
                diff_str = f"{diff:+.4f}"
            else:
                diff_str = f"{diff:+.2f}"
        else:
            diff_str = "N/A"
        print(f"    {label:<{name_col - 2}}{_fmt(v_a, fmt):^{a_col}}{_fmt(v_b, fmt):^{b_col}}{diff_str:^{diff_col}}")

    print(f"  {'─' * (total_w - 2)}")
    print(f"    主观指标")
    for label, key, fmt in SUBJECTIVE_METRICS:
        v_a = stats_a.get(key)
        v_b = stats_b.get(key)
        if v_a is not None and v_b is not None:
            diff = v_b - v_a
            diff_str = f"{diff:+.2f}"
        else:
            diff_str = "N/A"
        val_a = f"{v_a:.2f}" if v_a is not None else "N/A"
        val_b = f"{v_b:.2f}" if v_b is not None else "N/A"
        print(f"    {label:<{name_col - 2}}{val_a:^{a_col}}{val_b:^{b_col}}{diff_str:^{diff_col}}")


def main():
    print("=" * 80)
    print("  疾病难度分析: 加载数据...")
    print("=" * 80)

    true_disorders = load_true_disorders()
    print(f"\n  真实诊断: {len(true_disorders)} cases")

    # 统计
    all_disorders = Counter()
    for disorders in true_disorders.values():
        for d in disorders:
            all_disorders[d] += 1

    single_count = sum(1 for d in true_disorders.values() if len(d) == 1)
    multi_count = sum(1 for d in true_disorders.values() if len(d) > 1)
    print(f"\n  单病症: {single_count} cases ({single_count/len(true_disorders)*100:.1f}%)")
    print(f"  共病: {multi_count} cases ({multi_count/len(true_disorders)*100:.1f}%)")

    print(f"\n  疾病频率 Top 3:")
    for d, c in all_disorders.most_common(3):
        print(f"    {c:3d}  {d}")
    print(f"\n  疾病频率 Bottom 3:")
    for d, c in all_disorders.most_common()[-3:]:
        print(f"    {c:3d}  {d}")

    model_scores_all = {}
    for model in MODELS:
        model_scores_all[model] = load_model_scores(model)
        print(f"  {model}: {len(model_scores_all[model])} cases")

    complexity_groups, rarity_groups, _ = classify_cases(true_disorders)

    # ─── 实验 1: 单病症 vs 共病 ───
    print(f"\n\n{'#' * 80}")
    print(f"#  实验 1: 单病症 vs 共病")
    print(f"{'#' * 80}")

    s_label, s_ids = complexity_groups[0]
    m_label, m_ids = complexity_groups[1]

    for model in MODELS:
        scores = model_scores_all[model]
        s_filtered = [c for c in s_ids if c in scores]
        m_filtered = [c for c in m_ids if c in scores]
        if not s_filtered and not m_filtered:
            continue
        stats_s = analyze_group(scores, s_filtered)
        stats_m = analyze_group(scores, m_filtered)
        print_table(f"模型: {model}", s_label, stats_s, m_label, stats_m, len(s_filtered), len(m_filtered))

    # 跨模型汇总
    print(f"\n{'#' * 80}")
    print(f"#  跨模型汇总: 单病症 vs 共病")
    print(f"{'#' * 80}")

    cross_s = {}
    cross_m = {}
    for key in ALL_KEYS:
        s_vals = []
        m_vals = []
        for model in MODELS:
            scores = model_scores_all[model]
            for cid in s_ids:
                if cid in scores and scores[cid].get(key) is not None:
                    s_vals.append(scores[cid][key])
            for cid in m_ids:
                if cid in scores and scores[cid].get(key) is not None:
                    m_vals.append(scores[cid][key])
        cross_s[key] = _avg(s_vals)
        cross_m[key] = _avg(m_vals)

    print_table(
        "跨模型均值(所有模型所有case合并计算)",
        s_label, cross_s, m_label, cross_m, single_count, multi_count
    )

    # ─── 实验 2: 常见 vs 罕见 ───
    print(f"\n\n{'#' * 80}")
    print(f"#  实验 2: 常见疾病(Top-3) vs 罕见疾病(Bottom-3)")
    print(f"{'#' * 80}")

    t_label, t_ids = rarity_groups[0]
    b_label, b_ids = rarity_groups[1]

    for model in MODELS:
        scores = model_scores_all[model]
        t_filtered = [c for c in t_ids if c in scores]
        b_filtered = [c for c in b_ids if c in scores]
        if not t_filtered and not b_filtered:
            continue
        stats_t = analyze_group(scores, t_filtered)
        stats_b = analyze_group(scores, b_filtered)
        print_table(f"模型: {model}", t_label, stats_t, b_label, stats_b, len(t_filtered), len(b_filtered))

    # 跨模型汇总
    print(f"\n{'#' * 80}")
    print(f"#  跨模型汇总: 常见 vs 罕见")
    print(f"{'#' * 80}")

    cross_t = {}
    cross_b = {}
    for key in ALL_KEYS:
        t_vals = []
        b_vals = []
        for model in MODELS:
            scores = model_scores_all[model]
            for cid in t_ids:
                if cid in scores and scores[cid].get(key) is not None:
                    t_vals.append(scores[cid][key])
            for cid in b_ids:
                if cid in scores and scores[cid].get(key) is not None:
                    b_vals.append(scores[cid][key])
        cross_t[key] = _avg(t_vals)
        cross_b[key] = _avg(b_vals)

    print_table(
        "跨模型均值(所有模型所有case合并计算)",
        t_label, cross_t, b_label, cross_b, len(t_ids), len(b_ids)
    )


if __name__ == "__main__":
    main()
