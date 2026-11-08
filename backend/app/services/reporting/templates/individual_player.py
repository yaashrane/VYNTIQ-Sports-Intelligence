"""Report Template B: Individual Player Evaluation Report."""

from typing import Any
from reportlab.platypus import Flowable, Image, KeepTogether, Paragraph, Spacer, Table, TableStyle
from backend.app.services.reporting.charts import generate_player_radar_chart
from backend.app.services.reporting.styles import (
    COLOR_BORDER_LIGHT,
    COLOR_CARD,
    COLOR_CHARCOAL,
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
from backend.app.services.reporting.templates.base import (
    create_header_banner,
    create_key_value_grid,
    create_section_header,
)

styles = get_vyntiq_stylesheet()


def build_individual_player_flowables(
    data: dict[str, Any], usable_width: float = 540.0
) -> list[Flowable]:
    """Compile structured flowables for an Individual Player Evaluation Dossier."""
    story: list[Flowable] = []

    player = data.get("player", {})
    score = data.get("score", {})
    sample = data.get("sample_workload", {})
    dimensions = data.get("dimensions", [])
    explanation = data.get("explanation", {})
    breakdown = data.get("breakdown", {})
    provenance = data.get("provenance", {})

    player_name = player.get("player_name", "Athlete")
    role = player.get("role", "BATTER")

    # 1. Candidate Header Banner
    subtitle = (
        f"Candidate ID: {player.get('player_id', 'N/A')}  |  "
        f"Nationality: {player.get('country', 'India')}  |  "
        f"Batting: {player.get('batting_hand', 'RIGHT')}  |  "
        f"Bowling: {player.get('bowling_style', 'N/A')}"
    )
    story.append(
        create_header_banner(
            title=data.get("title", f"Candidate Dossier — {player_name}"),
            subtitle=subtitle,
            badge_label=role,
            badge_color="MAGENTA",
            usable_width=usable_width,
        )
    )
    story.append(Spacer(1, 8))

    # 2. Executive Rating Card
    story.extend(create_section_header("1. Executive Evaluation Rating", usable_width))

    vor_score = score.get("vor_score", 0.0)
    raw_score = score.get("raw_composite_score", 0.0)
    c_n = score.get("reliability_factor", 1.0)
    rel_status = score.get("reliability_status", "ADEQUATE")

    score_card_data = [
        [
            Paragraph(f"<b>{vor_score:.1f}</b>", styles["HeroScore"]),
            Paragraph(f"<b>{raw_score:.1f}</b>", styles["Heading1"]),
            Paragraph(f"<b>{c_n:.2f} ({rel_status})</b>", styles["Heading2"]),
            Paragraph(f"<b>{score.get('cohort_id', 'IPL_T20')}</b>", styles["TableCellBold"]),
        ],
        [
            Paragraph("COMPOSITE VOR RATING", styles["HeroLabel"]),
            Paragraph("RAW COMPOSITE (0–100)", styles["Caption"]),
            Paragraph("RELIABILITY FACTOR C(N)", styles["Caption"]),
            Paragraph("BENCHMARK COHORT", styles["Caption"]),
        ],
    ]
    t_score = Table(score_card_data, colWidths=[usable_width / 4] * 4)
    t_score.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER_LIGHT),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )
    story.append(t_score)
    story.append(Spacer(1, 10))

    # 3. Workload Activity Grid
    story.extend(create_section_header("2. Match Workloads & Sample Counts", usable_width))
    workload_items = [
        ("Total Innings", str(sample.get("innings") or "—")),
        ("Balls Faced", str(sample.get("balls_faced") or "—")),
        ("Dismissals", str(sample.get("dismissals") or "—")),
        ("Legal Balls Bowled", str(sample.get("legal_balls_bowled") or "—")),
        ("Wickets Taken", str(sample.get("wickets") or "—")),
        ("Dataset Reference", provenance.get("dataset_id", "DEFAULT")),
        ("Eligibility Status", "VERIFIED ELIGIBLE" if score.get("is_eligible", True) else "INELIGIBLE"),
        ("Engine Version", f"v{score.get('scoring_version', '1.0.0')}"),
    ]
    story.append(create_key_value_grid(workload_items, usable_width=usable_width, col_count=4))
    story.append(Spacer(1, 10))

    # 4. Role Dimension Profile (Table & Radar Chart side by side)
    story.extend(create_section_header("3. Role Dimension Profile & Radar Polygon", usable_width))

    dim_table_data = [
        [
            Paragraph("<b>Evaluation Dimension</b>", styles["TableHeader"]),
            Paragraph("<b>Percentile</b>", styles["TableHeaderRight"]),
            Paragraph("<b>Weight</b>", styles["TableHeaderRight"]),
            Paragraph("<b>Points</b>", styles["TableHeaderRight"]),
        ]
    ]
    for d in dimensions:
        dim_table_data.append(
            [
                Paragraph(d.get("dimension_name", ""), styles["TableCellBold"]),
                Paragraph(f"{d.get('dimension_score', 0.0):.1f}", styles["TableCellNumberBold"]),
                Paragraph(f"{d.get('weight', 0.0):.2f}", styles["TableCellNumber"]),
                Paragraph(f"{d.get('contribution', 0.0):.2f}", styles["TableCellNumber"]),
            ]
        )

    t_dims = Table(dim_table_data, colWidths=[130, 55, 45, 50], repeatRows=1)
    t_dims.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
            ]
        )
    )

    chart_buf = generate_player_radar_chart(dimensions, player_name, width_in=3.4, height_in=2.4)
    if chart_buf:
        chart_img = Image(chart_buf, width=240, height=160)
        profile_layout = Table([[t_dims, chart_img]], colWidths=[280, 260])
        profile_layout.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(profile_layout)
    else:
        story.append(t_dims)

    story.append(Spacer(1, 10))

    # 5. "The Story Behind the Metric" (Deterministic Explainability)
    story.extend(create_section_header("4. The Story Behind the Metric (Explainability)", usable_width))

    # Narrative Summary
    narrative = explanation.get("narrative_summary") or "Evaluation completed across peer role cohort."
    story.append(Paragraph(narrative, styles["BodyText"]))
    story.append(Spacer(1, 6))

    # Strengths and Drag Factors 2-column container
    strengths = explanation.get("top_strengths", [])
    drags = explanation.get("drag_factors", [])

    str_paragraphs = [Paragraph("<b>PRIMARY OUTLIER STRENGTHS</b>", styles["Heading2"])]
    if strengths:
        for s in strengths:
            str_paragraphs.append(
                Paragraph(f"• <font color='{COLOR_LIME_DARK.hexval()}'><b>{s}</b></font>", styles["BodyText"])
            )
    else:
        str_paragraphs.append(Paragraph("<i>No outlier strengths recorded.</i>", styles["Caption"]))

    drag_paragraphs = [Paragraph("<b>PERFORMANCE DRAG FACTORS</b>", styles["Heading2"])]
    if drags:
        for d in drags:
            drag_paragraphs.append(
                Paragraph(f"• <font color='{COLOR_WARNING_DARK.hexval()}'><b>{d}</b></font>", styles["BodyText"])
            )
    else:
        drag_paragraphs.append(Paragraph("<i>No severe drag factors recorded.</i>", styles["Caption"]))

    t_factors = Table([[str_paragraphs, drag_paragraphs]], colWidths=[usable_width / 2, usable_width / 2])
    t_factors.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), COLOR_LIME_TINT),
                ("BACKGROUND", (1, 0), (1, 0), COLOR_WARNING_TINT),
                ("BOX", (0, 0), (0, 0), 0.6, COLOR_LIME_DARK),
                ("BOX", (1, 0), (1, 0), 0.6, COLOR_WARNING),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t_factors)
    story.append(Spacer(1, 8))

    # Mathematical Reconciliation Audit Line
    reconciled = breakdown.get("is_reconciled", True)
    discrepancy = breakdown.get("reconciliation_discrepancy", 0.0)
    audit_text = (
        f"<b>Mathematical Audit Status:</b> "
        f"<font color='{COLOR_LIME_DARK.hexval()}'><b>{'RECONCILED' if reconciled else 'DISCREPANCY DETECTED'}</b></font>  |  "
        f"Discrepancy: {discrepancy:.3f} pts  |  "
        f"Lineage: Delivery IDs traceable to source matches in {provenance.get('dataset_id', 'DEFAULT')}"
    )
    story.append(Paragraph(audit_text, styles["Caption"]))

    return story
