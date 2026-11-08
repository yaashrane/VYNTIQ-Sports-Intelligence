"""API endpoints for multi-player comparison, head-to-head metrics, and difference analysis."""

from fastapi import APIRouter, status
from backend.app.schemas.comparison import (
    ComparisonMetadataResponse,
    PlayerComparisonRequest,
    PlayerComparisonResponse,
)
from backend.app.services.comparison.service import PlayerComparisonService

router = APIRouter(prefix="/comparisons", tags=["Player Comparison Engine"])


@router.get(
    "/metadata",
    response_model=ComparisonMetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Comparison Engine Metadata",
    description="Retrieve supported comparison rules, allowed player limits, and metric directionality conventions.",
)
async def get_comparison_metadata() -> ComparisonMetadataResponse:
    """Return comparison engine guidelines, role rules, and directionality metadata."""
    service = PlayerComparisonService()
    return service.get_metadata()


@router.post(
    "/players",
    response_model=PlayerComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare Two or More Players",
    description="Execute head-to-head or multi-player comparison (2 to 5 players) with directional advantage analysis.",
)
async def compare_players(request: PlayerComparisonRequest) -> PlayerComparisonResponse:
    """Execute multi-player comparison across requested player IDs."""
    service = PlayerComparisonService()
    return service.compare_players(request)


@router.get(
    "/{comparison_id}",
    response_model=PlayerComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Stored Comparison Result",
    description="Retrieve a previously calculated player comparison by comparison ID.",
)
async def get_comparison(comparison_id: str) -> PlayerComparisonResponse:
    """Fetch stored player comparison results."""
    service = PlayerComparisonService()
    return service.get_comparison(comparison_id)
