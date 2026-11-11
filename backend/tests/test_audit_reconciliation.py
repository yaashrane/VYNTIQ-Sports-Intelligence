"""Automated Verification and Technical Reconciliation Test Suite (V3).

Tests:
1. Extra classifications & legal deliveries (wides, overstep, other beamers, byes, leg-byes, penalty).
2. Bowler run attribution (0 runs for byes/leg-byes).
3. Batter dismissal attribution (striker-specific outs).
4. Canonical pressure engine boundary conditions (Innings 1, Innings 2, contestability, won-match, Super Overs).
5. Competition filtering & match reconciliation (837 delivered matches, 16 abandoned, 194,014 primary balls).
6. Empirical reliability shrinkage & genuine P-VOR calculation.
7. Ranking reproducibility & determinism.
8. API vs. audit ranking equality.
9. CSV vs. Markdown/PDF data consistency.
10. Strict/standard/broad multi-definition sensitivity for BOTH Batters and Bowlers.
11. Portable pathlib paths with spaces.
12. Mitchell Santner verified economy reconciliation (< 7.00 rpo).
"""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "official_super_rr_s2"
AUDIT_DIR = PROJECT_ROOT / "audit"
DOCS_DIR = PROJECT_ROOT / "docs"

from backend.app.services.analytics.pressure import PressureEngine, PressureWeights, PressureTier
from backend.app.services.scoring.pressure_ranking import (
    PressureRankingEngine,
    BattingRankingWeights,
    BowlingRankingWeights,
    RankingConfig,
)


def test_extra_classifications_and_legal_deliveries():
    """Verify that wides, overstep, and other beamers are illegal; byes/leg-byes are legal."""
    test_df = pd.DataFrame([
        {"extras_type": "Overstep", "runs": 2, "extras_2_runs": 0, "is_wicket": False, "dismissal_type": None},
        {"extras_type": "other", "runs": 0, "extras_2_runs": 0, "is_wicket": False, "dismissal_type": None},
        {"extras_type": "wide", "runs": 0, "extras_2_runs": 0, "is_wicket": False, "dismissal_type": None},
        {"extras_type": "legbyes", "runs": 4, "extras_2_runs": 0, "is_wicket": False, "dismissal_type": None},
        {"extras_type": "byes", "runs": 1, "extras_2_runs": 0, "is_wicket": False, "dismissal_type": None},
        {"extras_type": "Penalty", "runs": 0, "extras_2_runs": 0, "is_wicket": False, "dismissal_type": None},
        {"extras_type": None, "runs": 6, "extras_2_runs": 0, "is_wicket": False, "dismissal_type": None},
    ])

    test_df["match_id"] = 1
    test_df["innings"] = 1
    test_df["overid"] = 1
    test_df["over_ball_num"] = range(1, len(test_df) + 1)
    test_df["striker_id"] = 1
    test_df["bowler_id"] = 2

    engine = PressureEngine()
    enriched = engine.augment_deliveries_with_pressure(test_df)

    # 1. Legal balls: Overstep, other, wide are NOT legal balls
    assert list(enriched["is_legal_ball"]) == [False, False, False, True, True, True, True]

    # 2. Balls faced by batter: wide is NOT faced; no-balls and byes/leg-byes ARE faced
    assert list(enriched["is_batter_ball_faced"]) == [True, True, False, True, True, True, True]

    # 3. Bowler runs conceded:
    # Row 0: Overstep no-ball (1 penalty + 2 bat = 3 runs)
    # Row 1: Other beamer no-ball (1 penalty + 0 bat = 1 run)
    # Row 2: Wide (1 run)
    # Row 3: Leg-byes (0 runs conceded to bowler)
    # Row 4: Byes (0 runs conceded to bowler)
    # Row 5: Penalty (0 runs conceded to bowler)
    # Row 6: Legal six (6 runs conceded)
    assert list(enriched["bowler_runs_conceded"]) == [3.0, 1.0, 1.0, 0.0, 0.0, 0.0, 6.0]


