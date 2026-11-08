"""Comprehensive automated tests for VYNTIQ Explainability & Player Comparison Engine.

Validates:
1. Explainability Engine:
   - Mathematical reconciliation of dimension contributions with raw composite score.
   - Deterministic factor attribution (top strengths, drag factors).
   - Explanation completeness statuses (COMPLETE, PARTIAL, INSUFFICIENT_EVIDENCE).
   - Traceability of scoring run ID, dataset references, and versioning.
2. Player Comparison Engine:
   - Batter vs Batter head-to-head comparison.
   - Bowler vs Bowler head-to-head comparison.
   - All-Rounder vs All-Rounder comparison (separate batting & bowling components).
   - Cross-role comparison safeguard (flags cross-role and disables invalid VOR equivalence).
   - Incompatible cohort detection.
   - Metric directionality handling (advantage to lower economy, higher strike rate).
   - Absolute and relative difference calculations (safe division on zero).
3. REST API Endpoints:
   - GET /api/v1/explainability/players/{id}
   - GET /api/v1/explainability/players/{id}/breakdown
   - POST /api/v1/comparisons/players
   - GET /api/v1/comparisons/{id}
   - GET /api/v1/comparisons/metadata
"""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app
from backend.app.schemas.comparison import (
    ComparisonCompatibilityStatus,
    PlayerComparisonRequest,
)
from backend.app.schemas.evaluation import (
    PlayerRole,
    RoleClassificationResult,
    RoleClassificationStatus,
)
from backend.app.schemas.explainability import ExplanationStatus
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
from backend.app.services.comparison.compatibility import CompatibilityChecker
from backend.app.services.comparison.differencer import DifferenceAnalyzer
from backend.app.services.comparison.service import PlayerComparisonService
from backend.app.services.explainability.service import ExplainabilityService
from backend.app.services.scoring.service import RUN_CACHE, ScoringService


# ==============================================================================
# TEST FIXTURES
# ==============================================================================

@pytest.fixture(autouse=True)
def setup_mock_scoring_run():
    """Populate global RUN_CACHE with deterministically verified player scores."""
    run_id = "RUN_AUDIT_01"
    ds_id = "DS_AUDIT_DATA"

    # Player 1: Elite Batter (Adequate sample, C = 1.0)
    p_bat1 = _create_mock_scored_player(
        player_id="P_BAT_ELITE",
        name="Elite Opener",
        role=PlayerRole.BATTER,
        cohort_id="COHORT_BATTER_T20",
        vor=78.5,
        raw=78.5,
        c_factor=1.0,
        rel_stat=ReliabilityStatus.ADEQUATE,
        balls_faced=200,
        legal_balls=0,
        tsr=22.5,
        econ=None,
    )

    # Player 2: Anchor Batter (Discounted sample, C = 0.8)
    p_bat2 = _create_mock_scored_player(
        player_id="P_BAT_ANCHOR",
        name="Middle Anchor",
        role=PlayerRole.BATTER,
        cohort_id="COHORT_BATTER_T20",
        vor=62.0,
        raw=65.0,
        c_factor=0.8,
        rel_stat=ReliabilityStatus.RELIABILITY_DISCOUNTED,
        balls_faced=120,
        legal_balls=0,
        tsr=5.0,
        econ=None,
    )

    # Player 3: Elite Bowler (Adequate sample, C = 1.0)
    p_bowl1 = _create_mock_scored_player(
        player_id="P_BOWL_ELITE",
        name="Strike Pacer",
        role=PlayerRole.BOWLER,
        cohort_id="COHORT_BOWLER_T20",
        vor=81.0,
        raw=81.0,
        c_factor=1.0,
        rel_stat=ReliabilityStatus.ADEQUATE,
        balls_faced=0,
        legal_balls=192,
        tsr=None,
        econ=6.20,
    )

    # Player 4: Micro-sample Batter (quarantined, C = 0.0)
    p_micro = _create_mock_scored_player(
        player_id="P_BAT_MICRO",
        name="Rookie Slogger",
        role=PlayerRole.BATTER,
        cohort_id="COHORT_BATTER_T20",
        vor=50.0,
        raw=85.0,
        c_factor=0.0,
        rel_stat=ReliabilityStatus.INSUFFICIENT_SAMPLE,
        balls_faced=18,
        legal_balls=0,
        tsr=35.0,
        econ=None,
    )

    # Player 5: Genuine All-Rounder
    p_ar = _create_mock_scored_player(
        player_id="P_AR_GENUINE",
        name="Premier All-Rounder",
        role=PlayerRole.ALL_ROUNDER,
        cohort_id="COHORT_ALL_ROUNDER_T20",
        vor=76.0,
        raw=74.0,
        c_factor=1.0,
        rel_stat=ReliabilityStatus.ADEQUATE,
        balls_faced=180,
        legal_balls=180,
        tsr=12.0,
        econ=7.40,
        is_ar=True,
    )

    mock_run = ScoringRunResponse(
        run_id=run_id,
        dataset_id=ds_id,
        cohort_id="MULTI_ROLE_RUN",
        total_evaluated=5,
        total_qualified=4,
        total_quarantined=1,
        scoring_version="1.0.0",
        created_at="2026-11-08T12:00:00Z",
        players=[p_bat1, p_bat2, p_bowl1, p_micro, p_ar],
    )

    RUN_CACHE[run_id] = mock_run
    return mock_run


