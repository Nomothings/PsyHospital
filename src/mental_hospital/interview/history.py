"""Phase 1: Clinical History Collection — multi-turn doctor–patient dialogue."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from mental_hospital.agents.psychiatrist import create_psychiatrist
from mental_hospital.agents.patient import create_patient
from mental_hospital.config import settings
from mental_hospital.data.loader import get_patient_dirs, load_random_case
from mental_hospital.data.output import (
    append_conversation,
    init_phase_output,
    update_phase_output,
)
from mental_hospital.llm.client import LLMClient
from mental_hospital.prompts.phases import HISTORY_COLLECTION
from mental_hospital.utils.json_utils import extract_json_from_text, safe_parse_json, try_repair_json

logger = logging.getLogger(__name__)

_END_MARKERS = [
    "[END_INTERVIEW]", "[end_interview]", "END_INTERVIEW",
    "end_interview", "[END_INTERVIEW", "END_INTERVIEW]",
]


# ---------------------------------------------------------------------------
# Patient response parsing
# ---------------------------------------------------------------------------

def parse_patient_response(response: str) -> Tuple[str, List[str], List[str]]:
    """Parse a patient's JSON response → (visible_text, chief_complaints, mental_statuses)."""
    json_str = extract_json_from_text(response) or response
    data = safe_parse_json(json_str)
    if data is None:
        data = try_repair_json(json_str)
    if data is None:
        data = _extract_fields_regex(json_str)

    if isinstance(data, dict):
        presentation = data.get("presentation", "").strip()
        utterance = data.get("utterance", "").strip()
        grounding = data.get("grounding", {}) if isinstance(data.get("grounding"), dict) else {}
        visible = f"{presentation} {utterance}".strip() if presentation else utterance
        cc = [item.strip() for item in grounding.get("chief_complaint", []) if isinstance(item, str)]
        ms = [item.strip() for item in grounding.get("mental_status", []) if isinstance(item, str)]
        return visible, cc, ms
    return response.strip(), [], []


def _extract_fields_regex(response: str) -> Optional[Dict[str, Any]]:
    result: dict[str, Any] = {"presentation": "", "utterance": "", "grounding": {"chief_complaint": [], "mental_status": []}}
    for field in ("presentation", "utterance"):
        m = re.search(rf'"{field}"\s*:\s*"([^"]*)"', response, re.DOTALL)
        if m:
            result[field] = m.group(1)
    for field in ("chief_complaint", "mental_status"):
        m = re.search(rf'"{field}"\s*:\s*(\[[^\]]*\])', response, re.DOTALL)
        if m:
            parsed = safe_parse_json(m.group(1))
            result["grounding"][field] = parsed if isinstance(parsed, list) else re.findall(r'"([^"]*)"', m.group(1))
    if not result["presentation"] and not result["utterance"]:
        return None
    return result


# ---------------------------------------------------------------------------
# SEARCH command handling
# ---------------------------------------------------------------------------

def _handle_search_commands(
    raw_response: str, patient: LLMClient, case_id: str,
    searched_events: Set[str], doctor_response: str,
) -> str:
    json_match = re.search(r'\{[\s\S]*\}', raw_response)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            utterance = data.get("utterance", "")
            searches = re.findall(r'\[SEARCH_(.+?)\]', utterance)
            if searches:
                return _process_search(raw_response, data, searches, patient, case_id, doctor_response, searched_events)
        except (json.JSONDecodeError, KeyError):
            pass
    searches = re.findall(r'\[SEARCH_(.+?)\]', raw_response)
    return _process_search_plain(raw_response, searches, patient, case_id, doctor_response, searched_events) if searches else raw_response


def _process_search(
    raw_response: str, data: Dict, searches: List[str],
    patient: LLMClient, case_id: str, doctor_response: str, searched_events: Set[str],
) -> str:
    event = searches[0].strip()
    utterance = data.get("utterance", "")
    if event in searched_events:
        data["utterance"] = re.sub(r'\[SEARCH_.+?\]\s*', '', utterance).strip()
        return json.dumps(data, ensure_ascii=False)
    searched_events.add(event)
    return _do_search(event, patient, case_id, doctor_response, raw_response)


def _process_search_plain(
    raw_response: str, searches: List[str], patient: LLMClient,
    case_id: str, doctor_response: str, searched_events: Set[str],
) -> str:
    event = searches[0].strip()
    if event in searched_events:
        return re.sub(r'\[SEARCH_.+?\]\s*', '', raw_response).strip()
    searched_events.add(event)
    return _do_search(event, patient, case_id, doctor_response, raw_response)


