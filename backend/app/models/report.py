"""Relational model for generated PDF reports, metadata, and audit records."""

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TimestampMixin


class GeneratedReport(Base, TimestampMixin):
    """Immutable audit record and metadata for a generated PDF report."""

    __tablename__ = "generated_reports"

    report_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metric_registry_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    evaluation_methodology_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    ranking_engine_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    report_template_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    source_evaluation_references: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    configuration: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    generation_status: Mapped[str] = mapped_column(String(32), default="COMPLETED", nullable=False)
