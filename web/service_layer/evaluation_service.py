"""
Evaluation service module — phase evaluation logic extracted from app.py.

Rewired to use the new ``mental_hospital`` package (Scorer, evaluators, rubrics)
while keeping the original API response format for frontend compatibility.
"""
from __future__ import annotations

import json
import logging
import re

from config import DATA_DIR, PHASE_NAMES, API_PHASE_NAMES, TREATMENT_CATEGORIES
from utils.text_utils import format_conversation, extract_keywords, text_overlap

# New mental_hospital imports
from mental_hospital.evaluation.scorer import Scorer
from mental_hospital.evaluation.history_evaluator import calculate_coverage
from mental_hospital.evaluation.examination_evaluator import calculate_metrics as _exam_calculate_metrics
from mental_hospital.evaluation.diagnosis_evaluator import calculate_set_metrics
from mental_hospital.prompts.rubrics import (
    COMMUNICATION_EMPATHY,
    INTERVIEWING_PROFESSIONALISM,
    CLINICAL_NOTE_QUALITY,
    DIAGNOSTIC_RIGOR,
    TREATMENT_APPROPRIATENESS,
)

logger = logging.getLogger(__name__)


# ============================================================
# Adapter — maps new Scorer.evaluate_multi() output to old
#           SubjectiveEvaluator format for frontend compat
# ============================================================

def _adapt_subjective_result(new_result: dict) -> dict:
    """Convert ``Scorer.evaluate_multi()`` output to the shape the frontend expects."""
    analyses = new_result.get("analyses", [])
    full_analysis = "\n\n".join(analyses)
    return {
        "score": new_result.get("score"),
        "scores": new_result.get("scores", []),
        "full_analysis": full_analysis,
        "raw_response": full_analysis,
        "score_parsed": new_result.get("parsed_count", 0) > 0,
        "parsed_count": new_result.get("parsed_count", 0),
        "individual_results": new_result.get("individual_results", []),
    }


# ============================================================
# Common utilities
# ============================================================

def _is_empty_result(value) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return not text or text.upper() == "NONE" or text in {"No result", "N/A"}


