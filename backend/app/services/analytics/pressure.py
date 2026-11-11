"""Canonical Pressure Modeling Engine for T20 Cricket.

Formulates context-aware delivery-by-delivery pressure indices (0.5 to 10.0)
incorporating chase targets, required run rates, wickets in hand, balls remaining,
innings phase demands, collapse states, objective contestability bounds,
and tournament elimination stakes.
"""

from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd


class PressureTier(str, Enum):
    """Categorical pressure tiers for contextual analysis."""

    EXTREME_PRESSURE = "EXTREME_PRESSURE"  # PI >= 8.5: Acute crisis/death finish
    HIGH_PRESSURE = "HIGH_PRESSURE"        # 6.5 <= PI < 8.5: High-leverage, clutch moments
    MODERATE_PRESSURE = "MODERATE_PRESSURE"# 4.0 <= PI < 6.5: Contested match play
    LOW_PRESSURE = "LOW_PRESSURE"          # PI < 4.0: Comfortable, low-leverage play


@dataclass
class PressureWeights:
    """Configurable parameters for the canonical pressure index formula."""

    # Innings 1 phase baseline pressure
    inn1_powerplay_base: float = 3.5
    inn1_middle_base: float = 4.5
    inn1_death_base: float = 7.0

    # Innings 1 collapse bonuses
    collapse_powerplay_bonus: float = 2.0  # >= 2 wickets in overs 1-6
    collapse_middle_bonus: float = 2.5     # >= 3 wickets in overs 1-10 or >= 5 in overs 1-15
    slow_runrate_bonus: float = 1.0        # CRR < 7.0 in overs 8-15

    # Innings 2 RRR anchoring
    rrr_comfortable_threshold: float = 6.0
    rrr_contested_threshold: float = 10.0
    rrr_extreme_threshold: float = 15.0

    # Objective contestability / boundary thresholds
    max_runs_per_ball_cap: float = 6.0     # Mathematically unwinnable if runs needed > 6 * balls remaining
    won_match_max_runs: float = 2.0        # Foregone win if <= 2 runs needed with >= 24 balls remaining
    won_match_min_balls: float = 24.0

    # Knockout match escalation
    knockout_multiplier: float = 1.15

    # Standard Pressure Cutoffs
    extreme_pressure_cutoff: float = 8.5
    high_pressure_cutoff: float = 6.5
    moderate_pressure_cutoff: float = 4.0


