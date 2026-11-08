"""Comprehensive automated tests for VYNTIQ Player Role Classification & Evaluation Framework.

Validates:
1. Role Classification System:
   - Explicit source roles (CONFIRMED_FROM_SOURCE).
   - Data-driven Batter classification (BATTING_VOLUME_DOMINANCE).
   - Data-driven Bowler classification (BOWLING_VOLUME_DOMINANCE).
   - Data-driven All-Rounder classification (DUAL_DISCIPLINE_VOLUME_MET).
   - Wicketkeeper with supporting dismissal evidence (CLASSIFIED_FROM_DATA).
   - Insufficient sample volume handling (INSUFFICIENT_DATA / UNKNOWN).
   - Ambiguous borderline participation and source contradiction handling (AMBIGUOUS).
2. Sample Adequacy Evaluator:
   - ADEQUATE, LIMITED, INSUFFICIENT, and NOT_APPLICABLE statuses.
   - Separation of volume from skill/performance.
3. Role-Specific Evaluation Profiles:
   - Batter profile (Scoring Output, Scoring Efficiency, Resistance, Consistency).
   - Bowler profile (Wickets, Containment, Dot Balls, Workload, Boundaries).
   - All-Rounder profile (separate batting and bowling sections, NO combined score).
   - Wicketkeeper profile (handling DATA_UNAVAILABLE when fielding records are absent).
4. Central Dimension Registry.
5. Evaluation REST Endpoints:
   - GET /api/v1/evaluation/dimensions
   - POST /api/v1/evaluation/classify
   - GET /api/v1/evaluation/players/{player_id}
   - POST /api/v1/evaluation/dataset/{dataset_id}
"""

import uuid
import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.core.database import async_session_factory
from backend.app.main import app
from backend.app.models.cricket import Delivery, Player
from backend.app.models.dataset import Dataset
from backend.app.schemas.evaluation import (
    DimensionAvailabilityStatus,
    PlayerRole,
    RoleClassificationStatus,
    SampleAdequacyStatus,
)
from backend.app.schemas.metrics import SampleSizeInfo
from backend.app.services.evaluation.adequacy import SampleAdequacyEvaluator
from backend.app.services.evaluation.classifier import RoleClassifier
from backend.app.services.evaluation.config import RoleClassificationConfig
from backend.app.services.evaluation.profiles import ProfileBuilder
from backend.app.services.evaluation.registry import (
    get_all_evaluation_dimensions,
    get_dimension_definition,
)
from backend.app.services.evaluation.service import EvaluationService


# ==============================================================================
# 1. ROLE CLASSIFICATION TESTS
# ==============================================================================

def test_role_classification_explicit_source_confirmed():
    """Verify that valid explicit source roles are preserved and confirmed."""
    classifier = RoleClassifier()
    sample = SampleSizeInfo(balls_faced=80, legal_balls_bowled=0, matches_played=4)

    # Valid Batter source role
    res_bat = classifier.classify_player("P_01", sample, source_role="BATTER")
    assert res_bat.assigned_role == PlayerRole.BATTER
    assert res_bat.status == RoleClassificationStatus.CONFIRMED_FROM_SOURCE
    assert res_bat.confidence == "HIGH"

    # Valid Bowler source role
    sample_bowl = SampleSizeInfo(balls_faced=4, legal_balls_bowled=96, matches_played=4)
    res_bowl = classifier.classify_player("P_02", sample_bowl, source_role="FAST_BOWLER")
    assert res_bowl.assigned_role == PlayerRole.BOWLER
    assert res_bowl.status == RoleClassificationStatus.CONFIRMED_FROM_SOURCE

    # Valid All-Rounder source role
    sample_ar = SampleSizeInfo(balls_faced=60, legal_balls_bowled=72, matches_played=4)
    res_ar = classifier.classify_player("P_03", sample_ar, source_role="ALL_ROUNDER")
    assert res_ar.assigned_role == PlayerRole.ALL_ROUNDER
    assert res_ar.status == RoleClassificationStatus.CONFIRMED_FROM_SOURCE


