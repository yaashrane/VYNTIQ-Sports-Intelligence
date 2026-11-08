"""Source-to-canonical schema mapping engine for arbitrary cricket datasets.

Complies with docs/DATA_DICTIONARY.md and ADR-004.
"""

from typing import Any
from backend.app.core.logging import get_logger

logger = get_logger("vyntiq.ingestion.mapper")

# Standard canonical fields and their recognized source aliases (case-insensitive)
CANONICAL_FIELD_ALIASES: dict[str, list[str]] = {
    "match_id": ["match_id", "match_no", "id", "match_number", "game_id", "match"],
    "season": ["season", "year", "tournament_year", "edition"],
    "match_date": ["date", "match_date", "start_date", "fixture_date"],
    "venue_name": ["venue", "venue_name", "ground", "stadium", "location"],
    "batting_team": ["batting_team", "team1", "bat_team", "batting_side"],
    "bowling_team": ["bowling_team", "team2", "bowl_team", "bowling_side"],
    "innings_num": ["innings", "innings_num", "inning", "innings_no", "inn"],
    "over_delivery": ["ball", "delivery", "over_ball", "over_delivery"],
    "over_number": ["over", "over_num", "overs"],
    "ball_number": ["ball_num", "ball_number", "delivery_num"],
    "batter_id": ["batter", "batsman", "striker", "batter_name", "batsman_name", "player_out_striker"],
    "bowler_id": ["bowler", "bowler_name", "delivery_bowler"],
    "non_striker_id": ["non_striker", "nonstriker", "other_batter"],
    "batter_runs": ["runs_off_bat", "batter_runs", "batsman_runs", "runs_batter", "batsman_run", "bat_runs"],
    "extras_runs": ["extras", "extra_runs", "extras_runs", "extra", "extras_conceded"],
    "total_runs": ["total_runs", "runs_total", "total", "runs"],
    "is_wicket": ["is_wicket", "wicket", "wicket_flag", "is_dismissal"],
    "dismissed_player_id": ["player_dismissed", "dismissed_player", "dismissed_player_id", "wicket_player", "dismissal_player"],
    "dismissal_kind": ["dismissal_kind", "wicket_type", "kind", "method", "wicket_kind", "dismissal_type"],
    "extras_type": ["extras_type", "extra_type", "penalty_type"],
}

# Strict minimum canonical fields required to evaluate ball-by-ball events
MANDATORY_CANONICAL_FIELDS: set[str] = {
    "match_id",
    "innings_num",
    "batter_id",
    "bowler_id",
    "batter_runs",
}


class SchemaMapper:
    """Discovers, validates, and applies source-to-canonical column mappings."""

    def __init__(self, custom_mapping: dict[str, str] | None = None) -> None:
        self.custom_mapping = custom_mapping or {}

    def detect_mapping(self, source_columns: list[str]) -> dict[str, str]:
        """Infer canonical mapping from source column names using alias dictionary."""
        mapping: dict[str, str] = {}
        assigned_canonical: set[str] = set()

        # 1. Apply explicit custom overrides first
        for src_col, canon_col in self.custom_mapping.items():
            if src_col in source_columns:
                mapping[src_col] = canon_col
                assigned_canonical.add(canon_col)

        # 2. Automated fuzzy / alias matching for remaining columns
        for col in source_columns:
            if col in mapping:
                continue

            clean_col = col.strip().lower().replace(" ", "_").replace("-", "_")

            matched_canonical: str | None = None
            for canon_field, aliases in CANONICAL_FIELD_ALIASES.items():
                if canon_field in assigned_canonical:
                    continue

                if clean_col == canon_field or clean_col in aliases:
                    matched_canonical = canon_field
                    break

            if matched_canonical:
                mapping[col] = matched_canonical
                assigned_canonical.add(matched_canonical)

        return mapping

    def check_missing_required(self, mapped_fields: dict[str, str]) -> list[str]:
        """Identify if any mandatory analytical fields are missing from mapping."""
        mapped_canonical = set(mapped_fields.values())
        missing = []

        # Check over/ball progression representation:
        # Either 'over_delivery' or ('over_number' and 'ball_number') must be present
        has_delivery = "over_delivery" in mapped_canonical or (
            "over_number" in mapped_canonical and "ball_number" in mapped_canonical
        )
        if not has_delivery:
            missing.append("over_delivery (or separate over and ball columns)")

        for mandatory in MANDATORY_CANONICAL_FIELDS:
            if mandatory not in mapped_canonical:
                missing.append(mandatory)

        return sorted(missing)

    def identify_unmapped(
        self, source_columns: list[str], mapping: dict[str, str]
    ) -> list[str]:
        """Return list of source columns that could not be mapped to canonical fields."""
        return [col for col in source_columns if col not in mapping]
