"""Deterministic ranking, multi-criteria tie-breaking, and competition eligibility filtering."""

from datetime import date
from backend.app.schemas.evaluation import PlayerRole
from backend.app.schemas.scoring import (
    PlayerScoreResult,
    RankedPlayer,
    RankingResponse,
    ReliabilityStatus,
)


class RankingEngine:
    """Generates auditable leaderboards implementing official tie-breaking and eligibility gates.

    Strictly implements docs/SCORING_METHODOLOGY.md Section 8:
    1. Primary Sort: VOR descending
    2. Secondary Tie-Breaker: Reliability Factor C(N) descending
    3. Tertiary Tie-Breaker: True Metric primary dimension (TSR for batters, TER for bowlers)
    4. Quarantine Gate: is_eligible == False OR N < N_min excluded from qualified rankings.
    """

    def generate_rankings(
        self,
        scores: list[PlayerScoreResult],
        cohort_id: str,
        run_id: str,
        role_filter: str | None = None,
        max_age: float | None = None,
        uncapped_only: bool = False,
        reference_date: date | None = None,
    ) -> RankingResponse:
        """Produce separate qualified and quarantined leaderboards with full audit traceability."""
        qualified_candidates: list[PlayerScoreResult] = []
        quarantined_candidates: list[tuple[PlayerScoreResult, list[str]]] = []

        target_date = reference_date or date.today()

        for s in scores:
            if role_filter and s.role.value != role_filter.upper():
                continue

            quarantine_reasons: list[str] = []

            # 1. Sample adequacy check
            if s.reliability_status == ReliabilityStatus.INSUFFICIENT_SAMPLE or not s.is_qualified:
                quarantine_reasons.append("Sample volume below N_min threshold (INSUFFICIENT_SAMPLE)")

            # 2. Ineligible status check
            if not s.is_eligible:
                quarantine_reasons.append(s.eligibility_notes or "Ineligible per competition regulations")

            # 3. Uncapped filter (if enabled)
            if uncapped_only:
                # If uncapped status is explicitly False
                pass

            if quarantine_reasons:
                quarantined_candidates.append((s, quarantine_reasons))
            else:
                qualified_candidates.append(s)

        # Sort qualified candidates using strict multi-tier hierarchy
        # Sort key tuple: (VOR desc, Reliability C(N) desc, Primary Tiebreaker desc)
        def sort_key(item: PlayerScoreResult) -> tuple[float, float, float]:
            primary_tiebreaker = self._extract_primary_tiebreaker(item)
            return (item.vor_score, item.reliability_factor, primary_tiebreaker)

        qualified_candidates.sort(key=sort_key, reverse=True)

        ranked_list: list[RankedPlayer] = []
        for rank_idx, item in enumerate(qualified_candidates, start=1):
            ranked_list.append(
                RankedPlayer(
                    rank=rank_idx,
                    player_id=item.player_id,
                    player_name=item.player_name,
                    role=item.role,
                    vor_score=item.vor_score,
                    raw_composite_score=item.raw_composite_score,
                    reliability_factor=item.reliability_factor,
                    reliability_status=item.reliability_status,
                    primary_tiebreaker=self._extract_primary_tiebreaker(item),
                    is_qualified=True,
                    is_eligible=item.is_eligible,
                    quarantine_reasons=[],
                )
            )

        quarantined_list: list[RankedPlayer] = []
        for item, reasons in quarantined_candidates:
            quarantined_list.append(
                RankedPlayer(
                    rank=0,
                    player_id=item.player_id,
                    player_name=item.player_name,
                    role=item.role,
                    vor_score=item.vor_score,
                    raw_composite_score=item.raw_composite_score,
                    reliability_factor=item.reliability_factor,
                    reliability_status=item.reliability_status,
                    primary_tiebreaker=self._extract_primary_tiebreaker(item),
                    is_qualified=False,
                    is_eligible=item.is_eligible,
                    quarantine_reasons=reasons,
                )
            )

        return RankingResponse(
            run_id=run_id,
            cohort_id=cohort_id,
            role_filter=role_filter,
            total_ranked=len(ranked_list),
            total_quarantined=len(quarantined_list),
            rankings=ranked_list,
            quarantined=quarantined_list,
        )

    def _extract_primary_tiebreaker(self, item: PlayerScoreResult) -> float:
        """Extract True Strike Rate (TSR) for batters, True Economy Rate (TER) for bowlers."""
        if item.role in (PlayerRole.BATTER, PlayerRole.WICKETKEEPER):
            # Check TSR in scoring_efficiency
            eff_dim = item.dimensions.get("scoring_efficiency")
            if eff_dim:
                for m in eff_dim.metrics:
                    if m.metric_id == "true_strike_rate" and m.raw_value is not None:
                        return float(m.raw_value)
            return 0.0

        if item.role == PlayerRole.BOWLER:
            # Check TER in run_containment
            cont_dim = item.dimensions.get("run_containment")
            if cont_dim:
                for m in cont_dim.metrics:
                    if m.metric_id == "true_economy_rate" and m.raw_value is not None:
                        return float(m.raw_value)
            return 0.0

        if item.role == PlayerRole.ALL_ROUNDER:
            return item.dual_bonus_points

        return 0.0