def test_role_classification_source_contradiction_flags_ambiguous():
    """Verify that explicit source roles that flagrantly contradict empirical data return AMBIGUOUS."""
    classifier = RoleClassifier()
    # Source says BOWLER, but player faced 80 balls and bowled 0 balls across 4 matches
    sample = SampleSizeInfo(balls_faced=80, legal_balls_bowled=0, matches_played=4)
    res = classifier.classify_player("P_ERR", sample, source_role="BOWLER")

    assert res.assigned_role == PlayerRole.UNKNOWN
    assert res.status == RoleClassificationStatus.AMBIGUOUS
    assert res.confidence == "LOW"
    assert "contradict" in res.missing_information[0].lower() or "bowler" in res.missing_information[0].lower()


def test_role_classification_from_data_batter():
    """Verify data-driven classification of specialist batter when source role is missing."""
    classifier = RoleClassifier()
    # 65 balls faced, 0 balls bowled
    sample = SampleSizeInfo(balls_faced=65, legal_balls_bowled=0, matches_played=3)
    res = classifier.classify_player("P_DATA_BAT", sample, source_role=None)

    assert res.assigned_role == PlayerRole.BATTER
    assert res.status == RoleClassificationStatus.CLASSIFIED_FROM_DATA
    assert res.classification_method == "BATTING_VOLUME_DOMINANCE"


def test_role_classification_from_data_bowler():
    """Verify data-driven classification of specialist bowler when source role is missing."""
    classifier = RoleClassifier()
    # 6 balls faced, 60 legal balls bowled (10 overs)
    sample = SampleSizeInfo(balls_faced=6, legal_balls_bowled=60, matches_played=3)
    res = classifier.classify_player("P_DATA_BOWL", sample, source_role=None)

    assert res.assigned_role == PlayerRole.BOWLER
    assert res.status == RoleClassificationStatus.CLASSIFIED_FROM_DATA
    assert res.classification_method == "BOWLING_VOLUME_DOMINANCE"


def test_role_classification_from_data_all_rounder():
    """Verify that dual participation across both disciplines classifies as ALL_ROUNDER."""
    classifier = RoleClassifier()
    # 50 balls faced, 54 legal balls bowled (9 overs) -> meets both 36 and 48 thresholds
    sample = SampleSizeInfo(balls_faced=50, legal_balls_bowled=54, matches_played=4)
    res = classifier.classify_player("P_DATA_AR", sample, source_role=None)

    assert res.assigned_role == PlayerRole.ALL_ROUNDER
    assert res.status == RoleClassificationStatus.CLASSIFIED_FROM_DATA
    assert res.classification_method == "DUAL_DISCIPLINE_VOLUME_MET"


def test_role_classification_part_time_bowler_not_all_rounder():
    """Verify that occasional / part-time bowling (e.g. 6 balls) does NOT classify as an all-rounder."""
    classifier = RoleClassifier()
    # 80 balls faced, only 6 balls bowled (1 over)
    sample = SampleSizeInfo(balls_faced=80, legal_balls_bowled=6, matches_played=4)
    res = classifier.classify_player("P_PART_TIME", sample, source_role=None)

    # Must be classified as specialist BATTER, not all-rounder!
    assert res.assigned_role == PlayerRole.BATTER
    assert res.assigned_role != PlayerRole.ALL_ROUNDER


def test_role_classification_wicketkeeper_evidence():
    """Verify that wicketkeeper classification requires explicit supporting evidence (stumpings/catches)."""
    classifier = RoleClassifier()
    sample = SampleSizeInfo(balls_faced=70, legal_balls_bowled=0, matches_played=3)

    # With wicketkeeping dismissals
    res_wk = classifier.classify_player("P_WK", sample, source_role=None, wicketkeeping_dismissals=2)
    assert res_wk.assigned_role == PlayerRole.WICKETKEEPER
    assert res_wk.status == RoleClassificationStatus.CLASSIFIED_FROM_DATA

    # Without wicketkeeping dismissals and no source role -> regular batter
    res_no_wk = classifier.classify_player("P_NO_WK", sample, source_role=None, wicketkeeping_dismissals=0)
    assert res_no_wk.assigned_role == PlayerRole.BATTER


