"""Role-specific performance dimension clustering for batters, bowlers, and all-rounders."""

from backend.app.schemas.analytics import DimensionGroup
from backend.app.schemas.metrics import MetricValue


class DimensionBuilder:
    """Organizes atomic metrics into clear, thematic performance dimensions without arbitrary weights."""

    def build_batting_dimensions(
        self,
        metrics: dict[str, MetricValue],
    ) -> dict[str, DimensionGroup]:
        """Group batting metrics into the 5 core batting evaluation dimensions."""
        dimensions: dict[str, DimensionGroup] = {}

        # 1. Scoring Output
        output_keys = ["runs_scored", "fours_count", "sixes_count"]
        dimensions["scoring_output"] = DimensionGroup(
            dimension_id="scoring_output",
            dimension_name="Scoring Output",
            metrics={k: metrics[k] for k in output_keys if k in metrics},
        )

        # 2. Scoring Efficiency
        efficiency_keys = ["batting_strike_rate", "true_strike_rate"]
        dimensions["scoring_efficiency"] = DimensionGroup(
            dimension_id="scoring_efficiency",
            dimension_name="Scoring Efficiency",
            metrics={k: metrics[k] for k in efficiency_keys if k in metrics},
        )

        # 3. Boundary Contribution
        boundary_keys = ["boundary_percentage_runs", "boundary_percentage_balls", "balls_per_boundary"]
        dimensions["boundary_contribution"] = DimensionGroup(
            dimension_id="boundary_contribution",
            dimension_name="Boundary Contribution",
            metrics={k: metrics[k] for k in boundary_keys if k in metrics},
        )

        # 4. Dismissal Resistance
        resistance_keys = ["batting_average", "balls_per_dismissal"]
        dimensions["dismissal_resistance"] = DimensionGroup(
            dimension_id="dismissal_resistance",
            dimension_name="Dismissal Resistance",
            metrics={k: metrics[k] for k in resistance_keys if k in metrics},
        )

        # 5. Strike Rotation & Consistency
        consistency_keys = ["dot_ball_suppression", "dot_ball_percentage"]
        dimensions["consistency"] = DimensionGroup(
            dimension_id="consistency",
            dimension_name="Strike Rotation & Consistency",
            metrics={k: metrics[k] for k in consistency_keys if k in metrics},
        )

        return dimensions

    def build_bowling_dimensions(
        self,
        metrics: dict[str, MetricValue],
    ) -> dict[str, DimensionGroup]:
        """Group bowling metrics into the 5 core bowling evaluation dimensions."""
        dimensions: dict[str, DimensionGroup] = {}

        # 1. Wicket-Taking Performance
        wicket_keys = ["wickets_taken", "bowling_strike_rate", "bowling_average"]
        dimensions["wicket_taking_performance"] = DimensionGroup(
            dimension_id="wicket_taking_performance",
            dimension_name="Wicket-Taking Performance",
            metrics={k: metrics[k] for k in wicket_keys if k in metrics},
        )

        # 2. Run Containment
        containment_keys = ["economy_rate", "true_economy_rate"]
        dimensions["run_containment"] = DimensionGroup(
            dimension_id="run_containment",
            dimension_name="Run Containment",
            metrics={k: metrics[k] for k in containment_keys if k in metrics},
        )

        # 3. Dot-Ball Generation
        dot_keys = ["bowling_dot_ball_percentage"]
        dimensions["dot_ball_generation"] = DimensionGroup(
            dimension_id="dot_ball_generation",
            dimension_name="Dot-Ball Generation",
            metrics={k: metrics[k] for k in dot_keys if k in metrics},
        )

        # 4. Bowling Workload
        workload_keys = ["legal_balls_bowled", "overs_bowled", "runs_conceded", "extras_conceded"]
        dimensions["bowling_workload"] = DimensionGroup(
            dimension_id="bowling_workload",
            dimension_name="Bowling Workload",
            metrics={k: metrics[k] for k in workload_keys if k in metrics},
        )

        # 5. Boundary Containment
        boundary_keys = ["balls_per_boundary_conceded", "boundaries_conceded"]
        dimensions["boundary_containment"] = DimensionGroup(
            dimension_id="boundary_containment",
            dimension_name="Boundary Containment",
            metrics={k: metrics[k] for k in boundary_keys if k in metrics},
        )

        return dimensions

