"""Integration and unit tests for Competition Workspaces and Shortlisting Engine.

Covers:
- Workspace creation, retrieval, updates, and state machine lifecycle
- Workspace tenant data isolation
- Competition configuration and eligibility rules
- Shortlist generation consuming scoring run outputs
- Rejection of empty/incomplete scoring data
- Candidate review workflow without scoring mutation
- Audit log generation and deterministic reproducibility
- Full REST API integration lifecycle
"""

import uuid
from datetime import date, datetime, timezone
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from backend.app.core.database import check_db_health, engine, get_db_session
from backend.app.core.exceptions import (
    ConflictException,
    EntityNotFoundException,
    ValidationException,
    WorkspaceException,
)
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
from backend.app.schemas.metrics import (
    MetricDirection,
    MetricProvenance,
    SampleSizeInfo,
)
from backend.app.schemas.scoring import (
    DimensionScore,
    NormalizedMetric,
    PlayerScoreResult,
    ReliabilityStatus,
    ScoreExplanation,
    ScoringRunResponse,
)
from backend.app.schemas.workspace import (
    AgeCriteria,
    CompetitionConfigCreate,
    CompetitionConfigUpdate,
    EligibilityStatus,
    ParticipationCriteria,
    ReviewStatus,
    ShortlistGenerateRequest,
    ShortlistReviewRequest,
    SportType,
    WorkspaceCreate,
    WorkspaceStatus,
    WorkspaceUpdate,
)
from backend.app.services.scoring.service import RUN_CACHE
from backend.app.services.shortlisting.eligibility import EligibilityEngine
from backend.app.services.shortlisting.service import ShortlistingService
from backend.app.services.workspace.service import WorkspaceService


# ==============================================================================
# TEST FIXTURES & DATA SEEDING
# ==============================================================================

