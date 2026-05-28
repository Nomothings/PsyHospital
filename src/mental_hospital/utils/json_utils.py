"""JSON parsing utilities with graceful fallback for malformed LLM output."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Union

try:
    from json_repair import repair_json as _repair_json
    _HAS_JSON_REPAIR = True
except ImportError:  # pragma: no cover
    _HAS_JSON_REPAIR = False
    _repair_json = None


def safe_parse_json(text: str) -> Optional[Any]:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def extract_json_from_text(text: str) -> Optional[str]:
    match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', text)
    return match.group(0) if match else None


def try_repair_json(text: str) -> Optional[Any]:
    if not _HAS_JSON_REPAIR or _repair_json is None:
        return None
    try:
        repaired = _repair_json(text)
        return json.loads(repaired) if isinstance(repaired, str) else repaired
    except Exception:
        return None


def parse_json_array(data: Union[str, List[Any]], field_name: str = "data") -> List[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, str):
        parsed = safe_parse_json(data)
        if parsed is None:
            raise ValueError(f"{field_name} is not a valid JSON array string")
        if not isinstance(parsed, list):
            raise ValueError(f"{field_name} parsed but is not an array")
        return parsed
    raise TypeError(f"{field_name} must be a list or JSON array string")


def parse_json_object(data: Union[str, Dict[str, Any]], field_name: str = "data") -> Dict[str, Any]:
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        parsed = safe_parse_json(data)
        if parsed is None:
            raise ValueError(f"{field_name} is not a valid JSON object string")
        if not isinstance(parsed, dict):
            raise ValueError(f"{field_name} parsed but is not an object")
        return parsed
    raise TypeError(f"{field_name} must be a dict or JSON object string")
