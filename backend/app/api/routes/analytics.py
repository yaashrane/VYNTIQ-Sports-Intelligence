"""API endpoints for cricket performance metrics calculation, registry lookup, and summaries."""

from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.dependencies import get_db
from backend.app.schemas.analytics import (
    CalculationResponse,
    DatasetMetricsSummaryResponse,
    MetricCalculationRequest,
    MetricRegistryResponse,
)
from backend.app.services.analytics.registry import get_all_metrics
from backend.app.services.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics & Metrics Engine"])


@router.get(
    "/metrics",
    response_model=MetricRegistryResponse,
    status_code=status.HTTP_200_OK,
    summary="List Registered Metrics",
    description="Retrieve catalog of all registered cricket performance metrics, formulas, and availability statuses.",
)
async def list_metrics() -> MetricRegistryResponse:
    """Return all registered metrics with metadata from the central registry."""
    metrics = get_all_metrics()
    return MetricRegistryResponse(
        total_metrics=len(metrics),
        metrics=metrics,
    )


@router.post(
    "/calculate",
    response_model=CalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate Performance Metrics",
    description="Calculate standard and advanced performance metrics for a validated dataset with optional filters.",
)
async def calculate_metrics(
    request: MetricCalculationRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CalculationResponse:
    """Execute metric calculation across deliveries for the specified dataset and player/dimension filters."""
    service = AnalyticsService()
    return await service.calculate_for_dataset(session, request)


@router.get(
    "/datasets/{dataset_id}/summary",
    response_model=DatasetMetricsSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Dataset Metrics Summary",
    description="Retrieve high-level macro scoring and bowling summary for an ingested dataset.",
)
async def get_dataset_summary(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DatasetMetricsSummaryResponse:
    """Produce dataset-level aggregate metrics summary."""
    service = AnalyticsService()
    return await service.get_dataset_summary(session, dataset_id)
