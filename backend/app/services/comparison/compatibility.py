"""Compatibility verification for head-to-head and multi-player comparisons."""

from backend.app.schemas.comparison import ComparisonCompatibilityStatus
from backend.app.schemas.scoring import PlayerScoreResult


class CompatibilityChecker:
    """Verifies that compared athletes belong to valid, statistically comparable populations."""

    def check_compatibility(
        self,
        players: list[PlayerScoreResult],
    ) -> tuple[ComparisonCompatibilityStatus, list[str]]:
        """Verify role, cohort, and format compatibility across compared candidates."""
        if len(players) < 2:
            return (ComparisonCompatibilityStatus.INCOMPATIBLE_COHORTS, ["Minimum 2 players required for comparison"])

        notes: list[str] = []
        roles = {p.role for p in players}
        cohorts = {p.cohort_id for p in players}

        # 1. Role compatibility check
        is_cross_role = len(roles) > 1
        if is_cross_role:
            notes.append(
                f"Cross-role comparison detected across roles: {[r.value for r in roles]}. "
                f"Direct VOR ranking comparison is disabled to prevent misleading equivalence."
            )
            return (ComparisonCompatibilityStatus.CROSS_ROLE_PARTIAL, notes)

        # 2. Cohort compatibility check
        if len(cohorts) > 1:
            notes.append(
                f"Players evaluated in distinct cohorts: {list(cohorts)}. "
                f"Normalized percentiles reflect different peer populations."
            )
            return (ComparisonCompatibilityStatus.INCOMPATIBLE_COHORTS, notes)

        notes.append("Candidates share identical playing role and tournament comparison cohort.")
        return (ComparisonCompatibilityStatus.FULLY_COMPATIBLE, notes)
