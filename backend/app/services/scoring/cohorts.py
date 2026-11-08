"""Cohort construction, isolation, and peer group partitioning."""

from backend.app.schemas.evaluation import PlayerEvaluationResponse, PlayerRole
from backend.app.services.scoring.base import MINIMUM_COHORT_SIZE


class CohortManager:
    """Partitions and validates compatible player peer groups for fair percentile normalization."""

    def partition_cohorts(
        self,
        players: list[PlayerEvaluationResponse],
        competition: str = "COMPETITION",
        season: str = "ALL",
    ) -> dict[str, list[PlayerEvaluationResponse]]:
        """Group players strictly by playing role and tournament context to avoid cross-role contamination."""
        cohorts: dict[str, list[PlayerEvaluationResponse]] = {
            PlayerRole.BATTER.value: [],
            PlayerRole.BOWLER.value: [],
            PlayerRole.ALL_ROUNDER.value: [],
            PlayerRole.WICKETKEEPER.value: [],
        }

        for p in players:
            role_key = p.role.assigned_role.value
            if role_key in cohorts:
                cohorts[role_key].append(p)
            elif p.role.assigned_role == PlayerRole.UNKNOWN:
                # Unknown roles are not forced into specialist comparison cohorts
                continue

        return cohorts

    def build_cohort_id(self, role: str, competition: str = "COMPETITION", season: str = "ALL") -> str:
        """Create a deterministic, reproducible cohort identifier string."""
        return f"COHORT_{role.upper()}_{competition.upper()}_{season.upper()}"

    def validate_cohort_size(self, cohort: list[PlayerEvaluationResponse]) -> bool:
        """Verify whether cohort meets minimum size for statistical ECDF normalization."""
        return len(cohort) >= MINIMUM_COHORT_SIZE
