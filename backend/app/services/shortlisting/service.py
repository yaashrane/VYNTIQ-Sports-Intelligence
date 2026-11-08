"""Shortlisting service generating evidence-based player shortlists from scored runs and managing review workflows."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.exceptions import (
    EntityNotFoundException,
    ValidationException,
    WorkspaceException,
)
from backend.app.models.cricket import Player
from backend.app.models.dataset import Dataset
from backend.app.models.workspace import (
    Shortlist,
    ShortlistAuditLog,
    ShortlistCandidate,
)
from backend.app.repositories.workspace import WorkspaceRepository
from backend.app.schemas.scoring import ScoringRunResponse
from backend.app.schemas.workspace import (
    EligibilityStatus,
    ReviewStatus,
    ShortlistAuditResponse,
    ShortlistCandidateItem,
    ShortlistGenerateRequest,
    ShortlistResponse,
    ShortlistReviewRequest,
    ShortlistSummaryResponse,
    WorkspaceStatus,
)
from backend.app.services.scoring.service import RUN_CACHE, ScoringService
from backend.app.services.shortlisting.eligibility import EligibilityEngine
from backend.app.services.workspace.service import WorkspaceService


class ShortlistingService:
    """Consumes evaluation/scoring outputs to generate evidence-backed, reviewable player shortlists."""

    def __init__(
        self,
        session: AsyncSession,
        scoring_service: ScoringService | None = None,
        workspace_service: WorkspaceService | None = None,
    ) -> None:
        self.session = session
        self.repo = WorkspaceRepository(session)
        self.scoring_service = scoring_service or ScoringService()
        self.workspace_service = workspace_service or WorkspaceService(session)

    async def generate_shortlist(
        self, workspace_id: str, payload: ShortlistGenerateRequest
    ) -> ShortlistResponse:
        """Filter scored candidate pool against workspace eligibility rules and select top ranked players."""
        # 1. Validate Workspace
        workspace = await self.workspace_service.get_workspace(workspace_id)
        if workspace.status == WorkspaceStatus.ARCHIVED.value:
            raise ValidationException(
                f"Cannot generate shortlists in an ARCHIVED workspace '{workspace_id}'."
            )

        # 2. Verify Dataset Workspace Isolation (ADR-001)
        dataset_query = select(Dataset).where(Dataset.dataset_id == payload.dataset_id)
        ds_res = await self.session.execute(dataset_query)
        dataset = ds_res.scalars().first()
        if dataset and dataset.workspace_id and dataset.workspace_id != workspace_id:
            raise WorkspaceException(
                f"Dataset '{payload.dataset_id}' belongs to workspace '{dataset.workspace_id}' and cannot be accessed by '{workspace_id}'."
            )

        # 3. Retrieve Workspace Configuration
        config = await self.workspace_service.get_configuration(workspace_id)

        # 4. Retrieve Existing Scoring Run (Do not recalculate or invent scores)
        scoring_run = self._resolve_scoring_run(payload.dataset_id, payload.scoring_run_id)
        if not scoring_run or not scoring_run.players:
            raise ValidationException(
                f"No completed scoring run available for dataset '{payload.dataset_id}'. "
                "Please run scoring and ranking before generating a shortlist."
            )

        # 5. Retrieve Player Master Records for Context (e.g. DOB, Nationality)
        player_ids = [p.player_id for p in scoring_run.players]
        players_query = select(Player).where(Player.player_id.in_(player_ids))
        players_res = await self.session.execute(players_query)
        player_db_map: dict[str, Player] = {p.player_id: p for p in players_res.scalars().all()}

        # 6. Apply Eligibility Rules & Collect Exclusions
        eligible_players = []
        exclusion_details: dict[str, list[str]] = {}

        # Allow ad-hoc role override if supplied in request
        effective_config = config.model_copy()
        if payload.override_roles:
            effective_config.target_roles = payload.override_roles

        for player_score in scoring_run.players:
            p_record = player_db_map.get(player_score.player_id)
            assessment = EligibilityEngine.evaluate_player(
                player_score=player_score,
                config=effective_config,
                player_record=p_record,
            )

            if assessment.is_eligible:
                eligible_players.append(player_score)
            else:
                exclusion_details[player_score.player_id] = assessment.exclusion_reasons

        # 7. Select Top Candidates Ranked by VOR Score
        # Scoring run is already sorted by VOR score, but we sort explicitly to preserve deterministic ranking
        eligible_players.sort(key=lambda p: (p.vor_score, p.raw_composite_score), reverse=True)

        target_size = payload.override_shortlist_size or config.shortlist_size
        top_candidates = eligible_players[:target_size]

        shortlist_id = f"sl_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        # 8. Assemble Shortlist Candidate Records
        candidate_entities: list[ShortlistCandidate] = []
        candidate_items: list[ShortlistCandidateItem] = []

        for rank_idx, cand in enumerate(top_candidates, start=1):
            cand_id = f"cand_{uuid.uuid4().hex[:12]}"
            role_str = cand.role.value if hasattr(cand.role, "value") else str(cand.role)
            rel_stat_str = (
                cand.reliability_status.value
                if hasattr(cand.reliability_status, "value")
                else str(cand.reliability_status)
            )

            entity = ShortlistCandidate(
                candidate_entry_id=cand_id,
                shortlist_id=shortlist_id,
                workspace_id=workspace_id,
                player_id=cand.player_id,
                player_name=cand.player_name,
                assigned_role=role_str,
                rank=rank_idx,
                vor_score=cand.vor_score,
                raw_composite_score=cand.raw_composite_score,
                reliability_factor=cand.reliability_factor,
                reliability_status=rel_stat_str,
                evaluation_ref=f"scoring_run:{scoring_run.run_id}:player:{cand.player_id}",
                explainability_ref=f"/api/v1/explainability/players/{cand.player_id}?run_id={scoring_run.run_id}",
                eligibility_status=EligibilityStatus.ELIGIBLE.value,
                review_status=ReviewStatus.PENDING.value,
                reviewer_notes=None,
                selection_timestamp=now,
            )
            candidate_entities.append(entity)

            candidate_items.append(
                ShortlistCandidateItem(
                    candidate_entry_id=cand_id,
                    shortlist_id=shortlist_id,
                    workspace_id=workspace_id,
                    player_id=cand.player_id,
                    player_name=cand.player_name,
                    assigned_role=role_str,
                    rank=rank_idx,
                    vor_score=cand.vor_score,
                    raw_composite_score=cand.raw_composite_score,
                    reliability_factor=cand.reliability_factor,
                    reliability_status=rel_stat_str,
                    evaluation_ref=entity.evaluation_ref,
                    explainability_ref=entity.explainability_ref,
                    eligibility_status=EligibilityStatus.ELIGIBLE,
                    review_status=ReviewStatus.PENDING,
                    reviewer_notes=None,
                    selection_timestamp=now,
                )
            )

        # 9. Persist Shortlist Entity
        shortlist_record = Shortlist(
            shortlist_id=shortlist_id,
            workspace_id=workspace_id,
            name=payload.name.strip(),
            dataset_id=payload.dataset_id,
            scoring_run_id=scoring_run.run_id,
            config_version=config.version,
            methodology_version=config.evaluation_profile_version,
            target_size=target_size,
            eligible_count=len(eligible_players),
            excluded_count=len(exclusion_details),
            shortlisted_count=len(top_candidates),
            status="GENERATED",
        )
        await self.repo.create_shortlist(shortlist_record)
        await self.repo.add_candidates(candidate_entities)

        # 10. Persist Shortlist Audit Log
        audit_record = ShortlistAuditLog(
            audit_id=f"aud_{uuid.uuid4().hex[:12]}",
            shortlist_id=shortlist_id,
            workspace_id=workspace_id,
            dataset_id=payload.dataset_id,
            configuration_version=config.version,
            evaluation_methodology_version=config.evaluation_profile_version,
            metric_registry_version="1.0.0",
            ranking_engine_version="1.0.0",
            generation_timestamp=now,
            eligible_candidate_count=len(eligible_players),
            excluded_candidate_count=len(exclusion_details),
            shortlisted_candidate_count=len(top_candidates),
            exclusion_details=exclusion_details,
        )
        await self.repo.create_audit_log(audit_record)

        return ShortlistResponse(
            shortlist_id=shortlist_record.shortlist_id,
            workspace_id=shortlist_record.workspace_id,
            name=shortlist_record.name,
            dataset_id=shortlist_record.dataset_id,
            scoring_run_id=shortlist_record.scoring_run_id,
            config_version=shortlist_record.config_version,
            methodology_version=shortlist_record.methodology_version,
            target_size=shortlist_record.target_size,
            eligible_count=shortlist_record.eligible_count,
            excluded_count=shortlist_record.excluded_count,
            shortlisted_count=shortlist_record.shortlisted_count,
            status=shortlist_record.status,
            candidates=candidate_items,
            exclusion_summary=exclusion_details,
            created_at=shortlist_record.created_at,
        )

    async def get_shortlist(
        self, workspace_id: str, shortlist_id: str
    ) -> ShortlistResponse:
        """Fetch full shortlist details including candidates, verifying tenant isolation."""
        await self.workspace_service.get_workspace(workspace_id)
        shortlist = await self.repo.get_shortlist(shortlist_id)
        if not shortlist:
            raise EntityNotFoundException("Shortlist", shortlist_id)
        if shortlist.workspace_id != workspace_id:
            raise WorkspaceException(
                f"Shortlist '{shortlist_id}' does not belong to workspace '{workspace_id}'."
            )

        candidate_entities = await self.repo.get_candidates(shortlist_id)
        audit_log = await self.repo.get_audit_log(shortlist_id)

        candidates = [
            ShortlistCandidateItem(
                candidate_entry_id=c.candidate_entry_id,
                shortlist_id=c.shortlist_id,
                workspace_id=c.workspace_id,
                player_id=c.player_id,
                player_name=c.player_name,
                assigned_role=c.assigned_role,
                rank=c.rank,
                vor_score=c.vor_score,
                raw_composite_score=c.raw_composite_score,
                reliability_factor=c.reliability_factor,
                reliability_status=c.reliability_status,
                evaluation_ref=c.evaluation_ref,
                explainability_ref=c.explainability_ref,
                eligibility_status=EligibilityStatus(c.eligibility_status),
                review_status=ReviewStatus(c.review_status),
                reviewer_notes=c.reviewer_notes,
                selection_timestamp=c.selection_timestamp,
            )
            for c in candidate_entities
        ]

        return ShortlistResponse(
            shortlist_id=shortlist.shortlist_id,
            workspace_id=shortlist.workspace_id,
            name=shortlist.name,
            dataset_id=shortlist.dataset_id,
            scoring_run_id=shortlist.scoring_run_id,
            config_version=shortlist.config_version,
            methodology_version=shortlist.methodology_version,
            target_size=shortlist.target_size,
            eligible_count=shortlist.eligible_count,
            excluded_count=shortlist.excluded_count,
            shortlisted_count=shortlist.shortlisted_count,
            status=shortlist.status,
            candidates=candidates,
            exclusion_summary=audit_log.exclusion_details if audit_log else {},
            created_at=shortlist.created_at,
        )

    async def list_shortlists(
        self, workspace_id: str, limit: int = 50, offset: int = 0
    ) -> list[ShortlistSummaryResponse]:
        """List past shortlists for a workspace."""
        await self.workspace_service.get_workspace(workspace_id)
        items = await self.repo.list_shortlists_for_workspace(
            workspace_id=workspace_id, limit=limit, offset=offset
        )
        return [
            ShortlistSummaryResponse(
                shortlist_id=s.shortlist_id,
                workspace_id=s.workspace_id,
                name=s.name,
                dataset_id=s.dataset_id,
                scoring_run_id=s.scoring_run_id,
                config_version=s.config_version,
                methodology_version=s.methodology_version,
                target_size=s.target_size,
                eligible_count=s.eligible_count,
                excluded_count=s.excluded_count,
                shortlisted_count=s.shortlisted_count,
                status=s.status,
                created_at=s.created_at,
            )
            for s in items
        ]

    async def review_candidate(
        self,
        workspace_id: str,
        shortlist_id: str,
        player_id: str,
        payload: ShortlistReviewRequest,
    ) -> ShortlistCandidateItem:
        """Update reviewer disposition and notes without overwriting original evaluation scores."""
        await self.workspace_service.get_workspace(workspace_id)
        shortlist = await self.repo.get_shortlist(shortlist_id)
        if not shortlist:
            raise EntityNotFoundException("Shortlist", shortlist_id)
        if shortlist.workspace_id != workspace_id:
            raise WorkspaceException(
                f"Shortlist '{shortlist_id}' does not belong to workspace '{workspace_id}'."
            )

        candidate = await self.repo.get_candidate(shortlist_id, player_id)
        if not candidate:
            raise EntityNotFoundException("ShortlistCandidate", f"{shortlist_id}:{player_id}")

        # Update review workflow fields while strictly preserving evaluation metrics
        candidate.review_status = payload.review_status.value
        if payload.reviewer_notes is not None:
            candidate.reviewer_notes = payload.reviewer_notes

        await self.session.flush()
        await self.session.refresh(candidate)

        return ShortlistCandidateItem(
            candidate_entry_id=candidate.candidate_entry_id,
            shortlist_id=candidate.shortlist_id,
            workspace_id=candidate.workspace_id,
            player_id=candidate.player_id,
            player_name=candidate.player_name,
            assigned_role=candidate.assigned_role,
            rank=candidate.rank,
            vor_score=candidate.vor_score,
            raw_composite_score=candidate.raw_composite_score,
            reliability_factor=candidate.reliability_factor,
            reliability_status=candidate.reliability_status,
            evaluation_ref=candidate.evaluation_ref,
            explainability_ref=candidate.explainability_ref,
            eligibility_status=EligibilityStatus(candidate.eligibility_status),
            review_status=ReviewStatus(candidate.review_status),
            reviewer_notes=candidate.reviewer_notes,
            selection_timestamp=candidate.selection_timestamp,
        )

    async def get_audit_log(
        self, workspace_id: str, shortlist_id: str
    ) -> ShortlistAuditResponse:
        """Retrieve full audit record for a shortlist."""
        await self.workspace_service.get_workspace(workspace_id)
        shortlist = await self.repo.get_shortlist(shortlist_id)
        if not shortlist:
            raise EntityNotFoundException("Shortlist", shortlist_id)
        if shortlist.workspace_id != workspace_id:
            raise WorkspaceException(
                f"Shortlist '{shortlist_id}' does not belong to workspace '{workspace_id}'."
            )

        audit = await self.repo.get_audit_log(shortlist_id)
        if not audit:
            raise EntityNotFoundException("ShortlistAuditLog", shortlist_id)

        return ShortlistAuditResponse(
            audit_id=audit.audit_id,
            shortlist_id=audit.shortlist_id,
            workspace_id=audit.workspace_id,
            dataset_id=audit.dataset_id,
            configuration_version=audit.configuration_version,
            evaluation_methodology_version=audit.evaluation_methodology_version,
            metric_registry_version=audit.metric_registry_version,
            ranking_engine_version=audit.ranking_engine_version,
            generation_timestamp=audit.generation_timestamp,
            eligible_candidate_count=audit.eligible_candidate_count,
            excluded_candidate_count=audit.excluded_candidate_count,
            shortlisted_candidate_count=audit.shortlisted_candidate_count,
            exclusion_details=audit.exclusion_details or {},
        )

    def _resolve_scoring_run(
        self, dataset_id: str, run_id: str | None = None
    ) -> ScoringRunResponse | None:
        """Locate existing scoring run from memory cache or database."""
        if run_id:
            if run_id in RUN_CACHE:
                return RUN_CACHE[run_id]
            # Try via scoring service if method available
            try:
                return self.scoring_service.get_scoring_run(run_id)
            except Exception:
                pass

        # Otherwise find latest run for dataset
        for r in reversed(list(RUN_CACHE.values())):
            if r.dataset_id == dataset_id:
                return r

        return None
