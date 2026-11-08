"""Scoring service orchestrating ECDF normalization, Bayesian shrinkage, and VOR ranking."""

from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.core.logging import get_logger
from backend.app.schemas.evaluation import PlayerEvaluationResponse, PlayerRole
from backend.app.schemas.metrics import MetricDirection, MetricProvenance
from backend.app.schemas.scoring import (
    DimensionScore,
    NormalizedMetric,
    PlayerScoreResult,
    RankingResponse,
    ReliabilityStatus,
    ScoringCalculationRequest,
    ScoringMethodologyResponse,
    ScoringRunResponse,
)
from backend.app.services.evaluation.service import EvaluationService
from backend.app.services.scoring.base import SCORING_ENGINE_VERSION
from backend.app.services.scoring.cohorts import CohortManager
from backend.app.services.scoring.composite import VORCompositeCalculator
from backend.app.services.scoring.explainability import ScoreExplainer
from backend.app.services.scoring.normalization import ECDFNormalizer
from backend.app.services.scoring.ranking import RankingEngine
from backend.app.services.scoring.reliability import (
    BATTING_N_MIN,
    BOWLING_N_MIN,
    BayesianReliabilityAssessor,
)
from backend.app.services.scoring.weights import DEFAULT_WEIGHT_CONFIG, RoleWeightConfiguration

logger = get_logger("vyntiq.scoring.service")

# Global in-memory run cache for instant retrieval of runs and player score explanations
RUN_CACHE: dict[str, ScoringRunResponse] = {}


