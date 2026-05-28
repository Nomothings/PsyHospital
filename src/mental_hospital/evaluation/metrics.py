"""Unified metrics — the single source of truth for extracting flat,
comparable scores from raw interview + evaluation results."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Dict, Optional

from mental_hospital.config.constants import METRICS_4_DECIMAL


@dataclass
class CaseMetrics:
    """Standardised flat metrics for a single case.  All fields optional."""

    case_id: str = ""

    # Phase 1 — coverage
    p1_cc_coverage: Optional[float] = None
    p1_ms_coverage: Optional[float] = None
    p1_overall_coverage: Optional[float] = None
    p1_empathy: Optional[float] = None
    p1_empathy_detail: Optional[Dict[str, Any]] = None
    p1_profession: Optional[float] = None
    p1_profession_detail: Optional[Dict[str, Any]] = None

    # Phase 2 — examination
    p2_precision: Optional[float] = None
    p2_recall: Optional[float] = None
    p2_f1: Optional[float] = None
    p2_jaccard: Optional[float] = None

    # Phase 3 — clinical note
    p3_total_percentage: Optional[float] = None
    p3_subjective: Optional[float] = None
    p3_subjective_detail: Optional[Dict[str, Any]] = None

    # Phase 4 — diagnosis (disorder-level)
    p4_disorder_precision: Optional[float] = None
    p4_disorder_recall: Optional[float] = None
    p4_disorder_f1: Optional[float] = None
    p4_disorder_jaccard: Optional[float] = None
    # Phase 4 — diagnosis (category-level)
    p4_category_precision: Optional[float] = None
    p4_category_recall: Optional[float] = None
    p4_category_f1: Optional[float] = None
    p4_category_jaccard: Optional[float] = None
    # Phase 4 — ranking
    p4_exact_match: Optional[int] = None
    p4_hit3: Optional[int] = None
    p4_rr: Optional[float] = None
    p4_poa: Optional[float] = None
    p4_ndcg: Optional[float] = None
    p4_subjective: Optional[float] = None
    p4_subjective_detail: Optional[Dict[str, Any]] = None

    # Phase 5 — treatment
    p5_subjective: Optional[float] = None
    p5_subjective_detail: Optional[Dict[str, Any]] = None
    p5_length: Optional[int] = None

    def to_dict(self, *, include_details: bool = False) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for f in fields(self):
            if not include_details and f.name.endswith("_detail"):
                continue
            result[f.name] = getattr(self, f.name)
        return result

    @staticmethod
    def decimal_places(key: str) -> int:
        return 4 if key in METRICS_4_DECIMAL else 2


class MetricsExtractor:
    """Single source of truth for building ``CaseMetrics`` from raw results."""

    @staticmethod
    def from_interview_result(result: Dict[str, Any]) -> CaseMetrics:
        m = CaseMetrics(case_id=result.get("case_id", ""))

        # Phase 1
        p1e = result.get("phase1", {}).get("evaluation", {})
        cov = p1e.get("coverage_stats", {})
        m.p1_cc_coverage = cov.get("chief_complaint_coverage")
        m.p1_ms_coverage = cov.get("mental_status_coverage")
        m.p1_overall_coverage = cov.get("overall_coverage")
        if emp := p1e.get("empathy_evaluation"):
            m.p1_empathy = emp.get("score")
            m.p1_empathy_detail = _extract_individual(emp)
        if pro := p1e.get("profession_evaluation"):
            m.p1_profession = pro.get("score")
            m.p1_profession_detail = _extract_individual(pro)

        # Phase 2
        p2e = result.get("phase2", {}).get("evaluation", {}).get("metrics", {})
        m.p2_precision = p2e.get("precision")
        m.p2_recall = p2e.get("recall")
        m.p2_f1 = p2e.get("f1")
        m.p2_jaccard = p2e.get("jaccard")

        # Phase 3
        p3e = result.get("phase3", {}).get("evaluation", {})
        m.p3_total_percentage = p3e.get("total_percentage")
        if subj3 := p3e.get("clinical_note_subjective"):
            m.p3_subjective = subj3.get("score")
            m.p3_subjective_detail = _extract_individual(subj3)

        # Phase 4
        p4e = result.get("phase4", {}).get("evaluation", {})
        for prefix, src in [("p4_disorder", "disorder_metrics"), ("p4_category", "category_metrics")]:
            sm = p4e.get(src, {})
            setattr(m, f"{prefix}_precision", sm.get("precision"))
            setattr(m, f"{prefix}_recall", sm.get("recall"))
            setattr(m, f"{prefix}_f1", sm.get("f1"))
            setattr(m, f"{prefix}_jaccard", sm.get("jaccard"))
        pm = p4e.get("primary_metrics", {})
        m.p4_exact_match = pm.get("primary_exact_match")
        m.p4_hit3 = pm.get("primary_hit_at_k")
        m.p4_rr = pm.get("primary_reciprocal_rank")
        rm = p4e.get("ranking_metrics", {})
        m.p4_poa = rm.get("poa")
        m.p4_ndcg = rm.get("ndcg")
        if ds := p4e.get("diagnostic_rigor_subjective"):
            m.p4_subjective = ds.get("score")
            m.p4_subjective_detail = _extract_individual(ds)

        # Phase 5
        p5e = result.get("phase5", {}).get("evaluation", {})
        if ts := p5e.get("treatment_subjective"):
            m.p5_subjective = ts.get("score")
            m.p5_subjective_detail = _extract_individual(ts)
        tp = result.get("phase5", {}).get("treatment_plan", "")
        if tp:
            m.p5_length = len(tp)

        return m


def _extract_individual(subj_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not subj_result:
        return None
    individual = subj_result.get("individual_results", [])
    if not individual:
        return {"evaluator_models": {}, "average": subj_result.get("score")}
    model_scores = {f"evaluator_{item.get('evaluator_id')}": item.get("score") for item in individual}
    return {"evaluator_models": model_scores, "average": subj_result.get("score"), "parsed_count": subj_result.get("parsed_count", 0)}
