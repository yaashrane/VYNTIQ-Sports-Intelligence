"""Pydantic schemas for player role classification, sample adequacy, and evaluation profiles."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
from backend.app.schemas.metrics import (
    MetricProvenance,
    MetricValue,
    SampleSizeInfo,
)


class PlayerRole(str, Enum):
    """Cricketing playing roles recognized by the evaluation engine."""

    BATTER = "BATTER"
    BOWLER = "BOWLER"
    ALL_ROUNDER = "ALL_ROUNDER"
    WICKETKEEPER = "WICKETKEEPER"
    UNKNOWN = "UNKNOWN"


class RoleClassificationStatus(str, Enum):
    """Certainty and origin status of the assigned player role."""

    CONFIRMED_FROM_SOURCE = "CONFIRMED_FROM_SOURCE"
    CLASSIFIED_FROM_DATA = "CLASSIFIED_FROM_DATA"
    AMBIGUOUS = "AMBIGUOUS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"


class SampleAdequacyStatus(str, Enum):
    """Reliability categorization based strictly on volume of participation."""

    ADEQUATE = "ADEQUATE"
    LIMITED = "LIMITED"
    INSUFFICIENT = "INSUFFICIENT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DimensionAvailabilityStatus(str, Enum):
    """Availability status of an entire evaluation dimension."""

    AVAILABLE = "AVAILABLE"
    LIMITED = "LIMITED"
    INSUFFICIENT = "INSUFFICIENT"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"


class RoleClassificationResult(BaseModel):
    """Detailed role classification breakdown with audit provenance."""

    player_id: str
    assigned_role: PlayerRole
    source_role: str | None = None
    status: RoleClassificationStatus
    classification_method: str
    supporting_evidence: dict[str, Any] = Field(default_factory=dict)
    missing_information: list[str] = Field(default_factory=list)
    confidence: str = "PROVISIONAL"
    classification_version: str = "1.0.0"


class DimensionEvaluationProfile(BaseModel):
    """Collection of calculated metrics for an evaluation dimension with adequacy status."""

    dimension_id: str
    dimension_name: str
    status: DimensionAvailabilityStatus
    metrics: list[MetricValue] = Field(default_factory=list)
    interpretation: str = ""


class DisciplineSampleAdequacy(BaseModel):
    """Sample volume grading for batting and bowling disciplines."""

    batting: SampleAdequacyStatus
    bowling: SampleAdequacyStatus
    overall: SampleAdequacyStatus
    summary: str


class PlayerEvaluationResponse(BaseModel):
    """Complete role-specific evaluation profile for a single player."""

    player_id: str
    player_name: str
    role: RoleClassificationResult
    sample_size: SampleSizeInfo
    sample_adequacy: DisciplineSampleAdequacy
    evaluation_profile: dict[str, DimensionEvaluationProfile]
    data_quality_status: str = "VERIFIED"
    evaluation_version: str = "1.0.0"
    provenance: MetricProvenance


class DatasetEvaluationResponse(BaseModel):
    """Dataset-wide role classification and evaluation response."""

    dataset_id: str
    total_evaluated_players: int
    players: list[PlayerEvaluationResponse] = Field(default_factory=list)
    role_distribution: dict[str, int] = Field(default_factory=dict)
    provenance: MetricProvenance


class DimensionRegistryEntry(BaseModel):
    """Metadata entry cataloging an evaluation dimension."""

    dimension_id: str
    display_name: str
    description: str
    applicable_roles: list[str]
    associated_metrics: list[str]
    interpretation: str
    required_data_fields: list[str]
    sample_requirements: str
    limitations: str
