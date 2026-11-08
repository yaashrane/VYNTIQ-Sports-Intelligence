"""Repository primitives for workspace, configuration, shortlist, and audit persistence."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.dataset import Dataset
from backend.app.models.workspace import (
    Shortlist,
    ShortlistAuditLog,
    ShortlistCandidate,
    Workspace,
    WorkspaceConfiguration,
)
from backend.app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    """Data access repository for competition workspaces and associated entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Workspace, session)

    async def get_by_workspace_id(self, workspace_id: str) -> Workspace | None:
        """Fetch a workspace by its unique workspace_id."""
        return await self.session.get(Workspace, workspace_id)

    async def list_workspaces(
        self, limit: int = 100, offset: int = 0, status: str | None = None
    ) -> list[Workspace]:
        """Fetch workspaces, optionally filtered by status."""
        query = select(Workspace).order_by(Workspace.created_at.desc())
        if status:
            query = query.where(Workspace.status == status)
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_configuration(
        self, workspace_id: str
    ) -> WorkspaceConfiguration | None:
        """Fetch active competition configuration for a workspace."""
        query = select(WorkspaceConfiguration).where(
            WorkspaceConfiguration.workspace_id == workspace_id
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def save_configuration(
        self, config: WorkspaceConfiguration
    ) -> WorkspaceConfiguration:
        """Persist or update configuration entity."""
        self.session.add(config)
        await self.session.flush()
        await self.session.refresh(config)
        return config

    async def get_workspace_datasets(self, workspace_id: str) -> list[Dataset]:
        """Fetch datasets scoped to this workspace or canonical shared datasets."""
        query = select(Dataset).where(
            (Dataset.workspace_id == workspace_id) | (Dataset.workspace_id.is_(None))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # Shortlist operations
    async def create_shortlist(self, shortlist: Shortlist) -> Shortlist:
        """Persist a new shortlist master record."""
        self.session.add(shortlist)
        await self.session.flush()
        await self.session.refresh(shortlist)
        return shortlist

    async def get_shortlist(self, shortlist_id: str) -> Shortlist | None:
        """Fetch shortlist master record by ID."""
        return await self.session.get(Shortlist, shortlist_id)

    async def list_shortlists_for_workspace(
        self, workspace_id: str, limit: int = 50, offset: int = 0
    ) -> list[Shortlist]:
        """List shortlists belonging to a specific workspace."""
        query = (
            select(Shortlist)
            .where(Shortlist.workspace_id == workspace_id)
            .order_by(Shortlist.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add_candidates(
        self, candidates: list[ShortlistCandidate]
    ) -> list[ShortlistCandidate]:
        """Bulk persist candidate player records."""
        self.session.add_all(candidates)
        await self.session.flush()
        return candidates

    async def get_candidates(self, shortlist_id: str) -> list[ShortlistCandidate]:
        """Fetch all candidates for a shortlist, ordered by rank."""
        query = (
            select(ShortlistCandidate)
            .where(ShortlistCandidate.shortlist_id == shortlist_id)
            .order_by(ShortlistCandidate.rank.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_candidate(
        self, shortlist_id: str, player_id: str
    ) -> ShortlistCandidate | None:
        """Fetch an individual candidate within a shortlist."""
        query = select(ShortlistCandidate).where(
            ShortlistCandidate.shortlist_id == shortlist_id,
            ShortlistCandidate.player_id == player_id,
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def create_audit_log(self, log: ShortlistAuditLog) -> ShortlistAuditLog:
        """Persist shortlist generation audit log."""
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_audit_log(self, shortlist_id: str) -> ShortlistAuditLog | None:
        """Fetch audit log for a shortlist."""
        query = select(ShortlistAuditLog).where(
            ShortlistAuditLog.shortlist_id == shortlist_id
        )
        result = await self.session.execute(query)
        return result.scalars().first()

