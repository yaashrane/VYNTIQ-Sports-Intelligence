"""Vectorized bowling performance metric calculations."""

from typing import Any
import pandas as pd
from backend.app.schemas.metrics import MetricDirection, MetricStatus, MetricValue
from backend.app.services.analytics.base import (
    BOWLER_CREDITED_DISMISSALS,
    STANDARD_PHASES,
    create_metric_value,
    safe_divide,
)


class BowlingMetricsCalculator:
    """Computes comprehensive bowling rate statistics, wicket metrics, and phase splits."""

    def calculate_metrics(
        self,
        player_id: str,
        df: pd.DataFrame,
    ) -> dict[str, MetricValue]:
        """Calculate all standard bowling metrics for a bowler from delivery records."""
        b_df = df[df["bowler_id"] == player_id] if not df.empty and "bowler_id" in df.columns else pd.DataFrame()

        if b_df.empty:
            return self._empty_bowling_metrics()

        # 1. Legal Deliveries Bowled: Excludes Wides and No-Balls
        if "extras_type" in b_df.columns:
            # Check either is_legal flag or extras_type
            legal_mask = ~b_df["extras_type"].isin(["WIDE", "NO_BALL"])
            legal_df = b_df[legal_mask]
        elif "is_legal" in b_df.columns:
            legal_df = b_df[b_df["is_legal"] == True]  # noqa: E712
        else:
            legal_df = b_df

        legal_balls = len(legal_df)
        overs_bowled = round(legal_balls / 6.0, 2)

        # 2. Runs Conceded:
        # Batter runs + Bowler-chargeable extras (Wides and No-Balls).
        # Byes and leg-byes are EXCLUDED from bowler runs conceded.
        batter_runs = int(b_df["batter_runs"].sum()) if "batter_runs" in b_df.columns else 0
        if "extras_type" in b_df.columns and "extras_runs" in b_df.columns:
            bowler_extras_mask = b_df["extras_type"].isin(["WIDE", "NO_BALL"])
            bowler_extras = int(b_df.loc[bowler_extras_mask, "extras_runs"].sum())
        else:
            bowler_extras = 0
        runs_conceded = batter_runs + bowler_extras

        # 3. Wickets Taken (Bowler-Credited):
        # Bowled, Caught, LBW, Stumped, Hit Wicket, Caught and Bowled.
        # Excludes Run Outs, Retired Out/Hurt, Obstructing, Timed Out.
        wickets_taken = self._count_bowler_wickets(b_df)

        # 4. Dot balls conceded:
        # Legal deliveries with 0 batter runs and 0 extras runs conceded
        if "batter_runs" in legal_df.columns and "extras_runs" in legal_df.columns:
            dot_mask = (legal_df["batter_runs"] == 0) & (legal_df["extras_runs"] == 0)
            dot_balls = int(dot_mask.sum())
        elif "batter_runs" in legal_df.columns:
            dot_balls = int((legal_df["batter_runs"] == 0).sum())
        else:
            dot_balls = 0

        # 5. Boundaries Conceded: Fours and Sixes scored off the bat
        if "batter_runs" in b_df.columns:
            fours_conceded = int((b_df["batter_runs"] == 4).sum())
            sixes_conceded = int((b_df["batter_runs"] == 6).sum())
        else:
            fours_conceded = 0
            sixes_conceded = 0
        boundaries_conceded = fours_conceded + sixes_conceded

        metrics: dict[str, MetricValue] = {}

        # 1. Wickets Taken
        metrics["wickets_taken"] = create_metric_value(
            metric_id="wickets_taken",
            display_name="Bowler Wickets",
            value=wickets_taken,
            status=MetricStatus.CALCULATED,
            sample_size=legal_balls,
            sample_units="balls",
            directionality=MetricDirection.HIGHER_IS_BETTER,
        )

        # 2. Legal Balls Bowled
        metrics["legal_balls_bowled"] = create_metric_value(
            metric_id="legal_balls_bowled",
            display_name="Legal Balls Bowled",
            value=legal_balls,
            status=MetricStatus.CALCULATED,
            sample_size=legal_balls,
            sample_units="balls",
            directionality=MetricDirection.NEUTRAL,
        )

        # 3. Overs Bowled
        metrics["overs_bowled"] = create_metric_value(
            metric_id="overs_bowled",
            display_name="Overs Bowled",
            value=overs_bowled,
            status=MetricStatus.CALCULATED,
            sample_size=legal_balls,
            sample_units="balls",
            directionality=MetricDirection.NEUTRAL,
        )

        # 4. Runs Conceded
        metrics["runs_conceded"] = create_metric_value(
            metric_id="runs_conceded",
            display_name="Runs Conceded",
            value=runs_conceded,
            status=MetricStatus.CALCULATED,
            sample_size=legal_balls,
            sample_units="balls",
            directionality=MetricDirection.LOWER_IS_BETTER,
            context={"batter_runs": batter_runs, "bowler_extras": bowler_extras},
        )

        # 5. Economy Rate: (runs_conceded / legal_balls) * 6.0
        econ_val, econ_status = safe_divide(runs_conceded, legal_balls, multiplier=6.0)
        metrics["economy_rate"] = create_metric_value(
            metric_id="economy_rate",
            display_name="Economy Rate",
            value=econ_val,
            status=econ_status,
            sample_size=legal_balls,
            sample_units="balls",
            directionality=MetricDirection.LOWER_IS_BETTER,
        )

        # 6. Bowling Strike Rate: legal_balls / wickets_taken
        bsr_val, bsr_status = safe_divide(legal_balls, wickets_taken, multiplier=1.0)
        metrics["bowling_strike_rate"] = create_metric_value(
            metric_id="bowling_strike_rate",
            display_name="Bowling Strike Rate",
            value=bsr_val,
            status=bsr_status,
            sample_size=wickets_taken,
            sample_units="wickets",
            directionality=MetricDirection.LOWER_IS_BETTER,
        )

        # 7. Bowling Average: runs_conceded / wickets_taken
        bavg_val, bavg_status = safe_divide(runs_conceded, wickets_taken, multiplier=1.0)
        metrics["bowling_average"] = create_metric_value(
            metric_id="bowling_average",
            display_name="Bowling Average",
            value=bavg_val,
            status=bavg_status,
            sample_size=wickets_taken,
            sample_units="wickets",
            directionality=MetricDirection.LOWER_IS_BETTER,
        )

        # 8. Bowling Dot-Ball %: (dot_balls / legal_balls) * 100
        dot_val, dot_status = safe_divide(dot_balls, legal_balls, multiplier=100.0)
        metrics["bowling_dot_ball_percentage"] = create_metric_value(
            metric_id="bowling_dot_ball_percentage",
            display_name="Bowling Dot-Ball %",
            value=dot_val,
            status=dot_status,
            sample_size=legal_balls,
            sample_units="balls",
            directionality=MetricDirection.HIGHER_IS_BETTER,
            context={"dot_balls": dot_balls, "legal_balls": legal_balls},
        )

        # 9. Balls per Boundary Conceded (BBC): legal_balls / boundaries_conceded
        bbc_val, bbc_status = safe_divide(legal_balls, boundaries_conceded, multiplier=1.0)
        metrics["balls_per_boundary_conceded"] = create_metric_value(
            metric_id="balls_per_boundary_conceded",
            display_name="Balls per Boundary Conceded",
            value=bbc_val,
            status=bbc_status,
            sample_size=boundaries_conceded,
            sample_units="boundaries",
            directionality=MetricDirection.HIGHER_IS_BETTER,
        )

        # 10. Boundaries Conceded
        metrics["boundaries_conceded"] = create_metric_value(
            metric_id="boundaries_conceded",
            display_name="Boundaries Conceded",
            value=boundaries_conceded,
            status=MetricStatus.CALCULATED,
            sample_size=legal_balls,
            sample_units="balls",
            directionality=MetricDirection.LOWER_IS_BETTER,
            context={"fours": fours_conceded, "sixes": sixes_conceded},
        )

        # 11. Extras Conceded
        metrics["extras_conceded"] = create_metric_value(
            metric_id="extras_conceded",
            display_name="Extras Conceded",
            value=bowler_extras,
            status=MetricStatus.CALCULATED,
            sample_size=legal_balls,
            sample_units="balls",
            directionality=MetricDirection.LOWER_IS_BETTER,
        )

        return metrics

    def calculate_phase_breakdowns(
        self,
        player_id: str,
        df: pd.DataFrame,
    ) -> dict[str, dict[str, Any]]:
        """Calculate granular bowling performance per match phase (Powerplay, Middle, Death)."""
        b_df = df[df["bowler_id"] == player_id] if not df.empty and "bowler_id" in df.columns else pd.DataFrame()
        phase_splits: dict[str, dict[str, Any]] = {}

        for phase in STANDARD_PHASES:
            phase_df = b_df[b_df["phase"] == phase] if not b_df.empty and "phase" in b_df.columns else pd.DataFrame()
            if phase_df.empty:
                phase_splits[phase] = {
                    "legal_balls": 0,
                    "runs_conceded": 0,
                    "wickets": 0,
                    "economy": None,
                    "status": MetricStatus.INSUFFICIENT_SAMPLE,
                    "dot_ball_pct": None,
                }
                continue

            if "extras_type" in phase_df.columns:
                legal = phase_df[~phase_df["extras_type"].isin(["WIDE", "NO_BALL"])]
                bowler_extras = int(phase_df.loc[phase_df["extras_type"].isin(["WIDE", "NO_BALL"]), "extras_runs"].sum())
            else:
                legal = phase_df
                bowler_extras = 0

            l_count = len(legal)
            b_runs = int(phase_df["batter_runs"].sum()) if "batter_runs" in phase_df.columns else 0
            r_conceded = b_runs + bowler_extras
            w_count = self._count_bowler_wickets(phase_df)

            econ, econ_status = safe_divide(r_conceded, l_count, multiplier=6.0)

            dots = int(((legal["batter_runs"] == 0) & (legal["extras_runs"] == 0)).sum()) if "extras_runs" in legal.columns and "batter_runs" in legal.columns else 0
            dot_pct, _ = safe_divide(dots, l_count, multiplier=100.0)

            phase_splits[phase] = {
                "legal_balls": l_count,
                "runs_conceded": r_conceded,
                "wickets": w_count,
                "economy": econ,
                "status": econ_status,
                "dot_ball_pct": dot_pct,
            }

        return phase_splits

    def _count_bowler_wickets(self, df: pd.DataFrame) -> int:
        """Count bowler-credited wickets (excluding run outs, retired out/hurt, etc.)."""
        if df.empty or "is_wicket" not in df.columns:
            return 0

        wicket_df = df[df["is_wicket"] == True]  # noqa: E712
        if wicket_df.empty:
            return 0

        count = 0
        for _, row in wicket_df.iterrows():
            kind = str(row.get("dismissal_kind") or "").strip().lower()
            if kind in BOWLER_CREDITED_DISMISSALS:
                count += 1
            elif not kind:
                # If kind is missing, by default wicket is assumed bowler-credited unless specified
                count += 1

        return count

    def _empty_bowling_metrics(self) -> dict[str, MetricValue]:
        """Return metric envelopes with INSUFFICIENT_SAMPLE when no deliveries exist."""
        metric_ids = [
            ("wickets_taken", "Bowler Wickets", 0, MetricDirection.HIGHER_IS_BETTER),
            ("legal_balls_bowled", "Legal Balls Bowled", 0, MetricDirection.NEUTRAL),
            ("overs_bowled", "Overs Bowled", 0.0, MetricDirection.NEUTRAL),
            ("runs_conceded", "Runs Conceded", 0, MetricDirection.LOWER_IS_BETTER),
            ("economy_rate", "Economy Rate", None, MetricDirection.LOWER_IS_BETTER),
            ("bowling_strike_rate", "Bowling Strike Rate", None, MetricDirection.LOWER_IS_BETTER),
            ("bowling_average", "Bowling Average", None, MetricDirection.LOWER_IS_BETTER),
            ("bowling_dot_ball_percentage", "Bowling Dot-Ball %", None, MetricDirection.HIGHER_IS_BETTER),
            ("balls_per_boundary_conceded", "Balls per Boundary Conceded", None, MetricDirection.HIGHER_IS_BETTER),
            ("boundaries_conceded", "Boundaries Conceded", 0, MetricDirection.LOWER_IS_BETTER),
            ("extras_conceded", "Extras Conceded", 0, MetricDirection.LOWER_IS_BETTER),
        ]
        return {
            m_id: create_metric_value(
                metric_id=m_id,
                display_name=name,
                value=val,
                status=MetricStatus.INSUFFICIENT_SAMPLE,
                sample_size=0,
                directionality=dirn,
            )
            for m_id, name, val, dirn in metric_ids
        }

