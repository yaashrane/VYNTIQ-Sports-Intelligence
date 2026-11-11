"""VYNTIQ — Sports Intelligence Platform FastAPI Application.

Main entry point establishing application lifecycle, middleware, error handling,
and versioned routing architecture.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.api.api_v1 import api_v1_router
from backend.app.core.config import get_settings
from backend.app.core.database import initialize_database
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.logging import get_logger, setup_logging

settings = get_settings()
logger = get_logger("vyntiq.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle events."""
    # Startup sequence
    setup_logging(settings.LOG_LEVEL)
    logger.info(
        "Starting %s v%s [Environment: %s]",
        settings.PROJECT_NAME,
        settings.VERSION,
        settings.ENVIRONMENT,
    )
    await initialize_database()
    yield
    # Shutdown sequence
    logger.info("Shutting down %s gracefully.", settings.PROJECT_NAME)


def create_application() -> FastAPI:
    """Instantiate and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "VYNTIQ — Sports Intelligence Platform API.\n\n"
            "Tagline: 'Every Metric Tells a Story.'\n"
            "An independent, premium sports analytics platform providing explainable "
            "scouting, player evaluation, and recruitment intelligence."
        ),
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # Configure CORS with strict environment-specified origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register centralized exception handlers
    register_exception_handlers(app)

    # Mount versioned API v1 router
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    @app.get("/", include_in_schema=False)
    async def root() -> JSONResponse:
        """Root endpoint returning basic platform identity and status."""
        return JSONResponse(
            content={
                "name": settings.PROJECT_NAME,
                "category": "Sports Intelligence",
                "tagline": "Every Metric Tells a Story.",
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "docs_url": f"{settings.API_V1_STR}/docs",
                "health_url": f"{settings.API_V1_STR}/health",
            }
        )

    return app


app = create_application()
