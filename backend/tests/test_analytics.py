"""Comprehensive automated tests for VYNTIQ Cricket Performance Metrics Engine.

Validates:
1. Batting rate statistics (runs, strike rate, average, BPD, boundary %, dot-ball %).
2. Bowling rate statistics (wickets, economy, strike rate, average, dot-ball %, BBC, extras).
3. Cricket statistical rules (wides excluded from balls faced, byes excluded from bowler runs,
   run-outs excluded from bowler wickets, bowler-credited wickets only).
4. Edge cases (zero balls, zero wickets, zero dismissals / not-outs, empty dataframes, deduplication).
5. Advanced metrics status handling (TSR, TER, open/deferred definitions for WTI, CFI, NVC).
6. Role-specific performance dimension groupings.
7. Multidimensional filtering and aggregation.
8. Analytics API endpoints (/metrics, /calculate, /datasets/{id}/summary).
"""

import uuid
import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.core.database import async_session_factory
from backend.app.main import app
from backend.app.models.cricket import Delivery, Match, Player
from backend.app.models.dataset import Dataset
from backend.app.schemas.analytics import MetricCalculationFilter, MetricCalculationRequest
from backend.app.schemas.metrics import MetricCategory, MetricDirection, MetricStatus
from backend.app.services.analytics.advanced import AdvancedMetricsEvaluator
from backend.app.services.analytics.aggregation import DeliveryAggregator
from backend.app.services.analytics.batting import BattingMetricsCalculator
from backend.app.services.analytics.bowling import BowlingMetricsCalculator
from backend.app.services.analytics.dimensions import DimensionBuilder
from backend.app.services.analytics.registry import get_all_metrics, get_metric_definition
from backend.app.services.analytics.service import AnalyticsService


# ==============================================================================
# SYNTHETIC TEST FIXTURES (Explicitly Synthetic / Manually Verified)
# ==============================================================================

