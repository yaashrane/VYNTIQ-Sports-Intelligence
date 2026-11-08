"""API endpoints for player role classification and role-specific evaluation profiles."""

from typing import Annotated
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.dependencies import get_db
from backend.app.schemas.evaluation import (
    DatasetEvaluationResponse,
    DimensionRegistryEntry,
    PlayerEvaluationResponse,
    RoleClassificationResult,
)
from backend.app.services.evaluation.registry import get_all_evaluation_dimensions
from backend.app.services.evaluation.service import EvaluationService

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Role Classification"])


class ClassifyDatasetRequest(BaseModel):
    """Payload to trigger role classification across a dataset."""

    dataset_id: str


class EvaluationDimensionsResponse(BaseModel):
    """Response payload listing registered evaluation dimensions."""

    total_dimensions: int
    dimensions: list[DimensionRegistryEntry]


@router.get(
    "/dimensions",
    response_model=EvaluationDimensionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Evaluation Dimensions Registry",
    description="Retrieve all registered role-specific evaluation dimensions and metadata.",
)
async def get_dimensions() -> EvaluationDimensionsResponse:
    """Return all evaluation dimensions from the registry."""
    dims = get_all_evaluation_dimensions()
    return EvaluationDimensionsResponse(
        total_dimensions=len(dims),
        dimensions=dims,
    )


@router.post(
    "/classify",
    response_model=list[RoleClassificationResult],
    status_code=status.HTTP_200_OK,
    summary="Classify Player Roles for Dataset",
    description="Identify and classify playing roles for all players in a validated dataset with supporting evidence.",
)
async def classify_players(
    request: ClassifyDatasetRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[RoleClassificationResult]:
    """Execute evidence-based role classification for all players in the dataset."""
    service = EvaluationService()
    return await service.classify_players_from_db(session, request.dataset_id)


@router.get(
    "/players/{player_id}",
    response_model=PlayerEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Player Role & Evaluation Profile",
    description="Retrieve assigned cricketing role, sample adequacy, and structured dimension evaluation profile for a player.",
)
async def get_player_evaluation(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PlayerEvaluationResponse:
    """Fetch complete role classification and dimension evaluation profile for a player."""
    service = EvaluationService()
    return await service.evaluate_player_from_db(session, player_id)


@router.post(
    "/dataset/{dataset_id}",
    response_model=DatasetEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Dataset Players",
    description="Generate role-specific evaluation profiles and sample adequacy assessments for all players in a dataset.",
)
async def evaluate_dataset(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DatasetEvaluationResponse:
    """Generate structured evaluation profiles across an entire dataset."""
    service = EvaluationService()
    return await service.evaluate_dataset_from_db(session, dataset_id)

