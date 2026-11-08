"""Domain and API exception hierarchy for VYNTIQ.

Guarantees predictable, structured error responses with HTTP status mapping.
"""

from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from backend.app.core.logging import get_logger

logger = get_logger("vyntiq.exceptions")


class AppException(Exception):
    """Base application exception with structured error metadata."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []


class EntityNotFoundException(AppException):
    """Raised when an entity is not found in the database or workspace."""

    def __init__(
        self,
        entity_name: str,
        entity_id: str,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"{entity_name} with identifier '{entity_id}' was not found.",
            code="ENTITY_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ValidationException(AppException):
    """Raised when domain-level business constraints or rules are violated."""

    def __init__(
        self,
        message: str,
        code: str = "VALIDATION_ERROR",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=422,
            details=details,
        )


class ConflictException(AppException):
    """Raised when an operation conflicts with existing entity state (e.g. duplicate key)."""

    def __init__(
        self,
        message: str,
        code: str = "RESOURCE_CONFLICT",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class WorkspaceException(AppException):
    """Raised when a workspace boundary or isolation violation occurs."""

    def __init__(
        self,
        message: str,
        code: str = "WORKSPACE_ERROR",
        status_code: int = status.HTTP_403_FORBIDDEN,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            details=details,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def handle_app_exception(_request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "Application error [%s]: %s (status=%d)",
            exc.code,
            exc.message,
            exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", "Invalid field"),
                "type": err.get("type", "value_error"),
            }
            for err in exc.errors()
        ]
        logger.info("Request schema validation failed: %d errors", len(details))
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "REQUEST_VALIDATION_ERROR",
                    "message": "Invalid request payload or query parameters.",
                    "details": details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled server exception: %s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred.",
                    "details": [],
                }
            },
        )
