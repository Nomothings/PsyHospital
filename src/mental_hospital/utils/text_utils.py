"""Text formatting helpers."""

from __future__ import annotations

from typing import Any, Dict, List


def format_conversation_text(conversation: List[Dict[str, Any]]) -> str:
    lines: list[str] = []
    for idx, turn in enumerate(conversation, 1):
        role = turn.get("role", "unknown")
        content = turn.get("content", "")
        if role == "doctor":
            lines.append(f"[Turn {idx}] Doctor: {content}")
        elif role == "patient":
            lines.append(f"[Turn {idx}] Patient: {content}")
        else:
            lines.append(f"[Turn {idx}] [{role}]: {content}")
    return "\n\n".join(lines)


def format_examination_results(results: Dict[str, Any]) -> str:
    if not results:
        return "No auxiliary examination results"
    return "\n".join(f"- {name}: {value}" for name, value in results.items())