def test_role_classification_insufficient_sample():
    """Verify that micro-samples below thresholds return INSUFFICIENT_DATA and UNKNOWN role."""
    classifier = RoleClassifier()
    # Only 5 balls faced and 0 bowled
    sample = SampleSizeInfo(balls_faced=5, legal_balls_bowled=0, matches_played=1)
    res = classifier.classify_player("P_NEW", sample, source_role=None)

    assert res.assigned_role == PlayerRole.UNKNOWN
    assert res.status == RoleClassificationStatus.INSUFFICIENT_DATA


def test_role_classification_custom_config_override():
    """Verify that configurable thresholds are respected when altered."""
    custom_cfg = RoleClassificationConfig(min_balls_faced_for_batter=15)
    classifier = RoleClassifier(config=custom_cfg)

    # 20 balls faced: below default (30), but above custom (15)
    sample = SampleSizeInfo(balls_faced=20, legal_balls_bowled=0, matches_played=1)
    res = classifier.classify_player("P_CUSTOM", sample, source_role=None)

    assert res.assigned_role == PlayerRole.BATTER
    assert res.classification_version == custom_cfg.version


# ==============================================================================
# 2. SAMPLE ADEQUACY TESTS
# ==============================================================================

def test_sample_adequacy_assessment():
    """Verify ADEQUATE, LIMITED, INSUFFICIENT, and NOT_APPLICABLE status assignment."""
    evaluator = SampleAdequacyEvaluator()

    # Batter with 70 balls -> ADEQUATE
    sample_adequate_bat = SampleSizeInfo(balls_faced=70, legal_balls_bowled=0)
    res_bat = evaluator.assess_adequacy(PlayerRole.BATTER, sample_adequate_bat)
    assert res_bat.batting == SampleAdequacyStatus.ADEQUATE
    assert res_bat.bowling == SampleAdequacyStatus.NOT_APPLICABLE
    assert res_bat.overall == SampleAdequacyStatus.ADEQUATE

    # Batter with 25 balls -> LIMITED
    sample_limited_bat = SampleSizeInfo(balls_faced=25, legal_balls_bowled=0)
    res_lim = evaluator.assess_adequacy(PlayerRole.BATTER, sample_limited_bat)
    assert res_lim.batting == SampleAdequacyStatus.LIMITED
    assert res_lim.overall == SampleAdequacyStatus.LIMITED

    # Batter with 10 balls -> INSUFFICIENT
    sample_insuf_bat = SampleSizeInfo(balls_faced=10, legal_balls_bowled=0)
    res_insuf = evaluator.assess_adequacy(PlayerRole.BATTER, sample_insuf_bat)
    assert res_insuf.batting == SampleAdequacyStatus.INSUFFICIENT
    assert res_insuf.overall == SampleAdequacyStatus.INSUFFICIENT

    # Bowler with 80 legal balls (13.2 overs) -> ADEQUATE
    sample_adequate_bowl = SampleSizeInfo(balls_faced=2, legal_balls_bowled=80)
    res_bowl = evaluator.assess_adequacy(PlayerRole.BOWLER, sample_adequate_bowl)
    assert res_bowl.bowling == SampleAdequacyStatus.ADEQUATE
    assert res_bowl.batting == SampleAdequacyStatus.NOT_APPLICABLE
    assert res_bowl.overall == SampleAdequacyStatus.ADEQUATE

    # All-Rounder: requires BOTH to be adequate for overall ADEQUATE
    sample_ar_skew = SampleSizeInfo(balls_faced=80, legal_balls_bowled=30)  # Bat ADEQUATE, Bowl LIMITED
    res_ar_skew = evaluator.assess_adequacy(PlayerRole.ALL_ROUNDER, sample_ar_skew)
    assert res_ar_skew.batting == SampleAdequacyStatus.ADEQUATE
    assert res_ar_skew.bowling == SampleAdequacyStatus.LIMITED
    assert res_ar_skew.overall == SampleAdequacyStatus.LIMITED  # Governed by the limiting discipline!


