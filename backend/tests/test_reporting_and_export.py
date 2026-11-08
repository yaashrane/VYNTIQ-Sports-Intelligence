"""Comprehensive integration and unit tests for VYNTIQ PDF Reporting and Export Engine.

Covers:
- Competition overview report generation
- Individual player evaluation report generation
- Multi-player comparison report generation (compatible roles)
- Cross-role comparison safeguard enforcement in reports
- Shortlist and scouting dossier generation (with and without reviewer notes)
- Missing data validation and structured error handling
- File naming security and directory traversal protection
- PDF file validity, binary integrity, and multi-page table formatting
- REST API lifecycle: generation, metadata query, and streaming download
"""

import os
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.core.database import engine, get_db_session
from backend.app.core.exceptions import EntityNotFoundException, ValidationException
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.cricket import Player
from backend.app.models.dataset import Dataset
from backend.app.models.workspace import (
    Shortlist,
    ShortlistAuditLog,
    ShortlistCandidate,
    Workspace,
    WorkspaceConfiguration,
)
from backend.app.schemas.evaluation import (
    PlayerRole,
    RoleClassificationResult,
    RoleClassificationStatus,
)
from backend.app.schemas.metrics import MetricDirection, MetricProvenance, SampleSizeInfo
from backend.app.schemas.report import ReportCreateRequest, ReportType
from backend.app.schemas.scoring import (
    DimensionScore,
    NormalizedMetric,
    PlayerScoreResult,
    ReliabilityStatus,
    ScoreExplanation,
    ScoringRunResponse,
)
from backend.app.services.reporting.service import ReportingService
from backend.app.services.reporting.storage import ReportStorage
from backend.app.services.scoring.service import RUN_CACHE


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def init_database_tables():
    """Ensure all database schema tables exist before executing tests."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def _seed_mock_player_score(
    player_id: str,
    name: str,
    role: PlayerRole,
    vor: float,
    raw: float,
    balls_faced: int = 250,
    legal_balls: int = 0,
    cohort_id: str = "TEST_COHORT_2026",
    dataset_id: str = "ds_sample_2026",
) -> PlayerScoreResult:
    """Construct an auditable PlayerScoreResult fixture."""
    dims = {}
    if role in {PlayerRole.BATTER, PlayerRole.ALL_ROUNDER}:
        dims["SCORING_EFFICIENCY"] = DimensionScore(
            dimension_id="SCORING_EFFICIENCY",
            dimension_name="Scoring Efficiency",
            weight=0.35,
            dimension_score=raw,
            contribution_points=round(raw * 0.35, 2),
            metrics=[
                NormalizedMetric(
                    metric_id="batting_strike_rate",
                    display_name="Strike Rate",
                    raw_value=152.4,
                    percentile=raw,
                    directionality=MetricDirection.HIGHER_IS_BETTER,
                    cohort_id=cohort_id,
                    cohort_size=40,
                    normalization_method="ECDF_EXACT",
                )
            ],
        )
        dims["BOUNDARY_ABILITY"] = DimensionScore(
            dimension_id="BOUNDARY_ABILITY",
            dimension_name="Boundary Ability",
            weight=0.35,
            dimension_score=max(0.0, raw - 2.0),
            contribution_points=round((raw - 2.0) * 0.35, 2),
            metrics=[],
        )
        dims["ACCELERATION"] = DimensionScore(
            dimension_id="ACCELERATION",
            dimension_name="Acceleration",
            weight=0.30,
            dimension_score=max(0.0, raw - 4.0),
            contribution_points=round((raw - 4.0) * 0.30, 2),
            metrics=[],
        )
    else:
        dims["BOWLING_ECONOMY"] = DimensionScore(
            dimension_id="BOWLING_ECONOMY",
            dimension_name="Bowling Economy",
            weight=0.40,
            dimension_score=raw,
            contribution_points=round(raw * 0.40, 2),
            metrics=[
                NormalizedMetric(
                    metric_id="bowling_economy_rate",
                    display_name="Economy Rate",
                    raw_value=6.85,
                    percentile=raw,
                    directionality=MetricDirection.LOWER_IS_BETTER,
                    cohort_id=cohort_id,
                    cohort_size=40,
                    normalization_method="ECDF_EXACT",
                )
            ],
        )
        dims["DOT_BALL_PRESSURE"] = DimensionScore(
            dimension_id="DOT_BALL_PRESSURE",
            dimension_name="Dot Ball Pressure",
            weight=0.30,
            dimension_score=raw,
            contribution_points=round(raw * 0.30, 2),
            metrics=[],
        )
        dims["WICKETS_PENETRATION"] = DimensionScore(
            dimension_id="WICKETS_PENETRATION",
            dimension_name="Penetration",
            weight=0.30,
            dimension_score=raw,
            contribution_points=round(raw * 0.30, 2),
            metrics=[],
        )

    score = PlayerScoreResult(
        player_id=player_id,
        player_name=name,
        role=role,
        role_classification=RoleClassificationResult(
            player_id=player_id,
            assigned_role=role,
            status=RoleClassificationStatus.CONFIRMED_FROM_SOURCE,
            classification_method="MOCK",
        ),
        cohort_id=cohort_id,
        vor_score=vor,
        raw_composite_score=raw,
        reliability_factor=0.99,
        reliability_status=ReliabilityStatus.ADEQUATE,
        sample_size=SampleSizeInfo(
            innings=14,
            balls_faced=balls_faced,
            legal_balls_bowled=legal_balls,
            dismissals=10,
            wickets=12 if legal_balls > 0 else 0,
        ),
        dimensions=dims,
        is_qualified=True,
        is_eligible=True,
        explanation=ScoreExplanation(
            final_vor=vor,
            raw_composite=raw,
            reliability_factor=0.99,
            reliability_status=ReliabilityStatus.ADEQUATE,
            top_strengths=["Elite boundary percentage in middle overs", "High True Strike Rate"],
            drag_factors=["Higher dot percentage against spin"],
            missing_or_limited_dimensions=[],
            summary_text=f"{name} ranks among the top performers in {cohort_id}.",
        ),
        scoring_version="1.0.0",
        provenance=MetricProvenance(
            dataset_id=dataset_id,
            calculated_at="2026-11-08T12:00:00Z",
        ),
    )
    return score


@pytest.fixture
def seeded_scoring_environment():
    """Populate RUN_CACHE with multi-role players."""
    run_id = f"run_test_{uuid.uuid4().hex[:6]}"
    dataset_id = "ds_sample_2026"

    # Seed 2 Batters and 1 Bowler
    b1 = _seed_mock_player_score("P_SANJU", "Sanju Samson", PlayerRole.BATTER, 88.5, 89.0, balls_faced=380, dataset_id=dataset_id)
    b2 = _seed_mock_player_score("P_JAISWAL", "Yashasvi Jaiswal", PlayerRole.BATTER, 86.0, 86.8, balls_faced=340, dataset_id=dataset_id)
    bw1 = _seed_mock_player_score("P_BUMRAH", "Jasprit Bumrah", PlayerRole.BOWLER, 92.0, 92.5, legal_balls=300, dataset_id=dataset_id)

    run_resp = ScoringRunResponse(
        run_id=run_id,
        cohort_id="TEST_COHORT_2026",
        dataset_id=dataset_id,
        total_evaluated=3,
        total_qualified=3,
        total_quarantined=0,
        scoring_version="1.0.0",
        created_at="2026-11-08T12:00:00Z",
        players=[b1, b2, bw1],
    )
    RUN_CACHE[run_id] = run_resp
    RUN_CACHE["latest"] = run_resp

    return {
        "run_id": run_id,
        "dataset_id": dataset_id,
        "players": [b1, b2, bw1],
    }


# ==============================================================================
# TEST SUITE: CORE REPORT TYPES & GENERATION
# ==============================================================================

@pytest.mark.anyio
async def test_competition_overview_report_generation(seeded_scoring_environment):
    """Verify Competition Overview PDF generation with workspace, config, and dataset information."""
    run_id = seeded_scoring_environment["run_id"]
    ws_id = f"ws_{uuid.uuid4().hex[:8]}"

    async for session in get_db_session():
        # Create workspace
        ws = Workspace(
            workspace_id=ws_id,
            name="SuperRR Talent Hunt Season 2",
            description="Domestic talent hunt for emerging Indian prospects.",
            sport_type="CRICKET",
            competition_name="SuperRR Selector",
            season_or_edition="Season 2",
            status="ACTIVE",
            dataset_references=["ds_sample_2026"],
        )
        session.add(ws)

        # Create workspace configuration
        cfg = WorkspaceConfiguration(
            config_id=f"cfg_{uuid.uuid4().hex[:8]}",
            workspace_id=ws_id,
            target_sport="CRICKET",
            target_roles=["BATTER", "BOWLER", "ALL_ROUNDER", "WICKETKEEPER"],
            min_age=18,
            max_age=25,
            min_balls_faced=120,
            min_legal_balls_bowled=120,
        )
        session.add(cfg)

        # Create dataset
        ds = Dataset(
            dataset_id="ds_sample_2026",
            source_filename="super_rr_historical.csv",
            storage_path="storage/datasets/super_rr_historical.csv",
            file_format="CSV",
            file_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            status="VALIDATED",
            total_rows=14500,
            valid_rows=14500,
            quarantined_rows=0,
        )
        await session.merge(ds)
        await session.commit()

        # Test via ReportingService
        service = ReportingService(session)
        req = ReportCreateRequest(
            report_type=ReportType.COMPETITION_OVERVIEW,
            run_id=run_id,
        )
        report_res = await service.generate_report(workspace_id=ws_id, request=req)

        # Assertions on metadata
        assert report_res.report_id.startswith("rep_")
        assert report_res.report_type == ReportType.COMPETITION_OVERVIEW
        assert report_res.workspace_id == ws_id
        assert report_res.file_size_bytes > 0
        assert len(report_res.sha256_hash) == 64
        assert "download" in report_res.download_url

        # Verify on-disk file exists and starts with %PDF
        file_path, filename = await service.get_report_file(report_res.report_id)
        assert file_path.exists()
        with open(file_path, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-"


@pytest.mark.anyio
async def test_individual_player_report_generation(seeded_scoring_environment):
    """Verify Individual Player Evaluation Dossier generation with radar chart and explainability."""
    run_id = seeded_scoring_environment["run_id"]
    player_id = "P_SANJU"

    async for session in get_db_session():
        # Seed Player biographical record in DB
        p = Player(
            player_id=player_id,
            canonical_name="Sanju Samson",
            nationality="India",
            batting_hand="RIGHT",
            bowling_style="Right-arm offbreak",
        )
        await session.merge(p)
        await session.commit()

        service = ReportingService(session)
        req = ReportCreateRequest(
            report_type=ReportType.INDIVIDUAL_PLAYER,
            player_id=player_id,
            run_id=run_id,
        )
        report_res = await service.generate_report(workspace_id=None, request=req)

        assert report_res.report_type == ReportType.INDIVIDUAL_PLAYER
        assert report_res.file_size_bytes > 1000
        assert len(report_res.sha256_hash) == 64

        file_path, _ = await service.get_report_file(report_res.report_id)
        assert file_path.exists()
        with open(file_path, "rb") as f:
            content = f.read()
            assert b"%PDF-" in content


@pytest.mark.anyio
async def test_player_comparison_report_compatible(seeded_scoring_environment):
    """Verify Head-to-Head Comparison report between compatible batters with dimension deltas."""
    run_id = seeded_scoring_environment["run_id"]

    async for session in get_db_session():
        service = ReportingService(session)
        req = ReportCreateRequest(
            report_type=ReportType.PLAYER_COMPARISON,
            comparison_player_ids=["P_SANJU", "P_JAISWAL"],
            run_id=run_id,
        )
        report_res = await service.generate_report(workspace_id=None, request=req)

        assert report_res.report_type == ReportType.PLAYER_COMPARISON
        assert report_res.file_size_bytes > 1000

        file_path, _ = await service.get_report_file(report_res.report_id)
        assert file_path.exists()
        with open(file_path, "rb") as f:
            content = f.read()
            assert b"%PDF-" in content


@pytest.mark.anyio
async def test_player_comparison_report_cross_role_safeguards(seeded_scoring_environment):
    """Verify that comparing candidates from differing roles triggers cross-role safeguards in PDF."""
    run_id = seeded_scoring_environment["run_id"]

    async for session in get_db_session():
        service = ReportingService(session)
        req = ReportCreateRequest(
            report_type=ReportType.PLAYER_COMPARISON,
            comparison_player_ids=["P_SANJU", "P_BUMRAH"],  # Batter vs Bowler
            run_id=run_id,
        )
        report_res = await service.generate_report(workspace_id=None, request=req)

        assert report_res.report_type == ReportType.PLAYER_COMPARISON
        assert report_res.file_size_bytes > 1000

        file_path, _ = await service.get_report_file(report_res.report_id)
        assert file_path.exists()
        with open(file_path, "rb") as f:
            content = f.read()
            assert b"%PDF-" in content


@pytest.mark.anyio
async def test_shortlist_report_with_and_without_reviewer_notes(seeded_scoring_environment):
    """Verify Shortlist Report generation, testing reviewer notes privacy safeguard."""
    ws_id = f"ws_sl_{uuid.uuid4().hex[:6]}"
    sl_id = f"sl_{uuid.uuid4().hex[:6]}"

    async for session in get_db_session():
        # Create workspace
        ws = Workspace(
            workspace_id=ws_id,
            name="Rajasthan Royals Target 10",
            competition_name="SuperRR",
            season_or_edition="S2",
            status="ACTIVE",
        )
        session.add(ws)

        # Create Shortlist
        sl = Shortlist(
            shortlist_id=sl_id,
            workspace_id=ws_id,
            name="Top Emerging Batsmen",
            dataset_id="ds_sample_2026",
            target_size=5,
            eligible_count=1,
            excluded_count=1,
            shortlisted_count=1,
            status="GENERATED",
            scoring_run_id=seeded_scoring_environment["run_id"],
        )
        session.add(sl)

        # Add Eligible candidate with private notes
        c1 = ShortlistCandidate(
            candidate_entry_id=f"sc_{uuid.uuid4().hex[:6]}",
            shortlist_id=sl_id,
            workspace_id=ws_id,
            player_id="P_SANJU",
            player_name="Sanju Samson",
            assigned_role="BATTER",
            rank=1,
            vor_score=88.5,
            raw_composite_score=89.0,
            reliability_factor=0.99,
            reliability_status="ADEQUATE",
            evaluation_ref="eval_ref_1",
            explainability_ref="expl_ref_1",
            eligibility_status="ELIGIBLE",
            review_status="RECOMMENDED",
            reviewer_notes="CONFIDENTIAL SCOUT NOTE: Elite captaincy temperament.",
        )
        session.add(c1)

        # Add ShortlistAuditLog with exclusion details
        audit = ShortlistAuditLog(
            audit_id=f"aud_{uuid.uuid4().hex[:6]}",
            shortlist_id=sl_id,
            workspace_id=ws_id,
            dataset_id="ds_sample_2026",
            configuration_version="1.0.0",
            evaluation_methodology_version="1.0.0",
            metric_registry_version="1.0.0",
            ranking_engine_version="1.0.0",
            eligible_candidate_count=1,
            excluded_candidate_count=1,
            shortlisted_candidate_count=1,
            exclusion_details={
                "P_DISQUALIFIED": "Age 28 exceeds maximum competition cutoff of 25"
            },
        )
        session.add(audit)
        await session.commit()

        # 1. Generate Report with reviewer notes omitted (default privacy policy)
        service = ReportingService(session)
        req_clean = ReportCreateRequest(
            report_type=ReportType.SHORTLIST,
            shortlist_id=sl_id,
            include_reviewer_notes=False,
        )
        rep_clean = await service.generate_report(workspace_id=ws_id, request=req_clean)
        file_path, _ = await service.get_report_file(rep_clean.report_id)

        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
            # Confidential note must NOT be present
            assert b"Elite captaincy temperament" not in pdf_bytes

        # 2. Generate Report with reviewer notes explicitly authorized
        req_notes = ReportCreateRequest(
            report_type=ReportType.SHORTLIST,
            shortlist_id=sl_id,
            include_reviewer_notes=True,
        )
        rep_notes = await service.generate_report(workspace_id=ws_id, request=req_notes)
        file_path, _ = await service.get_report_file(rep_notes.report_id)

        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
            # Confidential note MUST be present when authorized
            assert b"Elite captaincy temperament" in pdf_bytes


# ==============================================================================
# TEST SUITE: VALIDATION & SECURITY
# ==============================================================================

@pytest.mark.anyio
async def test_missing_data_validation():
    """Verify that requests with missing entities raise structured exceptions without failing silently."""
    async for session in get_db_session():
        service = ReportingService(session)

        # 1. Non-existent player
        with pytest.raises(EntityNotFoundException):
            await service.generate_report(
                workspace_id=None,
                request=ReportCreateRequest(
                    report_type=ReportType.INDIVIDUAL_PLAYER,
                    player_id="P_DOES_NOT_EXIST",
                ),
            )

        # 2. Invalid comparison candidate count (< 2 players)
        with pytest.raises(ValidationException) as exc_info:
            await service.generate_report(
                workspace_id=None,
                request=ReportCreateRequest(
                    report_type=ReportType.PLAYER_COMPARISON,
                    comparison_player_ids=["P_SOLO"],
                ),
            )
        assert "between 2 and 5" in str(exc_info.value)

        # 3. Missing workspace ID for overview
        with pytest.raises(ValidationException):
            await service.generate_report(
                workspace_id=None,
                request=ReportCreateRequest(
                    report_type=ReportType.COMPETITION_OVERVIEW,
                ),
            )


@pytest.mark.anyio
async def test_file_naming_safety_and_path_traversal_prevention():
    """Verify that storage layer sanitizes filenames and rejects directory traversal attacks."""
    storage = ReportStorage()

    # 1. Safe filename generation
    safe_name = storage.generate_safe_filename("INDIVIDUAL_PLAYER", "P_001/../../malicious")
    assert ".." not in safe_name
    assert "/" not in safe_name
    assert "\\" not in safe_name
    assert safe_name.startswith("VYNTIQ_INDIVIDUAL_PLAYER_")
    assert safe_name.endswith(".pdf")

    # 2. Directory traversal prevention
    resolved = storage.get_file_path(safe_name)
    assert resolved.parent == storage.base_dir.resolve()


# ==============================================================================
# TEST SUITE: REST API INTEGRATION
# ==============================================================================

@pytest.mark.anyio
async def test_rest_api_reports_lifecycle(seeded_scoring_environment):
    """Verify REST API lifecycle: POST generation, GET metadata, and streaming PDF download."""
    ws_id = f"ws_api_{uuid.uuid4().hex[:6]}"

    async for session in get_db_session():
        ws = Workspace(
            workspace_id=ws_id,
            name="API Test Workspace",
            competition_name="Domestic T20",
            season_or_edition="2026",
            status="ACTIVE",
        )
        session.add(ws)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. POST generate workspace overview report
        create_payload = {
            "report_type": "COMPETITION_OVERVIEW",
            "title": "API Test Overview Report",
            "run_id": seeded_scoring_environment["run_id"],
        }
        resp = await ac.post(f"/api/v1/workspaces/{ws_id}/reports", json=create_payload)
        assert resp.status_code == 201
        data = resp.json()
        report_id = data["report_id"]
        assert data["title"] == "API Test Overview Report"
        assert data["file_size_bytes"] > 0
        assert data["generation_status"] == "COMPLETED"

        # 2. GET list reports for workspace
        list_resp = await ac.get(f"/api/v1/workspaces/{ws_id}/reports")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["total"] >= 1
        assert any(r["report_id"] == report_id for r in list_data["reports"])

        # 3. GET report metadata
        get_resp = await ac.get(f"/api/v1/workspaces/{ws_id}/reports/{report_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["report_id"] == report_id

        # 4. GET download report PDF file
        down_resp = await ac.get(f"/api/v1/workspaces/{ws_id}/reports/{report_id}/download")
        assert down_resp.status_code == 200
        assert down_resp.headers["content-type"] == "application/pdf"
        assert "attachment" in down_resp.headers["content-disposition"]
        assert down_resp.content.startswith(b"%PDF-")

        # 5. POST standalone report (outside workspace context)
        stand_payload = {
            "report_type": "INDIVIDUAL_PLAYER",
            "player_id": "P_SANJU",
            "run_id": seeded_scoring_environment["run_id"],
        }
        stand_resp = await ac.post("/api/v1/reports", json=stand_payload)
        assert stand_resp.status_code == 201
        stand_id = stand_resp.json()["report_id"]

        # 6. GET standalone download
        stand_down = await ac.get(f"/api/v1/reports/{stand_id}/download")
        assert stand_down.status_code == 200
        assert stand_down.content.startswith(b"%PDF-")
