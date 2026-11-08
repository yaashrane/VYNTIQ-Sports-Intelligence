"""Pytest test configuration and shared fixtures for VYNTIQ backend."""

from collections.abc import AsyncGenerator
import pytest
import httpx
from fastapi import FastAPI
from backend.app.core.config import Settings, get_settings
from backend.app.main import create_application


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Create a clean application instance for testing."""
    return create_application()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide testing environment settings."""
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
    )


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an asynchronous HTTP client bound to the FastAPI application."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
