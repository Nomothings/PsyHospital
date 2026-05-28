"""LLM-as-a-Judge subjective scorer.

Wraps a rubric prompt around the text under evaluation and calls *N*
independent evaluator LLMs in parallel, averaging their 1–5 scores.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from mental_hospital.config import settings
from mental_hospital.llm.factory import create_evaluator_client
from mental_hospital.prompts.rubrics import RUBRIC_FORMAT

logger = logging.getLogger(__name__)


class Scorer:
    """Rubric-based scorer using multiple LLM judges.

    Each evaluator receives the same rubric + content and independently
    assigns a score from 1–5.  The final score is the average across all
    evaluators that successfully returned a parseable score.
    """

    @staticmethod
    def evaluate_multi(rubric_content: str, test_context: str) -> Dict[str, Any]:
        """Run *N* evaluators in parallel; return averaged results.

        Returns a dict with keys ``score`` (float average), ``scores``
        (per-evaluator list), ``analyses``, ``parsed_count``, and
        ``individual_results``.
        """
        if not rubric_content.strip():
            raise ValueError("rubric_content must not be empty")
        if not test_context.strip():
            raise ValueError("test_context must not be empty")

        user_prompt = RUBRIC_FORMAT.replace("<RUBRIC_CONTENT>", rubric_content).replace("<TEST_CONTENT>", test_context)

        print(f"  [scorer] running {settings.num_evaluators} evaluators...", flush=True)
        num = settings.num_evaluators
        results: List[Dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=num) as executor:
            futures = {executor.submit(_evaluate_one, i, user_prompt): i for i in range(1, num + 1)}
            for fut in as_completed(futures):
                results.append(fut.result())

        results.sort(key=lambda r: r.get("evaluator_id", 0))
        scores = [r["score"] for r in results]
        valid = [s for s in scores if s is not None]
        avg = round(sum(valid) / len(valid), 2) if valid else None

        print(f"  [scorer] done — avg={avg}, parsed={len(valid)}/{num}", flush=True)
        return {
            "score": avg,
            "scores": scores,
            "analyses": [r.get("raw_response", "") for r in results],
            "parsed_count": len(valid),
            "individual_results": results,
        }


def _evaluate_one(evaluator_id: int, user_prompt: str) -> Dict[str, Any]:
    """Run one evaluator (module-level so it is picklable)."""
    try:
        llm = create_evaluator_client(evaluator_id=evaluator_id)
        raw = llm.chat(user_prompt)
        m = re.search(r'\[DECISION_START\]\s*(\d)\s*\[DECISION_END\]', raw)
        score = int(m.group(1)) if m and 1 <= int(m.group(1)) <= 5 else None
        return {"evaluator_id": evaluator_id, "score": score, "raw_response": raw, "score_parsed": score is not None}
    except Exception as exc:
        logger.exception("Evaluator %d failed", evaluator_id)
        return {"evaluator_id": evaluator_id, "score": None, "raw_response": f"Error: {exc}", "score_parsed": False, "error": str(exc)}
