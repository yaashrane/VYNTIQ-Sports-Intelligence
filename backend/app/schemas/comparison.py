"""Pydantic schemas for multi-player comparison, difference analysis, and compatibility checks."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
from backend.app.schemas.evaluation import PlayerRole
from backend.app.schemas.metrics import MetricDirection, MetricProvenance, SampleSizeInfo
from backend.app.schemas.scoring import ReliabilityStatus


class ComparisonCompatibilityStatus(str, Enum):
    """Compatibility grade for multi-player comparison."""

    FULLY_COMPATIBLE = "FULLY_COMPATIBLE"  # Identical role and cohort
    CROSS_ROLE_PARTIAL = "CROSS_ROLE_PARTIAL"  # Different roles; separate profiles shown
    INCOMPATIBLE_COHORTS = "INCOMPATIBLE_COHORTS"  # Incompatible tournament contexts


class MetricComparisonItem(BaseModel):
    """Direct head-to-head metric comparison with directional advantage attribution."""

    metric_id: str
    display_name: str
    directionality: MetricDirection
    unit: str = ""
    player_values: dict[str, float | int | None] = Field(default_factory=dict)
    player_percentiles: dict[str, float | None] = Field(default_factory=dict)
    absolute_difference: float | None = None
    relative_difference_pct: float | None = None
    favorable_player_id: str | None = None  # Player with statistical advantage respecting directionality
    favorable_player_name: str | None = None
    notes: str = ""


class DimensionComparisonItem(BaseModel):
    """Dimension-level comparison between candidates."""

    dimension_id: str
    dimension_name: str
    player_dimension_scores: dict[str, float] = Field(default_factory=dict)
    score_difference: float | None = None
    favorable_player_id: str | None = None
    metrics: list[MetricComparisonItem] = Field(default_factory=list)


class PlayerComparisonRequest(BaseModel):
    """Payload to initiate a player comparison."""

    player_ids: list[str] = Field(min_length=2, max_length=5, description="2 to 5 player IDs to compare")
    run_id: str | None = None
    dataset_id: str | None = None


class PlayerComparisonHeader(BaseModel):
    """Summary player metadata for comparison columns."""

    player_id: str
    player_name: str
    role: PlayerRole
    cohort_id: str
    vor_score: float
    raw_composite_score: float
    reliability_factor: float
    reliability_status: ReliabilityStatus
    sample_size: SampleSizeInfo


class PlayerComparisonResponse(BaseModel):
    """Complete multi-player comparison result with difference analysis."""

    comparison_id: str
    created_at: str
    compatibility_status: ComparisonCompatibilityStatus
    compatibility_notes: list[str] = Field(default_factory=list)
    players: list[PlayerComparisonHeader] = Field(default_factory=list)
    is_cross_role: bool
    vor_comparison_valid: bool
    vor_leader_id: str | None = None
    shared_dimensions: list[DimensionComparisonItem] = Field(default_factory=list)
    batting_comparison: list[MetricComparisonItem] = Field(default_factory=list)
    bowling_comparison: list[MetricComparisonItem] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)
    provenance: MetricProvenance


class ComparisonMetadataResponse(BaseModel):
    """Supported comparison rules, allowed player counts, and compatibility standards."""

    max_players_allowed: int = 5
    supported_roles: list[str]
    compatibility_rules: list[str]
    tie_breaking_rules: list[str]
    directionality_conventions: dict[str, str]
