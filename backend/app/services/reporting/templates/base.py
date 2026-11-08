"""Common ReportLab flowable builders, badges, and layout components for VYNTIQ reports."""

from typing import Any
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from backend.app.services.reporting.styles import (
    COLOR_BORDER_LIGHT,
    COLOR_CARD,
    COLOR_CHARCOAL,
    COLOR_HAIRLINE,
    COLOR_LIGHT_BG,
    COLOR_LIME_DARK,
    COLOR_LIME_TINT,
    COLOR_MAGENTA,
    COLOR_MAGENTA_TINT,
    COLOR_MUTED,
    COLOR_WARNING,
    COLOR_WARNING_DARK,
    COLOR_WARNING_TINT,
    COLOR_WHITE,
    get_vyntiq_stylesheet,
)

styles = get_vyntiq_stylesheet()


def create_header_banner(
    title: str,
    subtitle: str,
    badge_label: str | None = None,
    badge_color: str = "MAGENTA",
    usable_width: float = 540.0,
) -> Table:
    """Build an executive top banner with title, metadata subtitle, and badge."""
    title_p = Paragraph(f"<b>{title}</b>", styles["DocTitle"])
    sub_p = Paragraph(subtitle, styles["DocSubtitle"])

    left_cell = [title_p, sub_p]

    if badge_label:
        # Select badge color
        if badge_color == "LIME":
            bg = COLOR_LIME_TINT
            fg = COLOR_LIME_DARK
            border_c = COLOR_LIME_DARK
        elif badge_color == "WARNING":
            bg = COLOR_WARNING_TINT
            fg = COLOR_WARNING_DARK
            border_c = COLOR_WARNING
        else:
            bg = COLOR_MAGENTA_TINT
            fg = COLOR_MAGENTA
            border_c = COLOR_MAGENTA

        badge_p = Paragraph(
            f"<font color='{fg.hexval()}'><b>{badge_label.upper()}</b></font>",
            styles["TableCellBold"],
        )
        badge_table = Table([[badge_p]], colWidths=[90])
        badge_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), bg),
                    ("BOX", (0, 0), (-1, -1), 0.8, border_c),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        data = [[left_cell, badge_table]]
        col_widths = [usable_width - 100, 100]
    else:
        data = [[left_cell]]
        col_widths = [usable_width]

    t = Table(data, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return t


def create_section_header(title: str, usable_width: float = 540.0) -> list[Any]:
    """Generate a clean section heading with an underlying hairline separator."""
    p = Paragraph(f"<b>{title.upper()}</b>", styles["Heading1"])
    divider = Table([[""]], colWidths=[usable_width], rowHeights=[1])
    divider.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, -1), 0.8, COLOR_MAGENTA),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return [p, divider, Spacer(1, 4)]


def create_advisory_box(
    message: str,
    title: str = "Cross-Role Statistical Advisory",
    usable_width: float = 540.0,
) -> Table:
    """Generate a prominent warning box for cross-role statistical limitations."""
    content = [
        Paragraph(f"<b>{title}</b>", styles["Heading2"]),
        Spacer(1, 2),
        Paragraph(message, styles["WarningBox"]),
    ]
    t = Table([[content]], colWidths=[usable_width])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_WARNING_TINT),
                ("BOX", (0, 0), (-1, -1), 1.0, COLOR_WARNING),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return t


def create_key_value_grid(
    items: list[tuple[str, str]],
    usable_width: float = 540.0,
    col_count: int = 4,
) -> Table:
    """Format key-value pairs into a clean grid."""
    row_data = []
    current_row = []
    for label, val in items:
        cell_content = [
            Paragraph(label.upper(), styles["Caption"]),
            Paragraph(f"<b>{val}</b>", styles["TableCellBold"]),
        ]
        current_row.append(cell_content)
        if len(current_row) == col_count:
            row_data.append(current_row)
            current_row = []
    if current_row:
        # Pad with empty cells
        while len(current_row) < col_count:
            current_row.append([""])
        row_data.append(current_row)

    col_w = usable_width / col_count
    t = Table(row_data, colWidths=[col_w] * col_count)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.6, COLOR_BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER_LIGHT),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t

