"""VYNTIQ — Complete Analytical Audit & Final Report Regeneration Engine (v2).

Builds:
1. docs/SupeRR_Selector_Season_2_Methodology_Report.pdf (20-section publication PDF with ReportLab)
2. docs/SupeRR_Selector_Season_2_Methodology_Report.md (matching full Markdown report)
3. Copies to data/official_super_rr_s2/SupeRR_Selector_Season_2_Methodology_Report.pdf
"""

import os
import shutil
import pandas as pd
import numpy as np
import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DATA_DIR = r"d:\VYNTIQ Sports Intelligence\data\official_super_rr_s2"
AUDIT_DIR = r"d:\VYNTIQ Sports Intelligence\audit"
DOCS_DIR = r"d:\VYNTIQ Sports Intelligence\docs"
ASSETS_DIR = r"d:\VYNTIQ Sports Intelligence\docs\assets"

OUT_PDF = os.path.join(DOCS_DIR, "VYNTIQ_Confirmed_Round_1_Competition_Submission.pdf")
OUT_MD = os.path.join(DOCS_DIR, "VYNTIQ_Confirmed_Round_1_Competition_Submission.md")
COPY_PDF = os.path.join(DATA_DIR, "VYNTIQ_Confirmed_Round_1_Competition_Submission.pdf")


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
            self.drawRightString(558, 755, "CONFIRMED ROUND 1 COMPETITION SUBMISSION")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 747, 558, 747)

        # Footer (All pages)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 32, "VYNTIQ Sports Intelligence — Confirmed Round 1 Competition Submission")
        self.drawRightString(558, 32, f"Page {self._pageNumber} of {page_count}")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 44, 558, 44)
        self.restoreState()


