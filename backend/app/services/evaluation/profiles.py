"""Role-specific evaluation profile builders for batters, bowlers, all-rounders, and wicketkeepers."""

from typing import Any
from backend.app.schemas.evaluation import (
    DimensionAvailabilityStatus,
    DimensionEvaluationProfile,
    PlayerRole,
    SampleAdequacyStatus,
)
from backend.app.schemas.metrics import (
    MetricCategory,
    MetricDirection,
    MetricStatus,
    MetricValue,
    SampleSizeInfo,
)
from backend.app.services.analytics.base import create_metric_value
from backend.app.services.evaluation.adequacy import SampleAdequacyEvaluator
from backend.app.services.evaluation.registry import EVALUATION_DIMENSION_REGISTRY


class ProfileBuilder:
    """Builds structured, role-specific evaluation profiles organized into transparent dimensions."""

    def __init__(self, adequacy_evaluator: SampleAdequacyEvaluator | None = None) -> None:
        self.adequacy = adequacy_evaluator or SampleAdequacyEvaluator()

    def build_profile(
        self,
        role: PlayerRole,
        batting_metrics: dict[str, MetricValue],
        bowling_metrics: dict[str, MetricValue],
        sample: SampleSizeInfo,
        fielding_data: dict[str, Any] | None = None,
    ) -> dict[str, DimensionEvaluationProfile]:
        """Construct dimension profiles tailored to the player's specific cricketing role."""
        adequacy = self.adequacy.assess_adequacy(role, sample)
        profiles: dict[str, DimensionEvaluationProfile] = {}

        # 1. BATTING PROFILES (BATTER, ALL_ROUNDER, WICKETKEEPER, UNKNOWN with batting data)
        if role in (PlayerRole.BATTER, PlayerRole.ALL_ROUNDER, PlayerRole.WICKETKEEPER) or (
            role == PlayerRole.UNKNOWN and sample.balls_faced > 0
        ):
            bat_status = self._adequacy_to_dimension_status(adequacy.batting)

            # Scoring Output
            profiles["scoring_output"] = DimensionEvaluationProfile(
                dimension_id="scoring_output",
                dimension_name="Scoring Output",
                status=bat_status,
                metrics=[batting_metrics[k] for k in ["runs_scored", "fours_count", "sixes_count"] if k in batting_metrics],
                interpretation="Measures run volume off the bat and boundary distribution.",
            )

            # Scoring Efficiency
            profiles["scoring_efficiency"] = DimensionEvaluationProfile(
                dimension_id="scoring_efficiency",
                dimension_name="Scoring Efficiency",
                status=bat_status,
                metrics=[batting_metrics[k] for k in ["batting_strike_rate", "true_strike_rate"] if k in batting_metrics],
                interpretation="Evaluates scoring pace relative to balls faced and phase context.",
            )

            # Boundary Potency
            profiles["boundary_contribution"] = DimensionEvaluationProfile(
                dimension_id="boundary_contribution",
                dimension_name="Boundary Potency",
                status=bat_status,
                metrics=[
                    batting_metrics[k]
                    for k in ["boundary_percentage_runs", "boundary_percentage_balls", "balls_per_boundary"]
                    if k in batting_metrics
                ],
                interpretation="Measures boundary penetration and boundary-clearing frequency.",
            )

            # Dismissal Resistance
            # If dismissals are 0, status is LIMITED
            res_status = DimensionAvailabilityStatus.LIMITED if sample.times_dismissed == 0 else bat_status
            profiles["dismissal_resistance"] = DimensionEvaluationProfile(
                dimension_id="dismissal_resistance",
                dimension_name="Dismissal Resistance & Stability",
                status=res_status,
                metrics=[batting_metrics[k] for k in ["batting_average", "balls_per_dismissal"] if k in batting_metrics],
                interpretation="Evaluates crease durability and wicket preservation.",
            )

            # Strike Rotation & Consistency
            profiles["consistency"] = DimensionEvaluationProfile(
                dimension_id="consistency",
                dimension_name="Strike Rotation & Consistency",
                status=bat_status,
                metrics=[batting_metrics[k] for k in ["dot_ball_suppression", "dot_ball_percentage"] if k in batting_metrics],
                interpretation="Reflects single-taking strike rotation and non-scoring delivery reduction.",
            )

        # 2. BOWLING PROFILES (BOWLER, ALL_ROUNDER, UNKNOWN with bowling data)
        if role in (PlayerRole.BOWLER, PlayerRole.ALL_ROUNDER) or (
            role == PlayerRole.UNKNOWN and sample.legal_balls_bowled > 0
        ):
            bowl_status = self._adequacy_to_dimension_status(adequacy.bowling)

            # Wicket-Taking Performance
            profiles["wicket_taking_performance"] = DimensionEvaluationProfile(
                dimension_id="wicket_taking_performance",
                dimension_name="Wicket-Taking Performance",
                status=bowl_status,
                metrics=[
                    bowling_metrics[k]
                    for k in ["wickets_taken", "bowling_strike_rate", "bowling_average"]
                    if k in bowling_metrics
                ],
                interpretation="Measures frequency and efficiency of claiming opposition wickets.",
            )

            # Run Containment
            profiles["run_containment"] = DimensionEvaluationProfile(
                dimension_id="run_containment",
                dimension_name="Run Containment",
                status=bowl_status,
                metrics=[bowling_metrics[k] for k in ["economy_rate", "true_economy_rate"] if k in bowling_metrics],
                interpretation="Evaluates runs conceded per 6 legitimate deliveries and relative to phase par.",
            )

            # Dot-Ball Generation
            profiles["dot_ball_generation"] = DimensionEvaluationProfile(
                dimension_id="dot_ball_generation",
                dimension_name="Dot-Ball Generation & Pressure",
                status=bowl_status,
                metrics=[bowling_metrics[k] for k in ["bowling_dot_ball_percentage"] if k in bowling_metrics],
                interpretation="Evaluates sustained pressure creation via dot balls.",
            )

            # Bowling Workload
            profiles["bowling_workload"] = DimensionEvaluationProfile(
                dimension_id="bowling_workload",
                dimension_name="Bowling Workload & Discipline",
                status=bowl_status,
                metrics=[
                    bowling_metrics[k]
                    for k in ["legal_balls_bowled", "overs_bowled", "runs_conceded", "extras_conceded"]
                    if k in bowling_metrics
                ],
                interpretation="Tracks legitimate bowling overs delivered and extras control.",
            )

            # Boundary Suppression
            profiles["boundary_containment"] = DimensionEvaluationProfile(
                dimension_id="boundary_containment",
                dimension_name="Boundary Suppression",
                status=bowl_status,
                metrics=[
                    bowling_metrics[k]
                    for k in ["balls_per_boundary_conceded", "boundaries_conceded"]
                    if k in bowling_metrics
                ],
                interpretation="Measures delivery intervals between boundary concessions.",
            )

        # 3. WICKETKEEPER OPTIONAL DIMENSION
        if role == PlayerRole.WICKETKEEPER:
            f_data = fielding_data or {}
            has_fielding = "catches_taken" in f_data or "stumpings_made" in f_data

            if has_fielding:
                keeper_metrics = [
                    create_metric_value(
                        metric_id="catches_taken",
                        display_name="Catches as Keeper",
                        value=f_data.get("catches_taken", 0),
                        status=MetricStatus.CALCULATED,
                        sample_size=sample.matches_played,
                        sample_units="matches",
                        directionality=MetricDirection.HIGHER_IS_BETTER,
                    ),
                    create_metric_value(
                        metric_id="stumpings_made",
                        display_name="Stumpings Effected",
                        value=f_data.get("stumpings_made", 0),
                        status=MetricStatus.CALCULATED,
                        sample_size=sample.matches_played,
                        sample_units="matches",
                        directionality=MetricDirection.HIGHER_IS_BETTER,
                    ),
                ]
                wk_status = DimensionAvailabilityStatus.AVAILABLE
            else:
                keeper_metrics = [
                    create_metric_value(
                        metric_id="catches_taken",
                        display_name="Catches as Keeper",
                        value=None,
                        status=MetricStatus.DATA_UNAVAILABLE,
                        sample_size=0,
                        sample_units="matches",
                        context={"reason": "Fielding and wicketkeeper tracking not present in dataset."},
                    ),
                    create_metric_value(
                        metric_id="stumpings_made",
                        display_name="Stumpings Effected",
                        value=None,
                        status=MetricStatus.DATA_UNAVAILABLE,
                        sample_size=0,
                        sample_units="matches",
                        context={"reason": "Fielding and wicketkeeper tracking not present in dataset."},
                    ),
                ]
                wk_status = DimensionAvailabilityStatus.DATA_UNAVAILABLE

            profiles["wicketkeeping_dismissals"] = DimensionEvaluationProfile(
                dimension_id="wicketkeeping_dismissals",
                dimension_name="Wicketkeeping Dismissals",
                status=wk_status,
                metrics=keeper_metrics,
                interpretation="Direct dismissals effected behind the stumps; marked unavailable when fielding telemetry is absent.",
            )

        return profiles

    def _adequacy_to_dimension_status(self, adequacy_status: SampleAdequacyStatus) -> DimensionAvailabilityStatus:
        """Map sample volume reliability to dimension availability status."""
        if adequacy_status == SampleAdequacyStatus.ADEQUATE:
            return DimensionAvailabilityStatus.AVAILABLE
        elif adequacy_status == SampleAdequacyStatus.LIMITED:
            return DimensionAvailabilityStatus.LIMITED
        elif adequacy_status == SampleAdequacyStatus.INSUFFICIENT:
            return DimensionAvailabilityStatus.INSUFFICIENT
        return DimensionAvailabilityStatus.DATA_UNAVAILABLE
