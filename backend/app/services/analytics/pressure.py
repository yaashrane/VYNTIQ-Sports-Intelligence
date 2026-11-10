"""Pressure Modeling Engine for T20 Cricket.

Formulates context-aware delivery-by-delivery pressure indices (0.5 to 10.0)
incorporating chase targets, required run rates, wickets in hand, balls remaining,
innings phase demands, collapse states, and tournament elimination stakes.
"""

from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd


class PressureTier(str, Enum):
    """Categorical pressure tiers for contextual analysis."""

    HIGH_PRESSURE = "HIGH_PRESSURE"      # PI >= 6.5: High-leverage, clutch moments
    MEDIUM_PRESSURE = "MEDIUM_PRESSURE"  # 4.0 <= PI < 6.5: Contested match play
    LOW_PRESSURE = "LOW_PRESSURE"        # PI < 4.0: Comfortable, low-leverage play


@dataclass
class PressureWeights:
    """Configurable weights for the pressure index formula."""

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

    # Knockout match escalation
    knockout_multiplier: float = 1.15

    # High pressure threshold
    high_pressure_cutoff: float = 6.5
    medium_pressure_cutoff: float = 4.0


class PressureEngine:
    """Computes exact delivery-level pressure indices across T20 match archives."""

    def __init__(self, weights: PressureWeights | None = None) -> None:
        self.weights = weights or PressureWeights()

    def augment_deliveries_with_pressure(
        self,
        deliveries_df: pd.DataFrame,
        matches_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Enrich raw ball-by-ball records with cumulative match state and pressure indices."""
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

        # 3. Identify legal balls and total delivery runs
        df["is_legal"] = ~df["extras_type"].isin(["wide", "Overstep"])

        delivery_runs = df["runs"].astype(float).copy()
        wide_m = df["extras_type"] == "wide"
        nb_m = df["extras_type"] == "Overstep"
        bye_m = df["extras_type"].isin(["legbyes", "byes", "other"])
        pen_m = df["extras_type"] == "Penalty"

        ext2 = df["extras_2_runs"].fillna(0).astype(float) if "extras_2_runs" in df.columns else 0.0

        delivery_runs[wide_m] = 1.0 + ext2[wide_m]
        delivery_runs[nb_m] = 1.0 + df.loc[nb_m, "runs"].astype(float) + ext2[nb_m]
        delivery_runs[bye_m] = np.maximum(1.0, ext2[bye_m])
        delivery_runs[pen_m] = 5.0

        df["delivery_total_runs"] = delivery_runs

        # 4. Grouped cumulative state (before the current ball)
        grp = df.groupby(["match_id", "innings"])
        df["prev_runs"] = grp["delivery_total_runs"].cumsum() - df["delivery_total_runs"]
        df["prev_wickets"] = grp["is_wicket"].cumsum() - df["is_wicket"].astype(int)
        df["prev_legal_balls"] = grp["is_legal"].cumsum() - df["is_legal"].astype(int)

        df["balls_remaining"] = (120 - df["prev_legal_balls"]).clip(lower=1)
        df["wickets_in_hand"] = (10 - df["prev_wickets"]).clip(lower=1)
        df["crr"] = df["prev_runs"] / (df["prev_legal_balls"].clip(lower=1) / 6.0)

        # 5. Target calculation for Innings 2
        inn1_totals = (
            df[df["innings"] == 1]
            .groupby("match_id")["delivery_total_runs"]
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
        df["pressure_index"] = 4.0
        w = self.weights

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

        # Nonlinear rate pressure curve
        p_rate = np.where(
            rrr_vals <= w.rrr_comfortable_threshold,
            np.maximum(0.5, rrr_vals / 4.0),
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

        # Garbage time discounts
        balls_rem = df["balls_remaining"].to_numpy(dtype=float)
        runs_need = df["runs_needed"].to_numpy(dtype=float)

        garbage_lost = (balls_rem <= 18) & (rrr_vals > 24.0)
        p_rate = np.where(
            garbage_lost,
            p_rate * np.minimum(1.0, 24.0 / np.maximum(1.0, rrr_vals)),
            p_rate,
        ).astype(float)

        garbage_won = (runs_need <= 5) & (balls_rem >= 30)
        p_rate = np.where(garbage_won, 1.5, p_rate).astype(float)

        # Wickets in hand resource multiplier (DLS resource proxy)
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

        # --- Super Overs (Innings 3 & 4) ---
        super_m = (df["innings"] >= 3).to_numpy()
        df.loc[super_m, "pressure_index"] = 10.0

        # --- Knockout Stakes Multiplier ---
        ko_m = (df["knock_out"] == 1).to_numpy()
        df.loc[ko_m, "pressure_index"] = np.clip(
            df.loc[ko_m, "pressure_index"] * w.knockout_multiplier, 0.5, 10.0
        )

        # 7. Discretize into Tiers
        df["pressure_tier"] = np.where(
            df["pressure_index"] >= w.high_pressure_cutoff,
            PressureTier.HIGH_PRESSURE.value,
            np.where(
                df["pressure_index"] >= w.medium_pressure_cutoff,
                PressureTier.MEDIUM_PRESSURE.value,
                PressureTier.LOW_PRESSURE.value,
            ),
        )

        return df
