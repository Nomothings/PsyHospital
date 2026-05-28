"""Exponential-backoff retry."""

from __future__ import annotations

import logging
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


def retry_with_backoff(
    fn: Callable[[], T], max_retries: int = 3, base_delay: float = 1.0,
) -> T:
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            logger.warning("Retry %d/%d: %s", attempt + 1, max_retries, exc)
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
    raise last_error  # type: ignore[misc]
