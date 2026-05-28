"""SFT data parsing — extracts rubric content and test context from
concatenated instruction strings.

Ported from the original ``utils/sft_utils.py``.
"""

from __future__ import annotations

from typing import Dict, List

_RUBRIC_START = '\n---\n## Rubric细则：\n'
_TEST_START = '\n---\n\n---\n## 评测输入：\n'
_TEST_END = '\n\n---\n\n你的任务是：基于 Rubric 进行评分分析，并在分析结束后输出最终等级： [DECISION_START]X[DECISION_END]\n'


def parse_instruction(instruction: str) -> dict:
    """Split an SFT instruction into rubric_content and test_context."""
    idx1 = instruction.find(_RUBRIC_START)
    idx2 = instruction.find(_TEST_START)
    idx3 = instruction.find(_TEST_END)
    if idx1 == -1 or idx2 == -1:
        raise ValueError(f"Boundary markers not found: RUBRIC_START={idx1}, TEST_START={idx2}")
    rubric_content = instruction[idx1 + len(_RUBRIC_START):idx2]
    test_context = instruction[idx2 + len(_TEST_START):idx3] if idx3 != -1 else instruction[idx2 + len(_TEST_START):]
    return {"rubric_content": rubric_content, "test_context": test_context}


def parse_sft_item(item: dict) -> dict:
    """Parse a single SFT item, returning decoupled parts."""
    parsed = parse_instruction(item["instruction"])
    return {"rubric_content": parsed["rubric_content"], "test_context": parsed["test_context"], "input": item.get("input", ""), "output": item.get("output", ""), "score": item.get("score", 0)}


def batch_parse_sft(items: List[dict]) -> list:
    return [parse_sft_item(item) for item in items]