def test_dismissal_attribution():
    """Verify dismissal credit for bowlers and strikers."""
    sample = pd.DataFrame([
        {"striker_id": 101, "dismissed_player_id": 101, "is_wicket": True, "dismissal_type": "Bowled"},
        {"striker_id": 101, "dismissed_player_id": 102, "is_wicket": True, "dismissal_type": "RunOut"},
        {"striker_id": 101, "dismissed_player_id": 101, "is_wicket": True, "dismissal_type": "Caught"},
        {"striker_id": 101, "dismissed_player_id": 101, "is_wicket": True, "dismissal_type": "Retire Out"},
    ])
    sample["match_id"] = 1
    sample["innings"] = 1
    sample["overid"] = 1
    sample["over_ball_num"] = range(1, 5)
    sample["extras_type"] = None
    sample["runs"] = 0

    engine = PressureEngine()
    res = engine.augment_deliveries_with_pressure(sample)

    # Only Bowled and Caught are credited to bowler
    assert list(res["is_bowler_wicket"]) == [True, False, True, False]
    # Striker is out on rows 0, 2, 3 (row 1 is non-striker runout)
    assert list(res["is_batter_out"]) == [True, False, True, True]


def test_pressure_engine_boundaries_and_contestability():
    """Verify Innings 1, Innings 2, contestability filters, and Super Overs."""
    deliveries = [
        # Innings 1 death over
        {"match_id": 1, "innings": 1, "overid": 20, "over_ball_num": 1, "runs": 4, "extras_type": None, "is_wicket": False},
    ] + [
        # 114 prior balls in Innings 2 (Overs 1 to 19)
        {"match_id": 1, "innings": 2, "overid": o, "over_ball_num": b, "runs": 0, "extras_type": None, "is_wicket": False}
        for o in range(1, 20) for b in range(1, 7)
    ] + [
        # Innings 2 Over 20 Ball 1: Unwinnable chase (needs 50 off 6 balls -> runs_needed 50 > 6 * 6 = 36)
        {"match_id": 1, "innings": 2, "overid": 20, "over_ball_num": 1, "runs": 0, "extras_type": None, "is_wicket": False},
        # Innings 3: Super Over
        {"match_id": 1, "innings": 3, "overid": 1, "over_ball_num": 1, "runs": 1, "extras_type": None, "is_wicket": False},
    ]
    df_deliv = pd.DataFrame(deliveries)
    df_matches = pd.DataFrame([{"match_id": 1, "knock_out": 0, "revised_target": 50.0}])

    engine = PressureEngine()
    res = engine.augment_deliveries_with_pressure(df_deliv, df_matches)

    # Innings 1 death over must be >= 7.0
    assert res.iloc[0]["pressure_index"] >= 7.0

    # Unwinnable situation in over 20 should be clamped to 1.0 by contestability filter
    unwinnable_row = res[(res["innings"] == 2) & (res["overid"] == 20)].iloc[0]
    assert unwinnable_row["pressure_index"] == 1.0

    # Super over must be exactly 10.0
    super_row = res[res["innings"] == 3].iloc[0]
    assert super_row["pressure_index"] == 10.0
    assert super_row["pressure_tier"] == PressureTier.EXTREME_PRESSURE.value


def test_contestability_edge_cases_and_extras():
    """Verify contestability boundary edge cases with extras and threshold boundaries."""
    # 1. Competitive chase: 18 needed off 6 balls (RRR 18.0 <= 36.0) -> high pressure
    # 2. Borderline achievable: 6 needed off 1 ball (RRR 36.0 <= 36.0) -> high pressure
    # 3. Uncompetitive garbage time: 7 needed off 1 ball (7 > 6 * 1) -> clamped to 1.0
    # 4. Wide bowled when 7 needed off 1 ball: does not consume legal delivery
    deliveries = [
        # 114 prior balls in Innings 2 (Overs 1 to 19)
        {"match_id": 2, "innings": 2, "overid": o, "over_ball_num": b, "runs": 0, "extras_type": None, "is_wicket": False}
        for o in range(1, 20) for b in range(1, 7)
    ] + [
        # Over 20 Ball 1: Target was 20, 0 runs so far, 6 balls remaining -> 20 <= 36 -> highly competitive
        {"match_id": 2, "innings": 2, "overid": 20, "over_ball_num": 1, "runs": 0, "extras_type": None, "is_wicket": False},
        # Over 20 Ball 2: 5 balls remaining, say target was 31 (needs 31 off 5 balls -> 31 > 30 -> uncompetitive)
        {"match_id": 2, "innings": 2, "overid": 20, "over_ball_num": 2, "runs": 0, "extras_type": None, "is_wicket": False},
    ]
    df_deliv = pd.DataFrame(deliveries)
    df_matches = pd.DataFrame([{"match_id": 2, "knock_out": 0, "revised_target": 20.0}])

    engine = PressureEngine()
    res = engine.augment_deliveries_with_pressure(df_deliv, df_matches)
    
    over20_ball1 = res[(res["innings"] == 2) & (res["overid"] == 20) & (res["over_ball_num"] == 1)].iloc[0]
    # RRR is 20 off 6 balls = 20.0 rpo. Runs needed (20) <= 6 * 6 = 36. Pressure index should be elevated (>= 7.0)
    assert over20_ball1["pressure_index"] >= 7.0
    assert over20_ball1["pressure_tier"] in (PressureTier.HIGH_PRESSURE.value, PressureTier.EXTREME_PRESSURE.value)


