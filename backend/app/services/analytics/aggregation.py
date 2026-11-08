"""Delivery record filtering, boundary preservation, and multidimensional aggregation."""

import pandas as pd
from backend.app.schemas.analytics import (
    DatasetMetricsSummaryResponse,
    MetricCalculationFilter,
)
from backend.app.schemas.metrics import MetricProvenance, SampleSizeInfo
from backend.app.services.analytics.base import (
    CALCULATION_VERSION,
    safe_divide,
)


class DeliveryAggregator:
    """Manages robust filtering and aggregation of delivery events across dimensions."""

    def filter_deliveries(
        self,
        df: pd.DataFrame,
        filters: MetricCalculationFilter | None = None,
    ) -> pd.DataFrame:
        """Apply multidimensional filters while guaranteeing boundary preservation and deduplication."""
        if df.empty:
            return df

        # Deduplication safeguard: Ensure delivery_id or event composite is unique
        if "delivery_id" in df.columns:
            filtered_df = df.drop_duplicates(subset=["delivery_id"]).copy()
        elif all(c in df.columns for c in ["match_id", "innings_num", "over_number", "ball_number"]):
            filtered_df = df.drop_duplicates(
                subset=["match_id", "innings_num", "over_number", "ball_number"]
            ).copy()
        else:
            filtered_df = df.copy()

        if not filters:
            return filtered_df

        # Filter by player_ids (either as batter or bowler)
        if filters.player_ids:
            p_ids = set(filters.player_ids)
            p_mask = pd.Series(False, index=filtered_df.index)
            if "batter_id" in filtered_df.columns:
                p_mask |= filtered_df["batter_id"].isin(p_ids)
            if "bowler_id" in filtered_df.columns:
                p_mask |= filtered_df["bowler_id"].isin(p_ids)
            filtered_df = filtered_df[p_mask]

        # Filter by match_ids
        if filters.match_ids and "match_id" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["match_id"].isin(filters.match_ids)]

        # Filter by seasons
        if filters.seasons and "season" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["season"].isin(filters.seasons)]

        # Filter by phases
        if filters.phases and "phase" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["phase"].isin(filters.phases)]

        # Filter by innings_nums
        if filters.innings_nums and "innings_num" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["innings_num"].isin(filters.innings_nums)]

        return filtered_df

    def compute_player_sample_size(
        self,
        player_id: str,
        df: pd.DataFrame,
    ) -> SampleSizeInfo:
        """Calculate complete sample volume information across batting and bowling."""
        if df.empty:
            return SampleSizeInfo()

        # Batting sample
        b_df = df[df["batter_id"] == player_id] if "batter_id" in df.columns else pd.DataFrame()
        if not b_df.empty:
            balls_faced = len(b_df[b_df["extras_type"] != "WIDE"]) if "extras_type" in b_df.columns else len(b_df)
            batting_innings = int(b_df["match_id"].nunique()) if "match_id" in b_df.columns else 1
            if "is_wicket" in b_df.columns:
                times_dismissed = int(
                    ((b_df["is_wicket"] == True) & (b_df.get("dismissed_player_id", "") == player_id)).sum()  # noqa: E712
                )
            else:
                times_dismissed = 0
        else:
            balls_faced = 0
            batting_innings = 0
            times_dismissed = 0

        # Bowling sample
        bowl_df = df[df["bowler_id"] == player_id] if "bowler_id" in df.columns else pd.DataFrame()
        if not bowl_df.empty:
            if "extras_type" in bowl_df.columns:
                legal_balls = len(bowl_df[~bowl_df["extras_type"].isin(["WIDE", "NO_BALL"])])
            else:
                legal_balls = len(bowl_df)
            overs_bowled = round(legal_balls / 6.0, 2)
            bowling_innings = int(bowl_df["match_id"].nunique()) if "match_id" in bowl_df.columns else 1
        else:
            legal_balls = 0
            overs_bowled = 0.0
            bowling_innings = 0

        # Matches played: total unique matches where player appeared as batter or bowler
        matches = set()
        if not b_df.empty and "match_id" in b_df.columns:
            matches.update(b_df["match_id"].dropna().unique())
        if not bowl_df.empty and "match_id" in bowl_df.columns:
            matches.update(bowl_df["match_id"].dropna().unique())

        return SampleSizeInfo(
            balls_faced=balls_faced,
            batting_innings=batting_innings,
            times_dismissed=times_dismissed,
            legal_balls_bowled=legal_balls,
            overs_bowled=overs_bowled,
            bowling_innings=bowling_innings,
            matches_played=len(matches),
        )

    def compute_dataset_summary(
        self,
        dataset_id: str,
        df: pd.DataFrame,
    ) -> DatasetMetricsSummaryResponse:
        """Produce macro aggregate metrics across an entire ingested dataset."""
        if df.empty:
            return DatasetMetricsSummaryResponse(
                dataset_id=dataset_id,
                total_deliveries=0,
                total_matches=0,
                total_batters=0,
                total_bowlers=0,
                total_runs_scored=0,
                total_wickets_fallen=0,
                overall_run_rate=0.0,
                boundary_percentage_runs=0.0,
                dot_ball_percentage=0.0,
                provenance=MetricProvenance(
                    dataset_id=dataset_id,
                    calculation_version=CALCULATION_VERSION,
                ),
            )

        total_deliveries = len(df)
        total_matches = int(df["match_id"].nunique()) if "match_id" in df.columns else 0
        total_batters = int(df["batter_id"].nunique()) if "batter_id" in df.columns else 0
        total_bowlers = int(df["bowler_id"].nunique()) if "bowler_id" in df.columns else 0

        total_runs = int(df["total_runs"].sum()) if "total_runs" in df.columns else int(df["batter_runs"].sum()) if "batter_runs" in df.columns else 0
        total_wickets = int((df["is_wicket"] == True).sum()) if "is_wicket" in df.columns else 0  # noqa: E712

        # Legal deliveries
        if "extras_type" in df.columns:
            legal_deliveries = len(df[~df["extras_type"].isin(["WIDE", "NO_BALL"])])
        else:
            legal_deliveries = total_deliveries

        # Overall Run Rate: (total_runs / legal_deliveries) * 6.0
        overall_rr, _ = safe_divide(total_runs, legal_deliveries, multiplier=6.0)

        # Boundary runs
        if "batter_runs" in df.columns:
            fours = int((df["batter_runs"] == 4).sum())
            sixes = int((df["batter_runs"] == 6).sum())
            b_runs = (fours * 4) + (sixes * 6)
        else:
            b_runs = 0

        boundary_pct, _ = safe_divide(b_runs, total_runs, multiplier=100.0)

        # Dot balls (0 total runs on delivery)
        if "total_runs" in df.columns:
            dots = int((df["total_runs"] == 0).sum())
        elif "batter_runs" in df.columns and "extras_runs" in df.columns:
            dots = int(((df["batter_runs"] == 0) & (df["extras_runs"] == 0)).sum())
        else:
            dots = 0

        dot_pct, _ = safe_divide(dots, total_deliveries, multiplier=100.0)

        return DatasetMetricsSummaryResponse(
            dataset_id=dataset_id,
            total_deliveries=total_deliveries,
            total_matches=total_matches,
            total_batters=total_batters,
            total_bowlers=total_bowlers,
            total_runs_scored=total_runs,
            total_wickets_fallen=total_wickets,
            overall_run_rate=overall_rr or 0.0,
            boundary_percentage_runs=boundary_pct or 0.0,
            dot_ball_percentage=dot_pct or 0.0,
            provenance=MetricProvenance(
                dataset_id=dataset_id,
                calculation_version=CALCULATION_VERSION,
            ),
        )
