"""Centralised constants."""

# Number of parallel evaluators for rubric-based scoring.
NUM_EVALUATORS: int = 5

# Max messages retained in LLM conversation history (1 system + N chat).
MAX_HISTORY_MESSAGES: int = 42

# Default maximum conversation turns in Phase 1.
DEFAULT_MAX_TURNS: int = 50

# Default batch concurrency.
DEFAULT_CONCURRENCY: int = 32

# Min / max rubric levels.
RUBRIC_MIN_LEVEL: int = 1
RUBRIC_MAX_LEVEL: int = 5

# Metrics whose values are in [0, 1] → 4 decimal places.
METRICS_4_DECIMAL: frozenset[str] = frozenset({
    "phase2_precision", "phase2_recall", "phase2_f1",
    "phase4_disorder_precision", "phase4_disorder_recall",
    "phase4_disorder_f1", "phase4_disorder_jaccard",
    "phase4_category_precision", "phase4_category_recall",
    "phase4_category_f1", "phase4_category_jaccard",
    "phase4_exact_match", "phase4_reciprocal_rank",
    "phase4_poa", "phase4_ndcg",
})
