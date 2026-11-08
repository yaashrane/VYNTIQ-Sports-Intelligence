"""Schemas for analytics queries, metric calculation responses, and dimension summaries."""

from typing import Any
from pydantic import BaseModel, Field
from backend.app.schemas.metrics import (
    MetricProvenance,
    MetricRegistryEntry,
    MetricValue,
    SampleSizeInfo,
)


class MetricCalculationFilter(BaseModel):
    """Filter criteria for selective delivery aggregation."""

    player_ids: list[str] | None = None
    match_ids: list[str] | None = None
    seasons: list[str] | None = None
    phases: list[str] | None = None  # POWERPLAY, MIDDLE, DEATH
    innings_nums: list[int] | None = None  # 1, 2


class MetricCalculationRequest(BaseModel):
    """Payload to trigger on-demand metric calculation for a dataset."""

    dataset_id: str
    filters: MetricCalculationFilter | None = None
    player_id: str | None = None
    include_dimensions: bool = True


class DimensionGroup(BaseModel):
    """Thematic cluster of performance metrics for an evaluation dimension."""

    dimension_id: str
    dimension_name: str
    metrics: dict[str, MetricValue] = Field(default_factory=dict)


class PlayerMetricsSummary(BaseModel):
    """Consolidated performance profile for a player across disciplines and dimensions."""

    player_id: str
    player_name: str
    sample_size: SampleSizeInfo
    batting_metrics: dict[str, MetricValue] = Field(default_factory=dict)
    bowling_metrics: dict[str, MetricValue] = Field(default_factory=dict)
    batting_dimensions: dict[str, DimensionGroup] = Field(default_factory=dict)
    bowling_dimensions: dict[str, DimensionGroup] = Field(default_factory=dict)
    provenance: MetricProvenance


class CalculationResponse(BaseModel):
    """Standardized response from the calculation engine."""

    dataset_id: str
    total_players_computed: int
    players: list[PlayerMetricsSummary] = Field(default_factory=list)
    provenance: MetricProvenance


class DatasetMetricsSummaryResponse(BaseModel):
    """High-level aggregate summary of metrics computable across an entire dataset."""

    dataset_id: str
    total_deliveries: int
    total_matches: int
    total_batters: int
    total_bowlers: int
    total_runs_scored: int
    total_wickets_fallen: int
    overall_run_rate: float
    boundary_percentage_runs: float
    dot_ball_percentage: float
    provenance: MetricProvenance


class MetricRegistryResponse(BaseModel):
    """Response payload listing all metrics registered in the system."""

    total_metrics: int
    metrics: list[MetricRegistryEntry]