# ==============================================================================
# 3. DIMENSION REGISTRY & PROFILE BUILDER TESTS
# ==============================================================================

def test_dimension_registry_metadata():
    """Verify metadata completeness in the evaluation dimension registry."""
    dims = get_all_evaluation_dimensions()
    assert len(dims) >= 10

    scoring_out = get_dimension_definition("scoring_output")
    assert scoring_out is not None
    assert "BATTER" in scoring_out.applicable_roles
    assert "runs_scored" in scoring_out.associated_metrics

    wicket_threat = get_dimension_definition("wicket_taking_performance")
    assert wicket_threat is not None
    assert "BOWLER" in wicket_threat.applicable_roles
    assert "wickets_taken" in wicket_threat.associated_metrics


def test_role_specific_profile_builder_separation():
    """Verify that Batter, Bowler, and All-Rounder receive strictly role-appropriate dimensions."""
    builder = ProfileBuilder()
    mock_sample = SampleSizeInfo(balls_faced=80, legal_balls_bowled=84, times_dismissed=2, matches_played=4)

    # Empty mock metrics dictionaries
    mock_batting = {}
    mock_bowling = {}

    # 1. Batter Profile: Only batting dimensions
    bat_profile = builder.build_profile(PlayerRole.BATTER, mock_batting, mock_bowling, mock_sample)
    assert "scoring_output" in bat_profile
    assert "scoring_efficiency" in bat_profile
    assert "boundary_contribution" in bat_profile
    assert "dismissal_resistance" in bat_profile
    assert "consistency" in bat_profile
    assert "wicket_taking_performance" not in bat_profile
    assert "run_containment" not in bat_profile

    # 2. Bowler Profile: Only bowling dimensions
    bowl_profile = builder.build_profile(PlayerRole.BOWLER, mock_batting, mock_bowling, mock_sample)
    assert "wicket_taking_performance" in bowl_profile
    assert "run_containment" in bowl_profile
    assert "dot_ball_generation" in bowl_profile
    assert "bowling_workload" in bowl_profile
    assert "boundary_containment" in bowl_profile
    assert "scoring_output" not in bowl_profile

    # 3. All-Rounder Profile: Contains BOTH batting and bowling dimensions, completely unblended
    ar_profile = builder.build_profile(PlayerRole.ALL_ROUNDER, mock_batting, mock_bowling, mock_sample)
    assert "scoring_output" in ar_profile
    assert "wicket_taking_performance" in ar_profile
    assert "run_containment" in ar_profile
    assert "scoring_efficiency" in ar_profile

    # 4. Wicketkeeper Profile without fielding data: wicketkeeping_dismissals marked DATA_UNAVAILABLE
    wk_profile = builder.build_profile(PlayerRole.WICKETKEEPER, mock_batting, mock_bowling, mock_sample, fielding_data=None)
    assert "wicketkeeping_dismissals" in wk_profile
    assert wk_profile["wicketkeeping_dismissals"].status == DimensionAvailabilityStatus.DATA_UNAVAILABLE


# ==============================================================================
# 4. END-TO-END SERVICE & REST API INTEGRATION TESTS
# ==============================================================================

