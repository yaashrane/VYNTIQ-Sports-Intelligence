"""Pydantic schemas for workspaces, competition configurations, shortlists, reviews, and audit trails."""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class WorkspaceStatus(str, Enum):
    """Lifecycle state of an analytical workspace."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class SportType(str, Enum):
    """Supported sport categories within VYNTIQ."""

    CRICKET = "CRICKET"


class ReviewStatus(str, Enum):
    """Scout/analyst review workflow disposition."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class EligibilityStatus(str, Enum):
    """Player eligibility evaluation status."""

    ELIGIBLE = "ELIGIBLE"
    EXCLUDED = "EXCLUDED"
    CONDITIONALLY_ELIGIBLE = "CONDITIONALLY_ELIGIBLE"


# ==============================================================================
# CONFIGURATION SCHEMAS
# ==============================================================================

class AgeCriteria(BaseModel):
    """Optional age restrictions for competition entry."""

    model_config = ConfigDict(from_attributes=True)

    min_age: int | None = Field(default=None, ge=12, le=55, description="Minimum age in years")
    max_age: int | None = Field(default=None, ge=12, le=55, description="Maximum age in years")
    age_cutoff_date: str | None = Field(
        default=None, description="ISO-8601 date (YYYY-MM-DD) for age determination"
    )


class ParticipationCriteria(BaseModel):
    """Optional sample/participation thresholds for eligibility."""

    model_config = ConfigDict(from_attributes=True)

    min_matches: int | None = Field(default=None, ge=1, description="Minimum matches participated")
    min_balls_faced: int | None = Field(
        default=None, ge=0, description="Minimum balls faced for batting consideration"
    )
    min_legal_balls_bowled: int | None = Field(
        default=None, ge=0, description="Minimum legal balls bowled for bowling consideration"
    )


class CompetitionConfigCreate(BaseModel):
    """Creation payload for workspace evaluation & eligibility rules."""

    model_config = ConfigDict(from_attributes=True)

    target_sport: SportType = Field(default=SportType.CRICKET, description="Target sport category")
    target_roles: list[str] = Field(
        default_factory=lambda: ["BATTER", "BOWLER", "ALL_ROUNDER", "WICKETKEEPER"],
        description="Player roles eligible for this competition",
    )
    age_criteria: AgeCriteria | None = Field(
        default=None, description="Optional age limits"
    )
    participation_criteria: ParticipationCriteria | None = Field(
        default=None, description="Optional minimum workload thresholds"
    )
    required_metrics: list[str] = Field(
        default_factory=list, description="Mandatory metric IDs that must be present"
    )
    evaluation_profile_version: str = Field(
        default="1.0.0", description="Methodology version for scoring weights"
    )
    shortlist_size: int = Field(
        default=10, ge=1, le=100, description="Default target shortlist size"
    )
    custom_eligibility_rules: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary custom domain rules (e.g. nationality)"
    )
    dataset_ids: list[str] = Field(
        default_factory=list, description="Associated dataset IDs"
    )


class CompetitionConfigUpdate(BaseModel):
    """Update payload for workspace configuration."""

    target_roles: list[str] | None = None
    age_criteria: AgeCriteria | None = None
    participation_criteria: ParticipationCriteria | None = None
    required_metrics: list[str] | None = None
    evaluation_profile_version: str | None = None
    shortlist_size: int | None = Field(default=None, ge=1, le=100)
    custom_eligibility_rules: dict[str, Any] | None = None
    dataset_ids: list[str] | None = None


class CompetitionConfigResponse(BaseModel):
    """Response payload detailing workspace configuration."""

    model_config = ConfigDict(from_attributes=True)

    config_id: str
    workspace_id: str
    target_sport: str
    target_roles: list[str]
    age_criteria: AgeCriteria | None
    participation_criteria: ParticipationCriteria | None
    required_metrics: list[str]
    evaluation_profile_version: str
    shortlist_size: int
    custom_eligibility_rules: dict[str, Any]
    dataset_ids: list[str]
    version: str
    created_at: datetime | str
    updated_at: datetime | str


# ==============================================================================
# WORKSPACE SCHEMAS
# ==============================================================================