@pytest.fixture
def synthetic_cricket_dataframe() -> pd.DataFrame:
    """Deterministic synthetic ball-by-ball dataset with known statistical properties.

    Player P_BAT_01 (Batter):
      Match 1:
        1. 0 runs (dot)
        2. 4 runs (four)
        3. 1 run (single)
        4. WIDE (extras_type='WIDE', extras_runs=1, batter_runs=0) -> DOES NOT count as ball faced!
        5. 6 runs (six)
        6. 0 runs, caught (wicket credited to bowler, batter dismissed)
      Match 2:
        1. 2 runs (two)
        2. 4 runs (four)
        3. 1 run (single)
        4. 0 runs, not out
      Total Batter Stats:
        Balls Faced: 9 (excluding wide)
        Runs Scored: 0 + 4 + 1 + 6 + 0 + 2 + 4 + 1 + 0 = 18
        Fours: 2, Sixes: 1 -> Total Boundaries: 3
        Boundary Runs: 2*4 + 1*6 = 14
        Boundary % (Runs): 14 / 18 * 100 = 77.78%
        Boundary % (Balls): 3 / 9 * 100 = 33.33%
        Balls per Boundary: 9 / 3 = 3.0
        Dismissals: 1 (caught in M1)
        Strike Rate: (18 / 9) * 100 = 200.0
        Batting Average: 18 / 1 = 18.0
        Balls per Dismissal: 9 / 1 = 9.0
        Dot balls faced: 3 (Ball 1, Ball 6 in M1, Ball 4 in M2)
        Dot Ball %: (3 / 9) * 100 = 33.33%
        Dot Ball Suppression: 100.0 - 33.33 = 66.67%

    Player P_BOWL_01 (Bowler):
      1. 0 runs (legal, dot)
      2. WIDE (extras_type='WIDE', extras_runs=1, batter_runs=0) -> Illegal! 1 run conceded.
      3. 4 runs (legal, 4 conceded)
      4. 0 runs, caught (legal, bowler-credited wicket!)
      5. 4 BYES (extras_type='BYE', extras_runs=4, batter_runs=0) -> Legal delivery! EXCLUDED from bowler runs!
      6. 0 runs, RUN OUT (legal, wicket=True, dismissal_kind='run out') -> Non-bowler wicket! NOT credited to bowler!
      7. 1 run (legal, 1 conceded)
      Total Bowler Stats:
        Legal balls: 6 (1.0 over)
        Runs conceded: 4 (bat) + 1 (wide) + 1 (bat) = 6 (4 byes excluded!)
        Bowler wickets: 1 (caught credited, run out excluded!)
        Economy: (6 / 6) * 6.0 = 6.0
        Bowling Strike Rate: 6 / 1 = 6.0
        Bowling Average: 6 / 1 = 6.0
        Dot balls conceded: 3 (Ball 1, Ball 4, Ball 6)
        Dot %: (3 / 6) * 100 = 50.0%
        Boundaries conceded: 1 (Ball 3 four)
        Balls per Boundary Conceded: 6 / 1 = 6.0
        Extras conceded: 1 (the wide)
    """
    records = [
        # Match 1 (Innings 1)
        {
            "delivery_id": "DEL_001",
            "match_id": "MATCH_01",
            "innings_num": 1,
            "over_number": 0,
            "ball_number": 1,
            "over_delivery": 0.1,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_01",
            "bowler_id": "P_BOWL_01",
            "batter_runs": 0,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 0,
            "is_wicket": False,
            "dismissed_player_id": None,
            "dismissal_kind": None,
        },
        {
            "delivery_id": "DEL_002",
            "match_id": "MATCH_01",
            "innings_num": 1,
            "over_number": 0,
            "ball_number": 2,
            "over_delivery": 0.2,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_01",
            "bowler_id": "P_BOWL_01",
            "batter_runs": 0,
            "extras_runs": 1,
            "extras_type": "WIDE",
            "is_legal": False,
            "total_runs": 1,
            "is_wicket": False,
            "dismissed_player_id": None,
            "dismissal_kind": None,
        },
        {
            "delivery_id": "DEL_003",
            "match_id": "MATCH_01",
            "innings_num": 1,
            "over_number": 0,
            "ball_number": 3,
            "over_delivery": 0.2,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_01",
            "bowler_id": "P_BOWL_01",
            "batter_runs": 4,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 4,
            "is_wicket": False,
            "dismissed_player_id": None,
            "dismissal_kind": None,
        },
        {
            "delivery_id": "DEL_004",
            "match_id": "MATCH_01",
            "innings_num": 1,
            "over_number": 0,
            "ball_number": 4,
            "over_delivery": 0.3,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_02",  # Different batter faced ball 4
            "bowler_id": "P_BOWL_01",
            "batter_runs": 0,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 0,
            "is_wicket": True,
            "dismissed_player_id": "P_BAT_02",
            "dismissal_kind": "caught",
        },
        {
            "delivery_id": "DEL_005",
            "match_id": "MATCH_01",
            "innings_num": 1,
            "over_number": 0,
            "ball_number": 5,
            "over_delivery": 0.4,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_01",
            "bowler_id": "P_BOWL_01",
            "batter_runs": 0,
            "extras_runs": 4,
            "extras_type": "BYE",
            "is_legal": True,
            "total_runs": 4,
            "is_wicket": False,
            "dismissed_player_id": None,
            "dismissal_kind": None,
        },
        {
            "delivery_id": "DEL_006",
            "match_id": "MATCH_01",
            "innings_num": 1,
            "over_number": 0,
            "ball_number": 6,
            "over_delivery": 0.5,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_03",
            "bowler_id": "P_BOWL_01",
            "batter_runs": 0,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 0,
            "is_wicket": True,
            "dismissed_player_id": "P_BAT_03",
            "dismissal_kind": "run out",  # Run out! Not bowler wicket!
        },
        {
            "delivery_id": "DEL_007",
            "match_id": "MATCH_01",
            "innings_num": 1,
            "over_number": 0,
            "ball_number": 7,
            "over_delivery": 0.6,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_01",
            "bowler_id": "P_BOWL_01",
            "batter_runs": 1,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 1,
            "is_wicket": False,
            "dismissed_player_id": None,
            "dismissal_kind": None,
        },
        # Match 1 continuing for P_BAT_01 against a different bowler (P_BOWL_02)
        {
            "delivery_id": "DEL_008",
            "match_id": "MATCH_01",
            "innings_num": 1,
            "over_number": 1,
            "ball_number": 1,
            "over_delivery": 1.1,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_01",
            "bowler_id": "P_BOWL_02",
            "batter_runs": 6,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 6,
            "is_wicket": False,
            "dismissed_player_id": None,
            "dismissal_kind": None,
        },
        {
            "delivery_id": "DEL_009",
            "match_id": "MATCH_01",
            "innings_num": 1,
            "over_number": 1,
            "ball_number": 2,
            "over_delivery": 1.2,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_01",
            "bowler_id": "P_BOWL_02",
            "batter_runs": 0,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 0,
            "is_wicket": True,
            "dismissed_player_id": "P_BAT_01",
            "dismissal_kind": "caught",
        },
        # Match 2 for P_BAT_01
        {
            "delivery_id": "DEL_010",
            "match_id": "MATCH_02",
            "innings_num": 1,
            "over_number": 5,
            "ball_number": 1,
            "over_delivery": 5.1,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_01",
            "bowler_id": "P_BOWL_03",
            "batter_runs": 2,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 2,
            "is_wicket": False,
            "dismissed_player_id": None,
            "dismissal_kind": None,
        },
        {
            "delivery_id": "DEL_011",
            "match_id": "MATCH_02",
            "innings_num": 1,
            "over_number": 5,
            "ball_number": 2,
            "over_delivery": 5.2,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_01",
            "bowler_id": "P_BOWL_03",
            "batter_runs": 4,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 4,
            "is_wicket": False,
            "dismissed_player_id": None,
            "dismissal_kind": None,
        },
        {
            "delivery_id": "DEL_012",
            "match_id": "MATCH_02",
            "innings_num": 1,
            "over_number": 5,
            "ball_number": 3,
            "over_delivery": 5.3,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_01",
            "bowler_id": "P_BOWL_03",
            "batter_runs": 1,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 1,
            "is_wicket": False,
            "dismissed_player_id": None,
            "dismissal_kind": None,
        },
        {
            "delivery_id": "DEL_013",
            "match_id": "MATCH_02",
            "innings_num": 1,
            "over_number": 5,
            "ball_number": 4,
            "over_delivery": 5.4,
            "phase": "POWERPLAY",
            "batter_id": "P_BAT_01",
            "bowler_id": "P_BOWL_03",
            "batter_runs": 0,
            "extras_runs": 0,
            "extras_type": None,
            "is_legal": True,
            "total_runs": 0,
            "is_wicket": False,
            "dismissed_player_id": None,
            "dismissal_kind": None,
        },
    ]
    return pd.DataFrame(records)


