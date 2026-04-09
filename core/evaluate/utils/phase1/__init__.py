"""
Phase 1 评估工具模块

包含专业度评估和共情度评估的工具
"""

from core.evaluate.utils.phase1.scales import EMPATHY_SCALE, PROFESSION_SCALE
from core.evaluate.utils.phase1.prompts import (
    EMPATHY_SYSTEM_PROMPT,
    PROFESSION_SYSTEM_PROMPT,
    get_empathy_user_prompt,
    get_profession_user_prompt
)
from core.evaluate.utils.phase1.evaluator import (
    evaluate_empathy,
    evaluate_profession,
    evaluate_both
)

__all__ = [
    "EMPATHY_SCALE",
    "PROFESSION_SCALE",
    "EMPATHY_SYSTEM_PROMPT",
    "PROFESSION_SYSTEM_PROMPT",
    "get_empathy_user_prompt",
    "get_profession_user_prompt",
    "evaluate_empathy",
    "evaluate_profession",
    "evaluate_both"
]
