"""Base definitions, constants, and calculation helpers for the cricket analytics engine."""

from typing import Any
from backend.app.schemas.metrics import (
    MetricCategory,
    MetricDirection,
    MetricProvenance,
    MetricStatus,
    MetricValue,
    SampleSizeInfo,
)

# Canonical dismissal rules in accordance with MCC Laws of Cricket and T20 scoring conventions
BOWLER_CREDITED_DISMISSALS: set[str] = {
    "bowled",
    "caught",
    "lbw",
    "stumped",
    "caught and bowled",
    "caught & bowled",
    "hit wicket",
}

NON_BOWLER_DISMISSALS: set[str] = {
    "run out",
    "retired hurt",
    "retired out",
    "obstructing the field",
    "timed out",
    "hit the ball twice",
}

# Standard T20 match phase classifications
STANDARD_PHASES: list[str] = ["POWERPLAY", "MIDDLE", "DEATH"]

CALCULATION_VERSION: str = "1.0.0"


def safe_divide(
    numerator: float | int,
    denominator: float | int,
    multiplier: float = 1.0,
    round_digits: int = 2,
    default_on_zero: float | None = None,
) -> tuple[float | None, MetricStatus]:
    """Safely divide two numbers, returning a tuple of (result, status).

    Prevents silent zeroing and returns DIVIDE_BY_ZERO_SAFEGUARD when the denominator is 0.
    """
    if denominator == 0:
        return (default_on_zero, MetricStatus.DIVIDE_BY_ZERO_SAFEGUARD)
    val = round(float(numerator) / float(denominator) * multiplier, round_digits)
    return (val, MetricStatus.CALCULATED)


def create_metric_value(
    metric_id: str,
    display_name: str,
    value: float | int | None,
    status: MetricStatus,
    sample_size: int,
    sample_units: str = "balls",
    directionality: MetricDirection = MetricDirection.HIGHER_IS_BETTER,
    context: dict[str, Any] | None = None,
) -> MetricValue:
    """Factory helper to construct a standardized MetricValue."""
    return MetricValue(
        metric_id=metric_id,
        display_name=display_name,
        value=value,
        status=status,
        sample_size=sample_size,
        sample_units=sample_units,
        directionality=directionality,
        context=context or {},
    )