@pytest.fixture(autouse=True)
async def init_database_tables():
    """Ensure all database schema tables exist before executing tests."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
def mock_scoring_run_data():
    """Seed RUN_CACHE with a deterministic scoring run for shortlisting tests."""
    dataset_id = f"ds_comp_{uuid.uuid4().hex[:6]}"
    run_id = f"run_comp_{uuid.uuid4().hex[:6]}"

    # Candidate 1: Elite Batter (VOR = 82.5)
    p1 = _create_mock_player_score(
        player_id="P_BAT_TOP1",
        name="Top Batter 1",
        role=PlayerRole.BATTER,
        vor=82.5,
        raw=82.5,
        balls_faced=350,
        legal_balls=0,
    )

    # Candidate 2: Quality Batter (VOR = 74.0)
    p2 = _create_mock_player_score(
        player_id="P_BAT_TOP2",
        name="Top Batter 2",
        role=PlayerRole.BATTER,
        vor=74.0,
        raw=75.0,
        balls_faced=220,
        legal_balls=0,
    )

    # Candidate 3: Elite Bowler (VOR = 85.0) - Should be excluded if competition only targets Batters
    p3 = _create_mock_player_score(
        player_id="P_BOWL_TOP1",
        name="Strike Bowler",
        role=PlayerRole.BOWLER,
        vor=85.0,
        raw=85.0,
        balls_faced=10,
        legal_balls=300,
    )

    # Candidate 4: Micro-sample Batter (quarantined, VOR = 50.0)
    p4 = _create_mock_player_score(
        player_id="P_BAT_MICRO",
        name="Rookie Batter",
        role=PlayerRole.BATTER,
        vor=50.0,
        raw=88.0,
        balls_faced=15,  # Micro sample
        legal_balls=0,
        rel_stat=ReliabilityStatus.INSUFFICIENT_SAMPLE,
    )

    scoring_run = ScoringRunResponse(
        run_id=run_id,
        dataset_id=dataset_id,
        cohort_id="COHORT_COMP_T20",
        total_evaluated=4,
        total_qualified=3,
        total_quarantined=1,
        scoring_version="1.0.0",
        created_at="2026-11-08T12:00:00Z",
        players=[p3, p1, p2, p4],  # Unsorted initially to verify sorting
    )

    RUN_CACHE[run_id] = scoring_run
    return {"dataset_id": dataset_id, "run_id": run_id, "run": scoring_run}


def _create_mock_player_score(
    player_id: str,
    name: str,
    role: PlayerRole,
    vor: float,
    raw: float,
    balls_faced: int,
    legal_balls: int,
    rel_stat: ReliabilityStatus = ReliabilityStatus.ADEQUATE,
) -> PlayerScoreResult:
    """Helper creating reproducible PlayerScoreResult instances."""
    return PlayerScoreResult(
        player_id=player_id,
        player_name=name,
        role=role,
        role_classification=RoleClassificationResult(
            player_id=player_id,
            assigned_role=role,
            status=RoleClassificationStatus.CONFIRMED_FROM_SOURCE,
            classification_method="MOCK",
        ),
        cohort_id="COHORT_TEST",
        vor_score=vor,
        raw_composite_score=raw,
        reliability_factor=1.0 if rel_stat == ReliabilityStatus.ADEQUATE else 0.5,
        reliability_status=rel_stat,
        sample_size=SampleSizeInfo(balls_faced=balls_faced, legal_balls_bowled=legal_balls),
        dimensions={},
        is_qualified=rel_stat != ReliabilityStatus.INSUFFICIENT_SAMPLE,
        is_eligible=True,
        explanation=ScoreExplanation(
            final_vor=vor,
            raw_composite=raw,
            reliability_factor=1.0,
            reliability_status=rel_stat,
            top_strengths=["Top form"],
            drag_factors=[],
            summary_text="Mock score",
        ),
        provenance=MetricProvenance(dataset_id="MOCK_DS"),
    )


# ==============================================================================
# 1. WORKSPACE LIFECYCLE & STATE MACHINE TESTS
# ==============================================================================

@pytest.mark.anyio
async def test_workspace_creation_and_retrieval():
    """Verify workspace creation with default configuration and detail lookup."""
    async for session in get_db_session():
        service = WorkspaceService(session)
        ws_id = f"ws_rr_{uuid.uuid4().hex[:6]}"

        created = await service.create_workspace(
            WorkspaceCreate(
                workspace_id=ws_id,
                name="Rajasthan Royals SuperRR Workspace",
                description="Competition workspace for scouting emerging domestic talent.",
                sport_type=SportType.CRICKET,
                competition_name="SuperRR Selector",
                season_or_edition="Season 2",
            )
        )

        assert created.workspace_id == ws_id
        assert created.name == "Rajasthan Royals SuperRR Workspace"
        assert created.status == WorkspaceStatus.DRAFT
        assert created.configuration is not None
        assert created.configuration.shortlist_size == 10
        assert "BATTER" in created.configuration.target_roles

        # Detail lookup
        detail = await service.get_workspace_detail(ws_id)
        assert detail.workspace_id == ws_id
        assert detail.shortlists_count == 0


@pytest.mark.anyio
async def test_workspace_update_and_state_machine_transitions():
    """Verify state transitions DRAFT -> ACTIVE -> COMPLETED -> ARCHIVED, and invalid transitions."""
    async for session in get_db_session():
        service = WorkspaceService(session)
        ws_id = f"ws_{uuid.uuid4().hex[:6]}"
        await service.create_workspace(
            WorkspaceCreate(
                workspace_id=ws_id,
                name="State Machine Test",
                competition_name="IPL Scouting",
                season_or_edition="2026",
            )
        )

        # 1. DRAFT -> ACTIVE (valid)
        w_active = await service.update_workspace(
            ws_id, WorkspaceUpdate(status=WorkspaceStatus.ACTIVE)
        )
        assert w_active.status == WorkspaceStatus.ACTIVE

        # 2. ACTIVE -> COMPLETED (valid)
        w_comp = await service.update_workspace(
            ws_id, WorkspaceUpdate(status=WorkspaceStatus.COMPLETED)
        )
        assert w_comp.status == WorkspaceStatus.COMPLETED

        # 3. COMPLETED -> ARCHIVED (valid)
        w_arch = await service.archive_workspace(ws_id)
        assert w_arch.status == WorkspaceStatus.ARCHIVED

        # 4. ARCHIVED -> ACTIVE (Invalid transition - terminal state)
        with pytest.raises(ValidationException) as exc_info:
            await service.update_workspace(
                ws_id, WorkspaceUpdate(status=WorkspaceStatus.ACTIVE)
            )
        assert "Invalid workspace status transition" in str(exc_info.value)


@pytest.mark.anyio
async def test_workspace_duplicate_id_and_empty_name_validation():
    """Verify conflict exception on duplicate workspace ID and validation on empty name."""
    async for session in get_db_session():
        service = WorkspaceService(session)
        ws_id = f"ws_dup_{uuid.uuid4().hex[:6]}"

        await service.create_workspace(
            WorkspaceCreate(
                workspace_id=ws_id,
                name="Original Workspace",
                competition_name="Tournament A",
                season_or_edition="2026",
            )
        )

        # Duplicate ID check
        with pytest.raises(ConflictException):
            await service.create_workspace(
                WorkspaceCreate(
                    workspace_id=ws_id,
                    name="Duplicate ID Workspace",
                    competition_name="Tournament B",
                    season_or_edition="2026",
                )
            )

        # Empty name validation
        with pytest.raises(ValidationException):
            await service.create_workspace(
                WorkspaceCreate(
                    name="   ",
                    competition_name="Tournament C",
                    season_or_edition="2026",
                )
            )


# ==============================================================================
# 2. WORKSPACE ISOLATION TESTS (ADR-001)
# ==============================================================================

@pytest.mark.anyio
async def test_workspace_data_isolation():
    """Verify that a workspace cannot access private datasets or shortlists belonging to another workspace."""
    async for session in get_db_session():
        ws_service = WorkspaceService(session)
        sl_service = ShortlistingService(session)

        ws1_id = f"ws_tenant1_{uuid.uuid4().hex[:6]}"
        ws2_id = f"ws_tenant2_{uuid.uuid4().hex[:6]}"

        await ws_service.create_workspace(
            WorkspaceCreate(workspace_id=ws1_id, name="Tenant 1", competition_name="T1", season_or_edition="1")
        )
        await ws_service.create_workspace(
            WorkspaceCreate(workspace_id=ws2_id, name="Tenant 2", competition_name="T2", season_or_edition="1")
        )

        # Create a private dataset assigned exclusively to Tenant 2
        ds_t2 = Dataset(
            dataset_id=f"ds_private_t2_{uuid.uuid4().hex[:6]}",
            workspace_id=ws2_id,
            origin_type="COMPETITION_SANDBOX",
            source_filename="tenant2_scouting.csv",
            storage_path="/tmp/t2.csv",
            file_format="CSV",
            file_sha256="hash_t2",
            status="PERSISTED",
        )
        session.add(ds_t2)
        await session.flush()

        # Tenant 1 attempts to generate a shortlist referencing Tenant 2's private dataset
        with pytest.raises(WorkspaceException) as exc_info:
            await sl_service.generate_shortlist(
                workspace_id=ws1_id,
                payload=ShortlistGenerateRequest(dataset_id=ds_t2.dataset_id),
            )
        assert "cannot be accessed" in str(exc_info.value)


# ==============================================================================
# 3. ELIGIBILITY ENGINE TESTS
# ==============================================================================

@pytest.mark.anyio
async def test_eligibility_engine_role_age_and_workload_exclusions():
    """Verify non-silent exclusions with explicit machine-readable reasons."""
    from backend.app.schemas.workspace import CompetitionConfigResponse

    config = CompetitionConfigResponse(
        config_id="cfg_test",
        workspace_id="ws_test",
        target_sport="CRICKET",
        target_roles=["BATTER"],  # Only batters allowed
        age_criteria=AgeCriteria(min_age=19, max_age=23, age_cutoff_date="2026-11-01"),
        participation_criteria=ParticipationCriteria(min_balls_faced=50),
        required_metrics=[],
        evaluation_profile_version="1.0.0",
        shortlist_size=10,
        custom_eligibility_rules={"allowed_nationalities": ["IND"]},
        dataset_ids=[],
        version="1.0.0",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Case 1: Bowler (Role exclusion)
    bowler_score = _create_mock_player_score(
        player_id="P_BOWL", name="Pacer", role=PlayerRole.BOWLER, vor=80.0, raw=80.0, balls_faced=5, legal_balls=100
    )
    p_rec1 = Player(player_id="P_BOWL", canonical_name="Pacer", is_eligible=True, dob=date(2004, 5, 10), nationality="IND")
    eval_bowler = EligibilityEngine.evaluate_player(bowler_score, config, p_rec1)
    assert not eval_bowler.is_eligible
    assert any("not in configured competition roles" in r for r in eval_bowler.exclusion_reasons)

    # Case 2: Batter too old (DOB = 2000-01-01 -> Age 26 > max_age 23)
    batter_old = _create_mock_player_score(
        player_id="P_OLD", name="Veteran", role=PlayerRole.BATTER, vor=85.0, raw=85.0, balls_faced=200, legal_balls=0
    )
    p_rec2 = Player(player_id="P_OLD", canonical_name="Veteran", is_eligible=True, dob=date(2000, 1, 1), nationality="IND")
    eval_old = EligibilityEngine.evaluate_player(batter_old, config, p_rec2)
    assert not eval_old.is_eligible
    assert any("exceeds maximum age requirement" in r for r in eval_old.exclusion_reasons)

    # Case 3: Batter under workload threshold (balls_faced = 20 < 50)
    batter_micro = _create_mock_player_score(
        player_id="P_MICRO", name="Rookie", role=PlayerRole.BATTER, vor=60.0, raw=60.0, balls_faced=20, legal_balls=0
    )
    p_rec3 = Player(player_id="P_MICRO", canonical_name="Rookie", is_eligible=True, dob=date(2004, 3, 1), nationality="IND")
    eval_micro = EligibilityEngine.evaluate_player(batter_micro, config, p_rec3)
    assert not eval_micro.is_eligible
    assert any("Balls faced (20) is below minimum requirement" in r for r in eval_micro.exclusion_reasons)

    # Case 4: Fully eligible batter (Age 21, balls_faced 150, IND, BATTER)
    batter_valid = _create_mock_player_score(
        player_id="P_VALID", name="Prime Prospect", role=PlayerRole.BATTER, vor=78.0, raw=78.0, balls_faced=150, legal_balls=0
    )
    p_rec4 = Player(player_id="P_VALID", canonical_name="Prime Prospect", is_eligible=True, dob=date(2005, 2, 1), nationality="IND")
    eval_valid = EligibilityEngine.evaluate_player(batter_valid, config, p_rec4)
    assert eval_valid.is_eligible
    assert len(eval_valid.exclusion_reasons) == 0


# ==============================================================================
# 4. SHORTLIST GENERATION & CONSUMPTION OF SCORING RUNS
# ==============================================================================

@pytest.mark.anyio
async def test_shortlist_generation_from_scoring_run(mock_scoring_run_data):
    """Verify shortlist generation consumes existing scoring run outputs without re-scoring."""
    ds_id = mock_scoring_run_data["dataset_id"]
    run_id = mock_scoring_run_data["run_id"]

    async for session in get_db_session():
        ws_service = WorkspaceService(session)
        sl_service = ShortlistingService(session)

        ws_id = f"ws_gen_{uuid.uuid4().hex[:6]}"
        await ws_service.create_workspace(
            WorkspaceCreate(
                workspace_id=ws_id,
                name="Shortlist Generation Test",
                competition_name="SuperRR",
                season_or_edition="S2",
                initial_configuration=CompetitionConfigCreate(
                    target_roles=["BATTER"],  # Filter out Bowler
                    shortlist_size=2,
                ),
            )
        )

        # Generate shortlist
        shortlist = await sl_service.generate_shortlist(
            workspace_id=ws_id,
            payload=ShortlistGenerateRequest(
                name="Top Emerging Batters",
                dataset_id=ds_id,
                scoring_run_id=run_id,
                override_shortlist_size=2,
            ),
        )

        assert shortlist.workspace_id == ws_id
        assert shortlist.shortlisted_count == 2
        assert len(shortlist.candidates) == 2

        # Verify candidate rank order is determined by existing VOR score
        # Top 1: P_BAT_TOP1 (VOR 82.5, Rank 1)
        # Top 2: P_BAT_TOP2 (VOR 74.0, Rank 2)
        c1, c2 = shortlist.candidates[0], shortlist.candidates[1]
        assert c1.player_id == "P_BAT_TOP1"
        assert c1.rank == 1
        assert c1.vor_score == 82.5
        assert c1.review_status == ReviewStatus.PENDING

        assert c2.player_id == "P_BAT_TOP2"
        assert c2.rank == 2
        assert c2.vor_score == 74.0

        # Verify Bowler was excluded and logged with explicit reason
        assert "P_BOWL_TOP1" in shortlist.exclusion_summary
        assert any("not in configured competition roles" in r for r in shortlist.exclusion_summary["P_BOWL_TOP1"])


@pytest.mark.anyio
async def test_shortlist_generation_rejects_missing_scoring_run():
    """Verify explicit error response when attempting to generate shortlist without completed scoring data."""
    async for session in get_db_session():
        ws_service = WorkspaceService(session)
        sl_service = ShortlistingService(session)

        ws_id = f"ws_empty_{uuid.uuid4().hex[:6]}"
        await ws_service.create_workspace(
            WorkspaceCreate(workspace_id=ws_id, name="Empty WS", competition_name="Test", season_or_edition="1")
        )

        with pytest.raises(ValidationException) as exc_info:
            await sl_service.generate_shortlist(
                workspace_id=ws_id,
                payload=ShortlistGenerateRequest(dataset_id="NON_EXISTENT_DATASET_ID"),
            )
        assert "No completed scoring run available" in str(exc_info.value)


# ==============================================================================
# 5. SHORTLIST REVIEW LIFECYCLE TESTS
# ==============================================================================

@pytest.mark.anyio
async def test_shortlist_candidate_review_workflow(mock_scoring_run_data):
    """Verify reviewer approval/rejection without mutating underlying evaluation and VOR scores."""
    ds_id = mock_scoring_run_data["dataset_id"]
    run_id = mock_scoring_run_data["run_id"]

    async for session in get_db_session():
        ws_service = WorkspaceService(session)
        sl_service = ShortlistingService(session)

        ws_id = f"ws_review_{uuid.uuid4().hex[:6]}"
        await ws_service.create_workspace(
            WorkspaceCreate(
                workspace_id=ws_id,
                name="Review Test Workspace",
                competition_name="RR Trials",
                season_or_edition="2026",
            )
        )

        shortlist = await sl_service.generate_shortlist(
            workspace_id=ws_id,
            payload=ShortlistGenerateRequest(
                dataset_id=ds_id, scoring_run_id=run_id, override_shortlist_size=2
            ),
        )
        sl_id = shortlist.shortlist_id
        target_player_id = shortlist.candidates[0].player_id
        original_vor = shortlist.candidates[0].vor_score

        # Scout approves candidate with notes
        reviewed = await sl_service.review_candidate(
            workspace_id=ws_id,
            shortlist_id=sl_id,
            player_id=target_player_id,
            payload=ShortlistReviewRequest(
                review_status=ReviewStatus.APPROVED,
                reviewer_notes="High boundary percentage against spin bowling in middle overs.",
            ),
        )

        assert reviewed.player_id == target_player_id
        assert reviewed.review_status == ReviewStatus.APPROVED
        assert reviewed.reviewer_notes == "High boundary percentage against spin bowling in middle overs."
        # Verify original VOR score was not overwritten or mutated
        assert reviewed.vor_score == original_vor


# ==============================================================================
# 6. AUDIT TRAIL & REPRODUCIBILITY TESTS
# ==============================================================================

@pytest.mark.anyio
async def test_shortlist_audit_log_and_reproducible_generation(mock_scoring_run_data):
    """Verify audit log records methodology versions, exclusion reasons, and deterministic outputs."""
    ds_id = mock_scoring_run_data["dataset_id"]
    run_id = mock_scoring_run_data["run_id"]

    async for session in get_db_session():
        ws_service = WorkspaceService(session)
        sl_service = ShortlistingService(session)

        ws_id = f"ws_audit_{uuid.uuid4().hex[:6]}"
        await ws_service.create_workspace(
            WorkspaceCreate(
                workspace_id=ws_id,
                name="Audit Reproducibility Workspace",
                competition_name="RR Draft",
                season_or_edition="2026",
                initial_configuration=CompetitionConfigCreate(shortlist_size=2),
            )
        )

        # Iteration 1
        sl1 = await sl_service.generate_shortlist(
            workspace_id=ws_id,
            payload=ShortlistGenerateRequest(
                name="Run 1", dataset_id=ds_id, scoring_run_id=run_id
            ),
        )

        # Audit lookup
        audit = await sl_service.get_audit_log(ws_id, sl1.shortlist_id)
        assert audit.shortlist_id == sl1.shortlist_id
        assert audit.workspace_id == ws_id
        assert audit.dataset_id == ds_id
        assert audit.configuration_version == "1.0.0"
        assert audit.ranking_engine_version == "1.0.0"
        assert audit.shortlisted_candidate_count == 2
        assert isinstance(audit.exclusion_details, dict)

        # Iteration 2 (Duplicate request) - Must produce identical ordered candidates
        sl2 = await sl_service.generate_shortlist(
            workspace_id=ws_id,
            payload=ShortlistGenerateRequest(
                name="Run 2", dataset_id=ds_id, scoring_run_id=run_id
            ),
        )
        assert [c.player_id for c in sl1.candidates] == [c.player_id for c in sl2.candidates]
        assert [c.vor_score for c in sl1.candidates] == [c.vor_score for c in sl2.candidates]


# ==============================================================================
# 7. FULL REST API INTEGRATION LIFECYCLE
# ==============================================================================

@pytest.mark.anyio
async def test_api_workspace_and_shortlist_end_to_end_lifecycle(mock_scoring_run_data):
    """Verify full end-to-end HTTP API lifecycle for workspaces, configurations, shortlists, reviews, and audits."""
    ds_id = mock_scoring_run_data["dataset_id"]
    run_id = mock_scoring_run_data["run_id"]
    ws_id = f"ws_api_{uuid.uuid4().hex[:6]}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Workspace
        create_resp = await client.post(
            "/api/v1/workspaces",
            json={
                "workspace_id": ws_id,
                "name": "SuperRR Official Scouting Workspace",
                "competition_name": "SuperRR Selector",
                "season_or_edition": "Season 2",
                "initial_configuration": {
                    "shortlist_size": 3,
                    "target_roles": ["BATTER", "BOWLER"],
                },
            },
        )
        assert create_resp.status_code == 201
        ws_data = create_resp.json()
        assert ws_data["workspace_id"] == ws_id
        assert ws_data["status"] == "DRAFT"

        # 2. List Workspaces
        list_resp = await client.get("/api/v1/workspaces")
        assert list_resp.status_code == 200
        assert any(w["workspace_id"] == ws_id for w in list_resp.json())

        # 3. Retrieve Workspace Detail
        get_resp = await client.get(f"/api/v1/workspaces/{ws_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "SuperRR Official Scouting Workspace"

        # 4. Update Configuration
        cfg_resp = await client.put(
            f"/api/v1/workspaces/{ws_id}/configuration",
            json={
                "shortlist_size": 2,
                "target_roles": ["BATTER"],
            },
        )
        assert cfg_resp.status_code == 200
        assert cfg_resp.json()["shortlist_size"] == 2
        assert cfg_resp.json()["target_roles"] == ["BATTER"]

        # 5. Generate Shortlist
        sl_resp = await client.post(
            f"/api/v1/workspaces/{ws_id}/shortlists",
            json={
                "name": "SuperRR Official Top 2 Batters",
                "dataset_id": ds_id,
                "scoring_run_id": run_id,
            },
        )
        assert sl_resp.status_code == 201
        sl_data = sl_resp.json()
        sl_id = sl_data["shortlist_id"]
        assert sl_data["shortlisted_count"] == 2
        assert len(sl_data["candidates"]) == 2

        # 6. Retrieve Shortlist Detail
        sl_detail = await client.get(f"/api/v1/workspaces/{ws_id}/shortlists/{sl_id}")
        assert sl_detail.status_code == 200
        assert sl_detail.json()["shortlist_id"] == sl_id

        # 7. Review Candidate
        cand_id = sl_data["candidates"][0]["player_id"]
        review_resp = await client.post(
            f"/api/v1/workspaces/{ws_id}/shortlists/{sl_id}/candidates/{cand_id}/review",
            json={
                "review_status": "APPROVED",
                "reviewer_notes": "Confirmed top prospect for franchise draft.",
            },
        )
        assert review_resp.status_code == 200
        assert review_resp.json()["review_status"] == "APPROVED"
        assert review_resp.json()["reviewer_notes"] == "Confirmed top prospect for franchise draft."

        # 8. Retrieve Audit Trail
        audit_resp = await client.get(f"/api/v1/workspaces/{ws_id}/shortlists/{sl_id}/audit")
        assert audit_resp.status_code == 200
        assert audit_resp.json()["shortlist_id"] == sl_id
        assert audit_resp.json()["shortlisted_candidate_count"] == 2

