"""High-level orchestration service for player role classification and evaluation profiles."""

from collections import Counter
from datetime import datetime, timezone
from typing import Any
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.core.logging import get_logger
from backend.app.models.cricket import Delivery, Player
from backend.app.schemas.evaluation import (
    DatasetEvaluationResponse,
    PlayerEvaluationResponse,
    RoleClassificationResult,
)
from backend.app.schemas.metrics import MetricProvenance
from backend.app.services.analytics.base import CALCULATION_VERSION
from backend.app.services.analytics.service import AnalyticsService
from backend.app.services.evaluation.adequacy import SampleAdequacyEvaluator
from backend.app.services.evaluation.classifier import RoleClassifier
from backend.app.services.evaluation.config import (
    DEFAULT_ROLE_CONFIG,
    RoleClassificationConfig,
)
from backend.app.services.evaluation.profiles import ProfileBuilder

logger = get_logger("vyntiq.evaluation.service")


class EvaluationService:
    """Orchestrates role classification, sample adequacy assessment, and role-specific profiling.

    Reuses the existing AnalyticsService without recalculating raw cricket delivery statistics.
    """

    def __init__(self, config: RoleClassificationConfig | None = None) -> None:
        self.config = config or DEFAULT_ROLE_CONFIG
        self.analytics = AnalyticsService()
        self.classifier = RoleClassifier(self.config)
        self.adequacy = SampleAdequacyEvaluator(self.config)
        self.profile_builder = ProfileBuilder(self.adequacy)

    def evaluate_player_from_data(
        self,
        dataset_id: str,
        df: pd.DataFrame,
        player_id: str,
        player_name: str | None = None,
        source_role: str | None = None,
        fielding_data: dict[str, Any] | None = None,
    ) -> PlayerEvaluationResponse:
        """Evaluate a single player using in-memory DataFrame and analytics engine."""
        calc_res = self.analytics.calculate_from_dataframe(
            dataset_id=dataset_id,
            df=df,
            target_player_id=player_id,
            include_dimensions=False,  # Dimensions are built role-specifically here
            player_names={player_id: player_name} if player_name else None,
        )

        if not calc_res.players:
            raise EntityNotFoundException("Player", player_id)

        player_data = calc_res.players[0]
        sample = player_data.sample_size

        # 1. Classify Role
        role_result = self.classifier.classify_player(
            player_id=player_id,
            sample=sample,
            source_role=source_role,
        )

        # 2. Assess Sample Adequacy
        adequacy_result = self.adequacy.assess_adequacy(role_result.assigned_role, sample)

        # 3. Build Role-Specific Evaluation Profile
        eval_profile = self.profile_builder.build_profile(
            role=role_result.assigned_role,
            batting_metrics=player_data.batting_metrics,
            bowling_metrics=player_data.bowling_metrics,
            sample=sample,
            fielding_data=fielding_data,
        )

        return PlayerEvaluationResponse(
            player_id=player_id,
            player_name=player_data.player_name,
            role=role_result,
            sample_size=sample,
            sample_adequacy=adequacy_result,
            evaluation_profile=eval_profile,
            data_quality_status="VERIFIED" if role_result.status.value != "INSUFFICIENT_DATA" else "REVIEW_REQUIRED",
            evaluation_version=self.config.version,
            provenance=player_data.provenance,
        )

    def evaluate_dataset_from_dataframe(
        self,
        dataset_id: str,
        df: pd.DataFrame,
        source_roles: dict[str, str] | None = None,
        player_names: dict[str, str] | None = None,
    ) -> DatasetEvaluationResponse:
        """Evaluate all participating players in an in-memory dataset."""
        calc_res = self.analytics.calculate_from_dataframe(
            dataset_id=dataset_id,
            df=df,
            include_dimensions=False,
            player_names=player_names,
        )

        s_roles = source_roles or {}
        evaluated_players: list[PlayerEvaluationResponse] = []
        role_counts: Counter[str] = Counter()

        for p_data in calc_res.players:
            sample = p_data.sample_size
            s_role = s_roles.get(p_data.player_id)

            role_result = self.classifier.classify_player(
                player_id=p_data.player_id,
                sample=sample,
                source_role=s_role,
            )
            role_counts[role_result.assigned_role.value] += 1

            adequacy_result = self.adequacy.assess_adequacy(role_result.assigned_role, sample)

            eval_profile = self.profile_builder.build_profile(
                role=role_result.assigned_role,
                batting_metrics=p_data.batting_metrics,
                bowling_metrics=p_data.bowling_metrics,
                sample=sample,
            )

            evaluated_players.append(
                PlayerEvaluationResponse(
                    player_id=p_data.player_id,
                    player_name=p_data.player_name,
                    role=role_result,
                    sample_size=sample,
                    sample_adequacy=adequacy_result,
                    evaluation_profile=eval_profile,
                    data_quality_status="VERIFIED" if role_result.status.value != "INSUFFICIENT_DATA" else "REVIEW_REQUIRED",
                    evaluation_version=self.config.version,
                    provenance=p_data.provenance,
                )
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        provenance = MetricProvenance(
            dataset_id=dataset_id,
            calculation_version=CALCULATION_VERSION,
            calculated_at=now_iso,
        )

        return DatasetEvaluationResponse(
            dataset_id=dataset_id,
            total_evaluated_players=len(evaluated_players),
            players=evaluated_players,
            role_distribution=dict(role_counts),
            provenance=provenance,
        )

    async def evaluate_dataset_from_db(
        self,
        session: AsyncSession,
        dataset_id: str,
    ) -> DatasetEvaluationResponse:
        """Fetch deliveries and player metadata from the database and evaluate all players."""
        stmt = select(Delivery).where(Delivery.dataset_id == dataset_id)
        result = await session.execute(stmt)
        deliveries = result.scalars().all()

        if not deliveries:
            raise EntityNotFoundException("Dataset", dataset_id)

        df = self.analytics._deliveries_to_dataframe(deliveries)

        player_stmt = select(Player)
        p_res = await session.execute(player_stmt)
        players = p_res.scalars().all()
        names_map = {p.player_id: p.canonical_name for p in players}
        roles_map = {p.player_id: p.primary_role for p in players if p.primary_role}

        return self.evaluate_dataset_from_dataframe(
            dataset_id=dataset_id,
            df=df,
            source_roles=roles_map,
            player_names=names_map,
        )

    async def evaluate_player_from_db(
        self,
        session: AsyncSession,
        player_id: str,
    ) -> PlayerEvaluationResponse:
        """Fetch all deliveries for a player from the database and generate role evaluation profile."""
        p_stmt = select(Player).where(Player.player_id == player_id)
        p_res = await session.execute(p_stmt)
        player = p_res.scalar_one_or_none()

        # Query all deliveries where player is batter or bowler
        d_stmt = select(Delivery).where((Delivery.batter_id == player_id) | (Delivery.bowler_id == player_id))
        d_res = await session.execute(d_stmt)
        deliveries = d_res.scalars().all()

        if not deliveries:
            raise EntityNotFoundException("Player", player_id)

        df = self.analytics._deliveries_to_dataframe(deliveries)
        dataset_id = deliveries[0].dataset_id if deliveries else "UNKNOWN_DATASET"

        return self.evaluate_player_from_data(
            dataset_id=dataset_id,
            df=df,
            player_id=player_id,
            player_name=player.canonical_name if player else player_id,
            source_role=player.primary_role if player else None,
        )

    async def classify_players_from_db(
        self,
        session: AsyncSession,
        dataset_id: str,
    ) -> list[RoleClassificationResult]:
        """Classify all players in a dataset and return their classification provenance."""
        evaluation_res = await self.evaluate_dataset_from_db(session, dataset_id)
        return [p.role for p in evaluation_res.players]

