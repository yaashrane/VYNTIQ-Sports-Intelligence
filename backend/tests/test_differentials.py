"""Unit tests for the Performance Differential Analyzer."""

import pandas as pd
from backend.app.services.analytics.pressure_differentials import (
    DifferentialConfig,
    PerformanceDifferentialAnalyzer,
)


def test_differential_analyzer_batters():
    """Verify batting differential calculations."""
    deliveries = [
        # Normal delivery
        {
            "striker_id": 1,
            "striker_name": "Clutch Batter",
            "runs": 1,
            "is_four": False,
            "is_six": False,
            "is_wicket": False,
            "pressure_tier": "LOW_PRESSURE",
            "match_id": 101,
        },
        # High pressure delivery (boundary)
        {
            "striker_id": 1,
            "striker_name": "Clutch Batter",
            "runs": 6,
            "is_four": False,
            "is_six": True,
            "is_wicket": False,
            "pressure_tier": "HIGH_PRESSURE",
            "match_id": 101,
        },
    ]

    analyzer = PerformanceDifferentialAnalyzer(
        DifferentialConfig(min_hp_balls_batter=1, min_total_balls_batter=2)
    )
    df_bat = analyzer.analyze_batters(pd.DataFrame(deliveries))

    assert len(df_bat) == 1
    row = df_bat.iloc[0]
    assert row["total_balls"] == 2
    assert row["hp_balls"] == 1
    assert row["base_sr"] == 350.0  # 7 runs off 2 balls
    assert row["hp_sr"] == 600.0    # 6 runs off 1 ball
    assert row["delta_sr"] == 250.0
    assert bool(row["is_qualified"]) is True


def test_differential_analyzer_bowlers():
    """Verify bowling differential calculations."""
    deliveries = [
        # Baseline dot
        {
            "bowler_id": 2,
            "bowler_name": "Death Specialist",
            "is_legal": True,
            "delivery_total_runs": 0,
            "is_wicket": False,
            "runs": 0,
            "pressure_tier": "LOW_PRESSURE",
            "match_id": 101,
        },
        # High pressure wicket
        {
            "bowler_id": 2,
            "bowler_name": "Death Specialist",
            "is_legal": True,
            "delivery_total_runs": 1,
            "is_wicket": True,
            "runs": 1,
            "pressure_tier": "HIGH_PRESSURE",
            "match_id": 101,
        },
    ]

    analyzer = PerformanceDifferentialAnalyzer(
        DifferentialConfig(min_hp_balls_bowler=1, min_total_balls_bowler=2)
    )
    df_bowl = analyzer.analyze_bowlers(pd.DataFrame(deliveries))

    assert len(df_bowl) == 1
    row = df_bowl.iloc[0]
    assert row["total_legal_balls"] == 2
    assert row["hp_legal_balls"] == 1
    assert row["hp_wickets"] == 1
    assert bool(row["is_qualified"]) is True
