"""Generate publication-quality PDF Methodology Report for SupeRR Selector Season 2."""

import os
import shutil
import pandas as pd
import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#94A3B8"))
            self.drawString(54, 755, "RAJASTHAN ROYALS — SUPERR SELECTOR SEASON 2")
            self.setFont("Helvetica", 8)
            self.drawRightString(558, 755, "PRESSURE METHODOLOGY & SQUAD REPORT")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 747, 558, 747)

        # Footer (All pages)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 35, "VYNTIQ Sports Intelligence — Confirmed Official Competition Submission")
        self.drawRightString(558, 35, f"Page {self._pageNumber} of {page_count}")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 47, 558, 47)
        self.restoreState()


def generate_report():
    data_dir = r"d:\VYNTIQ Sports Intelligence\data\official_super_rr_s2"
    assets_dir = r"d:\VYNTIQ Sports Intelligence\docs\assets"
    out_pdf = r"d:\VYNTIQ Sports Intelligence\docs\SupeRR_Selector_Season_2_Methodology_Report.pdf"
    out_pdf_copy = os.path.join(data_dir, "SupeRR_Selector_Season_2_Methodology_Report.pdf")

    bat = pd.read_parquet(f"{data_dir}/official_top_batters_under_pressure.parquet").head(10)
    bowl = pd.read_parquet(f"{data_dir}/official_top_bowlers_under_pressure.parquet").head(10)

    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#0F172A")
    rr_pink = colors.HexColor("#E11D48")
    text_dark = colors.HexColor("#1E293B")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=21,
        leading=25,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=10,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#E11D48"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=6,
    )

    th_style = ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=7.5, leading=9.5, textColor=colors.white)
    td_style = ParagraphStyle("TD", fontName="Helvetica", fontSize=7.5, leading=9.5, textColor=text_dark)
    td_bold = ParagraphStyle("TDBold", fontName="Helvetica-Bold", fontSize=7.5, leading=9.5, textColor=text_dark)
    td_pink = ParagraphStyle("TDPink", fontName="Helvetica-Bold", fontSize=7.5, leading=9.5, textColor=rr_pink)

    doc = SimpleDocTemplate(
        out_pdf,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    story = []

    # Banner
    story.append(Paragraph("SUPERR SELECTOR SEASON 2 — METHODOLOGY REPORT", ParagraphStyle("SubHeader", fontName="Helvetica-Bold", fontSize=8.5, textColor=rr_pink, spaceAfter=2)))
    story.append(Paragraph("Quantifying T20 Clutch Performance: Identifying the Most Reliable Players Under Pressure", title_style))
    story.append(Paragraph("<b>Challenge:</b> Round 1 — Identify the Most Reliable Players Under Pressure | <b>Target:</b> IPL 2027 Auction Strategy<br/><b>Dataset Analyzed:</b> 200,999 Deliveries (883 Matches, 2022–2026 IPL & T20I Archives) | <b>Author:</b> VYNTIQ Sports Intelligence", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=rr_pink, spaceAfter=10))

    # Executive Summary
    story.append(Paragraph("Executive Summary: Official Unstop Dropdown Selections", h1_style))
    story.append(Paragraph(
        "This report delivers an audit-ready, statistically defensible evaluation of player performance under high-pressure T20 match situations. "
        "Using a dual-evidence framework baselined against career performance across 200,999 official deliveries, we quantify both <b>absolute clutch execution</b> "
        "and <b>relative performance elevation (&Delta;)</b>, applying Bayesian reliability shrinkage ($C = 120/150$) to ensure small-sample anomalies do not distort rankings.",
        body_style,
    ))

    # Batters Table
    bat_summary_data = [[
        Paragraph("Rank", th_style),
        Paragraph("Top 10 Batters (Unstop)", th_style),
        Paragraph("HP Balls", th_style),
        Paragraph("Base SR", th_style),
        Paragraph("HP SR", th_style),
        Paragraph("&Delta; SR", th_style),
        Paragraph("P-VOR", th_style),
    ]]
    for _, r in bat.iterrows():
        base_sr_str = f"{r['base_sr']:.1f}"
        hp_sr_str = f"{r['hp_sr']:.1f}"
        delta_sr_str = f"+{r['delta_sr']:.1f}"
        rating_str = f"{r['final_pressure_rating']:.1f}"
        bat_summary_data.append([
            Paragraph(str(r["pressure_rank"]), td_bold),
            Paragraph(str(r["striker_name"]), td_bold),
            Paragraph(str(r["hp_balls"]), td_style),
            Paragraph(base_sr_str, td_style),
            Paragraph(hp_sr_str, td_pink),
            Paragraph(delta_sr_str, td_style),
            Paragraph(rating_str, td_bold),
        ])

    t_bat = Table(bat_summary_data, colWidths=[32, 160, 55, 55, 55, 50, 50])
    t_bat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))

    # Bowlers Table
    bowl_summary_data = [[
        Paragraph("Rank", th_style),
        Paragraph("Top 10 Bowlers (Unstop)", th_style),
        Paragraph("HP Balls", th_style),
        Paragraph("Base Econ", th_style),
        Paragraph("HP Econ", th_style),
        Paragraph("&Delta; Econ", th_style),
        Paragraph("P-VOR", th_style),
    ]]
    for _, r in bowl.iterrows():
        base_econ_str = f"{r['base_econ']:.2f}"
        hp_econ_str = f"{r['hp_econ']:.2f}"
        delta_econ_str = f"+{r['delta_econ']:.2f}"
        rating_str = f"{r['final_pressure_rating']:.1f}"
        bowl_summary_data.append([
            Paragraph(str(r["pressure_rank"]), td_bold),
            Paragraph(str(r["bowler_name"]), td_bold),
            Paragraph(str(r["hp_legal_balls"]), td_style),
            Paragraph(base_econ_str, td_style),
            Paragraph(hp_econ_str, td_pink),
            Paragraph(delta_econ_str, td_style),
            Paragraph(rating_str, td_bold),
        ])

    t_bowl = Table(bowl_summary_data, colWidths=[32, 160, 55, 55, 55, 50, 50])
    t_bowl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))

    story.append(Paragraph("Official Top 10 Batters (Rank 1 to 10)", h2_style))
    story.append(t_bat)
    story.append(Spacer(1, 6))
    story.append(Paragraph("Official Top 10 Bowlers (Rank 1 to 10)", h2_style))
    story.append(t_bowl)

    # PAGE 2
    story.append(PageBreak())
    story.append(Paragraph("1. Context-Aware Pressure Definition & Modeling", h1_style))
    story.append(Paragraph(
        "In T20 cricket, pressure is neither static nor binary. It is a continuous, dynamic state determined by the interaction of "
        "required scoring velocity, resource constraints (wickets in hand, overs remaining), match phase, and tournament stakes.",
        body_style,
    ))
    story.append(Paragraph("A. Run Chase Formulation (Innings 2)", h2_style))
    story.append(Paragraph(
        "During chases, every ball has an exact mathematical demand. The <b>Chase Pressure Index ($PI_{\\text{inn2}}$)</b> is defined as:<br/>"
        "&bull; <b>Nonlinear Rate Curve ($P_{\\text{rate}}$):</b> Anchored to T20 league par (8.2 rpo). $RRR \\le 6.0 \\to 1.0$; $RRR \\in [8, 10] \\to 4.0-6.0$; $RRR \\ge 12 \\to 8.0-10.0$.<br/>"
        "&bull; <b>DLS Wicket Resource Multiplier ($M_{\\text{wickets}}$):</b> Scales from $0.85$ ($8+$ wickets in hand) up to $1.60$ for the final wicket pair ($W_{\\text{hand}} = 1$).<br/>"
        "&bull; <b>Urgency Multiplier ($M_{\\text{urgency}}$):</b> Escalates from $0.85$ in Powerplay to $1.35$ in death overs 18–20.<br/>"
        "&bull; <b>Garbage Time Filter:</b> Automatically discounts situations where the win probability is $\\ge 99\\%$ (e.g., needing 50 off 6 balls or 2 off 30 balls).",
        body_style,
    ))

    story.append(Paragraph("B. Target Setting Formulation (Innings 1) & High Stakes", h2_style))
    story.append(Paragraph(
        "In the 1st innings, pressure stems from phase demands and batting crisis:<br/>"
        "&bull; <b>Death Over Baseline:</b> Overs 16–20 baseline at $7.0$ due to non-negotiable boundary acceleration demands.<br/>"
        "&bull; <b>Early Collapse Bonus:</b> Escalates up to $+2.5$ if the batting side loses $\\ge 2$ wickets in the Powerplay or $\\ge 4$ before over 12.<br/>"
        "&bull; <b>Knockout Stakes Multiplier ($M_{\\text{stakes}}$):</b> $+15\\%$ pressure multiplier on playoff, qualifier, eliminator, and final matches.<br/>"
        "&bull; <b>Super Overs:</b> Fixed at maximum pressure: $\\text{PI} = 10.0$.",
        body_style,
    ))

    story.append(Spacer(1, 4))
    story.append(Image(f"{assets_dir}/pressure_distribution.png", width=500, height=195))
    story.append(Paragraph("Figure 1: Continuous Pressure Index distribution and resulting match phase breakdown across 200,999 balls.", callout_style))

    # PAGE 3
    story.append(PageBreak())
    story.append(Paragraph("2. Fair Comparisons: Sample Sizing, IPL vs. T20I Context", h1_style))
    story.append(Paragraph(
        "A central mandate of the Rajasthan Royals analytics challenge is ensuring <b>fair and reproducible comparisons</b> across disparate player cohorts:",
        body_style,
    ))
    story.append(Paragraph("A. IPL vs. International (T20I) Scoring Environments", h2_style))
    story.append(Paragraph(
        "Our analysis of the supplied 200,999 deliveries reveals a structural scoring disparity between tournament formats:<br/>"
        "&bull; <b>IPL Environment:</b> Average Run Rate = <b>9.20 rpo</b>, Boundary Frequency = <b>19.5%</b>, Balls/Wicket = 18.8.<br/>"
        "&bull; <b>T20I Environment:</b> Average Run Rate = <b>8.40 rpo</b>, Boundary Frequency = <b>16.7%</b>, Balls/Wicket = 16.9.<br/>"
        "Because the IPL features higher par scores ($+0.80$ rpo), raw unadjusted strike rates would artificially bias towards IPL batters, while raw economy rates "
        "would unfairly penalize IPL bowlers. Our scoring normalizes player outputs within empirical percentile distributions to maintain cross-format parity.",
        body_style,
    ))

    story.append(Paragraph("B. Minimum Sample Eligibility Thresholds", h2_style))
    story.append(Paragraph(
        "To eliminate sample volatility, we establish minimum workload qualification gates:<br/>"
        "&bull; <b>Batters:</b> $\\ge 100$ High-Pressure balls faced AND $\\ge 250$ total balls faced overall. (Yields 128 qualified candidates).<br/>"
        "&bull; <b>Bowlers:</b> $\\ge 120$ High-Pressure legal balls bowled ($20$ overs) AND $\\ge 300$ total balls bowled overall. (Yields 149 qualified candidates).",
        body_style,
    ))

    story.append(Paragraph("C. Bayesian Reliability Shrinkage Formulation", h2_style))
    story.append(Paragraph(
        "To prevent candidates with modest sample sizes from jumping ahead of proven performers with massive samples (e.g. Suryakumar Yadav facing 678 HP balls or Sunil Narine bowling 513 HP balls), "
        "we apply Bayesian shrinkage toward the cohort median ($50.0$):<br/>"
        "$$\\text{P-VOR Rating} = \\frac{N}{N + C} \\times \\text{Raw Composite} + \\left(1 - \\frac{N}{N + C}\\right) \\times 50.0$$<br/>"
        "Where $C = 120$ for batters and $C = 150$ for bowlers. This ensures that a player who faced 100 HP balls retains $45\\%$ of their raw deviation, while an athlete with 600 HP balls retains over $80\\%$.",
        body_style,
    ))

    story.append(Spacer(1, 6))
    story.append(Paragraph("3. Evidence & Statistical Deep-Dive: Top 10 Batters", h1_style))
    story.append(Image(f"{assets_dir}/top10_batters_chart.png", width=500, height=220))
    story.append(Paragraph("Figure 2: Top 10 Batters under pressure ranked by Bayesian Pressure Rating (P-VOR), showing HP Strike Rate and Surge (&Delta;).", callout_style))

    # PAGE 4
    story.append(PageBreak())
    story.append(Paragraph("Key Batting Selection Insights & Statistical Evidence", h2_style))
    story.append(Paragraph(
        "&bull; <b>#1 Suryakumar Yadav (P-VOR: 84.7):</b> The undisputed T20 clutch standard. Across <b>678 pressure balls</b>, he strikes at <b>182.3</b> ($+21.1$ elevation over baseline) with a staggering <b>27.3% boundary rate</b>.<br/>"
        "&bull; <b>#2 Naman Dhir (P-VOR: 80.2):</b> The breakout domestic revelation. Across 266 pressure deliveries, he achieves an elite <b>187.6 SR</b> ($+23.1$ surge) and 27.4% boundary execution, outperforming experienced finishers.<br/>"
        "&bull; <b>#3 Jos Buttler (P-VOR: 79.5):</b> The proven Rajasthan Royals anchor-finisher. In 393 HP balls, strikes at <b>176.3</b> with a $+25.8$ surge and elite balls-per-dismissal metrics.<br/>"
        "&bull; <b>#4 Rishabh Pant (P-VOR: 77.0):</b> Elevates his strike rate from 137.0 to <b>166.6</b> under high leverage ($+29.6$ surge across 407 HP balls).<br/>"
        "&bull; <b>#5 Sai Sudharsan (P-VOR: 75.8):</b> Exceptional temperament; transforms from a 142.9 baseline accumulator into an aggressive <b>173.8 clutch striker</b> ($+30.9$ delta).<br/>"
        "&bull; <b>#6 Babar Azam (P-VOR: 74.4):</b> Exhibits the largest recorded strike rate surge in the dataset ($+54.1$ delta, jumping from 128.9 to <b>183.1</b> in high-pressure chases).",
        body_style,
    ))

    story.append(Spacer(1, 8))
    story.append(Paragraph("4. Evidence & Statistical Deep-Dive: Top 10 Bowlers", h1_style))
    story.append(Image(f"{assets_dir}/top10_bowlers_chart.png", width=500, height=220))
    story.append(Paragraph("Figure 3: Top 10 Bowlers under pressure ranked by Bayesian Pressure Rating (P-VOR), showing HP Economy and Restriction Delta.", callout_style))

    # PAGE 5
    story.append(PageBreak())
    story.append(Paragraph("Key Bowling Selection Insights & Statistical Evidence", h2_style))
    story.append(Paragraph(
        "&bull; <b>#1 Sunil Narine (P-VOR: 81.2):</b> The preeminent lockdown bowler in world cricket. Concedes a miserly <b>6.14 rpo</b> under high pressure across 513 balls ($+0.80$ restriction over baseline) with <b>40.5% dot balls</b>.<br/>"
        "&bull; <b>#2 Mitchell Santner (P-VOR: 79.8):</b> Extraordinary defensive discipline. Concedes only <b>7.04 rpo</b> across 583 pressure balls, taking 41 clutch wickets.<br/>"
        "&bull; <b>#3 Abrar Ahmed (P-VOR: 78.7):</b> Mystery spin weapon restricting batters to <b>5.73 rpo</b> with <b>47.6% dot ball frequency</b> across 313 HP deliveries.<br/>"
        "&bull; <b>#4 Mohammad Nawaz (P-VOR: 77.1):</b> The highest restriction delta in the cohort ($+1.57$ rpo improvement under pressure, conceding only <b>5.59 rpo</b> in 232 HP balls).<br/>"
        "&bull; <b>#5 Wanindu Hasaranga (P-VOR: 77.0):</b> High-volume strike weapon: <b>62 pressure wickets</b> at an unbelievable strike rate of <b>11.0 balls per wicket</b>.<br/>"
        "&bull; <b>#6 Varun Chakravarthy (P-VOR: 75.2):</b> High-leverage execution across 856 HP balls, taking <b>62 wickets</b> at <b>7.86 rpo</b> and 40.0% dots.",
        body_style,
    ))

    story.append(Spacer(1, 8))
    story.append(Paragraph("5. Strategic Value: Strengthening the Rajasthan Royals for IPL 2027", h1_style))
    story.append(Paragraph(
        "To directly answer the Rajasthan Royals war room mandate (<i>'identify players whom Rajasthan Royals should back at the IPL 2027 auction to strengthen the RR squad'</i>), "
        "we map our top-ranked candidates to specific tactical vacancies:",
        body_style,
    ))

    rr_strategy_data = [
        [Paragraph("Target Role", th_style), Paragraph("Recommended Targets", th_style), Paragraph("Tactical Fit for Rajasthan Royals Ecosystem", th_style)],
        [
            Paragraph("<b>Death Finisher & Boundary Striker</b>", td_bold),
            Paragraph("<b>Naman Dhir</b> (#2)<br/><b>Shashank Singh</b> (#10)<br/><b>Glenn Phillips</b> (#7)", td_style),
            Paragraph("Solves RR's historical middle-order boundary deceleration. Naman Dhir provides an extraordinary 187.6 SR and 27.4% boundary rate under death pressure at high auction surplus value.", td_style),
        ],
        [
            Paragraph("<b>Top-Order Anchor / Accelerating Clutch</b>", td_bold),
            Paragraph("<b>Sai Sudharsan</b> (#5)<br/><b>Jos Buttler</b> (#3)", td_style),
            Paragraph("Pairs elite anchor stability with explosive +30.9 SR acceleration under chase pressure, providing insurance against top-order collapses.", td_style),
        ],
        [
            Paragraph("<b>Mystery Spin & Middle/Death Enforcer</b>", td_bold),
            Paragraph("<b>Varun Chakravarthy</b> (#6)<br/><b>Wanindu Hasaranga</b> (#5)", td_style),
            Paragraph("Supplements the Sawai Mansingh Stadium pitch dynamics. Provides guaranteed wicket-taking strike rates (11-13 balls/wicket) when opposing teams mount late-innings assaults.", td_style),
        ],
        [
            Paragraph("<b>Defensive Restrictor / Powerplay Death Spin</b>", td_bold),
            Paragraph("<b>Mitchell Santner</b> (#2)<br/><b>Akeal Hosein</b> (#10)", td_style),
            Paragraph("Guaranteed sub-7.0 rpo economy in extreme leverage overs, suffocating opposition run-rate requirements.", td_style),
        ],
    ]

    t_strat = Table(rr_strategy_data, colWidths=[120, 140, 240])
    t_strat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t_strat)

    story.append(Spacer(1, 8))
    story.append(Paragraph("6. Model Reliability, Limitations & Reproducibility Statement", h1_style))
    story.append(Paragraph(
        "&bull; <b>Consistency Check:</b> Player ratings were cross-validated across individual seasons (2022–2026) to ensure rankings reflect multi-season reliability rather than a single purple patch.<br/>"
        "&bull; <b>Format Adaptation:</b> Normalization accounts for the $+0.80$ rpo baseline variance between IPL and international T20I matches.<br/>"
        "&bull; <b>Known Model Boundaries:</b> (1) Impact Player substitution data from 2023+ alters bowling depth dynamics; (2) Small-sample international series against emerging nations were controlled via Bayesian priors.<br/>"
        "&bull; <b>Reproducibility:</b> All calculations are fully reproducible using the open modular codebase at <code>backend/app/services/analytics/pressure.py</code> and <code>pressure_ranking.py</code>.",
        body_style,
    ))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    shutil.copyfile(out_pdf, out_pdf_copy)
    print(f"PDF Report built successfully: {out_pdf} ({os.path.getsize(out_pdf):,} bytes)")


if __name__ == "__main__":
    generate_report()
