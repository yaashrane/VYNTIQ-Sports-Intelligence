"""Advanced and contextual cricket metric evaluation.

Handles True Strike Rate (TSR), True Economy Rate (TER), and safely reports
provisional or open definitions (WTI, CFI, NVC) without inventing unscientific formulas.
"""

from typing import Any
import pandas as pd
from backend.app.schemas.metrics import MetricDirection, MetricStatus, MetricValue
from backend.app.services.analytics.base import (
    STANDARD_PHASES,
    create_metric_value,
    safe_divide,
)

# Standard T20 par expectations by match phase (used when cohort volume is cold or default)
DEFAULT_PHASE_PARS = {
    "POWERPLAY": {"sr": 128.5, "economy": 7.40},
    "MIDDLE": {"sr": 134.0, "economy": 7.85},
    "DEATH": {"sr": 172.5, "economy": 10.20},
}


class AdvancedMetricsEvaluator:
    """Evaluates contextual and advanced metrics, strictly enforcing data availability checks."""

    def compute_true_strike_rate(
        self,
        player_id: str,
        df: pd.DataFrame,
        phase_baselines: dict[str, dict[str, float]] | None = None,
    ) -> MetricValue:
        """Calculate True Strike Rate (TSR) relative to phase baseline expectations.

        Formula: Actual_SR - Expected_SR(cohort, phase, venue)
        """
        b_df = df[df["batter_id"] == player_id] if not df.empty and "batter_id" in df.columns else pd.DataFrame()
        if b_df.empty:
            return create_metric_value(
                metric_id="true_strike_rate",
                display_name="True Strike Rate (TSR)",
                value=None,
                status=MetricStatus.INSUFFICIENT_SAMPLE,
                sample_size=0,
                directionality=MetricDirection.HIGHER_IS_BETTER,
            )

        balls_df = b_df[b_df["extras_type"] != "WIDE"] if "extras_type" in b_df.columns else b_df
        total_balls = len(balls_df)
        if total_balls == 0:
            return create_metric_value(
                metric_id="true_strike_rate",
                display_name="True Strike Rate (TSR)",
                value=None,
                status=MetricStatus.DIVIDE_BY_ZERO_SAFEGUARD,
                sample_size=0,
                directionality=MetricDirection.HIGHER_IS_BETTER,
            )

        # Compute weighted expected runs based on phase distribution
        baselines = phase_baselines or DEFAULT_PHASE_PARS
        total_expected_runs = 0.0
        total_actual_runs = int(balls_df["batter_runs"].sum()) if "batter_runs" in balls_df.columns else 0

        for phase in STANDARD_PHASES:
            p_balls = len(balls_df[balls_df["phase"] == phase]) if "phase" in balls_df.columns else 0
            if p_balls > 0:
                exp_sr = baselines.get(phase, {}).get("sr", 130.0)
                total_expected_runs += (exp_sr / 100.0) * p_balls

        expected_sr = (total_expected_runs / total_balls) * 100.0 if total_balls > 0 else 130.0
        actual_sr = (total_actual_runs / total_balls) * 100.0
        tsr_val = round(actual_sr - expected_sr, 2)

        return create_metric_value(
            metric_id="true_strike_rate",
            display_name="True Strike Rate (TSR)",
            value=tsr_val,
            status=MetricStatus.CALCULATED,
            sample_size=total_balls,
            sample_units="balls",
            directionality=MetricDirection.HIGHER_IS_BETTER,
            context={
                "actual_sr": round(actual_sr, 2),
                "expected_sr": round(expected_sr, 2),
                "balls_faced": total_balls,
            },
        )

    def compute_true_economy_rate(
        self,
        player_id: str,
        df: pd.DataFrame,
        phase_baselines: dict[str, dict[str, float]] | None = None,
    ) -> MetricValue:
        """Calculate True Economy Rate (TER) relative to phase baseline expectations.

        Formula: Expected_Economy - Actual_Economy (Positive is superior run containment)
        """
        b_df = df[df["bowler_id"] == player_id] if not df.empty and "bowler_id" in df.columns else pd.DataFrame()
        if b_df.empty:
            return create_metric_value(
                metric_id="true_economy_rate",
                display_name="True Economy Rate (TER)",
                value=None,
                status=MetricStatus.INSUFFICIENT_SAMPLE,
                sample_size=0,
                directionality=MetricDirection.HIGHER_IS_BETTER,
            )

        if "extras_type" in b_df.columns:
            legal_df = b_df[~b_df["extras_type"].isin(["WIDE", "NO_BALL"])]
        else:
            legal_df = b_df

        legal_balls = len(legal_df)
        if legal_balls == 0:
            return create_metric_value(
                metric_id="true_economy_rate",
                display_name="True Economy Rate (TER)",
                value=None,
                status=MetricStatus.DIVIDE_BY_ZERO_SAFEGUARD,
                sample_size=0,
                directionality=MetricDirection.HIGHER_IS_BETTER,
            )

        batter_runs = int(b_df["batter_runs"].sum()) if "batter_runs" in b_df.columns else 0
        if "extras_type" in b_df.columns and "extras_runs" in b_df.columns:
            bowler_extras = int(b_df.loc[b_df["extras_type"].isin(["WIDE", "NO_BALL"]), "extras_runs"].sum())
        else:
            bowler_extras = 0
        runs_conceded = batter_runs + bowler_extras
        actual_economy = (runs_conceded / legal_balls) * 6.0

        baselines = phase_baselines or DEFAULT_PHASE_PARS
        total_expected_runs = 0.0

        for phase in STANDARD_PHASES:
            p_legal = len(legal_df[legal_df["phase"] == phase]) if "phase" in legal_df.columns else 0
            if p_legal > 0:
                exp_econ = baselines.get(phase, {}).get("economy", 8.0)
                total_expected_runs += (exp_econ / 6.0) * p_legal

        expected_economy = (total_expected_runs / legal_balls) * 6.0 if legal_balls > 0 else 8.0
        ter_val = round(expected_economy - actual_economy, 2)

        return create_metric_value(
            metric_id="true_economy_rate",
            display_name="True Economy Rate (TER)",
            value=ter_val,
            status=MetricStatus.CALCULATED,
            sample_size=legal_balls,
            sample_units="balls",
            directionality=MetricDirection.HIGHER_IS_BETTER,
            context={
                "actual_economy": round(actual_economy, 2),
                "expected_economy": round(expected_economy, 2),
                "legal_balls": legal_balls,
            },
        )

    def evaluate_wicket_threat_index(
        self,
        player_id: str,
        df: pd.DataFrame,
    ) -> MetricValue:
        """Evaluate Wicket Threat Index (WTI) with explicit data-availability checking."""
        if "batting_order_position" not in df.columns:
            return create_metric_value(
                metric_id="wicket_threat_index",
                display_name="Wicket Threat Index (WTI)",
                value=None,
                status=MetricStatus.OPEN_DEFINITION,
                sample_size=0,
                directionality=MetricDirection.HIGHER_IS_BETTER,
                context={
                    "missing_source_field": "batting_order_position",
                    "reason": (
                        "Batting order position is required to calculate batter quality weights "
                        "(1-3: 1.5, 4-6: 1.0, 7-11: 0.6) per METHOD-VYNTIQ-001 Section 2.3. "
                        "Field not present in dataset schema."
                    ),
                },
            )

        # If field is present, compute weighted wickets per over
        b_df = df[df["bowler_id"] == player_id]
        if b_df.empty:
            return create_metric_value(
                metric_id="wicket_threat_index",
                display_name="Wicket Threat Index (WTI)",
                value=None,
                status=MetricStatus.INSUFFICIENT_SAMPLE,
                sample_size=0,
            )

        legal_balls = len(b_df[~b_df["extras_type"].isin(["WIDE", "NO_BALL"])]) if "extras_type" in b_df.columns else len(b_df)
        overs = legal_balls / 6.0
        if overs == 0:
            return create_metric_value(
                metric_id="wicket_threat_index",
                display_name="Wicket Threat Index (WTI)",
                value=None,
                status=MetricStatus.DIVIDE_BY_ZERO_SAFEGUARD,
                sample_size=0,
            )

        # Calculate weighted wickets
        weighted_wickets = 0.0
        wicket_df = b_df[b_df["is_wicket"] == True]  # noqa: E712
        for _, row in wicket_df.iterrows():
            pos = row.get("batting_order_position")
            weight = 1.5 if pos and pos <= 3 else (1.0 if pos and pos <= 6 else 0.6)
            weighted_wickets += weight

        wti = round(weighted_wickets / overs, 2)
        return create_metric_value(
            metric_id="wicket_threat_index",
            display_name="Wicket Threat Index (WTI)",
            value=wti,
            status=MetricStatus.CALCULATED,
            sample_size=legal_balls,
            sample_units="balls",
            directionality=MetricDirection.HIGHER_IS_BETTER,
        )

    def evaluate_clutch_finishing_index(
        self,
        player_id: str,
        df: pd.DataFrame,
    ) -> MetricValue:
        """Evaluate Clutch Finishing Index (CFI) with explicit data-availability checking."""
        if "required_run_rate" not in df.columns and "target_runs" not in df.columns:
            return create_metric_value(
                metric_id="clutch_finishing_index",
                display_name="Clutch Finishing Index (CFI)",
                value=None,
                status=MetricStatus.OPEN_DEFINITION,
                sample_size=0,
                directionality=MetricDirection.HIGHER_IS_BETTER,
                context={
                    "missing_source_field": "required_run_rate",
                    "reason": (
                        "Requires live chase target / required run rate (>= 9.5 RPO) in overs 16-20. "
                        "Field not present in standard first-innings ball-by-ball."
                    ),
                },
            )

        return create_metric_value(
            metric_id="clutch_finishing_index",
            display_name="Clutch Finishing Index (CFI)",
            value=None,
            status=MetricStatus.OPEN_DEFINITION,
            sample_size=0,
            directionality=MetricDirection.HIGHER_IS_BETTER,
            context={"reason": "Live chase context available but RRR indexing is provisional."},
        )

    def evaluate_net_value_contribution(self) -> MetricValue:
        """Report Net Value Contribution (NVC) as NOT_IMPLEMENTED per Section 6."""
        return create_metric_value(
            metric_id="net_value_contribution",
            display_name="Net Value Contribution (NVC)",
            value=None,
            status=MetricStatus.NOT_IMPLEMENTED,
            sample_size=0,
            directionality=MetricDirection.HIGHER_IS_BETTER,
            context={
                "reason": (
                    "Net Value Contribution requires a calibrated win-probability model and "
                    "run-expectancy transition matrix. Deferred per architectural roadmap."
                ),
            },
        )
