"""Automated test suite for dataset upload, schema inspection, validation, and persistence."""

import io
import json
import pytest
import httpx
from sqlalchemy import select
from backend.app.core.database import engine, get_db_session
from backend.app.models.base import Base
from backend.app.models.cricket import Delivery, Match, Player
from backend.app.models.dataset import Dataset, ValidationIssue
from backend.app.services.ingestion.mapper import SchemaMapper


@pytest.fixture(autouse=True)
async def init_test_db():
    """Ensure database schema tables exist for all test runs."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# ==============================================================================
# SYNTHETIC TEST FIXTURES (TEST-ONLY DATA)
# ==============================================================================

SYNTHETIC_TEST_CSV = (
    "match_id,season,venue,batting_team,bowling_team,innings,ball,batter,bowler,runs_off_bat,extras,total_runs,wicket,player_dismissed,dismissal_kind\n"
    "TEST_M01,2024,Test Arena,Team Alpha,Team Beta,1,0.1,Test Striker A,Test Bowler X,4,0,4,0,,\n"
    "TEST_M01,2024,Test Arena,Team Alpha,Team Beta,1,0.2,Test Striker A,Test Bowler X,0,0,0,0,,\n"
    "TEST_M01,2024,Test Arena,Team Alpha,Team Beta,1,0.3,Test Striker A,Test Bowler X,6,0,6,0,,\n"
    "TEST_M01,2024,Test Arena,Team Alpha,Team Beta,1,0.4,Test Striker A,Test Bowler X,1,0,1,0,,\n"
    "TEST_M01,2024,Test Arena,Team Alpha,Team Beta,1,0.5,Test Striker B,Test Bowler X,0,0,0,1,Test Striker B,BOWLED\n"
    "TEST_M01,2024,Test Arena,Team Alpha,Team Beta,1,0.6,Test Striker C,Test Bowler X,2,0,2,0,,\n"
)

SYNTHETIC_TEST_JSON = json.dumps([
    {
        "match_no": "TEST_M02",
        "edition": "2024",
        "ground": "Test Stadium",
        "inning": 1,
        "over": 18,
        "ball_num": 1,
        "striker": "Death Finisher A",
        "bowler": "Death Bowler Y",
        "runs_batter": 6,
        "extras_runs": 0,
        "total": 6,
        "is_dismissal": 0,
    },
    {
        "match_no": "TEST_M02",
        "edition": "2024",
        "ground": "Test Stadium",
        "inning": 1,
        "over": 18,
        "ball_num": 2,
        "striker": "Death Finisher A",
        "bowler": "Death Bowler Y",
        "runs_batter": 4,
        "extras_runs": 0,
        "total": 4,
        "is_dismissal": 0,
    },
])

SYNTHETIC_INVALID_CRICKET_CSV = (
    "match_id,innings,ball,batter,bowler,runs_off_bat,extras,total_runs,wicket\n"
    "TEST_M03,1,0.1,Test Batter,Test Bowler,-4,0,-4,0\n"  # Invalid negative runs
    "TEST_M03,5,0.2,Test Batter,Test Bowler,1,0,1,0\n"   # Invalid innings 5
    "TEST_M03,1,0.3,,Test Bowler,0,0,0,0\n"              # Missing mandatory batter
)


# ==============================================================================
# UNIT & INTEGRATION TESTS
# ==============================================================================

@pytest.mark.anyio
async def test_schema_mapper_aliases():
    """Verify SchemaMapper correctly infers canonical fields from aliases."""
    mapper = SchemaMapper()
    source_cols = ["match_number", "edition", "striker", "bowler_name", "runs_off_bat", "extra"]
    mapping = mapper.detect_mapping(source_cols)

    assert mapping["match_number"] == "match_id"
    assert mapping["edition"] == "season"
    assert mapping["striker"] == "batter_id"
    assert mapping["bowler_name"] == "bowler_id"
    assert mapping["runs_off_bat"] == "batter_runs"
    assert mapping["extra"] == "extras_runs"


@pytest.mark.anyio
async def test_schema_mapper_missing_required():
    """Verify SchemaMapper detects missing mandatory fields."""
    mapper = SchemaMapper()
    # Missing batter_id and over progression
    partial_mapping = {"match_id": "match_id", "innings_num": "innings_num", "bowler_id": "bowler_id"}
    missing = mapper.check_missing_required(partial_mapping)
    assert any("over_delivery" in m for m in missing)
    assert "batter_id" in missing


@pytest.mark.anyio
async def test_upload_valid_csv(async_client: httpx.AsyncClient):
    """Test uploading a valid synthetic CSV file."""
    files = {"file": ("synthetic_sample.csv", io.BytesIO(SYNTHETIC_TEST_CSV.encode("utf-8")), "text/csv")}
    response = await async_client.post("/api/v1/datasets/upload", files=files, headers={"X-Workspace-ID": "workspace_test"})

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["file_format"] == "CSV"
    assert data["dataset_id"] is not None


@pytest.mark.anyio
async def test_upload_valid_json(async_client: httpx.AsyncClient):
    """Test uploading a valid synthetic JSON file."""
    files = {"file": ("synthetic_sample.json", io.BytesIO(SYNTHETIC_TEST_JSON.encode("utf-8")), "application/json")}
    response = await async_client.post("/api/v1/datasets/upload", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["file_format"] == "JSON"


@pytest.mark.anyio
async def test_upload_empty_file_fails(async_client: httpx.AsyncClient):
    """Test that uploading an empty file returns 422 error."""
    files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    response = await async_client.post("/api/v1/datasets/upload", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "EMPTY_FILE"


@pytest.mark.anyio
async def test_upload_unsupported_format(async_client: httpx.AsyncClient):
    """Test that uploading an unsupported extension returns 422."""
    files = {"file": ("unsupported.txt", io.BytesIO(b"random text content"), "text/plain")}
    response = await async_client.post("/api/v1/datasets/upload", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "UNSUPPORTED_FORMAT"


@pytest.mark.anyio
async def test_inspect_dataset_endpoint(async_client: httpx.AsyncClient):
    """Test inspecting dataset columns and inferred schema."""
    # 1. Upload
    files = {"file": ("test_inspect.csv", io.BytesIO(SYNTHETIC_TEST_CSV.encode("utf-8")), "text/csv")}
    upload_res = await async_client.post("/api/v1/datasets/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    # 2. Inspect
    inspect_res = await async_client.get(f"/api/v1/datasets/{dataset_id}/inspection")
    assert inspect_res.status_code == 200
    inspect_data = inspect_res.json()

    assert inspect_data["dataset_id"] == dataset_id
    assert inspect_data["file_format"] == "CSV"
    assert inspect_data["total_columns"] == 15
    assert inspect_data["missing_required_fields"] == []
    # Check that 'batter' column was mapped to 'batter_id'
    batter_col = next(c for c in inspect_data["columns"] if c["column_name"] == "batter")
    assert batter_col["suggested_canonical_field"] == "batter_id"


@pytest.mark.anyio
async def test_validate_and_persist_valid_csv(async_client: httpx.AsyncClient):
    """End-to-end test of upload -> validate -> check report -> persist."""
    import uuid
    unique_match = f"TEST_M_{uuid.uuid4().hex[:6]}"
    csv_content = SYNTHETIC_TEST_CSV.replace("TEST_M01", unique_match)

    # 1. Upload
    files = {"file": ("test_flow.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    upload_res = await async_client.post("/api/v1/datasets/upload", files=files, headers={"X-Workspace-ID": "workspace_super_rr_s2"})
    dataset_id = upload_res.json()["dataset_id"]

    # 2. Validate
    val_res = await async_client.post(f"/api/v1/datasets/{dataset_id}/validate")
    assert val_res.status_code == 200
    val_data = val_res.json()

    assert val_data["summary"]["status"] == "VALIDATED"
    assert val_data["summary"]["total_records"] == 6
    assert val_data["summary"]["valid_records"] == 6
    assert val_data["summary"]["invalid_records"] == 0

    # 3. Check status
    status_res = await async_client.get(f"/api/v1/datasets/{dataset_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "VALIDATED"
    assert status_res.json()["workspace_id"] == "workspace_super_rr_s2"

    # 4. Check report
    report_res = await async_client.get(f"/api/v1/datasets/{dataset_id}/report")
    assert report_res.status_code == 200
    assert report_res.json()["summary"]["valid_records"] == 6

    # 5. Persist
    persist_res = await async_client.post(f"/api/v1/datasets/{dataset_id}/persist")
    assert persist_res.status_code == 200
    persist_data = persist_res.json()
    assert persist_data["deliveries_persisted"] == 6
    assert persist_data["matches_persisted"] == 1
    assert persist_data["players_persisted"] >= 0

    # 6. Verify in database directly
    async for session in get_db_session():
        del_count = (await session.execute(select(Delivery).where(Delivery.dataset_id == dataset_id))).scalars().all()
        assert len(del_count) == 6
        break


@pytest.mark.anyio
async def test_validation_quarantine_on_invalid_cricket_data(async_client: httpx.AsyncClient):
    """Test that invalid cricket rows are quarantined and logged to the quality report."""
    files = {"file": ("invalid_cricket.csv", io.BytesIO(SYNTHETIC_INVALID_CRICKET_CSV.encode("utf-8")), "text/csv")}
    upload_res = await async_client.post("/api/v1/datasets/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    val_res = await async_client.post(f"/api/v1/datasets/{dataset_id}/validate")
    assert val_res.status_code == 200
    val_data = val_res.json()

    # All 3 rows have fatal errors (negative runs, invalid innings 5, missing batter)
    assert val_data["summary"]["status"] == "REJECTED"
    assert val_data["summary"]["invalid_records"] == 3
    assert val_data["summary"]["valid_records"] == 0
    assert len(val_data["sample_issues"]) >= 3


@pytest.mark.anyio
async def test_upload_malformed_json_fails_inspection(async_client: httpx.AsyncClient):
    """Test that malformed JSON is caught during inspection with clean error."""
    malformed_json = b"{'invalid_json': broken"
    files = {"file": ("broken.json", io.BytesIO(malformed_json), "application/json")}
    upload_res = await async_client.post("/api/v1/datasets/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    inspect_res = await async_client.get(f"/api/v1/datasets/{dataset_id}/inspection")
    assert inspect_res.status_code == 422
    assert inspect_res.json()["error"]["code"] == "MALFORMED_JSON"


@pytest.mark.anyio
async def test_oversized_upload_rejection(async_client: httpx.AsyncClient, monkeypatch):
    """Test that payloads exceeding MAX_UPLOAD_SIZE_BYTES are rejected with 422."""
    from backend.app.core import config
    # Temporarily set max upload size to 100 bytes for test
    monkeypatch.setattr(config.get_settings(), "MAX_UPLOAD_SIZE_BYTES", 100)

    large_content = b"A" * 500
    files = {"file": ("large.csv", io.BytesIO(large_content), "text/csv")}
    response = await async_client.post("/api/v1/datasets/upload", files=files)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


@pytest.mark.anyio
async def test_json_pipeline_end_to_end(async_client: httpx.AsyncClient):
    """Test full upload -> inspection -> validation -> persistence lifecycle for JSON."""
    files = {"file": ("synthetic_t20.json", io.BytesIO(SYNTHETIC_TEST_JSON.encode("utf-8")), "application/json")}
    upload_res = await async_client.post("/api/v1/datasets/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    # 1. Inspect
    inspect_res = await async_client.get(f"/api/v1/datasets/{dataset_id}/inspection")
    assert inspect_res.status_code == 200
    assert inspect_res.json()["file_format"] == "JSON"

    # 2. Validate
    val_res = await async_client.post(f"/api/v1/datasets/{dataset_id}/validate")
    assert val_res.status_code == 200
    assert val_res.json()["summary"]["valid_records"] == 2

    # 3. Persist
    persist_res = await async_client.post(f"/api/v1/datasets/{dataset_id}/persist")
    assert persist_res.status_code == 200
    assert persist_res.json()["deliveries_persisted"] == 2

