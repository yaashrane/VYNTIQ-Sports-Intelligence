"""Evidence-based player role classification system."""

from typing import Any
from backend.app.schemas.evaluation import (
    PlayerRole,
    RoleClassificationResult,
    RoleClassificationStatus,
)
from backend.app.schemas.metrics import SampleSizeInfo
from backend.app.services.evaluation.config import (
    DEFAULT_ROLE_CONFIG,
    RoleClassificationConfig,
)

CANONICAL_SOURCE_ROLE_MAP: dict[str, PlayerRole] = {
    "BATTER": PlayerRole.BATTER,
    "BATSMAN": PlayerRole.BATTER,
    "TOP_ORDER_BATTER": PlayerRole.BATTER,
    "OPENER": PlayerRole.BATTER,
    "BOWLER": PlayerRole.BOWLER,
    "FAST_BOWLER": PlayerRole.BOWLER,
    "SPIN_BOWLER": PlayerRole.BOWLER,
    "SPINNER": PlayerRole.BOWLER,
    "ALL_ROUNDER": PlayerRole.ALL_ROUNDER,
    "ALLROUNDER": PlayerRole.ALL_ROUNDER,
    "BATTING_ALLROUNDER": PlayerRole.ALL_ROUNDER,
    "BOWLING_ALLROUNDER": PlayerRole.ALL_ROUNDER,
    "WICKETKEEPER": PlayerRole.WICKETKEEPER,
    "WICKET_KEEPER": PlayerRole.WICKETKEEPER,
    "WK": PlayerRole.WICKETKEEPER,
    "WICKETKEEPER_BATTER": PlayerRole.WICKETKEEPER,
}