@pytest.fixture
def multi_role_synthetic_deliveries() -> pd.DataFrame:
    """Synthetic dataset with 3 players: 1 Batter, 1 Bowler, and 1 All-Rounder."""
    records = []
    # Batter: P_BAT_SPEC (faces 40 balls, never bowls)
    for i in range(40):
        records.append({
            "delivery_id": f"DEL_BAT_{i}",
            "match_id": "MATCH_01" if i < 20 else "MATCH_02",
            "innings_num": 1,
            "over_number": i // 6,
            "ball_number": (i % 6) + 1,
            "over_delivery": float(f"{i // 6}.{(i % 6) + 1}"),
            "phase": "POWERPLAY" if i < 18 else "MIDDLE",
            "batter_id": "P_BAT_SPEC",
            "bowler_id": "P_BOWL_OPP",
            "batter_runs": 1 if i % 2 == 0 else 4,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 1 if i % 2 == 0 else 4,
            "is_wicket": i == 39,
            "dismissed_player_id": "P_BAT_SPEC" if i == 39 else None,
            "dismissal_kind": "caught" if i == 39 else None,
            "is_super_over": False,
        })

    # Bowler: P_BOWL_SPEC (bowls 48 legal balls, never bats)
    for i in range(48):
        records.append({
            "delivery_id": f"DEL_BOWL_{i}",
            "match_id": "MATCH_01" if i < 24 else "MATCH_02",
            "innings_num": 2,
            "over_number": i // 6,
            "ball_number": (i % 6) + 1,
            "over_delivery": float(f"{i // 6}.{(i % 6) + 1}"),
            "phase": "POWERPLAY" if i < 12 else ("MIDDLE" if i < 36 else "DEATH"),
            "batter_id": "P_BAT_OPP",
            "bowler_id": "P_BOWL_SPEC",
            "batter_runs": 0 if i % 3 == 0 else 1,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 0 if i % 3 == 0 else 1,
            "is_wicket": i in (10, 25),
            "dismissed_player_id": "P_BAT_OPP" if i in (10, 25) else None,
            "dismissal_kind": "bowled" if i in (10, 25) else None,
            "is_super_over": False,
        })

    # All-Rounder: P_AR_SPEC (faces 40 balls, bowls 48 legal balls)
    for i in range(40):
        records.append({
            "delivery_id": f"DEL_AR_BAT_{i}",
            "match_id": "MATCH_01" if i < 20 else "MATCH_02",
            "innings_num": 1,
            "over_number": i // 6,
            "ball_number": (i % 6) + 1,
            "over_delivery": float(f"{i // 6}.{(i % 6) + 1}"),
            "phase": "MIDDLE",
            "batter_id": "P_AR_SPEC",
            "bowler_id": "P_BOWL_OPP",
            "batter_runs": 2,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 2,
            "is_wicket": False,
            "dismissed_player_id": None,
            "dismissal_kind": None,
            "is_super_over": False,
        })

    for i in range(48):
        records.append({
            "delivery_id": f"DEL_AR_BOWL_{i}",
            "match_id": "MATCH_01" if i < 24 else "MATCH_02",
            "innings_num": 2,
            "over_number": i // 6,
            "ball_number": (i % 6) + 1,
            "over_delivery": float(f"{i // 6}.{(i % 6) + 1}"),
            "phase": "MIDDLE",
            "batter_id": "P_BAT_OPP",
            "bowler_id": "P_AR_SPEC",
            "batter_runs": 1,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 1,
            "is_wicket": i == 20,
            "dismissed_player_id": "P_BAT_OPP" if i == 20 else None,
            "dismissal_kind": "lbw" if i == 20 else None,
            "is_super_over": False,
        })

    return pd.DataFrame(records)


def test_evaluation_service_multi_role_dataset(multi_role_synthetic_deliveries):
    """Verify that EvaluationService classifies multiple players and builds correct profiles."""
    service = EvaluationService()
    res = service.evaluate_dataset_from_dataframe(
        dataset_id="TEST_MULTI_ROLE_DS",
        df=multi_role_synthetic_deliveries,
    )

    assert res.total_evaluated_players >= 3
    player_roles = {p.player_id: p.role.assigned_role for p in res.players}

    assert player_roles["P_BAT_SPEC"] == PlayerRole.BATTER
    assert player_roles["P_BOWL_SPEC"] == PlayerRole.BOWLER
    assert player_roles["P_AR_SPEC"] == PlayerRole.ALL_ROUNDER

    # Check that P_AR_SPEC evaluation profile has BOTH batting and bowling dimensions
    ar_eval = next(p for p in res.players if p.player_id == "P_AR_SPEC")
    assert "scoring_output" in ar_eval.evaluation_profile
    assert "wicket_taking_performance" in ar_eval.evaluation_profile


