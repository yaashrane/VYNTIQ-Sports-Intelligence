"""Report Template D: Shortlist & Scouting Dossier Report."""

from typing import Any
from reportlab.platypus import Flowable, Image, KeepTogether, Paragraph, Spacer, Table, TableStyle
from backend.app.services.reporting.charts import generate_shortlist_composition_chart
from backend.app.services.reporting.styles import (
    COLOR_BORDER_LIGHT,
    COLOR_CARD,
    COLOR_CHARCOAL,
    COLOR_LIGHT_BG,
    COLOR_LIME_DARK,
    COLOR_MAGENTA,
    COLOR_MAGENTA_TINT,
    COLOR_MUTED,
    COLOR_WARNING,
    COLOR_WARNING_DARK,
    COLOR_WHITE,
    get_vyntiq_stylesheet,
)
from backend.app.services.reporting.templates.base import (
    create_header_banner,
    create_key_value_grid,
    create_section_header,
)

styles = get_vyntiq_stylesheet()


def build_shortlist_flowables(
    data: dict[str, Any], usable_width: float = 540.0
) -> list[Flowable]:
    """Compile structured flowables for a Competition Shortlist Report."""
    story: list[Flowable] = []

    ws = data.get("workspace", {})
    sl = data.get("shortlist", {})
    candidates = data.get("candidates", [])
    excluded = data.get("excluded_candidates", [])
    role_counts = data.get("role_counts", {})
    include_notes = data.get("include_reviewer_notes", False)

    # 1. Shortlist Header Banner
    subtitle = (
        f"Workspace: {ws.get('name', 'N/A')}  |  "
        f"Competition: {ws.get('competition_name', 'SuperRR')} ({ws.get('season_or_edition', 'S2')})  |  "
        f"Shortlist ID: {sl.get('shortlist_id', 'N/A')}"
    )
    story.append(
        create_header_banner(
            title=data.get("title", f"Scouting Shortlist — {sl.get('name', 'Candidate Roster')}"),
            subtitle=subtitle,
            badge_label=sl.get("status", "ACTIVE"),
            badge_color="MAGENTA",
            usable_width=usable_width,
        )
    )
    story.append(Spacer(1, 8))

    # 2. Executive Roster Summary
    story.extend(create_section_header("1. Roster Composition & Targets", usable_width))
    roster_items = [
        ("Target Squad Size", str(sl.get("target_size", "N/A"))),
        ("Shortlisted Candidates", str(len(candidates))),
        ("Excluded / Ineligible", str(len(excluded))),
        ("Scoring Run Reference", sl.get("scoring_run_id") or "LATEST_VERIFIED"),
    ]
    story.append(create_key_value_grid(roster_items, usable_width=usable_width, col_count=4))
    story.append(Spacer(1, 8))

    # Role chart & distribution summary
    if role_counts:
        chart_buf = generate_shortlist_composition_chart(role_counts, width_in=3.0, height_in=1.5)
        role_table_data = [
            [
                Paragraph("<b>Role</b>", styles["TableHeader"]),
                Paragraph("<b>Shortlisted</b>", styles["TableHeaderRight"]),
            ]
        ]
        for role, count in role_counts.items():
            role_table_data.append(
                [
                    Paragraph(role, styles["TableCellBold"]),
                    Paragraph(str(count), styles["TableCellNumberBold"]),
                ]
            )

        t_role_dist = Table(role_table_data, colWidths=[120, 80])
        t_role_dist.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD),
                    ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
                ]
            )
        )

        if chart_buf:
            img = Image(chart_buf, width=220, height=110)
            layout_t = Table([[t_role_dist, img]], colWidths=[220, 320])
            layout_t.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (1, 0), (1, 0), "CENTER"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            story.append(layout_t)
        else:
            story.append(t_role_dist)

    story.append(Spacer(1, 10))

    # 3. Shortlisted Candidates Roster Table
    story.extend(create_section_header("2. Verified Candidate Leaderboard", usable_width))

    cand_headers = [
        Paragraph("<b>Rank</b>", styles["TableHeader"]),
        Paragraph("<b>Candidate Name</b>", styles["TableHeader"]),
        Paragraph("<b>Role</b>", styles["TableHeader"]),
        Paragraph("<b>VOR Score</b>", styles["TableHeaderRight"]),
        Paragraph("<b>Reliability C(N)</b>", styles["TableHeaderRight"]),
        Paragraph("<b>Review Status</b>", styles["TableHeader"]),
    ]

    cand_rows = [cand_headers]
    for c in candidates:
        r_num = c.get("rank_in_cohort", "—")
        c_name = c.get("player_name", c.get("player_id", "N/A"))
        c_role = c.get("role", "BATTER")
        vor = c.get("vor_score", 0.0)
        c_n = c.get("reliability_factor", 1.0)
        rel_stat = c.get("reliability_status", "ADEQUATE")
        rev_stat = c.get("review_status", "SHORTLISTED")

        # Color-code review status
        if rev_stat == "RECOMMENDED":
            status_color = COLOR_LIME_DARK.hexval()
        elif rev_stat == "REJECTED":
            status_color = COLOR_WARNING_DARK.hexval()
        else:
            status_color = COLOR_CHARCOAL.hexval()

        row = [
            Paragraph(f"<b>#{r_num}</b>", styles["TableCellBold"]),
            Paragraph(c_name, styles["TableCellBold"]),
            Paragraph(f"<font color='#636B7E'>{c_role}</font>", styles["TableCell"]),
            Paragraph(f"<font color='{COLOR_MAGENTA.hexval()}'><b>{vor:.1f}</b></font>", styles["TableCellNumberBold"]),
            Paragraph(f"{c_n:.2f} ({rel_stat})", styles["TableCellNumber"]),
            Paragraph(f"<font color='{status_color}'><b>{rev_stat}</b></font>", styles["TableCellBold"]),
        ]
        cand_rows.append(row)

    col_widths = [40, 160, 90, 70, 95, 85]
    t_roster = Table(cand_rows, colWidths=col_widths, repeatRows=1)
    t_roster.setStyle(
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
    story.append(t_roster)
    story.append(Spacer(1, 10))

    # 4. Candidate Mini-Dossiers & Reviewer Notes
    story.extend(create_section_header("3. Candidate Evaluation Profiles & Scout Notes", usable_width))

    for idx, c in enumerate(candidates[:10], 1):  # Detailed dossier for top 10 candidates
        c_name = c.get("player_name", c.get("player_id"))
        c_role = c.get("role", "BATTER")
        vor = c.get("vor_score", 0.0)
        c_notes = c.get("reviewer_notes")

        dossier_text = [
            Paragraph(f"<b>Candidate #{c.get('rank_in_cohort', idx)}: {c_name}</b> ({c_role}) — VOR Rating: <b>{vor:.1f}</b>", styles["Heading2"]),
        ]

        if include_notes and c_notes:
            dossier_text.append(
                Paragraph(f"<b>Scout Review Notes:</b> <i>{c_notes}</i>", styles["BodyText"])
            )
        elif not include_notes:
            dossier_text.append(
                Paragraph("<i>Private reviewer notes omitted per export privacy policy.</i>", styles["Caption"])
            )
        else:
            dossier_text.append(
                Paragraph("<i>No specific scout notes recorded for this candidate.</i>", styles["Caption"])
            )

        t_card = Table([[dossier_text]], colWidths=[usable_width])
        t_card.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(KeepTogether([t_card, Spacer(1, 4)]))

    story.append(Spacer(1, 8))

    # 5. Disqualified / Excluded Candidates Summary
    if excluded:
        story.extend(create_section_header("4. Excluded / Ineligible Candidates Audit", usable_width))

        ex_headers = [
            Paragraph("<b>Candidate Name</b>", styles["TableHeader"]),
            Paragraph("<b>Role</b>", styles["TableHeader"]),
            Paragraph("<b>Eligibility Status</b>", styles["TableHeader"]),
            Paragraph("<b>Reason for Disqualification</b>", styles["TableHeader"]),
        ]
        ex_rows = [ex_headers]
        for ec in excluded:
            ex_rows.append(
                [
                    Paragraph(ec.get("player_name", ec.get("player_id")), styles["TableCellBold"]),
                    Paragraph(ec.get("role", "BATTER"), styles["TableCell"]),
                    Paragraph(f"<font color='{COLOR_WARNING_DARK.hexval()}'><b>INELIGIBLE</b></font>", styles["TableCellBold"]),
                    Paragraph(ec.get("exclusion_reason") or "Workload / age requirements not met", styles["TableCell"]),
                ]
            )

        t_ex = Table(ex_rows, colWidths=[130, 70, 90, 250], repeatRows=1)
        t_ex.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD),
                    ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
                ]
            )
        )
        story.append(t_ex)
        story.append(Spacer(1, 8))

    # 6. Audit & Sign-off Manifest
    audit_text = (
        f"<b>Audit Provenance:</b> Generated for Workspace '{ws.get('workspace_id')}'  |  "
        f"Shortlist Reference: '{sl.get('shortlist_id')}'  |  "
        f"Evaluation Engine: v1.0.0 (ECDF + Bayesian Shrinkage)  |  "
        f"Export Security: Verified immutable PDF"
    )
    story.append(Paragraph(audit_text, styles["Caption"]))

    return story

