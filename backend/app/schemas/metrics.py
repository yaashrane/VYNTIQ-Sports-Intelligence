"""Schemas for individual cricket metric values, calculation statuses, and sample tracking."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class MetricStatus(str, Enum):
    """Standardized calculation outcome status."""

    CALCULATED = "CALCULATED"
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    DIVIDE_BY_ZERO_SAFEGUARD = "DIVIDE_BY_ZERO_SAFEGUARD"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    OPEN_DEFINITION = "OPEN_DEFINITION"


class MetricDirection(str, Enum):
    """Interpretive directionality for analytics and scouting."""

    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    NEUTRAL = "NEUTRAL"


class MetricCategory(str, Enum):
    """Discipline category for cricket performance metrics."""

    BATTING = "BATTING"
    BOWLING = "BOWLING"
    FIELDING = "FIELDING"
    ADVANCED = "ADVANCED"


class SampleSizeInfo(BaseModel):
    """Granular sample volume context for statistical reliability."""

    balls_faced: int = 0
    batting_innings: int = 0
    times_dismissed: int = 0
    legal_balls_bowled: int = 0
    overs_bowled: float = 0.0
    bowling_innings: int = 0
    matches_played: int = 0


class MetricProvenance(BaseModel):
    """Lineage and audit metadata for reproducible calculations."""

    dataset_id: str
    calculation_version: str = "1.0.0"
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    calculated_at: str | None = None


class MetricValue(BaseModel):
    """Standardized envelope for any calculated cricket metric."""

    metric_id: str
    display_name: str
    value: float | int | None = None
    status: MetricStatus = MetricStatus.CALCULATED
    sample_size: int = 0
    sample_units: str = "balls"
    directionality: MetricDirection = MetricDirection.HIGHER_IS_BETTER
    context: dict[str, Any] = Field(default_factory=dict)


class MetricRegistryEntry(BaseModel):
    """Catalog entry describing a cricket metric in the system registry."""

    metric_id: str
    name: str
    category: MetricCategory
    description: str
    directionality: MetricDirection
    formula: str
    required_source_fields: list[str] = Field(default_factory=list)
    unit: str = ""
    applicable_roles: list[str] = Field(default_factory=list)
    minimum_sample_recommendation: int | None = None
    sample_units: str = "balls"
    availability_status: MetricStatus = MetricStatus.CALCULATED
    limitations: str
    is_standard_ball_by_ball: bool = True
