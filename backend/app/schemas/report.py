"""Pydantic schemas for PDF report generation, export requests, metadata, and audit records."""

from enum import Enum
from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """Supported report generation types."""

    COMPETITION_OVERVIEW = "COMPETITION_OVERVIEW"
    INDIVIDUAL_PLAYER = "INDIVIDUAL_PLAYER"
    PLAYER_COMPARISON = "PLAYER_COMPARISON"
    SHORTLIST = "SHORTLIST"


class ReportStatus(str, Enum):
    """Report generation processing status."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReportCreateRequest(BaseModel):
    """Payload to request PDF report generation."""

    report_type: ReportType
    title: str | None = Field(default=None, description="Custom document title override")
    player_id: str | None = Field(default=None, description="Candidate ID required for INDIVIDUAL_PLAYER reports")
    comparison_player_ids: list[str] | None = Field(
        default=None, description="2 to 5 candidate IDs required for PLAYER_COMPARISON reports"
    )
    shortlist_id: str | None = Field(
        default=None, description="Optional target shortlist ID for SHORTLIST reports (defaults to active)"
    )
    run_id: str | None = Field(default=None, description="Optional scoring run reference (defaults to latest)")
    dataset_id: str | None = Field(default=None, description="Optional dataset reference")
    include_reviewer_notes: bool = Field(
        default=False,
        description="Whether to include private reviewer notes in exported reports (privacy safeguard)",
    )
    sections: list[str] = Field(
        default_factory=list, description="Optional specific section flags to include or exclude"
    )


class ReportResponse(BaseModel):
    """Export metadata and audit record for a generated PDF report."""

    report_id: str
    workspace_id: str | None
    report_type: ReportType
    title: str
    filename: str
    download_url: str
    file_size_bytes: int
    sha256_hash: str
    dataset_reference: str | None
    metric_registry_version: str
    evaluation_methodology_version: str
    ranking_engine_version: str
    report_template_version: str
    source_evaluation_references: list[str]
    configuration: dict
    generation_status: str
    created_at: str


class ReportListResponse(BaseModel):
    """Collection envelope for generated report metadata records."""

    total: int
    reports: list[ReportResponse]

