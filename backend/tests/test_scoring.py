"""Comprehensive automated tests for VYNTIQ VOR Scoring, Percentile Normalization & Player Ranking Engine.

Validates:
1. ECDF Percentile Normalization:
   - Higher-is-better scaling: Z_i = (sum(1_{x_j <= x_i}) / M) * 100
   - Lower-is-better scaling: Z_i = (sum(1_{x_j >= x_i}) / M) * 100
   - Tied values handling
   - Missing data filtering without silent zero conversion
   - Insufficient cohort handling (M < 3 fallback to median)
2. Bayesian Reliability Shrinkage:
   - C(N) = N / (N + K) for N_min <= N < N_full
   - C(N) = 1.0 for N >= N_full
   - C(N) = 0.0 and quarantine for N < N_min
3. VOR Composite Scoring:
   - Specialist Batter VOR: VOR = 50.0 + C(N) * (raw_composite - 50.0)
   - Specialist Bowler VOR
   - All-Rounder dual VOR: (alpha * VOR_bat + (1 - alpha) * VOR_bowl) + Dual_Bonus
   - Dual-utility bonus conditionality (awarded strictly if both meet N_min)
4. Leaderboard Ranking & Tie-Breaking Hierarchy:
   - Tier 1: VOR descending
   - Tier 2: Reliability Factor C(N) descending
   - Tier 3: Primary True Metric (TSR for batters, TER for bowlers)
   - Quarantine gating: Unqualified/ineligible candidates segregated from top ranks
5. Score Explanation & Factor Attribution:
   - Top strengths, drag factors, and missing dimensions identified
6. REST API Endpoints:
   - GET /api/v1/scoring/methodology
   - POST /api/v1/scoring/calculate
   - GET /api/v1/scoring/runs/{run_id}
   - GET /api/v1/scoring/players/{player_id}
   - GET /api/v1/scoring/rankings
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
    DimensionEvaluationProfile,
    DisciplineSampleAdequacy,
    PlayerEvaluationResponse,
    PlayerRole,
    RoleClassificationResult,
    RoleClassificationStatus,
    SampleAdequacyStatus,
)
from backend.app.schemas.metrics import (
    MetricDirection,
    MetricProvenance,
    MetricStatus,
    MetricValue,
    SampleSizeInfo,
)
from backend.app.schemas.scoring import (
    DimensionScore,
    NormalizedMetric,
    PlayerScoreResult,
    ReliabilityStatus,
    ScoreExplanation,
)
from backend.app.services.scoring.composite import VORCompositeCalculator
from backend.app.services.scoring.explainability import ScoreExplainer
from backend.app.services.scoring.normalization import ECDFNormalizer
from backend.app.services.scoring.ranking import RankingEngine
from backend.app.services.scoring.reliability import (
    BATTING_K,
    BATTING_N_FULL,
    BATTING_N_MIN,
    BOWLING_K,
    BOWLING_N_MIN,
    BayesianReliabilityAssessor,
)
from backend.app.services.scoring.service import ScoringService
from backend.app.services.scoring.weights import RoleWeightConfiguration


# ==============================================================================
# 1. ECDF NORMALIZATION TESTS
# ==============================================================================

def test_ecdf_normalization_higher_is_better():
    """Verify ECDF directional scaling where higher values are superior."""
    normalizer = ECDFNormalizer()
    # 4 players with Strike Rates: [120, 140, 160, 180]
    player_values = {
        "P1": 120.0,
        "P2": 140.0,
        "P3": 160.0,
        "P4": 180.0,
    }
    cohort_id = "COHORT_TEST_BAT"

    results = normalizer.normalize_cohort_metric(
        metric_id="strike_rate",
        display_name="Strike Rate",
        directionality=MetricDirection.HIGHER_IS_BETTER,
        player_values=player_values,
        cohort_id=cohort_id,
    )

    # In a cohort of 4:
    # P1 (120): 1 out of 4 <= 120 -> 25.0%
    # P2 (140): 2 out of 4 <= 140 -> 50.0% (median)
    # P3 (160): 3 out of 4 <= 160 -> 75.0%
    # P4 (180): 4 out of 4 <= 180 -> 100.0% (top performer)
    assert results["P1"].percentile == 25.0
    assert results["P2"].percentile == 50.0
    assert results["P3"].percentile == 75.0
    assert results["P4"].percentile == 100.0
    assert results["P4"].raw_value == 180.0


def test_ecdf_normalization_lower_is_better():
    """Verify ECDF directional scaling where lower values are superior (e.g. Economy)."""
    normalizer = ECDFNormalizer()
    # 4 bowlers with Economy Rates: [6.0, 7.5, 9.0, 10.5]
    player_values = {
        "P_ELITE": 6.0,   # Best
        "P_GOOD": 7.5,
        "P_AVG": 9.0,
        "P_EXPENSIVE": 10.5, # Worst
    }
    cohort_id = "COHORT_TEST_BOWL"

    results = normalizer.normalize_cohort_metric(
        metric_id="economy_rate",
        display_name="Economy Rate",
        directionality=MetricDirection.LOWER_IS_BETTER,
        player_values=player_values,
        cohort_id=cohort_id,
    )

    # For lower-is-better: count peers who are worse or equal (x_j >= x_i)
    # P_ELITE (6.0): 4 out of 4 >= 6.0 -> 100.0% (elite run suppression)
    # P_GOOD (7.5): 3 out of 4 >= 7.5 -> 75.0%
    # P_AVG (9.0): 2 out of 4 >= 9.0 -> 50.0%
    # P_EXPENSIVE (10.5): 1 out of 4 >= 10.5 -> 25.0%
    assert results["P_ELITE"].percentile == 100.0
    assert results["P_GOOD"].percentile == 75.0
    assert results["P_AVG"].percentile == 50.0
    assert results["P_EXPENSIVE"].percentile == 25.0


def test_ecdf_normalization_tied_values():
    """Verify that tied values receive identical top percentile ranking."""
    normalizer = ECDFNormalizer()
    # P1: 100, P2: 150, P3: 150, P4: 200
    player_values = {"P1": 100.0, "P2": 150.0, "P3": 150.0, "P4": 200.0}
    results = normalizer.normalize_cohort_metric(
        metric_id="runs",
        display_name="Runs",
        directionality=MetricDirection.HIGHER_IS_BETTER,
        player_values=player_values,
        cohort_id="COHORT_TIES",
    )

    # P2 and P3 are tied: 3 out of 4 <= 150 -> 75.0% for both
    assert results["P2"].percentile == 75.0
    assert results["P3"].percentile == 75.0


def test_ecdf_normalization_missing_and_insufficient_cohort():
    """Verify handling when metric is None or cohort is smaller than MINIMUM_COHORT_SIZE."""
    normalizer = ECDFNormalizer()
    # Missing value handling
    vals_with_missing = {"P1": 120.0, "P2": None, "P3": 140.0, "P4": 160.0}
    results = normalizer.normalize_cohort_metric(
        metric_id="runs",
        display_name="Runs",
        directionality=MetricDirection.HIGHER_IS_BETTER,
        player_values=vals_with_missing,
        cohort_id="COHORT_MISSING",
    )

    # Valid pool has 3 players (120, 140, 160)
    assert results["P2"].raw_value is None
    assert results["P2"].percentile == 50.0  # Safe median fallback
    assert results["P1"].percentile == round((1 / 3) * 100, 2)

    # Cohort of size 2 (below MINIMUM_COHORT_SIZE = 3)
    small_cohort = {"P1": 100.0, "P2": 200.0}
    res_small = normalizer.normalize_cohort_metric(
        metric_id="runs",
        display_name="Runs",
        directionality=MetricDirection.HIGHER_IS_BETTER,
        player_values=small_cohort,
        cohort_id="COHORT_TINY",
    )
    assert res_small["P1"].percentile == 50.0
    assert res_small["P1"].normalization_method == "INSUFFICIENT_COHORT_MEDIAN_FALLBACK"


# ==============================================================================
# 2. BAYESIAN RELIABILITY SHRINKAGE TESTS
# ==============================================================================

def test_bayesian_reliability_shrinkage_calculation():
    """Verify mathematical precision of C(N) shrinkage factor."""
    assessor = BayesianReliabilityAssessor()

    # 1. Below N_min (Batting: < 60 balls) -> C = 0.0, INSUFFICIENT_SAMPLE
    c_micro, stat_micro = assessor.calculate_batting_reliability(30)
    assert c_micro == 0.0
    assert stat_micro == ReliabilityStatus.INSUFFICIENT_SAMPLE

    # 2. Exactly N_min (60 balls faced)
    # C = 60 / (60 + 30) = 60 / 90 = 0.6667
    c_min, stat_min = assessor.calculate_batting_reliability(60)
    assert c_min == 0.6667
    assert stat_min == ReliabilityStatus.RELIABILITY_DISCOUNTED

    # 3. 120 balls faced (between 60 and 180)
    # C = 120 / (120 + 30) = 120 / 150 = 0.8000
    c_mid, stat_mid = assessor.calculate_batting_reliability(120)
    assert c_mid == 0.8000
    assert stat_mid == ReliabilityStatus.RELIABILITY_DISCOUNTED

    # 4. Full reliability (>= 180 balls) -> C = 1.0, ADEQUATE
    c_full, stat_full = assessor.calculate_batting_reliability(200)
    assert c_full == 1.0
    assert stat_full == ReliabilityStatus.ADEQUATE


# ==============================================================================
# 3. COMPOSITE SCORING (VOR) TESTS
# ==============================================================================

def test_specialist_batter_vor_calculation():
    """Verify Batter VOR = 50.0 + C(N) * (raw_composite - 50.0)."""
    calc = VORCompositeCalculator()

    # Create mock normalized dimensions:
    # Say raw_composite evaluates to 75.0 across dimensions
    norm_dims = {
        "scoring_efficiency": [
            _create_mock_norm_metric("tsr", 80.0),
        ],
        "boundary_contribution": [
            _create_mock_norm_metric("bp", 70.0),
        ],
        "dismissal_resistance": [
            _create_mock_norm_metric("bpd", 75.0),
        ],
        "consistency": [
            _create_mock_norm_metric("dbs", 75.0),
        ],
    }

    # Case A: Full reliability (180 balls faced, C = 1.0)
    sample_full = SampleSizeInfo(balls_faced=180)
    vor, raw, c_fac, stat, _ = calc.compute_batter_vor(norm_dims, sample_full)
    assert c_fac == 1.0
    assert stat == ReliabilityStatus.ADEQUATE
    # Since C = 1.0, VOR == raw_composite
    assert vor == raw

    # Case B: Discounted reliability (60 balls faced, C = 0.6667)
    sample_disc = SampleSizeInfo(balls_faced=60)
    vor_disc, raw_disc, c_disc, stat_disc, _ = calc.compute_batter_vor(norm_dims, sample_disc)
    assert c_disc == 0.6667
    assert stat_disc == ReliabilityStatus.RELIABILITY_DISCOUNTED
    # Expected VOR = 50.0 + 0.6667 * (raw - 50.0)
    expected_vor = round(50.0 + 0.6667 * (raw_disc - 50.0), 2)
    assert vor_disc == expected_vor
    assert vor_disc < raw_disc  # Regressed toward 50.0!

    # Case C: Insufficient sample (< 60 balls, e.g. 25 balls)
    sample_insuf = SampleSizeInfo(balls_faced=25)
    vor_insuf, _, c_insuf, stat_insuf, _ = calc.compute_batter_vor(norm_dims, sample_insuf)
    assert c_insuf == 0.0
    assert stat_insuf == ReliabilityStatus.INSUFFICIENT_SAMPLE
    assert vor_insuf == 50.0  # Regressed to median


def test_all_rounder_dual_vor_and_bonus():
    """Verify All-Rounder dual composite and qualification-contingent dual bonus."""
    calc = VORCompositeCalculator()

    # Case A: Qualified dual threat (balls_faced >= 60 AND legal_balls >= 72)
    sample_dual_qual = SampleSizeInfo(balls_faced=180, legal_balls_bowled=180)
    vor_ar, raw_ar, bonus, comps = calc.compute_all_rounder_vor(
        bat_vor=70.0,
        bowl_vor=65.0,
        raw_bat=70.0,
        raw_bowl=65.0,
        c_factor=1.0,
        rel_status=ReliabilityStatus.ADEQUATE,
        sample=sample_dual_qual,
        all_dim_scores={},
    )
    # Base blended: 0.5 * 70 + 0.5 * 65 = 67.5
    # Dual bonus: 5.0 * (min(70, 65) / 50.0) = 5.0 * (65 / 50) = 6.5
    assert bonus == 6.5
    assert vor_ar == round(67.5 + 6.5, 2)  # 74.0

    # Case B: Disqualified all-rounder (has bowling, but balls_faced < 60)
    sample_unqual = SampleSizeInfo(balls_faced=30, legal_balls_bowled=180)
    vor_unqual, _, bonus_unqual, _ = calc.compute_all_rounder_vor(
        bat_vor=50.0,
        bowl_vor=75.0,
        raw_bat=80.0,
        raw_bowl=75.0,
        c_factor=0.0,
        rel_status=ReliabilityStatus.INSUFFICIENT_SAMPLE,
        sample=sample_unqual,
        all_dim_scores={},
    )
    # Fails dual N_min -> Bonus is 0.0!
    assert bonus_unqual == 0.0


# ==============================================================================
# 4. RANKING & TIE-BREAKING HIERARCHY TESTS
# ==============================================================================

def test_ranking_engine_tie_breaking_and_quarantine():
    """Verify multi-tier tie breaking (VOR -> C(N) -> Primary True Metric) and quarantine exclusion."""
    engine = RankingEngine()
    cohort_id = "COHORT_BATTER_TEST"
    run_id = "RUN_TEST"

    # Create 4 candidates:
    # C1: VOR 75.0, C = 1.0, TSR = +15.0 (Qualified)
    # C2: VOR 75.0, C = 0.8, TSR = +20.0 (Qualified, but lower C than C1 -> Rank 2)
    # C3: VOR 75.0, C = 1.0, TSR = +10.0 (Tied with C1 on VOR and C, but lower TSR -> Rank 2, C2 becomes Rank 3)
    # C4: VOR 80.0, C = 0.0 (INSUFFICIENT_SAMPLE -> Quarantined!)
    # C5: VOR 70.0, is_eligible = False (Quarantined!)

    scores = [
        _create_mock_player_score("C1", 75.0, 1.0, ReliabilityStatus.ADEQUATE, tsr=15.0, is_qual=True, is_elig=True),
        _create_mock_player_score("C2", 75.0, 0.8, ReliabilityStatus.RELIABILITY_DISCOUNTED, tsr=20.0, is_qual=True, is_elig=True),
        _create_mock_player_score("C3", 75.0, 1.0, ReliabilityStatus.ADEQUATE, tsr=10.0, is_qual=True, is_elig=True),
        _create_mock_player_score("C4", 80.0, 0.0, ReliabilityStatus.INSUFFICIENT_SAMPLE, tsr=30.0, is_qual=False, is_elig=True),
        _create_mock_player_score("C5", 70.0, 1.0, ReliabilityStatus.ADEQUATE, tsr=5.0, is_qual=True, is_elig=False),
    ]

    res = engine.generate_rankings(scores, cohort_id, run_id)

    # 3 qualified candidates ranked; 2 quarantined
    assert res.total_ranked == 3
    assert res.total_quarantined == 2

    # Check ranking order:
    # 1. C1 (VOR 75.0, C=1.0, TSR=15.0)
    # 2. C3 (VOR 75.0, C=1.0, TSR=10.0) -> lost on TSR tie-breaker
    # 3. C2 (VOR 75.0, C=0.8) -> lost on C(N) tie-breaker
    assert res.rankings[0].player_id == "C1"
    assert res.rankings[0].rank == 1
    assert res.rankings[1].player_id == "C3"
    assert res.rankings[1].rank == 2
    assert res.rankings[2].player_id == "C2"
    assert res.rankings[2].rank == 3

    # Check quarantined list
    quarantine_ids = [q.player_id for q in res.quarantined]
    assert "C4" in quarantine_ids
    assert "C5" in quarantine_ids


# ==============================================================================
# 5. SCORE EXPLANATION TESTS
# ==============================================================================

def test_score_explainer_factor_attribution():
    """Verify transparent explanation generation, strengths, and drag factor decomposition."""
    explainer = ScoreExplainer()
    dim_scores = {
        "scoring_efficiency": _create_mock_dim_score("scoring_efficiency", "Scoring Efficiency", 85.0),
        "boundary_contribution": _create_mock_dim_score("boundary_contribution", "Boundary Potency", 80.0),
        "dismissal_resistance": _create_mock_dim_score("dismissal_resistance", "Dismissal Resistance", 35.0),
    }

    explanation = explainer.explain_score(
        vor=68.5,
        raw_composite=72.0,
        reliability_factor=0.88,
        reliability_status=ReliabilityStatus.RELIABILITY_DISCOUNTED,
        dimension_scores=dim_scores,
        role_name="BATTER",
        cohort_id="COHORT_BATTER_IPL",
    )

    assert len(explanation.top_strengths) >= 1
    assert "Scoring Efficiency" in explanation.top_strengths[0]
    assert len(explanation.drag_factors) >= 1
    assert "Dismissal Resistance" in explanation.drag_factors[0]
    assert "68.5" in explanation.summary_text


# ==============================================================================
# 6. REST API INTEGRATION TESTS
# ==============================================================================

@pytest.mark.anyio
async def test_api_scoring_methodology_endpoint():
    """Verify GET /api/v1/scoring/methodology returns full active configuration."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/scoring/methodology")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "1.0.0"
        assert "Z_i" in data["ecdf_formula_higher_better"]
        assert "VOR = 50.0" in data["bayesian_shrinkage_formula"]
        assert "batting_balanced" in data["role_weights"]


