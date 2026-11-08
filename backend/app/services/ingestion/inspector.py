"""Dataset file inspection and structural schema inference engine."""

import json
from pathlib import Path
from typing import Any
import pandas as pd
from backend.app.core.exceptions import ValidationException
from backend.app.core.logging import get_logger
from backend.app.models.dataset import Dataset
from backend.app.schemas.dataset import ColumnInspectionInfo, InspectionReport
from backend.app.services.ingestion.mapper import SchemaMapper

logger = get_logger("vyntiq.ingestion.inspector")


def infer_column_type(series: pd.Series) -> str:
    """Infer high-level data type from a pandas series."""
    dropped = series.dropna()
    if dropped.empty:
        return "UNKNOWN"

    dtype_str = str(dropped.dtype).lower()
    if "int" in dtype_str:
        return "INTEGER"
    if "float" in dtype_str:
        # Check if all floats are actually whole numbers
        if (dropped % 1 == 0).all():
            return "INTEGER"
        return "FLOAT"
    if "bool" in dtype_str:
        return "BOOLEAN"
    if "datetime" in dtype_str:
        return "DATETIME"

    # Sample string values to test for date or boolean strings
    first_vals = [str(v).strip() for v in dropped.head(20)]
    if all(v.lower() in {"true", "false", "0", "1", "yes", "no"} for v in first_vals):
        return "BOOLEAN"

    return "STRING"


class DatasetInspector:
    """Reads raw uploaded datasets and profiles their structural schema."""

    def __init__(self, mapper: SchemaMapper | None = None) -> None:
        self.mapper = mapper or SchemaMapper()

    def load_dataframe_sample(self, file_path: str, format_type: str, nrows: int | None = None) -> pd.DataFrame:
        """Load tabular data from CSV or JSON file into a Pandas DataFrame."""
        path = Path(file_path)
        if not path.exists():
            raise ValidationException(
                message=f"Raw dataset file not found at path '{file_path}'.",
                code="FILE_NOT_FOUND",
            )

        try:
            if format_type.upper() == "CSV":
                # Read CSV with flexible delimiter detection
                df = pd.read_csv(path, nrows=nrows, low_memory=False)
            elif format_type.upper() == "JSON":
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Case 1: Standard tabular list of delivery records [{...}, {...}]
                if isinstance(data, list):
                    df = pd.DataFrame(data[:nrows] if nrows else data)
                # Case 2: Dict with 'deliveries' or 'data' key
                elif isinstance(data, dict) and "deliveries" in data and isinstance(data["deliveries"], list):
                    df = pd.DataFrame(data["deliveries"][:nrows] if nrows else data["deliveries"])
                elif isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                    df = pd.DataFrame(data["data"][:nrows] if nrows else data["data"])
                # Case 3: Cricsheet structured format {"info": ..., "innings": [...]}
                elif isinstance(data, dict) and "innings" in data:
                    flat_rows = []
                    match_id = data.get("info", {}).get("match_type_number", "match_01")
                    season = str(data.get("info", {}).get("season", ""))
                    venue = data.get("info", {}).get("venue", "")
                    teams = data.get("info", {}).get("teams", ["Team1", "Team2"])

                    for inn_idx, inn in enumerate(data.get("innings", []), start=1):
                        team_name = inn.get("team", teams[0] if inn_idx == 1 else teams[1])
                        bowling_team = teams[1] if team_name == teams[0] else teams[0]

                        for over_obj in inn.get("overs", []):
                            over_num = over_obj.get("over", 0)
                            for d_idx, delivery in enumerate(over_obj.get("deliveries", []), start=1):
                                flat_rows.append({
                                    "match_id": match_id,
                                    "season": season,
                                    "venue": venue,
                                    "batting_team": team_name,
                                    "bowling_team": bowling_team,
                                    "innings": inn_idx,
                                    "over": over_num,
                                    "ball": d_idx,
                                    "batter": delivery.get("batter", ""),
                                    "bowler": delivery.get("bowler", ""),
                                    "non_striker": delivery.get("non_striker", ""),
                                    "runs_off_bat": delivery.get("runs", {}).get("batter", 0),
                                    "extras": delivery.get("runs", {}).get("extras", 0),
                                    "total_runs": delivery.get("runs", {}).get("total", 0),
                                    "wicket": 1 if "wickets" in delivery else 0,
                                    "player_dismissed": delivery.get("wickets", [{}])[0].get("player_out") if "wickets" in delivery else None,
                                    "dismissal_kind": delivery.get("wickets", [{}])[0].get("kind") if "wickets" in delivery else None,
                                })
                    df = pd.DataFrame(flat_rows[:nrows] if nrows else flat_rows)
                else:
                    raise ValidationException(
                        message="Unsupported JSON dataset structure. Expected a list of records or cricket innings format.",
                        code="INVALID_JSON_STRUCTURE",
                    )
            else:
                raise ValidationException(
                    message=f"Unsupported format '{format_type}'.",
                    code="UNSUPPORTED_FORMAT",
                )
        except json.JSONDecodeError as exc:
            raise ValidationException(
                message=f"Malformed JSON content: {str(exc)}",
                code="MALFORMED_JSON",
            )
        except Exception as exc:
            if isinstance(exc, ValidationException):
                raise
            raise ValidationException(
                message=f"Failed to parse dataset file: {str(exc)}",
                code="FILE_PARSE_ERROR",
            )

        if df.empty or len(df.columns) == 0:
            raise ValidationException(
                message="Dataset file contains no tabular columns or records.",
                code="EMPTY_DATASET",
            )

        return df

    def inspect_dataset(self, dataset: Dataset) -> InspectionReport:
        """Analyze headers, sample values, and infer schema mapping."""
        # Read sample of 1000 rows for rapid inspection
        df_sample = self.load_dataframe_sample(
            file_path=dataset.storage_path,
            format_type=dataset.file_format,
            nrows=1000,
        )

        source_columns = [str(c) for c in df_sample.columns]
        detected_mapping = self.mapper.detect_mapping(source_columns)
        missing_required = self.mapper.check_missing_required(detected_mapping)
        unmapped_columns = self.mapper.identify_unmapped(source_columns, detected_mapping)

        # Profile each column
        columns_info: list[ColumnInspectionInfo] = []
        for col in source_columns:
            series = df_sample[col]
            inferred_type = infer_column_type(series)
            null_count = int(series.isna().sum())
            non_null_count = int(len(series) - null_count)

            # Extract up to 3 non-null distinct sample values
            samples = list(series.dropna().astype(str).unique()[:3])

            columns_info.append(
                ColumnInspectionInfo(
                    column_name=col,
                    inferred_type=inferred_type,
                    non_null_count=non_null_count,
                    null_count=null_count,
                    sample_values=samples,
                    suggested_canonical_field=detected_mapping.get(col),
                )
            )

        file_size = Path(dataset.storage_path).stat().st_size

        return InspectionReport(
            dataset_id=dataset.dataset_id,
            filename=dataset.source_filename,
            file_format=dataset.file_format,
            file_size_bytes=file_size,
            total_columns=len(source_columns),
            total_rows_estimated=len(df_sample),
            columns=columns_info,
            unmapped_columns=unmapped_columns,
            missing_required_fields=missing_required,
        )
