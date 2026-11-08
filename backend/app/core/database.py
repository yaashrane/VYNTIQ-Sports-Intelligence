"""Database engine, connection pooling, and session management for VYNTIQ.

Complies with ADR-005 (PostgreSQL production target with SQLite developer parity).
"""

from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger

logger = get_logger("vyntiq.database")

settings = get_settings()

# Engine creation with connection safety parameters
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    # SQLite requires check_same_thread=False; asyncpg does not take this kwarg
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.DATABASE_URL
    else {},
)

# Async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an active transactional database session.

    Rolls back automatically on unhandled exception and closes cleanly.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    """Execute a low-overhead query (SELECT 1) to verify actual database connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database connectivity check failed: %s", str(exc))
        return False
