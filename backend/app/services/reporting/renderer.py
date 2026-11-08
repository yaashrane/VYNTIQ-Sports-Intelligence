"""PDF document compiler transforming domain flowables into vector PDF files."""

import reportlab.rl_config
from pathlib import Path
from typing import Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate

# Enable uncompressed text stream rendering for fast vector compilation and inspection
reportlab.rl_config.pageCompression = 0
from backend.app.core.exceptions import AppException
from backend.app.schemas.report import ReportType
from backend.app.services.reporting.canvas import VyntiqNumberedCanvas
from backend.app.services.reporting.templates import (
    build_competition_overview_flowables,
    build_individual_player_flowables,
    build_player_comparison_flowables,
    build_shortlist_flowables,
)


class ReportRenderer:
    """Renders structured domain data into print-ready, multi-page vector PDF documents."""

    def render_pdf(self, data: dict[str, Any], output_path: Path) -> Path:
        """Compile prepared report data into a PDF document at output_path."""
        report_type = data.get("report_type")

        # Select page geometry: Letter standard, 0.5in (36pt) margins
        usable_width = letter[0] - 72.0  # 612 - 72 = 540 pt

        # Dispatch to template flowable builder
        if report_type == ReportType.COMPETITION_OVERVIEW.value:
            flowables = build_competition_overview_flowables(data, usable_width=usable_width)
        elif report_type == ReportType.INDIVIDUAL_PLAYER.value:
            flowables = build_individual_player_flowables(data, usable_width=usable_width)
        elif report_type == ReportType.PLAYER_COMPARISON.value:
            flowables = build_player_comparison_flowables(data, usable_width=usable_width)
        elif report_type == ReportType.SHORTLIST.value:
            flowables = build_shortlist_flowables(data, usable_width=usable_width)
        else:
            raise AppException(f"Unsupported report type for PDF compilation: '{report_type}'.")

        try:
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                leftMargin=36.0,
                rightMargin=36.0,
                topMargin=36.0,
                bottomMargin=36.0,
            )
            doc.build(flowables, canvasmaker=VyntiqNumberedCanvas)
            return output_path
        except Exception as exc:
            raise AppException(f"PDF compilation failed for report '{report_type}': {str(exc)}") from exc
