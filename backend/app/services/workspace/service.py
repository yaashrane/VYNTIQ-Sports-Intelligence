"""Workspace management service orchestrating competition workspaces and configuration lifecycles."""

import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.exceptions import (
    ConflictException,
    EntityNotFoundException,
    ValidationException,
    WorkspaceException,
)
from backend.app.models.workspace import Workspace, WorkspaceConfiguration
from backend.app.repositories.workspace import WorkspaceRepository
from backend.app.schemas.workspace import (
    AgeCriteria,
    CompetitionConfigCreate,
    CompetitionConfigResponse,
    CompetitionConfigUpdate,
    ParticipationCriteria,
    SportType,
    WorkspaceCreate,
    WorkspaceDetailResponse,
    WorkspaceResponse,
    WorkspaceStatus,
    WorkspaceUpdate,
)

# Valid state machine transitions
ALLOWED_TRANSITIONS: dict[WorkspaceStatus, set[WorkspaceStatus]] = {
    WorkspaceStatus.DRAFT: {WorkspaceStatus.ACTIVE, WorkspaceStatus.ARCHIVED},
    WorkspaceStatus.ACTIVE: {WorkspaceStatus.COMPLETED, WorkspaceStatus.ARCHIVED},
    WorkspaceStatus.COMPLETED: {WorkspaceStatus.ARCHIVED},
    WorkspaceStatus.ARCHIVED: set(),  # Terminal state
}


