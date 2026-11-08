"""API endpoints for VOR composite scoring, ECDF percentile rankings, and methodology lookup."""

from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.dependencies import get_db
from backend.app.schemas.scoring import (
    PlayerScoreResult,
    RankingResponse,
    ScoringCalculationRequest,
    ScoringMethodologyResponse,
    ScoringRunResponse,
)
from backend.app.services.scoring.service import ScoringService

router = APIRouter(prefix="/scoring", tags=["Scoring & Player Rankings (VOR)"])


@router.get(
    "/methodology",
    response_model=ScoringMethodologyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Scoring Methodology & Active Configuration",
    description="Retrieve approved VOR mathematical formulas, ECDF parameters, Bayesian shrinkage thresholds, and role weights.",
)
async def get_scoring_methodology() -> ScoringMethodologyResponse:
    """Return active scoring engine configuration and mathematical specifications."""
    service = ScoringService()
    return service.get_methodology()


@router.post(
    "/calculate",
    response_model=ScoringRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute VOR Scoring Run",
    description="Compute ECDF percentiles, Bayesian reliability shrinkage, and VOR composite ratings for players in a dataset.",
)
async def calculate_scores(
    request: ScoringCalculationRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ScoringRunResponse:
    """Execute complete scoring pipeline across a stored dataset."""
    service = ScoringService()
    return await service.calculate_for_dataset(session, request)


@router.get(
    "/runs/{run_id}",
    response_model=ScoringRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Scoring Run Details",
    description="Retrieve full execution output and scored player roster for a specific run ID.",
)
async def get_scoring_run(run_id: str) -> ScoringRunResponse:
    """Lookup a historical or cached scoring run."""
    service = ScoringService()
    return service.get_run(run_id)


@router.get(
    "/players/{player_id}",
    response_model=PlayerScoreResult,
    status_code=status.HTTP_200_OK,
    summary="Get Player VOR Score & Explanation",
    description="Retrieve player composite rating, factor attribution (strengths/drags), and sample reliability breakdown.",
)
async def get_player_score(
    player_id: str,
    run_id: str | None = Query(default=None, description="Optional scoring run ID"),
) -> PlayerScoreResult:
    """Lookup player evaluation score and audit explanation."""
    service = ScoringService()
    return service.get_player_score(player_id, run_id)


@router.get(
    "/rankings",
    response_model=RankingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Ranked Leaderboards",
    description="Retrieve official ranked leaderboard implementing multi-criteria tie-breaking and qualification quarantine.",
)
async def get_rankings(
    run_id: str | None = Query(default=None, description="Optional scoring run ID"),
    role: str | None = Query(default=None, description="Filter leaderboard by role (BATTER, BOWLER, ALL_ROUNDER, WICKETKEEPER)"),
) -> RankingResponse:
    """Generate ranked player leaderboard for the specified run and role cohort."""
    service = ScoringService()
    return service.get_rankings(run_id=run_id, role_filter=role)
