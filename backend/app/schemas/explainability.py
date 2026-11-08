"""Pydantic schemas for VOR score explainability, factor attribution, and mathematical audit."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
from backend.app.schemas.evaluation import PlayerRole
from backend.app.schemas.metrics import MetricDirection, MetricProvenance, SampleSizeInfo
from backend.app.schemas.scoring import ReliabilityStatus


class ExplanationStatus(str, Enum):
    """Integrity and completeness status of the explanation output."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNAVAILABLE = "UNAVAILABLE"


class MetricContributionDetail(BaseModel):
    """Detailed audit trace for a single metric's contribution to the composite score."""

    metric_id: str
    display_name: str
    raw_value: float | int | None
    normalized_percentile: float
    directionality: MetricDirection
    dimension_id: str
    metric_weight_in_dimension: float
    contribution_to_dimension: float
    calculation_status: str
    normalization_method: str
    is_missing_or_fallback: bool


class DimensionContributionDetail(BaseModel):
    """Audit breakdown for an evaluation dimension and its mathematical weight."""

    dimension_id: str
    dimension_name: str
    dimension_score: float  # [0.0, 100.0]
    applied_weight: float  # [0.0, 1.0]
    contribution_to_raw_composite: float  # dimension_score * applied_weight
    metrics: list[MetricContributionDetail] = Field(default_factory=list)
    sample_adequacy: str
    is_limited: bool


class PlayerScoreBreakdownResponse(BaseModel):
    """Full metric-level and dimension-level contribution audit reconciling with VOR."""

    player_id: str
    player_name: str
    role: PlayerRole
    cohort_id: str
    run_id: str
    dataset_id: str
    final_vor: float
    raw_composite_score: float
    reliability_factor: float
    reliability_status: ReliabilityStatus
    sum_of_dimension_contributions: float  # Must reconcile with raw_composite_score
    reconciliation_discrepancy: float  # abs(raw_composite - sum_contributions)
    dimensions: list[DimensionContributionDetail] = Field(default_factory=list)
    scoring_version: str = "1.0.0"


class PlayerDetailedExplanationResponse(BaseModel):
    """Comprehensive, explainable intelligence dossier for a player's performance rating."""

    player_id: str
    player_name: str
    role: PlayerRole
    status: ExplanationStatus
    cohort_id: str
    run_id: str
    dataset_id: str
    final_vor: float
    raw_composite_score: float
    reliability_factor: float
    reliability_status: ReliabilityStatus
    sample_size: SampleSizeInfo
    top_strengths: list[str] = Field(default_factory=list)
    drag_factors: list[str] = Field(default_factory=list)
    areas_of_insufficient_evidence: list[str] = Field(default_factory=list)
    excluded_or_unsupported_metrics: list[dict[str, str]] = Field(default_factory=list)
    narrative_summary: str
    provenance: MetricProvenance

