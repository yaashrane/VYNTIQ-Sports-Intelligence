"""Orchestration service coordinating the 10-step cricket dataset ingestion pipeline."""

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.exceptions import EntityNotFoundException, ValidationException
from backend.app.core.logging import get_logger
from backend.app.models.dataset import Dataset, ValidationIssue
from backend.app.schemas.dataset import (
    InspectionReport,
    PersistenceResponse,
    ValidationIssueDetail,
    ValidationReport,
    ValidationSummary,
)
from backend.app.services.ingestion.inspector import DatasetInspector
from backend.app.services.ingestion.mapper import SchemaMapper
from backend.app.services.ingestion.normalizer import DataNormalizer
from backend.app.services.ingestion.persister import DataPersister
from backend.app.services.ingestion.validator import DataValidator

logger = get_logger("vyntiq.ingestion.pipeline")


class IngestionPipelineService:
    """Orchestrates inspection, mapping, validation, and persistence workflows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.mapper = SchemaMapper()
        self.inspector = DatasetInspector(self.mapper)
        self.normalizer = DataNormalizer()
        self.validator = DataValidator()
        self.persister = DataPersister(self.session)

    async def get_dataset_or_404(self, dataset_id: str) -> Dataset:
        """Fetch Dataset entity or raise EntityNotFoundException."""
        dataset = await self.session.get(Dataset, dataset_id)
        if not dataset:
            raise EntityNotFoundException(entity_name="Dataset", entity_id=dataset_id)
        return dataset

    async def inspect_dataset(self, dataset_id: str) -> InspectionReport:
        """Inspect headers, sample columns, and infer schema mapping."""
        dataset = await self.get_dataset_or_404(dataset_id)
        return self.inspector.inspect_dataset(dataset)

    async def validate_dataset(
        self, dataset_id: str, custom_mapping: dict[str, str] | None = None
    ) -> ValidationReport:
        """Execute full dataset normalization and two-tiered validation."""
        dataset = await self.get_dataset_or_404(dataset_id)

        dataset.status = "PROCESSING"
        await self.session.flush()

        # 1. Load full raw dataframe
        raw_df = self.inspector.load_dataframe_sample(
            file_path=dataset.storage_path,
            format_type=dataset.file_format,
            nrows=None,  # Load all rows
        )

        # 2. Derive and verify column mapping
        mapper = SchemaMapper(custom_mapping=custom_mapping)
        source_columns = [str(c) for c in raw_df.columns]
        mapping = mapper.detect_mapping(source_columns)

        missing_required = mapper.check_missing_required(mapping)
        if missing_required:
            dataset.status = "REJECTED"
            await self.session.flush()
            raise ValidationException(
                message=f"Dataset is missing mandatory fields: {', '.join(missing_required)}",
                code="MISSING_MANDATORY_FIELDS",
                details=[{"field": f, "message": "Required for analytical calculation"} for f in missing_required],
            )

        # 3. Normalize records
        normalized_df = self.normalizer.normalize_dataframe(
            df=raw_df,
            column_mapping=mapping,
            dataset_id=dataset.dataset_id,
            workspace_id=dataset.workspace_id,
            origin_type=dataset.origin_type,
        )

        # 4. Two-Tiered Validation
        valid_df, issues, report = self.validator.validate_deliveries(
            df=normalized_df, dataset_id=dataset.dataset_id
        )

        # Update dataset stats
        dataset.status = report.summary.status
        dataset.total_rows = report.summary.total_records
        dataset.valid_rows = report.summary.valid_records
        dataset.quarantined_rows = report.summary.invalid_records
        await self.session.flush()

        # Store issues in DB
        if issues:
            self.session.add_all(issues)
            await self.session.flush()

        report.summary.unmapped_columns = mapper.identify_unmapped(source_columns, mapping)
        return report

    async def get_validation_report(self, dataset_id: str) -> ValidationReport:
        """Fetch previously recorded validation report and quality summary."""
        dataset = await self.get_dataset_or_404(dataset_id)

        # Query recorded validation issues
        query = select(ValidationIssue).where(ValidationIssue.dataset_id == dataset_id)
        result = await self.session.execute(query)
        issues = list(result.scalars().all())

        error_count = sum(1 for iss in issues if "WARNING" not in iss.error_type)
        warning_count = len(issues) - error_count

        summary = ValidationSummary(
            dataset_id=dataset.dataset_id,
            status=dataset.status,
            total_records=dataset.total_rows,
            valid_records=dataset.valid_rows,
            invalid_records=dataset.quarantined_rows,
            duplicate_records=sum(1 for iss in issues if iss.error_type == "DUPLICATE_RECORD"),
            unmapped_columns=[],
            missing_fields_summary={},
            error_count=error_count,
            warning_count=warning_count,
            validated_at=dataset.updated_at or datetime.now(timezone.utc),
        )

        sample_issues = [
            ValidationIssueDetail(
                issue_id=iss.issue_id,
                row_index=iss.row_index,
                field_name=iss.field_name,
                error_type=iss.error_type,
                error_message=iss.error_message,
                raw_value=iss.raw_value,
            )
            for iss in issues[:50]
        ]

        return ValidationReport(summary=summary, sample_issues=sample_issues)

    async def persist_dataset(
        self, dataset_id: str, custom_mapping: dict[str, str] | None = None
    ) -> PersistenceResponse:
        """Normalize, validate, and persist records into canonical database tables."""
        dataset = await self.get_dataset_or_404(dataset_id)

        # Load raw dataframe
        raw_df = self.inspector.load_dataframe_sample(
            file_path=dataset.storage_path,
            format_type=dataset.file_format,
            nrows=None,
        )

        mapper = SchemaMapper(custom_mapping=custom_mapping)
        source_columns = [str(c) for c in raw_df.columns]
        mapping = mapper.detect_mapping(source_columns)

        missing_required = mapper.check_missing_required(mapping)
        if missing_required:
            raise ValidationException(
                message=f"Cannot persist dataset. Missing mandatory fields: {', '.join(missing_required)}",
                code="MISSING_MANDATORY_FIELDS",
            )

        norm_df = self.normalizer.normalize_dataframe(
            df=raw_df,
            column_mapping=mapping,
            dataset_id=dataset.dataset_id,
            workspace_id=dataset.workspace_id,
            origin_type=dataset.origin_type,
        )

        valid_df, issues, _ = self.validator.validate_deliveries(
            df=norm_df, dataset_id=dataset.dataset_id
        )

        return await self.persister.persist_validated_dataset(
            valid_df=valid_df, issues=issues, dataset=dataset
        )
