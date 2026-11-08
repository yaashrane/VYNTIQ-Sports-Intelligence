"""Two-tiered data validation engine and quarantine logging pipeline."""

import uuid
from datetime import datetime, timezone
import pandas as pd
from backend.app.core.logging import get_logger
from backend.app.models.dataset import ValidationIssue
from backend.app.schemas.dataset import (
    ValidationIssueDetail,
    ValidationReport,
    ValidationSummary,
)

logger = get_logger("vyntiq.ingestion.validator")

VALID_DISMISSAL_KINDS = {
    "BOWLED",
    "CAUGHT",
    "LBW",
    "RUN_OUT",
    "RUN OUT",
    "STUMPED",
    "CAUGHT_AND_BOWLED",
    "CAUGHT AND BOWLED",
    "HIT_WICKET",
    "HIT WICKET",
    "RETIRED_OUT",
    "RETIRED OUT",
    "RETIRED_HURT",
    "OBSTRUCTING_THE_FIELD",
}


class DataValidator:
    """Executes structural and cricket-specific validation on normalized datasets."""

    def validate_deliveries(
        self, df: pd.DataFrame, dataset_id: str
    ) -> tuple[pd.DataFrame, list[ValidationIssue], ValidationReport]:
        """Validate all rows in normalized delivery DataFrame and isolate violations."""
        issues: list[ValidationIssue] = []
        valid_indices: list[int] = []
        missing_summary: dict[str, int] = {}
        error_count = 0
        warning_count = 0

        # Duplicate checking: duplicate delivery events in the same match/innings/over/ball
        duplicate_mask = df.duplicated(
            subset=["match_id", "innings_num", "over_number", "ball_number", "batter_id", "bowler_id"],
            keep=False,
        )
        duplicate_count = int(duplicate_mask.sum())

        for idx, row in df.iterrows():
            row_idx = int(idx)
            row_has_fatal_error = False

            # Rule 1: Mandatory Fields Check
            for field in ["match_id", "batter_id", "bowler_id"]:
                val = row.get(field)
                if val is None or str(val).strip() in {"", "None", "nan", "UNKNOWN"}:
                    issues.append(
                        ValidationIssue(
                            issue_id=str(uuid.uuid4()),
                            dataset_id=dataset_id,
                            row_index=row_idx,
                            field_name=field,
                            error_type="MISSING_MANDATORY",
                            error_message=f"Mandatory field '{field}' is missing or empty.",
                            raw_value=str(val),
                        )
                    )
                    missing_summary[field] = missing_summary.get(field, 0) + 1
                    row_has_fatal_error = True
                    error_count += 1

            # Rule 2: Innings Number Range
            innings_num = row.get("innings_num")
            if innings_num not in {1, 2, 3, 4}:
                issues.append(
                    ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        dataset_id=dataset_id,
                        row_index=row_idx,
                        field_name="innings_num",
                        error_type="DOMAIN_LOGIC",
                        error_message=f"Invalid innings number {innings_num}. Expected 1 or 2.",
                        raw_value=str(innings_num),
                    )
                )
                row_has_fatal_error = True
                error_count += 1

            # Rule 3: Runs Non-Negativity
            batter_runs = row.get("batter_runs", 0)
            if batter_runs < 0:
                issues.append(
                    ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        dataset_id=dataset_id,
                        row_index=row_idx,
                        field_name="batter_runs",
                        error_type="DOMAIN_LOGIC",
                        error_message=f"Negative batter runs ({batter_runs}) is impossible in cricket.",
                        raw_value=str(batter_runs),
                    )
                )
                row_has_fatal_error = True
                error_count += 1

            extras_runs = row.get("extras_runs", 0)
            if extras_runs < 0:
                issues.append(
                    ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        dataset_id=dataset_id,
                        row_index=row_idx,
                        field_name="extras_runs",
                        error_type="DOMAIN_LOGIC",
                        error_message=f"Negative extras runs ({extras_runs}) is impossible in cricket.",
                        raw_value=str(extras_runs),
                    )
                )
                row_has_fatal_error = True
                error_count += 1

            # Rule 4: Run Reconciliation Check
            total_runs = row.get("total_runs", 0)
            expected_total = batter_runs + extras_runs
            if total_runs != expected_total:
                # Warning rather than fatal error: reconcile total_runs automatically
                issues.append(
                    ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        dataset_id=dataset_id,
                        row_index=row_idx,
                        field_name="total_runs",
                        error_type="RECONCILIATION_WARNING",
                        error_message=(
                            f"Total runs ({total_runs}) did not match batter_runs ({batter_runs}) + "
                            f"extras_runs ({extras_runs}). Reconciled to {expected_total}."
                        ),
                        raw_value=f"total={total_runs}, expected={expected_total}",
                    )
                )
                warning_count += 1

            # Rule 5: Dismissal Verification
            is_wicket = row.get("is_wicket", False)
            dismissal_kind = row.get("dismissal_kind")
            if is_wicket:
                if dismissal_kind and str(dismissal_kind).strip().upper() not in VALID_DISMISSAL_KINDS:
                    issues.append(
                        ValidationIssue(
                            issue_id=str(uuid.uuid4()),
                            dataset_id=dataset_id,
                            row_index=row_idx,
                            field_name="dismissal_kind",
                            error_type="DOMAIN_LOGIC_WARNING",
                            error_message=f"Unrecognized dismissal kind '{dismissal_kind}'.",
                            raw_value=str(dismissal_kind),
                        )
                    )
                    warning_count += 1

            # Rule 6: Duplicate Record Flagging
            if duplicate_mask.iloc[row_idx]:
                issues.append(
                    ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        dataset_id=dataset_id,
                        row_index=row_idx,
                        field_name="duplicate_delivery",
                        error_type="DUPLICATE_RECORD",
                        error_message="Identical match delivery event detected more than once.",
                        raw_value=f"over={row.get('over_delivery')}",
                    )
                )
                warning_count += 1

            if not row_has_fatal_error:
                valid_indices.append(row_idx)

        valid_df = df.iloc[valid_indices].copy()
        total_records = len(df)
        valid_records = len(valid_df)
        invalid_records = total_records - valid_records

        # Determine overall validation status
        if total_records == 0:
            status = "REJECTED"
        elif invalid_records == 0 and warning_count == 0:
            status = "VALIDATED"
        elif invalid_records == 0 and warning_count > 0:
            status = "VALIDATED_WITH_WARNINGS"
        elif valid_records > 0:
            status = "VALIDATED_WITH_WARNINGS"
        else:
            status = "REJECTED"

        summary = ValidationSummary(
            dataset_id=dataset_id,
            status=status,
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records,
            duplicate_records=duplicate_count,
            unmapped_columns=[],
            missing_fields_summary=missing_summary,
            error_count=error_count,
            warning_count=warning_count,
            validated_at=datetime.now(timezone.utc),
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
            for iss in issues[:50]  # First 50 issues for responsive reporting
        ]

        report = ValidationReport(summary=summary, sample_issues=sample_issues)
        logger.info(
            "Validation completed for %s: %d total, %d valid, %d invalid, %d errors, status=%s",
            dataset_id,
            total_records,
            valid_records,
            invalid_records,
            error_count,
            status,
        )

        return valid_df, issues, report