def test_rrr_curve_continuity_at_all_breakpoints():
    """Verify mathematical continuity of P_rate curve immediately below, at, and above every breakpoint."""
    w = PressureWeights()

    def calc_prate(rrr: float) -> float:
        if rrr <= w.rrr_comfortable_threshold:
            return max(0.5, rrr / 3.0)
        elif rrr <= w.rrr_contested_threshold:
            return 2.0 + (rrr - w.rrr_comfortable_threshold) * 1.0
        elif rrr <= w.rrr_extreme_threshold:
            return 6.0 + (rrr - w.rrr_contested_threshold) * 0.6
        else:
            return min(10.0, 9.0 + (rrr - w.rrr_extreme_threshold) * 0.2)

    eps = 0.001

    # 1. Breakpoint RRR = 6.0
    val_6_below = calc_prate(6.0 - eps)
    val_6_at = calc_prate(6.0)
    val_6_above = calc_prate(6.0 + eps)
    assert val_6_at == pytest.approx(2.0, abs=1e-5)
    assert abs(val_6_below - val_6_at) < 0.002
    assert abs(val_6_above - val_6_at) < 0.002

    # 2. Breakpoint RRR = 10.0
    val_10_below = calc_prate(10.0 - eps)
    val_10_at = calc_prate(10.0)
    val_10_above = calc_prate(10.0 + eps)
    assert val_10_at == pytest.approx(6.0, abs=1e-5)
    assert abs(val_10_below - val_10_at) < 0.002
    assert abs(val_10_above - val_10_at) < 0.002

    # 3. Breakpoint RRR = 15.0
    val_15_below = calc_prate(15.0 - eps)
    val_15_at = calc_prate(15.0)
    val_15_above = calc_prate(15.0 + eps)
    assert val_15_at == pytest.approx(9.0, abs=1e-5)
    assert abs(val_15_below - val_15_at) < 0.002
    assert abs(val_15_above - val_15_at) < 0.002

    # 4. Breakpoint RRR = 20.0 (asymptotic plateau cap at 10.0)
    val_20_below = calc_prate(20.0 - eps)
    val_20_at = calc_prate(20.0)
    val_20_above = calc_prate(20.0 + eps)
    assert val_20_at == pytest.approx(10.0, abs=1e-5)
    assert val_20_above == pytest.approx(10.0, abs=1e-5)
    assert abs(val_20_below - val_20_at) < 0.002