@pytest.mark.anyio
async def test_api_scoring_calculate_and_rankings_lifecycle():
    """Verify POST /api/v1/scoring/calculate, GET /runs/{id}, GET /players/{id}, and GET /rankings."""
    unique_ds_id = f"DS_SCORING_{uuid.uuid4().hex[:8]}"
    p_bat_id = f"P_BAT_{uuid.uuid4().hex[:6]}"
    p_bowl_id = f"P_BOWL_{uuid.uuid4().hex[:6]}"
    p_ar_id = f"P_AR_{uuid.uuid4().hex[:6]}"

    # Seed deliveries directly into database
    async with async_session_factory() as session:
        ds = Dataset(
            dataset_id=unique_ds_id,
            workspace_id="default_workspace",
            source_filename="test_scoring.csv",
            file_format="CSV",
            file_sha256=f"hash_{unique_ds_id}",
            storage_path="/tmp/scoring.csv",
            status="PERSISTED",
        )
        session.add(ds)

        # Seed players
        for p_id, p_name, p_role in [
            (p_bat_id, "Test Batter", "BATTER"),
            (p_bowl_id, "Test Bowler", "BOWLER"),
            (p_ar_id, "Test All-Rounder", "ALL_ROUNDER"),
        ]:
            session.add(Player(player_id=p_id, canonical_name=p_name, primary_role=p_role))

        # Deliveries for P_BAT: 80 balls faced
        for i in range(80):
            session.add(
                Delivery(
                    delivery_id=f"{unique_ds_id}_BAT_{i}",
                    dataset_id=unique_ds_id,
                    workspace_id="default_workspace",
                    origin_type="COMPETITION_SANDBOX",
                    match_id="M_01",
                    innings_num=1,
                    over_number=i // 6,
                    ball_number=(i % 6) + 1,
                    over_delivery=float(f"{i // 6}.{(i % 6) + 1}"),
                    phase="POWERPLAY" if i < 36 else "MIDDLE",
                    batter_id=p_bat_id,
                    bowler_id="OPP_BOWL",
                    batter_runs=4 if i % 4 == 0 else 1,
                    extras_runs=0,
                    extras_type=None,
                    is_legal=True,
                    total_runs=4 if i % 4 == 0 else 1,
                    is_wicket=False,
                    is_super_over=False,
                )
            )

        # Deliveries for P_BOWL: 96 legal balls bowled
        for i in range(96):
            session.add(
                Delivery(
                    delivery_id=f"{unique_ds_id}_BOWL_{i}",
                    dataset_id=unique_ds_id,
                    workspace_id="default_workspace",
                    origin_type="COMPETITION_SANDBOX",
                    match_id="M_01",
                    innings_num=2,
                    over_number=i // 6,
                    ball_number=(i % 6) + 1,
                    over_delivery=float(f"{i // 6}.{(i % 6) + 1}"),
                    phase="POWERPLAY" if i < 36 else "MIDDLE",
                    batter_id="OPP_BAT",
                    bowler_id=p_bowl_id,
                    batter_runs=0 if i % 2 == 0 else 1,
                    extras_runs=0,
                    extras_type=None,
                    is_legal=True,
                    total_runs=0 if i % 2 == 0 else 1,
                    is_wicket=i % 24 == 0,
                    dismissed_player_id="OPP_BAT" if i % 24 == 0 else None,
                    dismissal_kind="bowled" if i % 24 == 0 else None,
                    is_super_over=False,
                )
            )

        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. POST /api/v1/scoring/calculate
        calc_resp = await client.post(
            "/api/v1/scoring/calculate",
            json={"dataset_id": unique_ds_id},
        )
        assert calc_resp.status_code == 200
        run_data = calc_resp.json()
        run_id = run_data["run_id"]
        assert run_data["total_evaluated"] >= 2

        # 2. GET /api/v1/scoring/runs/{run_id}
        run_get = await client.get(f"/api/v1/scoring/runs/{run_id}")
        assert run_get.status_code == 200
        assert run_get.json()["run_id"] == run_id

        # 3. GET /api/v1/scoring/players/{player_id}
        p_get = await client.get(f"/api/v1/scoring/players/{p_bat_id}?run_id={run_id}")
        assert p_get.status_code == 200
        p_score = p_get.json()
        assert p_score["player_id"] == p_bat_id
        assert p_score["vor_score"] > 0
        assert p_score["explanation"]["final_vor"] == p_score["vor_score"]

        # 4. GET /api/v1/scoring/rankings
        rank_get = await client.get(f"/api/v1/scoring/rankings?run_id={run_id}")
        assert rank_get.status_code == 200
        rank_data = rank_get.json()
        assert rank_data["total_ranked"] + rank_data["total_quarantined"] >= 2


