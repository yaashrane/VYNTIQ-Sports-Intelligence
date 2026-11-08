"""Vectorized batting performance metric calculations."""

from typing import Any
import pandas as pd
from backend.app.schemas.metrics import MetricDirection, MetricStatus, MetricValue
from backend.app.services.analytics.base import (
    BOWLER_CREDITED_DISMISSALS,
    NON_BOWLER_DISMISSALS,
    STANDARD_PHASES,
    create_metric_value,
    safe_divide,
)

# Dismissal kinds that count as a batter dismissal for batting average
VALID_BATTER_DISMISSALS: set[str] = (BOWLER_CREDITED_DISMISSALS | NON_BOWLER_DISMISSALS) - {"retired hurt"}


class BattingMetricsCalculator:
    """Computes comprehensive batting rate statistics, boundary profiles, and phase splits."""

    def calculate_metrics(
        self,
        player_id: str,
        df: pd.DataFrame,
    ) -> dict[str, MetricValue]:
        """Calculate all standard batting metrics for a player from delivery records."""
        # Deliveries faced by this striker
        b_df = df[df["batter_id"] == player_id] if not df.empty and "batter_id" in df.columns else pd.DataFrame()

        if b_df.empty:
            return self._empty_batting_metrics()

        # In cricket, deliveries with extras_type == 'WIDE' do NOT count towards balls faced by the batter
        if "extras_type" in b_df.columns:
            balls_df = b_df[b_df["extras_type"] != "WIDE"]
        else:
            balls_df = b_df

        balls_faced = len(balls_df)
        batter_runs = int(balls_df["batter_runs"].sum()) if "batter_runs" in balls_df.columns else 0

        # Boundary calculations
        if "batter_runs" in balls_df.columns:
            fours = int((balls_df["batter_runs"] == 4).sum())
            sixes = int((balls_df["batter_runs"] == 6).sum())
        else:
            fours = 0
            sixes = 0
        total_boundaries = fours + sixes
        boundary_runs = (fours * 4) + (sixes * 6)

        # Dot balls: Deliveries faced (excluding wides) where batter scored 0 runs
        if "batter_runs" in balls_df.columns:
            dot_balls = int((balls_df["batter_runs"] == 0).sum())
        else:
            dot_balls = 0

        # Dismissal calculation:
        # Batter is out when is_wicket is True AND
        # (dismissed_player_id == player_id OR (dismissed_player_id is null and bowler wicket credited on delivery))
        # and dismissal_kind is not 'retired hurt'
        dismissals = self._count_batter_dismissals(player_id, b_df)

        metrics: dict[str, MetricValue] = {}

        # 1. Runs Scored
        metrics["runs_scored"] = create_metric_value(
            metric_id="runs_scored",
            display_name="Runs Scored",
            value=batter_runs,
            status=MetricStatus.CALCULATED,
            sample_size=balls_faced,
            sample_units="balls",
            directionality=MetricDirection.HIGHER_IS_BETTER,
        )

        # 2. Balls Faced
        metrics["balls_faced"] = create_metric_value(
            metric_id="balls_faced",
            display_name="Balls Faced",
            value=balls_faced,
            status=MetricStatus.CALCULATED,
            sample_size=balls_faced,
            sample_units="balls",
            directionality=MetricDirection.NEUTRAL,
        )

        # 3. Batting Strike Rate
        sr_val, sr_status = safe_divide(batter_runs, balls_faced, multiplier=100.0)
        metrics["batting_strike_rate"] = create_metric_value(
            metric_id="batting_strike_rate",
            display_name="Batting Strike Rate",
            value=sr_val,
            status=sr_status,
            sample_size=balls_faced,
            sample_units="balls",
            directionality=MetricDirection.HIGHER_IS_BETTER,
        )

        # 4. Batting Average
        avg_val, avg_status = safe_divide(batter_runs, dismissals, multiplier=1.0)
        metrics["batting_average"] = create_metric_value(
            metric_id="batting_average",
            display_name="Batting Average",
            value=avg_val,
            status=avg_status,
            sample_size=dismissals,
            sample_units="dismissals",
            directionality=MetricDirection.HIGHER_IS_BETTER,
            context={"dismissals": dismissals, "not_outs": max(0, b_df["match_id"].nunique() - dismissals) if "match_id" in b_df.columns else 0},
        )

        # 5. Balls per Dismissal (BPD)
        bpd_val, bpd_status = safe_divide(balls_faced, dismissals, multiplier=1.0)
        metrics["balls_per_dismissal"] = create_metric_value(
            metric_id="balls_per_dismissal",
            display_name="Balls per Dismissal",
            value=bpd_val,
            status=bpd_status,
            sample_size=dismissals,
            sample_units="dismissals",
            directionality=MetricDirection.HIGHER_IS_BETTER,
        )

        # 6. Boundary % (Runs)
        bp_runs_val, bp_runs_status = safe_divide(boundary_runs, batter_runs, multiplier=100.0)
        metrics["boundary_percentage_runs"] = create_metric_value(
            metric_id="boundary_percentage_runs",
            display_name="Boundary % (Runs)",
            value=bp_runs_val if batter_runs > 0 else 0.0,
            status=MetricStatus.CALCULATED if batter_runs > 0 else MetricStatus.DIVIDE_BY_ZERO_SAFEGUARD,
            sample_size=balls_faced,
            sample_units="balls",
            directionality=MetricDirection.HIGHER_IS_BETTER,
            context={"boundary_runs": boundary_runs, "total_runs": batter_runs},
        )

        # 7. Boundary % (Balls)
        bp_balls_val, bp_balls_status = safe_divide(total_boundaries, balls_faced, multiplier=100.0)
        metrics["boundary_percentage_balls"] = create_metric_value(
            metric_id="boundary_percentage_balls",
            display_name="Boundary % (Balls)",
            value=bp_balls_val,
            status=bp_balls_status,
            sample_size=balls_faced,
            sample_units="balls",
            directionality=MetricDirection.HIGHER_IS_BETTER,
            context={"total_boundaries": total_boundaries, "balls_faced": balls_faced},
        )

        # 8. Balls per Boundary
        bpb_val, bpb_status = safe_divide(balls_faced, total_boundaries, multiplier=1.0)
        metrics["balls_per_boundary"] = create_metric_value(
            metric_id="balls_per_boundary",
            display_name="Balls per Boundary",
            value=bpb_val,
            status=bpb_status,
            sample_size=total_boundaries,
            sample_units="boundaries",
            directionality=MetricDirection.LOWER_IS_BETTER,
        )

        # 9. Dot Ball %
        dot_val, dot_status = safe_divide(dot_balls, balls_faced, multiplier=100.0)
        metrics["dot_ball_percentage"] = create_metric_value(
            metric_id="dot_ball_percentage",
            display_name="Batting Dot-Ball %",
            value=dot_val,
            status=dot_status,
            sample_size=balls_faced,
            sample_units="balls",
            directionality=MetricDirection.LOWER_IS_BETTER,
            context={"dot_balls": dot_balls, "balls_faced": balls_faced},
        )

        # 10. Dot Ball Suppression (100 - Dot %)
        dbs_val = round(100.0 - dot_val, 2) if dot_val is not None else None
        metrics["dot_ball_suppression"] = create_metric_value(
            metric_id="dot_ball_suppression",
            display_name="Dot Ball Suppression",
            value=dbs_val,
            status=dot_status,
            sample_size=balls_faced,
            sample_units="balls",
            directionality=MetricDirection.HIGHER_IS_BETTER,
        )

        # 11. Fours Count
        metrics["fours_count"] = create_metric_value(
            metric_id="fours_count",
            display_name="Fours Hit",
            value=fours,
            status=MetricStatus.CALCULATED,
            sample_size=balls_faced,
            sample_units="balls",
            directionality=MetricDirection.HIGHER_IS_BETTER,
        )

        # 12. Sixes Count
        metrics["sixes_count"] = create_metric_value(
            metric_id="sixes_count",
            display_name="Sixes Hit",
            value=sixes,
            status=MetricStatus.CALCULATED,
            sample_size=balls_faced,
            sample_units="balls",
            directionality=MetricDirection.HIGHER_IS_BETTER,
        )

        return metrics

    def calculate_phase_breakdowns(
        self,
        player_id: str,
        df: pd.DataFrame,
    ) -> dict[str, dict[str, Any]]:
        """Calculate granular batting performance per match phase (Powerplay, Middle, Death)."""
        b_df = df[df["batter_id"] == player_id] if not df.empty and "batter_id" in df.columns else pd.DataFrame()
        phase_splits: dict[str, dict[str, Any]] = {}

        for phase in STANDARD_PHASES:
            phase_df = b_df[b_df["phase"] == phase] if not b_df.empty and "phase" in b_df.columns else pd.DataFrame()
            if phase_df.empty:
                phase_splits[phase] = {
                    "balls_faced": 0,
                    "runs_scored": 0,
                    "strike_rate": None,
                    "status": MetricStatus.INSUFFICIENT_SAMPLE,
                    "dot_ball_pct": None,
                    "fours": 0,
                    "sixes": 0,
                    "dismissals": 0,
                }
                continue

            balls = phase_df[phase_df["extras_type"] != "WIDE"] if "extras_type" in phase_df.columns else phase_df
            b_count = len(balls)
            r_count = int(balls["batter_runs"].sum()) if "batter_runs" in balls.columns else 0
            sr, sr_status = safe_divide(r_count, b_count, multiplier=100.0)

            dots = int((balls["batter_runs"] == 0).sum()) if "batter_runs" in balls.columns else 0
            dot_pct, _ = safe_divide(dots, b_count, multiplier=100.0)

            fours = int((balls["batter_runs"] == 4).sum()) if "batter_runs" in balls.columns else 0
            sixes = int((balls["batter_runs"] == 6).sum()) if "batter_runs" in balls.columns else 0
            dismissals = self._count_batter_dismissals(player_id, phase_df)

            phase_splits[phase] = {
                "balls_faced": b_count,
                "runs_scored": r_count,
                "strike_rate": sr,
                "status": sr_status,
                "dot_ball_pct": dot_pct,
                "fours": fours,
                "sixes": sixes,
                "dismissals": dismissals,
            }

        return phase_splits

    def _count_batter_dismissals(self, player_id: str, df: pd.DataFrame) -> int:
        """Count times the batter was dismissed, handling dismissal kinds and null fields."""
        if df.empty or "is_wicket" not in df.columns:
            return 0

        wicket_df = df[df["is_wicket"] == True]  # noqa: E712
        if wicket_df.empty:
            return 0

        count = 0
        for _, row in wicket_df.iterrows():
            dismissed_id = row.get("dismissed_player_id")
            kind = str(row.get("dismissal_kind") or "").strip().lower()

            # Ignore retired hurt
            if kind == "retired hurt":
                continue

            # If dismissed_player_id is explicit, match on it
            if dismissed_id and str(dismissed_id).strip():
                if str(dismissed_id).strip() == str(player_id).strip():
                    count += 1
            else:
                # If dismissed_player_id is not provided, check if it's a striker dismissal kind
                # where the batter at the crease is dismissed
                if kind in VALID_BATTER_DISMISSALS and kind != "run out":
                    count += 1

        return count

    def _empty_batting_metrics(self) -> dict[str, MetricValue]:
        """Return metric envelopes with INSUFFICIENT_SAMPLE when no deliveries exist."""
        metric_ids = [
            ("runs_scored", "Runs Scored", 0, MetricDirection.HIGHER_IS_BETTER),
            ("balls_faced", "Balls Faced", 0, MetricDirection.NEUTRAL),
            ("batting_strike_rate", "Batting Strike Rate", None, MetricDirection.HIGHER_IS_BETTER),
            ("batting_average", "Batting Average", None, MetricDirection.HIGHER_IS_BETTER),
            ("balls_per_dismissal", "Balls per Dismissal", None, MetricDirection.HIGHER_IS_BETTER),
            ("boundary_percentage_runs", "Boundary % (Runs)", None, MetricDirection.HIGHER_IS_BETTER),
            ("boundary_percentage_balls", "Boundary % (Balls)", None, MetricDirection.HIGHER_IS_BETTER),
            ("balls_per_boundary", "Balls per Boundary", None, MetricDirection.LOWER_IS_BETTER),
            ("dot_ball_percentage", "Batting Dot-Ball %", None, MetricDirection.LOWER_IS_BETTER),
            ("dot_ball_suppression", "Dot Ball Suppression", None, MetricDirection.HIGHER_IS_BETTER),
            ("fours_count", "Fours Hit", 0, MetricDirection.HIGHER_IS_BETTER),
            ("sixes_count", "Sixes Hit", 0, MetricDirection.HIGHER_IS_BETTER),
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