def load_ground_truth(case_id: str) -> dict | None:
    """Load ground truth diagnosis for specified case from ground_truth.jsonl"""
    gt_file = DATA_DIR / "ground_truth.jsonl"
    if not gt_file.exists():
        return None
    try:
        with open(gt_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("id") == case_id:
                            return data
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.warning(f"Failed to read ground truth: {e}")
    return None


# ============================================================
# Phase 1 evaluation
# ============================================================

def evaluate_phase1_live(case_id: str, body: dict, case_service=None) -> dict:
    """Phase 1 live evaluation — uses new Scorer with rubric constants."""
    messages = body.get("messages", [])
    conversation_stats = {
        "total_turns": len([m for m in messages if m["role"] == "patient"]),
        "doctor_turns": len([m for m in messages if m["role"] == "doctor"]),
        "patient_turns": len([m for m in messages if m["role"] == "patient"]),
        "conversation_length": len(messages),
    }

    conversation_text = format_conversation(messages)

    # ---- Coverage statistics (via new calculate_coverage) ----
    coverage_stats = None
    if case_service:
        try:
            case_data = case_service.get_case_for_interview(case_id)
            if case_data:
                cc_all = case_data.get("chiefComplaint", [])
                ms_all = case_data.get("mentalStatus", [])
                conv_lower = conversation_text.lower()
                cc_used = [item for item in cc_all if item.strip() and item.strip().lower() in conv_lower]
                ms_used = [item for item in ms_all if item.strip() and item.strip().lower() in conv_lower]
                coverage_stats = calculate_coverage(cc_all, ms_all, cc_used, ms_used)
        except Exception as e:
            logger.warning(f"Coverage statistics failed: {e}")

    empathy_result = None
    profession_result = None

    try:
        empathy_result = Scorer.evaluate_multi(
            rubric_content=COMMUNICATION_EMPATHY,
            test_context=conversation_text,
        )
    except Exception as e:
        logger.warning(f"Empathy evaluation failed: {e}")

    try:
        profession_result = Scorer.evaluate_multi(
            rubric_content=INTERVIEWING_PROFESSIONALISM,
            test_context=conversation_text,
        )
    except Exception as e:
        logger.warning(f"Professionalism evaluation failed: {e}")

    result = {
        "phase": 1,
        "case_id": case_id,
        "phase_name": PHASE_NAMES[1],
        "conversation_stats": conversation_stats,
    }

    if coverage_stats:
        result["coverage_stats"] = coverage_stats

    if empathy_result:
        adapted = _adapt_subjective_result(empathy_result)
        empathy_analysis = adapted["full_analysis"]
        result["empathy_evaluation"] = {
            **adapted,
            "empathy_level": adapted.get("score"),
            "why_this_level": empathy_analysis,
            "evidence": "",
            "level_count": 5,
            "raw_response": empathy_analysis,
        }

    if profession_result:
        adapted = _adapt_subjective_result(profession_result)
        profession_analysis = adapted["full_analysis"]
        result["profession_evaluation"] = {
            **adapted,
            "profession_level": adapted.get("score"),
            "total_score": adapted.get("score"),
            "average_score": adapted.get("score"),
            "question_count": 1,
            "raw_response": profession_analysis,
            "parsed_scores": adapted.get("scores", []),
            "evidence_verification": {},
        }

    return result


def evaluate_phase2_live(case_id: str, body: dict, case_service) -> dict:
    """Phase 2 live evaluation using the formal exam selection metric (new package)."""
    exam_results = body.get("exam_results", {})
    if not isinstance(exam_results, dict):
        exam_results = {}

    total_examined = len(exam_results)
    positive_count = sum(1 for value in exam_results.values() if not _is_empty_result(value))
    negative_count = sum(1 for value in exam_results.values() if _is_empty_result(value))

    metric_result = {}
    try:
        case_data = case_service.get_case_for_interview(case_id)
        if case_data:
            metric_result = _exam_calculate_metrics(
                response=exam_results,
                examination_query=list(exam_results.keys()),
                auxiliary_examinations=case_data.get("auxiliaryExamination", {}) or {},
            )
    except Exception as e:
        logger.warning(f"Phase 2 core evaluator call failed: {e}")

    metrics = metric_result.get("metrics") if metric_result else None
    return {
        "phase": 2,
        "case_id": case_id,
        "phase_name": PHASE_NAMES[2],
        "exam_stats": {
            "total_examined": total_examined,
            "positive_results": positive_count,
            "negative_results": negative_count,
        },
        "counts": metric_result.get("counts"),
        "metrics": metrics,
        "exam_selection_metrics": metrics,
        "warnings": metric_result.get("warnings", []),
    }


def evaluate_phase2_accuracy(case_id: str, exam_results: dict, case_service) -> float:
    """Phase 2 examination selection accuracy, returned as Jaccard (new package)."""
    if not isinstance(exam_results, dict):
        exam_results = {}

    try:
        case_data = case_service.get_case_for_interview(case_id)
        if not case_data:
            return 0.0
        result = _exam_calculate_metrics(
            response=exam_results,
            examination_query=list(exam_results.keys()),
            auxiliary_examinations=case_data.get("auxiliaryExamination", {}) or {},
        )
        return round(result.get("metrics", {}).get("jaccard", 0.0), 4)
    except Exception as e:
        logger.warning(f"Phase 2 accuracy calculation failed: {e}")
        return 0.0


# ============================================================
# Phase 3 evaluation — Case writing
# ============================================================

def evaluate_case_writing(case_id: str, case_form: dict, case_service) -> dict:
    """Case writing structural scoring

    Args:
        case_id: Case ID
        case_form: Case record form data
        case_service: Case service instance
    """
    case_data = case_service.get_case_for_interview(case_id)
    if not case_data:
        return {
            "total_percentage": 0,
            "total_score": 0,
            "dimensions": {},
            "warning": "Unable to retrieve case data",
        }

    return _evaluate_case_writing_fallback(case_id, case_form, case_data)


def _evaluate_case_writing_fallback(case_id: str, case_form: dict, case_data: dict) -> dict:
    """Fallback when LLM evaluation fails: simple keyword matching scoring"""
    if not isinstance(case_form, dict):
        case_form = {}
    if not isinstance(case_data, dict):
        case_data = {}

    sections = {}

    # Chief complaint
    user_chief = (case_form.get("chiefComplaint") or "").strip()
    gold_chief = " ".join(case_data.get("chiefComplaint", []))
    if user_chief and gold_chief:
        gold_keywords = extract_keywords(gold_chief)
        if gold_keywords:
            matched = sum(1 for kw in gold_keywords if kw in user_chief)
            score = round(matched / len(gold_keywords), 2)
            detail = f"Keyword coverage {matched}/{len(gold_keywords)}"
        else:
            score = 0.5
            detail = "Chief complaint filled; no comparable keywords extracted from standard answer"
        sections["chief_complaint"] = {
            "section_name": "Chief Complaint",
            "score": score,
            "detail": detail,
        }
    else:
        sections["chief_complaint"] = {"section_name": "Chief Complaint", "score": 0, "detail": "Not filled"}

    # Physical examination
    user_physical = (case_form.get("physicalExam") or "").strip()
    gold_physical = case_data.get("physicalExamination", "")
    if user_physical and gold_physical:
        vital_signs = ["T", "P", "R", "BP", "体温", "脉搏", "呼吸", "血压"]
        found = sum(1 for v in vital_signs if v in user_physical)
        total = sum(1 for v in vital_signs if v in gold_physical)
        score = round(found / max(total, 1), 2) if total > 0 else 0.3
        sections["physical_examination"] = {
            "section_name": "Physical Examination",
            "score": score,
            "detail": f"Vital signs coverage {found}/{total}",
        }
    else:
        sections["physical_examination"] = {"section_name": "Physical Examination", "score": 0, "detail": "Not filled"}

    # Mental examination
    user_mental = (case_form.get("mentalExam") or "").strip()
    gold_mental = " ".join(case_data.get("mentalStatus", []))
    if user_mental and gold_mental:
        score = round(text_overlap(user_mental, gold_mental), 2)
        sections["mental_examination"] = {
            "section_name": "Mental Examination",
            "score": score,
            "detail": f"Text similarity {score:.0%}",
        }
    else:
        sections["mental_examination"] = {"section_name": "Mental Examination", "score": 0, "detail": "Not filled"}

    # Past history and family history
    user_past = (case_form.get("pastHistory") or "").strip()
    user_family = (case_form.get("familyHistory") or "").strip()
    past_score = 0.5 if user_past else 0
    family_score = 0.5 if user_family else 0
    sections["past_family_history"] = {
        "section_name": "Past & Family History",
        "score": round((past_score + family_score) / 2, 2),
        "detail": f"Past history {'filled' if user_past else 'not filled'}, Family history {'filled' if user_family else 'not filled'}",
    }

    total_score = round(sum(s["score"] for s in sections.values()) / len(sections), 2)

    return {
        "total_percentage": round(total_score * 100, 2),
        "total_score": total_score,
        "dimensions": sections,
        "fallback": True,
    }


def format_case_writing_dimensions(dimensions: dict) -> dict:
    """Format dimensions returned by LLMEvaluator for frontend display"""
    result = {}
    name_map = {
        "chief_complaint": "Chief Complaint",
        "physical_examination": "Physical Examination",
        "mental_examination": "Mental Examination",
        "past_family_history": "Past & Family History",
    }

    for key, dim_data in dimensions.items():
        percentage = dim_data.get("percentage", 0)
        weighted = dim_data.get("weighted_score", 0)
        coverage_pct = dim_data.get("coverage_percentage", 0)
        accuracy_pct = dim_data.get("accuracy_percentage", 0)

        scoring_results = dim_data.get("scoring_results", [])
        total_items = len(scoring_results)
        scored_items = sum(
            1 for r in scoring_results
            if r.get("coverage_score") not in ("skip", None)
            and r.get("accuracy_score") not in ("skip", None)
        )

        result[key] = {
            "section_name": name_map.get(key, key),
            "score": round(percentage / 100, 2) if percentage else 0,
            "percentage": percentage,
            "coverage_percentage": coverage_pct,
            "accuracy_percentage": accuracy_pct,
            "weighted_score": weighted,
            "detail": f"Coverage {coverage_pct:.0f}%, Accuracy {accuracy_pct:.0f}%, {scored_items}/{total_items} scoring items valid",
            "scoring_results": scoring_results,
        }

    return result


# ============================================================
# Phase 3 evaluation — Diagnosis
# ============================================================

def evaluate_diagnosis_core(case_id: str, diagnosis: dict) -> dict:
    """Evaluate diagnosis using the new mental_hospital diagnosis evaluator.

    - Disease category: uses diagnosis_evaluator.calculate_set_metrics
    - Specific disease: compares with realDisorder, calculates Recall
    - Diagnostic reasoning: checks if filled + whether it contains key terms
    """

    diagnoses_list = diagnosis.get("diagnoses", [])
    reason = (diagnosis.get("reason") or "").strip()

    if not diagnoses_list:
        single_category = diagnosis.get("category", "")
        disease_text = diagnosis.get("disease", "") or ""
        split_diseases = [
            item.strip()
            for item in re.split(r"[|,，、;；]+", disease_text)
            if item and item.strip()
        ]
        if single_category or split_diseases:
            diagnoses_list = [{
                "category": single_category,
                "diseases": split_diseases,
            }]

    user_categories = []
    user_diseases = set()
    for cat in diagnoses_list:
        cat_name = cat.get("category", "")
        if cat_name:
            user_categories.append(cat_name)
        for dis in cat.get("diseases", []):
            if dis:
                user_diseases.add(dis.strip())

    # Load true categories directly from case data (replaces old load_real_categories)
    true_categories: list = []
    try:
        from mental_hospital.data.loader import load_case_by_id
        case = load_case_by_id(case_id)
        if case:
            true_categories = case.get("realCategory", [])
    except Exception:
        pass
    if true_categories is None:
        true_categories = []

    category_metrics = calculate_set_metrics(user_categories, true_categories)

    gt = load_ground_truth(case_id)
    gt_disorders = set()
    if gt:
        gt_disorders = set(gt.get("realDisorder", []))

    matched = set()
    if gt_disorders and user_diseases:
        matched = user_diseases & gt_disorders
        disorder_recall = len(matched) / len(gt_disorders)
        false_positives = user_diseases - gt_disorders
        if false_positives and disorder_recall > 0:
            penalty = len(false_positives) / len(user_diseases)
            disorder_recall = round(disorder_recall * (1 - penalty * 0.5), 4)
    elif gt_disorders:
        disorder_recall = 0.0
    else:
        disorder_recall = 1.0

    reason_score = 0.0
    reason_detail = ""
    if not gt_disorders:
        # gt has no diseases, full score if reason is filled
        if reason:
            reason_score = 1.0
            reason_detail = "No diseases in ground truth, reason filled"
        else:
            reason_detail = "Not filled"
    elif reason:
        reason_score = 0.6
        gt_terms = set()
        for dis in gt_disorders:
            parts = dis.split(" ", 1)
            if len(parts) > 1:
                gt_terms.add(parts[1].lower())
            gt_terms.add(parts[0].lower())
        reason_lower = reason.lower()
        matched_terms = sum(1 for t in gt_terms if t in reason_lower)
        if matched_terms > 0:
            reason_score = min(1.0, 0.6 + matched_terms * 0.1)
            reason_detail = f"Contains {matched_terms} key diagnostic terms"
        else:
            reason_detail = "Filled but does not contain key terms"
    else:
        reason_detail = "Not filled"

    total_score = round(
        category_metrics.get("recall", 0) * 0.35
        + disorder_recall * 0.45
        + reason_score * 0.2,
        2,
    )

    return {
        "total_score": total_score,
        "disease_type": {
            "score": category_metrics.get("recall", 0),
            "metrics": category_metrics,
            "predicted": user_categories,
            "true": true_categories,
            "detail": f"Recall {category_metrics.get('recall', 0):.0%}, Precision {category_metrics.get('precision', 0):.0%}, F1 {category_metrics.get('f1', 0):.0%}",
        },
        "diagnostic_correctness": {
            "score": disorder_recall,
            "predicted": sorted(user_diseases),
            "true": sorted(gt_disorders),
            "matched": sorted(user_diseases & gt_disorders),
            "detail": f"Specific disease Recall {disorder_recall:.0%}" + (f" ({len(user_diseases & gt_disorders)}/{len(gt_disorders)} items matched)" if gt_disorders else ""),
        },
        "diagnostic_reasoning": {
            "score": reason_score,
            "submitted_reason": reason,
            "detail": reason_detail,
        },
        "comprehensive": {
            "score": total_score,
            "detail": "Category weight 35%, Correctness 45%, Reasoning 20%",
        },
    }


# ============================================================
# Phase 3/4 context building (for subjective evaluation)
# ============================================================

def build_phase3_note_subjective_context(case_form: dict) -> str:
    if not case_form:
        return ""

    ordered_sections = [
        ("Name", case_form.get("name")),
        ("Age", case_form.get("age")),
        ("Gender", case_form.get("gender")),
        ("Chief Complaint", case_form.get("chiefComplaint")),
        ("Past History", case_form.get("pastHistory")),
        ("Family History", case_form.get("familyHistory")),
        ("Physical Examination", case_form.get("physicalExam")),
        ("Mental Examination", case_form.get("mentalExam")),
        ("Auxiliary Examination", case_form.get("auxiliaryExam")),
    ]
    lines = [
        f"{label}: {str(value).strip()}"
        for label, value in ordered_sections
        if value and str(value).strip()
    ]
    return "\n".join(lines)


def build_phase3_diagnosis_subjective_context(diagnosis: dict) -> str:
    if not diagnosis:
        return ""

    diagnoses_list = diagnosis.get("diagnoses", [])
    if not diagnoses_list:
        single_category = diagnosis.get("category", "")
        disease_text = diagnosis.get("disease", "") or ""
        split_diseases = [
            item.strip()
            for item in re.split(r"[|,，、;；]+", disease_text)
            if item and item.strip()
        ]
        if single_category or split_diseases:
            diagnoses_list = [{
                "category": single_category,
                "diseases": split_diseases,
            }]

    lines = []
    for index, item in enumerate(diagnoses_list, 1):
        category = str(item.get("category") or "").strip()
        diseases = [
            str(disease).strip()
            for disease in (item.get("diseases") or [])
            if disease and str(disease).strip()
        ]
        if category:
            lines.append(f"Diagnosis Category {index}: {category}")
        if diseases:
            lines.append(f"Diagnosis Details {index}: {', '.join(diseases)}")

    reason = str(diagnosis.get("reason") or "").strip()
    if reason:
        lines.append(f"Diagnostic Reasoning: {reason}")
    return "\n".join(lines)


def build_phase4_standard_treatment(case_id: str, case_service) -> list:
    """Build Phase 4 standard treatment plan (from ground truth or case data)

    Args:
        case_id: Case ID
        case_service: Case service instance
    """
    standard_items = []
    ground_truth = load_ground_truth(case_id) or {}
    real_formulation = ground_truth.get("realFormulation") or {}

    medication_history = real_formulation.get("medicationHistory") or []
    if isinstance(medication_history, list):
        for item in medication_history:
            text = str(item).strip()
            if text:
                standard_items.append(text)

    if not standard_items:
        case_data = case_service.get_case_for_interview(case_id) or {}
        fallback_history = case_data.get("medicationHistory") or []
        if isinstance(fallback_history, list):
            for item in fallback_history:
                text = str(item).strip()
                if text:
                    standard_items.append(text)

    return standard_items


# ============================================================
# Phase 3 comprehensive evaluation
# ============================================================

def evaluate_phase3_live(case_id: str, body: dict, case_service) -> dict:
    """Phase 3 live evaluation

    Args:
        case_id: Case ID
        body: Request body
        case_service: Case service instance
    """
    if not isinstance(body, dict):
        body = {}

    case_form = body.get("case_form", {})
    if not isinstance(case_form, dict):
        case_form = {}

    diagnosis = body.get("diagnosis", {})
    if not isinstance(diagnosis, dict):
        diagnosis = {}

    case_writing_eval = evaluate_case_writing(case_id, case_form, case_service)
    diagnosis_eval = evaluate_diagnosis_core(case_id, diagnosis)

    clinical_note_subjective = None
    diagnostic_rigor_subjective = None

    try:
        note_context = build_phase3_note_subjective_context(case_form)
        if note_context:
            clinical_note_subjective = Scorer.evaluate_multi(
                rubric_content=CLINICAL_NOTE_QUALITY,
                test_context=note_context,
            )
    except Exception as e:
        logger.warning(f"Phase 3 clinical note subjective evaluation failed: {e}")

    try:
        diagnosis_context = build_phase3_diagnosis_subjective_context(diagnosis)
        if diagnosis_context:
            diagnostic_rigor_subjective = Scorer.evaluate_multi(
                rubric_content=DIAGNOSTIC_RIGOR,
                test_context=diagnosis_context,
            )
    except Exception as e:
        logger.warning(f"Phase 3 diagnostic rigor subjective evaluation failed: {e}")

    writing_score = case_writing_eval.get("total_percentage", 0) / 100.0
    diagnosis_score = diagnosis_eval.get("total_score", 0)
    overall_score = round((writing_score * 0.5 + diagnosis_score * 0.5), 2)

    return {
        "phase": 3,
        "case_id": case_id,
        "phase_name": PHASE_NAMES[3],
        "overall_score": overall_score,
        "case_writing": case_writing_eval,
        "diagnosis": diagnosis_eval,
        "clinical_note_subjective": clinical_note_subjective,
        "diagnostic_rigor_subjective": diagnostic_rigor_subjective,
    }


# ============================================================
# Phase 4 comprehensive evaluation
# ============================================================

def evaluate_phase4_live(case_id: str, body: dict, case_service) -> dict:
    """Phase 4 treatment evaluation

    Args:
        case_id: Case ID
        body: Request body
        case_service: Case service instance
    """
    treatment = body.get("treatment", {})
    filled_count = sum(
        1 for value in treatment.values()
        if value and value not in ("无", "None") and str(value).strip()
    )
    empty_count = len(TREATMENT_CATEGORIES) - filled_count

    treatment_plan_lines = []
    for category in TREATMENT_CATEGORIES:
        value = str(treatment.get(category) or "").strip()
        if value and value not in ("无", "None"):
            treatment_plan_lines.append(f"{category}: {value}")
    treatment_plan = "\n".join(treatment_plan_lines)

    treatment_subjective = None
    if treatment_plan:
        try:
            treatment_subjective = Scorer.evaluate_multi(
                rubric_content=TREATMENT_APPROPRIATENESS,
                test_context=treatment_plan,
            )
        except Exception as e:
            logger.warning(f"Phase 4 treatment subjective evaluation failed: {e}")

    standard_treatment = build_phase4_standard_treatment(case_id, case_service)

    return {
        "phase": 4,
        "case_id": case_id,
        "phase_name": API_PHASE_NAMES.get(4, "Treatment Planning"),
        "treatment_stats": {
            "filled_categories": filled_count,
            "empty_categories": empty_count,
            "total_categories": len(TREATMENT_CATEGORIES),
            "details": treatment,
        },
        "treatment_plan": treatment_plan,
        "standard_treatment": standard_treatment,
        "treatment_subjective": treatment_subjective,
    }



# ============================================================
# Evaluation dispatcher
# ============================================================

def evaluate_phase(phase: int, case_id: str, body: dict, case_service) -> dict:
    """Unified evaluation entry point

    Args:
        phase: Phase number (1-4)
        case_id: Case ID
        body: Request body
        case_service: Case service instance

    Returns:
        Evaluation result dictionary

    Raises:
        ValueError: Unsupported phase number
    """
    if not isinstance(body, dict):
        body = {}

    evaluators = {
        1: lambda: evaluate_phase1_live(case_id, body, case_service),
        2: lambda: evaluate_phase2_live(case_id, body, case_service),
        3: lambda: evaluate_phase3_live(case_id, body, case_service),
        4: lambda: evaluate_phase4_live(case_id, body, case_service),
    }
    fn = evaluators.get(phase)
    if fn is None:
        raise ValueError(f"Unsupported phase number: {phase}")
    return fn()
