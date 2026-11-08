"""Canonical relational models for cricket performance analytics.

Complies strictly with docs/DATA_DICTIONARY.md specifications.
"""

from datetime import date
from sqlalchemy import Boolean, Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TimestampMixin


class Player(Base, TimestampMixin):
    """Canonical athlete master record."""

    __tablename__ = "players"

    player_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    primary_role: Mapped[str | None] = mapped_column(String(32), nullable=True)  # BATTER, BOWLER, ALL_ROUNDER, WICKETKEEPER
    batting_hand: Mapped[str | None] = mapped_column(String(16), nullable=True)
    bowling_style: Mapped[str | None] = mapped_column(String(32), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Team(Base, TimestampMixin):
    """Team master entity record."""

    __tablename__ = "teams"

    team_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_name: Mapped[str] = mapped_column(String(128), nullable=False)
    short_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    competition: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class Venue(Base, TimestampMixin):
    """Stadium and pitch location master record."""

    __tablename__ = "venues"

    venue_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    venue_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scoring_index: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)


class Match(Base, TimestampMixin):
    """Fixture record linking teams, venue, and workspace lineage."""

    __tablename__ = "matches"

    match_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    match_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    season: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    venue_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    team1_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    team2_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    toss_winner_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    toss_decision: Mapped[str | None] = mapped_column(String(16), nullable=True)
    winner_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dls_affected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Innings(Base, TimestampMixin):
    """Aggregated innings-level score and boundary summary."""

    __tablename__ = "innings"

    innings_id: Mapped[str] = mapped_column(String(64), primary_key=True)  # {match_id}_inn_{innings_num}
    match_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    innings_num: Mapped[int] = mapped_column(Integer, nullable=False)
    batting_team_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bowling_team_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_wickets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_legal_balls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Delivery(Base, TimestampMixin):
    """Atomic ball-by-ball performance and telemetry event."""

    __tablename__ = "deliveries"

    delivery_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    dataset_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    origin_type: Mapped[str] = mapped_column(
        String(32), default="COMPETITION_SANDBOX", nullable=False
    )
    match_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    innings_num: Mapped[int] = mapped_column(Integer, nullable=False)
    over_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 to 19
    ball_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 6+
    over_delivery: Mapped[float] = mapped_column(Float, nullable=False)  # e.g. 18.4
    phase: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # POWERPLAY, MIDDLE, DEATH
    batter_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    bowler_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    non_striker_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    batter_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extras_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extras_type: Mapped[str | None] = mapped_column(String(16), nullable=True)  # WIDE, NO_BALL, etc.
    is_legal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    total_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_wicket: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dismissed_player_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dismissal_kind: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_super_over: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