def _do_search(event: str, patient: LLMClient, case_id: str, doctor_response: str, fallback: str) -> str:
    _, experience_dir = get_patient_dirs(case_id)
    file_path = experience_dir / f"{event}.md"
    if not file_path.exists():
        logger.warning("Experience file not found: %s", event)
        return re.sub(r'\[SEARCH_.+?\]\s*', '', fallback).strip()

    logger.info("Patient performs internal search: %s", event)
    search_content = file_path.read_text(encoding="utf-8")
    prompt = (
        f"System note — your search result:\n\n{search_content}\n\n"
        f"Now, based on the search result and the doctor's question, answer formally.\n"
        f'Reply strictly in this JSON format:\n'
        f'{{"presentation": "(observable non-verbal behaviour)", "utterance": "(your spoken response)", '
        f'"grounding": {{"chief_complaint": [], "mental_status": []}}}}\n\n'
        f"Doctor's question: {doctor_response}"
    )
    new_response = patient.chat(prompt)
    json_match = re.search(r'\{[\s\S]*\}', new_response)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            data["utterance"] = re.sub(r'\[SEARCH_.+?\]\s*', '', data.get("utterance", "")).strip()
            return json.dumps(data, ensure_ascii=False)
        except (json.JSONDecodeError, KeyError):
            pass
    return re.sub(r'\[SEARCH_.+?\]\s*', '', new_response).strip()


# ---------------------------------------------------------------------------
# Phase runner
# ---------------------------------------------------------------------------

def run(case: Optional[Dict[str, Any]] = None, *, patient_backup: bool = False) -> Dict[str, Any]:
    """Run Phase 1: Clinical History Collection.

    Returns a dict with keys: case_id, model_name, conversation,
    chief_complaint_used, mental_status_used, output_file, status,
    doctor, case_data.
    """
    max_turns = settings.max_turns
    if case is None:
        case = load_random_case()
    case_id = case.get("id", "unknown")
    basic_info = case.get("basicInfomation", "")
    chief_complaint = case.get("chiefComplaint", [])
    mental_status = case.get("mentalStatus", [])
    physical_examination = case.get("physicalExamination", "")
    if isinstance(physical_examination, list):
        physical_examination = "；".join(physical_examination)

    doctor = create_psychiatrist()
    doctor_model = doctor.config.model

    skill_path, _ = get_patient_dirs(case_id)
    patient = create_patient(
        basic_info=basic_info, chief_complaint=chief_complaint,
        mental_status=mental_status,
        skill_file=str(skill_path) if skill_path.exists() else None,
        backup=patient_backup,
    )

    output_file = init_phase_output(model_name=doctor_model, case_id=case_id, phase=1, initial_data={
        "basic_info": basic_info, "chief_complaint_all": chief_complaint,
        "mental_status_all": mental_status, "conversation": [],
        "chief_complaint_used": [], "mental_status_used": [],
    })

    start_prompt = HISTORY_COLLECTION.replace("<BASIC_INFO>", basic_info).replace("<PHYSICAL_EXAMINATION>", physical_examination)
    doctor_response = doctor.chat(start_prompt)
    append_conversation(output_file, "doctor", doctor_response)

    if any(m in doctor_response for m in _END_MARKERS):
        append_conversation(output_file, "system", "Doctor ended interview immediately")
        update_phase_output(output_file, {}, status="completed")
    else:
        searched_events: Set[str] = set()
        for turn in range(max_turns):
            current = turn + 1
            patient_raw = patient.chat(doctor_response)
            patient_raw = _handle_search_commands(patient_raw, patient, case_id, searched_events, doctor_response)
            patient_visible, cc_used, ms_used = parse_patient_response(patient_raw)
            if '[SEARCH_' in patient_visible:
                patient_visible = re.sub(r'\[SEARCH_.+?\]\s*', '', patient_visible).strip()
            append_conversation(output_file, "patient", patient_visible, chief_complaint_used=cc_used, mental_status_used=ms_used)

            msg = patient_visible
            if current in (30, 40):
                msg += f"\n-----\nReminder: turn {current}. Plan remaining turns efficiently. Output [END_INTERVIEW] only when information is sufficient.\n-----"
            doctor_response = doctor.chat(msg)

            if any(m in doctor_response for m in _END_MARKERS):
                append_conversation(output_file, "doctor", doctor_response)
                update_phase_output(output_file, {}, status="completed")
                break
            append_conversation(output_file, "doctor", doctor_response)
        else:
            append_conversation(output_file, "system", f"Max turns ({max_turns}) reached")
            update_phase_output(output_file, {}, status="max_turns_reached")

    final_data = json.loads(output_file.read_text(encoding="utf-8"))
    logger.info("Phase 1 complete — %d patient turns, status=%s",
                sum(1 for c in final_data["conversation"] if c["role"] == "patient"), final_data["status"])
    return {
        "case_id": case_id, "model_name": doctor_model,
        "conversation": final_data["conversation"],
        "chief_complaint_used": final_data["chief_complaint_used"],
        "mental_status_used": final_data["mental_status_used"],
        "output_file": str(output_file), "status": final_data["status"],
        "doctor": doctor, "case_data": case,
    }