class PressureEngine:
    """Canonical engine to enrich delivery-level data with cricket rules and pressure scores."""

    def __init__(self, weights: PressureWeights | None = None) -> None:
        self.weights = weights or PressureWeights()

    def augment_deliveries_with_pressure(
        self,
        deliveries_df: pd.DataFrame,
        matches_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Enrich raw ball-by-ball records with cricket-accounting and pressure indices."""
        df = deliveries_df.copy()

        # 1. Attach Match Metadata if provided
        if matches_df is not None:
            cols_to_merge = ["match_id"]
            for col in ["knock_out", "stage", "revised_target", "venue_country"]:
                if col in matches_df.columns and col not in df.columns:
                    cols_to_merge.append(col)
            if len(cols_to_merge) > 1:
                df = df.merge(matches_df[cols_to_merge], on="match_id", how="left")

        if "knock_out" not in df.columns:
            df["knock_out"] = 0
        df["knock_out"] = df["knock_out"].fillna(0).astype(int)

        # 2. Sort chronologically
        sort_cols = ["match_id", "innings", "overid", "over_ball_num"]
        df = df.sort_values(sort_cols).reset_index(drop=True)

        # 3. Cricket-Correct Extras and Legal Deliveries
        # Legal ball for bowler/over: wides, overstep no-balls, and other no-balls are NOT legal balls
        df["is_legal_ball"] = ~df["extras_type"].isin(["wide", "Overstep", "other"])
        # Retain is_legal alias for backward compatibility
        df["is_legal"] = df["is_legal_ball"]

        # Ball faced by batter: wide is NOT faced; no-balls and byes/leg-byes ARE faced
        df["is_batter_ball_faced"] = df["extras_type"] != "wide"

        # Batter runs: runs off the bat only (0 on wide, legbyes, byes, Penalty)
        df["batter_runs"] = np.where(
            df["extras_type"].isin(["wide", "legbyes", "byes", "Penalty"]), 0, df["runs"]
        )

        # Bowler runs conceded: bat runs + wide penalty (1 + ext2) + no-ball penalty (1 + bat + ext2)
        # Byes, leg-byes, and penalty runs are EXCLUDED from bowler runs conceded
        ext2 = df["extras_2_runs"].fillna(0).astype(float) if "extras_2_runs" in df.columns else pd.Series(0.0, index=df.index)
        bowler_runs = df["batter_runs"].astype(float).copy()
        wide_m = df["extras_type"] == "wide"
        nb_m = df["extras_type"].isin(["Overstep", "other"])

        bowler_runs[wide_m] = 1.0 + ext2[wide_m]
        bowler_runs[nb_m] = 1.0 + df.loc[nb_m, "batter_runs"].astype(float) + ext2[nb_m]
        df["bowler_runs_conceded"] = bowler_runs

        # Team delivery total runs (for match scoring state and target calculations)
        team_runs = df["batter_runs"].astype(float).copy()
        bye_m = df["extras_type"].isin(["legbyes", "byes"])
        pen_m = df["extras_type"] == "Penalty"

        team_runs[wide_m] = 1.0 + ext2[wide_m]
        team_runs[nb_m] = 1.0 + df.loc[nb_m, "batter_runs"].astype(float) + ext2[nb_m]
        team_runs[bye_m] = np.maximum(1.0, ext2[bye_m])
        team_runs[pen_m] = 5.0
        df["team_delivery_runs"] = team_runs
        df["delivery_total_runs"] = team_runs

        # Bowler wickets: only dismissals credited to the bowler
        bowler_wicket_types = ["Caught", "Bowled", "LBW", "Stump", "Hit Wicket"]
        if "dismissal_type" in df.columns:
            df["is_bowler_wicket"] = (df["is_wicket"] == True) & (df["dismissal_type"].isin(bowler_wicket_types))
        else:
            df["is_bowler_wicket"] = df["is_wicket"].astype(bool)

        # Batter dismissals: striker is dismissed
        if "dismissed_player_id" in df.columns and "striker_id" in df.columns:
            df["is_batter_out"] = (df["is_wicket"] == True) & (df["dismissed_player_id"] == df["striker_id"])
        else:
            df["is_batter_out"] = df["is_wicket"].astype(bool)

        # Dot balls
        df["is_batter_dot"] = df["is_batter_ball_faced"] & (df["batter_runs"] == 0)
        df["is_bowler_dot"] = df["is_legal_ball"] & (df["bowler_runs_conceded"] == 0)

        # Boundaries
        df["is_four_hit"] = df["is_four"].fillna(False).astype(bool) if "is_four" in df.columns else (df["runs"] == 4)
        df["is_six_hit"] = df["is_six"].fillna(False).astype(bool) if "is_six" in df.columns else (df["runs"] == 6)
        df["is_boundary_hit"] = df["is_four_hit"] | df["is_six_hit"]

        # 4. Grouped cumulative state (before the current ball)
        grp = df.groupby(["match_id", "innings"])
        df["prev_runs"] = grp["team_delivery_runs"].cumsum() - df["team_delivery_runs"]
        df["prev_wickets"] = grp["is_wicket"].cumsum() - df["is_wicket"].astype(int)
        df["prev_legal_balls"] = grp["is_legal_ball"].cumsum() - df["is_legal_ball"].astype(int)

        df["balls_remaining"] = (120 - df["prev_legal_balls"]).clip(lower=1)
        df["legal_balls_remaining"] = df["balls_remaining"]
        df["wickets_in_hand"] = (10 - df["prev_wickets"]).clip(lower=1)
        df["crr"] = df["prev_runs"] / (df["prev_legal_balls"].clip(lower=1) / 6.0)

        # 5. Target calculation for Innings 2
        inn1_totals = (
            df[df["innings"] == 1]
            .groupby("match_id")["team_delivery_runs"]
            .sum()
            .rename("inn1_total")
        )
        df = df.merge(inn1_totals, on="match_id", how="left")

        if "revised_target" in df.columns:
            df["target"] = df["revised_target"].fillna(df["inn1_total"] + 1)
        else:
            df["target"] = df["inn1_total"] + 1
        df["target"] = df["target"].fillna(160.0).astype(float)
        df["runs_needed"] = (df["target"] - df["prev_runs"]).clip(lower=0).astype(float)
        df["rrr"] = (df["runs_needed"] / (df["balls_remaining"] / 6.0)).astype(float)

        # 6. Pressure Index Calculation
        w = self.weights
        df["pressure_index"] = 4.0

        # --- Innings 1: Target-Setting Pressure ---
        inn1_m = (df["innings"] == 1).to_numpy()
        phase_base = np.where(
            df["overid"] <= 6,
            w.inn1_powerplay_base,
            np.where(df["overid"] <= 15, w.inn1_middle_base, w.inn1_death_base),
        ).astype(float)
        collapse_bonus = np.where(
            (df["overid"] <= 6) & (df["prev_wickets"] >= 2),
            w.collapse_powerplay_bonus,
            np.where(
                (df["overid"] <= 10) & (df["prev_wickets"] >= 3),
                w.collapse_middle_bonus,
                np.where(
                    (df["overid"] <= 15) & (df["prev_wickets"] >= 5),
                    w.collapse_middle_bonus,
                    0.0,
                ),
            ),
        ).astype(float)
        slow_bonus = np.where(
            (df["overid"] >= 8) & (df["overid"] <= 15) & (df["crr"] < 7.0),
            w.slow_runrate_bonus,
            0.0,
        ).astype(float)
        pi_inn1 = np.clip(phase_base + collapse_bonus + slow_bonus, 1.0, 9.5).astype(float)
        df.loc[inn1_m, "pressure_index"] = pi_inn1[inn1_m]

        # --- Innings 2: Chase Pressure ---
        inn2_m = (df["innings"] == 2).to_numpy()
        rrr_vals = df["rrr"].fillna(8.0).to_numpy(dtype=float)

        # Continuous Piecewise Required Run Rate Curve (P_rate):
        # Anchor 1: RRR <= 6.0 -> P_rate = max(0.5, RRR / 3.0). Continuous at RRR=6.0 (value = 2.0)
        # Anchor 2: 6.0 < RRR <= 10.0 -> P_rate = 2.0 + (RRR - 6.0) * 1.0. Continuous at RRR=10.0 (value = 6.0)
        # Anchor 3: 10.0 < RRR <= 15.0 -> P_rate = 6.0 + (RRR - 10.0) * 0.6. Continuous at RRR=15.0 (value = 9.0)
        # Anchor 4: RRR > 15.0 -> P_rate = min(10.0, 9.0 + (RRR - 15.0) * 0.2). Linear increase with an upper cap at 10.0
        p_rate = np.where(
            rrr_vals <= w.rrr_comfortable_threshold,
            np.maximum(0.5, rrr_vals / 3.0),
            np.where(
                rrr_vals <= w.rrr_contested_threshold,
                2.0 + (rrr_vals - w.rrr_comfortable_threshold) * 1.0,
                np.where(
                    rrr_vals <= w.rrr_extreme_threshold,
                    6.0 + (rrr_vals - w.rrr_contested_threshold) * 0.6,
                    np.minimum(10.0, 9.0 + (rrr_vals - w.rrr_extreme_threshold) * 0.2),
                ),
            ),
        ).astype(float)

        # Objective Contestability Filter (uncompetitive garbage time if runs needed > 6 * balls remaining)
        balls_rem = df["balls_remaining"].to_numpy(dtype=float)
        runs_need = df["runs_needed"].to_numpy(dtype=float)
        unwinnable = runs_need > (balls_rem * w.max_runs_per_ball_cap)
        foregone_won = (runs_need <= w.won_match_max_runs) & (balls_rem >= w.won_match_min_balls)

        # Wickets in hand resource multiplier
        w_hand = df["wickets_in_hand"].to_numpy(dtype=float)
        m_wickets = np.where(
            w_hand >= 8,
            0.85,
            np.where(
                w_hand >= 6,
                1.00,
                np.where(
                    w_hand >= 4,
                    1.20,
                    np.where(w_hand >= 2, 1.40, 1.60),
                ),
            ),
        ).astype(float)

        # Phase urgency multiplier
        over_arr = df["overid"].to_numpy(dtype=int)
        m_urgency = np.where(
            over_arr <= 6,
            0.85,
            np.where(
                over_arr <= 15,
                1.00,
                np.where(over_arr <= 17, 1.20, 1.35),
            ),
        ).astype(float)

        pi_inn2 = np.clip(p_rate * m_wickets * m_urgency, 0.5, 10.0).astype(float)
        df.loc[inn2_m, "pressure_index"] = pi_inn2[inn2_m]

        # --- Explicit Knockout Stakes Multiplier ---
        # Scaled in a single stateless pass across active Innings 1 and Innings 2 deliveries.
        ko_m = (df["knock_out"] == 1) & (df["innings"].isin([1, 2]))
        df.loc[ko_m, "pressure_index"] = np.clip(
            df.loc[ko_m, "pressure_index"] * w.knockout_multiplier, 0.5, 10.0
        )

        # Direct contestability / foregone win clamp to lowest baseline (1.0)
        # Applied after knockout scalar so uncompetitive garbage time is strictly 1.0 regardless of tournament stage
        df.loc[inn2_m & (unwinnable | foregone_won), "pressure_index"] = 1.0

        # --- Super Overs (Innings 3 & 4) ---
        # Fixed at terminal maximum leverage (10.0) regardless of knockout scalar
        super_m = (df["innings"] >= 3).to_numpy()
        df.loc[super_m, "pressure_index"] = 10.0

        # 7. Discretize into Tiers
        df["pressure_tier"] = np.where(
            df["pressure_index"] >= w.extreme_pressure_cutoff,
            PressureTier.EXTREME_PRESSURE.value,
            np.where(
                df["pressure_index"] >= w.high_pressure_cutoff,
                PressureTier.HIGH_PRESSURE.value,
                np.where(
                    df["pressure_index"] >= w.moderate_pressure_cutoff,
                    PressureTier.MODERATE_PRESSURE.value,
                    PressureTier.LOW_PRESSURE.value,
                ),
            ),
        )

        return df
