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
from backend.app.schemas.comparison import (
    ComparisonCompatibilityStatus,
    ComparisonMetadataResponse,
    DimensionComparisonItem,
    MetricComparisonItem,
    PlayerComparisonHeader,
    PlayerComparisonRequest,
    PlayerComparisonResponse,
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
from backend.app.schemas.evaluation import (
    DatasetEvaluationResponse,
    DimensionAvailabilityStatus,
    DimensionEvaluationProfile,
    DimensionRegistryEntry,
    DisciplineSampleAdequacy,
    PlayerEvaluationResponse,
    PlayerRole,
    RoleClassificationResult,
    RoleClassificationStatus,
    SampleAdequacyStatus,
)
from backend.app.schemas.explainability import (
    DimensionContributionDetail,
    ExplanationStatus,
    MetricContributionDetail,
    PlayerDetailedExplanationResponse,
    PlayerScoreBreakdownResponse,
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
from backend.app.schemas.scoring import (
    DimensionScore,
    NormalizedMetric,
    PlayerScoreResult,
    RankedPlayer,
    RankingResponse,
    ReliabilityStatus,
    ScoreExplanation,
    ScoringCalculationRequest,
    ScoringMethodologyResponse,
    ScoringRunResponse,
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
    # Evaluation & Role Classification
    "PlayerRole",
    "RoleClassificationStatus",
    "SampleAdequacyStatus",
    "DimensionAvailabilityStatus",
    "RoleClassificationResult",
    "DimensionEvaluationProfile",
    "DisciplineSampleAdequacy",
    "PlayerEvaluationResponse",
    "DatasetEvaluationResponse",
    "DimensionRegistryEntry",
    # VOR Scoring & Rankings
    "ReliabilityStatus",
    "NormalizedMetric",
    "DimensionScore",
    "ScoreExplanation",
    "PlayerScoreResult",
    "RankedPlayer",
    "ScoringRunResponse",
    "RankingResponse",
    "ScoringCalculationRequest",
    "ScoringMethodologyResponse",
    # Explainability
    "ExplanationStatus",
    "MetricContributionDetail",
    "DimensionContributionDetail",
    "PlayerScoreBreakdownResponse",
    "PlayerDetailedExplanationResponse",
    # Comparison
    "ComparisonCompatibilityStatus",
    "MetricComparisonItem",
    "DimensionComparisonItem",
    "PlayerComparisonHeader",
    "PlayerComparisonRequest",
    "PlayerComparisonResponse",
    "ComparisonMetadataResponse",
]
