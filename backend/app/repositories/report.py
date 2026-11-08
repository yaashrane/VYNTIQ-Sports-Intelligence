"""Repository primitives for generated PDF reports, metadata, and audit records."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.report import GeneratedReport
from backend.app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[GeneratedReport]):
    """Data access repository for generated PDF reports and audit metadata."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(GeneratedReport, session)

    async def get_by_report_id(self, report_id: str) -> GeneratedReport | None:
        """Fetch a report by its unique report_id."""
        return await self.session.get(GeneratedReport, report_id)

    async def list_by_workspace_id(
        self, workspace_id: str, limit: int = 100, offset: int = 0
    ) -> list[GeneratedReport]:
        """Fetch generated reports associated with a specific workspace, ordered by newest first."""
        query = (
            select(GeneratedReport)
            .where(GeneratedReport.workspace_id == workspace_id)
            .order_by(GeneratedReport.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_all(
        self, limit: int = 100, offset: int = 0
    ) -> list[GeneratedReport]:
        """Fetch all generated reports across workspaces, newest first."""
        query = (
            select(GeneratedReport)
            .order_by(GeneratedReport.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
