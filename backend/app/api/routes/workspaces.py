"""API routes for competition workspaces, evaluation configuration, shortlisting, and candidate reviews."""

from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.dependencies import get_db
from backend.app.schemas.workspace import (
    CompetitionConfigResponse,
    CompetitionConfigUpdate,
    ShortlistAuditResponse,
    ShortlistCandidateItem,
    ShortlistGenerateRequest,
    ShortlistResponse,
    ShortlistReviewRequest,
    ShortlistSummaryResponse,
    WorkspaceCreate,
    WorkspaceDetailResponse,
    WorkspaceResponse,
    WorkspaceStatus,
    WorkspaceUpdate,
)
from backend.app.services.shortlisting.service import ShortlistingService
from backend.app.services.workspace.service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Competition Workspaces & Shortlisting"])


# ==============================================================================
# WORKSPACE MANAGEMENT
# ==============================================================================

@router.post(
    "",
    response_model=WorkspaceDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Competition Workspace",
    description="Provision an independent competition workspace sandbox with initial evaluation configuration.",
)
async def create_workspace(
    payload: WorkspaceCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceDetailResponse:
    """Create a new workspace."""
    service = WorkspaceService(session)
    return await service.create_workspace(payload)


@router.get(
    "",
    response_model=list[WorkspaceResponse],
    status_code=status.HTTP_200_OK,
    summary="List Workspaces",
    description="Retrieve all workspaces with optional lifecycle status filtering.",
)
async def list_workspaces(
    session: Annotated[AsyncSession, Depends(get_db)],
    status: WorkspaceStatus | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[WorkspaceResponse]:
    """List workspaces."""
    service = WorkspaceService(session)
    return await service.list_workspaces(limit=limit, offset=offset, status=status)


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Workspace Detail",
    description="Retrieve full workspace details including active configuration and shortlist count.",
)
async def get_workspace(
    workspace_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceDetailResponse:
    """Get workspace details."""
    service = WorkspaceService(session)
    return await service.get_workspace_detail(workspace_id)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Workspace",
    description="Modify workspace metadata or transition its lifecycle status according to valid state machine rules.",
)
async def update_workspace(
    workspace_id: str,
    payload: WorkspaceUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    """Update workspace properties."""
    service = WorkspaceService(session)
    return await service.update_workspace(workspace_id, payload)


@router.delete(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive Workspace",
    description="Archive a workspace, moving it into ARCHIVED status.",
)
async def archive_workspace(
    workspace_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    """Archive workspace."""
    service = WorkspaceService(session)
    return await service.archive_workspace(workspace_id)


# ==============================================================================
# CONFIGURATION & DATASETS
# ==============================================================================

@router.get(
    "/{workspace_id}/configuration",
    response_model=CompetitionConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Competition Configuration",
    description="Retrieve the active evaluation, eligibility, and sample requirements for the workspace.",
)
async def get_configuration(
    workspace_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CompetitionConfigResponse:
    """Get configuration."""
    service = WorkspaceService(session)
    return await service.get_configuration(workspace_id)


@router.put(
    "/{workspace_id}/configuration",
    response_model=CompetitionConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Competition Configuration",
    description="Modify role requirements, age criteria, minimum participation thresholds, or shortlist size.",
)
async def update_configuration(
    workspace_id: str,
    payload: CompetitionConfigUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CompetitionConfigResponse:
    """Update configuration."""
    service = WorkspaceService(session)
    return await service.update_configuration(workspace_id, payload)


@router.get(
    "/{workspace_id}/datasets",
    response_model=list[dict],
    status_code=status.HTTP_200_OK,
    summary="Get Workspace Datasets",
    description="Retrieve datasets accessible to this workspace under tenant isolation boundaries.",
)
async def get_workspace_datasets(
    workspace_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """Get accessible datasets."""
    service = WorkspaceService(session)
    return await service.get_workspace_datasets(workspace_id)


# ==============================================================================
# SHORTLISTS & REVIEWS
# ==============================================================================

@router.post(
    "/{workspace_id}/shortlists",
    response_model=ShortlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Player Shortlist",
    description="Apply competition eligibility criteria to scored players, select top VOR candidates, and record audit log.",
)
async def generate_shortlist(
    workspace_id: str,
    payload: ShortlistGenerateRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ShortlistResponse:
    """Generate candidate shortlist."""
    service = ShortlistingService(session)
    return await service.generate_shortlist(workspace_id, payload)


@router.get(
    "/{workspace_id}/shortlists",
    response_model=list[ShortlistSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Shortlists",
    description="Retrieve all previously generated shortlists for this workspace.",
)
async def list_shortlists(
    workspace_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ShortlistSummaryResponse]:
    """List shortlists."""
    service = ShortlistingService(session)
    return await service.list_shortlists(workspace_id, limit=limit, offset=offset)


@router.get(
    "/{workspace_id}/shortlists/{shortlist_id}",
    response_model=ShortlistResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Shortlist Details",
    description="Retrieve a shortlist by ID, including its ordered candidates, review dispositions, and exclusion summaries.",
)
async def get_shortlist_detail(
    workspace_id: str,
    shortlist_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ShortlistResponse:
    """Get shortlist details."""
    service = ShortlistingService(session)
    return await service.get_shortlist(workspace_id, shortlist_id)


@router.post(
    "/{workspace_id}/shortlists/{shortlist_id}/candidates/{player_id}/review",
    response_model=ShortlistCandidateItem,
    status_code=status.HTTP_200_OK,
    summary="Review Shortlist Candidate",
    description="Submit scout/analyst review status (APPROVED, REJECTED, NEEDS_REVIEW, PENDING) and notes without altering original scores.",
)
@router.patch(
    "/{workspace_id}/shortlists/{shortlist_id}/candidates/{player_id}/review",
    response_model=ShortlistCandidateItem,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def review_candidate(
    workspace_id: str,
    shortlist_id: str,
    player_id: str,
    payload: ShortlistReviewRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ShortlistCandidateItem:
    """Review candidate."""
    service = ShortlistingService(session)
    return await service.review_candidate(workspace_id, shortlist_id, player_id, payload)


@router.get(
    "/{workspace_id}/shortlists/{shortlist_id}/audit",
    response_model=ShortlistAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Shortlist Audit Trail",
    description="Retrieve audit record verifying generation parameters, version numbers, and machine-readable exclusion reasons.",
)
async def get_shortlist_audit(
    workspace_id: str,
    shortlist_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ShortlistAuditResponse:
    """Get shortlist audit."""
    service = ShortlistingService(session)
    return await service.get_audit_log(workspace_id, shortlist_id)