class RoleClassifier:
    """Classifies player cricketing roles using transparent, configurable rules."""

    def __init__(self, config: RoleClassificationConfig | None = None) -> None:
        self.config = config or DEFAULT_ROLE_CONFIG

    def classify_player(
        self,
        player_id: str,
        sample: SampleSizeInfo,
        source_role: str | None = None,
        wicketkeeping_dismissals: int = 0,
    ) -> RoleClassificationResult:
        """Classify a player's role, preserving source metadata and recording supporting evidence."""
        evidence: dict[str, Any] = {
            "balls_faced": sample.balls_faced,
            "batting_innings": sample.batting_innings,
            "legal_balls_bowled": sample.legal_balls_bowled,
            "overs_bowled": sample.overs_bowled,
            "bowling_innings": sample.bowling_innings,
            "matches_played": sample.matches_played,
            "wicketkeeping_dismissals": wicketkeeping_dismissals,
        }
        missing_info: list[str] = []

        # 1. EVALUATE EXPLICIT SOURCE ROLE
        if source_role and str(source_role).strip():
            normalized_source = str(source_role).strip().upper().replace(" ", "_").replace("-", "_")
            canonical_role = CANONICAL_SOURCE_ROLE_MAP.get(normalized_source)

            if canonical_role:
                # Check for direct contradictions against empirical data
                contradiction = self._check_source_contradiction(canonical_role, sample)
                if contradiction:
                    return RoleClassificationResult(
                        player_id=player_id,
                        assigned_role=PlayerRole.UNKNOWN,
                        source_role=source_role,
                        status=RoleClassificationStatus.AMBIGUOUS,
                        classification_method="SOURCE_DATA_CONFLICT",
                        supporting_evidence=evidence,
                        missing_information=[contradiction],
                        confidence="LOW",
                        classification_version=self.config.version,
                    )

                return RoleClassificationResult(
                    player_id=player_id,
                    assigned_role=canonical_role,
                    source_role=source_role,
                    status=RoleClassificationStatus.CONFIRMED_FROM_SOURCE,
                    classification_method="EXPLICIT_SOURCE_RECORD",
                    supporting_evidence=evidence,
                    missing_information=missing_info,
                    confidence="HIGH",
                    classification_version=self.config.version,
                )
            else:
                missing_info.append(f"Unrecognized source role label: '{source_role}'")

        # 2. EVALUATE EMPIRICAL PARTICIPATION EVIDENCE (DATA-DRIVEN CLASSIFICATION)
        total_volume = sample.balls_faced + sample.legal_balls_bowled
        if total_volume == 0:
            return RoleClassificationResult(
                player_id=player_id,
                assigned_role=PlayerRole.UNKNOWN,
                source_role=source_role,
                status=RoleClassificationStatus.INSUFFICIENT_DATA,
                classification_method="ZERO_RECORDED_DELIVERIES",
                supporting_evidence=evidence,
                missing_information=["No balls faced or bowled in analysis window"],
                confidence="NONE",
                classification_version=self.config.version,
            )

        # Wicketkeeper: Strictly requires explicit wicketkeeping indicator (stumpings / catches as keeper)
        if wicketkeeping_dismissals > 0:
            return RoleClassificationResult(
                player_id=player_id,
                assigned_role=PlayerRole.WICKETKEEPER,
                source_role=source_role,
                status=RoleClassificationStatus.CLASSIFIED_FROM_DATA,
                classification_method="WICKETKEEPING_DISMISSAL_EVIDENCE",
                supporting_evidence=evidence,
                missing_information=missing_info,
                confidence="HIGH",
                classification_version=self.config.version,
            )

        # All-Rounder Evaluation: Requires substantial dual participation
        is_all_rounder = (
            sample.balls_faced >= self.config.all_rounder_min_balls_faced
            and sample.legal_balls_bowled >= self.config.all_rounder_min_legal_balls_bowled
        )
        if is_all_rounder:
            return RoleClassificationResult(
                player_id=player_id,
                assigned_role=PlayerRole.ALL_ROUNDER,
                source_role=source_role,
                status=RoleClassificationStatus.CLASSIFIED_FROM_DATA,
                classification_method="DUAL_DISCIPLINE_VOLUME_MET",
                supporting_evidence=evidence,
                missing_information=missing_info,
                confidence="MEDIUM",
                classification_version=self.config.version,
            )

        # Specialist Bowler: Substantial bowling volume, little to no batting volume
        if (
            sample.legal_balls_bowled >= self.config.min_legal_balls_for_bowler
            and sample.balls_faced < self.config.min_balls_faced_for_batter
        ):
            return RoleClassificationResult(
                player_id=player_id,
                assigned_role=PlayerRole.BOWLER,
                source_role=source_role,
                status=RoleClassificationStatus.CLASSIFIED_FROM_DATA,
                classification_method="BOWLING_VOLUME_DOMINANCE",
                supporting_evidence=evidence,
                missing_information=missing_info,
                confidence="MEDIUM",
                classification_version=self.config.version,
            )

        # Specialist Batter: Substantial batting volume, negligible bowling volume (< 12 legal balls)
        if (
            sample.balls_faced >= self.config.min_balls_faced_for_batter
            and sample.legal_balls_bowled < 12
        ):
            return RoleClassificationResult(
                player_id=player_id,
                assigned_role=PlayerRole.BATTER,
                source_role=source_role,
                status=RoleClassificationStatus.CLASSIFIED_FROM_DATA,
                classification_method="BATTING_VOLUME_DOMINANCE",
                supporting_evidence=evidence,
                missing_information=missing_info,
                confidence="MEDIUM",
                classification_version=self.config.version,
            )

        # Insufficient volume to classify
        if (
            sample.balls_faced < self.config.min_balls_faced_for_batter
            and sample.legal_balls_bowled < self.config.min_legal_balls_for_bowler
        ):
            return RoleClassificationResult(
                player_id=player_id,
                assigned_role=PlayerRole.UNKNOWN,
                source_role=source_role,
                status=RoleClassificationStatus.INSUFFICIENT_DATA,
                classification_method="BELOW_MINIMUM_THRESHOLDS",
                supporting_evidence=evidence,
                missing_information=["Sample volume below classification thresholds in both disciplines"],
                confidence="LOW",
                classification_version=self.config.version,
            )

        # If volume is moderate in both but fails strict all-rounder threshold -> AMBIGUOUS
        return RoleClassificationResult(
            player_id=player_id,
            assigned_role=PlayerRole.UNKNOWN,
            source_role=source_role,
            status=RoleClassificationStatus.AMBIGUOUS,
            classification_method="BORDERLINE_PARTICIPATION_SPLIT",
            supporting_evidence=evidence,
            missing_information=["Participation split between batting and bowling does not meet clear specialist or dual criteria"],
            confidence="LOW",
            classification_version=self.config.version,
        )

    def _check_source_contradiction(self, canonical_role: PlayerRole, sample: SampleSizeInfo) -> str | None:
        """Check for severe discrepancy between explicit label and observed volume."""
        # Bowler label but bowled zero deliveries over 3+ matches while facing 50+ balls
        if canonical_role == PlayerRole.BOWLER:
            if sample.matches_played >= 3 and sample.legal_balls_bowled == 0 and sample.balls_faced >= 50:
                return "Source records state BOWLER but player bowled 0 deliveries and faced 50+ balls"

        # Batter label but faced zero balls over 3+ matches while bowling 60+ deliveries
        if canonical_role == PlayerRole.BATTER:
            if sample.matches_played >= 3 and sample.balls_faced == 0 and sample.legal_balls_bowled >= 60:
                return "Source records state BATTER but player faced 0 balls and bowled 60+ deliveries"

        return None