def build_reports():
    print("Loading audited analytical tables...")
    bat_df = pd.read_csv(f"{AUDIT_DIR}/rankings/batters_ppr_audit.csv")
    bowl_df = pd.read_csv(f"{AUDIT_DIR}/rankings/bowlers_ppr_audit.csv")
    mapping = pd.read_csv(f"{DATA_DIR}/competition_team_player_mapping.csv")
    player_teams = mapping.groupby("player_id")["team_name"].apply(lambda s: ", ".join(sorted(set(s)))).to_dict()

    top10_bat = bat_df.head(10).copy()
    top10_bowl = bowl_df.head(10).copy()
    top10_bat["teams"] = top10_bat["player_id"].map(player_teams)
    top10_bowl["teams"] = top10_bowl["player_id"].map(player_teams)

    # Styles
    styles = getSampleStyleSheet()
    primary_color = colors.HexColor("#0F172A")
    rr_pink = colors.HexColor("#E11D48")
    accent_blue = colors.HexColor("#0284C7")
    text_dark = colors.HexColor("#1E293B")
    bg_light = colors.HexColor("#F8FAFC")
    border_color = colors.HexColor("#E2E8F0")

    title_style = ParagraphStyle("DocTitle", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=primary_color, spaceAfter=4)
    subtitle_style = ParagraphStyle("DocSubTitle", fontName="Helvetica", fontSize=9, leading=13, textColor=colors.HexColor("#475569"), spaceAfter=8)
    h1_style = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=primary_color, spaceBefore=10, spaceAfter=4, keepWithNext=True)
    h2_style = ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=9.5, leading=13, textColor=rr_pink, spaceBefore=6, spaceAfter=3, keepWithNext=True)
    body_style = ParagraphStyle("Body", fontName="Helvetica", fontSize=8, leading=11.5, textColor=colors.HexColor("#334155"), spaceAfter=5)
    callout_style = ParagraphStyle("Callout", fontName="Helvetica-Oblique", fontSize=7.5, leading=10, textColor=colors.HexColor("#1E3A8A"), spaceAfter=5)

    th_style = ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=colors.white, alignment=1)
    th_left = ParagraphStyle("THLeft", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=colors.white, alignment=0)
    td_style = ParagraphStyle("TD", fontName="Helvetica", fontSize=6.5, leading=8, textColor=text_dark, alignment=1)
    td_bold = ParagraphStyle("TDBold", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=text_dark, alignment=1)
    td_name = ParagraphStyle("TDName", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=text_dark, alignment=0)
    td_team = ParagraphStyle("TDTeam", fontName="Helvetica", fontSize=6.0, leading=7.5, textColor=colors.HexColor("#475569"), alignment=0)
    td_pink = ParagraphStyle("TDPink", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=rr_pink, alignment=1)
    td_blue = ParagraphStyle("TDBlue", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=accent_blue, alignment=1)
    formula_style = ParagraphStyle("Formula", fontName="Helvetica-Bold", fontSize=8.5, leading=12, textColor=colors.HexColor("#1E3A8A"), alignment=1, spaceBefore=3, spaceAfter=3)

    doc = SimpleDocTemplate(
        OUT_PDF,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    story = []

    # ==================== PAGE 1 ====================
    story.append(Paragraph("SUPERR SELECTOR SEASON 2 — OFFICIAL REVISED METHODOLOGY REPORT", ParagraphStyle("SubHeader", fontName="Helvetica-Bold", fontSize=8.5, textColor=rr_pink, spaceAfter=2)))
    story.append(Paragraph("VYNTIQ — Confirmed Round 1 Competition Submission", title_style))
    story.append(Paragraph("Quantifying T20 Clutch Resilience: Player Selection Under Pressure for RR IPL 2027", ParagraphStyle("DocSubTitle2", fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=primary_color, spaceAfter=4)))
    story.append(Paragraph(
        "<b>Competition:</b> Rajasthan Royals SupeRR Selector Season 2 (Round 1) | <b>Target:</b> IPL 2027 Auction Strategy<br/>"
        "<b>Audited Primary Scope:</b> 194,014 Deliveries across 837 Matches (IPL & T20I Archives 2022–2026) | <b>System:</b> VYNTIQ Sports Intelligence",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=rr_pink, spaceAfter=8))

    story.append(Paragraph("1. Executive Summary & Official Dropdown Selections", h1_style))
    story.append(Paragraph(
        "This submission presents a comprehensive, audited cricket analytics framework developed for the Rajasthan Royals war room to identify "
        "the most reliable players under extreme match pressure for the IPL 2027 auction. Following an exhaustive technical and statistical audit "
        "of the official dataset (200,999 raw deliveries), the evaluation engine implements cricket-correct extras accounting (charging 0 runs to bowlers for byes/leg-byes), "
        "striker-verified dismissal attribution, explicit isolation of the primary competitive scope (IPL + T20I: 194,014 deliveries), "
        "and mathematically calibrated Bayesian shrinkage (<i>C</i> = 120 for batters, <i>C</i> = 150 for bowlers) to eliminate sample size volatility.",
        body_style
    ))

    # Top 10 Batters Table
    story.append(Paragraph("Official Top 10 Batters (Unstop Dropdowns 1 to 10)", h2_style))
    bat_data = [[
        Paragraph("Rank", th_style),
        Paragraph("Player Name", th_left),
        Paragraph("ID", th_style),
        Paragraph("Teams in Dataset", th_left),
        Paragraph("HP Balls", th_style),
        Paragraph("Norm SR", th_style),
        Paragraph("HP SR", th_style),
        Paragraph("&Delta; SR", th_style),
        Paragraph("Control%", th_style),
        Paragraph("PPR", th_style),
    ]]
    for _, r in top10_bat.iterrows():
        bat_data.append([
            Paragraph(str(int(r["rank"])), td_bold),
            Paragraph(str(r["player_name"]), td_name),
            Paragraph(str(int(r["player_id"])), td_style),
            Paragraph(str(r["teams"]), td_team),
            Paragraph(str(int(r["pressure_balls"])), td_style),
            Paragraph(f"{r['normal_sr']:.1f}", td_style),
            Paragraph(f"{r['pressure_sr']:.1f}", td_pink),
            Paragraph(f"+{r['sr_delta']:.1f}", td_blue),
            Paragraph(f"{r['control_pct']:.1f}%", td_style),
            Paragraph(f"{r['pressure_rating']:.2f}", td_bold),
        ])
    t_bat = Table(bat_data, colWidths=[28, 88, 30, 118, 40, 40, 40, 38, 42, 40])
    t_bat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, bg_light]),
        ("GRID", (0, 0), (-1, -1), 0.5, border_color),
    ]))
    story.append(t_bat)
    story.append(Spacer(1, 4))

    # Top 10 Bowlers Table
    story.append(Paragraph("Official Top 10 Bowlers (Unstop Dropdowns 1 to 10)", h2_style))
    bowl_data = [[
        Paragraph("Rank", th_style),
        Paragraph("Player Name", th_left),
        Paragraph("ID", th_style),
        Paragraph("Teams in Dataset", th_left),
        Paragraph("HP Balls", th_style),
        Paragraph("Norm Econ", th_style),
        Paragraph("HP Econ", th_style),
        Paragraph("&Delta; Econ", th_style),
        Paragraph("HP Wkts", th_style),
        Paragraph("PPR", th_style),
    ]]
    for _, r in top10_bowl.iterrows():
        bowl_data.append([
            Paragraph(str(int(r["rank"])), td_bold),
            Paragraph(str(r["player_name"]), td_name),
            Paragraph(str(int(r["player_id"])), td_style),
            Paragraph(str(r["teams"]), td_team),
            Paragraph(str(int(r["pressure_balls"])), td_style),
            Paragraph(f"{r['normal_econ']:.2f}", td_style),
            Paragraph(f"{r['pressure_econ']:.2f}", td_pink),
            Paragraph(f"+{r['econ_delta']:.2f}", td_blue),
            Paragraph(str(int(r["pressure_wickets"])), td_style),
            Paragraph(f"{r['pressure_rating']:.2f}", td_bold),
        ])
    t_bowl = Table(bowl_data, colWidths=[28, 88, 30, 118, 40, 40, 40, 40, 40, 40])
    t_bowl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, bg_light]),
        ("GRID", (0, 0), (-1, -1), 0.5, border_color),
    ]))
    story.append(t_bowl)
    story.append(Spacer(1, 4))

    # ==================== PAGE 2 ====================
    story.append(PageBreak())
    story.append(Paragraph("2. Audit Background & Problem Formulation", h1_style))
    story.append(Paragraph(
        "T20 matches in high-stakes franchise cricket are decided in clutch leverage windows: the final overs of steep run chases, "
        "defending modest totals with dew on the ground, or recovering from top-order Powerplay collapses. Traditional aggregated statistics "
        "(raw career strike rates and tournament economy rates) conflate low-leverage stat-padding with genuine high-pressure reliability. "
        "The objective of SupeRR Selector Season 2 is to isolate deliveries where match leverage is acute (<i>PI</i> &ge; 6.5) and "
        "identify players who consistently outperform the empirical cohort baseline in high-pressure T20 situations.",
        body_style
    ))

    story.append(Paragraph("3. Dataset Inventory, Provenance & Competition Filtering Audit", h1_style))
    story.append(Paragraph(
        "The raw dataset provided contains 200,999 ball-by-ball records across 883 match files from 2022 to 2026. "
        "An explicit tournament audit identified three distinct competitive tiers:<br/>"
        "&bull; <b>Tier 1 — Indian Premier League (IPL):</b> 371 matches (367 completed, 4 abandoned washouts), 87,687 deliveries.<br/>"
        "&bull; <b>Tier 2 — International T20 (T20I):</b> 482 matches (470 completed, 12 abandoned), 106,327 deliveries.<br/>"
        "&bull; <b>Tier 3 — Secondary / Emerging Teams ('A' Competitions):</b> 30 matches, 6,985 deliveries (3.48% of records).<br/>"
        "<b>Audited Primary Scope:</b> To preserve data purity and align strictly with elite auction standards, all primary rankings evaluate "
        "the 194,014 deliveries from Tier 1 (IPL) and Tier 2 (T20I). Emerging team records are quarantined in sensitivity analysis.",
        body_style
    ))

    story.append(Paragraph("4. Cricket Rules & Accounting Corrections", h1_style))
    story.append(Paragraph(
        "A rigorous audit revealed crucial cricket accounting adjustments that distinguish this v2 engine from standard generic aggregators:<br/>"
        "1. <b>Extras & Legal Balls:</b> Wides (3,097 balls) and No-balls (Overstep: 406 balls, waist-high 'other': 573 balls) are correctly treated as non-legal deliveries. Wides do not count as balls faced by batters.<br/>"
        "2. <b>Bowler Runs Conceded:</b> Bowlers are charged strictly with runs off the bat + wide extras + no-ball extras. Byes (432 balls) and leg-byes (1,848 balls) are classified as fielding extras and contribute <b>0 runs</b> to bowler figures.<br/>"
        "3. <b>Bowler Wicket Credit:</b> Only dismissals credited to the bowler (Caught, Bowled, LBW, Stumped, Hit Wicket — 10,272 events) are counted. Run-outs (600 events) and retired outs are excluded from bowler wickets.<br/>"
        "4. <b>Striker Dismissal Alignment:</b> Batting outs are strictly charged when <code>dismissed_player_id == striker_id</code>, correctly avoiding charging strikers when non-strikers are run out (271 instances).",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Image(f"{ASSETS_DIR}/pressure_distribution.png", width=480, height=185))
    story.append(Paragraph("Figure 1: Continuous Pressure Index (PI) density distribution across 194,014 primary match deliveries, marking standard (6.5) and extreme (8.5) thresholds.", callout_style))

    # ==================== PAGE 3 ====================
    story.append(PageBreak())
    story.append(Paragraph("5. Mathematical Specification of the Pressure Index", h1_style))
    story.append(Paragraph(
        "Pressure is dynamic and non-linear. The VYNTIQ Pressure Index (<i>PI</i> &isin; [0.5, 10.0]) explicitly bifurcates match states between target-setting and run chases:",
        body_style
    ))
    story.append(Paragraph("A. Second Innings: Target Chase Formulation (<i>PI</i><sub>inn2</sub>)", h2_style))
    story.append(Paragraph(
        "During chases, exact match requirements dictate every delivery:<br/>",
        body_style
    ))
    story.append(Paragraph(
        "<i>PI</i><sub>inn2</sub> = clip( <i>P</i><sub>rate</sub>(RRR) &times; <i>M</i><sub>wickets</sub>(<i>W</i><sub>hand</sub>) &times; <i>M</i><sub>urgency</sub>(Over), 0.5, 10.0 )",
        formula_style
    ))
    story.append(Paragraph(
        "&bull; <b>Required Run Rate Curve (<i>P</i><sub>rate</sub>):</b> Piecewise continuous function anchored to T20 norms:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&bull; If RRR &le; 6.0: <i>P</i><sub>rate</sub> = max(0.5, RRR / 3.0) &nbsp;(Low leverage, continuous value 2.0 at RRR = 6.0)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&bull; If 6.0 &lt; RRR &le; 10.0: <i>P</i><sub>rate</sub> = 2.0 + (RRR &minus; 6.0) &times; 1.0<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&bull; If 10.0 &lt; RRR &le; 15.0: <i>P</i><sub>rate</sub> = 6.0 + (RRR &minus; 10.0) &times; 0.6<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&bull; If RRR &gt; 15.0: <i>P</i><sub>rate</sub> = min(10.0, 9.0 + (RRR &minus; 15.0) &times; 0.2)<br/>"
        "&bull; <b>Wicket Resource Multiplier (<i>M</i><sub>wickets</sub>):</b> Scales inversely with wickets in hand: &ge; 8 wkts: 0.85&times;; 6&ndash;7 wkts: 1.00&times;; 4&ndash;5 wkts: 1.20&times;; 2&ndash;3 wkts: 1.40&times;; 1 wkt: 1.60&times;.<br/>"
        "&bull; <b>Match Urgency Multiplier (<i>M</i><sub>urgency</sub>):</b> Scales with overs elapsed: Overs 1&ndash;6: 0.85&times;; Overs 7&ndash;15: 1.00&times;; Overs 16&ndash;17: 1.20&times;; Overs 18&ndash;20: 1.35&times;.<br/>"
        "&bull; <b>Boundary Condition / Contestability Filter:</b> If runs needed &gt; 6 &times; legal balls remaining (unwinnable off the bat without extras) or if runs needed &le; 2 with &ge; 24 legal balls remaining (foregone victory), <i>PI</i> is reset to 1.0.",
        body_style
    ))

    story.append(Paragraph("B. First Innings: Target Setting Formulation (<i>PI</i><sub>inn1</sub>)", h2_style))
    story.append(Paragraph(
        "In Innings 1, pressure is driven by phase demands, run velocity deficit, and collapse crisis:<br/>",
        body_style
    ))
    story.append(Paragraph(
        "<i>PI</i><sub>inn1</sub> = clip( <i>P</i><sub>phase</sub>(Over) + <i>P</i><sub>collapse</sub>(<i>W</i><sub>lost</sub>, Over) + <i>P</i><sub>slow</sub>(CRR, Over), 1.0, 9.5 )",
        formula_style
    ))
    story.append(Paragraph(
        "&bull; <b>Phase Baseline:</b> Overs 1&ndash;6: 3.5; Overs 7&ndash;15: 4.5; Overs 16&ndash;20: 7.0 (compulsory death acceleration).<br/>"
        "&bull; <b>Collapse Escalation:</b> Overs 1&ndash;6 with &ge; 2 wkts lost: +2.0; Overs 1&ndash;10 with &ge; 3 wkts lost: +2.5; Overs 1&ndash;15 with &ge; 5 wkts lost: +2.5.<br/>"
        "&bull; <b>Run Rate Slump:</b> Overs 8&ndash;15 with CRR &lt; 7.0 rpo: +1.0.<br/>"
        "&bull; <b>Knockout Stakes Multiplier:</b> Playoff / Knockout matches apply a +15% scalar across all deliveries. Super Overs are set to 10.0.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Image(f"{ASSETS_DIR}/pressure_by_match_phase.png", width=480, height=185))
    story.append(Paragraph("Figure 2: Pressure Index distribution across match phases (Powerplay, Middle, Death) segmented by innings.", callout_style))

    # ==================== PAGE 4 ====================
    story.append(PageBreak())
    story.append(Paragraph("6. Pressure Tiers & Delivery Distribution", h1_style))
    story.append(Paragraph(
        "Deliveries are partitioned into four operational tiers:<br/>"
        "&bull; <b>Extreme Pressure (<i>PI</i> &ge; 8.5):</b> 11.2% of deliveries. Acute finish situations (RRR &gt; 13 rpo, final 3 overs, top-order wiped out).<br/>"
        "&bull; <b>High Pressure (6.5 &le; <i>PI</i> &lt; 8.5):</b> 21.0% of deliveries. Standard high-leverage situations (death overs, tough chases, post-collapse recovery).<br/>"
        "&bull; <b>Moderate Pressure (4.0 &le; <i>PI</i> &lt; 6.5):</b> 42.4% of deliveries. Standard contest baseline (middle overs par scoring).<br/>"
        "&bull; <b>Low Pressure (<i>PI</i> &lt; 4.0):</b> 25.4% of deliveries. Low-stakes situations (routine Powerplay balls with no wickets down, blowout chases).<br/>"
        "Our standard evaluation threshold focuses on high-and-extreme leverage deliveries (<i>PI</i> &ge; 6.5, comprising 32.2% of the primary dataset).",
        body_style
    ))

    story.append(Paragraph("7. Dual Baseline Performance Framework", h1_style))
    story.append(Paragraph(
        "To measure true resilience, a player's performance under pressure is evaluated against their own baseline in non-pressure conditions (<i>PI</i> &lt; 6.5):<br/>"
        "&bull; <b>Batting Elevation:</b> &Delta;SR = SR<sub>pressure</sub> &minus; SR<sub>normal</sub>. Positive delta denotes clutch surge; negative denotes pressure contraction.<br/>"
        "&bull; <b>Bowling Restriction:</b> &Delta;Econ = Econ<sub>normal</sub> &minus; Econ<sub>pressure</sub>. Positive delta denotes tighter economy under pressure.",
        body_style
    ))

    story.append(Paragraph("8. Bayesian Shrinkage & Sample Size Calibration", h1_style))
    story.append(Paragraph(
        "In tournament cricket, unregressed statistics heavily distort small samples: a batter who faces 20 balls and hits 50 runs has a 250 SR, "
        "but zero statistical reliability. To ensure fair and robust rankings, we apply empirical Bayesian shrinkage towards the cohort median prior (50.0):<br/>",
        body_style
    ))
    story.append(Paragraph(
        "PPR = Reliability(<i>N</i>) &times; Raw Composite + (1 &minus; Reliability(<i>N</i>)) &times; 50.0<br/><font size='7.5'>where Reliability(<i>N</i>) = <i>N</i> / (<i>N</i> + <i>C</i>)</font>",
        formula_style
    ))
    story.append(Paragraph(
        "<b>Mathematical Derivation of <i>C</i>:</b> <i>C</i> represents the sample size required for an athlete's empirical data to equal the weight of the prior (50% reliability). "
        "Based on binomial and Poisson variance stabilization in T20 match records:<br/>"
        "&bull; <b>Batters (<i>C</i> = 120 balls):</b> Corresponds to ~6 completed pressure innings (20 balls each). At the eligibility threshold (<i>N</i> = 60), reliability is 33.3%. At <i>N</i> = 300, reliability is 71.4%. At <i>N</i> = 651 (Tristan Stubbs), reliability reaches 84.4%.<br/>"
        "&bull; <b>Bowlers (<i>C</i> = 150 balls):</b> Corresponds to 25 pressure overs. At <i>N</i> = 60, reliability is 28.6%. At <i>N</i> = 508 (Sunil Narine), reliability is 77.2%.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Image(f"{ASSETS_DIR}/player_reliability_confidence.png", width=480, height=185))
    story.append(Paragraph("Figure 3: Bayesian reliability weighting curve as a function of pressure sample size (N) for batters (C=120) and bowlers (C=150).", callout_style))

    # ==================== PAGE 5 ====================
    story.append(PageBreak())
    story.append(Paragraph("9. Pressure Performance Rating (PPR) Engine Specification", h1_style))
    story.append(Paragraph(
        "The Pressure Performance Rating (PPR) composite metric scales all underlying performance attributes to empirical cumulative distribution percentiles ([0, 100]):<br/>"
        "&bull; <b>Batter Raw Composite:</b> 0.35 &times; Pct(SR) + 0.25 &times; Pct(&Delta;SR) + 0.20 &times; Pct(Control%) + 0.20 &times; Pct(Avg)<br/>"
        "&bull; <b>Bowler Raw Composite:</b> 0.35 &times; Pct(Econ<sub>inv</sub>) + 0.25 &times; Pct(&Delta;Econ) + 0.20 &times; Pct(Dot%) + 0.20 &times; Pct(WktRate)<br/>"
        "Raw composite scores are regressed via the Bayesian reliability formula towards the empirical cohort prior median (50.0) to yield the final PPR. "
        "The surplus relative to the cohort prior median is designated as the Pressure Surplus Rating (PSR = PPR &minus; 50.0).",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Image(f"{ASSETS_DIR}/top10_batters_chart.png", width=480, height=195))
    story.append(Paragraph("Figure 4: Top 10 Batters by Pressure Performance Rating (PPR), reflecting Bayesian-regressed clutch performance across IPL and T20I matches.", callout_style))

    story.append(Paragraph("10. Official Top 10 Batters: Tactical Breakdown & Auction Profiles", h1_style))
    story.append(Paragraph(
        "&bull; <b>1. Tristan Stubbs (PPR: 82.23):</b> The preeminent modern T20 finisher. Across 651 pressure balls, maintains a lethal <b>168.51 SR</b> with an astounding <b>+46.70 SR delta</b> over his normal baseline. Exceptional 360-degree boundary hitting and 76.5% control under death pressure make him an indispensable asset.<br/>"
        "&bull; <b>2. David Miller (PPR: 80.34):</b> The ultimate veteran closer. Faced 805 pressure balls, scoring 1,343 runs at a <b>166.83 SR</b> (+47.25 delta). Incredible consistency in high-stakes chases across both IPL and international cricket.<br/>"
        "&bull; <b>3. Suryakumar Yadav (PPR: 80.16):</b> The highest raw strike rate among elite volume batters: <b>189.17 SR</b> across 665 pressure balls (+29.96 delta). Manipulates fields at will and dismantles death bowling regardless of boundary dimensions.<br/>"
        "&bull; <b>4. Naman Dhir (PPR: 79.39):</b> Prime auction breakout target. Striking at an outstanding <b>196.06 SR</b> across 254 pressure balls (+47.40 delta). High-potential domestic players identified through the defined performance metrics.<br/>"
        "&bull; <b>5. Tilak Varma (PPR: 78.26):</b> Massive sample anchor-accelerator. Across 904 pressure balls, scored 1,498 runs at <b>165.71 SR</b> (+34.86 delta). Possesses elite temperament against spin in middle overs and pace at the death.<br/>"
        "&bull; <b>6. Shashank Singh (PPR: 77.45):</b> Proven IPL clutch performer. In 371 pressure deliveries, achieves a <b>173.85 SR</b> (+36.28 delta). Specializes in entering during overs 14–17 and immediately executing boundary options.<br/>"
        "&bull; <b>7. Rishabh Pant (PPR: 76.76):</b> Generates the second-highest delta in the cohort: <b>+51.60 SR surge</b> under pressure, leaping from 127.29 normal SR to <b>178.89 pressure SR</b> across 379 balls.<br/>"
        "&bull; <b>8. Rinku Singh (PPR: 75.59):</b> High-volume death specialist: 823 pressure balls faced, striking at <b>166.10 SR</b> (+37.31 delta) with 70.7% control and an ice-cool temperament in last-over chases.<br/>"
        "&bull; <b>9. Jos Buttler (PPR: 75.07):</b> World-class top-order aggressor who elevates in late overs: <b>182.89 SR</b> across 380 pressure balls (+31.77 delta), pairing boundary dominance with match-winning longevity.<br/>"
        "&bull; <b>10. Glenn Phillips (PPR: 74.98):</b> Dynamic middle-order enforcer: strikes at <b>179.51 SR</b> under pressure (+44.00 delta) in 327 balls with exceptional power against high-pace bowling.",
        body_style
    ))

    # ==================== PAGE 6 ====================
    story.append(PageBreak())
    story.append(Spacer(1, 4))
    story.append(Image(f"{ASSETS_DIR}/top10_bowlers_chart.png", width=480, height=195))
    story.append(Paragraph("Figure 5: Top 10 Bowlers by Pressure Performance Rating (PPR), reflecting Bayesian-regressed clutch performance across IPL and T20I matches.", callout_style))

    story.append(Paragraph("11. Official Top 10 Bowlers: Tactical Breakdown & Auction Profiles", h1_style))
    story.append(Paragraph(
        "&bull; <b>1. Mohammad Nawaz (PPR: 78.11):</b> Outstanding defensive spin metric. Across 232 pressure balls, holds opponents to an extraordinary <b>5.51 rpo</b> (+2.10 restriction delta over normal conditions) with a 47.8% dot ball frequency.<br/>"
        "&bull; <b>2. Sunil Narine (PPR: 77.88):</b> Franchise cricket's gold standard. Across 508 pressure deliveries, maintains an elite <b>6.04 rpo economy</b> (+1.22 delta) and 34 clutch wickets. Remains virtually unhittable even with spread fields.<br/>"
        "&bull; <b>3. Abrar Ahmed (PPR: 77.72):</b> High-impact mystery leg-spin weapon. Concedes only <b>5.65 rpo</b> in 309 pressure balls (+1.70 delta) with 23 wickets, neutralizing middle-order scoring surges.<br/>"
        "&bull; <b>4. Wanindu Hasaranga (PPR: 76.36):</b> Premier strike wicket-taker under pressure: took <b>61 pressure wickets</b> in 678 balls (strike rate of 11.1 balls per wicket) at <b>7.69 rpo</b>.<br/>"
        "&bull; <b>5. Mitchell Santner (PPR: 75.66):</b> Exemplary tactical control. Recorded a 6.97 RPO economy across 583 high-pressure legal deliveries (+0.64 delta) and 41 clutch wickets, delivering genuine sub-7.0 defensive precision.<br/>"
        "&bull; <b>6. Varun Chakravarthy (PPR: 74.37):</b> Proven high-volume mystery spin enforcer: <b>61 pressure wickets</b> in 854 balls at <b>7.76 rpo</b> (+0.40 delta) with 41.5% dot ball suppression.<br/>"
        "&bull; <b>7. Jamie Overton (PPR: 73.75):</b> High-pace enforcer who improves under pressure: drops economy to <b>7.91 rpo</b> in 257 balls (+1.44 delta) while taking 24 wickets with heavy length execution.<br/>"
        "&bull; <b>8. Shaheen Afridi (PPR: 73.61):</b> High-impact Powerplay and death left-arm weapon: <b>7.61 rpo</b> across 287 pressure balls (+0.45 delta) with 30 wickets and extreme opening-over strike power.<br/>"
        "&bull; <b>9. Umran Malik (PPR: 73.24):</b> Highest restriction improvement in the bowling cohort: improves from 10.83 normal economy to <b>8.20 pressure economy</b> (+2.63 delta) with 21 wickets across 237 balls.<br/>"
        "&bull; <b>10. Rashid Khan (PPR: 72.07):</b> Immense career workload: <b>1,064 pressure balls</b> bowled, taking <b>78 pressure wickets</b> at <b>7.38 rpo</b>. Represents unmatched consistency under maximum tournament pressure.",
        body_style
    ))

    # ==================== PAGE 7 ====================
    story.append(PageBreak())
    story.append(Paragraph("12. Rajasthan Royals Squad Construction & Tactical Fit Analysis", h1_style))
    story.append(Paragraph(
        "To maximize competitive advantage at the IPL 2027 auction, the Rajasthan Royals should deploy auction capital to address four strategic squad needs:",
        body_style
    ))

    rr_strategy_data = [
        [Paragraph("Target Tactical Archetype", th_style), Paragraph("Recommended Primary Targets", th_style), Paragraph("Tactical Fit for Sawai Mansingh Stadium & RR Roster", th_style)],
        [
            Paragraph("<b>Death-Over Finisher & Boundary Striker</b>", td_bold),
            Paragraph("<b>Tristan Stubbs</b> (#1)<br/><b>Naman Dhir</b> (#4)<br/><b>Shashank Singh</b> (#6)", td_style),
            Paragraph("Addresses death-phase scoring requirements with verified elite boundary execution under acute pressure (Stubbs: 168.5 SR, 76.5% control; Dhir: 196.1 SR; Shashank: 173.9 SR) to convert contested run chases.", td_style),
        ],
        [
            Paragraph("<b>Top-Order Anchor / Accelerating Clutch</b>", td_bold),
            Paragraph("<b>Tilak Varma</b> (#5)<br/><b>Jos Buttler</b> (#9)", td_style),
            Paragraph("Combines Powerplay stability against collapses with decisive +30 to +35 SR clutch acceleration. Varma (165.7 HP SR across 904 balls) and Buttler (182.9 HP SR) maintain chase momentum at SMS Stadium.", td_style),
        ],
        [
            Paragraph("<b>Middle-Overs Strike Mystery Spin</b>", td_bold),
            Paragraph("<b>Wanindu Hasaranga</b> (#4)<br/><b>Varun Chakravarthy</b> (#6)", td_style),
            Paragraph("Capitalizes on Jaipur's expansive square boundaries with high wicket strike rates (11&ndash;14 balls/wicket) to disrupt established partnerships during middle-overs consolidation.", td_style),
        ],
        [
            Paragraph("<b>Defensive Restrictor / Powerplay Death Spin</b>", td_bold),
            Paragraph("<b>Mitchell Santner</b> (#5)<br/><b>Mohammad Nawaz</b> (#1)", td_style),
            Paragraph("Provides phase containment with verified sub-7.0 economy (Santner: 6.97 RPO across 583 HP legal balls; Nawaz: 5.51 RPO), accumulating dot-ball pressure to induce dismissals.", td_style),
        ],
    ]
    t_rr = Table(rr_strategy_data, colWidths=[125, 135, 244])
    t_rr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, bg_light]),
        ("GRID", (0, 0), (-1, -1), 0.5, border_color),
    ]))
    story.append(t_rr)
    story.append(Spacer(1, 4))

    story.append(Image(f"{ASSETS_DIR}/rr_squad_role_coverage.png", width=480, height=185))
    story.append(Paragraph("Figure 6: Average PPR rating of recommended auction targets across Rajasthan Royals core tactical archetypes.", callout_style))

    # ==================== PAGE 8 ====================
    story.append(PageBreak())
    story.append(Paragraph("13. IPL vs T20I Competition Dynamics & Format Specificity", h1_style))
    story.append(Paragraph(
        "A critical finding of our dataset audit is the structural disparity between tournament formats. Comparing 87,687 IPL deliveries (83,755 legal balls) with 106,327 T20I deliveries (101,960 legal balls):<br/>"
        "&bull; <b>IPL Run Rate:</b> <b>9.23 RPO</b> vs. <b>8.46 RPO</b> in T20I matches (+0.77 RPO higher scoring environment in the IPL; Combined: 8.81 RPO).<br/>"
        "&bull; <b>IPL Boundary Frequency:</b> <b>20.45%</b> of legal balls vs. <b>17.58%</b> in T20I matches (+2.87% higher boundary rate; Combined: 18.88%).<br/>"
        "&bull; <b>Pressure Delivery Share:</b> 31.87% in IPL vs. 32.51% in T20I matches (Combined: 32.22%).<br/>"
        "<b>Reconciliation of Preliminary Draft Discrepancy:</b> Earlier preliminary unadjusted notes cited 9.20 RPO and 19.46% boundaries; our mathematical audit verified that this preliminary variance arose from dividing boundary hits across all raw deliveries (including non-legal wides and no-balls) rather than standard legal balls. Under canonical cricket accounting (overs = legal balls / 6), the IPL scoring velocity is exactly 9.23 RPO with 20.45% boundaries, which Figure 7 and this text present with 100% agreement.<br/>"
        "The dual-baseline framework helps reduce tournament-specific scoring bias through within-format baseline comparisons.",
        body_style
    ))
    story.append(Spacer(1, 3))
    story.append(Image(f"{ASSETS_DIR}/format_comparison_ipl_vs_t20i.png", width=440, height=135))
    story.append(Paragraph("Figure 7: Scoring velocity (RPO) and boundary frequency comparison between IPL and T20I tournament environments.", callout_style))

    story.append(Paragraph("14. Multi-Definition Robustness Analysis (Strict, Standard, Broad)", h1_style))
    story.append(Paragraph(
        "To confirm that our rankings are not artifacts of a single arbitrary threshold, we evaluated candidate rankings across three distinct pressure definitions:<br/>"
        "&bull; <b>Strict Pressure (<i>PI</i> &ge; 7.5):</b> Isolates extreme leverage situations.<br/>"
        "&bull; <b>Standard Pressure (<i>PI</i> &ge; 6.5):</b> Primary baseline benchmark.<br/>"
        "&bull; <b>Broad Pressure (<i>PI</i> &ge; 5.5):</b> Broad leverage cohort.<br/>"
        "<b>Statistical Validation:</b> For batters (Figure 8), Spearman correlation is &rho; = 0.780 (&tau; = 0.603, 60% Top-10 overlap) for Standard vs. Strict, and &rho; = 0.900 (&tau; = 0.749) for Standard vs. Broad. For bowlers, rank stability is equally robust: Standard vs. Strict yields &rho; = 0.756 (&tau; = 0.568, 70% overlap) and Standard vs. Broad yields &rho; = 0.894 (&tau; = 0.723, 80% overlap). Core clutch performers (Stubbs, Miller, Suryakumar, Narine, Santner) consistently appear in the upper decile across all definitions, demonstrating robust statistical validity.",
        body_style
    ))
    story.append(Spacer(1, 3))
    story.append(Image(f"{ASSETS_DIR}/ranking_stability_across_definitions.png", width=440, height=135))
    story.append(Paragraph("Figure 8: Ranking stability across Strict (PI &ge; 7.5), Standard (PI &ge; 6.5), and Broad (PI &ge; 5.5) pressure thresholds.", callout_style))

    # ==================== PAGE 9 ====================
    story.append(PageBreak())
    story.append(Paragraph("15. Scoring Weight Sensitivity Analysis", h1_style))
    story.append(Paragraph(
        "We tested the sensitivity of the PPR engine to alternative weighting schemes:<br/>"
        "&bull; <b>Baseline Weights:</b> 35% Velocity, 25% Delta, 20% Control, 20% Secondary.<br/>"
        "&bull; <b>Velocity-Heavy (50% SR/Econ):</b> Spearman &rho; = 0.988, 90% Top-10 overlap.<br/>"
        "&bull; <b>Delta-Heavy (50% &Delta;):</b> Spearman &rho; = 0.932, 90% Top-10 overlap.<br/>"
        "&bull; <b>Control-Heavy (40% Dot/Control):</b> Spearman &rho; = 0.977, 80% Top-10 overlap.<br/>"
        "The minimal variation across weighting regimes confirms that player rankings demonstrate stability under the tested scoring-weight regimes rather than model hyper-parameter sensitivity.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Image(f"{ASSETS_DIR}/pressure_vs_normal_scatter.png", width=480, height=185))
    story.append(Paragraph("Figure 9: Scatter plot of Pressure Strike Rate vs. Normal Strike Rate, illustrating batter elevation above the parity line.", callout_style))

    story.append(Paragraph("16. Verification of Resolved Inconsistencies", h1_style))
    story.append(Paragraph(
        "This audit definitively resolves all prior ambiguities:<br/>"
        "1. <b>Mitchell Santner Economy Verification:</b> Santner recorded a 6.97 RPO economy across 583 high-pressure legal deliveries in the primary scope (677 runs conceded / 97.16 overs). The previous table listed 7.04 rpo due to unadjusted fielding extras. Both table and narrative now accurately present 6.97 rpo.<br/>"
        "2. <b>Extras Accounting:</b> Byes and leg-byes are strictly excluded from bowler runs conceded, reconciling bowler economy with official BCCI/ICC scorecard standards.<br/>"
        "3. <b>Striker-Specific Dismissal Alignment:</b> Non-striker run-outs are properly disassociated from striker dismissals, preserving true batting averages.<br/>"
        "4. <b>Contestability Feasibility Filter:</b> The contestability heuristic flags chases where runs needed exceed 6 runs per legal ball remaining (equivalent to 36 runs off the bat per 6-ball over). While total team runs in an over can theoretically exceed 36 through bowling extras (wides and no-balls) or fielding overthrows, the model treats chases requiring > 6 runs per legal delivery as non-contestable under standard play, resetting PI to 1.0 to prevent garbage-time distortions. Chases requiring &le; 2 runs with &ge; 24 legal balls remaining are similarly reset to baseline.",
        body_style
    ))

    # ==================== PAGE 10 ====================
    story.append(PageBreak())
    story.append(Paragraph("17. Edge-Case Handling & Boundary Conditions", h1_style))
    story.append(Paragraph(
        "The analytical pipeline includes automated safeguards for all structural edge cases:<br/>"
        "&bull; <b>Zero Denominators:</b> Undefined rate calculations arising from zero denominators are explicitly flagged and excluded from rate-based comparisons. Any denominator adjustment used in scoring is documented separately.<br/>"
        "&bull; <b>Super Overs:</b> Automatically flagged and hardcoded to maximum leverage (<i>PI</i> = 10.0).<br/>"
        "&bull; <b>Rain-Shortened DLS Targets:</b> Revised target values from match records take precedence over first innings totals.<br/>"
        "&bull; <b>Workload Qualification Gates:</b> Established explicit qualification thresholds (<i>N</i> &ge; 60 pressure balls faced/bowled) with full exclusion logging.",
        body_style
    ))

    story.append(Paragraph("18. Risk Analysis, Sample Limitations & Auction Traps", h1_style))
    story.append(Paragraph(
        "Franchise war rooms frequently fall prey to three predictable auction traps:<br/>"
        "1. <b>Small-Sample Outlier Trap:</b> Bidding on players with a high raw strike rate across only 15–20 deliveries. Our Bayesian shrinkage dampens these anomalies.<br/>"
        "2. <b>Recency Bias Trap:</b> Overvaluing a single playoff performance while ignoring multi-year career baselines.<br/>"
        "3. <b>Role Mismatch Trap:</b> Purchasing an anchor batter to play as a death-overs finisher, ignoring that their delta (&Delta;SR) drops under acute required run rates.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Image(f"{ASSETS_DIR}/sample_size_vs_p_vor.png", width=480, height=185))
    story.append(Paragraph("Figure 10: Pressure deliveries faced/bowled vs. Regressed PPR score, illustrating how Bayesian shrinkage pulls small samples toward the empirical cohort prior median.", callout_style))

    story.append(Paragraph("19. Reproducibility & Code Architecture Documentation", h1_style))
    story.append(Paragraph(
        "All analytical steps, data cleaning routines, and metric pipelines are fully reproducible via the VYNTIQ codebase:<br/>"
        "&bull; <b>Pipeline Execution Script:</b> <code>scripts/run_full_audit_metrics.py</code><br/>"
        "&bull; <b>Audited Delivery Dataset:</b> <code>data/official_super_rr_s2/ball_by_ball_audited.parquet</code><br/>"
        "&bull; <b>Audit Logs:</b> <code>audit/rankings/batters_ppr_audit.csv</code>, <code>bowlers_ppr_audit.csv</code>, <code>eligibility_audit.csv</code><br/>"
        "&bull; <b>Automated Verification Test Suite:</b> <code>backend/tests/test_audit_reconciliation.py</code>",
        body_style
    ))

    story.append(Paragraph("20. Conclusion & Strategic Recommendations for RR War Room", h1_style))
    story.append(Paragraph(
        "Our analytical audit provides the Rajasthan Royals with an objective, mathematically grounded roadmap for the IPL 2027 auction:<br/>"
        "1. <b>Prioritize Tristan Stubbs and Naman Dhir:</b> High-pressure performance ratings and potential auction relevance for world-class death finishing.<br/>"
        "2. <b>Target Mitchell Santner</b> as an elite defensive restrictor to control Jaipur's middle overs. Recorded a 6.97 RPO economy across 583 high-pressure legal deliveries.<br/>"
        "3. <b>Pair Wanindu Hasaranga or Varun Chakravarthy</b> with existing pace assets to maintain aggressive wicket-taking pressure throughout all 20 overs.<br/>"
        "By grounding squad construction in verified high-leverage data rather than unadjusted career totals, Rajasthan Royals can support more informed, data-driven squad construction and auction decisions.",
        body_style
    ))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    shutil.copyfile(OUT_PDF, COPY_PDF)
    print(f"PDF built successfully: {OUT_PDF} ({os.path.getsize(OUT_PDF):,} bytes)")

    # Build matching Markdown Report
    build_markdown_report(top10_bat, top10_bowl)


def build_markdown_report(top10_bat, top10_bowl):
    md_content = f"""# SupeRR Selector Season 2 — Official Methodology Report (Audited v2)

**Competition:** Rajasthan Royals — SupeRR Selector Season 2 (Round 1)  
**Challenge:** Identify the Most Reliable Players Under Pressure  
**Target:** IPL 2027 Auction Strategy  
**Dataset Analyzed:** 194,014 Audited Deliveries across 837 Matches (Primary Scope: IPL & T20I Archives 2022–2026)  
**Author:** VYNTIQ Sports Intelligence Platform  
**Generated PDF File:** `docs/VYNTIQ_Confirmed_Round_1_Competition_Submission.pdf`

---

## 1. Executive Summary & Official Dropdown Selections

This submission presents a comprehensive, audited cricket analytics framework developed for the Rajasthan Royals war room to identify the most reliable players under extreme match pressure for the IPL 2027 auction. Following an exhaustive technical and statistical audit of the official dataset (200,999 raw deliveries), the evaluation engine implements cricket-correct extras accounting (charging 0 runs to bowlers for byes/leg-byes), striker-verified dismissal attribution, explicit isolation of the primary competitive scope (IPL + T20I: 194,014 deliveries), and mathematically calibrated Bayesian shrinkage ($C = 120$ for batters, $C = 150$ for bowlers) to eliminate sample size volatility.

### Top 10 Batters (Unstop Dropdowns 1 to 10)

| Rank | Player Name | Player ID | Teams in Dataset | HP Balls | Normal SR | **HP Strike Rate** | **Elevation ($\\Delta\\text{{SR}}$)** | Control % | **PPR Rating** |
|:---:|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
"""
    for _, r in top10_bat.iterrows():
        md_content += f"| **{int(r['rank'])}** | **{r['player_name']}** | `{int(r['player_id'])}` | {r['teams']} | {int(r['pressure_balls'])} | {r['normal_sr']:.1f} | **{r['pressure_sr']:.1f}** | **+{r['sr_delta']:.1f}** | {r['control_pct']:.1f}% | **{r['pressure_rating']:.2f}** |\n"

    md_content += """
---

### Top 10 Bowlers (Unstop Dropdowns 1 to 10)

| Rank | Player Name | Player ID | Teams in Dataset | HP Balls | Normal Econ | **HP Economy** | **Restriction ($\\Delta\\text{{Econ}}$)** | HP Wkts | **PPR Rating** |
|:---:|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
"""
    for _, r in top10_bowl.iterrows():
        md_content += f"| **{int(r['rank'])}** | **{r['player_name']}** | `{int(r['player_id'])}` | {r['teams']} | {int(r['pressure_balls'])} | {r['normal_econ']:.2f} | **{r['pressure_econ']:.2f}** | **+{r['econ_delta']:.2f}** | {int(r['pressure_wickets'])} | **{r['pressure_rating']:.2f}** |\n"

    md_content += """
---

## 2. Audit Background & Problem Formulation
T20 matches in high-stakes franchise cricket are decided in clutch leverage windows: the final overs of steep run chases, defending modest totals with dew on the ground, or recovering from top-order Powerplay collapses. Traditional aggregated statistics conflate low-leverage stat-padding with genuine high-pressure reliability. The objective of SupeRR Selector Season 2 is to isolate deliveries where match leverage is acute ($PI \\ge 6.5$) and identify players who consistently outperform the empirical cohort baseline in high-pressure T20 situations.

---

## 3. Dataset Inventory, Provenance & Competition Filtering Audit
The raw dataset provided contains 200,999 ball-by-ball records across 883 match files from 2022 to 2026. An explicit tournament audit identified three distinct competitive tiers:
- **Tier 1 — Indian Premier League (IPL):** 371 matches (367 completed, 4 abandoned washouts), 87,687 deliveries.
- **Tier 2 — International T20 (T20I):** 482 matches (470 completed, 12 abandoned), 106,327 deliveries.
- **Tier 3 — Secondary / Emerging Teams ('A' Competitions):** 30 matches, 6,985 deliveries (3.48% of records).

**Audited Primary Scope:** All primary rankings evaluate the 194,014 deliveries from Tier 1 (IPL) and Tier 2 (T20I). Secondary emerging team records are quarantined in sensitivity analysis.

---

## 4. Cricket Rules & Accounting Corrections
1. **Extras & Legal Balls:** Wides (3,097 balls) and No-balls (Overstep: 406 balls, waist-high 'other': 573 balls) are correctly treated as non-legal deliveries. Wides do not count as balls faced by batters.
2. **Bowler Runs Conceded:** Bowlers are charged strictly with runs off the bat + wide extras + no-ball extras. Byes (432 balls) and leg-byes (1,848 balls) are classified as fielding extras and contribute **0 runs** to bowler figures.
3. **Bowler Wicket Credit:** Only dismissals credited to the bowler (Caught, Bowled, LBW, Stumped, Hit Wicket — 10,272 events) are counted. Run-outs (600 events) and retired outs are excluded.
4. **Striker Dismissal Alignment:** Batting outs are strictly charged when `dismissed_player_id == striker_id`, correctly avoiding charging strikers when non-strikers are run out (271 instances).

![Figure 1: Pressure Distribution](assets/pressure_distribution.png)

---

## 5. Mathematical Specification of the Pressure Index
Pressure is dynamic and non-linear. The VYNTIQ Pressure Index ($PI \\in [0.5, 10.0]$) explicitly bifurcates match states between target-setting and run chases:

### Second Innings: Target Chase Formulation ($PI_{\\text{inn2}}$)
$$PI_{\\text{inn2}} = \\text{clip}\\Big(P_{\\text{rate}}(RRR) \\times M_{\\text{wickets}}(W_{\\text{hand}}) \\times M_{\\text{urgency}}(\\text{Over}), 0.5, 10.0\\Big)$$

- **Required Run Rate Curve ($P_{\\text{rate}}$):** Piecewise continuous function anchored to T20 norms:
  - If $\\text{RRR} \\le 6.0$: $P_{\\text{rate}} = \\max(0.5, \\text{RRR} / 3.0)$ (low leverage, continuous value $2.0$ at $\\text{RRR} = 6.0$).
  - If $6.0 < \\text{RRR} \\le 10.0$: $P_{\\text{rate}} = 2.0 + (\\text{RRR} - 6.0) \\times 1.0$.
  - If $10.0 < \\text{RRR} \\le 15.0$: $P_{\\text{rate}} = 6.0 + (\\text{RRR} - 10.0) \\times 0.6$.
  - If $\\text{RRR} > 15.0$: $P_{\\text{rate}} = \\min(10.0, 9.0 + (\\text{RRR} - 15.0) \\times 0.2)$.
- **Wicket Resource Multiplier ($M_{\\text{wickets}}$):** Scales inversely with batting resources: $\\ge 8$ wkts: $0.85\\times$; 6–7 wkts: $1.00\\times$; 4–5 wkts: $1.20\\times$; 2–3 wkts: $1.40\\times$; 1 wkt: $1.60\\times$.
- **Match Urgency Multiplier ($M_{\\text{urgency}}$):** Scales with over elapsed: Overs 1–6: $0.85\\times$; Overs 7–15: $1.00\\times$; Overs 16–17: $1.20\\times$; Overs 18–20: $1.35\\times$.
- **Boundary Condition / Contestability Filter:** If runs needed $> 6 \\times$ legal balls remaining or if runs needed $\\le 2$ with $\\ge 24$ balls remaining, $PI$ is reset to $1.0$.

### First Innings: Target Setting Formulation ($PI_{\\text{inn1}}$)
$$PI_{\\text{inn1}} = \\text{clip}\\Big(P_{\\text{phase}}(\\text{Over}) + P_{\\text{collapse}}(W_{\\text{lost}}, \\text{Over}) + P_{\\text{slow}}(CRR, \\text{Over}), 1.0, 9.5\\Big)$$

- **Phase Baseline:** Overs 1–6: $3.5$; Overs 7–15: $4.5$; Overs 16–20: $7.0$.
- **Collapse Escalation:** Overs 1–6 with $\\ge 2$ wkts lost: $+2.0$; Overs 1–10 with $\\ge 3$ wkts lost: $+2.5$; Overs 1–15 with $\\ge 5$ wkts lost: $+2.5$.
- **Knockout Stakes Multiplier:** Playoff / Knockout matches apply a $+15\\%$ scalar across all deliveries. Super Overs are set to $10.0$.

![Figure 2: Pressure by Match Phase](assets/pressure_by_match_phase.png)

---

## 6. Pressure Tiers & Delivery Distribution
- **Extreme Pressure ($PI \\ge 8.5$):** 11.2% of deliveries. Acute finish situations.
- **High Pressure ($6.5 \\le PI < 8.5$):** 21.0% of deliveries. Standard high-leverage situations.
- **Moderate Pressure ($4.0 \\le PI < 6.5$):** 42.4% of deliveries. Standard contest baseline.
- **Low Pressure ($PI < 4.0$):** 25.4% of deliveries. Low-stakes situations.

---

## 7. Dual Baseline Performance Framework
- **Batting Elevation:** $\\Delta\\text{SR} = \\text{SR}_{\\text{pressure}} - \\text{SR}_{\\text{normal}}$.
- **Bowling Restriction:** $\\Delta\\text{Econ} = \\text{Econ}_{\\text{normal}} - \\text{Econ}_{\\text{pressure}}$.

---

## 8. Bayesian Shrinkage & Sample Size Calibration
$$\\text{PPR} = \\frac{N}{N + C} \\times \\text{Raw Composite} + \\left(1 - \\frac{N}{N + C}\\right) \\times 50.0$$
- **Batters ($C = 120$ balls):** Corresponds to ~6 completed pressure innings (20 balls each).
- **Bowlers ($C = 150$ balls):** Corresponds to 25 pressure overs.

![Figure 3: Reliability Curve](assets/player_reliability_confidence.png)

---

## 9. Pressure Performance Rating (PPR) Engine Specification
Composite scores normalize metrics using empirical cumulative distribution percentiles ($[0, 100]$) and apply Bayesian shrinkage towards the empirical cohort prior median ($50.0$). The difference is the Pressure Surplus Rating ($PSR = PPR - 50.0$).

![Figure 4: Top 10 Batters Chart](assets/top10_batters_chart.png)

---

## 10. Official Top 10 Batters: Tactical Breakdown & Auction Profiles
1. **Tristan Stubbs (PPR: 82.23):** 651 HP balls, 168.51 SR (+46.70 delta), 76.5% control. World-class 360-degree death execution.
2. **David Miller (PPR: 80.34):** 805 HP balls, 166.83 SR (+47.25 delta). Veteran closer with ice in his veins.
3. **Suryakumar Yadav (PPR: 80.16):** 665 HP balls, 189.17 SR (+29.96 delta). Field manipulation genius.
4. **Naman Dhir (PPR: 79.39):** 254 HP balls, 196.06 SR (+47.40 delta). High-potential domestic players identified through the defined performance metrics.
5. **Tilak Varma (PPR: 78.26):** 904 HP balls, 165.71 SR (+34.86 delta). Heavy-volume clutch accumulator and finisher.
6. **Shashank Singh (PPR: 77.45):** 371 HP balls, 173.85 SR (+36.28 delta). Elite middle-to-death acceleration.
7. **Rishabh Pant (PPR: 76.76):** 379 HP balls, 178.89 SR (+51.60 delta). Exceptional chase elevation.
8. **Rinku Singh (PPR: 75.59):** 823 HP balls, 166.10 SR (+37.31 delta) with 70.7% control. Proven death-over match-winner.
9. **Jos Buttler (PPR: 75.07):** 380 HP balls, 182.89 SR (+31.77 delta). Explosive top-order accelerator.
10. **Glenn Phillips (PPR: 74.98):** 327 HP balls, 179.51 SR (+44.00 delta). Dynamic middle-order power striker.

![Figure 5: Top 10 Bowlers Chart](assets/top10_bowlers_chart.png)

---

## 11. Official Top 10 Bowlers: Tactical Breakdown & Auction Profiles
1. **Mohammad Nawaz (PPR: 78.11):** 232 HP balls, 5.51 rpo (+2.10 delta), 47.8% dots. Defensive lockdown master.
2. **Sunil Narine (PPR: 77.88):** 508 HP balls, 6.04 rpo (+1.22 delta), 34 wickets. Gold-standard franchise bowler.
3. **Abrar Ahmed (PPR: 77.72):** 309 HP balls, 5.65 rpo (+1.70 delta), 23 wickets. Unreadable mystery leg-spin.
4. **Wanindu Hasaranga (PPR: 76.36):** 678 HP balls, 7.69 rpo, 61 wickets (11.1 balls/wkt). High-leverage strike weapon.
5. **Mitchell Santner (PPR: 75.66):** 583 HP balls, recorded a 6.97 RPO economy across 583 high-pressure legal deliveries (+0.64 delta), 41 wickets. Sub-7.0 defensive precision.
6. **Varun Chakravarthy (PPR: 74.37):** 854 HP balls, 7.76 rpo, 61 wickets, 41.5% dots. Consistent mystery enforcer.
7. **Jamie Overton (PPR: 73.75):** 257 HP balls, 7.91 rpo (+1.44 delta), 24 wickets. High-pace heavy length execution.
8. **Shaheen Afridi (PPR: 73.61):** 287 HP balls, 7.61 rpo (+0.45 delta), 30 wickets. Left-arm Powerplay/death strike bowler.
9. **Umran Malik (PPR: 73.24):** 237 HP balls, 8.20 rpo (+2.63 delta), 21 wickets. Highest restriction surge in cohort.
10. **Rashid Khan (PPR: 72.07):** 1,064 HP balls, 7.38 rpo, 78 wickets. Unrivaled career clutch longevity.

---

## 12. Rajasthan Royals Squad Construction & Tactical Fit Analysis

| Target Tactical Archetype | Recommended Primary Targets | Tactical Fit for Sawai Mansingh Stadium & RR Roster |
|:---|:---|:---|
| **Death Finisher & Boundary Striker** | **Tristan Stubbs** (#1)<br/>**Naman Dhir** (#4)<br/>**Shashank Singh** (#6) | Addresses death-phase scoring requirements with verified elite boundary execution under acute pressure (Stubbs: 168.5 SR, 76.5% control; Dhir: 196.1 SR; Shashank: 173.9 SR) to convert contested run chases. |
| **Top-Order Anchor / Accelerating Clutch** | **Tilak Varma** (#5)<br/>**Jos Buttler** (#9) | Combines Powerplay stability against collapses with decisive +30 to +35 SR clutch acceleration. Varma (165.7 HP SR across 904 balls) and Buttler (182.9 HP SR) maintain chase momentum at SMS Stadium. |
| **Middle-Overs Strike Mystery Spin** | **Wanindu Hasaranga** (#4)<br/>**Varun Chakravarthy** (#6) | Capitalizes on Jaipur's expansive square boundaries with high wicket strike rates (11–14 balls/wicket) to disrupt established partnerships during middle-overs consolidation. |
| **Defensive Restrictor / Powerplay Death Spin** | **Mitchell Santner** (#5)<br/>**Mohammad Nawaz** (#1) | Provides phase containment with verified sub-7.0 economy (Santner: 6.97 RPO across 583 HP legal balls; Nawaz: 5.51 RPO), accumulating dot-ball pressure to induce dismissals. |

![Figure 6: Tactical Role Coverage](assets/rr_squad_role_coverage.png)

---

## 13. IPL vs T20I Competition Dynamics & Format Specificity
- **IPL Scoring Environment:** 9.23 RPO, 20.45% boundaries across 83,755 legal balls.
- **T20I Scoring Environment:** 8.46 RPO, 17.58% boundaries across 101,960 legal balls.
- **Combined Primary Environment:** 8.81 RPO, 18.88% boundaries across 185,715 legal balls.
- **Reconciliation of Preliminary Draft Discrepancy:** Earlier unadjusted preliminary notes cited 9.20 RPO and 19.46% boundaries; audit confirmed that this preliminary variance arose from dividing boundary hits across raw deliveries (including wides and no-balls) rather than standard legal deliveries. Under canonical cricket accounting (overs = legal balls / 6), the IPL scoring velocity is exactly 9.23 RPO with 20.45% boundaries, which Figure 7 and this text present with 100% agreement.
- The dual-baseline framework helps reduce tournament-specific scoring bias through within-format baseline comparisons.

![Figure 7: IPL vs T20I Format Comparison](assets/format_comparison_ipl_vs_t20i.png)

---

## 14. Multi-Definition Robustness Analysis
- **Batters (Figure 8):**
  - Standard ($PI \\ge 6.5$) vs. Strict ($PI \\ge 7.5$): $\\rho = 0.780$, $\\tau = 0.603$, 60% Top-10 overlap.
  - Standard ($PI \\ge 6.5$) vs. Broad ($PI \\ge 5.5$): $\\rho = 0.900$, $\\tau = 0.749$, 40% Top-10 overlap.
- **Bowlers:**
  - Standard ($PI \\ge 6.5$) vs. Strict ($PI \\ge 7.5$): $\\rho = 0.756$, $\\tau = 0.568$, 70% Top-10 overlap.
  - Standard ($PI \\ge 6.5$) vs. Broad ($PI \\ge 5.5$): $\\rho = 0.894$, $\\tau = 0.723$, 80% Top-10 overlap.

![Figure 8: Ranking Stability](assets/ranking_stability_across_definitions.png)

---

## 15. Scoring Weight Sensitivity Analysis
Rankings remain remarkably stable across Velocity-Heavy ($\\rho = 0.988$), Delta-Heavy ($\\rho = 0.932$), and Control-Heavy ($\\rho = 0.977$) regimes.

![Figure 9: Scatter Plot](assets/pressure_vs_normal_scatter.png)

---

## 16. Verification of Resolved Inconsistencies
1. **Mitchell Santner Economy Verified:** Santner recorded a 6.97 RPO economy across 583 high-pressure legal deliveries in the primary scope (677 runs conceded / 97.16 overs). The previous table listed 7.04 rpo due to unadjusted fielding extras. Both table and narrative now accurately present 6.97 rpo.
2. **Extras Accounting Corrected:** Bowler runs conceded strictly exclude byes and leg-byes.
3. **Striker Dismissals Corrected:** Non-striker runouts properly excluded from striker dismissals.
4. **Contestability Feasibility Filter:** The contestability heuristic flags chases where runs needed exceed 6 runs per legal ball remaining as non-contestable under standard play, resetting PI to 1.0 to prevent garbage-time distortions.

---

## 17. Edge-Case Handling & Boundary Conditions
- **Zero Denominators:** Undefined rate calculations arising from zero denominators are explicitly flagged and excluded from rate-based comparisons. Any denominator adjustment used in scoring is documented separately.
- **Super Overs:** Automatically flagged and hardcoded to maximum leverage ($PI = 10.0$).
- **Rain-Shortened DLS Targets:** Revised target values from match records take precedence over first innings totals.
- **Workload Qualification Gates:** Established explicit qualification thresholds ($N \\ge 60$ pressure balls faced/bowled) with full exclusion logging.

---

## 18. Risk Analysis, Sample Limitations & Auction Traps
Bayesian shrinkage protects the war room against small-sample traps, recency bias, and role mismatches.

![Figure 10: Sample Size vs PPR](assets/sample_size_vs_p_vor.png)

---

## 19. Reproducibility & Code Architecture Documentation
- Execution Script: `scripts/run_full_audit_metrics.py`
- Audited Parquet: `data/official_super_rr_s2/ball_by_ball_audited.parquet`
- Full Audit Logs: `audit/rankings/batters_ppr_audit.csv`, `bowlers_ppr_audit.csv`, `eligibility_audit.csv`
- Automated Verification Tests: `backend/tests/test_audit_reconciliation.py`

---

## 20. Conclusion & Strategic Recommendations for RR War Room
1. **Prioritize Tristan Stubbs and Naman Dhir:** High-pressure performance ratings and potential auction relevance for world-class death finishing.
2. **Target Mitchell Santner** as an elite defensive restrictor to control Jaipur's middle overs. Recorded a 6.97 RPO economy across 583 high-pressure legal deliveries.
3. **Pair Wanindu Hasaranga or Varun Chakravarthy** with existing pace assets to maintain aggressive wicket-taking pressure throughout all 20 overs.

By grounding squad construction in verified high-leverage data rather than unadjusted career totals, Rajasthan Royals can support more informed, data-driven squad construction and auction decisions.
"""
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Markdown Report built successfully: {OUT_MD}")


if __name__ == "__main__":
    build_reports()

