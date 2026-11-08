"""Versioned weight configurations and presets for VOR dimension aggregation."""

from pydantic import BaseModel, Field

WEIGHT_CONFIG_VERSION: str = "1.0.0"

# Approved role presets from docs/SCORING_METHODOLOGY.md Section 6.1
DEFAULT_BATTING_WEIGHTS: dict[str, float] = {
    "scoring_efficiency": 0.25,      # TSR / Strike Rate
    "boundary_contribution": 0.25,   # Boundary % and Balls per Boundary
    "dismissal_resistance": 0.15,    # Balls per Dismissal / Average
    "consistency": 0.15,             # Dot Ball Suppression
    "scoring_output": 0.10,          # Total Runs off the bat
    "phase_adaptability": 0.10,      # Phase performance distribution
}

DEFAULT_BOWLING_WEIGHTS: dict[str, float] = {
    "run_containment": 0.25,          # TER / Economy Rate
    "wicket_taking_performance": 0.25,# Bowling Strike Rate / Wickets
    "dot_ball_generation": 0.20,      # Bowling Dot-Ball %
    "boundary_containment": 0.15,     # Balls per Boundary Conceded
    "bowling_workload": 0.10,         # Legal Balls / Overs Bowled
    "tactical_discipline": 0.05,      # Extras Control
}


class RoleWeightConfiguration(BaseModel):
    """Centralized, versioned weights for role composite calculation."""

    version: str = WEIGHT_CONFIG_VERSION
    batting_weights: dict[str, float] = Field(default_factory=lambda: dict(DEFAULT_BATTING_WEIGHTS))
    bowling_weights: dict[str, float] = Field(default_factory=lambda: dict(DEFAULT_BOWLING_WEIGHTS))
    all_rounder_alpha: float = 0.50  # Balanced role bias between batting and bowling
    all_rounder_dual_bonus_max: float = 5.0  # Maximum dual-utility bonus points

    def get_normalized_weights(self, role_weights: dict[str, float], active_dimensions: list[str]) -> dict[str, float]:
        """Normalize active dimension weights so they sum strictly to 1.0.

        Guarantees mathematical integrity even when an optional dimension is omitted.
        """
        filtered = {dim: role_weights.get(dim, 0.0) for dim in active_dimensions if dim in role_weights}
        total = sum(filtered.values())

        if total <= 0:
            # Equal distribution if all weights are zero or missing
            eq = round(1.0 / len(active_dimensions), 4) if active_dimensions else 1.0
            return {dim: eq for dim in active_dimensions}

        return {dim: round(w / total, 4) for dim, w in filtered.items()}


# Default singleton instance
DEFAULT_WEIGHT_CONFIG = RoleWeightConfiguration()

