"""Controlled database persistence engine for validated cricket records."""

import uuid
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.logging import get_logger
from backend.app.models.cricket import Delivery, Innings, Match, Player
from backend.app.models.dataset import Dataset, ValidationIssue
from backend.app.schemas.dataset import PersistenceResponse

logger = get_logger("vyntiq.ingestion.persister")


class DataPersister:
    """Manages transactional insertion of validated cricket entities into canonical tables."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def persist_validated_dataset(
        self,
        valid_df: pd.DataFrame,
        issues: list[ValidationIssue],
        dataset: Dataset,
    ) -> PersistenceResponse:
        """Persist deliveries, players, matches, and quarantine issues atomically."""
        # 1. Persist Quarantined Issues
        if issues:
            self.session.add_all(issues)
            await self.session.flush()

        deliveries_persisted = 0
        matches_persisted = 0
        players_persisted = 0

        if not valid_df.empty:
            # 2. Extract & Upsert Players (Batters and Bowlers)
            unique_batters = valid_df["batter_id"].dropna().unique()
            unique_bowlers = valid_df["bowler_id"].dropna().unique()
            all_player_names = set(unique_batters).union(set(unique_bowlers))

            # Query existing players to avoid duplicate inserts
            existing_players_query = select(Player.canonical_name)
            result = await self.session.execute(existing_players_query)
            existing_names = set(result.scalars().all())

            new_players = []
            for name in all_player_names:
                clean_name = str(name).strip()
                if clean_name and clean_name not in existing_names and clean_name != "UNKNOWN":
                    new_players.append(
                        Player(
                            player_id=f"pl_{uuid.uuid4().hex[:12]}",
                            canonical_name=clean_name,
                            primary_role=None,
                            is_eligible=True,
                        )
                    )
                    existing_names.add(clean_name)

            if new_players:
                self.session.add_all(new_players)
                await self.session.flush()
                players_persisted = len(new_players)

            # 3. Extract & Upsert Matches
            unique_matches = valid_df["match_id"].dropna().unique()
            existing_matches_query = select(Match.match_id).where(Match.match_id.in_(unique_matches))
            res_matches = await self.session.execute(existing_matches_query)
            existing_match_ids = set(res_matches.scalars().all())

            new_matches = []
            for m_id in unique_matches:
                if m_id not in existing_match_ids:
                    match_rows = valid_df[valid_df["match_id"] == m_id]
                    season = str(match_rows.iloc[0].get("season", "UNKNOWN"))
                    venue = str(match_rows.iloc[0].get("venue_name", "UNKNOWN")) if "venue_name" in match_rows.columns else None

                    new_matches.append(
                        Match(
                            match_id=str(m_id),
                            workspace_id=dataset.workspace_id,
                            dataset_id=dataset.dataset_id,
                            season=season,
                            venue_id=venue,
                        )
                    )
                    existing_match_ids.add(m_id)

            if new_matches:
                self.session.add_all(new_matches)
                await self.session.flush()
                matches_persisted = len(new_matches)

            # 4. Insert Canonical Deliveries
            new_deliveries = []
            for _, row in valid_df.iterrows():
                delivery_id = f"del_{uuid.uuid4().hex[:16]}"
                new_deliveries.append(
                    Delivery(
                        delivery_id=delivery_id,
                        workspace_id=dataset.workspace_id,
                        dataset_id=dataset.dataset_id,
                        origin_type=dataset.origin_type,
                        match_id=str(row.get("match_id")),
                        innings_num=int(row.get("innings_num", 1)),
                        over_number=int(row.get("over_number", 0)),
                        ball_number=int(row.get("ball_number", 1)),
                        over_delivery=float(row.get("over_delivery", 0.1)),
                        phase=str(row.get("phase", "MIDDLE")),
                        batter_id=str(row.get("batter_id")),
                        bowler_id=str(row.get("bowler_id")),
                        non_striker_id=str(row.get("non_striker_id")) if pd.notna(row.get("non_striker_id")) else None,
                        batter_runs=int(row.get("batter_runs", 0)),
                        extras_runs=int(row.get("extras_runs", 0)),
                        extras_type=str(row.get("extras_type")) if pd.notna(row.get("extras_type")) else None,
                        is_legal=bool(row.get("is_legal", True)),
                        total_runs=int(row.get("total_runs", 0)),
                        is_wicket=bool(row.get("is_wicket", False)),
                        dismissed_player_id=str(row.get("dismissed_player_id")) if pd.notna(row.get("dismissed_player_id")) else None,
                        dismissal_kind=str(row.get("dismissal_kind")) if pd.notna(row.get("dismissal_kind")) else None,
                        is_super_over=bool(row.get("is_super_over", False)),
                    )
                )

            # Batch insert deliveries
            self.session.add_all(new_deliveries)
            await self.session.flush()
            deliveries_persisted = len(new_deliveries)

        # 5. Update Dataset Record
        dataset.status = "PERSISTED" if len(issues) == 0 else "VALIDATED_WITH_WARNINGS"
        dataset.total_rows = len(valid_df) + len(issues)
        dataset.valid_rows = len(valid_df)
        dataset.quarantined_rows = len(issues)
        await self.session.flush()

        logger.info(
            "Dataset %s successfully persisted: %d deliveries, %d matches, %d players",
            dataset.dataset_id,
            deliveries_persisted,
            matches_persisted,
            players_persisted,
        )

        return PersistenceResponse(
            dataset_id=dataset.dataset_id,
            status=dataset.status,
            deliveries_persisted=deliveries_persisted,
            matches_persisted=matches_persisted,
            players_persisted=players_persisted,
            persisted_at=datetime.now(timezone.utc),
        )
