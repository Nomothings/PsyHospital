#!/usr/bin/env python3
"""Compute and export aggregated model metrics as JSON."""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from mental_hospital.analysis.aggregate import aggregate_metrics

if __name__ == "__main__":
    aggregate_metrics()
