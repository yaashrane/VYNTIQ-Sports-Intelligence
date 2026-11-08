"""Transparent factor attribution and audit explanations for VOR player scores."""

from backend.app.schemas.scoring import DimensionScore, ReliabilityStatus, ScoreExplanation


class ScoreExplainer:
    """Generates deterministic, audit-ready explanations decomposing VOR ratings."""

    def explain_score(
        self,
        vor: float,
        raw_composite: float,
        reliability_factor: float,
        reliability_status: ReliabilityStatus,
        dimension_scores: dict[str, DimensionScore],
        role_name: str,
        cohort_id: str,
    ) -> ScoreExplanation:
        """Decompose final rating into strengths, drag factors, and reliability impact."""
        # Sort dimensions by their score
        sorted_dims = sorted(
            dimension_scores.values(),
            key=lambda d: d.dimension_score,
            reverse=True,
        )

        top_strengths: list[str] = []
        drag_factors: list[str] = []
        missing_or_limited: list[str] = []

        for d in sorted_dims:
            if d.dimension_score >= 60.0:
                top_strengths.append(f"{d.dimension_name} ({d.dimension_score:.1f}th percentile)")
            elif d.dimension_score <= 40.0:
                drag_factors.append(f"{d.dimension_name} ({d.dimension_score:.1f}th percentile)")

            # Check if any metrics inside had missing or zero sample
            for m in d.metrics:
                if m.raw_value is None or "FALLBACK" in m.normalization_method:
                    missing_or_limited.append(f"{m.display_name} in {d.dimension_name}")

        # Summary narrative
        if reliability_status == ReliabilityStatus.INSUFFICIENT_SAMPLE:
            summary = (
                f"{role_name} evaluated in cohort '{cohort_id}'. Raw unregressed score of {raw_composite:.1f} "
                f"was quarantined due to micro-sample volume below minimum thresholds. "
                f"Rating regressed to cohort median (50.0)."
            )
        elif reliability_status == ReliabilityStatus.RELIABILITY_DISCOUNTED:
            summary = (
                f"{role_name} evaluated in cohort '{cohort_id}' with VOR rating of {vor:.1f}. "
                f"Performance supported by provisional sample volume (Reliability Factor C = {reliability_factor:.2f}), "
                f"regressing raw performance ({raw_composite:.1f}) toward cohort median (50.0)."
            )
        else:
            summary = (
                f"{role_name} evaluated in cohort '{cohort_id}' with full sample reliability (C = 1.0). "
                f"Achieved VOR rating of {vor:.1f} across {len(dimension_scores)} evaluation dimensions."
            )

        return ScoreExplanation(
            final_vor=vor,
            raw_composite=raw_composite,
            reliability_factor=reliability_factor,
            reliability_status=reliability_status,
            top_strengths=top_strengths[:3],
            drag_factors=drag_factors[:3],
            missing_or_limited_dimensions=list(set(missing_or_limited)),
            summary_text=summary,
        )
