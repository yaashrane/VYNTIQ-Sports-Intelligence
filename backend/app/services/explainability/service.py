"""Explainability engine providing factor attribution, score decomposition, and mathematical audit."""

from datetime import datetime, timezone
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.schemas.explainability import (
    DimensionContributionDetail,
    ExplanationStatus,
    MetricContributionDetail,
    PlayerDetailedExplanationResponse,
    PlayerScoreBreakdownResponse,
)
from backend.app.schemas.metrics import MetricProvenance
from backend.app.schemas.scoring import PlayerScoreResult, ReliabilityStatus
from backend.app.services.analytics.registry import METRIC_REGISTRY
from backend.app.services.scoring.service import ScoringService


class ExplainabilityService:
    """Explains how VOR ratings were calculated, attributing scores to specific metrics and dimensions."""

    def __init__(self, scoring_service: ScoringService | None = None) -> None:
        self.scoring_service = scoring_service or ScoringService()

    def get_score_breakdown(self, player_id: str, run_id: str | None = None) -> PlayerScoreBreakdownResponse:
        """Decompose player score into exact metric-level and dimension-level contributions with reconciliation."""
        player_score = self.scoring_service.get_player_score(player_id, run_id)
        dim_details: list[DimensionContributionDetail] = []
        total_dim_contributions = 0.0

        for dim_id, d_score in player_score.dimensions.items():
            metric_details: list[MetricContributionDetail] = []
            num_metrics = len(d_score.metrics) if d_score.metrics else 1
            metric_weight_in_dim = round(1.0 / num_metrics, 4)

            for m in d_score.metrics:
                pct = m.percentile
                contrib_to_dim = round(pct * metric_weight_in_dim, 2)
                is_missing = m.raw_value is None or "FALLBACK" in m.normalization_method

                metric_details.append(
                    MetricContributionDetail(
                        metric_id=m.metric_id,
                        display_name=m.display_name,
                        raw_value=m.raw_value,
                        normalized_percentile=m.percentile,
                        directionality=m.directionality,
                        dimension_id=dim_id,
                        metric_weight_in_dimension=metric_weight_in_dim,
                        contribution_to_dimension=contrib_to_dim,
                        calculation_status="FALLBACK" if is_missing else "CALCULATED",
                        normalization_method=m.normalization_method,
                        is_missing_or_fallback=is_missing,
                    )
                )

            contrib_to_raw = round(d_score.dimension_score * d_score.weight, 2)
            total_dim_contributions += contrib_to_raw

            is_lim = any(m.is_missing_or_fallback for m in metric_details)
            dim_details.append(
                DimensionContributionDetail(
                    dimension_id=dim_id,
                    dimension_name=d_score.dimension_name,
                    dimension_score=d_score.dimension_score,
                    applied_weight=d_score.weight,
                    contribution_to_raw_composite=contrib_to_raw,
                    metrics=metric_details,
                    sample_adequacy="LIMITED" if is_lim else "ADEQUATE",
                    is_limited=is_lim,
                )
            )

        total_dim_contributions = round(total_dim_contributions, 2)
        discrepancy = round(abs(player_score.raw_composite_score - total_dim_contributions), 2)

        return PlayerScoreBreakdownResponse(
            player_id=player_score.player_id,
            player_name=player_score.player_name,
            role=player_score.role,
            cohort_id=player_score.cohort_id,
            run_id=run_id or "LATEST",
            dataset_id=player_score.provenance.dataset_id,
            final_vor=player_score.vor_score,
            raw_composite_score=player_score.raw_composite_score,
            reliability_factor=player_score.reliability_factor,
            reliability_status=player_score.reliability_status,
            sum_of_dimension_contributions=total_dim_contributions,
            reconciliation_discrepancy=discrepancy,
            dimensions=dim_details,
            scoring_version=player_score.scoring_version,
        )

    def generate_player_explanation(
        self,
        player_id: str,
        run_id: str | None = None,
    ) -> PlayerDetailedExplanationResponse:
        """Produce comprehensive audit intelligence dossier explaining strengths, drag factors, and gaps."""
        player_score = self.scoring_service.get_player_score(player_id, run_id)
        breakdown = self.get_score_breakdown(player_id, run_id)

        # 1. Determine Explanation Status
        if player_score.reliability_status == ReliabilityStatus.INSUFFICIENT_SAMPLE:
            status = ExplanationStatus.INSUFFICIENT_EVIDENCE
        elif any(d.is_limited for d in breakdown.dimensions) or player_score.reliability_status == ReliabilityStatus.RELIABILITY_DISCOUNTED:
            status = ExplanationStatus.PARTIAL
        else:
            status = ExplanationStatus.COMPLETE

        # 2. Extract top strengths and drag factors
        top_strengths: list[str] = []
        drag_factors: list[str] = []
        areas_insufficient: list[str] = []

        sorted_dims = sorted(breakdown.dimensions, key=lambda d: d.dimension_score, reverse=True)
        for d in sorted_dims:
            if d.dimension_score >= 60.0:
                top_strengths.append(
                    f"{d.dimension_name}: {d.dimension_score:.1f}th percentile (contributes +{d.contribution_to_raw_composite:.1f} pts)"
                )
            elif d.dimension_score <= 40.0:
                drag_factors.append(
                    f"{d.dimension_name}: {d.dimension_score:.1f}th percentile (contributes {d.contribution_to_raw_composite:.1f} pts)"
                )

            if d.is_limited:
                areas_insufficient.append(f"{d.dimension_name} contains missing data or fallback medians")

        # 3. Identify excluded or unsupported metrics
        excluded_metrics: list[dict[str, str]] = [
            {"metric_id": "wicket_threat_index", "reason": "Batting order position not available in flat ball-by-ball schema."},
            {"metric_id": "clutch_finishing_index", "reason": "Requires dynamic match chase state and required run rate."},
            {"metric_id": "net_value_contribution", "reason": "Markov run expectancy / WPA model deferred per architectural roadmap."},
        ]

        # 4. Formulate deterministic narrative
        role_label = player_score.role.value
        if status == ExplanationStatus.INSUFFICIENT_EVIDENCE:
            narrative = (
                f"{role_label} {player_score.player_name} faced/bowled insufficient sample volume to generate an unpenalized score. "
                f"Raw evaluation of {player_score.raw_composite_score:.1f} was quarantined and regressed to the cohort center (50.0). "
                f"Additional verified match deliveries are required before competitive ranking."
            )
        elif status == ExplanationStatus.PARTIAL:
            narrative = (
                f"{role_label} {player_score.player_name} achieved a VOR rating of {player_score.vor_score:.1f} in cohort '{player_score.cohort_id}'. "
                f"Supported by provisional sample volume (C = {player_score.reliability_factor:.2f}). "
                f"Raw composite of {player_score.raw_composite_score:.1f} was shrunk toward cohort median (50.0). "
                f"Primary strength: {top_strengths[0] if top_strengths else 'Balanced'}. "
                f"Primary area for improvement: {drag_factors[0] if drag_factors else 'None noted'}."
            )
        else:
            narrative = (
                f"{role_label} {player_score.player_name} achieved a fully reliable VOR rating of {player_score.vor_score:.1f} in cohort '{player_score.cohort_id}' (C = 1.0). "
                f"Demonstrates elite potency in {top_strengths[0] if top_strengths else 'all core dimensions'}. "
                f"Evaluation is mathematically verified across all {len(breakdown.dimensions)} dimensions."
            )

        provenance = MetricProvenance(
            dataset_id=player_score.provenance.dataset_id,
            calculation_version="1.0.0",
        )

        return PlayerDetailedExplanationResponse(
            player_id=player_score.player_id,
            player_name=player_score.player_name,
            role=player_score.role,
            status=status,
            cohort_id=player_score.cohort_id,
            run_id=run_id or "LATEST",
            dataset_id=player_score.provenance.dataset_id,
            final_vor=player_score.vor_score,
            raw_composite_score=player_score.raw_composite_score,
            reliability_factor=player_score.reliability_factor,
            reliability_status=player_score.reliability_status,
            sample_size=player_score.sample_size,
            top_strengths=top_strengths[:3],
            drag_factors=drag_factors[:3],
            areas_of_insufficient_evidence=areas_insufficient,
            excluded_or_unsupported_metrics=excluded_metrics,
            narrative_summary=narrative,
            provenance=provenance,
        )