# ==============================================================================
# 1. METRIC REGISTRY TESTS
# ==============================================================================

def test_metric_registry_structure_and_completeness():
    """Verify that all core batting, bowling, and advanced metrics are properly registered."""
    metrics = get_all_metrics()
    assert len(metrics) >= 20

    # Ensure required keys and metadata exist
    for m in metrics:
        assert m.metric_id
        assert m.name
        assert m.category in [MetricCategory.BATTING, MetricCategory.BOWLING, MetricCategory.FIELDING, MetricCategory.ADVANCED]
        assert m.directionality in [MetricDirection.HIGHER_IS_BETTER, MetricDirection.LOWER_IS_BETTER, MetricDirection.NEUTRAL]
        assert m.formula
        assert m.limitations

    # Check key specific metrics
    sr = get_metric_definition("batting_strike_rate")
    assert sr is not None
    assert sr.category == MetricCategory.BATTING
    assert sr.directionality == MetricDirection.HIGHER_IS_BETTER

    econ = get_metric_definition("economy_rate")
    assert econ is not None
    assert econ.category == MetricCategory.BOWLING
    assert econ.directionality == MetricDirection.LOWER_IS_BETTER

    # Check that advanced open definitions are explicitly marked
    wti = get_metric_definition("wicket_threat_index")
    assert wti is not None
    assert wti.availability_status == MetricStatus.OPEN_DEFINITION

    nvc = get_metric_definition("net_value_contribution")
    assert nvc is not None
    assert nvc.availability_status == MetricStatus.NOT_IMPLEMENTED


