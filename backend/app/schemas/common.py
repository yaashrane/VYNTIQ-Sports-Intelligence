"""Common reusable Pydantic schemas across API endpoints."""

from typing import Any
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Specific field or parameter-level error context."""

    field: str | None = Field(default=None, description="Path to invalid field")
    message: str = Field(description="Human-readable violation description")
    type: str | None = Field(default=None, description="Error classification tag")


class ErrorEnvelope(BaseModel):
    """Standardized error envelope payload."""

    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Primary descriptive error message")
    details: list[ErrorDetail] = Field(
        default_factory=list, description="Optional granular error descriptors"
    )


class ErrorResponse(BaseModel):
    """Root error response container."""

    error: ErrorEnvelope


class MessageResponse(BaseModel):
    """Generic informational response payload."""

    message: str
    data: dict[str, Any] | None = None
