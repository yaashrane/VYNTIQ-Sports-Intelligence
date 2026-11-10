"""Unit tests for the Pressure Ranking Engine."""

import pandas as pd
from backend.app.services.scoring.pressure_ranking import (
    BattingWeights,
    BowlingWeights,
    PressureRankingEngine,
)


def test_pressure_ranking_batters():
    """Verify that batters are ranked deterministically and shrunken appropriately."""
    batters_data = [
        # Player A: High sample, strong strike rate
        {
            "striker_id": 1,
            "striker_name": "Elite Clutch",
            "hp_balls": 400,
            "base_sr": 150.0,
            "hp_sr": 180.0,
            "delta_sr": 30.0,
            "hp_bnd_pct": 25.0,
            "hp_dot_pct": 25.0,
            "hp_avg": 40.0,
            "is_qualified": True,
        },
        # Player B: Small sample, identical raw stats
        {
            "striker_id": 2,
            "striker_name": "Small Sample Clutch",
            "hp_balls": 100,
            "base_sr": 150.0,
            "hp_sr": 180.0,
            "delta_sr": 30.0,
            "hp_bnd_pct": 25.0,
            "hp_dot_pct": 25.0,
            "hp_avg": 40.0,
            "is_qualified": True,
        },
        # Player C: Poor under pressure
        {
            "striker_id": 3,
            "striker_name": "Struggler",
            "hp_balls": 300,
            "base_sr": 140.0,
            "hp_sr": 110.0,
            "delta_sr": -30.0,
            "hp_bnd_pct": 12.0,
            "hp_dot_pct": 45.0,
            "hp_avg": 15.0,
            "is_qualified": True,
        },
    ]

    engine = PressureRankingEngine(bat_weights=BattingWeights(shrinkage_c=100.0))
    ranked = engine.rank_batters(pd.DataFrame(batters_data))

    assert len(ranked) == 3
    # Player A has higher sample reliability than Player B, so Player A must rank #1
    assert ranked.iloc[0]["striker_name"] == "Elite Clutch"
    assert ranked.iloc[1]["striker_name"] == "Small Sample Clutch"
    assert ranked.iloc[2]["striker_name"] == "Struggler"
    assert ranked.iloc[0]["final_pressure_rating"] > ranked.iloc[1]["final_pressure_rating"]
    assert ranked.iloc[0]["pressure_rank"] == 1


def test_pressure_ranking_bowlers():
    """Verify that bowlers are ranked deterministically with economy and wickets."""
    bowlers_data = [
        # Bowler A: Elite economy under pressure
        {
            "bowler_id": 1,
            "bowler_name": "Lockdown Spinner",
            "hp_legal_balls": 300,
            "base_econ": 7.5,
            "hp_econ": 6.2,
            "delta_econ": 1.3,
            "hp_dot_pct": 42.0,
            "hp_bnd_conc_pct": 10.0,
            "hp_wickets": 30,
            "hp_wkt_sr": 10.0,
            "is_qualified": True,
        },
        # Bowler B: High economy under pressure
        {
            "bowler_id": 2,
            "bowler_name": "Expensive Bowler",
            "hp_legal_balls": 300,
            "base_econ": 8.5,
            "hp_econ": 11.0,
            "delta_econ": -2.5,
            "hp_dot_pct": 20.0,
            "hp_bnd_conc_pct": 22.0,
            "hp_wickets": 15,
            "hp_wkt_sr": 20.0,
            "is_qualified": True,
        },
    ]

    engine = PressureRankingEngine(bowl_weights=BowlingWeights(shrinkage_c=100.0))
    ranked = engine.rank_bowlers(pd.DataFrame(bowlers_data))

    assert len(ranked) == 2
    assert ranked.iloc[0]["bowler_name"] == "Lockdown Spinner"
    assert ranked.iloc[0]["pressure_rank"] == 1
    assert ranked.iloc[0]["final_pressure_rating"] > ranked.iloc[1]["final_pressure_rating"]