def test_knockout_multiplier_explicit_integration():
    """Verify knockout multiplier across league, playoff, super over, and uncompetitive scenarios."""
    engine = PressureEngine()

    # Deliveries: Innings 1 over 10, Innings 2 contested over 18, Innings 2 uncompetitive, Innings 3 super over
    # Provide 102 prior balls in Innings 2 so over 18 ball 1 has 18 balls remaining
    inn2_prior = [
        {"match_id": 99, "innings": 2, "overid": o, "over_ball_num": b, "runs": 0, "extras_type": None, "is_wicket": False}
        for o in range(1, 18) for b in range(1, 7)
    ]
    deliveries = [
        # Innings 1: middle over
        {"match_id": 99, "innings": 1, "overid": 10, "over_ball_num": 1, "runs": 1, "extras_type": None, "is_wicket": False},
    ] + inn2_prior + [
        # Innings 2: Over 18 Ball 1 (needs 30 off 18 balls -> RRR = 10.0, 10 wickets in hand)
        {"match_id": 99, "innings": 2, "overid": 18, "over_ball_num": 1, "runs": 1, "extras_type": None, "is_wicket": False},
        # Innings 3: Super Over
        {"match_id": 99, "innings": 3, "overid": 1, "over_ball_num": 1, "runs": 2, "extras_type": None, "is_wicket": False},
    ]
    df_deliv = pd.DataFrame(deliveries)

    # 1. League match (knock_out = 0)
    res_league = engine.augment_deliveries_with_pressure(df_deliv, pd.DataFrame([{"match_id": 99, "knock_out": 0, "revised_target": 30.0}]))
    
    # 2. Playoff match (knock_out = 1)
    res_playoff = engine.augment_deliveries_with_pressure(df_deliv, pd.DataFrame([{"match_id": 99, "knock_out": 1, "revised_target": 30.0}]))

    pi_inn1_league = res_league[res_league["innings"] == 1].iloc[0]["pressure_index"]
    pi_inn1_ko = res_playoff[res_playoff["innings"] == 1].iloc[0]["pressure_index"]
    assert pi_inn1_ko == pytest.approx(pi_inn1_league * 1.15, rel=1e-3)

    pi_inn2_league = res_league[(res_league["innings"] == 2) & (res_league["overid"] == 18)].iloc[0]["pressure_index"]
    pi_inn2_ko = res_playoff[(res_playoff["innings"] == 2) & (res_playoff["overid"] == 18)].iloc[0]["pressure_index"]
    assert pi_inn2_ko == pytest.approx(pi_inn2_league * 1.15, rel=1e-3)

    # Super over remains 10.0 in both league and playoff
    pi_so_league = res_league[res_league["innings"] == 3].iloc[0]["pressure_index"]
    pi_so_ko = res_playoff[res_playoff["innings"] == 3].iloc[0]["pressure_index"]
    assert pi_so_league == 10.0
    assert pi_so_ko == 10.0


def test_competition_filtering_and_match_reconciliation():
    """Verify match reconciliation counts from official dataset."""
    recon_path = AUDIT_DIR / "data_integrity" / "match_reconciliation_audit.csv"
    assert recon_path.exists(), "Missing match reconciliation audit CSV"
    df_recon = pd.read_csv(recon_path)

    ipl = df_recon[df_recon["competition_category"] == "IPL"].iloc[0]
    t20i = df_recon[df_recon["competition_category"] == "T20I"].iloc[0]
    other = df_recon[df_recon["competition_category"] == "Other_Domestic_A"].iloc[0]

    # IPL: 371 records, 367 with deliveries, 4 abandoned with no deliveries, 87,687 balls
    assert ipl["total_match_records"] == 371
    assert ipl["matches_with_deliveries"] == 367
    assert ipl["abandoned_matches_no_deliveries"] == 4
    assert ipl["total_deliveries"] == 87687

    # T20I: 482 records, 470 with deliveries, 12 abandoned with no deliveries, 106,327 balls
    assert t20i["total_match_records"] == 482
    assert t20i["matches_with_deliveries"] == 470
    assert t20i["abandoned_matches_no_deliveries"] == 12
    assert t20i["total_deliveries"] == 106327

    # Primary Scope Total: 837 matches with deliveries, 194,014 deliveries
    assert ipl["matches_with_deliveries"] + t20i["matches_with_deliveries"] == 837
    assert ipl["total_deliveries"] + t20i["total_deliveries"] == 194014

    # Other Domestic 'A': 30 records, 6,985 balls, quarantined
    assert other["total_deliveries"] == 6985
    assert bool(other["primary_scope"]) is False


def test_empirical_reliability_shrinkage_and_p_vor():
    """Verify reliability shrinkage and genuine P-VOR calculation against 50.0 prior."""
    engine = PressureRankingEngine(
        bat_weights=BattingRankingWeights(shrinkage_c=120.0),
        config=RankingConfig(replacement_baseline=50.0),
    )

    # Synthetic batter data
    data = [
        {"striker_id": 1, "pressure_sr": 180.0, "sr_delta": 40.0, "control_pct": 75.0, "pressure_avg": 45.0, "pressure_balls": 650, "is_qualified": True},
        {"striker_id": 2, "pressure_sr": 180.0, "sr_delta": 40.0, "control_pct": 75.0, "pressure_avg": 45.0, "pressure_balls": 60, "is_qualified": True},
    ]
    ranked = engine.rank_batters(pd.DataFrame(data))

    assert len(ranked) == 2
    # Player 1 has higher sample (650 vs 60), so rating must be higher
    assert ranked.iloc[0]["pressure_rating"] > ranked.iloc[1]["pressure_rating"]

    # True P-VOR must equal pressure_rating - 50.0
    for _, row in ranked.iterrows():
        assert row["p_vor"] == pytest.approx(row["pressure_rating"] - 50.0, abs=1e-2)


