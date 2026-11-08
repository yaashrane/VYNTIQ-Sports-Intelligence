"""API endpoints for PDF report compilation, metadata retrieval, and secure file downloads."""

from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.dependencies import get_db
from backend.app.schemas.report import (
    ReportCreateRequest,
    ReportListResponse,
    ReportResponse,
)
from backend.app.services.reporting.service import ReportingService

# Router for workspace-scoped report operations
workspace_reports_router = APIRouter(
    prefix="/workspaces/{workspace_id}/reports",
    tags=["PDF Reporting & Export Engine"],
)

# Router for standalone/direct report operations
global_reports_router = APIRouter(
    prefix="/reports",
    tags=["PDF Reporting & Export Engine"],
)


# ==============================================================================
# WORKSPACE-SCOPED REPORT ENDPOINTS
# ==============================================================================

@workspace_reports_router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Workspace PDF Report",
    description="Validate domain evaluation data, compile a vector PDF report, persist it safely, and return audit metadata.",
)
async def generate_workspace_report(
    workspace_id: str,
    payload: ReportCreateRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Generate a PDF report scoped to a specific competition workspace."""
    service = ReportingService(session)
    return await service.generate_report(workspace_id=workspace_id, request=payload)


@workspace_reports_router.get(
    "",
    response_model=ReportListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Workspace Reports",
    description="Retrieve audit metadata for all PDF reports generated within this workspace.",
)
async def list_workspace_reports(
    workspace_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ReportListResponse:
    """List all reports for the given workspace."""
    service = ReportingService(session)
    return await service.list_workspace_reports(workspace_id=workspace_id, limit=limit, offset=offset)


@workspace_reports_router.get(
    "/{report_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Workspace Report Metadata",
    description="Retrieve audit metadata for a specific generated report.",
)
async def get_workspace_report_metadata(
    workspace_id: str,
    report_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Fetch report audit metadata."""
    service = ReportingService(session)
    return await service.get_report_metadata(report_id=report_id, workspace_id=workspace_id)


@workspace_reports_router.get(
    "/{report_id}/download",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Download Workspace PDF Report",
    description="Stream the verified vector PDF file for download with safe content disposition.",
)
async def download_workspace_report(
    workspace_id: str,
    report_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    """Download the generated PDF report file."""
    service = ReportingService(session)
    file_path, filename = await service.get_report_file(report_id)
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ==============================================================================
# GLOBAL / STANDALONE REPORT ENDPOINTS
# ==============================================================================

@global_reports_router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Standalone PDF Report",
    description="Compile a standalone individual player or head-to-head comparison PDF report.",
)
async def generate_standalone_report(
    payload: ReportCreateRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Generate a standalone PDF report."""
    service = ReportingService(session)
    return await service.generate_report(workspace_id=None, request=payload)


@global_reports_router.get(
    "/{report_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Report Metadata by ID",
    description="Retrieve audit record for a report by report_id.",
)
async def get_report_metadata(
    report_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Fetch report metadata."""
    service = ReportingService(session)
    return await service.get_report_metadata(report_id=report_id)


@global_reports_router.get(
    "/{report_id}/download",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Download PDF Report",
    description="Stream the generated PDF document by report ID.",
)
async def download_report(
    report_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    """Stream PDF document for download."""
    service = ReportingService(session)
    file_path, filename = await service.get_report_file(report_id)
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
