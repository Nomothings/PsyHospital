"""
JSON file read/write utility functions
"""
import json
import logging

logger = logging.getLogger(__name__)


def read_json_safe(filepath) -> dict | None:
    """Safely read JSON file, returns None on failure

    Args:
        filepath: File path (str or Path)

    Returns:
        Parsed dict, returns None on failure
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read file {filepath}: {e}")
        return None