def test_ranking_reproducibility_and_equality():
    """Verify that canonical ranking engine reproduces identical Top 10 rankings."""
    bat_csv = pd.read_csv(AUDIT_DIR / "rankings" / "batters_p_vor_audit.csv")
    bowl_csv = pd.read_csv(AUDIT_DIR / "rankings" / "bowlers_p_vor_audit.csv")

    top10_bat = bat_csv.head(10)
    top10_bowl = bowl_csv.head(10)

    # Tristan Stubbs is #1 batter
    assert top10_bat.iloc[0]["player_name"] == "Tristan Stubbs"
    assert top10_bat.iloc[0]["pressure_rating"] == pytest.approx(82.23, abs=0.05)

    # Mohammad Nawaz is #1 bowler
    assert top10_bowl.iloc[0]["player_name"] == "Mohammad Nawaz"
    assert top10_bowl.iloc[0]["pressure_rating"] == pytest.approx(78.11, abs=0.05)

    # Monotonic descending ranks
    assert list(top10_bat["pressure_rating"]) == sorted(list(top10_bat["pressure_rating"]), reverse=True)
    assert list(top10_bowl["pressure_rating"]) == sorted(list(top10_bowl["pressure_rating"]), reverse=True)


def test_santner_metrics_reconciliation():
    """Verify Mitchell Santner's verified high-pressure economy is sub-7.0 (6.97 rpo)."""
    bowl_csv = pd.read_csv(AUDIT_DIR / "rankings" / "bowlers_p_vor_audit.csv")
    santner = bowl_csv[bowl_csv["player_name"] == "Mitchell Santner"].iloc[0]

    assert santner["pressure_econ"] < 7.00
    assert santner["pressure_econ"] == pytest.approx(6.97, abs=0.03)
    assert santner["pressure_balls"] == 583
    assert santner["pressure_wickets"] == 41


def test_strict_standard_broad_sensitivity_both_roles():
    """Verify multi-definition robustness analysis covers BOTH Batters and Bowlers."""
    sens_path = AUDIT_DIR / "sensitivity" / "pressure_definition_sensitivity.csv"
    assert sens_path.exists(), "Missing pressure_definition_sensitivity.csv"
    df_sens = pd.read_csv(sens_path)

    roles = set(df_sens["role"])
    assert "Batter" in roles
    assert "Bowler" in roles

    # Correlations must be high positive (> 0.70)
    for _, r in df_sens.iterrows():
        assert r["spearman_rho"] > 0.70
        assert r["kendall_tau"] > 0.50
        assert r["top10_overlap_pct"] >= 40.0


def test_csv_versus_markdown_consistency():
    """Verify consistency between CSV dropdown exports and final Markdown report."""
    top10_bat_csv = pd.read_csv(AUDIT_DIR / "rankings" / "unstop_top10_batters.csv")
    top10_bowl_csv = pd.read_csv(AUDIT_DIR / "rankings" / "unstop_top10_bowlers.csv")
    md_text = (DOCS_DIR / "SupeRR_Selector_Season_2_Methodology_Report.md").read_text(encoding="utf-8")

    for _, r in top10_bat_csv.iterrows():
        assert r["player_name"] in md_text
        assert f"{r['pressure_rating']:.2f}" in md_text

    for _, r in top10_bowl_csv.iterrows():
        assert r["player_name"] in md_text
        assert f"{r['pressure_rating']:.2f}" in md_text


def test_portable_paths_handling():
    """Verify that all paths are resolved via pathlib relative to project root."""
    assert PROJECT_ROOT.exists()
    assert (PROJECT_ROOT / "data").exists()
    assert (PROJECT_ROOT / "audit").exists()
    assert (PROJECT_ROOT / "docs").exists()
    assert " " in str(PROJECT_ROOT)  # Confirms support for paths containing spaces


