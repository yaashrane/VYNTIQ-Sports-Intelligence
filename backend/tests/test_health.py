"""Integration tests for application health and root availability endpoints."""

import httpx
import pytest
from backend.app.schemas.health import HealthResponse


@pytest.mark.anyio
async def test_health_endpoint_success(async_client: httpx.AsyncClient) -> None:
    """Verify that GET /api/v1/health returns 200 and matches the expected schema."""
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "vyntiq-api"
    assert data["version"] == "1.0.0"

    # Schema validation assertion
    validated = HealthResponse(**data)
    assert validated.status == "healthy"


@pytest.mark.anyio
async def test_root_endpoint_metadata(async_client: httpx.AsyncClient) -> None:
    """Verify that GET / returns the platform identity without exposing sensitive info."""
    response = await async_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "VYNTIQ API"
    assert data["category"] == "Sports Intelligence"
    assert data["tagline"] == "Every Metric Tells a Story."
    assert data["version"] == "1.0.0"
    assert "/api/v1/docs" in data["docs_url"]

