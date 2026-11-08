"""Analytics service orchestrating cricket metrics calculation, aggregation, and dimensions."""

from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.core.logging import get_logger
from backend.app.models.cricket import Delivery, Player
from backend.app.schemas.analytics import (
    CalculationResponse,
    DatasetMetricsSummaryResponse,
    MetricCalculationFilter,
    MetricCalculationRequest,
    PlayerMetricsSummary,
)
from backend.app.schemas.metrics import MetricProvenance
from backend.app.services.analytics.advanced import AdvancedMetricsEvaluator
from backend.app.services.analytics.aggregation import DeliveryAggregator
from backend.app.services.analytics.base import CALCULATION_VERSION
from backend.app.services.analytics.batting import BattingMetricsCalculator
from backend.app.services.analytics.bowling import BowlingMetricsCalculator
from backend.app.services.analytics.dimensions import DimensionBuilder

logger = get_logger("vyntiq.analytics.service")


class AnalyticsService:
    """High-level facade orchestrating data extraction, metric calculation, and aggregation."""

    def __init__(self) -> None:
        self.aggregator = DeliveryAggregator()
        self.batting_calc = BattingMetricsCalculator()
        self.bowling_calc = BowlingMetricsCalculator()
        self.advanced_eval = AdvancedMetricsEvaluator()
        self.dim_builder = DimensionBuilder()

    def calculate_from_dataframe(
        self,
        dataset_id: str,
        df: pd.DataFrame,
        filters: MetricCalculationFilter | None = None,
        target_player_id: str | None = None,
        include_dimensions: bool = True,
        player_names: dict[str, str] | None = None,
    ) -> CalculationResponse:
        """Calculate metrics directly from an in-memory Pandas DataFrame (test & pipeline friendly)."""
        filtered_df = self.aggregator.filter_deliveries(df, filters)

        # Identify target players
        if target_player_id:
            players_to_compute = [target_player_id]
        elif filters and filters.player_ids:
            players_to_compute = filters.player_ids
        else:
            batters = set(filtered_df["batter_id"].dropna().unique()) if "batter_id" in filtered_df.columns else set()
            bowlers = set(filtered_df["bowler_id"].dropna().unique()) if "bowler_id" in filtered_df.columns else set()
            players_to_compute = sorted(list(batters | bowlers))

        names_map = player_names or {}
        player_summaries: list[PlayerMetricsSummary] = []

        now_iso = datetime.now(timezone.utc).isoformat()
        filter_dict = filters.model_dump() if filters else {}

        provenance = MetricProvenance(
            dataset_id=dataset_id,
            calculation_version=CALCULATION_VERSION,
            filters_applied=filter_dict,
            calculated_at=now_iso,
        )

        for p_id in players_to_compute:
            summary = self._compute_single_player(
                player_id=p_id,
                player_name=names_map.get(p_id, p_id),
                df=filtered_df,
                provenance=provenance,
                include_dimensions=include_dimensions,
            )
            player_summaries.append(summary)

        return CalculationResponse(
            dataset_id=dataset_id,
            total_players_computed=len(player_summaries),
            players=player_summaries,
            provenance=provenance,
        )

    async def calculate_for_dataset(
        self,
        session: AsyncSession,
        request: MetricCalculationRequest,
    ) -> CalculationResponse:
        """Fetch delivery records from the database and compute metrics for requested filters."""
        # Query deliveries for dataset
        stmt = select(Delivery).where(Delivery.dataset_id == request.dataset_id)
        result = await session.execute(stmt)
        deliveries = result.scalars().all()

        if not deliveries:
            raise EntityNotFoundException("Delivery", request.dataset_id)

        # Convert to DataFrame
        df = self._deliveries_to_dataframe(deliveries)

        # Lookup player names from DB
        player_stmt = select(Player)
        player_result = await session.execute(player_stmt)
        players = player_result.scalars().all()
        names_map = {p.player_id: p.canonical_name for p in players}

        return self.calculate_from_dataframe(
            dataset_id=request.dataset_id,
            df=df,
            filters=request.filters,
            target_player_id=request.player_id,
            include_dimensions=request.include_dimensions,
            player_names=names_map,
        )

    async def get_dataset_summary(
        self,
        session: AsyncSession,
        dataset_id: str,
    ) -> DatasetMetricsSummaryResponse:
        """Produce macro aggregate summary for an entire stored dataset."""
        stmt = select(Delivery).where(Delivery.dataset_id == dataset_id)
        result = await session.execute(stmt)
        deliveries = result.scalars().all()

        if not deliveries:
            raise EntityNotFoundException("Dataset", dataset_id)

        df = self._deliveries_to_dataframe(deliveries)
        return self.aggregator.compute_dataset_summary(dataset_id, df)

    def _compute_single_player(
        self,
        player_id: str,
        player_name: str,
        df: pd.DataFrame,
        provenance: MetricProvenance,
        include_dimensions: bool = True,
    ) -> PlayerMetricsSummary:
        """Internal helper to calculate full profile for one player."""
        sample_size = self.aggregator.compute_player_sample_size(player_id, df)

        # Batting calculations
        batting_metrics = self.batting_calc.calculate_metrics(player_id, df)
        # Append True Strike Rate
        tsr_metric = self.advanced_eval.compute_true_strike_rate(player_id, df)
        batting_metrics["true_strike_rate"] = tsr_metric

        # Bowling calculations
        bowling_metrics = self.bowling_calc.calculate_metrics(player_id, df)
        # Append True Economy Rate
        ter_metric = self.advanced_eval.compute_true_economy_rate(player_id, df)
        bowling_metrics["true_economy_rate"] = ter_metric

        # Append advanced evaluations (WTI, CFI, NVC)
        bowling_metrics["wicket_threat_index"] = self.advanced_eval.evaluate_wicket_threat_index(player_id, df)
        batting_metrics["clutch_finishing_index"] = self.advanced_eval.evaluate_clutch_finishing_index(player_id, df)
        batting_metrics["net_value_contribution"] = self.advanced_eval.evaluate_net_value_contribution()

        # Dimension groupings
        if include_dimensions:
            batting_dims = self.dim_builder.build_batting_dimensions(batting_metrics)
            bowling_dims = self.dim_builder.build_bowling_dimensions(bowling_metrics)
        else:
            batting_dims = {}
            bowling_dims = {}

        return PlayerMetricsSummary(
            player_id=player_id,
            player_name=player_name,
            sample_size=sample_size,
            batting_metrics=batting_metrics,
            bowling_metrics=bowling_metrics,
            batting_dimensions=batting_dims,
            bowling_dimensions=bowling_dims,
            provenance=provenance,
        )

    def _deliveries_to_dataframe(self, deliveries: list[Delivery]) -> pd.DataFrame:
        """Convert SQLAlchemy Delivery models to a clean, typed Pandas DataFrame."""
        records = [
            {
                "delivery_id": d.delivery_id,
                "workspace_id": d.workspace_id,
                "dataset_id": d.dataset_id,
                "origin_type": d.origin_type,
                "match_id": d.match_id,
                "innings_num": d.innings_num,
                "over_number": d.over_number,
                "ball_number": d.ball_number,
                "over_delivery": d.over_delivery,
                "phase": d.phase,
                "batter_id": d.batter_id,
                "bowler_id": d.bowler_id,
                "non_striker_id": d.non_striker_id,
                "batter_runs": d.batter_runs,
                "extras_runs": d.extras_runs,
                "extras_type": d.extras_type,
                "is_legal": d.is_legal,
                "total_runs": d.total_runs,
                "is_wicket": d.is_wicket,
                "dismissed_player_id": d.dismissed_player_id,
                "dismissal_kind": d.dismissal_kind,
                "is_super_over": d.is_super_over,
            }
            for d in deliveries
        ]
        return pd.DataFrame(records)