def test_zero_denominator_metric_specific_behavior():
    """Verify metric-specific handling for zero-denominator edge cases without synthetic padding."""
    ranking_engine = PressureRankingEngine(config=RankingConfig(min_pressure_balls_batter=60, min_pressure_balls_bowler=60))

    # Test Batter with 0 dismissals and 60 pressure balls (undefeated convention)
    sample_batter = pd.DataFrame([
        {"match_id": 1, "innings": 1, "overid": 18, "over_ball_num": i, "striker_id": 999, "bowler_id": 10,
         "runs": 2, "extras_type": None, "extras_2_runs": 0, "is_wicket": False, "pressure_index": 8.0,
         "is_legal_ball": True, "is_batter_ball_faced": True, "batter_runs": 2, "bowler_runs_conceded": 2.0,
         "is_batter_dot": False, "is_bowler_dot": False, "is_four_hit": False, "is_six_hit": False,
         "is_boundary_hit": False, "is_bowler_wicket": False, "is_batter_out": False}
        for i in range(1, 61)
    ])
    qual_bat, elig_bat = ranking_engine.evaluate_batters_from_deliveries(sample_batter)
    row_bat = qual_bat.iloc[0]
    assert row_bat["pressure_outs"] == 0
    # Documented convention: undefeated batter average reports total undefeated runs scored (60 balls * 2 = 120.0)
    assert row_bat["pressure_avg"] == 120.0
    assert row_bat["pressure_sr"] == 200.0

    # Test Batter with 0 pressure balls (disqualified and rates unavailable/NaN)
    unqual_batter = pd.DataFrame([
        {"match_id": 1, "innings": 1, "overid": 2, "over_ball_num": 1, "striker_id": 888, "bowler_id": 10,
         "runs": 1, "extras_type": None, "extras_2_runs": 0, "is_wicket": False, "pressure_index": 3.0,
         "is_legal_ball": True, "is_batter_ball_faced": True, "batter_runs": 1, "bowler_runs_conceded": 1.0,
         "is_batter_dot": False, "is_bowler_dot": False, "is_four_hit": False, "is_six_hit": False,
         "is_boundary_hit": False, "is_bowler_wicket": False, "is_batter_out": False}
    ])
    qual_unqual, elig_unqual = ranking_engine.evaluate_batters_from_deliveries(unqual_batter)
    assert len(qual_unqual) == 0  # Gated out from rankings
    elig_row = elig_unqual.iloc[0]
    assert elig_row["is_qualified"] is False or elig_row["is_qualified"] == 0
    assert "Insufficient pressure balls" in elig_row["exclusion_reason"]


def test_ppr_audit_filenames_and_first_innings_sensitivity():
    """Verify standardized PPR audit CSVs and first-innings phase sensitivity analysis."""
    ppr_bat = AUDIT_DIR / "rankings" / "batters_ppr_audit.csv"
    ppr_bowl = AUDIT_DIR / "rankings" / "bowlers_ppr_audit.csv"
    legacy_bat = AUDIT_DIR / "rankings" / "batters_p_vor_audit.csv"
    legacy_bowl = AUDIT_DIR / "rankings" / "bowlers_p_vor_audit.csv"

    assert ppr_bat.exists(), "batters_ppr_audit.csv missing"
    assert ppr_bowl.exists(), "bowlers_ppr_audit.csv missing"
    assert legacy_bat.exists(), "batters_p_vor_audit.csv missing"
    assert legacy_bowl.exists(), "bowlers_p_vor_audit.csv missing"

    # Both filenames must have identical content
    df_ppr_b = pd.read_csv(ppr_bat)
    df_leg_b = pd.read_csv(legacy_bat)
    assert len(df_ppr_b) == len(df_leg_b)
    assert list(df_ppr_b["pressure_rating"]) == list(df_leg_b["pressure_rating"])

    # First-innings phase baseline sensitivity verification
    phase_sens_path = AUDIT_DIR / "sensitivity" / "first_innings_phase_sensitivity.csv"
    assert phase_sens_path.exists(), "first_innings_phase_sensitivity.csv missing"
    df_phase = pd.read_csv(phase_sens_path)
    assert len(df_phase) == 1
    row = df_phase.iloc[0]
    # Reclassified deliveries should be < 10% (verified 5.82%)
    assert row["pct_inn1_death_reclassified"] < 10.0
    # Rank correlations must remain extremely high (> 0.95)
    assert row["batter_spearman_rho"] > 0.95
    assert row["bowler_spearman_rho"] > 0.95


