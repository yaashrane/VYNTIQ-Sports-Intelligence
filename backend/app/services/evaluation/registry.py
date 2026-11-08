"""Central registry for role-specific evaluation dimensions and metadata."""

from backend.app.schemas.evaluation import DimensionRegistryEntry

EVALUATION_DIMENSION_REGISTRY: dict[str, DimensionRegistryEntry] = {
    # ==================== BATTING DIMENSIONS ====================
    "scoring_output": DimensionRegistryEntry(
        dimension_id="scoring_output",
        display_name="Scoring Output",
        description="Measures raw run accumulation, volume, and boundary run contribution.",
        applicable_roles=["BATTER", "ALL_ROUNDER", "WICKETKEEPER"],
        associated_metrics=["runs_scored", "fours_count", "sixes_count"],
        interpretation="Quantifies total run production; essential for establishing core match contribution volume.",
        required_data_fields=["batter_runs"],
        sample_requirements="Minimum 20 balls faced for provisional evaluation; 60+ balls for adequate assessment.",
        limitations="Does not reflect scoring speed or phase-of-play difficulty.",
    ),
    "scoring_efficiency": DimensionRegistryEntry(
        dimension_id="scoring_efficiency",
        display_name="Scoring Efficiency",
        description="Measures scoring velocity (Strike Rate) and delivery consumption efficiency.",
        applicable_roles=["BATTER", "ALL_ROUNDER", "WICKETKEEPER"],
        associated_metrics=["batting_strike_rate", "true_strike_rate"],
        interpretation="Evaluates scoring pace relative to balls consumed and phase baseline par.",
        required_data_fields=["batter_runs", "extras_type"],
        sample_requirements="Minimum 30 balls faced for meaningful rate calculation.",
        limitations="Strike rate can be volatile over short innings.",
    ),
    "boundary_contribution": DimensionRegistryEntry(
        dimension_id="boundary_contribution",
        display_name="Boundary Potency",
        description="Evaluates field-penetration and boundary-clearing frequency and percentage of runs.",
        applicable_roles=["BATTER", "ALL_ROUNDER", "WICKETKEEPER"],
        associated_metrics=["boundary_percentage_runs", "boundary_percentage_balls", "balls_per_boundary"],
        interpretation="High boundary percentage indicates power-hitting ability and pressure generation.",
        required_data_fields=["batter_runs", "extras_type"],
        sample_requirements="Minimum 30 balls faced.",
        limitations="Does not measure singles strike rotation between boundaries.",
    ),
    "dismissal_resistance": DimensionRegistryEntry(
        dimension_id="dismissal_resistance",
        display_name="Dismissal Resistance & Stability",
        description="Evaluates crease preservation and batting durability (Batting Average and Balls per Dismissal).",
        applicable_roles=["BATTER", "ALL_ROUNDER", "WICKETKEEPER"],
        associated_metrics=["batting_average", "balls_per_dismissal"],
        interpretation="Higher balls per dismissal denotes stability and resistance to bowling attack.",
        required_data_fields=["batter_runs", "extras_type", "is_wicket", "dismissed_player_id"],
        sample_requirements="Minimum 3 completed dismissals to avoid infinite/skewed not-out rates.",
        limitations="Can reward slow, defensive batting if uncoupled from strike rate.",
    ),
    "consistency": DimensionRegistryEntry(
        dimension_id="consistency",
        display_name="Strike Rotation & Consistency",
        description="Measures ability to rotate strike and avoid non-scoring deliveries (Dot Ball Suppression).",
        applicable_roles=["BATTER", "ALL_ROUNDER", "WICKETKEEPER"],
        associated_metrics=["dot_ball_suppression", "dot_ball_percentage"],
        interpretation="Strike rotation keeps the scoreboard ticking and disrupts bowling plans.",
        required_data_fields=["batter_runs", "extras_type"],
        sample_requirements="Minimum 30 balls faced.",
        limitations="Does not distinguish between defensive blocks and swing-and-misses.",
    ),

    # ==================== BOWLING DIMENSIONS ====================
    "wicket_taking_performance": DimensionRegistryEntry(
        dimension_id="wicket_taking_performance",
        display_name="Wicket-Taking Performance",
        description="Measures breakthrough potential and frequency of dismissing opposing batters.",
        applicable_roles=["BOWLER", "ALL_ROUNDER"],
        associated_metrics=["wickets_taken", "bowling_strike_rate", "bowling_average"],
        interpretation="Core bowling potency; lower balls-per-wicket denotes elite wicket threat.",
        required_data_fields=["is_wicket", "dismissal_kind", "extras_type"],
        sample_requirements="Minimum 3 wickets taken to calculate meaningful bowling average.",
        limitations="Excludes non-bowler wickets (run-outs, retired out).",
    ),
    "run_containment": DimensionRegistryEntry(
        dimension_id="run_containment",
        display_name="Run Containment",
        description="Measures defensive run suppression (Economy Rate and True Economy Rate).",
        applicable_roles=["BOWLER", "ALL_ROUNDER"],
        associated_metrics=["economy_rate", "true_economy_rate"],
        interpretation="Lower economy signifies superior boundary control and run denial per 6 balls.",
        required_data_fields=["batter_runs", "extras_runs", "extras_type"],
        sample_requirements="Minimum 24 legal deliveries (4 overs); 72+ balls for adequate assessment.",
        limitations="Unadjusted economy penalizes specialist death overs bowlers.",
    ),
    "dot_ball_generation": DimensionRegistryEntry(
        dimension_id="dot_ball_generation",
        display_name="Dot-Ball Generation & Pressure",
        description="Evaluates ability to build pressure through consecutive scoreless deliveries.",
        applicable_roles=["BOWLER", "ALL_ROUNDER"],
        associated_metrics=["bowling_dot_ball_percentage"],
        interpretation="Higher dot ball percentage forces opposing batters into high-risk shots.",
        required_data_fields=["batter_runs", "extras_runs", "extras_type"],
        sample_requirements="Minimum 24 legal deliveries.",
        limitations="Does not capture whether dot balls were followed by boundary releases.",
    ),
    "bowling_workload": DimensionRegistryEntry(
        dimension_id="bowling_workload",
        display_name="Bowling Workload & Discipline",
        description="Tracks bowling volume (overs, legal balls) and bowler extras conceded.",
        applicable_roles=["BOWLER", "ALL_ROUNDER"],
        associated_metrics=["legal_balls_bowled", "overs_bowled", "runs_conceded", "extras_conceded"],
        interpretation="Assesses trusted over-allocation by captain and disciplined bowling control.",
        required_data_fields=["extras_type", "extras_runs"],
        sample_requirements="Minimum 1 over bowled.",
        limitations="Volume metric; does not adjust for match conditions.",
    ),
    "boundary_containment": DimensionRegistryEntry(
        dimension_id="boundary_containment",
        display_name="Boundary Suppression",
        description="Evaluates resistance to conceding boundaries (Balls per Boundary Conceded).",
        applicable_roles=["BOWLER", "ALL_ROUNDER"],
        associated_metrics=["balls_per_boundary_conceded", "boundaries_conceded"],
        interpretation="Higher balls per boundary conceded demonstrates effective boundary protection.",
        required_data_fields=["batter_runs", "extras_type"],
        sample_requirements="Minimum 24 legal deliveries.",
        limitations="Does not differentiate between mishits that drop safe and clean strokes.",
    ),

    # ==================== WICKETKEEPER / FIELDING DIMENSIONS ====================
    "wicketkeeping_dismissals": DimensionRegistryEntry(
        dimension_id="wicketkeeping_dismissals",
        display_name="Wicketkeeping Dismissals",
        description="Evaluates direct wicketkeeper dismissals (Catches and Stumpings behind the stumps).",
        applicable_roles=["WICKETKEEPER"],
        associated_metrics=["catches_taken", "stumpings_made"],
        interpretation="Quantifies glovework reliability and wicket assistance.",
        required_data_fields=["fielder_id", "dismissal_kind"],
        sample_requirements="Requires keeper telemetry / fielder tagging in ball-by-ball records.",
        limitations="Frequently unavailable in basic flat delivery scorecards.",
    ),
}


def get_all_evaluation_dimensions() -> list[DimensionRegistryEntry]:
    """Retrieve full catalog of registered evaluation dimensions."""
    return list(EVALUATION_DIMENSION_REGISTRY.values())


def get_dimension_definition(dimension_id: str) -> DimensionRegistryEntry | None:
    """Retrieve metadata entry for a specific evaluation dimension ID."""
    return EVALUATION_DIMENSION_REGISTRY.get(dimension_id)

