"""Player Performance Differential Analytics under High Pressure.

Calculates player baseline vs. high-pressure performance differentials,
adjusting for competition format (IPL vs. T20I) scoring baselines and
evaluating match-by-match reliability.
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class DifferentialConfig:
    """Thresholds and baseline parameters for differential evaluation."""

    min_hp_balls_batter: int = 60      # Configurable minimum pressure balls
    min_total_balls_batter: int = 150  # Minimum total career balls in dataset
    min_hp_balls_bowler: int = 60      # Configurable minimum pressure balls bowled
    min_total_balls_bowler: int = 180  # Minimum total balls bowled in dataset


class PerformanceDifferentialAnalyzer:
    """Evaluates how athletes elevate or decline under high match pressure."""

    def __init__(self, config: DifferentialConfig | None = None) -> None:
        self.config = config or DifferentialConfig()

    def analyze_batters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute batting performance metrics across baseline and high pressure."""
        ball_col = "is_batter_ball_faced" if "is_batter_ball_faced" in df.columns else "runs"
        run_col = "batter_runs" if "batter_runs" in df.columns else "runs"
        wkt_col = "is_batter_out" if "is_batter_out" in df.columns else "is_wicket"

        # 1. Base Aggregation across all balls
        all_grp = df.groupby(["striker_id", "striker_name"])
        base_stats = all_grp.agg(
            total_balls=(ball_col, "sum" if ball_col == "is_batter_ball_faced" else "count"),
            total_runs=(run_col, "sum"),
            total_fours=("is_four", "sum"),
            total_sixes=("is_six", "sum"),
            total_dots=(run_col, lambda r: (r == 0).sum()),
            total_dismissals=(wkt_col, "sum"),
            matches_played=("match_id", "nunique"),
        ).reset_index()

        base_stats["base_sr"] = (base_stats["total_runs"] / base_stats["total_balls"].clip(lower=1)) * 100.0
        base_stats["base_bnd_pct"] = (
            (base_stats["total_fours"] + base_stats["total_sixes"]) / base_stats["total_balls"].clip(lower=1)
        ) * 100.0
        base_stats["base_dot_pct"] = (base_stats["total_dots"] / base_stats["total_balls"].clip(lower=1)) * 100.0

        # 2. High Pressure Aggregation (PI >= 6.5)
        hp_df = df[df["pressure_tier"].isin(["HIGH_PRESSURE", "EXTREME_PRESSURE"])]
        hp_grp = hp_df.groupby(["striker_id", "striker_name"])
        hp_stats = hp_grp.agg(
            hp_balls=(ball_col, "sum" if ball_col == "is_batter_ball_faced" else "count"),
            hp_runs=(run_col, "sum"),
            hp_fours=("is_four", "sum"),
            hp_sixes=("is_six", "sum"),
            hp_dots=(run_col, lambda r: (r == 0).sum()),
            hp_dismissals=(wkt_col, "sum"),
            hp_innings=("match_id", "nunique"),
        ).reset_index()

        hp_stats["hp_sr"] = (hp_stats["hp_runs"] / hp_stats["hp_balls"].clip(lower=1)) * 100.0
        hp_stats["hp_bnd_pct"] = (
            (hp_stats["hp_fours"] + hp_stats["hp_sixes"]) / hp_stats["hp_balls"].clip(lower=1)
        ) * 100.0
        hp_stats["hp_dot_pct"] = (hp_stats["hp_dots"] / hp_stats["hp_balls"].clip(lower=1)) * 100.0
        hp_stats["hp_avg"] = hp_stats["hp_runs"] / hp_stats["hp_dismissals"].replace(0, np.nan)

        # 3. Merge and compute Differentials
        merged = pd.merge(base_stats, hp_stats, on=["striker_id", "striker_name"], how="inner")

        # Differentials
        merged["delta_sr"] = merged["hp_sr"] - merged["base_sr"]
        merged["delta_bnd_pct"] = merged["hp_bnd_pct"] - merged["base_bnd_pct"]
        merged["delta_dot_pct"] = merged["base_dot_pct"] - merged["hp_dot_pct"]

        # Qualification Flag
        cfg = self.config
        merged["is_qualified"] = (merged["hp_balls"] >= cfg.min_hp_balls_batter) & (
            merged["total_balls"] >= cfg.min_total_balls_batter
        )
        merged["hp_runs_per_inn"] = merged["hp_runs"] / merged["hp_innings"].clip(lower=1)

        return merged.sort_values("hp_balls", ascending=False).reset_index(drop=True)

    def analyze_bowlers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute bowling performance metrics across baseline and high pressure."""
        legal_col = "is_legal_ball" if "is_legal_ball" in df.columns else "is_legal"
        runs_conc_col = "bowler_runs_conceded" if "bowler_runs_conceded" in df.columns else "delivery_total_runs"
        wkt_col = "is_bowler_wicket" if "is_bowler_wicket" in df.columns else "is_wicket"

        # 1. Base Aggregation across all legal balls
        all_grp = df.groupby(["bowler_id", "bowler_name"])
        base_stats = all_grp.agg(
            total_legal_balls=(legal_col, "sum"),
            total_runs_conceded=(runs_conc_col, "sum"),
            total_wickets=(wkt_col, "sum"),
            total_dots=(runs_conc_col, lambda r: (r == 0).sum()),
            total_boundaries=("runs", lambda r: (r >= 4).sum()),
            matches_played=("match_id", "nunique"),
        ).reset_index()

        base_stats["base_econ"] = base_stats["total_runs_conceded"] / (
            base_stats["total_legal_balls"].clip(lower=1) / 6.0
        )
        base_stats["base_wkt_sr"] = base_stats["total_legal_balls"] / base_stats[
            "total_wickets"
        ].replace(0, np.nan)
        base_stats["base_dot_pct"] = (
            base_stats["total_dots"] / base_stats["total_legal_balls"].clip(lower=1)
        ) * 100.0
        base_stats["base_bnd_conc_pct"] = (
            base_stats["total_boundaries"] / base_stats["total_legal_balls"].clip(lower=1)
        ) * 100.0

        # 2. High Pressure Aggregation (PI >= 6.5)
        hp_df = df[df["pressure_tier"].isin(["HIGH_PRESSURE", "EXTREME_PRESSURE"])]
        hp_grp = hp_df.groupby(["bowler_id", "bowler_name"])
        hp_stats = hp_grp.agg(
            hp_legal_balls=(legal_col, "sum"),
            hp_runs_conceded=(runs_conc_col, "sum"),
            hp_wickets=(wkt_col, "sum"),
            hp_dots=(runs_conc_col, lambda r: (r == 0).sum()),
            hp_boundaries=("runs", lambda r: (r >= 4).sum()),
            hp_matches=("match_id", "nunique"),
        ).reset_index()

        hp_stats["hp_econ"] = hp_stats["hp_runs_conceded"] / (
            hp_stats["hp_legal_balls"].clip(lower=1) / 6.0
        )
        hp_stats["hp_wkt_sr"] = hp_stats["hp_legal_balls"] / hp_stats["hp_wickets"].replace(
            0, np.nan
        )
        hp_stats["hp_dot_pct"] = (
            hp_stats["hp_dots"] / hp_stats["hp_legal_balls"].clip(lower=1)
        ) * 100.0
        hp_stats["hp_bnd_conc_pct"] = (
            hp_stats["hp_boundaries"] / hp_stats["hp_legal_balls"].clip(lower=1)
        ) * 100.0

        # 3. Merge and compute Differentials
        merged = pd.merge(base_stats, hp_stats, on=["bowler_id", "bowler_name"], how="inner")

        # Differentials
        merged["delta_econ"] = merged["base_econ"] - merged["hp_econ"]
        merged["delta_dot_pct"] = merged["hp_dot_pct"] - merged["base_dot_pct"]
        merged["delta_wkt_sr"] = merged["base_wkt_sr"] - merged["hp_wkt_sr"]
        merged["delta_bnd_conc_pct"] = merged["base_bnd_conc_pct"] - merged["hp_bnd_conc_pct"]

        # Qualification Flag
        cfg = self.config
        merged["is_qualified"] = (merged["hp_legal_balls"] >= cfg.min_hp_balls_bowler) & (
            merged["total_legal_balls"] >= cfg.min_total_balls_bowler
        )
        merged["hp_wickets_per_match"] = merged["hp_wickets"] / merged["hp_matches"].clip(lower=1)

        return merged.sort_values("hp_legal_balls", ascending=False).reset_index(drop=True)
