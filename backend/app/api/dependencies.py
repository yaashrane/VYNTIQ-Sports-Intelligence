"""FastAPI dependency injection providers."""

from collections.abc import AsyncGenerator
from typing import Annotated
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import Settings, get_settings
from backend.app.core.database import get_db_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that injects an active database session."""
    async for session in get_db_session():
        yield session


def get_current_settings() -> Settings:
    """Dependency that injects the cached application settings."""
    return get_settings()


async def get_current_workspace_id(
    x_workspace_id: Annotated[
        str | None,
        Header(
            alias="X-Workspace-ID",
            description="Tenant workspace scope identifier (e.g. 'workspace_super_rr_s2')",
        ),
    ] = None,
) -> str | None:
    """Extract and validate the active workspace scope from request headers.

    Returns None for canonical un-scoped queries, or the workspace identifier string.
    """
    return x_workspace_id