class WorkspaceCreate(BaseModel):
    """Payload to create an independent competition workspace."""

    workspace_id: str | None = Field(
        default=None,
        description="Explicit identifier (e.g. workspace_super_rr_s2). Generated if omitted.",
        max_length=64,
    )
    name: str = Field(
        ..., min_length=1, max_length=128, description="Descriptive workspace title"
    )
    description: str | None = Field(
        default=None, description="Optional analytical scope and background"
    )
    sport_type: SportType = Field(default=SportType.CRICKET, description="Target sport")
    competition_name: str = Field(
        ..., min_length=1, max_length=128, description="Competition/tournament title"
    )
    season_or_edition: str = Field(
        ..., min_length=1, max_length=64, description="Season or edition tag (e.g. Season 2)"
    )
    initial_configuration: CompetitionConfigCreate | None = Field(
        default=None, description="Optional embedded configuration"
    )
    dataset_references: list[str] = Field(
        default_factory=list, description="Initial dataset IDs associated with workspace"
    )


class WorkspaceUpdate(BaseModel):
    """Payload to modify workspace metadata or status."""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    competition_name: str | None = Field(default=None, min_length=1, max_length=128)
    season_or_edition: str | None = Field(default=None, min_length=1, max_length=64)
    status: WorkspaceStatus | None = None
    dataset_references: list[str] | None = None


class WorkspaceResponse(BaseModel):
    """Standard workspace summary response."""

    model_config = ConfigDict(from_attributes=True)

    workspace_id: str
    name: str
    description: str | None
    sport_type: str
    competition_name: str
    season_or_edition: str
    status: WorkspaceStatus
    dataset_references: list[str]
    created_at: datetime | str
    updated_at: datetime | str


class WorkspaceDetailResponse(WorkspaceResponse):
    """Comprehensive workspace detail including its active configuration."""

    configuration: CompetitionConfigResponse | None = None
    shortlists_count: int = 0


# ==============================================================================
# SHORTLIST SCHEMAS
# ==============================================================================

class ShortlistGenerateRequest(BaseModel):
    """Request payload to generate a candidate shortlist."""

    name: str = Field(
        default="Official Candidate Shortlist",
        min_length=1,
        max_length=128,
        description="Name of this shortlist iteration",
    )
    dataset_id: str = Field(..., description="Target dataset identifier to evaluate")
    scoring_run_id: str | None = Field(
        default=None,
        description="Explicit scoring run ID. If omitted, uses latest scoring run for dataset.",
    )
    override_shortlist_size: int | None = Field(
        default=None, ge=1, le=100, description="Optional override of default shortlist size"
    )
    override_roles: list[str] | None = Field(
        default=None, description="Optional override of target roles for this specific run"
    )


class ShortlistCandidateItem(BaseModel):
    """Individual player record within a generated shortlist."""

    model_config = ConfigDict(from_attributes=True)

    candidate_entry_id: str
    shortlist_id: str
    workspace_id: str
    player_id: str
    player_name: str
    assigned_role: str
    rank: int
    vor_score: float
    raw_composite_score: float
    reliability_factor: float
    reliability_status: str
    evaluation_ref: str
    explainability_ref: str
    eligibility_status: EligibilityStatus
    review_status: ReviewStatus
    reviewer_notes: str | None = None
    selection_timestamp: datetime | str


class ShortlistSummaryResponse(BaseModel):
    """Summary of a generated shortlist."""

    model_config = ConfigDict(from_attributes=True)

    shortlist_id: str
    workspace_id: str
    name: str
    dataset_id: str
    scoring_run_id: str
    config_version: str
    methodology_version: str
    target_size: int
    eligible_count: int
    excluded_count: int
    shortlisted_count: int
    status: str
    created_at: datetime | str


class ShortlistResponse(ShortlistSummaryResponse):
    """Full detail of a shortlist including candidates and exclusion summary."""

    candidates: list[ShortlistCandidateItem] = Field(default_factory=list)
    exclusion_summary: dict[str, list[str]] = Field(
        default_factory=dict, description="Player ID to list of machine-readable exclusion reasons"
    )


class ShortlistReviewRequest(BaseModel):
    """Payload for reviewer decisions on a candidate."""

    review_status: ReviewStatus = Field(
        ..., description="Updated disposition: APPROVED, REJECTED, NEEDS_REVIEW, PENDING"
    )
    reviewer_notes: str | None = Field(
        default=None, description="Scouting notes or rationale for the status update"
    )


class ShortlistAuditResponse(BaseModel):
    """Audit log verifying generation parameters and reproducible methodology."""

    model_config = ConfigDict(from_attributes=True)

    audit_id: str
    shortlist_id: str
    workspace_id: str
    dataset_id: str
    configuration_version: str
    evaluation_methodology_version: str
    metric_registry_version: str
    ranking_engine_version: str
    generation_timestamp: datetime | str
    eligible_candidate_count: int
    excluded_candidate_count: int
    shortlisted_candidate_count: int
    exclusion_details: dict[str, list[str]]
