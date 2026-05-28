"""Cross-model metrics aggregation — computes per-model averages and exports
a structured JSON summary.

Ported from the original ``cal_metrics.py`` script.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = _PROJECT_ROOT / "data" / "output" / "results"
EVAL_DIR = _PROJECT_ROOT / "data" / "output" / "evaluation"
OUTPUT_DIR = _PROJECT_ROOT / "results"

OBJECTIVE_METRICS = [
    ("phase1", [("Chief Complaint Coverage", "phase1_cc", "pct"), ("Mental Status Coverage", "phase1_ms", "pct"), ("Overall Coverage", "phase1_overall", "pct")]),
    ("phase2", [("Precision", "phase2_precision", "dec4"), ("Recall", "phase2_recall", "dec4"), ("F1", "phase2_f1", "dec4"), ("Jaccard", "phase2_jaccard", "dec4")]),
    ("phase3", [("Total Score", "phase3_total", "pct"), ("Chief Complaint", "phase3_chief_complaint", "dec4"), ("Physical Exam", "phase3_physical_examination", "dec4"), ("Mental Exam", "phase3_mental_examination", "dec4"), ("Past/Family History", "phase3_past_family_history", "dec4")]),
    ("phase4", [("Category Precision", "phase4_cat_precision", "dec4"), ("Category Recall", "phase4_cat_recall", "dec4"), ("Category F1", "phase4_cat_f1", "dec4"), ("Category Jaccard", "phase4_cat_jaccard", "dec4"), ("Exact Match", "phase4_exact_match", "dec4"), ("nDCG", "phase4_ndcg", "dec4"), ("Reciprocal Rank", "phase4_rr", "dec4")]),
    ("phase5", [("Text Length", "phase5_length", "int")]),
]

SUBJECTIVE_METRICS = [
    ("Empathy", "phase1_empathy"), ("Professionalism", "phase1_profession"),
    ("Note Quality", "phase3_subjective"), ("Diagnostic Rigor", "phase4_subjective"),
    ("Treatment Appropriateness", "phase5_subjective"),
]

_KEY_OBJ = {"phase1_overall": 100.0, "phase2_f1": 1.0, "phase3_total": 100.0, "phase4_cat_f1": 1.0, "phase4_exact_match": 1.0, "phase4_ndcg": 1.0, "phase4_rr": 1.0}
_KEY_SUBJ = ["phase1_empathy", "phase1_profession", "phase3_subjective", "phase4_subjective", "phase5_subjective"]


def _avg(scores_list: List[Dict], key: str) -> Optional[float]:
    values = [s[key] for s in scores_list if s.get(key) is not None]
    return sum(values) / len(values) if values else None


def _load_scores_from_eval(model_name: str) -> List[Dict[str, Any]]:
    eval_path = EVAL_DIR / model_name
    if not eval_path.exists():
        return []
    scores_list = []
    for case_dir in sorted(eval_path.iterdir()):
        if not case_dir.is_dir():
            continue
        s: Dict[str, Any] = {}
        for phase, extractor in [
            (1, lambda d: [("phase1_cc", d["coverage_stats"]["chief_complaint_coverage"]), ("phase1_ms", d["coverage_stats"]["mental_status_coverage"]), ("phase1_overall", d["coverage_stats"]["overall_coverage"]), ("phase1_empathy", (d.get("empathy_evaluation") or {}).get("score")), ("phase1_profession", (d.get("profession_evaluation") or {}).get("score"))]),
            (2, lambda d: [("phase2_precision", d["metrics"]["precision"]), ("phase2_recall", d["metrics"]["recall"]), ("phase2_f1", d["metrics"]["f1"]), ("phase2_jaccard", d["metrics"]["jaccard"])]),
            (3, lambda d: [("phase3_total", d["total_percentage"]), ("phase3_subjective", (d.get("clinical_note_subjective") or {}).get("score"))] + [(f"phase3_{dim}", dim_data.get("percentage")) for dim, dim_data in d.get("dimensions", {}).items()]),
            (4, lambda d: [
                ("phase4_cat_precision", d["category_metrics"]["precision"]), ("phase4_cat_recall", d["category_metrics"]["recall"]), ("phase4_cat_f1", d["category_metrics"]["f1"]), ("phase4_cat_jaccard", d["category_metrics"]["jaccard"]),
                ("phase4_exact_match", d["primary_metrics"]["primary_exact_match"]), ("phase4_rr", d["primary_metrics"]["primary_reciprocal_rank"]),
                ("phase4_ndcg", d["ranking_metrics"]["ndcg"]), ("phase4_poa", d["ranking_metrics"].get("poa")),
                ("phase4_subjective", (d.get("diagnostic_rigor_subjective") or {}).get("score")),
            ]),
            (5, lambda d: [("phase5_subjective", (d.get("treatment_subjective") or {}).get("score")), ("phase5_length", d.get("treatment_plan_length"))]),
        ]:
            pfile = case_dir / f"evaluation_phase{phase}_output.json"
            if pfile.exists():
                try:
                    data = json.loads(pfile.read_text(encoding="utf-8"))
                    for k, v in extractor(data):
                        if v is not None:
                            s[k] = v
                except (json.JSONDecodeError, OSError, KeyError):
                    pass
        if s:
            scores_list.append(s)
    return scores_list


def _composite_obj(scores_list: List[Dict]) -> Optional[float]:
    vals = [_avg(scores_list, k) / cap for k, cap in _KEY_OBJ.items() if _avg(scores_list, k) is not None]
    return sum(vals) / len(vals) if vals else None


def _composite_subj(scores_list: List[Dict]) -> Optional[float]:
    vals = [_avg(scores_list, k) for k in _KEY_SUBJ if _avg(scores_list, k) is not None]
    return sum(vals) / len(vals) if vals else None


def aggregate_metrics(
    models: Optional[List[str]] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """Compute per-model averages and write a structured JSON summary.

    Returns the path to the output file.
    """
    if models is None:
        if RESULTS_DIR.exists():
            models = sorted(p.stem for p in RESULTS_DIR.glob("*.json"))
        if not models:
            models = sorted(d.name for d in EVAL_DIR.iterdir()) if EVAL_DIR.exists() else []
    if not models:
        raise FileNotFoundError("No model data found")

    results: Dict[str, Any] = {}
    for model_name in models:
        scores_list = _load_scores_from_eval(model_name)
        if not scores_list:
            scores_list = []
            rp = RESULTS_DIR / f"{model_name}.json"
            if rp.exists():
                try:
                    data = json.loads(rp.read_text(encoding="utf-8"))
                    scores_list = [r.get("scores", {}) for r in data.get("per_case", [])]
                except (json.JSONDecodeError, OSError):
                    pass
        if not scores_list:
            continue

        objective: Dict[str, Any] = {}
        for phase_key, metrics in OBJECTIVE_METRICS:
            phase_data = {}
            for label, key, fmt_type in metrics:
                avg = _avg(scores_list, key)
                if avg is not None:
                    if fmt_type == "pct":
                        phase_data[label] = f"{avg:.2f}%"
                    elif fmt_type == "dec4":
                        phase_data[label] = round(avg, 4)
                    elif fmt_type == "int":
                        phase_data[label] = int(round(avg))
            objective[phase_key] = phase_data

        comp_obj = _composite_obj(scores_list)
        if comp_obj is not None:
            objective["objective_composite"] = round(comp_obj, 4)

        subjective: Dict[str, Any] = {}
        for label, key in SUBJECTIVE_METRICS:
            avg = _avg(scores_list, key)
            if avg is not None:
                subjective[label] = round(avg, 2)

        comp_subj = _composite_subj(scores_list)
        if comp_subj is not None:
            subjective["subjective_composite"] = round(comp_subj, 2)

        results[model_name] = {"objective": objective, "subjective": subjective}

    out = output_path or OUTPUT_DIR / "results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"models": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Results saved: {out} ({len(results)} models)")
    return out
