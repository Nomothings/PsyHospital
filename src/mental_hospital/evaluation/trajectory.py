"""Trajectory collector — SFT / DPO training data generation from evaluator outputs.

Directory layout (under ``data/output/eval_trajectory/``)::

    sft/{Emp,Pro,Note,Diag,Treat}/   — high-agreement examples
    dpo/{Emp,Pro,Note,Diag,Treat}/   — low-agreement examples
"""

from __future__ import annotations

import json
import random
import string
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from mental_hospital.config import settings

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
TRAJECTORY_DIR = _PROJECT_ROOT / "data" / "output" / "eval_trajectory"

_DIMENSION_MAP = {
    "Emp": "Empathy",
    "Pro": "Professionalism",
    "Note": "ClinicalNote",
    "Diag": "DiagnosticRigor",
    "Treat": "TreatmentAppropriateness",
}

_MODE_THRESHOLD = {5: 3, 4: 2, 3: 2}
_MIN_EVALUATORS = 3


def _random_stamp(n: int = 6) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


class TrajectoryCollector:
    """Collects evaluator outputs and writes SFT / DPO trajectory files."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = output_dir or TRAJECTORY_DIR
        for dim in _DIMENSION_MAP:
            (self.output_dir / "sft" / dim).mkdir(parents=True, exist_ok=True)
            (self.output_dir / "dpo" / dim).mkdir(parents=True, exist_ok=True)

    def collect(
        self, dimension: str, user_prompt: str,
        individual_results: List[Dict], case_id: Optional[str] = None,
        test_model: Optional[str] = None,
    ) -> Dict:
        """Collect one evaluation's trajectory data.

        Returns a dict with keys ``mode``, ``mode_count``, ``n_valid``,
        ``quality``, ``sft_files``, ``dpo_file``.
        """
        if dimension not in _DIMENSION_MAP:
            raise ValueError(f"Unknown dimension: {dimension}. Options: {list(_DIMENSION_MAP)}")

        valid = [r for r in individual_results if r.get("score") is not None]
        n_valid = len(valid)
        if n_valid < _MIN_EVALUATORS:
            return {"mode": None, "mode_count": 0, "n_valid": n_valid, "quality": "discard_few_evaluators", "sft_files": [], "dpo_file": None}

        scores = [r["score"] for r in valid]
        counter = Counter(scores)
        mode_count = max(counter.values())
        mode_values = [s for s, c in counter.items() if c == mode_count]

        if len(mode_values) > 1:
            return self._save_low_agreement(dimension, user_prompt, valid, case_id, test_model, "low_agreement_tie")

        mode = mode_values[0]
        threshold = _MODE_THRESHOLD.get(n_valid, 3)
        if mode_count < threshold:
            return self._save_low_agreement(dimension, user_prompt, valid, case_id, test_model, "low_agreement_split")

        # High agreement → SFT only
        high_quality = [r for r in valid if r["score"] == mode]
        sft_files: list[str] = []
        if high_quality:
            chosen = random.choice(high_quality)
            sft_files.append(self._save_sft(dimension, user_prompt, chosen, case_id, test_model))
        return {"mode": mode, "mode_count": mode_count, "n_valid": n_valid, "quality": "high_agreement_sft", "sft_files": sft_files, "dpo_file": None}

    def _save_low_agreement(self, dimension: str, user_prompt: str, valid: List[Dict], case_id: Optional[str], test_model: Optional[str], quality: str) -> Dict:
        valid.sort(key=lambda r: r["evaluator_id"])
        dpo_file = self._save_dpo(dimension, user_prompt, valid, case_id, test_model)
        return {"mode": None, "mode_count": 0, "n_valid": len(valid), "quality": quality, "sft_files": [], "dpo_file": dpo_file}

    def _save_sft(self, dimension: str, user_prompt: str, result: Dict, case_id: Optional[str], test_model: Optional[str]) -> str:
        evaluator_name = settings.get_evaluator_model_name(result["evaluator_id"])
        stamp = _random_stamp()
        cid = case_id or "unknown"
        filepath = self.output_dir / "sft" / dimension / f"{cid}_{evaluator_name}_{stamp}.json"
        entry = {"case_id": case_id, "score": result["score"], "test_model": test_model, "evaluate_model": evaluator_name, "instruction": user_prompt, "input": "", "output": result["raw_response"]}
        filepath.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(filepath)

    def _save_dpo(self, dimension: str, user_prompt: str, valid: List[Dict], case_id: Optional[str], test_model: Optional[str]) -> str:
        first_model = settings.get_evaluator_model_name(valid[0]["evaluator_id"])
        stamp = _random_stamp()
        cid = case_id or "unknown"
        filepath = self.output_dir / "dpo" / dimension / f"{cid}_{first_model}_{stamp}.json"
        entry = {"case_id": case_id, "score": [r["score"] for r in valid], "test_model": test_model, "evaluate_model": [settings.get_evaluator_model_name(r["evaluator_id"]) for r in valid], "instruction": user_prompt, "input": "", "output": [r["raw_response"] for r in valid]}
        filepath.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(filepath)


def collect_from_evaluation_result(
    dimension: str, evaluation_result: Dict,
    case_id: Optional[str] = None, test_model: Optional[str] = None,
) -> Dict:
    """Convenience: collect trajectory from a ``Scorer.evaluate_multi()`` result."""
    individual = evaluation_result.get("individual_results", [])
    if not individual:
        return {"error": "no individual_results available", "sft_files": [], "dpo_file": None}
    user_prompt = evaluation_result.get("metadata", {}).get("user_prompt", "")
    if not user_prompt:
        return {"error": "user_prompt not available", "sft_files": [], "dpo_file": None}
    return TrajectoryCollector().collect(dimension=dimension, user_prompt=user_prompt, individual_results=individual, case_id=case_id, test_model=test_model)
