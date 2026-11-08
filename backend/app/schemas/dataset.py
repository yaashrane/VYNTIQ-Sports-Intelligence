"""Pydantic schemas for dataset uploads, inspection, validation, and quality reports."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class DatasetUploadResponse(BaseModel):
    """Initial receipt returned upon dataset upload."""

    dataset_id: str
    filename: str
    file_format: str
    file_size_bytes: int
    status: str
    message: str


class ColumnInspectionInfo(BaseModel):
    """Diagnostic profile of an uploaded file column."""

    column_name: str
    inferred_type: str
    non_null_count: int
    null_count: int
    sample_values: list[Any] = Field(default_factory=list)
    suggested_canonical_field: str | None = None


class InspectionReport(BaseModel):
    """Detailed structural inspection of an uploaded raw dataset."""

    dataset_id: str
    filename: str
    file_format: str
    file_size_bytes: int
    total_columns: int
    total_rows_estimated: int
    columns: list[ColumnInspectionInfo]
    unmapped_columns: list[str] = Field(default_factory=list)
    missing_required_fields: list[str] = Field(default_factory=list)


class ValidationIssueDetail(BaseModel):
    """Granular record-level validation failure descriptor."""

    issue_id: str
    row_index: int | None = None
    field_name: str | None = None
    error_type: str
    error_message: str
    raw_value: str | None = None


class ValidationSummary(BaseModel):
    """Aggregated metrics from dataset validation execution."""

    dataset_id: str
    status: str
    total_records: int
    valid_records: int
    invalid_records: int
    duplicate_records: int
    unmapped_columns: list[str] = Field(default_factory=list)
    missing_fields_summary: dict[str, int] = Field(default_factory=dict)
    error_count: int
    warning_count: int
    validated_at: datetime


class ValidationReport(BaseModel):
    """Full data quality and audit report for an ingestion job."""

    summary: ValidationSummary
    sample_issues: list[ValidationIssueDetail] = Field(default_factory=list)


class ValidationRequest(BaseModel):
    """Optional user-supplied overrides for column mapping."""

    column_mapping: dict[str, str] | None = Field(
        default=None,
        description="Explicit map of {source_column_name: canonical_field_name}",
    )


class PersistenceResponse(BaseModel):
    """Result of controlled database persistence for validated records."""

    dataset_id: str
    status: str
    deliveries_persisted: int
    matches_persisted: int
    players_persisted: int
    persisted_at: datetime
