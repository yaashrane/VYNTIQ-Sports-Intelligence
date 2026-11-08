"""Composite calculation engine for VYNTIQ Overall Rating (VOR)."""

from typing import Any
from backend.app.schemas.evaluation import PlayerRole
from backend.app.schemas.metrics import SampleSizeInfo
from backend.app.schemas.scoring import (
    DimensionScore,
    NormalizedMetric,
    ReliabilityStatus,
)
from backend.app.services.scoring.base import COHORT_MEDIAN_SCORE, SCORING_ENGINE_VERSION
from backend.app.services.scoring.reliability import (
    BATTING_N_MIN,
    BOWLING_N_MIN,
    BayesianReliabilityAssessor,
)
from backend.app.services.scoring.weights import (
    DEFAULT_WEIGHT_CONFIG,
    RoleWeightConfiguration,
)


class VORCompositeCalculator:
    """Computes transparent, reliability-adjusted VOR scores.

    Strictly implements docs/SCORING_METHODOLOGY.md Section 6:
    VOR = 50.0 + C(N) * (sum(w_k * Z_k) - 50.0)
    """

    def __init__(
        self,
        weight_config: RoleWeightConfiguration | None = None,
        reliability_assessor: BayesianReliabilityAssessor | None = None,
    ) -> None:
        self.weights = weight_config or DEFAULT_WEIGHT_CONFIG
        self.reliability = reliability_assessor or BayesianReliabilityAssessor()

    def compute_batter_vor(
        self,
        normalized_dimensions: dict[str, list[NormalizedMetric]],
        sample: SampleSizeInfo,
    ) -> tuple[float, float, float, ReliabilityStatus, dict[str, DimensionScore]]:
        """Calculate VOR for a specialist batter."""
        # 1. Compute dimension scores from normalized metrics
        active_dims = list(normalized_dimensions.keys())
        norm_weights = self.weights.get_normalized_weights(self.weights.batting_weights, active_dims)

        dim_scores: dict[str, DimensionScore] = {}
        raw_composite = 0.0

        for dim_id, metrics in normalized_dimensions.items():
            if not metrics:
                continue
            # Dimension score is average of normalized metric percentiles in that dimension
            dim_val = round(sum(m.percentile for m in metrics) / len(metrics), 2)
            w = norm_weights.get(dim_id, 0.0)
            contribution = round(dim_val * w, 2)
            raw_composite += contribution

            dim_scores[dim_id] = DimensionScore(
                dimension_id=dim_id,
                dimension_name=metrics[0].display_name if metrics else dim_id,
                dimension_score=dim_val,
                weight=w,
                contribution_points=contribution,
                metrics=metrics,
            )

        raw_composite = round(raw_composite, 2)

        # 2. Bayesian Reliability Shrinkage
        c_factor, rel_status = self.reliability.calculate_batting_reliability(sample.balls_faced)
        if rel_status == ReliabilityStatus.INSUFFICIENT_SAMPLE:
            # Regress fully to cohort median (50.0) for leaderboard quarantine
            vor_score = COHORT_MEDIAN_SCORE
        else:
            vor_score = round(COHORT_MEDIAN_SCORE + c_factor * (raw_composite - COHORT_MEDIAN_SCORE), 2)

        return (vor_score, raw_composite, c_factor, rel_status, dim_scores)

    def compute_bowler_vor(
        self,
        normalized_dimensions: dict[str, list[NormalizedMetric]],
        sample: SampleSizeInfo,
    ) -> tuple[float, float, float, ReliabilityStatus, dict[str, DimensionScore]]:
        """Calculate VOR for a specialist bowler."""
        active_dims = list(normalized_dimensions.keys())
        norm_weights = self.weights.get_normalized_weights(self.weights.bowling_weights, active_dims)

        dim_scores: dict[str, DimensionScore] = {}
        raw_composite = 0.0

        for dim_id, metrics in normalized_dimensions.items():
            if not metrics:
                continue
            dim_val = round(sum(m.percentile for m in metrics) / len(metrics), 2)
            w = norm_weights.get(dim_id, 0.0)
            contribution = round(dim_val * w, 2)
            raw_composite += contribution

            dim_scores[dim_id] = DimensionScore(
                dimension_id=dim_id,
                dimension_name=metrics[0].display_name if metrics else dim_id,
                dimension_score=dim_val,
                weight=w,
                contribution_points=contribution,
                metrics=metrics,
            )

        raw_composite = round(raw_composite, 2)

        # Bayesian Reliability Shrinkage
        c_factor, rel_status = self.reliability.calculate_bowling_reliability(sample.legal_balls_bowled)
        if rel_status == ReliabilityStatus.INSUFFICIENT_SAMPLE:
            vor_score = COHORT_MEDIAN_SCORE
        else:
            vor_score = round(COHORT_MEDIAN_SCORE + c_factor * (raw_composite - COHORT_MEDIAN_SCORE), 2)

        return (vor_score, raw_composite, c_factor, rel_status, dim_scores)

    def compute_all_rounder_vor(
        self,
        bat_vor: float,
        bowl_vor: float,
        raw_bat: float,
        raw_bowl: float,
        c_factor: float,
        rel_status: ReliabilityStatus,
        sample: SampleSizeInfo,
        all_dim_scores: dict[str, DimensionScore],
    ) -> tuple[float, float, float, dict[str, float]]:
        """Calculate dual-threat VOR for an All-Rounder (SCORING_METHODOLOGY Section 7).

        Formula:
        VOR_ar = (alpha * VOR_bat + (1 - alpha) * VOR_bowl) + Dual_Bonus
        Dual_Bonus = 5.0 * (min(VOR_bat, VOR_bowl) / 50.0) if both meet N_min
        """
        alpha = self.weights.all_rounder_alpha
        base_blended = (alpha * bat_vor) + ((1.0 - alpha) * bowl_vor)
        raw_blended = round((alpha * raw_bat) + ((1.0 - alpha) * raw_bowl), 2)

        # Dual utility bonus only awarded if BOTH disciplines meet N_min
        meets_dual_n_min = sample.balls_faced >= BATTING_N_MIN and sample.legal_balls_bowled >= BOWLING_N_MIN
        if meets_dual_n_min and rel_status != ReliabilityStatus.INSUFFICIENT_SAMPLE:
            min_sub_score = min(bat_vor, bowl_vor)
            dual_bonus = round(self.weights.all_rounder_dual_bonus_max * (min_sub_score / COHORT_MEDIAN_SCORE), 2)
        else:
            dual_bonus = 0.0

        vor_ar = round(base_blended + dual_bonus, 2)
        components = {
            "batting_vor": bat_vor,
            "bowling_vor": bowl_vor,
            "raw_batting": raw_bat,
            "raw_bowling": raw_bowl,
            "dual_bonus": dual_bonus,
        }
        return (vor_ar, raw_blended, dual_bonus, components)

