"""Player comparison service orchestrating head-to-head difference analysis and compatibility checks."""

from datetime import datetime, timezone
import uuid
from backend.app.core.exceptions import EntityNotFoundException, ValidationException
from backend.app.schemas.comparison import (
    ComparisonCompatibilityStatus,
    ComparisonMetadataResponse,
    DimensionComparisonItem,
    MetricComparisonItem,
    PlayerComparisonHeader,
    PlayerComparisonRequest,
    PlayerComparisonResponse,
)
from backend.app.schemas.evaluation import PlayerRole
from backend.app.schemas.metrics import MetricDirection, MetricProvenance
from backend.app.schemas.scoring import PlayerScoreResult
from backend.app.services.analytics.registry import METRIC_REGISTRY
from backend.app.services.comparison.compatibility import CompatibilityChecker
from backend.app.services.comparison.differencer import DifferenceAnalyzer
from backend.app.services.scoring.service import ScoringService

# In-memory comparison cache
COMPARISON_CACHE: dict[str, PlayerComparisonResponse] = {}


class PlayerComparisonService:
    """Orchestrates structured player comparisons, dimension differences, and compatibility verification."""

    def __init__(self, scoring_service: ScoringService | None = None) -> None:
        self.scoring_service = scoring_service or ScoringService()
        self.compatibility_checker = CompatibilityChecker()
        self.differencer = DifferenceAnalyzer()

    def compare_players(self, request: PlayerComparisonRequest) -> PlayerComparisonResponse:
        """Execute multi-player comparison across 2 to 5 candidates."""
        if len(request.player_ids) < 2 or len(request.player_ids) > 5:
            raise ValidationException("Player comparison requires between 2 and 5 players.")

        # 1. Fetch player score results
        player_scores: list[PlayerScoreResult] = []
        for p_id in request.player_ids:
            try:
                s = self.scoring_service.get_player_score(p_id, request.run_id)
                player_scores.append(s)
            except EntityNotFoundException:
                raise EntityNotFoundException("PlayerScore", p_id)

        # 2. Check compatibility
        compat_status, compat_notes = self.compatibility_checker.check_compatibility(player_scores)
        is_cross_role = compat_status == ComparisonCompatibilityStatus.CROSS_ROLE_PARTIAL
        vor_valid = compat_status == ComparisonCompatibilityStatus.FULLY_COMPATIBLE

        # Determine VOR leader if valid
        vor_leader_id: str | None = None
        if vor_valid:
            leader = max(player_scores, key=lambda p: p.vor_score)
            vor_leader_id = leader.player_id

        # 3. Create headers
        headers = [
            PlayerComparisonHeader(
                player_id=p.player_id,
                player_name=p.player_name,
                role=p.role,
                cohort_id=p.cohort_id,
                vor_score=p.vor_score,
                raw_composite_score=p.raw_composite_score,
                reliability_factor=p.reliability_factor,
                reliability_status=p.reliability_status,
                sample_size=p.sample_size,
            )
            for p in player_scores
        ]

        names_map = {p.player_id: p.player_name for p in player_scores}

        # 4. Compare Shared Dimensions
        shared_dimensions = self._compare_dimensions(player_scores, names_map)

        # 5. Compare Batting & Bowling Metrics
        batting_comp = self._compare_discipline_metrics(player_scores, names_map, category="BATTING")
        bowling_comp = self._compare_discipline_metrics(player_scores, names_map, category="BOWLING")

        # 6. Data quality warnings
        warnings: list[str] = []
        for p in player_scores:
            if not p.is_qualified:
                warnings.append(f"{p.player_name} has insufficient sample volume (< N_min). Rating regressed to median.")

        comp_id = f"COMP_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        provenance = MetricProvenance(
            dataset_id=player_scores[0].provenance.dataset_id,
            calculation_version="1.0.0",
            calculated_at=now_iso,
        )

        response = PlayerComparisonResponse(
            comparison_id=comp_id,
            created_at=now_iso,
            compatibility_status=compat_status,
            compatibility_notes=compat_notes,
            players=headers,
            is_cross_role=is_cross_role,
            vor_comparison_valid=vor_valid,
            vor_leader_id=vor_leader_id,
            shared_dimensions=shared_dimensions,
            batting_comparison=batting_comp,
            bowling_comparison=bowling_comp,
            data_quality_warnings=warnings,
            provenance=provenance,
        )

        COMPARISON_CACHE[comp_id] = response
        return response

    def get_comparison(self, comparison_id: str) -> PlayerComparisonResponse:
        """Lookup stored comparison by ID."""
        if comparison_id not in COMPARISON_CACHE:
            raise EntityNotFoundException("PlayerComparison", comparison_id)
        return COMPARISON_CACHE[comparison_id]

    def get_metadata(self) -> ComparisonMetadataResponse:
        """Return supported comparison metadata, rules, and directionality conventions."""
        return ComparisonMetadataResponse(
            max_players_allowed=5,
            supported_roles=[r.value for r in PlayerRole],
            compatibility_rules=[
                "Candidates must belong to identical role and tournament cohorts for direct VOR comparison.",
                "Cross-role comparisons show separate discipline sections; VOR rankings are not directly equated.",
                "Metrics with lower-is-better directionality (e.g. Economy Rate) award advantage to the smaller value.",
            ],
            tie_breaking_rules=[
                "1. VOR composite score",
                "2. Reliability Factor C(N)",
                "3. Primary True Metric (TSR / TER)",
            ],
            directionality_conventions={
                "HIGHER_IS_BETTER": "Higher value indicates superior performance (e.g. Strike Rate, Boundary %, Dot Suppression).",
                "LOWER_IS_BETTER": "Lower value indicates superior performance (e.g. Economy Rate, Bowling Strike Rate, Dot % Faced).",
                "NEUTRAL": "Descriptive volume count (e.g. Balls Faced, Overs Bowled).",
            },
        )

    def _compare_dimensions(
        self,
        players: list[PlayerScoreResult],
        names_map: dict[str, str],
    ) -> list[DimensionComparisonItem]:
        """Compare scores across shared evaluation dimensions."""
        # Find dimension IDs present in all players
        common_dims = set(players[0].dimensions.keys())
        for p in players[1:]:
            common_dims &= set(p.dimensions.keys())

        dim_items: list[DimensionComparisonItem] = []
        for dim_id in sorted(list(common_dims)):
            dim_name = players[0].dimensions[dim_id].dimension_name
            p_scores = {p.player_id: p.dimensions[dim_id].dimension_score for p in players}

            diff: float | None = None
            favorable_id: str | None = None

            if len(players) == 2:
                s1, s2 = list(p_scores.values())[0], list(p_scores.values())[1]
                diff = round(abs(s1 - s2), 2)

            max_score = max(p_scores.values())
            leaders = [p_id for p_id, s in p_scores.items() if s == max_score]
            if len(leaders) == 1:
                favorable_id = leaders[0]

            dim_items.append(
                DimensionComparisonItem(
                    dimension_id=dim_id,
                    dimension_name=dim_name,
                    player_dimension_scores=p_scores,
                    score_difference=diff,
                    favorable_player_id=favorable_id,
                )
            )

        return dim_items

    def _compare_discipline_metrics(
        self,
        players: list[PlayerScoreResult],
        names_map: dict[str, str],
        category: str,
    ) -> list[MetricComparisonItem]:
        """Compare atomic metrics for a specific discipline (Batting or Bowling)."""
        # Collect metric entries from registry matching category or applicable roles
        target_metrics = [
            m for m in METRIC_REGISTRY.values()
            if m.is_standard_ball_by_ball and (
                m.category.value == category
                or (category == "BATTING" and "BATTER" in m.applicable_roles)
                or (category == "BOWLING" and "BOWLER" in m.applicable_roles)
            )
        ]

        metric_items: list[MetricComparisonItem] = []
        for m in target_metrics:
            p_vals: dict[str, float | int | None] = {}
            p_pcts: dict[str, float | None] = {}

            for p in players:
                # Find metric in player's dimensions
                found = False
                for d in p.dimensions.values():
                    for nm in d.metrics:
                        if nm.metric_id == m.metric_id:
                            p_vals[p.player_id] = nm.raw_value
                            p_pcts[p.player_id] = nm.percentile
                            found = True
                            break
                    if found:
                        break
                if not found:
                    p_vals[p.player_id] = None
                    p_pcts[p.player_id] = None

            # Skip metric if all players have None
            if all(v is None for v in p_vals.values()):
                continue

            item = self.differencer.compare_metric(
                metric_id=m.metric_id,
                display_name=m.name,
                directionality=m.directionality,
                unit=m.unit,
                player_values=p_vals,
                player_percentiles=p_pcts,
                player_names=names_map,
            )
            metric_items.append(item)

        return metric_items
