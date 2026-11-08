"""Generic asynchronous repository pattern for data access isolation."""

from typing import Any, Generic, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository providing foundational CRUD query primitives."""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: Any) -> ModelType | None:
        """Fetch a single entity instance by its primary key."""
        return await self.session.get(self.model, entity_id)

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        """Fetch paginated entity instances."""
        query = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, instance: ModelType) -> ModelType:
        """Persist a new entity instance."""
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Remove an entity instance from the session."""
        await self.session.delete(instance)
        await self.session.flush()
