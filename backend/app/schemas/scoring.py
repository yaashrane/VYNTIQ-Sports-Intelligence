"""Pydantic schemas for ECDF normalization, Bayesian reliability adjustment, VOR composite scoring, and player rankings."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
from backend.app.schemas.evaluation import PlayerRole, RoleClassificationResult
from backend.app.schemas.metrics import MetricDirection, MetricProvenance, SampleSizeInfo


class ReliabilityStatus(str, Enum):
    """Statistical sample reliability status."""

    ADEQUATE = "ADEQUATE"  # Full reliability, C(N) = 1.0
    RELIABILITY_DISCOUNTED = "RELIABILITY_DISCOUNTED"  # Regressed toward cohort median, C(N) in (0, 1)
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"  # N < N_min, quarantined from top leaderboards


class NormalizedMetric(BaseModel):
    """Individual metric normalized via Empirical Cumulative Distribution Function (ECDF)."""

    metric_id: str
    display_name: str
    raw_value: float | int | None
    directionality: MetricDirection
    percentile: float  # [0.0, 100.0]
    cohort_id: str
    cohort_size: int
    normalization_method: str = "ECDF"


class DimensionScore(BaseModel):
    """Aggregated score for a single evaluation dimension."""

    dimension_id: str
    dimension_name: str
    dimension_score: float  # [0.0, 100.0]
    weight: float  # [0.0, 1.0]
    contribution_points: float  # dimension_score * weight
    metrics: list[NormalizedMetric] = Field(default_factory=list)


class ScoreExplanation(BaseModel):
    """Transparent factor attribution and audit breakdown for a player's VOR score."""

    final_vor: float
    raw_composite: float
    reliability_factor: float
    reliability_status: ReliabilityStatus
    top_strengths: list[str] = Field(default_factory=list)
    drag_factors: list[str] = Field(default_factory=list)
    missing_or_limited_dimensions: list[str] = Field(default_factory=list)
    summary_text: str


class PlayerScoreResult(BaseModel):
    """Consolidated VOR evaluation, reliability shrinkage, and dimension breakdown for a player."""

    player_id: str
    player_name: str
    role: PlayerRole
    role_classification: RoleClassificationResult
    cohort_id: str
    vor_score: float  # Final reliability-adjusted composite score
    raw_composite_score: float  # Unregressed weighted dimension sum
    reliability_factor: float  # C(N) in [0.0, 1.0]
    reliability_status: ReliabilityStatus
    sample_size: SampleSizeInfo
    discipline_components: dict[str, float] = Field(default_factory=dict)  # e.g. batting_vor, bowling_vor
    dual_bonus_points: float = 0.0  # For all-rounders
    dimensions: dict[str, DimensionScore] = Field(default_factory=dict)
    is_qualified: bool  # Meets minimum sample thresholds
    is_eligible: bool = True  # Competition eligibility
    eligibility_notes: str | None = None
    explanation: ScoreExplanation
    scoring_version: str = "1.0.0"
    provenance: MetricProvenance


class RankedPlayer(BaseModel):
    """Leaderboard entry for a ranked player."""

    rank: int
    player_id: str
    player_name: str
    role: PlayerRole
    vor_score: float
    raw_composite_score: float
    reliability_factor: float
    reliability_status: ReliabilityStatus
    primary_tiebreaker: float  # TSR for batters, TER for bowlers
    is_qualified: bool
    is_eligible: bool
    quarantine_reasons: list[str] = Field(default_factory=list)


class ScoringRunResponse(BaseModel):
    """Metadata and execution results for a complete scoring run."""

    run_id: str
    dataset_id: str
    cohort_id: str
    total_evaluated: int
    total_qualified: int
    total_quarantined: int
    scoring_version: str = "1.0.0"
    created_at: str
    players: list[PlayerScoreResult] = Field(default_factory=list)


class RankingResponse(BaseModel):
    """Role-isolated leaderboard response with qualified and quarantined pools."""

    run_id: str
    cohort_id: str
    role_filter: str | None = None
    total_ranked: int
    total_quarantined: int
    rankings: list[RankedPlayer] = Field(default_factory=list)
    quarantined: list[RankedPlayer] = Field(default_factory=list)


class ScoringCalculationRequest(BaseModel):
    """Payload to trigger VOR scoring execution."""

    dataset_id: str
    role_filter: str | None = None
    min_batting_balls: int | None = None
    min_bowling_balls: int | None = None
    apply_eligibility_filter: bool = False
    max_age_years: float | None = None
    uncapped_only: bool = False


class ScoringMethodologyResponse(BaseModel):
    """Documentation and configuration parameters for the active VOR scoring engine."""

    version: str = "1.0.0"
    ecdf_formula_higher_better: str
    ecdf_formula_lower_better: str
    bayesian_shrinkage_formula: str
    sample_thresholds: dict[str, Any]
    role_weights: dict[str, dict[str, float]]
    all_rounder_dual_bonus_formula: str
    tie_breaking_hierarchy: list[str]
