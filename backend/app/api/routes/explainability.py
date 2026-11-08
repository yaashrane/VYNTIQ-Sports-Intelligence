"""API endpoints for player score explainability and mathematical factor breakdown."""

from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from backend.app.schemas.explainability import (
    PlayerDetailedExplanationResponse,
    PlayerScoreBreakdownResponse,
)
from backend.app.services.explainability.service import ExplainabilityService

router = APIRouter(prefix="/explainability", tags=["Explainability & Factor Attribution"])


@router.get(
    "/players/{player_id}",
    response_model=PlayerDetailedExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Detailed Player Score Explanation",
    description="Retrieve comprehensive explanation decomposing VOR score into top strengths, drag factors, and sample reliability.",
)
async def get_player_explanation(
    player_id: str,
    run_id: str | None = Query(default=None, description="Optional scoring run ID"),
) -> PlayerDetailedExplanationResponse:
    """Fetch detailed explainable intelligence narrative for a player."""
    service = ExplainabilityService()
    return service.generate_player_explanation(player_id, run_id)


@router.get(
    "/players/{player_id}/breakdown",
    response_model=PlayerScoreBreakdownResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Mathematical Score Breakdown",
    description="Retrieve metric-level and dimension-level contributions that mathematically reconcile with the raw composite and final VOR score.",
)
async def get_score_breakdown(
    player_id: str,
    run_id: str | None = Query(default=None, description="Optional scoring run ID"),
) -> PlayerScoreBreakdownResponse:
    """Fetch mathematical contribution audit for a player's VOR score."""
    service = ExplainabilityService()
    return service.get_score_breakdown(player_id, run_id)
