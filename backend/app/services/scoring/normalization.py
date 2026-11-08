"""Empirical Cumulative Distribution Function (ECDF) percentile normalization engine."""

from typing import Any
from backend.app.schemas.metrics import MetricDirection
from backend.app.schemas.scoring import NormalizedMetric
from backend.app.services.scoring.base import MINIMUM_COHORT_SIZE, SCORING_ENGINE_VERSION


class ECDFNormalizer:
    """Transforms raw performance metrics into directional percentiles [0.0, 100.0].

    Strictly adheres to docs/SCORING_METHODOLOGY.md Section 4:
    - Higher-is-better: Z_i = (sum(1_{x_j <= x_i}) / M) * 100
    - Lower-is-better: Z_i = (sum(1_{x_j >= x_i}) / M) * 100
    """

    def normalize_cohort_metric(
        self,
        metric_id: str,
        display_name: str,
        directionality: MetricDirection,
        player_values: dict[str, float | int | None],
        cohort_id: str,
    ) -> dict[str, NormalizedMetric]:
        """Normalize a single metric across all players in a cohort using ECDF."""
        # 1. Filter out missing / None values from comparison pool
        valid_pool: list[float] = [
            float(val) for val in player_values.values() if val is not None
        ]
        m = len(valid_pool)

        results: dict[str, NormalizedMetric] = {}

        # 2. Check cohort size adequacy
        if m < MINIMUM_COHORT_SIZE:
            # Inadequate cohort volume for statistical percentiles
            for p_id, raw_val in player_values.items():
                results[p_id] = NormalizedMetric(
                    metric_id=metric_id,
                    display_name=display_name,
                    raw_value=raw_val,
                    directionality=directionality,
                    percentile=50.0,  # Fall back to cohort neutral median
                    cohort_id=cohort_id,
                    cohort_size=m,
                    normalization_method="INSUFFICIENT_COHORT_MEDIAN_FALLBACK",
                )
            return results

        # 3. Compute directional ECDF percentile for each player
        for p_id, raw_val in player_values.items():
            if raw_val is None:
                # Missing value is preserved as None or median fallback with explanation
                results[p_id] = NormalizedMetric(
                    metric_id=metric_id,
                    display_name=display_name,
                    raw_value=None,
                    directionality=directionality,
                    percentile=50.0,
                    cohort_id=cohort_id,
                    cohort_size=m,
                    normalization_method="MISSING_DATA_MEDIAN_FALLBACK",
                )
                continue

            x_i = float(raw_val)

            if directionality == MetricDirection.LOWER_IS_BETTER:
                # Lower value represents superior performance (e.g. Economy, Bowling SR)
                # Count peers who are worse or equal (i.e. x_j >= x_i)
                count_better_or_equal = sum(1 for x_j in valid_pool if x_j >= x_i)
                percentile = round((count_better_or_equal / m) * 100.0, 2)
            else:
                # Higher value represents superior performance (e.g. TSR, Boundary %, Dot Suppression)
                # Count peers who are worse or equal (i.e. x_j <= x_i)
                count_worse_or_equal = sum(1 for x_j in valid_pool if x_j <= x_i)
                percentile = round((count_worse_or_equal / m) * 100.0, 2)

            # Clamp to guarantee [0.0, 100.0]
            clamped_pct = max(0.0, min(100.0, percentile))

            results[p_id] = NormalizedMetric(
                metric_id=metric_id,
                display_name=display_name,
                raw_value=raw_val,
                directionality=directionality,
                percentile=clamped_pct,
                cohort_id=cohort_id,
                cohort_size=m,
                normalization_method="ECDF",
            )

        return results

