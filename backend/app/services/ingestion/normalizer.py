"""Data normalization and canonical field standardization engine."""

from typing import Any
import numpy as np
import pandas as pd
from backend.app.core.logging import get_logger

logger = get_logger("vyntiq.ingestion.normalizer")


def determine_phase(over_num: int) -> str:
    """Classify T20 delivery into match phase based on over index (0-indexed)."""
    if over_num <= 5:
        return "POWERPLAY"
    if over_num <= 14:
        return "MIDDLE"
    return "DEATH"


class DataNormalizer:
    """Normalizes arbitrary tabular cricket data into canonical internal types."""

    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        column_mapping: dict[str, str],
        dataset_id: str,
        workspace_id: str | None = None,
        origin_type: str = "COMPETITION_SANDBOX",
    ) -> pd.DataFrame:
        """Apply column mappings, type conversions, and derive required cricket fields."""
        norm_df = df.copy()

        # 1. Rename columns according to mapping
        norm_df = norm_df.rename(columns=column_mapping)

        # 2. Derive over and ball progression
        if "over_delivery" in norm_df.columns:
            # Coerce over_delivery to numeric float
            norm_df["over_delivery"] = pd.to_numeric(norm_df["over_delivery"], errors="coerce")
            if "over_number" not in norm_df.columns:
                norm_df["over_number"] = norm_df["over_delivery"].apply(
                    lambda x: int(x) if pd.notna(x) else 0
                )
            if "ball_number" not in norm_df.columns:
                norm_df["ball_number"] = norm_df["over_delivery"].apply(
                    lambda x: int(round((x - int(x)) * 10)) if pd.notna(x) else 1
                )
        elif "over_number" in norm_df.columns and "ball_number" in norm_df.columns:
            norm_df["over_number"] = pd.to_numeric(norm_df["over_number"], errors="coerce").fillna(0).astype(int)
            norm_df["ball_number"] = pd.to_numeric(norm_df["ball_number"], errors="coerce").fillna(1).astype(int)
            norm_df["over_delivery"] = norm_df["over_number"] + (norm_df["ball_number"] / 10.0)
        else:
            norm_df["over_number"] = 0
            norm_df["ball_number"] = 1
            norm_df["over_delivery"] = 0.1

        # 3. Assign match phase
        norm_df["phase"] = norm_df["over_number"].apply(determine_phase)

        # 4. Standardize runs and extras
        if "batter_runs" in norm_df.columns:
            norm_df["batter_runs"] = pd.to_numeric(norm_df["batter_runs"], errors="coerce").fillna(0).astype(int)
        else:
            norm_df["batter_runs"] = 0

        if "extras_runs" in norm_df.columns:
            norm_df["extras_runs"] = pd.to_numeric(norm_df["extras_runs"], errors="coerce").fillna(0).astype(int)
        else:
            norm_df["extras_runs"] = 0

        if "total_runs" in norm_df.columns:
            norm_df["total_runs"] = pd.to_numeric(norm_df["total_runs"], errors="coerce").fillna(
                norm_df["batter_runs"] + norm_df["extras_runs"]
            ).astype(int)
        else:
            norm_df["total_runs"] = norm_df["batter_runs"] + norm_df["extras_runs"]

        # 5. Extras type and legality
        if "extras_type" in norm_df.columns:
            norm_df["extras_type"] = norm_df["extras_type"].astype(str).str.upper().replace({"NAN": None, "NONE": None, "": None})
        else:
            norm_df["extras_type"] = None

        # Determine legal delivery (Wides and No-balls do not count as legal deliveries in cricket)
        norm_df["is_legal"] = ~norm_df["extras_type"].isin(["WIDE", "NO_BALL", "NO BALL", "WIDES", "NOBALLS"])

        # 6. Standardize Wicket flag and dismissal
        if "is_wicket" in norm_df.columns:
            norm_df["is_wicket"] = norm_df["is_wicket"].apply(
                lambda val: True if str(val).strip().lower() in {"1", "true", "yes", "y"} else False
            )
        elif "dismissed_player_id" in norm_df.columns:
            norm_df["is_wicket"] = norm_df["dismissed_player_id"].notna() & (
                norm_df["dismissed_player_id"].astype(str).str.strip().str.upper() != "NAN"
            ) & (norm_df["dismissed_player_id"].astype(str).str.strip() != "")
        else:
            norm_df["is_wicket"] = False

        if "dismissal_kind" not in norm_df.columns:
            norm_df["dismissal_kind"] = None
        else:
            norm_df["dismissal_kind"] = norm_df["dismissal_kind"].astype(str).str.upper().replace({"NAN": None, "": None})

        if "dismissed_player_id" not in norm_df.columns:
            norm_df["dismissed_player_id"] = None
        else:
            norm_df["dismissed_player_id"] = norm_df["dismissed_player_id"].astype(str).replace({"nan": None, "": None})

        # 7. Player IDs / Names
        for field in ["batter_id", "bowler_id", "non_striker_id"]:
            if field in norm_df.columns:
                norm_df[field] = norm_df[field].astype(str).str.strip().replace({"nan": None, "": None})
            else:
                norm_df[field] = "UNKNOWN"

        # 8. Match context metadata
        if "match_id" in norm_df.columns:
            norm_df["match_id"] = norm_df["match_id"].astype(str).str.strip()
        else:
            norm_df["match_id"] = f"match_{dataset_id[:8]}"

        if "innings_num" in norm_df.columns:
            norm_df["innings_num"] = pd.to_numeric(norm_df["innings_num"], errors="coerce").fillna(1).astype(int)
        else:
            norm_df["innings_num"] = 1

        if "season" in norm_df.columns:
            norm_df["season"] = norm_df["season"].astype(str).str.strip()
        else:
            norm_df["season"] = "UNKNOWN"

        # 9. Lineage and provenance stamps
        norm_df["dataset_id"] = dataset_id
        norm_df["workspace_id"] = workspace_id
        norm_df["origin_type"] = origin_type

        return norm_df
