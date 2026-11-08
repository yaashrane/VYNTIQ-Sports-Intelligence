"""Reporting service orchestrating data validation, PDF compilation, storage, and audit logging."""

import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.exceptions import EntityNotFoundException, ValidationException
from backend.app.models.report import GeneratedReport
from backend.app.repositories.report import ReportRepository
from backend.app.schemas.report import (
    ReportCreateRequest,
    ReportListResponse,
    ReportResponse,
    ReportStatus,
    ReportType,
)
from backend.app.services.reporting.data_preparer import ReportDataPreparer
from backend.app.services.reporting.renderer import ReportRenderer
from backend.app.services.reporting.storage import ReportStorage


class ReportingService:
    """Manages the full lifecycle of generated PDF reports and audit metadata."""

    def __init__(
        self,
        session: AsyncSession,
        storage: ReportStorage | None = None,
        renderer: ReportRenderer | None = None,
        data_preparer: ReportDataPreparer | None = None,
    ) -> None:
        self.session = session
        self.repo = ReportRepository(session)
        self.storage = storage or ReportStorage()
        self.renderer = renderer or ReportRenderer()
        self.data_preparer = data_preparer or ReportDataPreparer(session)

    async def generate_report(
        self, workspace_id: str | None, request: ReportCreateRequest
    ) -> ReportResponse:
        """Validate domain data, compile vector PDF, persist file safely, and record audit log."""
        # 1. Prepare and validate domain data (raises structured exceptions if missing)
        prepared_data = await self.data_preparer.prepare_data(
            request.report_type, workspace_id, request
        )

        # 2. Determine context identifier for filename
        if request.report_type == ReportType.INDIVIDUAL_PLAYER:
            context_id = request.player_id
        elif request.report_type == ReportType.PLAYER_COMPARISON:
            context_id = "_vs_".join(request.comparison_player_ids[:2]) if request.comparison_player_ids else "COMPARE"
        elif request.report_type == ReportType.SHORTLIST:
            context_id = request.shortlist_id or workspace_id
        else:
            context_id = workspace_id

        # 3. Generate safe filename and target path
        filename = self.storage.generate_safe_filename(request.report_type.value, context_id)
        output_path = self.storage.get_file_path(filename)

        # 4. Compile PDF
        report_id = f"rep_{uuid.uuid4().hex[:12]}"
        self.renderer.render_pdf(prepared_data, output_path)

        # 5. Compute cryptographic digest and file metrics
        file_size = self.storage.get_file_size(output_path)
        sha256_hash = self.storage.compute_sha256(output_path)

        # 6. Build download URL
        if workspace_id:
            download_url = f"/api/v1/workspaces/{workspace_id}/reports/{report_id}/download"
        else:
            download_url = f"/api/v1/reports/{report_id}/download"

        # 7. Persist audit entity
        report_entity = GeneratedReport(
            report_id=report_id,
            workspace_id=workspace_id,
            report_type=request.report_type.value,
            title=prepared_data.get("title", f"{request.report_type.value} Report"),
            filename=filename,
            file_path=str(output_path),
            file_size_bytes=file_size,
            sha256_hash=sha256_hash,
            dataset_reference=prepared_data.get("dataset", {}).get("dataset_id")
            if isinstance(prepared_data.get("dataset"), dict)
            else prepared_data.get("provenance", {}).get("dataset_id"),
            metric_registry_version="1.0.0",
            evaluation_methodology_version=prepared_data.get("methodology_version", "1.0.0"),
            ranking_engine_version="1.0.0",
            report_template_version="1.0.0",
            source_evaluation_references=prepared_data.get("source_references", []),
            configuration=request.model_dump(),
            generation_status=ReportStatus.COMPLETED.value,
        )

        saved = await self.repo.create(report_entity)
        await self.session.commit()

        return self._to_schema(saved, download_url)

    async def get_report_metadata(
        self, report_id: str, workspace_id: str | None = None
    ) -> ReportResponse:
        """Fetch report audit metadata by unique report_id."""
        report = await self.repo.get_by_report_id(report_id)
        if not report:
            raise EntityNotFoundException("Report", report_id)
        if workspace_id and report.workspace_id and report.workspace_id != workspace_id:
            raise EntityNotFoundException("Report", report_id)

        ws_id = report.workspace_id or workspace_id
        download_url = (
            f"/api/v1/workspaces/{ws_id}/reports/{report_id}/download"
            if ws_id
            else f"/api/v1/reports/{report_id}/download"
        )
        return self._to_schema(report, download_url)

    async def list_workspace_reports(
        self, workspace_id: str, limit: int = 100, offset: int = 0
    ) -> ReportListResponse:
        """Fetch all reports generated within a competition workspace context."""
        reports = await self.repo.list_by_workspace_id(workspace_id, limit, offset)
        items = [
            self._to_schema(
                r, f"/api/v1/workspaces/{workspace_id}/reports/{r.report_id}/download"
            )
            for r in reports
        ]
        return ReportListResponse(total=len(items), reports=items)

    async def get_report_file(self, report_id: str) -> tuple[Path, str]:
        """Fetch verified on-disk file path and safe download filename for HTTP streaming."""
        report = await self.repo.get_by_report_id(report_id)
        if not report:
            raise EntityNotFoundException("Report", report_id)

        file_path = Path(report.file_path)
        if not file_path.exists():
            raise EntityNotFoundException(
                "ReportFile", f"PDF file for report '{report_id}' was not found on disk."
            )

        return file_path, report.filename

    def _to_schema(self, entity: GeneratedReport, download_url: str) -> ReportResponse:
        """Map SQLAlchemy model to API response schema without exposing local file path."""
        return ReportResponse(
            report_id=entity.report_id,
            workspace_id=entity.workspace_id,
            report_type=ReportType(entity.report_type),
            title=entity.title,
            filename=entity.filename,
            download_url=download_url,
            file_size_bytes=entity.file_size_bytes,
            sha256_hash=entity.sha256_hash,
            dataset_reference=entity.dataset_reference,
            metric_registry_version=entity.metric_registry_version,
            evaluation_methodology_version=entity.evaluation_methodology_version,
            ranking_engine_version=entity.ranking_engine_version,
            report_template_version=entity.report_template_version,
            source_evaluation_references=entity.source_evaluation_references,
            configuration=entity.configuration,
            generation_status=entity.generation_status,
            created_at=str(entity.created_at),
        )
