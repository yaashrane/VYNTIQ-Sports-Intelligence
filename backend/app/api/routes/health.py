"""System health and service availability endpoints."""

from fastapi import APIRouter, status
from backend.app.core.config import get_settings
from backend.app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Health Check",
    description="Verifies the operational availability of the VYNTIQ API service.",
)
async def get_health() -> HealthResponse:
    """Return application availability status, service name, and semantic version."""
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        version=settings.VERSION,
    )

