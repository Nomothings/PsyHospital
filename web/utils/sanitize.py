"""
Input sanitization utility functions
"""
import re


def sanitize_case_id(case_id: str) -> str:
    """Prevent path traversal: only allow letters, digits, underscores, hyphens, dots

    Args:
        case_id: Original case_id

    Returns:
        Sanitized case_id

    Raises:
        ValueError: If case_id contains illegal characters
    """
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', case_id):
        raise ValueError(f"Illegal case_id: {case_id}")
    return case_id


def is_valid_record_id(record_id: str) -> bool:
    """Check if record_id is valid (only letters, digits, underscores, hyphens, dots)"""
    return bool(re.match(r'^[a-zA-Z0-9_\-\.]+$', record_id))
