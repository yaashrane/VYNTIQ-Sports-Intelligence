"""Pressure Ranking Engine for T20 Cricket.

Computes multi-dimensional pressure ratings using Empirical Cumulative Distribution
Function (ECDF) percentile normalization and Bayesian reliability shrinkage to determine
the official Top 10 Batters and Top 10 Bowlers under pressure.
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class BattingWeights:
    """Weights for the composite batting pressure rating."""

    weight_hp_strike_rate: float = 0.40
    weight_delta_strike_rate: float = 0.25
    weight_boundary_and_dots: float = 0.20
    weight_hp_average: float = 0.15
    shrinkage_c: float = 120.0  # Bayesian prior workload constant


@dataclass
class BowlingWeights:
    """Weights for the composite bowling pressure rating."""

    weight_hp_economy: float = 0.40
    weight_delta_economy: float = 0.25
    weight_control_and_dots: float = 0.20
    weight_wicket_impact: float = 0.15
    shrinkage_c: float = 150.0  # Bayesian prior workload constant


class PressureRankingEngine:
    """Computes transparent, reproducible candidate rankings under match pressure."""

    def __init__(
        self,
        bat_weights: BattingWeights | None = None,
        bowl_weights: BowlingWeights | None = None,
    ) -> None:
        self.bat_weights = bat_weights or BattingWeights()
        self.bowl_weights = bowl_weights or BowlingWeights()

    @staticmethod
    def _to_ecdf_percentile(series: pd.Series, ascending: bool = True) -> np.ndarray:
        """Convert a continuous metric series into empirical percentile ranks [0, 100]."""
        clean = series.fillna(series.median()).to_numpy(dtype=float)
        ranks = stats.rankdata(clean, method="average")
        if not ascending:
            ranks = len(clean) + 1.0 - ranks
        return (ranks / (len(clean) + 1.0)) * 100.0

    def rank_batters(self, qualified_batters_df: pd.DataFrame) -> pd.DataFrame:
        """Compute Bayesian-shrunken Pressure Ratings for qualified batters."""
        df = qualified_batters_df[qualified_batters_df["is_qualified"]].copy()
        if len(df) == 0:
            return df

        w = self.bat_weights

        # 1. Percentile scaling
        df["pct_hp_sr"] = self._to_ecdf_percentile(df["hp_sr"], ascending=True)
        df["pct_delta_sr"] = self._to_ecdf_percentile(df["delta_sr"], ascending=True)
        df["pct_bnd"] = self._to_ecdf_percentile(df["hp_bnd_pct"], ascending=True)
        df["pct_dot"] = self._to_ecdf_percentile(df["hp_dot_pct"], ascending=False)
        df["pct_control"] = (df["pct_bnd"] + df["pct_dot"]) / 2.0
        df["pct_avg"] = self._to_ecdf_percentile(
            df["hp_avg"].fillna(df["hp_avg"].median()), ascending=True
        )

        # 2. Raw Composite Score
        df["raw_composite_score"] = (
            w.weight_hp_strike_rate * df["pct_hp_sr"]
            + w.weight_delta_strike_rate * df["pct_delta_sr"]
            + w.weight_boundary_and_dots * df["pct_control"]
            + w.weight_hp_average * df["pct_avg"]
        )

        # 3. Bayesian Reliability Shrinkage toward Cohort Median (50.0)
        df["reliability_factor"] = df["hp_balls"] / (df["hp_balls"] + w.shrinkage_c)
        df["final_pressure_rating"] = (
            df["reliability_factor"] * df["raw_composite_score"]
            + (1.0 - df["reliability_factor"]) * 50.0
        )

        ranked = df.sort_values(
            ["final_pressure_rating", "hp_sr", "hp_balls"], ascending=False
        ).reset_index(drop=True)
        ranked["pressure_rank"] = ranked.index + 1
        return ranked

    def rank_bowlers(self, qualified_bowlers_df: pd.DataFrame) -> pd.DataFrame:
        """Compute Bayesian-shrunken Pressure Ratings for qualified bowlers."""
        df = qualified_bowlers_df[qualified_bowlers_df["is_qualified"]].copy()
        if len(df) == 0:
            return df

        w = self.bowl_weights

        # 1. Percentile scaling
        # Economy: lower is better
        df["pct_hp_econ"] = self._to_ecdf_percentile(df["hp_econ"], ascending=False)
        # Delta economy: positive (restriction improvement) is better
        df["pct_delta_econ"] = self._to_ecdf_percentile(df["delta_econ"], ascending=True)
        df["pct_dot"] = self._to_ecdf_percentile(df["hp_dot_pct"], ascending=True)
        df["pct_bnd_conc"] = self._to_ecdf_percentile(df["hp_bnd_conc_pct"], ascending=False)
        df["pct_control"] = (df["pct_dot"] + df["pct_bnd_conc"]) / 2.0

        # Wicket impact: total wickets + strike rate
        df["pct_wickets"] = self._to_ecdf_percentile(df["hp_wickets"], ascending=True)
        df["pct_wkt_sr"] = self._to_ecdf_percentile(
            df["hp_wkt_sr"].fillna(99.0), ascending=False
        )
        df["pct_wicket_impact"] = (df["pct_wickets"] + df["pct_wkt_sr"]) / 2.0

        # 2. Raw Composite Score
        df["raw_composite_score"] = (
            w.weight_hp_economy * df["pct_hp_econ"]
            + w.weight_delta_economy * df["pct_delta_econ"]
            + w.weight_control_and_dots * df["pct_control"]
            + w.weight_wicket_impact * df["pct_wicket_impact"]
        )

        # 3. Bayesian Reliability Shrinkage toward Cohort Median (50.0)
        df["reliability_factor"] = df["hp_legal_balls"] / (df["hp_legal_balls"] + w.shrinkage_c)
        df["final_pressure_rating"] = (
            df["reliability_factor"] * df["raw_composite_score"]
            + (1.0 - df["reliability_factor"]) * 50.0
        )

        ranked = df.sort_values(
            ["final_pressure_rating", "hp_econ", "hp_wickets"], ascending=[False, True, False]
        ).reset_index(drop=True)
        ranked["pressure_rank"] = ranked.index + 1
        return ranked