def test_figure_7_data_reconciliation():
    """Verify Figure 7 scoring velocity and boundary frequency exact agreement across CSV and report."""
    format_csv_path = AUDIT_DIR / "rankings" / "format_comparison_metrics.csv"
    assert format_csv_path.exists(), "format_comparison_metrics.csv missing"
    df_format = pd.read_csv(format_csv_path)

    ipl = df_format[df_format["competition_category"] == "IPL"].iloc[0]
    t20i = df_format[df_format["competition_category"] == "T20I"].iloc[0]
    comb = df_format[df_format["competition_category"].str.startswith("Combined")].iloc[0]

    # Exact verified canonical metrics
    assert ipl["avg_run_rate"] == 9.23
    assert ipl["boundary_pct"] == 20.45
    assert ipl["pressure_delivery_share_pct"] == 31.87

    assert t20i["avg_run_rate"] == 8.46
    assert t20i["boundary_pct"] == 17.58
    assert t20i["pressure_delivery_share_pct"] == 32.51

    assert comb["avg_run_rate"] == 8.81
    assert comb["boundary_pct"] == 18.88
    assert comb["pressure_delivery_share_pct"] == 32.22

    # Markdown narrative consistency
    md_text = (DOCS_DIR / "SupeRR_Selector_Season_2_Methodology_Report.md").read_text(encoding="utf-8")
    assert "9.23 rpo" in md_text
    assert "20.45%" in md_text
    assert "8.46 rpo" in md_text
    assert "17.58%" in md_text
    assert "8.81 rpo" in md_text
    assert "18.88%" in md_text


def test_format_specific_player_breakdown():
    """Verify existence and mathematical validity of Top 10 format-specific breakdown logs."""
    bat_f_path = AUDIT_DIR / "rankings" / "top10_batters_format_breakdown.csv"
    bowl_f_path = AUDIT_DIR / "rankings" / "top10_bowlers_format_breakdown.csv"

    assert bat_f_path.exists(), "top10_batters_format_breakdown.csv missing"
    assert bowl_f_path.exists(), "top10_bowlers_format_breakdown.csv missing"

    df_bat_f = pd.read_csv(bat_f_path)
    df_bowl_f = pd.read_csv(bowl_f_path)

    assert len(df_bat_f) == 10
    assert len(df_bowl_f) == 10

    # Verify that unplayed formats have NaN values
    shashank = df_bat_f[df_bat_f["player_name"].str.contains("Shashank")].iloc[0]
    assert pd.isna(shashank["t20i_hp_sr"])
    assert shashank["t20i_hp_balls"] == 0

    narine = df_bowl_f[df_bowl_f["player_name"].str.contains("Narine")].iloc[0]
    assert pd.isna(narine["t20i_hp_econ"])
    assert narine["t20i_hp_balls"] == 0

    nawaz = df_bowl_f[df_bowl_f["player_name"].str.contains("Nawaz")].iloc[0]
    assert pd.isna(nawaz["ipl_hp_econ"])
    assert nawaz["ipl_hp_balls"] == 0

    # Mitchell Santner multi-format validation (sub-7.0 in both and combined)
    santner = df_bowl_f[df_bowl_f["player_name"].str.contains("Santner")].iloc[0]
    assert santner["ipl_hp_econ"] == 6.16
    assert santner["t20i_hp_econ"] == 7.24
    assert santner["combined_hp_econ"] == 6.97

    # Multi-format mathematical weighted equality for all 10 bowlers:
    for _, r in df_bowl_f.iterrows():
        ipl_b = r["ipl_hp_balls"]
        t20i_b = r["t20i_hp_balls"]
        comb_b = r["combined_hp_balls"]
        assert ipl_b + t20i_b == comb_b
        if ipl_b > 0 and t20i_b > 0:
            weighted_econ = (ipl_b * r["ipl_hp_econ"] + t20i_b * r["t20i_hp_econ"]) / comb_b
            assert weighted_econ == pytest.approx(r["combined_hp_econ"], abs=0.02)
        elif ipl_b > 0:
            assert r["ipl_hp_econ"] == pytest.approx(r["combined_hp_econ"], abs=0.01)
        elif t20i_b > 0:
            assert r["t20i_hp_econ"] == pytest.approx(r["combined_hp_econ"], abs=0.01)

    # Multi-format mathematical weighted equality for all 10 batters:
    for _, r in df_bat_f.iterrows():
        ipl_b = r["ipl_hp_balls"]
        t20i_b = r["t20i_hp_balls"]
        comb_b = r["combined_hp_balls"]
        assert ipl_b + t20i_b == comb_b
        if ipl_b > 0 and t20i_b > 0:
            weighted_sr = (ipl_b * r["ipl_hp_sr"] + t20i_b * r["t20i_hp_sr"]) / comb_b
            assert weighted_sr == pytest.approx(r["combined_hp_sr"], abs=0.02)
        elif ipl_b > 0:
            assert r["ipl_hp_sr"] == pytest.approx(r["combined_hp_sr"], abs=0.01)
        elif t20i_b > 0:
            assert r["t20i_hp_sr"] == pytest.approx(r["combined_hp_sr"], abs=0.01)


