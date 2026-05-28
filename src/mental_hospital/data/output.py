"""Output file management — phase outputs, evaluation results, and
conversation persistence.

Directory layout (under ``data/output/``)::

    interview/{model_name}/{case_id}/
        interview_phase{1..5}_output.json
        interview_summary.json
    evaluation/{model_name}/{case_id}/
        evaluation_phase{1..5}_output.json
    results/{model_name}.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_OUTPUT_ROOT = _PROJECT_ROOT / "data" / "output"


def get_output_dir(model_name: str, case_id: str) -> Path:
    d = _OUTPUT_ROOT / "interview" / model_name / case_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_phase_output_file(model_name: str, case_id: str, phase: int) -> Path:
    return get_output_dir(model_name, case_id) / f"interview_phase{phase}_output.json"


def init_phase_output(model_name: str, case_id: str, phase: int, initial_data: Dict[str, Any]) -> Path:
    path = get_phase_output_file(model_name, case_id, phase)
    payload: dict[str, Any] = {"phase": phase, "case_id": case_id, "model_name": model_name, "timestamp": datetime.now().isoformat(), "status": "running", **initial_data}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def update_phase_output(output_file: Path, updates: Dict[str, Any], status: Optional[str] = None) -> None:
    data = json.loads(output_file.read_text(encoding="utf-8"))
    data.update(updates)
    data["last_update"] = datetime.now().isoformat()
    if status is not None:
        data["status"] = status
    output_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_conversation(
    output_file: Path, role: str, content: str,
    chief_complaint_used: Optional[List[str]] = None,
    mental_status_used: Optional[List[str]] = None,
) -> None:
    data = json.loads(output_file.read_text(encoding="utf-8"))
    data.setdefault("conversation", []).append({"role": role, "content": content, "timestamp": datetime.now().strftime("%H:%M:%S")})
    if chief_complaint_used:
        existing = set(data.setdefault("chief_complaint_used", []))
        existing.update(chief_complaint_used)
        data["chief_complaint_used"] = list(existing)
    if mental_status_used:
        existing = set(data.setdefault("mental_status_used", []))
        existing.update(mental_status_used)
        data["mental_status_used"] = list(existing)
    data["last_update"] = datetime.now().isoformat()
    output_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_phase_output(model_name: str, case_id: str, phase: int) -> Optional[Dict[str, Any]]:
    path = get_phase_output_file(model_name, case_id, phase)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_evaluation_dir(model_name: str, case_id: str) -> Path:
    d = _OUTPUT_ROOT / "evaluation" / model_name / case_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_evaluation_output_file(model_name: str, case_id: str, phase: int) -> Path:
    return get_evaluation_dir(model_name, case_id) / f"evaluation_phase{phase}_output.json"


def save_evaluation_result(model_name: str, case_id: str, phase: int, evaluation_data: Dict[str, Any]) -> Path:
    path = get_evaluation_output_file(model_name, case_id, phase)
    payload: dict[str, Any] = {"phase": phase, "case_id": case_id, "model_name": model_name, "timestamp": datetime.now().isoformat(), **evaluation_data}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
