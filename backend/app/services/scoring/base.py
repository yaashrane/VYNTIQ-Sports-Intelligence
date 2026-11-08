"""Base constants and shared definitions for the VOR scoring engine."""

SCORING_ENGINE_VERSION: str = "1.0.0"

# Standard baseline median score for regressing ratings toward cohort center
COHORT_MEDIAN_SCORE: float = 50.0

# Minimum cohort size required to compute statistically viable empirical percentiles
MINIMUM_COHORT_SIZE: int = 3
