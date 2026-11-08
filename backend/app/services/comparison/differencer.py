"""Mathematical difference analysis and directional statistical advantage attribution."""

from backend.app.schemas.comparison import MetricComparisonItem
from backend.app.schemas.metrics import MetricDirection


class DifferenceAnalyzer:
    """Computes absolute differences, relative deltas, and favorable candidate attribution."""

    def compare_metric(
        self,
        metric_id: str,
        display_name: str,
        directionality: MetricDirection,
        unit: str,
        player_values: dict[str, float | int | None],
        player_percentiles: dict[str, float | None],
        player_names: dict[str, str],
    ) -> MetricComparisonItem:
        """Compare a single metric across players, determining the favorable candidate respecting directionality."""
        valid_vals = {p_id: float(v) for p_id, v in player_values.items() if v is not None}

        abs_diff: float | None = None
        rel_diff_pct: float | None = None
        favorable_id: str | None = None

        if len(valid_vals) >= 2:
            vals_list = list(valid_vals.values())
            p_ids = list(valid_vals.keys())

            # For 2 players, compute exact difference
            if len(valid_vals) == 2:
                v1, v2 = vals_list[0], vals_list[1]
                abs_diff = round(abs(v1 - v2), 2)
                base = min(abs(v1), abs(v2))
                if base > 0:
                    rel_diff_pct = round((abs_diff / base) * 100.0, 1)

            # Determine favorable player based on directionality
            if directionality == MetricDirection.HIGHER_IS_BETTER:
                max_val = max(valid_vals.values())
                # Ensure no tie for the max value
                leaders = [p_id for p_id, v in valid_vals.items() if v == max_val]
                if len(leaders) == 1:
                    favorable_id = leaders[0]
            elif directionality == MetricDirection.LOWER_IS_BETTER:
                min_val = min(valid_vals.values())
                leaders = [p_id for p_id, v in valid_vals.items() if v == min_val]
                if len(leaders) == 1:
                    favorable_id = leaders[0]

        return MetricComparisonItem(
            metric_id=metric_id,
            display_name=display_name,
            directionality=directionality,
            unit=unit,
            player_values=player_values,
            player_percentiles=player_percentiles,
            absolute_difference=abs_diff,
            relative_difference_pct=rel_diff_pct,
            favorable_player_id=favorable_id,
            favorable_player_name=player_names.get(favorable_id) if favorable_id else None,
        )

