"""Canonical Pressure Ranking Engine for T20 Cricket.

Computes multi-dimensional pressure ratings using Empirical Cumulative Distribution
Function (ECDF) percentile normalization, empirical reliability shrinkage,
and Pressure Surplus Rating (PSR) relative to the empirical cohort prior median (50.0).
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class BattingRankingWeights:
    """Weights for the composite batting pressure rating."""

    weight_sr: float = 0.35
    weight_delta_sr: float = 0.25
    weight_control: float = 0.20
    weight_avg: float = 0.20
    shrinkage_c: float = 120.0  # Empirical prior workload constant (balls faced)


@dataclass
class BowlingRankingWeights:
    """Weights for the composite bowling pressure rating."""

    weight_econ: float = 0.35
    weight_delta_econ: float = 0.25
    weight_dot: float = 0.20
    weight_wicket: float = 0.20
    shrinkage_c: float = 150.0  # Empirical prior workload constant (legal balls bowled)


@dataclass
class RankingConfig:
    """Thresholds and baseline settings for ranking execution."""

    min_pressure_balls_batter: int = 60
    min_pressure_balls_bowler: int = 60
    replacement_baseline: float = 50.0  # Empirical cohort prior median
    pressure_threshold: float = 6.5


# Aliases for backward compatibility
BattingWeights = BattingRankingWeights
BowlingWeights = BowlingRankingWeights


class PressureRankingEngine:
    """Canonical ranking engine consumed across backend API, audit pipeline, and reporting."""

    def __init__(
        self,
        bat_weights: BattingRankingWeights | None = None,
        bowl_weights: BowlingRankingWeights | None = None,
        config: RankingConfig | None = None,
    ) -> None:
        self.bat_weights = bat_weights or BattingRankingWeights()
        self.bowl_weights = bowl_weights or BowlingRankingWeights()
        self.config = config or RankingConfig()

    @staticmethod
    def _to_ecdf_percentile(series: pd.Series, ascending: bool = True) -> np.ndarray:
        """Convert a continuous metric series into empirical percentile ranks [0, 100]."""
        clean = series.fillna(series.median()).to_numpy(dtype=float)
        n = len(clean)
        if n == 0:
            return np.array([])
        ranks = stats.rankdata(clean, method="average")
        if not ascending:
            ranks = n + 1.0 - ranks
        return (ranks / (n + 1.0)) * 100.0

    def evaluate_batters_from_deliveries(
        self,
        deliveries_df: pd.DataFrame,
        player_names: dict | None = None,
        threshold_pi: float | None = None,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Aggregate delivery records and compute complete player-level batting ratings."""
        th = threshold_pi if threshold_pi is not None else self.config.pressure_threshold
        df = deliveries_df.copy()
        df["is_pressure"] = df["pressure_index"] >= th

        # Total career in dataset
        tot = df.groupby("striker_id").agg(
            total_balls=("is_batter_ball_faced", "sum"),
            total_runs=("batter_runs", "sum"),
            total_outs=("is_batter_out", "sum"),
        )

        # High Pressure deliveries
        p_df = df[df["is_pressure"]]
        p_stats = p_df.groupby("striker_id").agg(
            pressure_balls=("is_batter_ball_faced", "sum"),
            pressure_runs=("batter_runs", "sum"),
            pressure_outs=("is_batter_out", "sum"),
            pressure_dots=("is_batter_dot", "sum"),
            pressure_fours=("is_four_hit", "sum"),
            pressure_sixes=("is_six_hit", "sum"),
        )

        # Non-Pressure deliveries (normal baseline)
        np_df = df[~df["is_pressure"]]
        np_stats = np_df.groupby("striker_id").agg(
            normal_balls=("is_batter_ball_faced", "sum"),
            normal_runs=("batter_runs", "sum"),
            normal_outs=("is_batter_out", "sum"),
        )

        merged = tot.join(p_stats, how="left").join(np_stats, how="left").fillna(0)
        merged.index.name = "player_id"
        merged = merged.reset_index()

        min_balls = self.config.min_pressure_balls_batter
        merged["is_qualified"] = merged["pressure_balls"] >= min_balls
        merged["exclusion_reason"] = np.where(
            merged["is_qualified"],
            "Qualified",
            "Insufficient pressure balls faced (" + merged["pressure_balls"].astype(str) + f" < {min_balls})",
        )

        eligibility_df = merged[
            ["player_id", "total_balls", "pressure_balls", "is_qualified", "exclusion_reason"]
        ].copy()
        eligibility_df["role"] = "Batter"

        qual = merged[merged["is_qualified"]].copy()
        if qual.empty:
            return qual, eligibility_df

        # Calculated rates with metric-specific zero-denominator handling:
        # Strike rate: unavailable (NaN) when legal balls faced == 0
        qual["pressure_sr"] = np.where(
            qual["pressure_balls"] > 0,
            (qual["pressure_runs"] / qual["pressure_balls"] * 100.0),
            np.nan,
        ).round(2)
        qual["normal_sr"] = np.where(
            qual["normal_balls"] > 0,
            (qual["normal_runs"] / qual["normal_balls"] * 100.0),
            np.nan,
        ).round(2)
        qual["overall_sr"] = np.where(
            qual["total_balls"] > 0,
            (qual["total_runs"] / qual["total_balls"] * 100.0),
            np.nan,
        ).round(2)
        # Delta SR: calculated when both normal and pressure strike rates are available; otherwise neutral 0.0
        qual["sr_delta"] = np.where(
            qual["normal_sr"].notna() & qual["pressure_sr"].notna(),
            (qual["pressure_sr"] - qual["normal_sr"]),
            0.0,
        ).round(2)

        # Batting average: unavailable (NaN) when 0 balls faced.
        # Documented reporting convention: when dismissals == 0 and balls faced > 0, average is reported as undefeated runs scored.
        qual["pressure_avg"] = np.where(
            qual["pressure_balls"] == 0,
            np.nan,
            np.where(
                qual["pressure_outs"] > 0,
                (qual["pressure_runs"] / qual["pressure_outs"]),
                qual["pressure_runs"],  # Documented convention: undefeated runs scored
            ),
        ).round(2)
        qual["dot_pct"] = np.where(
            qual["pressure_balls"] > 0,
            (qual["pressure_dots"] / qual["pressure_balls"] * 100.0),
            np.nan,
        ).round(2)
        qual["boundary_pct"] = np.where(
            qual["pressure_balls"] > 0,
            ((qual["pressure_fours"] + qual["pressure_sixes"]) / qual["pressure_balls"] * 100.0),
            np.nan,
        ).round(2)
        qual["control_pct"] = np.where(
            qual["dot_pct"].notna(),
            (100.0 - qual["dot_pct"]),
            np.nan,
        ).round(2)

        # ECDF Percentiles (0 to 100)
        n_qual = len(qual)
        qual["pct_sr"] = (stats.rankdata(qual["pressure_sr"]) / n_qual * 100.0).round(2)
        qual["pct_delta"] = (stats.rankdata(qual["sr_delta"]) / n_qual * 100.0).round(2)
        qual["pct_control"] = (stats.rankdata(qual["control_pct"]) / n_qual * 100.0).round(2)
        qual["pct_avg"] = (stats.rankdata(qual["pressure_avg"]) / n_qual * 100.0).round(2)

        w = self.bat_weights
        qual["raw_score"] = (
            w.weight_sr * qual["pct_sr"]
            + w.weight_delta_sr * qual["pct_delta"]
            + w.weight_control * qual["pct_control"]
            + w.weight_avg * qual["pct_avg"]
        ).round(2)

        # Empirical Reliability Shrinkage
        qual["reliability"] = (qual["pressure_balls"] / (qual["pressure_balls"] + w.shrinkage_c)).round(4)
        rep_base = self.config.replacement_baseline
        qual["pressure_rating"] = (
            (qual["raw_score"] * qual["reliability"]) + (rep_base * (1.0 - qual["reliability"]))
        ).round(2)

        # Performance Deviation from Prior Median (Pressure Surplus Rating, PSR)
        qual["pressure_surplus"] = (qual["pressure_rating"] - rep_base).round(2)
        # Retained alias for backwards compatibility
        qual["p_vor"] = qual["pressure_surplus"]

        if player_names is not None:
            qual["player_name"] = qual["player_id"].map(player_names)
            eligibility_df["player_name"] = eligibility_df["player_id"].map(player_names)

        # Tie-breaking
        qual = qual.sort_values(
            ["pressure_rating", "pressure_sr", "pressure_balls"], ascending=[False, False, False]
        ).reset_index(drop=True)
        qual["rank"] = qual.index + 1
        # Compatibility aliases
        qual["final_pressure_rating"] = qual["pressure_rating"]
        qual["pressure_rank"] = qual["rank"]
        qual["striker_name"] = qual.get("player_name", qual["player_id"].astype(str))
        qual["hp_balls"] = qual["pressure_balls"]
        qual["hp_sr"] = qual["pressure_sr"]
        qual["base_sr"] = qual["normal_sr"]
        qual["delta_sr"] = qual["sr_delta"]

        return qual, eligibility_df

    def evaluate_bowlers_from_deliveries(
        self,
        deliveries_df: pd.DataFrame,
        player_names: dict | None = None,
        threshold_pi: float | None = None,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Aggregate delivery records and compute complete player-level bowling ratings."""
        th = threshold_pi if threshold_pi is not None else self.config.pressure_threshold
        df = deliveries_df.copy()
        df["is_pressure"] = df["pressure_index"] >= th

        # Total career
        tot = df.groupby("bowler_id").agg(
            total_balls=("is_legal_ball", "sum"),
            total_runs=("bowler_runs_conceded", "sum"),
            total_wickets=("is_bowler_wicket", "sum"),
        )

        p_df = df[df["is_pressure"]]
        p_stats = p_df.groupby("bowler_id").agg(
            pressure_balls=("is_legal_ball", "sum"),
            pressure_runs_conceded=("bowler_runs_conceded", "sum"),
            pressure_wickets=("is_bowler_wicket", "sum"),
            pressure_dots=("is_bowler_dot", "sum"),
            pressure_fours=("is_four_hit", "sum"),
            pressure_sixes=("is_six_hit", "sum"),
        )

        np_df = df[~df["is_pressure"]]
        np_stats = np_df.groupby("bowler_id").agg(
            normal_balls=("is_legal_ball", "sum"),
            normal_runs_conceded=("bowler_runs_conceded", "sum"),
            normal_wickets=("is_bowler_wicket", "sum"),
        )

        merged = tot.join(p_stats, how="left").join(np_stats, how="left").fillna(0)
        merged.index.name = "player_id"
        merged = merged.reset_index()

        min_balls = self.config.min_pressure_balls_bowler
        merged["is_qualified"] = merged["pressure_balls"] >= min_balls
        merged["exclusion_reason"] = np.where(
            merged["is_qualified"],
            "Qualified",
            "Insufficient legal pressure balls bowled ("
            + merged["pressure_balls"].astype(str)
            + f" < {min_balls})",
        )

        eligibility_df = merged[
            ["player_id", "total_balls", "pressure_balls", "is_qualified", "exclusion_reason"]
        ].copy()
        eligibility_df["role"] = "Bowler"

        qual = merged[merged["is_qualified"]].copy()
        if qual.empty:
            return qual, eligibility_df

        # Calculated rates with metric-specific zero-denominator handling:
        # Economy: unavailable (NaN) when legal balls bowled == 0
        qual["pressure_econ"] = np.where(
            qual["pressure_balls"] > 0,
            (qual["pressure_runs_conceded"] / (qual["pressure_balls"] / 6.0)),
            np.nan,
        ).round(2)
        qual["normal_econ"] = np.where(
            qual["normal_balls"] > 0,
            (qual["normal_runs_conceded"] / (qual["normal_balls"] / 6.0)),
            np.nan,
        ).round(2)
        qual["overall_econ"] = np.where(
            qual["total_balls"] > 0,
            (qual["total_runs"] / (qual["total_balls"] / 6.0)),
            np.nan,
        ).round(2)
        # Economy delta: normal_econ - pressure_econ; neutral 0.0 if normal economy unavailable
        qual["econ_delta"] = np.where(
            qual["normal_econ"].notna() & qual["pressure_econ"].notna(),
            (qual["normal_econ"] - qual["pressure_econ"]),
            0.0,
        ).round(2)

        # Dot % and Boundary %: unavailable when legal balls bowled == 0
        qual["dot_pct"] = np.where(
            qual["pressure_balls"] > 0,
            (qual["pressure_dots"] / qual["pressure_balls"] * 100.0),
            np.nan,
        ).round(2)
        qual["boundary_pct"] = np.where(
            qual["pressure_balls"] > 0,
            ((qual["pressure_fours"] + qual["pressure_sixes"]) / qual["pressure_balls"] * 100.0),
            np.nan,
        ).round(2)

        # Wicket rate (wickets per ball): unavailable when legal balls bowled == 0
        qual["wickets_per_ball"] = np.where(
            qual["pressure_balls"] > 0,
            (qual["pressure_wickets"] / qual["pressure_balls"]),
            np.nan,
        ).round(4)
        # Balls per wicket: unavailable when wickets == 0 or balls == 0
        qual["balls_per_wicket"] = np.where(
            (qual["pressure_wickets"] > 0) & (qual["pressure_balls"] > 0),
            (qual["pressure_balls"] / qual["pressure_wickets"]),
            np.nan,
        ).round(2)

        n_qual = len(qual)
        # Inverted economy rank (lower economy is better)
        qual["pct_econ"] = ((n_qual - stats.rankdata(qual["pressure_econ"]) + 1) / n_qual * 100.0).round(2)
        qual["pct_delta"] = (stats.rankdata(qual["econ_delta"]) / n_qual * 100.0).round(2)
        qual["pct_dot"] = (stats.rankdata(qual["dot_pct"]) / n_qual * 100.0).round(2)
        qual["pct_wickets"] = (stats.rankdata(qual["wickets_per_ball"]) / n_qual * 100.0).round(2)

        w = self.bowl_weights
        qual["raw_score"] = (
            w.weight_econ * qual["pct_econ"]
            + w.weight_delta_econ * qual["pct_delta"]
            + w.weight_dot * qual["pct_dot"]
            + w.weight_wicket * qual["pct_wickets"]
        ).round(2)

        qual["reliability"] = (qual["pressure_balls"] / (qual["pressure_balls"] + w.shrinkage_c)).round(4)
        rep_base = self.config.replacement_baseline
        qual["pressure_rating"] = (
            (qual["raw_score"] * qual["reliability"]) + (rep_base * (1.0 - qual["reliability"]))
        ).round(2)

        # Performance Deviation from Prior Median (Pressure Surplus Rating, PSR)
        qual["pressure_surplus"] = (qual["pressure_rating"] - rep_base).round(2)
        # Retained alias for backwards compatibility
        qual["p_vor"] = qual["pressure_surplus"]

        if player_names is not None:
            qual["player_name"] = qual["player_id"].map(player_names)
            eligibility_df["player_name"] = eligibility_df["player_id"].map(player_names)

        # Tie-breaking
        qual = qual.sort_values(
            ["pressure_rating", "pressure_econ", "pressure_wickets"], ascending=[False, True, False]
        ).reset_index(drop=True)
        qual["rank"] = qual.index + 1
        # Compatibility aliases
        qual["final_pressure_rating"] = qual["pressure_rating"]
        qual["pressure_rank"] = qual["rank"]
        qual["bowler_name"] = qual.get("player_name", qual["player_id"].astype(str))
        qual["hp_legal_balls"] = qual["pressure_balls"]
        qual["hp_econ"] = qual["pressure_econ"]
        qual["base_econ"] = qual["normal_econ"]
        qual["delta_econ"] = qual["econ_delta"]
        qual["hp_wickets"] = qual["pressure_wickets"]

        return qual, eligibility_df

    def rank_batters(self, qualified_batters_df: pd.DataFrame) -> pd.DataFrame:
        """Compatibility wrapper for pre-aggregated batter DataFrames."""
        df = qualified_batters_df[qualified_batters_df["is_qualified"]].copy()
        if len(df) == 0:
            return df
        # Normalize columns if needed
        if "pressure_sr" not in df.columns and "hp_sr" in df.columns:
            df["pressure_sr"] = df["hp_sr"]
        if "sr_delta" not in df.columns and "delta_sr" in df.columns:
            df["sr_delta"] = df["delta_sr"]
        if "control_pct" not in df.columns and "hp_dot_pct" in df.columns:
            df["control_pct"] = 100.0 - df["hp_dot_pct"]
        if "pressure_avg" not in df.columns and "hp_avg" in df.columns:
            df["pressure_avg"] = df["hp_avg"].fillna(df["hp_avg"].median())
        if "pressure_balls" not in df.columns and "hp_balls" in df.columns:
            df["pressure_balls"] = df["hp_balls"]

        n_qual = len(df)
        df["pct_sr"] = (stats.rankdata(df["pressure_sr"]) / n_qual * 100.0).round(2)
        df["pct_delta"] = (stats.rankdata(df["sr_delta"]) / n_qual * 100.0).round(2)
        df["pct_control"] = (stats.rankdata(df["control_pct"]) / n_qual * 100.0).round(2)
        df["pct_avg"] = (stats.rankdata(df["pressure_avg"]) / n_qual * 100.0).round(2)

        w = self.bat_weights
        df["raw_composite_score"] = (
            w.weight_sr * df["pct_sr"]
            + w.weight_delta_sr * df["pct_delta"]
            + w.weight_control * df["pct_control"]
            + w.weight_avg * df["pct_avg"]
        ).round(2)

        df["reliability_factor"] = (df["pressure_balls"] / (df["pressure_balls"] + w.shrinkage_c)).round(4)
        rep_base = self.config.replacement_baseline
        df["final_pressure_rating"] = (
            (df["raw_composite_score"] * df["reliability_factor"])
            + (rep_base * (1.0 - df["reliability_factor"]))
        ).round(2)
        df["pressure_surplus"] = (df["final_pressure_rating"] - rep_base).round(2)
        df["p_vor"] = df["pressure_surplus"]
        df["pressure_rating"] = df["final_pressure_rating"]

        ranked = df.sort_values(
            ["final_pressure_rating", "pressure_sr", "pressure_balls"], ascending=False
        ).reset_index(drop=True)
        ranked["pressure_rank"] = ranked.index + 1
        ranked["rank"] = ranked["pressure_rank"]
        return ranked

    def rank_bowlers(self, qualified_bowlers_df: pd.DataFrame) -> pd.DataFrame:
        """Compatibility wrapper for pre-aggregated bowler DataFrames."""
        df = qualified_bowlers_df[qualified_bowlers_df["is_qualified"]].copy()
        if len(df) == 0:
            return df

        if "pressure_econ" not in df.columns and "hp_econ" in df.columns:
            df["pressure_econ"] = df["hp_econ"]
        if "econ_delta" not in df.columns and "delta_econ" in df.columns:
            df["econ_delta"] = df["delta_econ"]
        if "dot_pct" not in df.columns and "hp_dot_pct" in df.columns:
            df["dot_pct"] = df["hp_dot_pct"]
        if "wickets_per_ball" not in df.columns:
            if "hp_wickets" in df.columns and "hp_legal_balls" in df.columns:
                df["wickets_per_ball"] = df["hp_wickets"] / df["hp_legal_balls"].clip(lower=1)
            else:
                df["wickets_per_ball"] = 0.05
        if "pressure_balls" not in df.columns and "hp_legal_balls" in df.columns:
            df["pressure_balls"] = df["hp_legal_balls"]
        if "pressure_wickets" not in df.columns and "hp_wickets" in df.columns:
            df["pressure_wickets"] = df["hp_wickets"]

        n_qual = len(df)
        df["pct_econ"] = ((n_qual - stats.rankdata(df["pressure_econ"]) + 1) / n_qual * 100.0).round(2)
        df["pct_delta"] = (stats.rankdata(df["econ_delta"]) / n_qual * 100.0).round(2)
        df["pct_dot"] = (stats.rankdata(df["dot_pct"]) / n_qual * 100.0).round(2)
        df["pct_wickets"] = (stats.rankdata(df["wickets_per_ball"]) / n_qual * 100.0).round(2)

        w = self.bowl_weights
        df["raw_composite_score"] = (
            w.weight_econ * df["pct_econ"]
            + w.weight_delta_econ * df["pct_delta"]
            + w.weight_dot * df["pct_dot"]
            + w.weight_wicket * df["pct_wickets"]
        ).round(2)

        df["reliability_factor"] = (df["pressure_balls"] / (df["pressure_balls"] + w.shrinkage_c)).round(4)
        rep_base = self.config.replacement_baseline
        df["final_pressure_rating"] = (
            (df["raw_composite_score"] * df["reliability_factor"])
            + (rep_base * (1.0 - df["reliability_factor"]))
        ).round(2)
        df["pressure_surplus"] = (df["final_pressure_rating"] - rep_base).round(2)
        df["p_vor"] = df["pressure_surplus"]
        df["pressure_rating"] = df["final_pressure_rating"]

        ranked = df.sort_values(
            ["final_pressure_rating", "pressure_econ", "pressure_wickets"],
            ascending=[False, True, False],
        ).reset_index(drop=True)
        ranked["pressure_rank"] = ranked.index + 1
        ranked["rank"] = ranked["pressure_rank"]
        return ranked
