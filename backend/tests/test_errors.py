"""Tests for error handling, exception hierarchies, and standardized error responses."""

import httpx
import pytest
from fastapi import APIRouter
from backend.app.core.exceptions import (
    AppException,
    ConflictException,
    EntityNotFoundException,
    ValidationException,
    WorkspaceException,
)
from backend.app.main import create_application


@pytest.fixture
def error_test_app():
    """Create a FastAPI app with deliberate error-raising test endpoints."""
    test_app = create_application()
    test_router = APIRouter(prefix="/test-errors")

    @test_router.get("/app-exception")
    async def raise_app_exception():
        raise AppException(
            message="Custom error message",
            code="CUSTOM_TEST_ERROR",
            status_code=400,
            details=[{"field": "param", "message": "Invalid parameter value"}],
        )

    @test_router.get("/not-found")
    async def raise_not_found():
        raise EntityNotFoundException(entity_name="Player", entity_id="PL-9999")

    @test_router.get("/validation")
    async def raise_validation():
        raise ValidationException(
            message="Over delivery count exceeds maximum allowed legal balls.",
            code="INVALID_DELIVERY_SEQUENCE",
        )

    @test_router.get("/conflict")
    async def raise_conflict():
        raise ConflictException(
            message="Dataset with identical hash already exists in workspace."
        )

    @test_router.get("/workspace-violation")
    async def raise_workspace_violation():
        raise WorkspaceException(
            message="Cross-workspace write access denied.",
            code="WORKSPACE_ACCESS_DENIED",
        )

    @test_router.get("/unhandled-server-error")
    async def raise_unhandled():
        raise ZeroDivisionError("Simulated unexpected server error")

    test_app.include_router(test_router)
    return test_app


@pytest.mark.anyio
async def test_404_not_found(async_client: httpx.AsyncClient) -> None:
    """Verify non-existent route returns 404."""
    response = await async_client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_app_exception_envelope(error_test_app) -> None:
    """Verify custom AppException formats into predictable error JSON."""
    transport = httpx.ASGITransport(app=error_test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-errors/app-exception")
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "CUSTOM_TEST_ERROR"
        assert data["error"]["message"] == "Custom error message"
        assert len(data["error"]["details"]) == 1
        assert data["error"]["details"][0]["field"] == "param"


@pytest.mark.anyio
async def test_entity_not_found_exception(error_test_app) -> None:
    """Verify EntityNotFoundException returns 404 and structured entity message."""
    transport = httpx.ASGITransport(app=error_test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-errors/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "ENTITY_NOT_FOUND"
        assert "PL-9999" in data["error"]["message"]


@pytest.mark.anyio
async def test_validation_exception(error_test_app) -> None:
    """Verify ValidationException returns 422 with domain error code."""
    transport = httpx.ASGITransport(app=error_test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-errors/validation")
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "INVALID_DELIVERY_SEQUENCE"


@pytest.mark.anyio
async def test_conflict_exception(error_test_app) -> None:
    """Verify ConflictException returns 409."""
    transport = httpx.ASGITransport(app=error_test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-errors/conflict")
        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "RESOURCE_CONFLICT"


@pytest.mark.anyio
async def test_workspace_exception(error_test_app) -> None:
    """Verify WorkspaceException returns 403."""
    transport = httpx.ASGITransport(app=error_test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-errors/workspace-violation")
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "WORKSPACE_ACCESS_DENIED"


@pytest.mark.anyio
async def test_unhandled_exception_does_not_leak_traceback(error_test_app) -> None:
    """Verify unhandled exceptions return 500 without internal tracebacks leaked to client."""
    transport = httpx.ASGITransport(app=error_test_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-errors/unhandled-server-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        # Ensure raw division by zero traceback is not sent in the response message
        assert "ZeroDivisionError" not in data["error"]["message"]