class WorkspaceService:
    """Manages workspace lifecycle, configuration, and data isolation boundaries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = WorkspaceRepository(session)

    async def create_workspace(self, payload: WorkspaceCreate) -> WorkspaceDetailResponse:
        """Create a new independent competition workspace with baseline configuration."""
        name = payload.name.strip()
        if not name:
            raise ValidationException("Workspace name cannot be empty.")

        ws_id = payload.workspace_id or f"ws_{uuid.uuid4().hex[:12]}"
        existing = await self.repo.get_by_workspace_id(ws_id)
        if existing:
            raise ConflictException(f"Workspace with ID '{ws_id}' already exists.")

        workspace = Workspace(
            workspace_id=ws_id,
            name=name,
            description=payload.description,
            sport_type=payload.sport_type.value,
            competition_name=payload.competition_name.strip(),
            season_or_edition=payload.season_or_edition.strip(),
            status=WorkspaceStatus.DRAFT.value,
            dataset_references=payload.dataset_references,
        )
        await self.repo.create(workspace)

        # Initialize configuration
        init_conf = payload.initial_configuration or CompetitionConfigCreate()
        config_entity = WorkspaceConfiguration(
            config_id=f"cfg_{uuid.uuid4().hex[:12]}",
            workspace_id=ws_id,
            target_sport=init_conf.target_sport.value,
            target_roles=init_conf.target_roles,
            min_age=init_conf.age_criteria.min_age if init_conf.age_criteria else None,
            max_age=init_conf.age_criteria.max_age if init_conf.age_criteria else None,
            age_cutoff_date=init_conf.age_criteria.age_cutoff_date
            if init_conf.age_criteria
            else None,
            min_matches=init_conf.participation_criteria.min_matches
            if init_conf.participation_criteria
            else None,
            min_balls_faced=init_conf.participation_criteria.min_balls_faced
            if init_conf.participation_criteria
            else None,
            min_legal_balls_bowled=init_conf.participation_criteria.min_legal_balls_bowled
            if init_conf.participation_criteria
            else None,
            required_metrics=init_conf.required_metrics,
            evaluation_profile_version=init_conf.evaluation_profile_version,
            shortlist_size=init_conf.shortlist_size,
            custom_eligibility_rules=init_conf.custom_eligibility_rules,
            dataset_ids=init_conf.dataset_ids or payload.dataset_references,
            version="1.0.0",
        )
        await self.repo.save_configuration(config_entity)

        return await self.get_workspace_detail(ws_id)

    async def list_workspaces(
        self, limit: int = 100, offset: int = 0, status: WorkspaceStatus | None = None
    ) -> list[WorkspaceResponse]:
        """List all workspaces with optional status filter."""
        items = await self.repo.list_workspaces(
            limit=limit, offset=offset, status=status.value if status else None
        )
        return [
            WorkspaceResponse(
                workspace_id=w.workspace_id,
                name=w.name,
                description=w.description,
                sport_type=w.sport_type,
                competition_name=w.competition_name,
                season_or_edition=w.season_or_edition,
                status=WorkspaceStatus(w.status),
                dataset_references=w.dataset_references or [],
                created_at=w.created_at,
                updated_at=w.updated_at,
            )
            for w in items
        ]

    async def get_workspace(self, workspace_id: str) -> Workspace:
        """Fetch workspace or raise 404 EntityNotFoundException."""
        ws = await self.repo.get_by_workspace_id(workspace_id)
        if not ws:
            raise EntityNotFoundException("Workspace", workspace_id)
        return ws

    async def get_workspace_detail(self, workspace_id: str) -> WorkspaceDetailResponse:
        """Fetch full workspace detail including its active configuration."""
        ws = await self.get_workspace(workspace_id)
        conf_entity = await self.repo.get_configuration(workspace_id)
        conf_resp = self._serialize_configuration(conf_entity) if conf_entity else None
        shortlists = await self.repo.list_shortlists_for_workspace(workspace_id)

        return WorkspaceDetailResponse(
            workspace_id=ws.workspace_id,
            name=ws.name,
            description=ws.description,
            sport_type=ws.sport_type,
            competition_name=ws.competition_name,
            season_or_edition=ws.season_or_edition,
            status=WorkspaceStatus(ws.status),
            dataset_references=ws.dataset_references or [],
            created_at=ws.created_at,
            updated_at=ws.updated_at,
            configuration=conf_resp,
            shortlists_count=len(shortlists),
        )

    async def update_workspace(
        self, workspace_id: str, payload: WorkspaceUpdate
    ) -> WorkspaceResponse:
        """Update workspace metadata or transition its lifecycle status."""
        ws = await self.get_workspace(workspace_id)

        if payload.name is not None:
            clean_name = payload.name.strip()
            if not clean_name:
                raise ValidationException("Workspace name cannot be empty.")
            ws.name = clean_name

        if payload.description is not None:
            ws.description = payload.description

        if payload.competition_name is not None:
            ws.competition_name = payload.competition_name.strip()

        if payload.season_or_edition is not None:
            ws.season_or_edition = payload.season_or_edition.strip()

        if payload.dataset_references is not None:
            ws.dataset_references = payload.dataset_references

        if payload.status is not None and payload.status != WorkspaceStatus(ws.status):
            current_status = WorkspaceStatus(ws.status)
            new_status = payload.status
            allowed = ALLOWED_TRANSITIONS.get(current_status, set())
            if new_status not in allowed:
                raise ValidationException(
                    f"Invalid workspace status transition from '{current_status.value}' to '{new_status.value}'. "
                    f"Allowed target states: {[s.value for s in allowed]}"
                )
            ws.status = new_status.value

        ws.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(ws)

        return WorkspaceResponse(
            workspace_id=ws.workspace_id,
            name=ws.name,
            description=ws.description,
            sport_type=ws.sport_type,
            competition_name=ws.competition_name,
            season_or_edition=ws.season_or_edition,
            status=WorkspaceStatus(ws.status),
            dataset_references=ws.dataset_references or [],
            created_at=ws.created_at,
            updated_at=ws.updated_at,
        )

    async def archive_workspace(self, workspace_id: str) -> WorkspaceResponse:
        """Archive a workspace, setting its state to ARCHIVED."""
        return await self.update_workspace(
            workspace_id, WorkspaceUpdate(status=WorkspaceStatus.ARCHIVED)
        )

    async def get_configuration(
        self, workspace_id: str
    ) -> CompetitionConfigResponse:
        """Fetch active competition configuration for a workspace."""
        await self.get_workspace(workspace_id)  # Validate existence
        conf = await self.repo.get_configuration(workspace_id)
        if not conf:
            raise EntityNotFoundException("WorkspaceConfiguration", workspace_id)
        return self._serialize_configuration(conf)

    async def update_configuration(
        self, workspace_id: str, payload: CompetitionConfigUpdate
    ) -> CompetitionConfigResponse:
        """Update competition configuration parameters."""
        await self.get_workspace(workspace_id)
        conf = await self.repo.get_configuration(workspace_id)
        if not conf:
            raise EntityNotFoundException("WorkspaceConfiguration", workspace_id)

        if payload.target_roles is not None:
            conf.target_roles = payload.target_roles
        if payload.age_criteria is not None:
            conf.min_age = payload.age_criteria.min_age
            conf.max_age = payload.age_criteria.max_age
            conf.age_cutoff_date = payload.age_criteria.age_cutoff_date
        if payload.participation_criteria is not None:
            conf.min_matches = payload.participation_criteria.min_matches
            conf.min_balls_faced = payload.participation_criteria.min_balls_faced
            conf.min_legal_balls_bowled = payload.participation_criteria.min_legal_balls_bowled
        if payload.required_metrics is not None:
            conf.required_metrics = payload.required_metrics
        if payload.evaluation_profile_version is not None:
            conf.evaluation_profile_version = payload.evaluation_profile_version
        if payload.shortlist_size is not None:
            conf.shortlist_size = payload.shortlist_size
        if payload.custom_eligibility_rules is not None:
            conf.custom_eligibility_rules = payload.custom_eligibility_rules
        if payload.dataset_ids is not None:
            conf.dataset_ids = payload.dataset_ids

        # Increment minor version
        try:
            parts = conf.version.split(".")
            conf.version = f"{parts[0]}.{int(parts[1]) + 1}.0"
        except Exception:
            conf.version = "1.1.0"

        conf.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(conf)

        return self._serialize_configuration(conf)

    async def get_workspace_datasets(self, workspace_id: str) -> list[dict]:
        """Fetch datasets scoped to this workspace, respecting tenant isolation."""
        await self.get_workspace(workspace_id)
        datasets = await self.repo.get_workspace_datasets(workspace_id)
        return [
            {
                "dataset_id": d.dataset_id,
                "workspace_id": d.workspace_id,
                "origin_type": d.origin_type,
                "source_filename": d.source_filename,
                "status": d.status,
                "total_rows": d.total_rows,
                "valid_rows": d.valid_rows,
                "quarantined_rows": d.quarantined_rows,
                "created_at": d.created_at,
            }
            for d in datasets
        ]

    def _serialize_configuration(
        self, conf: WorkspaceConfiguration
    ) -> CompetitionConfigResponse:
        """Helper to format DB configuration model into response schema."""
        has_age = bool(conf.min_age or conf.max_age or conf.age_cutoff_date)
        age_crit = (
            AgeCriteria(
                min_age=conf.min_age,
                max_age=conf.max_age,
                age_cutoff_date=conf.age_cutoff_date,
            )
            if has_age
            else None
        )

        has_part = bool(
            conf.min_matches or conf.min_balls_faced or conf.min_legal_balls_bowled
        )
        part_crit = (
            ParticipationCriteria(
                min_matches=conf.min_matches,
                min_balls_faced=conf.min_balls_faced,
                min_legal_balls_bowled=conf.min_legal_balls_bowled,
            )
            if has_part
            else None
        )

        return CompetitionConfigResponse(
            config_id=conf.config_id,
            workspace_id=conf.workspace_id,
            target_sport=conf.target_sport,
            target_roles=conf.target_roles or [],
            age_criteria=age_crit,
            participation_criteria=part_crit,
            required_metrics=conf.required_metrics or [],
            evaluation_profile_version=conf.evaluation_profile_version,
            shortlist_size=conf.shortlist_size,
            custom_eligibility_rules=conf.custom_eligibility_rules or {},
            dataset_ids=conf.dataset_ids or [],
            version=conf.version,
            created_at=conf.created_at,
            updated_at=conf.updated_at,
        )

