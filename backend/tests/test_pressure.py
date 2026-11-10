"""Unit tests for the T20 Pressure Modeling Engine."""

import pandas as pd
import pytest
from backend.app.services.analytics.pressure import PressureEngine, PressureTier


def test_pressure_engine_chase_and_super_over():
    """Verify pressure escalation in chase and 10.0 score in super overs."""
    # Synthetic deliveries: 1 match, 2 innings
    deliveries_data = [
        # Innings 1: 6 balls in death over 20
        {
            "match_id": 1,
            "innings": 1,
            "overid": 20,
            "over_ball_num": i,
            "runs": 2,
            "extras_type": None,
            "extras_2_runs": 0,
            "is_wicket": False,
        }
        for i in range(1, 7)
    ] + [
        # Innings 2: Ball 1 (Target: 13, RRR: 0.65 -> comfortable)
        {
            "match_id": 1,
            "innings": 2,
            "overid": 1,
            "over_ball_num": 1,
            "runs": 1,
            "extras_type": None,
            "extras_2_runs": 0,
            "is_wicket": False,
        },
        # Innings 2: Ball 115 (Over 20.1, Needs 14 off 6 balls -> high pressure)
        {
            "match_id": 1,
            "innings": 2,
            "overid": 20,
            "over_ball_num": 1,
            "runs": 0,
            "extras_type": None,
            "extras_2_runs": 0,
            "is_wicket": False,
        },
        # Innings 3: Super Over delivery
        {
            "match_id": 1,
            "innings": 3,
            "overid": 1,
            "over_ball_num": 1,
            "runs": 1,
            "extras_type": None,
            "extras_2_runs": 0,
            "is_wicket": False,
        },
    ]

    matches_data = [{"match_id": 1, "knock_out": 0, "revised_target": None}]

    df_deliv = pd.DataFrame(deliveries_data)
    df_match = pd.DataFrame(matches_data)

    engine = PressureEngine()
    enriched = engine.augment_deliveries_with_pressure(df_deliv, df_match)

    assert len(enriched) == len(deliveries_data)
    assert "pressure_index" in enriched.columns
    assert "pressure_tier" in enriched.columns

    # Innings 1 over 20 should have death-over baseline pressure (>= 7.0)
    inn1_death = enriched[enriched["innings"] == 1]
    assert (inn1_death["pressure_index"] >= 7.0).all()

    # Super over must be 10.0
    super_over = enriched[enriched["innings"] == 3].iloc[0]
    assert super_over["pressure_index"] == 10.0
    assert super_over["pressure_tier"] == PressureTier.HIGH_PRESSURE.value


def test_knockout_multiplier():
    """Verify knockout match raises pressure by 15%."""
    data = [
        {
            "match_id": 10,
            "innings": 1,
            "overid": 5,
            "over_ball_num": 1,
            "runs": 0,
            "extras_type": None,
            "extras_2_runs": 0,
            "is_wicket": False,
        }
    ]
    df = pd.DataFrame(data)

    engine = PressureEngine()
    res_league = engine.augment_deliveries_with_pressure(df, pd.DataFrame([{"match_id": 10, "knock_out": 0}]))
    res_ko = engine.augment_deliveries_with_pressure(df, pd.DataFrame([{"match_id": 10, "knock_out": 1}]))

    assert res_ko.iloc[0]["pressure_index"] == pytest.approx(res_league.iloc[0]["pressure_index"] * 1.15, rel=1e-3)