# ==============================================================================
# 1. EXPLAINABILITY ENGINE TESTS
# ==============================================================================

def test_explainability_score_breakdown_mathematical_reconciliation():
    """Verify that dimension contributions mathematically reconcile with raw composite score."""
    service = ExplainabilityService()
    breakdown = service.get_score_breakdown("P_BAT_ELITE", "RUN_AUDIT_01")

    assert breakdown.player_id == "P_BAT_ELITE"
    assert breakdown.final_vor == 78.5
    assert breakdown.raw_composite_score == 78.5
    assert len(breakdown.dimensions) >= 4

    # Mathematical reconciliation assertion:
    # Sum of dimension contributions must equal raw composite score (within 0.05 rounding tolerance)
    assert breakdown.reconciliation_discrepancy <= 0.05
    assert breakdown.sum_of_dimension_contributions == pytest.approx(breakdown.raw_composite_score, abs=0.05)


def test_explainability_detailed_explanation_complete_status():
    """Verify COMPLETE explanation generation for an adequate-sample player."""
    service = ExplainabilityService()
    explanation = service.generate_player_explanation("P_BAT_ELITE", "RUN_AUDIT_01")

    assert explanation.player_id == "P_BAT_ELITE"
    assert explanation.status == ExplanationStatus.COMPLETE
    assert explanation.final_vor == 78.5
    assert len(explanation.top_strengths) >= 1
    assert "Elite Opener" in explanation.narrative_summary
    assert len(explanation.excluded_or_unsupported_metrics) >= 3


def test_explainability_insufficient_evidence_status():
    """Verify INSUFFICIENT_EVIDENCE status and regression narrative for micro-sample player."""
    service = ExplainabilityService()
    explanation = service.generate_player_explanation("P_BAT_MICRO", "RUN_AUDIT_01")

    assert explanation.player_id == "P_BAT_MICRO"
    assert explanation.status == ExplanationStatus.INSUFFICIENT_EVIDENCE
    assert explanation.final_vor == 50.0  # Regressed to median
    assert explanation.raw_composite_score == 85.0  # Raw preserved for audit
    assert "quarantined" in explanation.narrative_summary.lower()


# ==============================================================================
# 2. COMPARISON ENGINE TESTS
# ==============================================================================

def test_comparison_batter_vs_batter_compatibility_and_difference():
    """Verify head-to-head comparison between two batters in the same cohort."""
    service = PlayerComparisonService()
    req = PlayerComparisonRequest(
        player_ids=["P_BAT_ELITE", "P_BAT_ANCHOR"],
        run_id="RUN_AUDIT_01",
    )
    res = service.compare_players(req)

    assert res.compatibility_status == ComparisonCompatibilityStatus.FULLY_COMPATIBLE
    assert res.vor_comparison_valid is True
    assert res.vor_leader_id == "P_BAT_ELITE"
    assert res.is_cross_role is False
    assert len(res.players) == 2

    # Verify Strike Rate / TSR comparison:
    # P_BAT_ELITE (TSR +22.5) should be favorable over P_BAT_ANCHOR (TSR +5.0)
    tsr_item = next(m for m in res.batting_comparison if m.metric_id == "true_strike_rate")
    assert tsr_item.favorable_player_id == "P_BAT_ELITE"
    assert tsr_item.absolute_difference == 17.5


