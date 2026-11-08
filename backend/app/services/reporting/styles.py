"""PDF styling specifications, design tokens, and ReportLab stylesheets for VYNTIQ.

Complies strictly with docs/DESIGN_SYSTEM.md and ADR-007.
"""

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

# ==============================================================================
# COLOR PALETTE (DESIGN_SYSTEM.md)
# ==============================================================================

COLOR_CHARCOAL = HexColor("#111318")  # Deep Charcoal (Primary surface / dark text)
COLOR_CARD = HexColor("#181B22")  # Surface Card
COLOR_ELEVATED = HexColor("#222630")  # Surface Elevated
COLOR_BORDER = HexColor("#2D323E")  # Hairline dividing border (dark)
COLOR_BORDER_LIGHT = HexColor("#E2DFD8")  # Hairline dividing border (light / print)
COLOR_HAIRLINE = HexColor("#D8D4CC")  # Hairline dividing border (canvas)
COLOR_WARM_IVORY = HexColor("#F1EFEA")  # Warm Ivory text / light surface
COLOR_LIGHT_BG = HexColor("#F8F7F4")  # Very light warm ivory for print cards
COLOR_WHITE = HexColor("#FFFFFF")  # Crisp White

# Editorial Accent Tokens
COLOR_MAGENTA = HexColor("#D62978")  # Royal Magenta (Primary brand accent / VOR highlight)
COLOR_MAGENTA_TINT = HexColor("#FDF0F6")  # 10% Magenta tint for badge background
COLOR_LIME = HexColor("#B9D66C")  # Sage Lime (Positive delta / C(N) Adequate)
COLOR_LIME_TINT = HexColor("#F4F8EB")  # 10% Lime tint for badge background
COLOR_LIME_DARK = HexColor("#2E6930")  # High-contrast lime for text readability
COLOR_WARNING = HexColor("#E5A83B")  # Status Warning (Amber)
COLOR_WARNING_TINT = HexColor("#FEF8EE")  # 10% Warning tint
COLOR_WARNING_DARK = HexColor("#8F5A00")  # High-contrast amber for text
COLOR_NEGATIVE = HexColor("#E05D52")  # Status Negative (Red)
COLOR_NEGATIVE_TINT = HexColor("#FCF0EF")  # 10% Negative tint
COLOR_NEGATIVE_DARK = HexColor("#992318")  # High-contrast red for text
COLOR_MUTED = HexColor("#636B7E")  # Subtle Slate Gray
COLOR_SECONDARY = HexColor("#9DA3B4")  # Metadata labels


def get_vyntiq_stylesheet() -> dict[str, ParagraphStyle]:
    """Build and return unified typography styles adhering to VYNTIQ design rules."""
    base_sheet = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}

    # Document Title (20pt Bold)
    styles["DocTitle"] = ParagraphStyle(
        "DocTitle",
        parent=base_sheet["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=COLOR_CHARCOAL,
        spaceAfter=4,
    )

    # Document Subtitle (10pt Regular)
    styles["DocSubtitle"] = ParagraphStyle(
        "DocSubtitle",
        parent=base_sheet["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=COLOR_MUTED,
        spaceAfter=12,
    )

    # Section Heading 1 (14pt Bold with hairline bottom border effect)
    styles["Heading1"] = ParagraphStyle(
        "Heading1",
        parent=base_sheet["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=COLOR_CHARCOAL,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    # Sub-section Heading 2 (10pt Bold)
    styles["Heading2"] = ParagraphStyle(
        "Heading2",
        parent=base_sheet["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=COLOR_CHARCOAL,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    # Body Editorial Narrative (9pt Regular, 13pt line height)
    styles["BodyText"] = ParagraphStyle(
        "BodyText",
        parent=base_sheet["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=COLOR_CHARCOAL,
        spaceAfter=6,
    )

    # Subtle Metadata / Footnote (7.5pt Regular)
    styles["Caption"] = ParagraphStyle(
        "Caption",
        parent=base_sheet["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=COLOR_MUTED,
    )

    # Metric Score Hero (24pt Bold Royal Magenta)
    styles["HeroScore"] = ParagraphStyle(
        "HeroScore",
        parent=base_sheet["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=COLOR_MAGENTA,
    )

    # Hero Score Sub-label (8pt Bold)
    styles["HeroLabel"] = ParagraphStyle(
        "HeroLabel",
        parent=base_sheet["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=COLOR_MUTED,
    )

    # Table Header (8pt Bold White text on dark banner)
    styles["TableHeader"] = ParagraphStyle(
        "TableHeader",
        parent=base_sheet["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=COLOR_WHITE,
        alignment=0,  # Left
    )
    styles["TableHeaderRight"] = ParagraphStyle(
        "TableHeaderRight",
        parent=styles["TableHeader"],
        alignment=2,  # Right
    )

    # Table Cell (8pt Regular)
    styles["TableCell"] = ParagraphStyle(
        "TableCell",
        parent=base_sheet["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=COLOR_CHARCOAL,
    )
    styles["TableCellBold"] = ParagraphStyle(
        "TableCellBold",
        parent=styles["TableCell"],
        fontName="Helvetica-Bold",
    )
    styles["TableCellNumber"] = ParagraphStyle(
        "TableCellNumber",
        parent=styles["TableCell"],
        alignment=2,  # Right
    )
    styles["TableCellNumberBold"] = ParagraphStyle(
        "TableCellNumberBold",
        parent=styles["TableCellBold"],
        alignment=2,  # Right
    )

    # Warning Advisory Box Paragraph
    styles["WarningBox"] = ParagraphStyle(
        "WarningBox",
        parent=base_sheet["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=COLOR_WARNING_DARK,
    )

    # Strength Bullet / Pill text
    styles["StrengthText"] = ParagraphStyle(
        "StrengthText",
        parent=base_sheet["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10.5,
        textColor=COLOR_LIME_DARK,
    )

    # Drag Factor Bullet / Pill text
    styles["DragFactorText"] = ParagraphStyle(
        "DragFactorText",
        parent=base_sheet["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10.5,
        textColor=COLOR_WARNING_DARK,
    )

    return styles