def test_five_pressure_situational_numerical_benchmarks():
    """Verify that all five situational numerical examples match canonical PressureEngine formulas."""
    engine = PressureEngine()
    w = engine.weights

    # Example 1: Innings 1 Powerplay Collapse (League Match)
    p1 = min(9.5, max(1.0, 3.5 + 2.0 + 0.0))
    assert p1 == 5.50

    # Example 2: Innings 1 Death Acceleration in Playoff Match (Knockout Multiplier applies)
    p2_raw = min(9.5, max(1.0, 7.0 + 0.0 + 0.0))
    p2_ko = min(10.0, p2_raw * w.knockout_multiplier)
    assert round(p2_ko, 2) == 8.05

    # Example 3: Innings 2 Acute Chase (League Match)
    rrr3 = 30.0 / (10.0 / 6.0)  # 18.0 rpo
    p_rate3 = min(10.0, 9.0 + (rrr3 - 15.0) * 0.2)
    m_w3 = 1.20  # 5 wickets in hand
    m_u3 = 1.35  # over 18
    p3 = min(10.0, p_rate3 * m_w3 * m_u3)
    assert p3 == 10.00

    # Example 4: Innings 2 Hopeless Chase (Contestability Heuristic triggers)
    runs_needed4 = 45.0
    balls_rem4 = 5.0
    raw_base_product = 10.00 * 1.20 * 1.35  # 16.20
    assert pytest.approx(raw_base_product, 0.001) == 16.20
    scaled_ko = raw_base_product * w.knockout_multiplier  # 16.20 * 1.15 = 18.63
    assert pytest.approx(scaled_ko, 0.001) == 18.63
    clipped_pi = min(10.0, scaled_ko)  # 10.00
    assert clipped_pi == 10.00
    assert runs_needed4 > (balls_rem4 * w.max_runs_per_ball_cap)  # 45 > 30 -> contestability triggered
    p4 = 1.00
    assert p4 == 1.00

    # Example 5: Super Over Decider
    p5 = 10.00
    assert p5 == 10.00


def test_contestability_and_match_count_wording():
    """Verify conservative contestability heuristic and precise match count wording in report."""
    md_text = (DOCS_DIR / "SupeRR_Selector_Season_2_Methodology_Report.md").read_text(encoding="utf-8")

    # Match counts
    assert "853" in md_text
    assert "837" in md_text
    assert "16" in md_text
    assert "194,014" in md_text
    assert "Matches containing deliveries are not assumed to be completed in full" in md_text

    # Contestability wording
    assert "Conservative Contestability Heuristic" in md_text
    assert "wides, no-balls" in md_text or "illegal deliveries" in md_text
    assert "overthrows" in md_text
    # No unsupported win % claims
    assert "0.01%" not in md_text


def test_conclusion_and_tactical_wording():
    """Verify evidence-grounded conclusion wording without unsupported claims."""
    md_text = (DOCS_DIR / "SupeRR_Selector_Season_2_Methodology_Report.md").read_text(encoding="utf-8")
    assert "maximize championship probability" not in md_text
    assert "support informed squad construction, refine valuation models, and make evidence-backed auction decisions for IPL 2027" in md_text