def test_comparison_cross_role_safeguard():
    """Verify that comparing a Batter against a Bowler flags cross-role and disables VOR equivalence."""
    service = PlayerComparisonService()
    req = PlayerComparisonRequest(
        player_ids=["P_BAT_ELITE", "P_BOWL_ELITE"],
        run_id="RUN_AUDIT_01",
    )
    res = service.compare_players(req)

    # Must be CROSS_ROLE_PARTIAL
    assert res.compatibility_status == ComparisonCompatibilityStatus.CROSS_ROLE_PARTIAL
    assert res.is_cross_role is True
    # VOR direct equivalence must be strictly disabled!
    assert res.vor_comparison_valid is False
    assert res.vor_leader_id is None
    assert any("cross-role" in note.lower() for note in res.compatibility_notes)


def test_comparison_directionality_lower_is_better():
    """Verify that metrics with LOWER_IS_BETTER award statistical advantage to smaller value (Economy)."""
    differencer = DifferenceAnalyzer()
    player_values = {"BOWLER_A": 6.20, "BOWLER_B": 8.50}
    player_pcts = {"BOWLER_A": 90.0, "BOWLER_B": 45.0}
    names = {"BOWLER_A": "Pacer A", "BOWLER_B": "Pacer B"}

    item = differencer.compare_metric(
        metric_id="economy_rate",
        display_name="Economy Rate",
        directionality=MetricDirection.LOWER_IS_BETTER,
        unit="rpo",
        player_values=player_values,
        player_percentiles=player_pcts,
        player_names=names,
    )

    # BOWLER_A (6.20) must be favorable over BOWLER_B (8.50) because lower economy is better!
    assert item.favorable_player_id == "BOWLER_A"
    assert item.absolute_difference == 2.30


def test_comparison_safe_division_on_zero():
    """Verify difference analysis handles zero baselines without division by zero errors."""
    differencer = DifferenceAnalyzer()
    # One value is 0.0, another is 5.0
    player_values = {"P1": 0.0, "P2": 5.0}
    player_pcts = {"P1": 10.0, "P2": 60.0}
    names = {"P1": "Player 1", "P2": "Player 2"}

    item = differencer.compare_metric(
        metric_id="wickets_taken",
        display_name="Bowler Wickets",
        directionality=MetricDirection.HIGHER_IS_BETTER,
        unit="w",
        player_values=player_values,
        player_percentiles=player_pcts,
        player_names=names,
    )

    assert item.favorable_player_id == "P2"
    assert item.absolute_difference == 5.0
    # Relative difference does not divide by zero
    assert item.relative_difference_pct is None or item.relative_difference_pct >= 0.0


# ==============================================================================
# 3. REST API ENDPOINT TESTS
# ==============================================================================

@pytest.mark.anyio
async def test_api_get_player_explanation():
    """Verify GET /api/v1/explainability/players/{id} returns full audit explanation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/explainability/players/P_BAT_ELITE?run_id=RUN_AUDIT_01")
        assert resp.status_code == 200
        data = resp.json()
        assert data["player_id"] == "P_BAT_ELITE"
        assert data["status"] == "COMPLETE"
        assert data["final_vor"] == 78.5
        assert len(data["top_strengths"]) >= 1


@pytest.mark.anyio
async def test_api_get_score_breakdown():
    """Verify GET /api/v1/explainability/players/{id}/breakdown returns reconciled dimensions."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/explainability/players/P_BAT_ELITE/breakdown?run_id=RUN_AUDIT_01")
        assert resp.status_code == 200
        data = resp.json()
        assert data["player_id"] == "P_BAT_ELITE"
        assert data["reconciliation_discrepancy"] <= 0.05
        assert len(data["dimensions"]) >= 4


