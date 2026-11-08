"""Eligibility engine evaluating candidate players against competition-specific criteria."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from backend.app.models.cricket import Player
from backend.app.schemas.scoring import PlayerScoreResult
from backend.app.schemas.workspace import (
    CompetitionConfigResponse,
    EligibilityStatus,
)


@dataclass
class PlayerEligibilityAssessment:
    """Detailed evaluation result of a player against competition criteria."""

    player_id: str
    is_eligible: bool
    status: EligibilityStatus
    exclusion_reasons: list[str] = field(default_factory=list)


class EligibilityEngine:
    """Evaluates players against competition-configured eligibility rules without conflating performance scores."""

    @staticmethod
    def evaluate_player(
        player_score: PlayerScoreResult,
        config: CompetitionConfigResponse,
        player_record: Player | None = None,
    ) -> PlayerEligibilityAssessment:
        """Evaluate a single scored player against competition rules, recording all exclusion reasons."""
        exclusion_reasons: list[str] = []
        assigned_role = (
            player_score.role.value
            if hasattr(player_score.role, "value")
            else str(player_score.role)
        )

        # 1. Target Role Eligibility
        target_roles = [r.upper() for r in config.target_roles]
        if assigned_role.upper() not in target_roles:
            exclusion_reasons.append(
                f"Assigned role '{assigned_role}' is not in configured competition roles: {target_roles}"
            )

        # 2. Master Eligibility Record Check
        if player_record is not None and not player_record.is_eligible:
            exclusion_reasons.append(
                "Player master record has explicit eligibility flag set to False"
            )

        # 3. Age Eligibility Criteria (Optional)
        if config.age_criteria:
            crit = config.age_criteria
            if crit.min_age is not None or crit.max_age is not None:
                if player_record is None or player_record.dob is None:
                    exclusion_reasons.append(
                        "Player date of birth is unavailable for competition age verification"
                    )
                else:
                    cutoff = (
                        datetime.fromisoformat(crit.age_cutoff_date).date()
                        if crit.age_cutoff_date
                        else datetime.now(timezone.utc).date()
                    )
                    dob: date = player_record.dob
                    # Accurate age calculation accounting for leap years and anniversary
                    age = (
                        cutoff.year
                        - dob.year
                        - ((cutoff.month, cutoff.day) < (dob.month, dob.day))
                    )

                    if crit.min_age is not None and age < crit.min_age:
                        exclusion_reasons.append(
                            f"Player age ({age} years) is below minimum age requirement of {crit.min_age} years"
                        )
                    if crit.max_age is not None and age > crit.max_age:
                        exclusion_reasons.append(
                            f"Player age ({age} years) exceeds maximum age requirement of {crit.max_age} years"
                        )

        # 4. Minimum Participation Workload Requirements (Optional)
        if config.participation_criteria:
            part = config.participation_criteria
            sample = player_score.sample_size

            if part.min_balls_faced is not None and assigned_role in {"BATTER", "ALL_ROUNDER", "WICKETKEEPER"}:
                if sample.balls_faced < part.min_balls_faced:
                    exclusion_reasons.append(
                        f"Balls faced ({sample.balls_faced}) is below minimum requirement of {part.min_balls_faced}"
                    )

            if part.min_legal_balls_bowled is not None and assigned_role in {"BOWLER", "ALL_ROUNDER"}:
                if sample.legal_balls_bowled < part.min_legal_balls_bowled:
                    exclusion_reasons.append(
                        f"Legal balls bowled ({sample.legal_balls_bowled}) is below minimum requirement of {part.min_legal_balls_bowled}"
                    )

        # 5. Custom Eligibility Rules (e.g. Nationality Restrictions)
        if config.custom_eligibility_rules:
            allowed_nats = config.custom_eligibility_rules.get("allowed_nationalities")
            if allowed_nats and isinstance(allowed_nats, list):
                player_nat = player_record.nationality if player_record else None
                if not player_nat or player_nat.upper() not in [n.upper() for n in allowed_nats]:
                    exclusion_reasons.append(
                        f"Player nationality '{player_nat}' is not in allowed competition nationalities: {allowed_nats}"
                    )

        is_eligible = len(exclusion_reasons) == 0
        status = EligibilityStatus.ELIGIBLE if is_eligible else EligibilityStatus.EXCLUDED

        return PlayerEligibilityAssessment(
            player_id=player_score.player_id,
            is_eligible=is_eligible,
            status=status,
            exclusion_reasons=exclusion_reasons,
        )

