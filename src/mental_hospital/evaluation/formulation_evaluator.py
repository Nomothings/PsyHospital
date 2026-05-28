"""Phase 3 evaluation: clinical note quality — dimension scoring + subjective rubric.

Uses a two-stage LLM pipeline:
1. ``ClinicalNoteParser`` splits the note into four regions.
2. ``DimensionScorer`` scores each region against the gold in parallel.
3. ``Scorer`` provides an overall Clinical Note Quality rubric score.
"""

from __future__ import annotations

import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Optional, Union

from mental_hospital.data.loader import CASES_FILE
from mental_hospital.data.output import get_phase_output_file, save_evaluation_result
from mental_hospital.evaluation.scorer import Scorer
from mental_hospital.llm.client import LLMClient
from mental_hospital.llm.factory import create_evaluator_client
from mental_hospital.prompts.rubrics import CLINICAL_NOTE_QUALITY

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Phase 3 dimension rubrics (previously phase3_rubrics.py)
# ---------------------------------------------------------------------------

RUBRICS: dict = {
    "chief_complaint": {
        "rubric_name": "Chief Complaint", "weight": 0.25,
        "scoring_notes": "Score against gold. Accuracy based on clinical semantic equivalence.",
        "scoring_items": [
            {"id": 1, "element": "Onset time", "description": "When symptoms began — time point and/or duration.", "coverage_definition": {"1": "Test mentions onset time or duration.", "0": "Gold has it but test omits it.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent with gold.", "0": "Clinically inconsistent or wrong.", "skip": "Gold does not mention."}},
            {"id": 2, "element": "Main symptom", "description": "Core presenting symptom(s).", "coverage_definition": {"1": "Test includes main symptom from gold.", "0": "Gold has it but test omits it.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent (equivalents allowed).", "0": "Clinically inconsistent or wrong.", "skip": "Gold does not mention."}},
            {"id": 3, "element": "Symptom manifestation", "description": "Specific forms and characteristics.", "coverage_definition": {"1": "Test describes concrete manifestations from gold.", "0": "Gold has them but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent or wrong.", "skip": "Gold does not mention."}},
            {"id": 4, "element": "Accompanying symptoms", "description": "Other symptoms alongside the main symptom.", "coverage_definition": {"1": "Test includes accompanying symptoms from gold.", "0": "Gold has them but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent or wrong.", "skip": "Gold does not mention."}},
            {"id": 5, "element": "Course evolution", "description": "How symptoms developed and changed.", "coverage_definition": {"1": "Test mentions course evolution from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent or wrong.", "skip": "Gold does not mention."}},
            {"id": 6, "element": "Aggravating factors", "description": "Situations worsening symptoms.", "coverage_definition": {"1": "Test mentions aggravating factors from gold.", "0": "Gold has them but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent or wrong.", "skip": "Gold does not mention."}},
        ],
    },
    "physical_examination": {
        "rubric_name": "Physical Examination", "weight": 0.25,
        "scoring_notes": "Physical exam findings are objective data; accuracy requires strict match.",
        "scoring_items": [
            {"id": 1, "element": "Vital signs", "description": "T, P, R, BP.", "coverage_definition": {"1": "Test includes vitals from gold.", "0": "Gold has them but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Values consistent with gold.", "0": "Values inconsistent.", "skip": "Gold does not mention."}},
            {"id": 2, "element": "General appearance", "description": "Consciousness, development, nutrition, posture, gait, cooperation.", "coverage_definition": {"1": "Test includes general appearance from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 3, "element": "Skin / mucosa", "description": "Skin, mucosa, superficial lymph nodes.", "coverage_definition": {"1": "Test includes skin/mucosa from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 4, "element": "Head / neck", "description": "Head and neck findings.", "coverage_definition": {"1": "Test includes head/neck from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 5, "element": "Chest / heart / lungs", "description": "Chest, lung, heart findings.", "coverage_definition": {"1": "Test includes cardiopulmonary from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 6, "element": "Abdomen", "description": "Abdominal findings.", "coverage_definition": {"1": "Test includes abdomen from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 7, "element": "Extremities / neurological", "description": "Extremity and neuro reflex findings.", "coverage_definition": {"1": "Test includes extremity/neuro from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
        ],
    },
    "mental_examination": {
        "rubric_name": "Mental Status Examination", "weight": 0.25,
        "scoring_notes": "Mental exam is clinical description; use clinical semantic equivalence.",
        "scoring_items": [
            {"id": 1, "element": "Appearance / behaviour", "description": "Appearance, demeanour, behaviour, cooperation.", "coverage_definition": {"1": "Test includes appearance/behaviour from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 2, "element": "Speech", "description": "Rate, quantity, coherence.", "coverage_definition": {"1": "Test includes speech from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 3, "element": "Affect / mood", "description": "Emotional state, affective response, congruence.", "coverage_definition": {"1": "Test includes affect/mood from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 4, "element": "Perception", "description": "Hallucinations, illusions, perceptual disturbances.", "coverage_definition": {"1": "Test includes perception from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 5, "element": "Thought form", "description": "Thought association, logic.", "coverage_definition": {"1": "Test includes thought form from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 6, "element": "Thought content", "description": "Delusions, obsessions, thought-content disturbances.", "coverage_definition": {"1": "Test includes thought content from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent (equivalents allowed).", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 7, "element": "Cognition", "description": "Attention, memory, orientation, intelligence.", "coverage_definition": {"1": "Test includes cognition from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 8, "element": "Insight", "description": "Patient's awareness of own mental state.", "coverage_definition": {"1": "Test includes insight from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
        ],
    },
    "past_family_history": {
        "rubric_name": "Past and Family History", "weight": 0.25,
        "scoring_notes": "History descriptions use clinical semantic equivalence.",
        "scoring_items": [
            {"id": 1, "element": "Past medical history", "description": "Past illnesses, surgeries, trauma.", "coverage_definition": {"1": "Test includes past history from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 2, "element": "Personal history", "description": "Birth/development, education, occupation, marriage, personality.", "coverage_definition": {"1": "Test includes personal history from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 3, "element": "Family history", "description": "Family psychiatric/genetic disease history.", "coverage_definition": {"1": "Test includes family history from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
            {"id": 4, "element": "Substance use history", "description": "Psychoactive substance, smoking, alcohol.", "coverage_definition": {"1": "Test includes substance use from gold.", "0": "Gold has it but test omits.", "skip": "Gold does not mention."}, "accuracy_definition": {"1": "Clinically consistent.", "0": "Clinically inconsistent.", "skip": "Gold does not mention."}},
        ],
    },
}

# ---------------------------------------------------------------------------
# Rubric loader
# ---------------------------------------------------------------------------

class _RubricLoader:
    def __init__(self) -> None:
        self.rubrics = RUBRICS

    def get(self, rubric_type: str) -> Dict:
        return self.rubrics.get(rubric_type, {})

    def build_prompt(self, rubric_type: str) -> str:
        rubric = self.rubrics.get(rubric_type)
        if not rubric:
            return ""
        lines = [f"[{rubric['rubric_name']}]", f"Weight: {rubric['weight'] * 100:.0f}%"]
        if "scoring_notes" in rubric:
            lines.append(f"Scoring notes: {rubric['scoring_notes']}")
        lines.append("")
        for item in rubric.get("scoring_items", []):
            lines.append(f"[Item {item['id']}] {item['element']}")
            lines.append(f"Description: {item['description']}")
            lines.append("Coverage (0 or 1):")
            for k in ("1", "0", "skip"):
                lines.append(f"  {k}: {item['coverage_definition'][k]}")
            lines.append("Accuracy (0 or 1):")
            for k in ("1", "0", "skip"):
                lines.append(f"  {k}: {item['accuracy_definition'][k]}")
            lines.append("")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Clinical note parser
# ---------------------------------------------------------------------------

class _ClinicalNoteParser:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def parse(self, note_text: str) -> Dict[str, str]:
        prompt = f"""You are a professional psychiatric clinical note reviewer.
Split the following clinical note into four regions and return JSON.

Clinical note:
{note_text}

Regions: chief_complaint, physical_examination, mental_examination, past_family_history.

Return strictly this JSON format:
{{"chief_complaint": "...", "physical_examination": "...", "mental_examination": "...", "past_family_history": "..."}}"""
        try:
            raw = self._llm.chat(prompt).strip()
            for prefix in ("```json", "```"):
                if raw.startswith(prefix):
                    raw = raw[len(prefix):]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            result = json.loads(raw)
            for k in ("chief_complaint", "physical_examination", "mental_examination", "past_family_history"):
                if k not in result:
                    result[k] = ""
                elif isinstance(result[k], (dict, list)):
                    result[f"{k}_structured"] = result[k]
                    result[k] = _dict_to_text(result[k])
            return result
        except Exception as exc:
            logger.warning("ClinicalNoteParser failed: %s", exc)
            return {"chief_complaint": "", "physical_examination": "", "mental_examination": "", "past_family_history": "", "parse_error": str(exc)}


def _dict_to_text(obj, indent: int = 0) -> str:
    if isinstance(obj, dict):
        return "; ".join(f"{k}: {_dict_to_text(v, indent + 1)}" for k, v in obj.items())
    if isinstance(obj, list):
        return ", ".join(str(i) for i in obj)
    return str(obj)


# ---------------------------------------------------------------------------
# Dimension scorer
# ---------------------------------------------------------------------------

class _DimensionScorer:
    def __init__(self, llm: LLMClient, rubrics: _RubricLoader) -> None:
        self._llm = llm
        self._rubrics = rubrics
        self._lock = threading.Lock()

    def score_parallel(self, generated: Dict[str, str], gold: Dict[str, str]) -> Dict[str, Any]:
        dimensions = [("chief_complaint", "chief_complaint"), ("physical_examination", "physical_examination"), ("mental_examination", "mental_examination"), ("past_family_history", "past_family_history")]
        result: Dict[str, Any] = {"generated_record": generated, "true_record": gold, "dimensions": {}}
        total_weighted = 0.0
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(self._score_one, rk, rt, generated.get(rk, ""), gold.get(rk, "")): rk for rk, rt in dimensions}
            for fut in as_completed(futures):
                rk, eval_res, weighted = fut.result()
                with self._lock:
                    result["dimensions"][rk] = eval_res
                    total_weighted += weighted
        result["total_weighted_score"] = round(total_weighted, 4)
        result["total_percentage"] = round(total_weighted * 100, 2)
        return result

    def _score_one(self, record_key: str, rubric_type: str, generated_text: str, true_text: str) -> tuple:
        rubric = self._rubrics.get(rubric_type)
        weight = rubric.get("weight", 0) if rubric else 0
        eval_res = self._score_dimension(rubric_type, generated_text, true_text)
        actual = eval_res.get("total_score", 0)
        maximum = eval_res.get("max_score", 0)
        pct = (actual / maximum) if maximum > 0 else 0.0
        weighted = round(pct * weight, 4)
        eval_res["dimension_weight"] = weight
        eval_res["weighted_score"] = weighted
        return record_key, eval_res, weighted

    def _score_dimension(self, rubric_type: str, generated_text: str, true_text: str) -> Dict[str, Any]:
        rubric = self._rubrics.get(rubric_type)
        scoring_items = rubric.get("scoring_items", [])
        rubric_prompt = self._rubrics.build_prompt(rubric_type)
        prompt = f"""You are a professional psychiatric clinical note scorer. Compare the test note against the gold note item by item.

{rubric_prompt}

=== Gold note (true) ===
{true_text or "(blank)"}

=== Test note (generated) ===
{generated_text or "(blank)"}

For each item, first check if gold has the element. If not → "skip". If yes → evaluate coverage (0/1) and accuracy (0/1).
Return JSON: {{"scoring_results": [{{"id": ..., "element": ..., "true_has_element": ..., "coverage_score": ..., "accuracy_score": ..., "coverage_reasoning": ..., "accuracy_reasoning": ...}}], "total_score": ..., "max_score": ..., "coverage_total": ..., "accuracy_total": ..., "summary": "..."}}
Return ONLY the JSON."""

        try:
            raw = self._llm.chat(prompt).strip()
            for prefix in ("```json", "```"):
                if raw.startswith(prefix):
                    raw = raw[len(prefix):]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            res = json.loads(raw)
            # LLM may return a list instead of a dict — try to extract the dict.
            if isinstance(res, list):
                res = res[0] if res and isinstance(res[0], dict) else {}
            if not isinstance(res, dict):
                raise ValueError(f"Expected JSON object, got {type(res).__name__}")
            total, maximum = res.get("total_score", 0), res.get("max_score", 0)
            res["percentage"] = round(total / maximum * 100, 2) if maximum > 0 else 0
            res["coverage_percentage"] = round(res.get("coverage_total", 0) / (maximum / 2) * 100, 2) if maximum > 0 else 0
            res["accuracy_percentage"] = round(res.get("accuracy_total", 0) / (maximum / 2) * 100, 2) if maximum > 0 else 0
            return res
        except Exception as exc:
            logger.warning("Dimension scoring failed for %s: %s", rubric_type, exc)
            return {"scoring_results": [{"id": item.get("id", 0), "element": item.get("element", ""), "true_has_element": False, "coverage_score": "skip", "accuracy_score": "skip", "coverage_reasoning": f"Scoring error: {exc}", "accuracy_reasoning": f"Scoring error: {exc}"} for item in scoring_items], "total_score": 0, "max_score": 0, "percentage": 0, "coverage_percentage": 0, "accuracy_percentage": 0, "summary": f"Scoring error: {exc}", "error": str(exc)}


# ---------------------------------------------------------------------------
# Ground-truth loading
# ---------------------------------------------------------------------------

def _load_ground_truth(case_id: str) -> Optional[str]:
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
                    return data.get("realFormulation", "")
            except json.JSONDecodeError:
                continue
    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def evaluate(
    model_name: Optional[str] = None, case_id: Optional[str] = None,
    output_file: Optional[Union[str, Path]] = None,
    phase3_data: Optional[Dict[str, Any]] = None,
    true_formulation: Optional[str] = None,
) -> Dict[str, Any]:
    if phase3_data is None:
        if output_file is None:
            if model_name is None or case_id is None:
                raise ValueError("Provide model_name+case_id, output_file, or phase3_data")
            output_file = get_phase_output_file(model_name, case_id, 3)
        output_file = Path(output_file)
        phase3_data = json.loads(output_file.read_text(encoding="utf-8"))
    model_name = phase3_data.get("model_name", model_name or "")
    case_id = phase3_data.get("case_id", case_id or "")
    if not model_name or not case_id:
        raise ValueError("Cannot determine model_name or case_id")

    formulation = phase3_data.get("syntactic_formulation", "")
    status = phase3_data.get("status", "unknown")
    if true_formulation is None:
        true_formulation = _load_ground_truth(case_id)

    if not formulation or not true_formulation:
        eval_data = {"total_percentage": 0, "status": status, "syntactic_formulation": formulation, "true_formulation": true_formulation, "error": "Missing generated or gold formulation", "dimensions": {}}
        path = save_evaluation_result(model_name, case_id, 3, eval_data)
        return {"total_percentage": 0, "status": status, "output_file": str(path), "model_name": model_name, "case_id": case_id, "error": "Missing generated or gold formulation"}

    evaluator_llm = create_evaluator_client()
    rubrics = _RubricLoader()
    parser = _ClinicalNoteParser(evaluator_llm)
    scorer = _DimensionScorer(evaluator_llm, rubrics)

    generated_record = parser.parse(formulation)
    true_record = parser.parse(true_formulation)
    eval_result = scorer.score_parallel(generated_record, true_record)

    eval_data: Dict[str, Any] = {
        "total_percentage": eval_result.get("total_percentage", 0),
        "total_weighted_score": eval_result.get("total_weighted_score", 0),
        "total_actual_score": eval_result.get("total_actual_score", 0),
        "total_actual_max": eval_result.get("total_actual_max", 0),
        "status": status, "syntactic_formulation": formulation,
        "true_formulation": true_formulation, "generated_record": generated_record,
        "true_record": true_record, "dimensions": eval_result.get("dimensions", {}),
    }

    clinical_note_subjective = None
    try:
        clinical_note_subjective = Scorer.evaluate_multi(rubric_content=CLINICAL_NOTE_QUALITY, test_context=formulation)
        eval_data["clinical_note_subjective"] = clinical_note_subjective
    except Exception:
        logger.exception("Phase 3 subjective evaluation failed")

    path = save_evaluation_result(model_name, case_id, 3, eval_data)
    return {"total_percentage": eval_result.get("total_percentage", 0), "total_weighted_score": eval_result.get("total_weighted_score", 0), "dimensions": eval_result.get("dimensions", {}), "clinical_note_subjective": clinical_note_subjective, "status": status, "output_file": str(path), "model_name": model_name, "case_id": case_id}
