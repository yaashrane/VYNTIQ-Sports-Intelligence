"""Integration tests for Player Master API endpoints."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.core.database import engine
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.cricket import Player


@pytest.fixture(autouse=True)
async def init_tables():
    """Ensure DB tables exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.anyio
async def test_list_and_get_players_api():
    """Verify GET /api/v1/players and GET /api/v1/players/{id}."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List players
        resp = await client.get("/api/v1/players")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "players" in data
        assert isinstance(data["players"], list)

        # 2. Filter by role
        role_resp = await client.get("/api/v1/players?role=BATTER")
        assert role_resp.status_code == 200

        # 3. 404 for unknown player
        unknown_resp = await client.get("/api/v1/players/P_UNKNOWN_99999")
        assert unknown_resp.status_code == 404
