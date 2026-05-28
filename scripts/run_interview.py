#!/usr/bin/env python3
"""MentalHospital — LLM-based psychiatric interview simulation system.

Usage::

    python scripts/run_interview.py --mode test
    python scripts/run_interview.py --mode test --case-id 01343170
    python scripts/run_interview.py --mode eval
    python scripts/run_interview.py --mode batch --concurrency 32
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any, Dict, List, Optional

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from mental_hospital.config import settings
from mental_hospital.data.loader import load_all_cases, load_random_case
from mental_hospital.data.output import get_output_dir
from mental_hospital.evaluation import (
    MetricsExtractor,
    evaluate_history,
    evaluate_examination,
    evaluate_formulation,
    evaluate_diagnosis,
    evaluate_treatment,
)
from mental_hospital.interview import InterviewPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("mental_hospital")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "output" / "results"

_METRICS_4DEC = {
    "p2_precision", "p2_recall", "p2_f1",
    "p4_disorder_precision", "p4_disorder_recall", "p4_disorder_f1", "p4_disorder_jaccard",
    "p4_category_precision", "p4_category_recall", "p4_category_f1", "p4_category_jaccard",
    "p4_exact_match", "p4_rr", "p4_poa", "p4_ndcg",
}

_results_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Core pipeline (interview + evaluation)
# ---------------------------------------------------------------------------

def run_full_interview(
    case: Optional[Dict[str, Any]] = None,
    *, patient_backup: bool = False, instrument_backup: bool = False,
) -> Dict[str, Any]:
    pipeline = InterviewPipeline()
    result = pipeline.run(case=case, patient_backup=patient_backup, instrument_backup=instrument_backup)
    model, cid = result["model_name"], result["case_id"]

    print("Evaluating Phase 1...", flush=True)
    p1e = evaluate_history(model_name=model, case_id=cid)
    print("Evaluating Phase 2...", flush=True)
    p2e = evaluate_examination(model_name=model, case_id=cid, case_data=case)
    print("Evaluating Phase 3...", flush=True)
    p3e = evaluate_formulation(model_name=model, case_id=cid)
    print("Evaluating Phase 4...", flush=True)
    p4e = evaluate_diagnosis(model_name=model, case_id=cid)
    print("Evaluating Phase 5...", flush=True)
    p5e = evaluate_treatment(model_name=model, case_id=cid)

    result.setdefault("phase1", {})["evaluation"] = {"coverage_stats": p1e["coverage_stats"], "conversation_stats": p1e["conversation_stats"], "empathy_evaluation": p1e.get("empathy_evaluation"), "profession_evaluation": p1e.get("profession_evaluation"), "output_file": p1e["output_file"]}
    result.setdefault("phase2", {})["evaluation"] = {"metrics": p2e["metrics"], "counts": p2e["counts"], "output_file": p2e["output_file"]}
    result.setdefault("phase3", {})["evaluation"] = {"total_percentage": p3e["total_percentage"], "total_weighted_score": p3e.get("total_weighted_score"), "dimensions": p3e.get("dimensions", {}), "clinical_note_subjective": p3e.get("clinical_note_subjective"), "output_file": p3e["output_file"]}
    result.setdefault("phase4", {})["evaluation"] = {"disorder_metrics": p4e["disorder_metrics"], "category_metrics": p4e["category_metrics"], "primary_metrics": p4e["primary_metrics"], "ranking_metrics": p4e["ranking_metrics"], "diagnostic_rigor_subjective": p4e.get("diagnostic_rigor_subjective"), "predicted_diagnoses": p4e.get("predicted_diagnoses", []), "true_disorders": p4e.get("true_disorders", []), "predicted_categories": p4e.get("predicted_categories"), "true_categories": p4e.get("true_categories"), "output_file": p4e["output_file"]}
    result.setdefault("phase5", {})["evaluation"] = {"treatment_subjective": p5e.get("treatment_subjective"), "output_file": p5e["output_file"]}

    output_dir = get_output_dir(model, cid)
    (output_dir / "interview_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    metrics = MetricsExtractor.from_interview_result(result)
    _append_per_case_result(model, cid, metrics)
    return result


# ---------------------------------------------------------------------------
# Results persistence
# ---------------------------------------------------------------------------

def _get_results_path(model_name: str) -> Path:
    return RESULTS_DIR / f"{model_name}.json"


def _append_per_case_result(model_name: str, case_id: str, metrics) -> None:
    path = _get_results_path(model_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"case_id": case_id, "scores": metrics.to_dict(include_details=False)}
    with _results_lock:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {"model": model_name, "num_cases": 0, "averages": {}, "per_case": []}
        else:
            data = {"model": model_name, "num_cases": 0, "averages": {}, "per_case": []}
        per_case = data.setdefault("per_case", [])
        existing = {r["case_id"]: i for i, r in enumerate(per_case)}
        if case_id in existing:
            per_case[existing[case_id]] = record
        else:
            per_case.append(record)
        data["num_cases"] = len(per_case)
        _update_averages(data)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _update_averages(data: Dict[str, Any]) -> None:
    per_case = data.get("per_case", [])
    scores_list = [r.get("scores", {}) for r in per_case]
    if not scores_list:
        return
    all_keys = set()
    for s in scores_list:
        all_keys.update(s.keys())
    averages: Dict[str, float] = {}
    for key in sorted(all_keys):
        if key.endswith("_detail"):
            continue
        vals = [s[key] for s in scores_list if s.get(key) is not None and isinstance(s.get(key), (int, float))]
        if not vals:
            continue
        dec = 4 if key in _METRICS_4DEC else 2
        averages[key] = round(sum(vals) / len(vals), dec)
    data["averages"] = averages
    data["num_cases"] = len(scores_list)


def _find_completed_cases(model_name: str, all_ids: List[str]) -> set:
    path = _get_results_path(model_name)
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    return {r["case_id"] for r in data.get("per_case", []) if r.get("case_id") and all(v is not None for v in r.get("scores", {}).values())}


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def run_test(case_id: Optional[str] = None) -> None:
    if case_id:
        case = load_random_case(case_id=case_id)
        print(f"\n[Test mode] Specified case: {case_id}")
    else:
        case = load_random_case()
        print(f"\n[Test mode] Random case: {case['id']}")
    result = run_full_interview(case=case)
    _print_result(result)


def _print_result(result: Dict[str, Any]) -> None:
    metrics = MetricsExtractor.from_interview_result(result)
    print("\n" + "=" * 70)
    print(" " * 25 + "Evaluation Results")
    print("=" * 70)
    print(f"Case ID: {result['case_id']}")
    print(f"Model:   {result['model_name']}")
    if metrics.p1_overall_coverage is not None:
        print(f"\nPhase 1 — Overall coverage: {metrics.p1_overall_coverage:.2f}%")
    _subj("Communication Empathy", (result.get("phase1", {}).get("evaluation", {}) or {}).get("empathy_evaluation"))
    _subj("Professionalism", (result.get("phase1", {}).get("evaluation", {}) or {}).get("profession_evaluation"))
    if metrics.p2_precision is not None:
        print(f"\nPhase 2 — P={metrics.p2_precision:.4f} R={metrics.p2_recall:.4f} F1={metrics.p2_f1:.4f}")
    if metrics.p3_total_percentage is not None:
        print(f"Phase 3 — Total: {metrics.p3_total_percentage:.2f}%")
    _subj("Clinical Note Quality", (result.get("phase3", {}).get("evaluation", {}) or {}).get("clinical_note_subjective"))
    print(f"\nPhase 4 — Disorder F1={metrics.p4_disorder_f1 or 0:.4f}  Category F1={metrics.p4_category_f1 or 0:.4f}  Exact Match={metrics.p4_exact_match or 0}")
    _subj("Diagnostic Rigor", (result.get("phase4", {}).get("evaluation", {}) or {}).get("diagnostic_rigor_subjective"))
    _subj("Treatment Appropriateness", (result.get("phase5", {}).get("evaluation", {}) or {}).get("treatment_subjective"))
    print("=" * 70)


def _subj(label: str, subj: Optional[Dict[str, Any]]) -> None:
    if subj and subj.get("score") is not None:
        print(f"  [{label}]: {subj['score']}/5  (individual: {subj.get('scores', [])})")


def run_eval() -> None:
    all_ids = [c["id"] for c in load_all_cases() if "id" in c]
    model_name = settings.doctor.model
    completed = _find_completed_cases(model_name, all_ids)
    pending = [cid for cid in all_ids if cid not in completed]
    if not pending:
        print("All cases already completed.")
        return
    new = 0
    for cid in tqdm(pending, desc="Evaluating", unit="case"):
        try:
            run_full_interview(case=load_random_case(case_id=cid))
            new += 1
        except Exception:
            logger.exception("Case %s failed", cid)
    print(f"\nDone — {new} new, {len(completed)} skipped")


def run_batch(concurrency: int = 32) -> None:
    all_ids = [c["id"] for c in load_all_cases() if "id" in c]
    model_name = settings.doctor.model
    completed = _find_completed_cases(model_name, all_ids)
    pending = [cid for cid in all_ids if cid not in completed]
    if not pending:
        print("All cases already completed.")
        return

    total = len(pending)
    pbar = tqdm(total=total, desc="Batch", unit="case")

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        running: set = set()
        idx = 0
        submit_counter = 0

        def _submit(cid: str) -> None:
            nonlocal submit_counter
            use_b = (submit_counter % 2 == 1)
            submit_counter += 1
            fut = executor.submit(_run_one, cid, use_b)
            fut._mh_cid = cid  # type: ignore[attr-defined]
            running.add(fut)
            fut.add_done_callback(_on_done)

        def _on_done(fut) -> None:
            nonlocal idx
            try:
                fut.result()
            except Exception:
                logger.exception("Case %s failed", getattr(fut, "_mh_cid", "unknown"))
            pbar.update(1)
            if idx < total:
                _submit(pending[idx])
                idx += 1

        for _ in range(min(concurrency, total)):
            _submit(pending[idx])
            idx += 1

        while running:
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            running.difference_update(done)
    pbar.close()

    path = _get_results_path(model_name)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        _print_batch_summary(data)


def _run_one(cid: str, use_backup: bool) -> None:
    case = load_random_case(case_id=cid)
    run_full_interview(case=case, patient_backup=use_backup, instrument_backup=use_backup)


def _print_batch_summary(data: Dict[str, Any]) -> None:
    per_case = data.get("per_case", [])
    n = len(per_case)
    if n == 0:
        return
    print(f"\n{'=' * 70}")
    print(f"  Average Results — {n} case(s)")
    print(f"{'=' * 70}")
    for key in sorted(data.get("averages", {})):
        dec = 4 if key in _METRICS_4DEC else 2
        print(f"  {key.replace('p', 'P').replace('_', ' ')}: {data['averages'][key]:.{dec}f}")
    print(f"{'=' * 70}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="MentalHospital — LLM-based psychiatric interview simulation")
    parser.add_argument("--mode", choices=["test", "eval", "batch"], default="test")
    parser.add_argument("--case-id", type=str, default=None)
    parser.add_argument("--concurrency", type=int, default=32)
    args = parser.parse_args()

    try:
        if args.mode == "test":
            run_test(case_id=args.case_id)
        elif args.mode == "eval":
            run_eval()
        elif args.mode == "batch":
            run_batch(concurrency=args.concurrency)
        print("\nDone.")
    except Exception:
        logger.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()