@pytest.mark.anyio
async def test_api_evaluation_dimensions_endpoint():
    """Verify GET /api/v1/evaluation/dimensions returns all registered evaluation dimensions."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/evaluation/dimensions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_dimensions"] >= 10
        dim_ids = [d["dimension_id"] for d in data["dimensions"]]
        assert "scoring_output" in dim_ids
        assert "wicket_taking_performance" in dim_ids
        assert "wicketkeeping_dismissals" in dim_ids


@pytest.mark.anyio
async def test_api_evaluation_dataset_and_classify_endpoints(multi_role_synthetic_deliveries):
    """Verify POST /api/v1/evaluation/classify, POST /api/v1/evaluation/dataset/{id}, and GET /players/{id}."""
    unique_ds_id = f"DS_EVAL_{uuid.uuid4().hex[:8]}"

    # Seed test dataset and deliveries in SQLite
    async with async_session_factory() as session:
        ds = Dataset(
            dataset_id=unique_ds_id,
            workspace_id="default_workspace",
            source_filename="test_eval.csv",
            file_format="CSV",
            file_sha256=f"hash_{unique_ds_id}",
            storage_path="/tmp/eval.csv",
            status="PERSISTED",
        )
        session.add(ds)

        # Seed players
        for p_id, p_name in [
            ("P_BAT_SPEC", "Specialist Batter"),
            ("P_BOWL_SPEC", "Specialist Bowler"),
            ("P_AR_SPEC", "Genuine All-Rounder"),
        ]:
            p = Player(player_id=p_id, canonical_name=p_name)
            # Use merge to avoid collisions across test runs
            await session.merge(p)

        # Add deliveries
        for _, row in multi_role_synthetic_deliveries.iterrows():
            d = Delivery(
                delivery_id=f"{unique_ds_id}_{row['delivery_id']}",
                dataset_id=unique_ds_id,
                workspace_id="default_workspace",
                origin_type="COMPETITION_SANDBOX",
                match_id=row["match_id"],
                innings_num=row["innings_num"],
                over_number=row["over_number"],
                ball_number=row["ball_number"],
                over_delivery=row["over_delivery"],
                phase=row["phase"],
                batter_id=row["batter_id"],
                bowler_id=row["bowler_id"],
                batter_runs=row["batter_runs"],
                extras_runs=row["extras_runs"],
                extras_type=row["extras_type"],
                is_legal=row["is_legal"],
                total_runs=row["total_runs"],
                is_wicket=row["is_wicket"],
                dismissed_player_id=row["dismissed_player_id"],
                dismissal_kind=row["dismissal_kind"],
                is_super_over=False,
            )
            session.add(d)

        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. POST /api/v1/evaluation/classify
        classify_resp = await client.post(
            "/api/v1/evaluation/classify",
            json={"dataset_id": unique_ds_id},
        )
        assert classify_resp.status_code == 200
        roles_list = classify_resp.json()
        assert len(roles_list) >= 3
        roles_dict = {r["player_id"]: r["assigned_role"] for r in roles_list}
        assert roles_dict.get("P_BAT_SPEC") == "BATTER"
        assert roles_dict.get("P_BOWL_SPEC") == "BOWLER"
        assert roles_dict.get("P_AR_SPEC") == "ALL_ROUNDER"

        # 2. POST /api/v1/evaluation/dataset/{id}
        eval_resp = await client.post(f"/api/v1/evaluation/dataset/{unique_ds_id}")
        assert eval_resp.status_code == 200
        eval_data = eval_resp.json()
        assert eval_data["total_evaluated_players"] >= 3
        assert "BATTER" in eval_data["role_distribution"]

        # 3. GET /api/v1/evaluation/players/{player_id}
        p_resp = await client.get("/api/v1/evaluation/players/P_BAT_SPEC")
        assert p_resp.status_code == 200
        p_data = p_resp.json()
        assert p_data["player_id"] == "P_BAT_SPEC"
        assert p_data["role"]["assigned_role"] == "BATTER"
        assert "scoring_output" in p_data["evaluation_profile"]
        assert "wicket_taking_performance" not in p_data["evaluation_profile"]