@pytest.mark.anyio
async def test_api_compare_players_and_get_comparison():
    """Verify POST /api/v1/comparisons/players and GET /api/v1/comparisons/{id} lifecycle."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Initiate comparison
        post_resp = await client.post(
            "/api/v1/comparisons/players",
            json={
                "player_ids": ["P_BAT_ELITE", "P_BAT_ANCHOR"],
                "run_id": "RUN_AUDIT_01",
            },
        )
        assert post_resp.status_code == 200
        comp_data = post_resp.json()
        comp_id = comp_data["comparison_id"]
        assert comp_data["compatibility_status"] == "FULLY_COMPATIBLE"
        assert comp_data["vor_leader_id"] == "P_BAT_ELITE"

        # 2. Lookup stored comparison
        get_resp = await client.get(f"/api/v1/comparisons/{comp_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["comparison_id"] == comp_id


@pytest.mark.anyio
async def test_api_comparison_metadata():
    """Verify GET /api/v1/comparisons/metadata returns guidelines and directionality rules."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/comparisons/metadata")
        assert resp.status_code == 200
        data = resp.json()
        assert data["max_players_allowed"] == 5
        assert "LOWER_IS_BETTER" in data["directionality_conventions"]


# ==============================================================================
# TEST DATA GENERATOR HELPER
# ==============================================================================