# ==============================================================================
# 2. BATTING METRICS CALCULATION TESTS
# ==============================================================================

def test_batting_metrics_exact_calculation(synthetic_cricket_dataframe):
    """Verify mathematical precision of standard batting metrics against synthetic fixture."""
    calc = BattingMetricsCalculator()
    metrics = calc.calculate_metrics("P_BAT_01", synthetic_cricket_dataframe)

    # 1. Runs Scored = 18
    assert metrics["runs_scored"].value == 18
    assert metrics["runs_scored"].status == MetricStatus.CALCULATED

    # 2. Balls Faced = 10 (1 wide correctly excluded from 11 deliveries)
    assert metrics["balls_faced"].value == 10
    assert metrics["balls_faced"].status == MetricStatus.CALCULATED

    # 3. Strike Rate = (18 / 10) * 100 = 180.0
    assert metrics["batting_strike_rate"].value == 180.0
    assert metrics["batting_strike_rate"].status == MetricStatus.CALCULATED

    # 4. Batting Average = 18 / 1 = 18.0
    assert metrics["batting_average"].value == 18.0
    assert metrics["batting_average"].status == MetricStatus.CALCULATED

    # 5. Balls per Dismissal = 10 / 1 = 10.0
    assert metrics["balls_per_dismissal"].value == 10.0
    assert metrics["balls_per_dismissal"].status == MetricStatus.CALCULATED

    # 6. Boundaries
    assert metrics["fours_count"].value == 2
    assert metrics["sixes_count"].value == 1
    assert metrics["boundary_percentage_runs"].value == 77.78
    assert metrics["boundary_percentage_balls"].value == 30.0
    assert metrics["balls_per_boundary"].value == 3.33

    # 7. Dot balls & Suppression (4 dot balls out of 10)
    assert metrics["dot_ball_percentage"].value == 40.0
    assert metrics["dot_ball_suppression"].value == 60.0


def test_batting_edge_case_zero_balls_faced():
    """Verify safe handling when batter faced 0 balls."""
    calc = BattingMetricsCalculator()
    empty_df = pd.DataFrame(columns=["batter_id", "batter_runs", "extras_type", "is_wicket"])
    metrics = calc.calculate_metrics("UNKNOWN_BATTER", empty_df)

    assert metrics["balls_faced"].value == 0
    assert metrics["balls_faced"].status == MetricStatus.INSUFFICIENT_SAMPLE
    assert metrics["batting_strike_rate"].value is None
    assert metrics["batting_strike_rate"].status == MetricStatus.INSUFFICIENT_SAMPLE
    assert metrics["batting_average"].value is None


def test_batting_edge_case_zero_dismissals_not_out(synthetic_cricket_dataframe):
    """Verify that an undefeated batter (0 dismissals) returns DIVIDE_BY_ZERO_SAFEGUARD for average."""
    # Filter dataset so P_BAT_01 has only Match 2 deliveries (where they were not out)
    m2_df = synthetic_cricket_dataframe[synthetic_cricket_dataframe["match_id"] == "MATCH_02"]
    calc = BattingMetricsCalculator()
    metrics = calc.calculate_metrics("P_BAT_01", m2_df)

    assert metrics["runs_scored"].value == 7  # 2 + 4 + 1 + 0 = 7
    assert metrics["balls_faced"].value == 4
    # Dismissals == 0 -> Batting average should be None with DIVIDE_BY_ZERO_SAFEGUARD
    assert metrics["batting_average"].value is None
    assert metrics["batting_average"].status == MetricStatus.DIVIDE_BY_ZERO_SAFEGUARD
    assert metrics["balls_per_dismissal"].value is None
    assert metrics["balls_per_dismissal"].status == MetricStatus.DIVIDE_BY_ZERO_SAFEGUARD


