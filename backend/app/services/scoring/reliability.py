"""Bayesian reliability adjustment and sample shrinkage modeling."""

from backend.app.schemas.evaluation import PlayerRole
from backend.app.schemas.metrics import SampleSizeInfo
from backend.app.schemas.scoring import ReliabilityStatus

RELIABILITY_VERSION: str = "1.0.0"

# Thresholds strictly adhering to docs/SCORING_METHODOLOGY.md Section 5
BATTING_N_MIN: int = 60
BATTING_N_FULL: int = 180
BATTING_K: float = BATTING_N_MIN / 2.0  # 30.0

BOWLING_N_MIN: int = 72  # 12 overs
BOWLING_N_FULL: int = 180  # 30 overs
BOWLING_K: float = BOWLING_N_MIN / 2.0  # 36.0


class BayesianReliabilityAssessor:
    """Computes continuous Bayesian reliability shrinkage factor C(N) in (0, 1].

    Formula (docs/SCORING_METHODOLOGY.md Section 5.2):
    - If N < N_min: C(N) = 0.0, status = INSUFFICIENT_SAMPLE (Quarantined)
    - If N_min <= N < N_full: C(N) = N / (N + K), status = RELIABILITY_DISCOUNTED
    - If N >= N_full: C(N) = 1.0, status = ADEQUATE
    """

    def calculate_batting_reliability(self, balls_faced: int) -> tuple[float, ReliabilityStatus]:
        """Compute reliability discount factor C(N) for batting."""
        if balls_faced < BATTING_N_MIN:
            return (0.0, ReliabilityStatus.INSUFFICIENT_SAMPLE)
        if balls_faced >= BATTING_N_FULL:
            return (1.0, ReliabilityStatus.ADEQUATE)

        c_val = round(balls_faced / (balls_faced + BATTING_K), 4)
        return (c_val, ReliabilityStatus.RELIABILITY_DISCOUNTED)

    def calculate_bowling_reliability(self, legal_balls_bowled: int) -> tuple[float, ReliabilityStatus]:
        """Compute reliability discount factor C(N) for bowling."""
        if legal_balls_bowled < BOWLING_N_MIN:
            return (0.0, ReliabilityStatus.INSUFFICIENT_SAMPLE)
        if legal_balls_bowled >= BOWLING_N_FULL:
            return (1.0, ReliabilityStatus.ADEQUATE)

        c_val = round(legal_balls_bowled / (legal_balls_bowled + BOWLING_K), 4)
        return (c_val, ReliabilityStatus.RELIABILITY_DISCOUNTED)

    def calculate_player_reliability(
        self,
        role: PlayerRole,
        sample: SampleSizeInfo,
    ) -> tuple[float, ReliabilityStatus]:
        """Determine applicable reliability factor based on player role and participation volume."""
        if role == PlayerRole.BATTER:
            return self.calculate_batting_reliability(sample.balls_faced)
        elif role == PlayerRole.BOWLER:
            return self.calculate_bowling_reliability(sample.legal_balls_bowled)
        elif role == PlayerRole.ALL_ROUNDER:
            c_bat, stat_bat = self.calculate_batting_reliability(sample.balls_faced)
            c_bowl, stat_bowl = self.calculate_bowling_reliability(sample.legal_balls_bowled)

            # If either discipline fails minimum volume, player is quarantined from elite all-rounder ranking
            if stat_bat == ReliabilityStatus.INSUFFICIENT_SAMPLE or stat_bowl == ReliabilityStatus.INSUFFICIENT_SAMPLE:
                return (0.0, ReliabilityStatus.INSUFFICIENT_SAMPLE)

            # Weighted combined reliability factor
            combined_c = round(0.5 * (c_bat + c_bowl), 4)
            status = ReliabilityStatus.ADEQUATE if combined_c >= 1.0 else ReliabilityStatus.RELIABILITY_DISCOUNTED
            return (combined_c, status)
        elif role == PlayerRole.WICKETKEEPER:
            return self.calculate_batting_reliability(sample.balls_faced)
        else:  # UNKNOWN
            return (0.0, ReliabilityStatus.INSUFFICIENT_SAMPLE)

