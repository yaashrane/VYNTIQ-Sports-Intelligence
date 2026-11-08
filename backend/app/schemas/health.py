"""Health check response schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """System health check payload specification."""

    status: str = Field(
        default="healthy", description="Application service status indicator"
    )
    service: str = Field(
        default="vyntiq-api", description="Service identifier name"
    )
    version: str = Field(
        default="1.0.0", description="Application semantic version"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "service": "vyntiq-api",
                "version": "1.0.0",
            }
        }
    }
