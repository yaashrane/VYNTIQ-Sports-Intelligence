"""Relational models for competition workspaces, configurations, shortlists, candidates, and audit logs.

Complies strictly with ADR-001 (shared tables with workspace_id scoping) and Prompt 09.
"""

from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TimestampMixin


class Workspace(Base, TimestampMixin):
    """Competition workspace / analytical sandbox container."""

    __tablename__ = "workspaces"

    workspace_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sport_type: Mapped[str] = mapped_column(String(32), default="CRICKET", nullable=False)
    competition_name: Mapped[str] = mapped_column(String(128), nullable=False)
    season_or_edition: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="DRAFT", nullable=False, index=True
    )  # DRAFT, ACTIVE, COMPLETED, ARCHIVED
    dataset_references: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )


class WorkspaceConfiguration(Base, TimestampMixin):
    """Configurable evaluation and eligibility rules for a specific competition workspace."""

    __tablename__ = "workspace_configurations"

    config_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    target_sport: Mapped[str] = mapped_column(String(32), default="CRICKET", nullable=False)
    target_roles: Mapped[list[str]] = mapped_column(
        JSON,
        default=lambda: ["BATTER", "BOWLER", "ALL_ROUNDER", "WICKETKEEPER"],
        nullable=False,
    )
    min_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_cutoff_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    min_matches: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_balls_faced: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_legal_balls_bowled: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_metrics: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    evaluation_profile_version: Mapped[str] = mapped_column(
        String(32), default="1.0.0", nullable=False
    )
    shortlist_size: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    custom_eligibility_rules: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )
    dataset_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)


class Shortlist(Base, TimestampMixin):
    """Generated player shortlist for an active workspace."""

    __tablename__ = "shortlists"

    shortlist_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(64), nullable=False)
    scoring_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    config_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    methodology_version: Mapped[str] = mapped_column(
        String(32), default="1.0.0", nullable=False
    )
    target_size: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    eligible_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    excluded_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shortlisted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="GENERATED", nullable=False, index=True
    )  # GENERATED, REVIEWED, FINALIZED


class ShortlistCandidate(Base):
    """Individual candidate player selected into a shortlist."""

    __tablename__ = "shortlist_candidates"

    candidate_entry_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    shortlist_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    player_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    player_name: Mapped[str] = mapped_column(String(128), nullable=False)
    assigned_role: Mapped[str] = mapped_column(String(32), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    vor_score: Mapped[float] = mapped_column(Float, nullable=False)
    raw_composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    reliability_factor: Mapped[float] = mapped_column(Float, nullable=False)
    reliability_status: Mapped[str] = mapped_column(String(32), nullable=False)
    evaluation_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    explainability_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    eligibility_status: Mapped[str] = mapped_column(
        String(32), default="ELIGIBLE", nullable=False
    )
    review_status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False, index=True
    )  # PENDING, APPROVED, REJECTED, NEEDS_REVIEW
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    selection_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ShortlistAuditLog(Base):
    """Immutable audit log recording parameters and exclusion reasons for a shortlist run."""

    __tablename__ = "shortlist_audit_logs"

    audit_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    shortlist_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    workspace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    dataset_id: Mapped[str] = mapped_column(String(64), nullable=False)
    configuration_version: Mapped[str] = mapped_column(String(32), nullable=False)
    evaluation_methodology_version: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    metric_registry_version: Mapped[str] = mapped_column(String(32), nullable=False)
    ranking_engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    generation_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    eligible_candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    excluded_candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    shortlisted_candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    exclusion_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

