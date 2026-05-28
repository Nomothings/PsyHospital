"""Phase 4 evaluation: diagnosis set-matching, ranking, and subjective rigor."""

from __future__ import annotations

import json
import logging
import math
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from mental_hospital.data.loader import CASES_FILE, load_mapping
from mental_hospital.data.output import get_phase_output_file, save_evaluation_result
from mental_hospital.evaluation.scorer import Scorer
from mental_hospital.prompts.rubrics import DIAGNOSTIC_RIGOR

logger = logging.getLogger(__name__)


def calculate_set_metrics(predicted: List[str], gold: List[str]) -> Dict[str, float]:
    p_set, g_set = set(predicted), set(gold)
    if len(p_set) == 0 and len(g_set) == 0:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "jaccard": 1.0}
    if len(p_set) == 0 or len(g_set) == 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "jaccard": 0.0}
    inter, union = p_set & g_set, p_set | g_set
    prec, rec = len(inter) / len(p_set), len(inter) / len(g_set)
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return {"precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4), "jaccard": round(len(inter) / len(union), 4)}


def calculate_primary_metrics(predicted: List[str], gold: List[str], k: int = 3) -> Dict[str, Any]:
    if len(gold) == 0:
        return {"primary_exact_match": 0, "primary_hit_at_k": 0, "primary_reciprocal_rank": 0.0}
    primary = gold[0]
    exact = 1 if len(predicted) > 0 and predicted[0] == primary else 0
    hit = 1 if primary in predicted[:k] else 0
    rr = 0.0
    for i, pred in enumerate(predicted):
        if pred == primary:
            rr = 1.0 / (i + 1)
            break
    return {"primary_exact_match": exact, "primary_hit_at_k": hit, "primary_reciprocal_rank": round(rr, 4)}


def calculate_poa(predicted: List[str], gold: List[str]) -> Optional[float]:
    common = list(set(predicted) & set(gold))
    if len(common) < 2:
        return None
    pred_order = {item: i for i, item in enumerate(predicted) if item in common}
    gold_order = {item: i for i, item in enumerate(gold) if item in common}
    pairs = list(combinations(common, 2))
    consistent = sum(1 for a, b in pairs if (pred_order[a] < pred_order[b]) == (gold_order[a] < gold_order[b]))
    return round(consistent / len(pairs), 4)


def calculate_ndcg(predicted: List[str], gold: List[str]) -> float:
    if len(gold) == 0:
        return 0.0
    relevance = {item: 1.0 / (i + 1) for i, item in enumerate(gold)}
    dcg = sum(relevance.get(pred, 0.0) / math.log2(i + 2) for i, pred in enumerate(predicted))
    idcg = sum((1.0 / (i + 1)) / math.log2(i + 2) for i in range(len(gold)))
    return round(dcg / idcg, 4) if idcg > 0 else 0.0


def _build_disorder_to_category(mapping: Dict[str, List[str]]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for cat, disorders in mapping.items():
        for d in disorders:
            result[d] = cat
    return result


def disorders_to_categories(disorders: List[str], mapping: Dict[str, List[str]]) -> List[str]:
    d2c = _build_disorder_to_category(mapping)
    seen: Set[str] = set()
    result: List[str] = []
    for d in disorders:
        cat = d2c.get(d)
        if cat and cat not in seen:
            seen.add(cat)
            result.append(cat)
    return result


def _load_case(case_id: str) -> Optional[Dict[str, Any]]:
    if not CASES_FILE.exists():
        return None
    with open(CASES_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("id") == case_id:
                    return data
            except json.JSONDecodeError:
                continue
    return None


def evaluate(
    model_name: Optional[str] = None, case_id: Optional[str] = None,
    output_file: Optional[Union[str, Path]] = None,
    phase4_data: Optional[Dict[str, Any]] = None,
    true_disorders: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if phase4_data is None:
        if output_file is None:
            if model_name is None or case_id is None:
                raise ValueError("Provide model_name+case_id, output_file, or phase4_data")
            output_file = get_phase_output_file(model_name, case_id, 4)
        output_file = Path(output_file)
        phase4_data = json.loads(output_file.read_text(encoding="utf-8"))
    model_name = phase4_data.get("model_name", model_name or "")
    case_id = phase4_data.get("case_id", case_id or "")
    if not model_name or not case_id:
        raise ValueError("Cannot determine model_name or case_id")

    predicted = phase4_data.get("definitive_diagnosis", [])
    status = phase4_data.get("status", "unknown")
    if true_disorders is None:
        case = _load_case(case_id)
        true_disorders = case.get("realDisorder", []) if case else []
    true_categories: List[str] = (case or {}).get("realCategory", [])

    mapping = load_mapping()
    predicted_categories = disorders_to_categories(predicted, mapping)

    disorder_metrics = calculate_set_metrics(predicted, true_disorders)
    category_metrics = calculate_set_metrics(predicted_categories, true_categories)
    primary_metrics = calculate_primary_metrics(predicted, true_disorders)
    ranking_metrics = {"poa": calculate_poa(predicted, true_disorders), "ndcg": calculate_ndcg(predicted, true_disorders)}

    eval_data: Dict[str, Any] = {
        "disorder_metrics": disorder_metrics, "category_metrics": category_metrics,
        "primary_metrics": primary_metrics, "ranking_metrics": ranking_metrics,
        "predicted_diagnoses": predicted, "true_disorders": true_disorders,
        "predicted_categories": predicted_categories, "true_categories": true_categories,
        "status": status,
    }

    diagnostic_rigor_subjective = None
    reasoning = phase4_data.get("diagnosis_reasoning", "")
    if reasoning and reasoning.strip():
        try:
            diagnostic_rigor_subjective = Scorer.evaluate_multi(rubric_content=DIAGNOSTIC_RIGOR, test_context=reasoning)
            eval_data["diagnostic_rigor_subjective"] = diagnostic_rigor_subjective
        except Exception:
            logger.exception("Phase 4 subjective evaluation failed")

    path = save_evaluation_result(model_name, case_id, 4, eval_data)
    return {"disorder_metrics": disorder_metrics, "category_metrics": category_metrics, "primary_metrics": primary_metrics, "ranking_metrics": ranking_metrics, "diagnostic_rigor_subjective": diagnostic_rigor_subjective, "predicted_diagnoses": predicted, "true_disorders": true_disorders, "predicted_categories": predicted_categories, "true_categories": true_categories, "status": status, "output_file": str(path), "model_name": model_name, "case_id": case_id}