# ==============================================================================
# 3. BOWLING METRICS CALCULATION TESTS
# ==============================================================================

def test_bowling_metrics_exact_calculation(synthetic_cricket_dataframe):
    """Verify bowling metrics, legal ball handling, byes exclusion, and wicket attribution."""
    calc = BowlingMetricsCalculator()
    metrics = calc.calculate_metrics("P_BOWL_01", synthetic_cricket_dataframe)

    # 1. Legal Balls Bowled = 6 (1 wide excluded from legal balls)
    assert metrics["legal_balls_bowled"].value == 6
    assert metrics["overs_bowled"].value == 1.0

    # 2. Runs Conceded: 4 (bat) + 1 (wide) + 1 (bat) = 6 (4 byes EXCLUDED!)
    assert metrics["runs_conceded"].value == 6
    assert metrics["runs_conceded"].status == MetricStatus.CALCULATED

    # 3. Wickets Taken: 1 (Caught credited; Run Out EXCLUDED from bowler wickets!)
    assert metrics["wickets_taken"].value == 1
    assert metrics["wickets_taken"].status == MetricStatus.CALCULATED

    # 4. Economy Rate: (6 / 6) * 6.0 = 6.0
    assert metrics["economy_rate"].value == 6.0
    assert metrics["economy_rate"].status == MetricStatus.CALCULATED

    # 5. Bowling Strike Rate: 6 / 1 = 6.0
    assert metrics["bowling_strike_rate"].value == 6.0

    # 6. Bowling Average: 6 / 1 = 6.0
    assert metrics["bowling_average"].value == 6.0

    # 7. Dot Ball %: 3 dots out of 6 legal deliveries = 50.0%
    assert metrics["bowling_dot_ball_percentage"].value == 50.0

    # 8. Boundaries conceded: 1 four
    assert metrics["boundaries_conceded"].value == 1
    assert metrics["balls_per_boundary_conceded"].value == 6.0

    # 9. Extras conceded: 1 wide
    assert metrics["extras_conceded"].value == 1


def test_bowling_edge_case_zero_wickets(synthetic_cricket_dataframe):
    """Verify that a bowler with zero wickets returns DIVIDE_BY_ZERO_SAFEGUARD for average and strike rate."""
    # P_BOWL_03 has no wickets in MATCH_02
    calc = BowlingMetricsCalculator()
    metrics = calc.calculate_metrics("P_BOWL_03", synthetic_cricket_dataframe)

    assert metrics["wickets_taken"].value == 0
    assert metrics["bowling_strike_rate"].value is None
    assert metrics["bowling_strike_rate"].status == MetricStatus.DIVIDE_BY_ZERO_SAFEGUARD
    assert metrics["bowling_average"].value is None
    assert metrics["bowling_average"].status == MetricStatus.DIVIDE_BY_ZERO_SAFEGUARD


def test_bowling_edge_case_zero_legal_balls():
    """Verify safe handling when bowler has bowled zero deliveries."""
    calc = BowlingMetricsCalculator()
    empty_df = pd.DataFrame(columns=["bowler_id", "batter_runs", "extras_runs", "extras_type", "is_wicket"])
    metrics = calc.calculate_metrics("GHOST_BOWLER", empty_df)

    assert metrics["legal_balls_bowled"].value == 0
    assert metrics["legal_balls_bowled"].status == MetricStatus.INSUFFICIENT_SAMPLE
    assert metrics["economy_rate"].value is None
    assert metrics["economy_rate"].status == MetricStatus.INSUFFICIENT_SAMPLE


# ==============================================================================
# 4. ADVANCED METRICS & DATA AVAILABILITY TESTS
# ==============================================================================