class ScoringService:
    """High-level orchestration service for the VOR evaluation and ranking engine."""

    def __init__(
        self,
        weight_config: RoleWeightConfiguration | None = None,
        reliability_assessor: BayesianReliabilityAssessor | None = None,
    ) -> None:
        self.weights = weight_config or DEFAULT_WEIGHT_CONFIG
        self.reliability = reliability_assessor or BayesianReliabilityAssessor()
        self.normalizer = ECDFNormalizer()
        self.cohort_manager = CohortManager()
        self.calculator = VORCompositeCalculator(self.weights, self.reliability)
        self.explainer = ScoreExplainer()
        self.ranking_engine = RankingEngine()
        self.evaluation_service = EvaluationService()

    def score_players_from_evaluations(
        self,
        dataset_id: str,
        evaluations: list[PlayerEvaluationResponse],
        run_id: str | None = None,
    ) -> ScoringRunResponse:
        """Run complete VOR scoring pipeline from a list of structured player evaluation profiles."""
        scoring_run_id = run_id or f"RUN_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Partition players into role-specific comparison cohorts
        cohort_dict = self.cohort_manager.partition_cohorts(evaluations)
        all_scored_players: list[PlayerScoreResult] = []

        total_qualified = 0
        total_quarantined = 0

        for role_str, cohort_players in cohort_dict.items():
            if not cohort_players:
                continue

            cohort_id = self.cohort_manager.build_cohort_id(role_str)
            role_enum = PlayerRole(role_str)

            # Score each cohort independently to avoid cross-role distortion
            scored_cohort = self._score_cohort(
                role=role_enum,
                cohort_id=cohort_id,
                players=cohort_players,
                dataset_id=dataset_id,
            )

            for p in scored_cohort:
                all_scored_players.append(p)
                if p.is_qualified:
                    total_qualified += 1
                else:
                    total_quarantined += 1

        run_result = ScoringRunResponse(
            run_id=scoring_run_id,
            dataset_id=dataset_id,
            cohort_id="MULTI_ROLE_RUN",
            total_evaluated=len(all_scored_players),
            total_qualified=total_qualified,
            total_quarantined=total_quarantined,
            scoring_version=SCORING_ENGINE_VERSION,
            created_at=now_iso,
            players=all_scored_players,
        )

        # Store in cache
        RUN_CACHE[scoring_run_id] = run_result
        return run_result

    async def calculate_for_dataset(
        self,
        session: AsyncSession,
        request: ScoringCalculationRequest,
    ) -> ScoringRunResponse:
        """Fetch evaluated players from DB and compute full VOR composite scoring."""
        eval_resp = await self.evaluation_service.evaluate_dataset_from_db(session, request.dataset_id)
        return self.score_players_from_evaluations(
            dataset_id=request.dataset_id,
            evaluations=eval_resp.players,
        )

    def get_run(self, run_id: str) -> ScoringRunResponse:
        """Retrieve historical or cached scoring run details."""
        if run_id not in RUN_CACHE:
            raise EntityNotFoundException("ScoringRun", run_id)
        return RUN_CACHE[run_id]

    def get_player_score(self, player_id: str, run_id: str | None = None) -> PlayerScoreResult:
        """Lookup player score and explanation from the latest or specified run."""
        target_runs = [RUN_CACHE[run_id]] if run_id and run_id in RUN_CACHE else list(RUN_CACHE.values())
        if not target_runs:
            raise EntityNotFoundException("PlayerScore", player_id)

        # Search backward from latest run
        for run in reversed(target_runs):
            for p in run.players:
                if p.player_id == player_id:
                    return p

        raise EntityNotFoundException("PlayerScore", player_id)

    def get_rankings(
        self,
        run_id: str | None = None,
        role_filter: str | None = None,
    ) -> RankingResponse:
        """Generate official ranked leaderboard from the specified or latest scoring run."""
        if not RUN_CACHE:
            return RankingResponse(
                run_id="EMPTY",
                cohort_id="EMPTY",
                role_filter=role_filter,
                total_ranked=0,
                total_quarantined=0,
                rankings=[],
                quarantined=[],
            )

        target_run = RUN_CACHE[run_id] if run_id and run_id in RUN_CACHE else list(RUN_CACHE.values())[-1]
        cohort_id = f"COHORT_{role_filter.upper()}" if role_filter else target_run.cohort_id

        return self.ranking_engine.generate_rankings(
            scores=target_run.players,
            cohort_id=cohort_id,
            run_id=target_run.run_id,
            role_filter=role_filter,
        )

    def get_methodology(self) -> ScoringMethodologyResponse:
        """Return full documentation, formulas, and parameters for the active VOR engine."""
        return ScoringMethodologyResponse(
            version=SCORING_ENGINE_VERSION,
            ecdf_formula_higher_better="Z_i = (sum(1_{x_j <= x_i}) / M) * 100",
            ecdf_formula_lower_better="Z_i = (sum(1_{x_j >= x_i}) / M) * 100",
            bayesian_shrinkage_formula="VOR = 50.0 + C(N) * (raw_composite - 50.0); C(N) = N / (N + K)",
            sample_thresholds={
                "batting": {"N_min": BATTING_N_MIN, "N_full": 180, "K": 30.0},
                "bowling": {"N_min": BOWLING_N_MIN, "N_full": 180, "K": 36.0},
            },
            role_weights={
                "batting_balanced": self.weights.batting_weights,
                "bowling_balanced": self.weights.bowling_weights,
            },
            all_rounder_dual_bonus_formula="Bonus = 5.0 * (min(VOR_bat, VOR_bowl) / 50.0) if both meet N_min",
            tie_breaking_hierarchy=[
                "1. Primary Sort: VOR Composite Score descending",
                "2. Secondary Tie-Breaker: Reliability Factor C(N) descending",
                "3. Tertiary Tie-Breaker: Primary True Metric (TSR for batters, TER for bowlers)",
                "4. Quarantine Filter: is_eligible == False or N < N_min excluded from qualified ranks",
            ],
        )

    def _score_cohort(
        self,
        role: PlayerRole,
        cohort_id: str,
        players: list[PlayerEvaluationResponse],
        dataset_id: str,
    ) -> list[PlayerScoreResult]:
        """Normalize metrics and calculate VOR composite scores for a specific role cohort."""
        # 1. Normalize all dimensions across players in the cohort
        player_norm_dims: dict[str, dict[str, list[NormalizedMetric]]] = {p.player_id: {} for p in players}

        # Collect unique dimensions present across players
        all_dims = set()
        for p in players:
            all_dims.update(p.evaluation_profile.keys())

        for dim_id in sorted(list(all_dims)):
            # Collect metric values across players for this dimension
            # Map metric_id -> dict of {player_id: value}
            metric_player_vals: dict[str, dict[str, float | int | None]] = {}
            metric_metadata: dict[str, tuple[str, MetricDirection]] = {}

            for p in players:
                dim_prof = p.evaluation_profile.get(dim_id)
                if not dim_prof:
                    continue
                for m in dim_prof.metrics:
                    if m.metric_id not in metric_player_vals:
                        metric_player_vals[m.metric_id] = {}
                        metric_metadata[m.metric_id] = (m.display_name, m.directionality)
                    metric_player_vals[m.metric_id][p.player_id] = m.value

            # ECDF Normalize each metric across cohort
            for m_id, p_vals in metric_player_vals.items():
                disp_name, dirn = metric_metadata[m_id]
                norm_dict = self.normalizer.normalize_cohort_metric(
                    metric_id=m_id,
                    display_name=disp_name,
                    directionality=dirn,
                    player_values=p_vals,
                    cohort_id=cohort_id,
                )
                for p_id, norm_m in norm_dict.items():
                    if dim_id not in player_norm_dims[p_id]:
                        player_norm_dims[p_id][dim_id] = []
                    player_norm_dims[p_id][dim_id].append(norm_m)

        # 2. Compute composite score for each player
        results: list[PlayerScoreResult] = []

        for p in players:
            p_dims = player_norm_dims.get(p.player_id, {})
            sample = p.sample_size

            if role == PlayerRole.BATTER or role == PlayerRole.WICKETKEEPER:
                vor, raw_comp, c_fac, rel_stat, dim_scores = self.calculator.compute_batter_vor(p_dims, sample)
                dual_bonus = 0.0
                disc_comps = {"batting_vor": vor}
                is_qual = sample.balls_faced >= BATTING_N_MIN
            elif role == PlayerRole.BOWLER:
                vor, raw_comp, c_fac, rel_stat, dim_scores = self.calculator.compute_bowler_vor(p_dims, sample)
                dual_bonus = 0.0
                disc_comps = {"bowling_vor": vor}
                is_qual = sample.legal_balls_bowled >= BOWLING_N_MIN
            elif role == PlayerRole.ALL_ROUNDER:
                # Compute batting and bowling components
                bat_vor, raw_bat, _, _, bat_dim_scores = self.calculator.compute_batter_vor(p_dims, sample)
                bowl_vor, raw_bowl, _, _, bowl_dim_scores = self.calculator.compute_bowler_vor(p_dims, sample)

                c_fac, rel_stat = self.reliability.calculate_player_reliability(role, sample)
                dim_scores = {**bat_dim_scores, **bowl_dim_scores}

                vor, raw_comp, dual_bonus, disc_comps = self.calculator.compute_all_rounder_vor(
                    bat_vor=bat_vor,
                    bowl_vor=bowl_vor,
                    raw_bat=raw_bat,
                    raw_bowl=raw_bowl,
                    c_factor=c_fac,
                    rel_status=rel_stat,
                    sample=sample,
                    all_dim_scores=dim_scores,
                )
                is_qual = (
                    sample.balls_faced >= BATTING_N_MIN
                    and sample.legal_balls_bowled >= BOWLING_N_MIN
                    and rel_stat != ReliabilityStatus.INSUFFICIENT_SAMPLE
                )
            else:  # UNKNOWN
                vor = 50.0
                raw_comp = 50.0
                c_fac = 0.0
                rel_stat = ReliabilityStatus.INSUFFICIENT_SAMPLE
                dim_scores = {}
                dual_bonus = 0.0
                disc_comps = {}
                is_qual = False

            # Generate transparent explanation
            explanation = self.explainer.explain_score(
                vor=vor,
                raw_composite=raw_comp,
                reliability_factor=c_fac,
                reliability_status=rel_stat,
                dimension_scores=dim_scores,
                role_name=role.value,
                cohort_id=cohort_id,
            )

            provenance = MetricProvenance(
                dataset_id=dataset_id,
                calculation_version=SCORING_ENGINE_VERSION,
            )

            results.append(
                PlayerScoreResult(
                    player_id=p.player_id,
                    player_name=p.player_name,
                    role=role,
                    role_classification=p.role,
                    cohort_id=cohort_id,
                    vor_score=vor,
                    raw_composite_score=raw_comp,
                    reliability_factor=c_fac,
                    reliability_status=rel_stat,
                    sample_size=sample,
                    discipline_components=disc_comps,
                    dual_bonus_points=dual_bonus,
                    dimensions=dim_scores,
                    is_qualified=is_qual,
                    is_eligible=True,
                    explanation=explanation,
                    scoring_version=SCORING_ENGINE_VERSION,
                    provenance=provenance,
                )
            )

        return results
