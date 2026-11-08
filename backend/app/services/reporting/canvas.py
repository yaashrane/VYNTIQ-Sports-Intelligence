"""Two-pass NumberedCanvas for dynamic total page count, running headers, and footers."""

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# Exact brand tokens
COLOR_CHARCOAL = HexColor("#111318")
COLOR_MAGENTA = HexColor("#D62978")
COLOR_LIME_DARK = HexColor("#4E7019")
COLOR_MUTED = HexColor("#636B7E")
COLOR_HAIRLINE = HexColor("#D8D4CC")


class VyntiqNumberedCanvas(canvas.Canvas):
    """Two-pass canvas that computes total page counts and draws running headers/footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict] = []

    def showPage(self) -> None:
        """Capture page state dictionary and defer rendering until total page count is known."""
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        """Two-pass save: iterate across saved page states, draw headers and footers, and commit."""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_header_and_footer(num_pages)
            super().showPage()
        super().save()

    def _draw_header_and_footer(self, total_pages: int) -> None:
        """Render running header, hairline dividers, and page number footer on each page."""
        width = self._pagesize[0]
        height = self._pagesize[1]
        margin_x = 36.0

        self.saveState()

        # ======================================================================
        # RUNNING HEADER
        # ======================================================================
        header_y = height - 28.0

        # Brand Wordmark: "VYNTIQ" in Royal Magenta, "— SPORTS INTELLIGENCE" in Deep Charcoal
        self.setFont("Helvetica-Bold", 8.5)
        self.setFillColor(COLOR_MAGENTA)
        self.drawString(margin_x, header_y, "VYNTIQ")

        offset = margin_x + self.stringWidth("VYNTIQ ", "Helvetica-Bold", 8.5)
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(COLOR_CHARCOAL)
        self.drawString(offset, header_y, "— SPORTS INTELLIGENCE")

        # Brand Tagline: "Every Metric Tells a Story." (Right-aligned)
        self.setFont("Helvetica-Oblique", 7.5)
        self.setFillColor(COLOR_MUTED)
        tagline = "Every Metric Tells a Story."
        self.drawRightString(width - margin_x, header_y, tagline)

        # Hairline divider rule below header
        self.setStrokeColor(COLOR_HAIRLINE)
        self.setLineWidth(0.6)
        self.line(margin_x, header_y - 6.0, width - margin_x, header_y - 6.0)

        # ======================================================================
        # RUNNING FOOTER
        # ======================================================================
        footer_y = 26.0

        # Hairline divider rule above footer
        self.setStrokeColor(COLOR_HAIRLINE)
        self.setLineWidth(0.6)
        self.line(margin_x, footer_y + 10.0, width - margin_x, footer_y + 10.0)

        # Confidentiality Notice (Left-aligned)
        self.setFont("Helvetica", 6.8)
        self.setFillColor(COLOR_MUTED)
        self.drawString(
            margin_x,
            footer_y,
            "CONFIDENTIAL & PROPRIETARY — FOR PROFESSIONAL SCOUTING & COMPETITION AUDIT ONLY",
        )

        # Dynamic Page Number (Right-aligned: "Page X of Y")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.setFont("Helvetica-Bold", 7.0)
        self.setFillColor(COLOR_CHARCOAL)
        self.drawRightString(width - margin_x, footer_y, page_str)

        self.restoreState()