def test_advanced_metrics_true_strike_rate(synthetic_cricket_dataframe):
    """Verify True Strike Rate calculation against phase baselines."""
    evaluator = AdvancedMetricsEvaluator()
    # P_BAT_01 faced all balls in POWERPLAY where default SR baseline is 128.5
    # Actual SR is 180.0 -> TSR = 180.0 - 128.5 = 51.5
    tsr = evaluator.compute_true_strike_rate("P_BAT_01", synthetic_cricket_dataframe)

    assert tsr.value == 51.5
    assert tsr.status == MetricStatus.CALCULATED
    assert tsr.sample_size == 10


def test_advanced_metrics_open_and_deferred_definitions(synthetic_cricket_dataframe):
    """Verify that WTI, CFI, and NVC are reported as OPEN_DEFINITION / NOT_IMPLEMENTED when unsupported."""
    evaluator = AdvancedMetricsEvaluator()

    # WTI without batting_order_position column
    wti = evaluator.evaluate_wicket_threat_index("P_BOWL_01", synthetic_cricket_dataframe)
    assert wti.status == MetricStatus.OPEN_DEFINITION
    assert wti.value is None
    assert "batting_order_position" in wti.context["missing_source_field"]

    # CFI without required_run_rate column
    cfi = evaluator.evaluate_clutch_finishing_index("P_BAT_01", synthetic_cricket_dataframe)
    assert cfi.status == MetricStatus.OPEN_DEFINITION
    assert cfi.value is None

    # NVC is permanently NOT_IMPLEMENTED in this phase
    nvc = evaluator.evaluate_net_value_contribution()
    assert nvc.status == MetricStatus.NOT_IMPLEMENTED
    assert nvc.value is None


# ==============================================================================
# 5. AGGREGATION & FILTERING TESTS
# ==============================================================================

def test_aggregation_and_deduplication(synthetic_cricket_dataframe):
    """Verify delivery filtering, sample size calculation, and duplicate delivery rejection."""
    aggregator = DeliveryAggregator()

    # Append a duplicate delivery
    duplicated_df = pd.concat([synthetic_cricket_dataframe, synthetic_cricket_dataframe.iloc[[0]]], ignore_index=True)
    assert len(duplicated_df) == len(synthetic_cricket_dataframe) + 1

    # Filter with deduplication
    cleaned_df = aggregator.filter_deliveries(duplicated_df)
    assert len(cleaned_df) == len(synthetic_cricket_dataframe)

    # Filter by match_id
    filtered_m1 = aggregator.filter_deliveries(
        synthetic_cricket_dataframe,
        MetricCalculationFilter(match_ids=["MATCH_01"]),
    )
    assert len(filtered_m1) == 9
    assert set(filtered_m1["match_id"].unique()) == {"MATCH_01"}

    # Sample size info for P_BAT_01
    sample = aggregator.compute_player_sample_size("P_BAT_01", synthetic_cricket_dataframe)
    assert sample.balls_faced == 10
    assert sample.batting_innings == 2
    assert sample.matches_played == 2


# ==============================================================================
# 6. DIMENSION GROUPING TESTS
# ==============================================================================

def test_role_specific_dimension_builders(synthetic_cricket_dataframe):
    """Verify that performance dimensions are cleanly structured without composite score blending."""
    bat_calc = BattingMetricsCalculator()
    bowl_calc = BowlingMetricsCalculator()
    dim_builder = DimensionBuilder()

    bat_metrics = bat_calc.calculate_metrics("P_BAT_01", synthetic_cricket_dataframe)
    bowl_metrics = bowl_calc.calculate_metrics("P_BOWL_01", synthetic_cricket_dataframe)

    bat_dims = dim_builder.build_batting_dimensions(bat_metrics)
    assert "scoring_output" in bat_dims
    assert "scoring_efficiency" in bat_dims
    assert "boundary_contribution" in bat_dims
    assert "dismissal_resistance" in bat_dims
    assert "consistency" in bat_dims

    assert "runs_scored" in bat_dims["scoring_output"].metrics
    assert "batting_strike_rate" in bat_dims["scoring_efficiency"].metrics

    bowl_dims = dim_builder.build_bowling_dimensions(bowl_metrics)
    assert "wicket_taking_performance" in bowl_dims
    assert "run_containment" in bowl_dims
    assert "dot_ball_generation" in bowl_dims
    assert "bowling_workload" in bowl_dims
    assert "boundary_containment" in bowl_dims


