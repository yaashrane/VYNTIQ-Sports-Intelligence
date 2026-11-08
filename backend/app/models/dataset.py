"""Database entity models for datasets, uploads, and data quality issues."""

from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TimestampMixin


class Dataset(Base, TimestampMixin):
    """Tracks uploaded files, dataset provenance, and validation lifecycle."""

    __tablename__ = "datasets"

    dataset_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    origin_type: Mapped[str] = mapped_column(
        String(32), default="COMPETITION_SANDBOX", nullable=False
    )
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_format: Mapped[str] = mapped_column(String(16), nullable=False)  # CSV, JSON
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False, index=True
    )  # PENDING, PROCESSING, VALIDATED, VALIDATED_WITH_WARNINGS, REJECTED, FAILED, PERSISTED
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quarantined_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ValidationIssue(Base):
    """Logs individual quarantined records and diagnostic constraint violations."""

    __tablename__ = "validation_issues"

    issue_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    row_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    field_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_type: Mapped[str] = mapped_column(String(64), nullable=False)  # STRUCTURAL, DOMAIN_LOGIC, etc.
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
