"""Sample volume adequacy and statistical reliability qualification."""

from backend.app.schemas.evaluation import DisciplineSampleAdequacy, PlayerRole, SampleAdequacyStatus
from backend.app.schemas.metrics import SampleSizeInfo
from backend.app.services.evaluation.config import DEFAULT_ROLE_CONFIG, RoleClassificationConfig


class SampleAdequacyEvaluator:
    """Evaluates whether observation volume is sufficient for statistical reliability.

    STRICT PRINCIPLE:
    Keeps sample volume strictly separated from performance.
    A small sample is never equated with poor skill, nor a large sample with elite skill.
    """

    def __init__(self, config: RoleClassificationConfig | None = None) -> None:
        self.config = config or DEFAULT_ROLE_CONFIG

    def assess_adequacy(
        self,
        role: PlayerRole,
        sample: SampleSizeInfo,
    ) -> DisciplineSampleAdequacy:
        """Categorize sample adequacy across batting, bowling, and overall role expectations."""
        # 1. Batting sample adequacy
        if role == PlayerRole.BOWLER and sample.balls_faced < self.config.batting_limited_balls:
            batting_status = SampleAdequacyStatus.NOT_APPLICABLE
        elif sample.balls_faced >= self.config.batting_adequate_balls:
            batting_status = SampleAdequacyStatus.ADEQUATE
        elif sample.balls_faced >= self.config.batting_limited_balls:
            batting_status = SampleAdequacyStatus.LIMITED
        else:
            batting_status = SampleAdequacyStatus.INSUFFICIENT

        # 2. Bowling sample adequacy
        if role in (PlayerRole.BATTER, PlayerRole.WICKETKEEPER) and sample.legal_balls_bowled < self.config.bowling_limited_balls:
            bowling_status = SampleAdequacyStatus.NOT_APPLICABLE
        elif sample.legal_balls_bowled >= self.config.bowling_adequate_balls:
            bowling_status = SampleAdequacyStatus.ADEQUATE
        elif sample.legal_balls_bowled >= self.config.bowling_limited_balls:
            bowling_status = SampleAdequacyStatus.LIMITED
        else:
            bowling_status = SampleAdequacyStatus.INSUFFICIENT

        # 3. Overall role adequacy synthesis
        if role == PlayerRole.BATTER:
            overall_status = batting_status
            summary = f"Batting sample: {sample.balls_faced} balls ({batting_status.value}). Bowling not applicable."
        elif role == PlayerRole.BOWLER:
            overall_status = bowling_status
            summary = f"Bowling sample: {sample.legal_balls_bowled} balls ({bowling_status.value}). Batting not applicable."
        elif role == PlayerRole.ALL_ROUNDER:
            # All-rounder requires dual reliability
            order = {
                SampleAdequacyStatus.INSUFFICIENT: 0,
                SampleAdequacyStatus.LIMITED: 1,
                SampleAdequacyStatus.ADEQUATE: 2,
                SampleAdequacyStatus.NOT_APPLICABLE: 0,
            }
            min_level = min(order[batting_status], order[bowling_status])
            rev_order = {0: SampleAdequacyStatus.INSUFFICIENT, 1: SampleAdequacyStatus.LIMITED, 2: SampleAdequacyStatus.ADEQUATE}
            overall_status = rev_order[min_level]
            summary = (
                f"Dual discipline assessment: Batting {batting_status.value} ({sample.balls_faced} balls), "
                f"Bowling {bowling_status.value} ({sample.legal_balls_bowled} balls). "
                f"Overall: {overall_status.value}."
            )
        elif role == PlayerRole.WICKETKEEPER:
            overall_status = batting_status
            summary = f"Wicketkeeper batting sample: {sample.balls_faced} balls ({batting_status.value})."
        else:  # UNKNOWN
            if batting_status == SampleAdequacyStatus.ADEQUATE or bowling_status == SampleAdequacyStatus.ADEQUATE:
                overall_status = SampleAdequacyStatus.LIMITED
            else:
                overall_status = SampleAdequacyStatus.INSUFFICIENT
            summary = "Unclassified player role; sample volume fragmented across disciplines."

        return DisciplineSampleAdequacy(
            batting=batting_status,
            bowling=bowling_status,
            overall=overall_status,
            summary=summary,
        )
