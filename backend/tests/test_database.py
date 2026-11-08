"""Integration tests for database connection, health checks, and repository patterns."""

import pytest
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import check_db_health, get_db_session
from backend.app.models.base import Base, TimestampMixin
from backend.app.repositories.base import BaseRepository


class SampleEntity(Base, TimestampMixin):
    """Test entity for validating Base, TimestampMixin, and BaseRepository."""

    __tablename__ = "test_sample_entities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)


@pytest.mark.anyio
async def test_database_health_check() -> None:
    """Verify that check_db_health returns True on active SQLite connection."""
    is_healthy = await check_db_health()
    assert is_healthy is True


@pytest.mark.anyio
async def test_repository_crud_lifecycle() -> None:
    """Verify BaseRepository CRUD operations on an async session."""
    from backend.app.core.database import engine

    # Create tables in memory
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async for session in get_db_session():
        repo = BaseRepository(SampleEntity, session)

        # 1. Create
        entity = SampleEntity(id="sample-01", name="Alpha Player")
        saved = await repo.create(entity)
        assert saved.id == "sample-01"
        assert saved.name == "Alpha Player"
        assert saved.created_at is not None

        # 2. Get by ID
        fetched = await repo.get_by_id("sample-01")
        assert fetched is not None
        assert fetched.name == "Alpha Player"

        # 3. List All
        all_items = await repo.list_all(limit=10)
        assert len(all_items) >= 1

        # 4. Delete
        await repo.delete(fetched)
        deleted = await repo.get_by_id("sample-01")
        assert deleted is None
        break

