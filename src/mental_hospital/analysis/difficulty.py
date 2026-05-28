"""Disease difficulty analysis — compares model performance across case complexity
and disease rarity dimensions.

Ported from the original ``analyze_difficulty.py`` script.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
EVAL_BASE = _PROJECT_ROOT / "data" / "output" / "evaluation"

OBJECTIVE_METRICS = [
    ("P1 Overall Coverage", "phase1_overall", "pct"),
    ("P2 F1", "phase2_f1", "dec4"),
    ("P2 Jaccard", "phase2_jaccard", "dec4"),
    ("P3 Total Score", "phase3_total", "pct"),
    ("P4 Category F1", "phase4_cat_f1", "dec4"),
    ("P4 Exact Match", "phase4_exact_match", "dec4"),
    ("P4 nDCG", "phase4_ndcg", "dec4"),
    ("P4 Reciprocal Rank", "phase4_rr", "dec4"),
]

SUBJECTIVE_METRICS = [
    ("P1 Empathy", "phase1_empathy", "score5"),
    ("P1 Professionalism", "phase1_profession", "score5"),
    ("P3 Note Quality", "phase3_subjective", "score5"),
    ("P4 Diagnostic Rigor", "phase4_subjective", "score5"),
    ("P5 Treatment Appropriateness", "phase5_subjective", "score5"),
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


def _load_true_disorders(ref_model: str) -> Dict[str, List[str]]:
    disorders: Dict[str, List[str]] = {}
    ref_dir = EVAL_BASE / ref_model
    if not ref_dir.exists():
        return disorders
    for f in ref_dir.glob("*/evaluation_phase4_output.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        disorders[d["case_id"]] = d.get("true_disorders", [])
    return disorders


def _load_model_scores(model_name: str) -> Dict[str, Dict]:
    scores: Dict[str, Dict] = {}
    eval_dir = EVAL_BASE / model_name
    if not eval_dir.exists():
        return scores
    for case_dir in sorted(eval_dir.iterdir()):
        if not case_dir.is_dir():
            continue
        cid = case_dir.name
        s: Dict = {}
        for phase, keys_fn in [
            (1, lambda d: [
                ("phase1_overall", d.get("coverage_stats", {}).get("overall_coverage")),
                ("phase1_empathy", (d.get("empathy_evaluation") or {}).get("score")),
                ("phase1_profession", (d.get("profession_evaluation") or {}).get("score")),
            ]),
            (2, lambda d: [("phase2_f1", d.get("metrics", {}).get("f1")), ("phase2_jaccard", d.get("metrics", {}).get("jaccard"))]),
            (3, lambda d: [("phase3_total", d.get("total_percentage")), ("phase3_subjective", (d.get("clinical_note_subjective") or {}).get("score"))]),
            (4, lambda d: [
                ("phase4_cat_f1", d.get("category_metrics", {}).get("f1")),
                ("phase4_exact_match", d.get("primary_metrics", {}).get("primary_exact_match")),
                ("phase4_rr", d.get("primary_metrics", {}).get("primary_reciprocal_rank")),
                ("phase4_ndcg", d.get("ranking_metrics", {}).get("ndcg")),
                ("phase4_subjective", (d.get("diagnostic_rigor_subjective") or {}).get("score")),
            ]),
            (5, lambda d: [("phase5_subjective", (d.get("treatment_subjective") or {}).get("score"))]),
        ]:
            pfile = case_dir / f"evaluation_phase{phase}_output.json"
            if pfile.exists():
                try:
                    data = json.loads(pfile.read_text(encoding="utf-8"))
                    for k, v in keys_fn(data):
                        if v is not None:
                            s[k] = v
                except (json.JSONDecodeError, OSError):
                    pass
        if s:
            scores[cid] = s
    return scores


def _classify_cases(true_disorders: Dict[str, List[str]], top_n: int = 3, bottom_n: int = 3):
    all_disorders = Counter()
    for disorders in true_disorders.values():
        for d in disorders:
            all_disorders[d] += 1
    single_ids = [cid for cid, d in true_disorders.items() if len(d) == 1]
    multi_ids = [cid for cid, d in true_disorders.items() if len(d) > 1]
    top_diseases = [d for d, _ in all_disorders.most_common(top_n)]
    bottom_diseases = [d for d, _ in all_disorders.most_common()[-bottom_n:]]
    top_ids, bottom_ids = [], []
    for cid, disorders in true_disorders.items():
        if any(d in top_diseases for d in disorders):
            top_ids.append(cid)
        if any(d in bottom_diseases for d in disorders):
            bottom_ids.append(cid)
    pure_top = [c for c in top_ids if c not in set(bottom_ids)]
    pure_bottom = [c for c in bottom_ids if c not in set(top_ids)]
    return (
        ("Single-disorder", single_ids),
        ("Comorbid (multi-disorder)", multi_ids),
    ), (
        (f"Common (Top-{top_n}): {', '.join(top_diseases)}", pure_top),
        (f"Rare (Bottom-{bottom_n}): {', '.join(bottom_diseases)}", pure_bottom),
    ), all_disorders


def analyze_difficulty(
    models: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    """Run the full difficulty analysis and write a report.

    Returns the path to the generated report file.
    """
    if models is None:
        models = [d.name for d in EVAL_BASE.iterdir() if d.is_dir()] if EVAL_BASE.exists() else []
    if not models:
        raise FileNotFoundError(f"No model data found in {EVAL_BASE}")

    ref_model = models[0]
    true_disorders = _load_true_disorders(ref_model)

    model_scores = {m: _load_model_scores(m) for m in models}
    complexity_groups, rarity_groups, all_disorders = _classify_cases(true_disorders)

    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("  Disease Difficulty Analysis Report")
    lines.append("=" * 80)
    lines.append(f"  Models: {', '.join(models)}")
    lines.append(f"  Cases with ground truth: {len(true_disorders)}")

    # Experiment 1: single vs multi
    lines.append(f"\n{'#' * 80}")
    lines.append(f"#  Experiment 1: Single-disorder vs Comorbid")
    for model in models:
        scores = model_scores[model]
        for label, ids in complexity_groups:
            filtered = [c for c in ids if c in scores]
            avgs = {k: _avg([scores[cid][k] for cid in filtered if scores[cid].get(k) is not None]) for k in ALL_KEYS}
            lines.append(f"\n  Model: {model} — {label} (n={len(filtered)})")
            for name, key, fmt in OBJECTIVE_METRICS:
                lines.append(f"    {name}: {_fmt(avgs.get(key), fmt)}")
            for name, key, fmt in SUBJECTIVE_METRICS:
                lines.append(f"    {name}: {_fmt(avgs.get(key), fmt)}")

    # Experiment 2: common vs rare
    lines.append(f"\n{'#' * 80}")
    lines.append(f"#  Experiment 2: Common vs Rare Diseases")
    for model in models:
        scores = model_scores[model]
        for label, ids in rarity_groups:
            filtered = [c for c in ids if c in scores]
            avgs = {k: _avg([scores[cid][k] for cid in filtered if scores[cid].get(k) is not None]) for k in ALL_KEYS}
            lines.append(f"\n  Model: {model} — {label} (n={len(filtered)})")
            for name, key, fmt in OBJECTIVE_METRICS:
                lines.append(f"    {name}: {_fmt(avgs.get(key), fmt)}")
            for name, key, fmt in SUBJECTIVE_METRICS:
                lines.append(f"    {name}: {_fmt(avgs.get(key), fmt)}")

    report = "\n".join(lines)
    out = (output_dir or _PROJECT_ROOT / "results") / "difficulty_analysis.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nReport saved: {out}")
    return out