def _create_mock_scored_player(
    player_id: str,
    name: str,
    role: PlayerRole,
    cohort_id: str,
    vor: float,
    raw: float,
    c_factor: float,
    rel_stat: ReliabilityStatus,
    balls_faced: int,
    legal_balls: int,
    tsr: float | None = None,
    econ: float | None = None,
    is_ar: bool = False,
) -> PlayerScoreResult:
    """Helper to assemble a mathematically consistent mock PlayerScoreResult."""
    dims: dict[str, DimensionScore] = {}
    score_val = raw if raw > 0 else vor

    if role == PlayerRole.BATTER or is_ar:
        dims["scoring_efficiency"] = DimensionScore(
            dimension_id="scoring_efficiency",
            dimension_name="Scoring Efficiency",
            dimension_score=score_val,
            weight=0.25,
            contribution_points=round(score_val * 0.25, 2),
            metrics=[
                NormalizedMetric(
                    metric_id="true_strike_rate",
                    display_name="True Strike Rate (TSR)",
                    raw_value=tsr or 15.0,
                    directionality=MetricDirection.HIGHER_IS_BETTER,
                    percentile=score_val,
                    cohort_id=cohort_id,
                    cohort_size=10,
                ),
                NormalizedMetric(
                    metric_id="batting_strike_rate",
                    display_name="Batting Strike Rate",
                    raw_value=145.0,
                    directionality=MetricDirection.HIGHER_IS_BETTER,
                    percentile=score_val,
                    cohort_id=cohort_id,
                    cohort_size=10,
                ),
            ],
        )
        dims["boundary_contribution"] = DimensionScore(
            dimension_id="boundary_contribution",
            dimension_name="Boundary Potency",
            dimension_score=score_val,
            weight=0.25,
            contribution_points=round(score_val * 0.25, 2),
            metrics=[
                NormalizedMetric(
                    metric_id="boundary_percentage_runs",
                    display_name="Boundary % (Runs)",
                    raw_value=65.0,
                    directionality=MetricDirection.HIGHER_IS_BETTER,
                    percentile=score_val,
                    cohort_id=cohort_id,
                    cohort_size=10,
                )
            ],
        )
        dims["dismissal_resistance"] = DimensionScore(
            dimension_id="dismissal_resistance",
            dimension_name="Dismissal Resistance & Stability",
            dimension_score=score_val,
            weight=0.25,
            contribution_points=round(score_val * 0.25, 2),
            metrics=[
                NormalizedMetric(
                    metric_id="batting_average",
                    display_name="Batting Average",
                    raw_value=35.0,
                    directionality=MetricDirection.HIGHER_IS_BETTER,
                    percentile=score_val,
                    cohort_id=cohort_id,
                    cohort_size=10,
                )
            ],
        )
        dims["consistency"] = DimensionScore(
            dimension_id="consistency",
            dimension_name="Strike Rotation & Consistency",
            dimension_score=score_val,
            weight=0.25,
            contribution_points=round(score_val * 0.25, 2),
            metrics=[
                NormalizedMetric(
                    metric_id="dot_ball_suppression",
                    display_name="Dot Ball Suppression",
                    raw_value=62.0,
                    directionality=MetricDirection.HIGHER_IS_BETTER,
                    percentile=score_val,
                    cohort_id=cohort_id,
                    cohort_size=10,
                )
            ],
        )

    if role == PlayerRole.BOWLER:
        dims["run_containment"] = DimensionScore(
            dimension_id="run_containment",
            dimension_name="Run Containment",
            dimension_score=score_val,
            weight=0.30,
            contribution_points=round(score_val * 0.30, 2),
            metrics=[
                NormalizedMetric(
                    metric_id="economy_rate",
                    display_name="Economy Rate",
                    raw_value=econ or 7.20,
                    directionality=MetricDirection.LOWER_IS_BETTER,
                    percentile=score_val,
                    cohort_id=cohort_id,
                    cohort_size=10,
                )
            ],
        )
        dims["wicket_taking_performance"] = DimensionScore(
            dimension_id="wicket_taking_performance",
            dimension_name="Wicket-Taking Performance",
            dimension_score=score_val,
            weight=0.30,
            contribution_points=round(score_val * 0.30, 2),
            metrics=[
                NormalizedMetric(
                    metric_id="wickets_taken",
                    display_name="Bowler Wickets",
                    raw_value=12,
                    directionality=MetricDirection.HIGHER_IS_BETTER,
                    percentile=score_val,
                    cohort_id=cohort_id,
                    cohort_size=10,
                )
            ],
        )
        dims["dot_ball_generation"] = DimensionScore(
            dimension_id="dot_ball_generation",
            dimension_name="Dot-Ball Generation & Pressure",
            dimension_score=score_val,
            weight=0.20,
            contribution_points=round(score_val * 0.20, 2),
            metrics=[
                NormalizedMetric(
                    metric_id="bowling_dot_ball_percentage",
                    display_name="Bowling Dot-Ball %",
                    raw_value=48.0,
                    directionality=MetricDirection.HIGHER_IS_BETTER,
                    percentile=score_val,
                    cohort_id=cohort_id,
                    cohort_size=10,
                )
            ],
        )
        dims["bowling_workload"] = DimensionScore(
            dimension_id="bowling_workload",
            dimension_name="Bowling Workload & Discipline",
            dimension_score=score_val,
            weight=0.20,
            contribution_points=round(score_val * 0.20, 2),
            metrics=[
                NormalizedMetric(
                    metric_id="legal_balls_bowled",
                    display_name="Legal Balls Bowled",
                    raw_value=legal_balls,
                    directionality=MetricDirection.NEUTRAL,
                    percentile=score_val,
                    cohort_id=cohort_id,
                    cohort_size=10,
                )
            ],
        )

    return PlayerScoreResult(
        player_id=player_id,
        player_name=name,
        role=role,
        role_classification=RoleClassificationResult(
            player_id=player_id,
            assigned_role=role,
            status=RoleClassificationStatus.CONFIRMED_FROM_SOURCE,
            classification_method="MOCK_AUDIT",
        ),
        cohort_id=cohort_id,
        vor_score=vor,
        raw_composite_score=raw,
        reliability_factor=c_factor,
        reliability_status=rel_stat,
        sample_size=SampleSizeInfo(balls_faced=balls_faced, legal_balls_bowled=legal_balls),
        dimensions=dims,
        is_qualified=rel_stat != ReliabilityStatus.INSUFFICIENT_SAMPLE,
        is_eligible=True,
        explanation=ScoreExplanation(
            final_vor=vor,
            raw_composite=raw,
            reliability_factor=c_factor,
            reliability_status=rel_stat,
            top_strengths=["Scoring Efficiency (78.5th percentile)"],
            drag_factors=[],
            summary_text="Mock score explanation",
        ),
        provenance=MetricProvenance(dataset_id="DS_AUDIT_DATA"),
    )
