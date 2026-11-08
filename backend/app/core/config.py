"""Centralized configuration management for VYNTIQ.

Utilizes Pydantic Settings to validate environment variables with safe development defaults.
"""

from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and runtime environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Core Application Metadata
    PROJECT_NAME: str = Field(default="VYNTIQ API", description="Public project title")
    SERVICE_NAME: str = Field(default="vyntiq-api", description="Internal service identifier")
    VERSION: str = Field(default="1.0.0", description="API semantic version")
    API_V1_STR: str = Field(default="/api/v1", description="Version 1 route prefix")

    # Environment & Diagnostics
    ENVIRONMENT: Literal["development", "staging", "production", "testing"] = Field(
        default="development", description="Runtime environment"
    )
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Standard logging level")

    # Security & Access Control
    SECRET_KEY: str = Field(
        default="vyntiq-insecure-dev-secret-key-change-in-production-min32chars",
        description="Application cryptographic signing key",
    )
    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origins",
    )

    # Persistence Configuration (ADR-005)
    # Defaults to local SQLite for instant developer setup; toggleable to PostgreSQL in production
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./vyntiq_dev.db",
        description="Async database connection string",
    )
    DB_ECHO: bool = Field(default=False, description="Echo raw SQL statements to logs")

    # Storage & Upload Security (ADR-004)
    UPLOAD_DIR: str = Field(
        default="storage/uploads/raw",
        description="Directory for securely persisting raw uploaded datasets",
    )
    REPORTS_DIR: str = Field(
        default="storage/reports",
        description="Directory for securely persisting generated PDF reports",
    )
    MAX_UPLOAD_SIZE_BYTES: int = Field(
        default=52_428_800,  # 50 MB
        description="Maximum allowed upload payload size in bytes",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Parse comma-separated origin strings into a list."""
        if isinstance(value, str) and not value.startswith("["):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        raise ValueError("Invalid format for CORS_ORIGINS")

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Ensure log level is a valid standard level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_val = value.upper()
        if upper_val not in valid_levels:
            raise ValueError(f"Invalid log level: {value}. Must be one of {valid_levels}")
        return upper_val


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton application settings."""
    return Settings()

