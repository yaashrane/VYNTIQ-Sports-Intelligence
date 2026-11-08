"""Unit tests for centralized configuration management."""

import pytest
from pydantic import ValidationError
from backend.app.core.config import Settings, get_settings


def test_default_settings() -> None:
    """Verify default development configuration parameters."""
    settings = Settings()
    assert settings.PROJECT_NAME == "VYNTIQ API"
    assert settings.SERVICE_NAME == "vyntiq-api"
    assert settings.VERSION == "1.0.0"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is False
    assert settings.LOG_LEVEL == "INFO"
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "sqlite+aiosqlite" in settings.DATABASE_URL


def test_cors_origins_parsing_from_string() -> None:
    """Verify CORS origins string is parsed into a list of cleaned URLs."""
    raw_origins = "http://localhost:8000, https://vyntiq.sports.analytics "
    settings = Settings(CORS_ORIGINS=raw_origins)
    assert settings.CORS_ORIGINS == [
        "http://localhost:8000",
        "https://vyntiq.sports.analytics",
    ]


def test_log_level_validation() -> None:
    """Verify log level validation enforces standard levels and upper-casing."""
    settings = Settings(LOG_LEVEL="debug")
    assert settings.LOG_LEVEL == "DEBUG"

    with pytest.raises(ValidationError):
        Settings(LOG_LEVEL="INVALID_LOG_LEVEL")


def test_get_settings_caching() -> None:
    """Verify get_settings returns a cached singleton instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
