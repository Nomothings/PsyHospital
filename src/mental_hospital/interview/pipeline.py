"""InterviewPipeline — orchestrates all five clinical interview phases."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from mental_hospital.data.output import get_output_dir
from mental_hospital.llm.client import LLMClient
from mental_hospital.interview import history, examination, formulation, diagnosis, treatment

logger = logging.getLogger(__name__)


@dataclass
class InterviewContext:
    """Mutable context carried across all five interview phases."""

    case_id: str = ""
    model_name: str = ""
    doctor: Optional[LLMClient] = None
    case_data: Dict[str, Any] = field(default_factory=dict)


class InterviewPipeline:
    """Orchestrates a full 5-phase psychiatric interview for one case.

    Usage::

        pipeline = InterviewPipeline()
        result = pipeline.run(case=case_data)
    """

    def run(
        self,
        case: Optional[Dict[str, Any]] = None,
        *,
        patient_backup: bool = False,
        instrument_backup: bool = False,
    ) -> Dict[str, Any]:
        """Execute all five phases; return the full interview result dict."""
        # Phase 1
        logger.info("Phase 1/5: Clinical History Collection")
        p1 = history.run(case=case, patient_backup=patient_backup)
        ctx = InterviewContext(case_id=p1["case_id"], model_name=p1["model_name"], doctor=p1["doctor"], case_data=p1["case_data"])

        # Phase 2
        logger.info("Phase 2/5: Examination Recommendation")
        p2 = examination.run(ctx.doctor, ctx.model_name, ctx.case_id, ctx.case_data, instrument_backup=instrument_backup)

        # Phase 3
        logger.info("Phase 3/5: Clinical Formulation")
        p3 = formulation.run(ctx.doctor, ctx.model_name, ctx.case_id, p2["examination_results"])

        # Phase 4
        logger.info("Phase 4/5: Definitive Diagnosis")
        p4 = diagnosis.run(ctx.doctor, ctx.model_name, ctx.case_id)

        # Phase 5
        logger.info("Phase 5/5: Treatment Planning")
        p5 = treatment.run(ctx.doctor, ctx.model_name, ctx.case_id)

        result = self._assemble(p1, p2, p3, p4, p5)
        self._save_summary(result)
        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _assemble(p1: Dict, p2: Dict, p3: Dict, p4: Dict, p5: Dict) -> Dict[str, Any]:
        return {
            "case_id": p1["case_id"], "model_name": p1["model_name"],
            "phase1": {
                "status": p1["status"],
                "conversation_turns": sum(1 for c in p1["conversation"] if c["role"] == "patient"),
                "output_file": p1["output_file"], "conversation": p1["conversation"],
                "chief_complaint_used": p1["chief_complaint_used"],
                "mental_status_used": p1["mental_status_used"],
            },
            "phase2": {"examinations": p2["examinations"], "examination_results": p2["examination_results"], "output_file": p2["output_file"]},
            "phase3": {"syntactic_formulation": p3["syntactic_formulation"], "output_file": p3["output_file"]},
            "phase4": {"definitive_diagnosis": p4["definitive_diagnosis"], "diagnosis_reasoning": p4["diagnosis_reasoning"], "output_file": p4["output_file"]},
            "phase5": {"treatment_plan": p5["treatment_plan"], "output_file": p5["output_file"]},
        }

    @staticmethod
    def _save_summary(result: Dict[str, Any]) -> Path:
        output_dir = get_output_dir(result["model_name"], result["case_id"])
        path = output_dir / "interview_summary.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
