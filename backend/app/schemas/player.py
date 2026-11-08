"""Pydantic schemas for canonical athlete master records."""

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class PlayerMasterResponse(BaseModel):
    """Canonical athlete master entity representation."""

    model_config = ConfigDict(from_attributes=True)

    player_id: str
    canonical_name: str
    primary_role: str | None = None
    batting_hand: str | None = None
    bowling_style: str | None = None
    nationality: str | None = None
    dob: date | str | None = None
    is_eligible: bool = True
    created_at: datetime | str
    updated_at: datetime | str


class PlayerListResponse(BaseModel):
    """Paginated collection of player records."""

    total: int
    limit: int
    offset: int
    players: list[PlayerMasterResponse] = Field(default_factory=list)
