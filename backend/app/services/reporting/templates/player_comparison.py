"""Report Template C: Player Comparison Report."""

from typing import Any
from reportlab.platypus import Flowable, Image, KeepTogether, Paragraph, Spacer, Table, TableStyle
from backend.app.services.reporting.charts import generate_comparison_bar_chart
from backend.app.services.reporting.styles import (
    COLOR_BORDER_LIGHT,
    COLOR_CARD,
    COLOR_CHARCOAL,
    COLOR_LIGHT_BG,
    COLOR_LIME_DARK,
    COLOR_MAGENTA,
    COLOR_MAGENTA_TINT,
    COLOR_WHITE,
    get_vyntiq_stylesheet,
)
from backend.app.services.reporting.templates.base import (
    create_advisory_box,
    create_header_banner,
    create_section_header,
)

styles = get_vyntiq_stylesheet()


def build_player_comparison_flowables(
    data: dict[str, Any], usable_width: float = 540.0
) -> list[Flowable]:
    """Compile structured flowables for a Head-to-Head Multi-Player Comparison Report."""
    story: list[Flowable] = []

    players = data.get("players", [])
    is_cross_role = data.get("is_cross_role", False)
    vor_valid = data.get("vor_comparison_valid", True)
    compat_status = data.get("compatibility_status", "FULLY_COMPATIBLE")
    shared_dims = data.get("shared_dimensions", [])
    batting_metrics = data.get("batting_comparison", [])
    bowling_metrics = data.get("bowling_comparison", [])
    vor_leader_id = data.get("vor_leader_id")

    player_names = [p.get("player_name", p.get("player_id")) for p in players]

    # 1. Comparison Header Banner
    subtitle = (
        f"Candidates: {', '.join(player_names)}  |  "
        f"Compatibility Grade: {compat_status}  |  "
        f"Comparison ID: {data.get('comparison_id', 'N/A')}"
    )
    story.append(
        create_header_banner(
            title=data.get("title", f"Head-to-Head Comparison — {' vs '.join(player_names[:2])}"),
            subtitle=subtitle,
            badge_label=compat_status.replace("_", " "),
            badge_color="WARNING" if is_cross_role else "LIME",
            usable_width=usable_width,
        )
    )
    story.append(Spacer(1, 8))

    # 2. Cross-Role Safeguard Box (if cross-role or invalid VOR equivalence)
    if is_cross_role or not vor_valid:
        warning_msg = (
            data.get("compatibility_notes", [""])[0]
            if data.get("compatibility_notes")
            else "Candidates belong to different role cohorts. Normalized VOR scores are not directly equivalent across disciplines; leader equivalence is suppressed."
        )
        story.append(
            create_advisory_box(
                message=warning_msg,
                title=f"Cross-Role Safeguard Enforced ({compat_status})",
                usable_width=usable_width,
            )
        )
        story.append(Spacer(1, 10))

    # 3. Candidate Overview Cards Table
    story.extend(create_section_header("1. Candidate Evaluation Ratings", usable_width))
    col_w = usable_width / len(players)
    row_headers = []
    row_sub = []

    for p in players:
        p_id = p.get("player_id", "")
        p_name = p.get("player_name", p_id)
        p_role = p.get("role", "BATTER")
        vor_score = p.get("vor_score", 0.0)
        c_n = p.get("reliability_factor", 1.0)
        rel_status = p.get("reliability_status", "ADEQUATE")

        is_leader = (p_id == vor_leader_id) and vor_valid

        leader_str = f" <font color='{COLOR_MAGENTA.hexval()}'><b>[VOR LEADER]</b></font>" if is_leader else ""
        header_p = Paragraph(f"<b>{p_name}</b>{leader_str}<br/><font color='#636B7E'>{p_role}</font>", styles["TableCellBold"])
        score_p = Paragraph(
            f"<font color='{COLOR_MAGENTA.hexval()}' size=14><b>{vor_score:.1f}</b></font> VOR Rating<br/>"
            f"<font color='#636B7E'>C(N): {c_n:.2f} ({rel_status})</font>",
            styles["TableCell"],
        )
        row_headers.append(header_p)
        row_sub.append(score_p)

    t_candidates = Table([row_headers, row_sub], colWidths=[col_w] * len(players))
    t_candidates.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER_LIGHT),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_candidates)
    story.append(Spacer(1, 10))

    # 4. Role Dimension Matrix & Grouped Bar Chart
    if shared_dims:
        story.extend(create_section_header("2. Role Dimension Matrix & Delta Analysis", usable_width))

        dim_headers = [Paragraph("<b>Dimension</b>", styles["TableHeader"])]
        for p in players:
            dim_headers.append(Paragraph(f"<b>{p.get('player_name', '')}</b>", styles["TableHeaderRight"]))
        dim_headers.append(Paragraph("<b>Score Diff</b>", styles["TableHeaderRight"]))
        dim_headers.append(Paragraph("<b>Advantage</b>", styles["TableHeaderRight"]))

        dim_rows = [dim_headers]
        for d in shared_dims:
            d_name = d.get("dimension_name", d.get("dimension_id", ""))
            scores_dict = d.get("player_dimension_scores", d.get("player_scores", {}))
            score_diff = d.get("score_difference", 0.0)
            fav_id = d.get("favorable_player_id")

            fav_name = "Tied"
            for p in players:
                if p.get("player_id") == fav_id:
                    fav_name = p.get("player_name", fav_id)
                    break

            row = [Paragraph(d_name, styles["TableCellBold"])]
            for p in players:
                val = scores_dict.get(p.get("player_id"), 0.0)
                is_fav = p.get("player_id") == fav_id
                style_name = "TableCellNumberBold" if is_fav else "TableCellNumber"
                color_tag = f"<font color='{COLOR_MAGENTA.hexval()}'>" if is_fav else ""
                end_tag = "</font>" if is_fav else ""
                row.append(Paragraph(f"{color_tag}{val:.1f}{end_tag}", styles[style_name]))

            diff_str = f"{score_diff:.1f} pts" if score_diff is not None else "—"
            row.append(Paragraph(diff_str, styles["TableCellNumber"]))
            row.append(
                Paragraph(
                    f"<font color='{COLOR_MAGENTA.hexval()}'><b>{fav_name}</b></font>",
                    styles["TableCellNumberBold"],
                )
            )
            dim_rows.append(row)

        col_w_dim = (usable_width - 150) / len(players)
        col_widths = [150] + [col_w_dim] * len(players) + [50, 70]
        # adjust total width
        scale = usable_width / sum(col_widths)
        adjusted_widths = [w * scale for w in col_widths]

        t_dim_matrix = Table(dim_rows, colWidths=adjusted_widths, repeatRows=1)
        t_dim_matrix.setStyle(
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
        story.append(t_dim_matrix)
        story.append(Spacer(1, 8))

        # Comparison Bar Chart
        chart_buf = generate_comparison_bar_chart(shared_dims, players, width_in=5.8, height_in=2.0)
        if chart_buf:
            story.append(Image(chart_buf, width=usable_width, height=135))
            story.append(Spacer(1, 8))

    # 5. Discipline Metric Comparisons (Batting & Bowling)
    for section_title, metric_list in [
        ("3. Batting Performance Metrics", batting_metrics),
        ("4. Bowling Performance Metrics", bowling_metrics),
    ]:
        if not metric_list:
            continue

        story.extend(create_section_header(section_title, usable_width))

        m_headers = [
            Paragraph("<b>Metric</b>", styles["TableHeader"]),
            Paragraph("<b>Polarity</b>", styles["TableHeader"]),
        ]
        for p in players:
            m_headers.append(Paragraph(f"<b>{p.get('player_name', '')}</b>", styles["TableHeaderRight"]))
        m_headers.append(Paragraph("<b>Delta</b>", styles["TableHeaderRight"]))
        m_headers.append(Paragraph("<b>Advantage</b>", styles["TableHeaderRight"]))

        m_rows = [m_headers]
        for m in metric_list:
            m_name = m.get("display_name", m.get("metric_id", ""))
            unit = f" ({m.get('unit')})" if m.get("unit") else ""
            polarity = m.get("directionality", "HIGHER_IS_BETTER")
            polarity_str = "Higher is better" if polarity == "HIGHER_IS_BETTER" else "Lower is better"
            p_values = m.get("player_values", {})
            abs_diff = m.get("absolute_difference")
            fav_name = m.get("favorable_player_name") or "Tied"
            fav_id = m.get("favorable_player_id")

            row = [
                Paragraph(f"{m_name}{unit}", styles["TableCellBold"]),
                Paragraph(f"<font color='#636B7E'>{polarity_str}</font>", styles["Caption"]),
            ]
            for p in players:
                val = p_values.get(p.get("player_id"))
                val_str = f"{float(val):.2f}" if val is not None else "—"
                is_fav = p.get("player_id") == fav_id
                style_name = "TableCellNumberBold" if is_fav else "TableCellNumber"
                color_tag = f"<font color='{COLOR_LIME_DARK.hexval()}'>" if is_fav else ""
                end_tag = "</font>" if is_fav else ""
                row.append(Paragraph(f"{color_tag}{val_str}{end_tag}", styles[style_name]))

            diff_str = f"{float(abs_diff):.2f}" if abs_diff is not None else "—"
            row.append(Paragraph(diff_str, styles["TableCellNumber"]))
            row.append(
                Paragraph(
                    f"<font color='{COLOR_LIME_DARK.hexval()}'><b>{fav_name}</b></font>",
                    styles["TableCellNumberBold"],
                )
            )
            m_rows.append(row)

        m_col_w = (usable_width - 180) / len(players)
        m_col_widths = [120, 60] + [m_col_w] * len(players) + [45, 65]
        m_scale = usable_width / sum(m_col_widths)
        adj_m_widths = [w * m_scale for w in m_col_widths]

        t_metrics = Table(m_rows, colWidths=adj_m_widths, repeatRows=1)
        t_metrics.setStyle(
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
        story.append(t_metrics)
        story.append(Spacer(1, 10))

    return story

