"""Database repository interfaces and implementations."""

from backend.app.repositories.base import BaseRepository
from backend.app.repositories.workspace import WorkspaceRepository

__all__ = ["BaseRepository", "WorkspaceRepository"]

