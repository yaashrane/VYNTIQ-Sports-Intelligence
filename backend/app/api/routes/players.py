"""API routes for canonical athlete discovery and master record lookup."""

from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.dependencies import get_db
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.models.cricket import Player
from backend.app.schemas.player import PlayerListResponse, PlayerMasterResponse

router = APIRouter(prefix="/players", tags=["Players & Athlete Master"])


@router.get(
    "",
    response_model=PlayerListResponse,
    status_code=status.HTTP_200_OK,
    summary="List and Search Players",
    description="Retrieve paginated canonical athlete master records with optional search and role filtering.",
)
async def list_players(
    session: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = Query(default=None, description="Search by player name"),
    role: str | None = Query(default=None, description="Filter by primary role (BATTER, BOWLER, ALL_ROUNDER, WICKETKEEPER)"),
    is_eligible: bool | None = Query(default=None, description="Filter by eligibility flag"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> PlayerListResponse:
    """Search and filter canonical player master records."""
    query = select(Player)
    count_query = select(func.count(Player.player_id))

    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.where(Player.canonical_name.ilike(search_term))
        count_query = count_query.where(Player.canonical_name.ilike(search_term))

    if role and role.strip():
        role_term = role.strip().upper()
        query = query.where(Player.primary_role == role_term)
        count_query = count_query.where(Player.primary_role == role_term)

    if is_eligible is not None:
        query = query.where(Player.is_eligible == is_eligible)
        count_query = count_query.where(Player.is_eligible == is_eligible)

    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(Player.canonical_name.asc()).limit(limit).offset(offset)
    result = await session.execute(query)
    players = list(result.scalars().all())

    return PlayerListResponse(
        total=total,
        limit=limit,
        offset=offset,
        players=[
            PlayerMasterResponse(
                player_id=p.player_id,
                canonical_name=p.canonical_name,
                primary_role=p.primary_role,
                batting_hand=p.batting_hand,
                bowling_style=p.bowling_style,
                nationality=p.nationality,
                dob=p.dob,
                is_eligible=p.is_eligible,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in players
        ],
    )


@router.get(
    "/{player_id}",
    response_model=PlayerMasterResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Player Master Record",
    description="Retrieve canonical biographical and master details for an athlete by identifier.",
)
async def get_player(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PlayerMasterResponse:
    """Fetch individual player master record."""
    player = await session.get(Player, player_id)
    if not player:
        raise EntityNotFoundException("Player", player_id)

    return PlayerMasterResponse(
        player_id=player.player_id,
        canonical_name=player.canonical_name,
        primary_role=player.primary_role,
        batting_hand=player.batting_hand,
        bowling_style=player.bowling_style,
        nationality=player.nationality,
        dob=player.dob,
        is_eligible=player.is_eligible,
        created_at=player.created_at,
        updated_at=player.updated_at,
    )
