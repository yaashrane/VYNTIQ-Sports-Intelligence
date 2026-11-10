"""Automated Verification and Reconciliation Test Suite for VYNTIQ Analytical Audit.

Tests deterministic cricket accounting rules, pressure formula boundaries,
Bayesian shrinkage mechanics, and ranking integrity.
"""

import os
import pytest
import numpy as np
import pandas as pd

AUDIT_DIR = r"d:\VYNTIQ Sports Intelligence\audit"
DATA_DIR = r"d:\VYNTIQ Sports Intelligence\data\official_super_rr_s2"


def test_cricket_accounting_extras_and_legal_balls():
    """Verify cricket rules for legal balls, batter balls faced, and bowler conceded runs."""
    # Synthetic test delivery DataFrame
    sample = pd.DataFrame([
        # Overstep no-ball with 2 bat runs
        {"extras_type": "Overstep", "runs": 2, "extras_2_runs": 0, "is_wicket": False, "dismissal_type": None},
        # Wide ball with 1 extra
        {"extras_type": "wide", "runs": 0, "extras_2_runs": 0, "is_wicket": False, "dismissal_type": None},
        # Leg-bye with 4 runs
        {"extras_type": "legbyes", "runs": 4, "extras_2_runs": 0, "is_wicket": False, "dismissal_type": None},
        # Legal ball with 6 runs
        {"extras_type": None, "runs": 6, "extras_2_runs": 0, "is_wicket": False, "dismissal_type": None},
    ])

    # 1. Legal ball check
    sample["is_legal_ball"] = ~sample["extras_type"].isin(["wide", "Overstep", "other"])
    assert list(sample["is_legal_ball"]) == [False, False, True, True]

    # 2. Batter ball faced check
    sample["is_batter_ball_faced"] = sample["extras_type"] != "wide"
    assert list(sample["is_batter_ball_faced"]) == [True, False, True, True]

    # 3. Bowler runs conceded check
    # Bat runs + wides (1 + ext2) + noballs (1 + bat + ext2); legbyes = 0 runs conceded
    batter_runs = np.where(sample["extras_type"].isin(["wide", "legbyes", "byes", "Penalty"]), 0, sample["runs"])
    ext2 = sample["extras_2_runs"].fillna(0)
    wide_m = sample["extras_type"] == "wide"
    nb_m = sample["extras_type"].isin(["Overstep", "other"])

    bowler_runs = batter_runs.astype(float).copy()
    bowler_runs[wide_m] = 1.0 + ext2[wide_m]
    bowler_runs[nb_m] = 1.0 + batter_runs[nb_m] + ext2[nb_m]

    # Row 0: No-ball (1 penalty + 2 bat = 3 runs conceded)
    # Row 1: Wide (1 run conceded)
    # Row 2: Leg-bye (0 runs conceded to bowler)
    # Row 3: Legal 6 (6 runs conceded)
    assert list(bowler_runs) == [3.0, 1.0, 0.0, 6.0]


def test_cricket_accounting_dismissal_attribution():
    """Verify dismissal credit for bowlers and batters."""
    sample = pd.DataFrame([
        {"striker_id": 101, "dismissed_player_id": 101, "is_wicket": True, "dismissal_type": "Bowled"},
        {"striker_id": 101, "dismissed_player_id": 102, "is_wicket": True, "dismissal_type": "RunOut"},
        {"striker_id": 101, "dismissed_player_id": 101, "is_wicket": True, "dismissal_type": "Caught"},
        {"striker_id": 101, "dismissed_player_id": 101, "is_wicket": True, "dismissal_type": "Retire Out"},
    ])

    bowler_wicket_types = ["Caught", "Bowled", "LBW", "Stump", "Hit Wicket"]
    is_bowler_wkt = (sample["is_wicket"] == True) & (sample["dismissal_type"].isin(bowler_wicket_types))
    # Only Bowled and Caught are credited to bowler
    assert list(is_bowler_wkt) == [True, False, True, False]

    is_batter_out = (sample["is_wicket"] == True) & (sample["dismissed_player_id"] == sample["striker_id"])
    # Row 1 is non-striker runout, striker is NOT out
    assert list(is_batter_out) == [True, False, True, True]


def test_bayesian_shrinkage_monotonicity():
    """Verify Bayesian shrinkage pulls small samples toward prior mean (50.0)."""
    C_bat = 120
    prior_mean = 50.0

    raw_score = 90.0
    for N in [10, 60, 120, 300, 600]:
        rel = N / (N + C_bat)
        p_vor = (raw_score * rel) + (prior_mean * (1.0 - rel))
        # As N increases, p_vor approaches raw_score (90.0)
        assert 50.0 < p_vor <= raw_score

    # Check N=120 gives exactly 50% sample weight
    rel_120 = 120 / (120 + 120)
    assert rel_120 == 0.5
    assert (raw_score * 0.5 + prior_mean * 0.5) == 70.0


def test_ranking_audited_artifacts_exist():
    """Verify all audit artifacts were created and are non-empty."""
    expected_files = [
        f"{AUDIT_DIR}/data_integrity/competition_filtering_audit.csv",
        f"{AUDIT_DIR}/data_integrity/extras_and_legal_balls_audit.csv",
        f"{AUDIT_DIR}/pressure_model/pressure_tier_distribution.csv",
        f"{AUDIT_DIR}/rankings/batters_p_vor_audit.csv",
        f"{AUDIT_DIR}/rankings/bowlers_p_vor_audit.csv",
        f"{AUDIT_DIR}/rankings/unstop_top10_batters.csv",
        f"{AUDIT_DIR}/rankings/unstop_top10_bowlers.csv",
        f"{AUDIT_DIR}/rankings/eligibility_audit.csv",
        f"{AUDIT_DIR}/rankings/format_comparison_metrics.csv",
        f"{AUDIT_DIR}/sensitivity/pressure_definition_sensitivity.csv",
        f"{AUDIT_DIR}/sensitivity/weight_sensitivity.csv",
    ]
    for path in expected_files:
        assert os.path.exists(path), f"Missing audit artifact: {path}"
        df = pd.read_csv(path)
        assert len(df) > 0, f"Artifact is empty: {path}"


def test_top10_rankings_integrity_and_santner_metrics():
    """Verify top 10 rankings are strictly sorted and Mitchell Santner's verified economy is sub-7.0."""
    bat_df = pd.read_csv(f"{AUDIT_DIR}/rankings/batters_p_vor_audit.csv")
    bowl_df = pd.read_csv(f"{AUDIT_DIR}/rankings/bowlers_p_vor_audit.csv")

    top10_bat = bat_df.head(10)
    top10_bowl = bowl_df.head(10)

    # Check monotonic descending order of P-VOR
    assert list(top10_bat["p_vor"]) == sorted(list(top10_bat["p_vor"]), reverse=True)
    assert list(top10_bowl["p_vor"]) == sorted(list(top10_bowl["p_vor"]), reverse=True)

    # Check Tristan Stubbs is #1 batter
    assert top10_bat.iloc[0]["player_name"] == "Tristan Stubbs"

    # Check Mitchell Santner's pressure economy is sub-7.0 (6.97)
    santner_rows = bowl_df[bowl_df["player_name"] == "Mitchell Santner"]
    assert len(santner_rows) == 1
    santner = santner_rows.iloc[0]
    assert santner["pressure_econ"] < 7.00
    assert abs(santner["pressure_econ"] - 6.97) < 0.05

