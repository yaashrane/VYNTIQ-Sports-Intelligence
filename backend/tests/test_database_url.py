"""Tests for converting hosted PostgreSQL URLs to the async SQLAlchemy driver."""

from backend.app.core.database import build_async_database_url


def test_postgresql_url_uses_asyncpg_driver() -> None:
    url = build_async_database_url("postgresql://user:secret@db.example/vyntiq")

    assert url.drivername == "postgresql+asyncpg"
    assert url.username == "user"
    assert url.host == "db.example"
    assert url.database == "vyntiq"


def test_neon_url_translates_ssl_options_for_asyncpg() -> None:
    url = build_async_database_url(
        "postgresql://user:secret@db.example/vyntiq"
        "?sslmode=require&channel_binding=require"
    )

    assert url.drivername == "postgresql+asyncpg"
    assert url.query["ssl"] == "require"
    assert "sslmode" not in url.query
    assert "channel_binding" not in url.query


def test_sqlite_url_is_unchanged() -> None:
    url = build_async_database_url("sqlite+aiosqlite:///./vyntiq_dev.db")

    assert url.drivername == "sqlite+aiosqlite"
    assert url.database == "./vyntiq_dev.db"
