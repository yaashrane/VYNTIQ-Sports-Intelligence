"""Pydantic request and response schemas."""

from backend.app.schemas.analytics import (
    CalculationResponse,
    DatasetMetricsSummaryResponse,
    DimensionGroup,
    MetricCalculationFilter,
    MetricCalculationRequest,
    MetricRegistryResponse,
    PlayerMetricsSummary,
)
from backend.app.schemas.common import (
    ErrorDetail,
    ErrorEnvelope,
    ErrorResponse,
    MessageResponse,
)
from backend.app.schemas.dataset import (
    ColumnInspectionInfo,
    DatasetUploadResponse,
    InspectionReport,
    PersistenceResponse,
    ValidationIssueDetail,
    ValidationReport,
    ValidationRequest,
    ValidationSummary,
)
from backend.app.schemas.health import HealthResponse
from backend.app.schemas.metrics import (
    MetricCategory,
    MetricDirection,
    MetricProvenance,
    MetricRegistryEntry,
    MetricStatus,
    MetricValue,
    SampleSizeInfo,
)

__all__ = [
    # Common
    "ErrorDetail",
    "ErrorEnvelope",
    "ErrorResponse",
    "HealthResponse",
    "MessageResponse",
    # Dataset Ingestion
    "DatasetUploadResponse",
    "ColumnInspectionInfo",
    "InspectionReport",
    "ValidationIssueDetail",
    "ValidationSummary",
    "ValidationReport",
    "ValidationRequest",
    "PersistenceResponse",
    # Metrics
    "MetricStatus",
    "MetricDirection",
    "MetricCategory",
    "SampleSizeInfo",
    "MetricProvenance",
    "MetricValue",
    "MetricRegistryEntry",
    # Analytics
    "MetricCalculationFilter",
    "MetricCalculationRequest",
    "DimensionGroup",
    "PlayerMetricsSummary",
    "CalculationResponse",
    "DatasetMetricsSummaryResponse",
    "MetricRegistryResponse",
]