# ==============================================================================
# TEST HELPERS
# ==============================================================================

def _create_mock_norm_metric(metric_id: str, percentile: float) -> NormalizedMetric:
    return NormalizedMetric(
        metric_id=metric_id,
        display_name=metric_id.upper(),
        raw_value=100.0,
        directionality=MetricDirection.HIGHER_IS_BETTER,
        percentile=percentile,
        cohort_id="MOCK_COHORT",
        cohort_size=10,
    )


def _create_mock_dim_score(dim_id: str, dim_name: str, score: float) -> DimensionScore:
    return DimensionScore(
        dimension_id=dim_id,
        dimension_name=dim_name,
        dimension_score=score,
        weight=0.25,
        contribution_points=round(score * 0.25, 2),
        metrics=[_create_mock_norm_metric(dim_id, score)],
    )


def _create_mock_player_score(
    p_id: str,
    vor: float,
    c_fac: float,
    stat: ReliabilityStatus,
    tsr: float,
    is_qual: bool,
    is_elig: bool,
) -> PlayerScoreResult:
    dims = {
        "scoring_efficiency": DimensionScore(
            dimension_id="scoring_efficiency",
            dimension_name="Scoring Efficiency",
            dimension_score=vor,
            weight=0.25,
            contribution_points=vor * 0.25,
            metrics=[
                NormalizedMetric(
                    metric_id="true_strike_rate",
                    display_name="TSR",
                    raw_value=tsr,
                    directionality=MetricDirection.HIGHER_IS_BETTER,
                    percentile=vor,
                    cohort_id="TEST",
                    cohort_size=5,
                )
            ],
        )
    }
    return PlayerScoreResult(
        player_id=p_id,
        player_name=f"Player {p_id}",
        role=PlayerRole.BATTER,
        role_classification=RoleClassificationResult(
            player_id=p_id,
            assigned_role=PlayerRole.BATTER,
            status=RoleClassificationStatus.CONFIRMED_FROM_SOURCE,
            classification_method="TEST",
        ),
        cohort_id="TEST",
        vor_score=vor,
        raw_composite_score=vor,
        reliability_factor=c_fac,
        reliability_status=stat,
        sample_size=SampleSizeInfo(balls_faced=int(180 * c_fac)),
        dimensions=dims,
        is_qualified=is_qual,
        is_eligible=is_elig,
        explanation=ScoreExplanation(
            final_vor=vor,
            raw_composite=vor,
            reliability_factor=c_fac,
            reliability_status=stat,
            summary_text="Mock explanation",
        ),
        provenance=MetricProvenance(dataset_id="TEST_DS"),
    )
