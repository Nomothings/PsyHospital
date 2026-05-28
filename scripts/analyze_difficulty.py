#!/usr/bin/env python3
"""Run the disease difficulty analysis report."""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from mental_hospital.analysis.difficulty import analyze_difficulty

if __name__ == "__main__":
    analyze_difficulty()
