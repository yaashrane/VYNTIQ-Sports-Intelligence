"""Configurable thresholds and rules for player role classification and sample adequacy.

All thresholds defined herein are provisional, versioned engineering parameters
designed for domain inspection during competition discovery and exploratory analysis.
They are deliberately decoupled from core calculation functions.
"""

from pydantic import BaseModel

CLASSIFICATION_VERSION: str = "1.0.0"


class RoleClassificationConfig(BaseModel):
    """Provisional heuristics for classifying player roles from participation evidence."""

    # Version identifier
    version: str = CLASSIFICATION_VERSION

    # Batter thresholds
    # Minimum balls faced across matches to be classified as a primary batter when source role is missing
    min_balls_faced_for_batter: int = 30
    # Average balls faced per match to qualify as specialist batter
    min_balls_per_match_batter: float = 6.0

    # Bowler thresholds
    # Minimum legal balls bowled across matches (36 balls = 6 overs)
    min_legal_balls_for_bowler: int = 36
    # Average overs bowled per match to qualify as specialist bowler (1.5 overs = 9 balls)
    min_legal_balls_per_match_bowler: float = 9.0

    # All-Rounder dual-qualification thresholds:
    # A player must demonstrate meaningful, regular participation in BOTH disciplines
    # Occasional part-time bowling (e.g. 1 over in 5 matches) strictly fails this requirement
    all_rounder_min_balls_faced: int = 36
    all_rounder_min_legal_balls_bowled: int = 48  # 8 overs
    all_rounder_min_bat_ratio: float = 0.35  # Participated as batter in at least 35% of player's matches
    all_rounder_min_bowl_ratio: float = 0.35  # Bowled in at least 35% of player's matches

    # Sample Adequacy Thresholds (aligned with docs/SCORING_METHODOLOGY.md Section 5)
    # Batting
    batting_adequate_balls: int = 60
    batting_limited_balls: int = 20
    # Bowling (72 balls = 12 overs; 24 balls = 4 overs)
    bowling_adequate_balls: int = 72
    bowling_limited_balls: int = 24


# Default singleton instance for runtime use
DEFAULT_ROLE_CONFIG = RoleClassificationConfig()
