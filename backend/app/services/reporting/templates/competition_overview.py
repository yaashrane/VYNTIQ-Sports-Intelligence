"""Report Template A: Competition Overview Report."""

from typing import Any
from reportlab.platypus import Flowable, Image, Paragraph, Spacer, Table, TableStyle
from backend.app.services.reporting.charts import generate_shortlist_composition_chart
from backend.app.services.reporting.styles import (
    COLOR_BORDER_LIGHT,
    COLOR_CARD,
    COLOR_LIGHT_BG,
    COLOR_MAGENTA,
    COLOR_WHITE,
    get_vyntiq_stylesheet,
)
from backend.app.services.reporting.templates.base import (
    create_header_banner,
    create_key_value_grid,
    create_section_header,
)

styles = get_vyntiq_stylesheet()


def build_competition_overview_flowables(
    data: dict[str, Any], usable_width: float = 540.0
) -> list[Flowable]:
    """Compile structured flowables for the Competition Overview Report."""
    story: list[Flowable] = []

    ws = data.get("workspace", {})
    cfg = data.get("configuration", {})
    ds = data.get("dataset")
    sl = data.get("active_shortlist")

    # 1. Executive Header Banner
    subtitle = (
        f"Competition: {ws.get('competition_name', 'N/A')} ({ws.get('season_or_edition', 'N/A')})  |  "
        f"Workspace ID: {ws.get('workspace_id', 'N/A')}  |  Methodology: {data.get('methodology_version', 'v1.0.0')}"
    )
    story.append(
        create_header_banner(
            title=data.get("title", "Competition Overview Report"),
            subtitle=subtitle,
            badge_label=ws.get("status", "ACTIVE"),
            badge_color="LIME" if ws.get("status") == "ACTIVE" else "MAGENTA",
            usable_width=usable_width,
        )
    )
    story.append(Spacer(1, 10))

    # 2. Executive Summary Paragraph
    desc = ws.get("description") or "Analytical competition sandbox for candidate scouting and shortlist generation."
    story.append(Paragraph(desc, styles["BodyText"]))
    story.append(Spacer(1, 8))

    # 3. Workspace & Dataset Profile
    story.extend(create_section_header("1. Workspace & Dataset Intelligence", usable_width))
    ws_items = [
        ("Sport Type", ws.get("sport_type", "CRICKET")),
        ("Competition", ws.get("competition_name", "N/A")),
        ("Season / Edition", ws.get("season_or_edition", "N/A")),
        ("Status", ws.get("status", "ACTIVE")),
    ]
    story.append(create_key_value_grid(ws_items, usable_width=usable_width, col_count=4))
    story.append(Spacer(1, 6))

    if ds:
        ds_items = [
            ("Dataset ID", ds.get("dataset_id", "N/A")),
            ("File Format", str(ds.get("format", "CSV")).upper()),
            ("Total Deliveries", f"{ds.get('total_deliveries', 0):,}"),
            ("Total Matches", f"{ds.get('total_matches', 0):,}"),
        ]
        story.append(create_key_value_grid(ds_items, usable_width=usable_width, col_count=4))
    else:
        story.append(
            Paragraph("<i>No canonical dataset ingested into this workspace context yet.</i>", styles["Caption"])
        )
    story.append(Spacer(1, 12))

    # 4. Eligibility & Evaluation Parameters
    story.extend(create_section_header("2. Competition Eligibility Configuration", usable_width))
    target_roles_str = ", ".join(cfg.get("target_roles", [])) or "All Disciplines"
    age_str = (
        f"{cfg.get('min_age', 0)} to {cfg.get('max_age', 'No Max')} yrs"
        if cfg.get("max_age")
        else "No Restrictions"
    )
    eligibility_items = [
        ("Target Roles", target_roles_str),
        ("Age Range", age_str),
        ("Min Balls Faced", str(cfg.get("min_balls_faced", 120))),
        ("Min Balls Bowled", str(cfg.get("min_balls_bowled", 120))),
    ]
    story.append(create_key_value_grid(eligibility_items, usable_width=usable_width, col_count=4))
    story.append(Spacer(1, 12))

    # 5. Candidate Pool Breakdown & Shortlist Overview
    story.extend(create_section_header("3. Candidate Pool & Shortlist Overview", usable_width))

    pool_items = [
        ("Total Qualified Athletes", str(data.get("total_ranked", 0))),
        ("Sample Quarantined", str(data.get("total_quarantined", 0))),
        ("Active Shortlist", sl.get("name", "None") if sl else "None"),
        ("Target Squad Size", str(sl.get("target_size", "N/A")) if sl else "N/A"),
    ]
    story.append(create_key_value_grid(pool_items, usable_width=usable_width, col_count=4))
    story.append(Spacer(1, 10))

    # Role breakdown chart and table side by side
    role_counts = data.get("role_breakdown", {})
    if role_counts:
        chart_buf = generate_shortlist_composition_chart(role_counts, width_in=3.0, height_in=1.6)
        table_data = [
            [
                Paragraph("<b>Role Discipline</b>", styles["TableHeader"]),
                Paragraph("<b>Qualified Candidates</b>", styles["TableHeaderRight"]),
            ]
        ]
        for role, count in role_counts.items():
            table_data.append(
                [
                    Paragraph(role, styles["TableCellBold"]),
                    Paragraph(str(count), styles["TableCellNumberBold"]),
                ]
            )

        t_roles = Table(table_data, colWidths=[140, 90])
        t_roles.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD),
                    ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
                ]
            )
        )

        if chart_buf:
            img = Image(chart_buf, width=220, height=120)
            comp_table = Table([[t_roles, img]], colWidths=[240, 300])
            comp_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (1, 0), (1, 0), "CENTER"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            story.append(comp_table)
        else:
            story.append(t_roles)

    story.append(Spacer(1, 12))

    # 6. Evaluation Methodology & Technical Limitations
    story.extend(create_section_header("4. Scoring Methodology & Known Limitations", usable_width))
    methodology_text = (
        "<b>Deterministic Framework:</b> Every rating is calculated via multi-stage Empirical Cumulative "
        "Distribution Function (ECDF) percentile normalization, benchmarked strictly against peer role cohorts. "
        "Athletes with limited match samples are mathematically penalized using Bayesian reliability shrinkage: "
        "<i>C(N) = N / (N + K)</i>, ensuring high-variance outliers do not artificially top the leaderboard.<br/><br/>"
        "<b>Known Limitations:</b> Match phases (Powerplay, Middle, Death) are segmented by over numbers; "
        "ball-tracking telemetry (pitch maps, release speed) is omitted when not provided by tournament data feeds. "
        "True Strike Rates and True Economy Rates represent phase-baselined adjustments without full venue pitch degradation modeling."
    )
    story.append(Paragraph(methodology_text, styles["BodyText"]))

    return story