# ==============================================================================
# 7. END-TO-END SERVICE & API INTEGRATION TESTS
# ==============================================================================

def test_analytics_service_end_to_end_calculation(synthetic_cricket_dataframe):
    """Verify that AnalyticsService orchestrates calculation and returns full structured response."""
    service = AnalyticsService()
    res = service.calculate_from_dataframe(
        dataset_id="SYNTHETIC_DATASET_01",
        df=synthetic_cricket_dataframe,
        target_player_id="P_BAT_01",
    )

    assert res.dataset_id == "SYNTHETIC_DATASET_01"
    assert res.total_players_computed == 1
    player = res.players[0]
    assert player.player_id == "P_BAT_01"
    assert player.sample_size.balls_faced == 10
    assert player.batting_metrics["runs_scored"].value == 18
    assert player.provenance.calculation_version == "1.0.0"


@pytest.mark.anyio
async def test_api_list_metrics():
    """Verify GET /api/v1/analytics/metrics returns the full registry catalog."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_metrics"] >= 20
        metric_ids = [m["metric_id"] for m in data["metrics"]]
        assert "batting_strike_rate" in metric_ids
        assert "economy_rate" in metric_ids
        assert "true_strike_rate" in metric_ids


@pytest.mark.anyio
async def test_api_calculate_and_dataset_summary(synthetic_cricket_dataframe):
    """Verify POST /api/v1/analytics/calculate and GET /datasets/{id}/summary against DB records."""
    unique_ds_id = f"DS_ANALYTICS_{uuid.uuid4().hex[:8]}"
    unique_player_id = f"P_BAT_{uuid.uuid4().hex[:6]}"

    # Copy fixture and replace batter_id P_BAT_01 with unique_player_id
    df_copy = synthetic_cricket_dataframe.copy()
    df_copy.loc[df_copy["batter_id"] == "P_BAT_01", "batter_id"] = unique_player_id
    df_copy.loc[df_copy["dismissed_player_id"] == "P_BAT_01", "dismissed_player_id"] = unique_player_id

    # Seed deliveries into DB
    async with async_session_factory() as session:
        # Create dataset
        ds = Dataset(
            dataset_id=unique_ds_id,
            workspace_id="default_workspace",
            source_filename="test_cricket_analytics.csv",
            file_format="CSV",
            file_sha256=f"hash_{unique_ds_id}",
            storage_path="/tmp/test.csv",
            status="PERSISTED",
        )
        session.add(ds)

        # Create player
        p = Player(
            player_id=unique_player_id,
            canonical_name="Synthetic Test Batter",
            primary_role="BATTER",
        )
        session.add(p)

        # Add deliveries from synthetic fixture
        for _, row in df_copy.iterrows():
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
        # 1. Test POST /api/v1/analytics/calculate
        calc_resp = await client.post(
            "/api/v1/analytics/calculate",
            json={
                "dataset_id": unique_ds_id,
                "player_id": unique_player_id,
                "include_dimensions": True,
            },
        )
        assert calc_resp.status_code == 200
        calc_data = calc_resp.json()
        assert calc_data["dataset_id"] == unique_ds_id
        assert calc_data["total_players_computed"] == 1
        p_res = calc_data["players"][0]
        assert p_res["player_name"] == "Synthetic Test Batter"
        assert p_res["batting_metrics"]["runs_scored"]["value"] == 18
        assert p_res["batting_metrics"]["batting_strike_rate"]["value"] == 180.0

        # 2. Test GET /api/v1/analytics/datasets/{id}/summary
        sum_resp = await client.get(f"/api/v1/analytics/datasets/{unique_ds_id}/summary")
        assert sum_resp.status_code == 200
        sum_data = sum_resp.json()
        assert sum_data["dataset_id"] == unique_ds_id
        assert sum_data["total_deliveries"] == len(df_copy)
        assert sum_data["total_runs_scored"] > 0
