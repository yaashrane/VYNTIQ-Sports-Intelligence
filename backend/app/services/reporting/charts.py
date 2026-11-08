"""Headless chart generation for VYNTIQ PDF reports.

Produces high-resolution, vector/PNG visualizations using the VYNTIQ editorial design palette.
Always executes in headless Agg mode without GUI dependencies or memory leaks.
"""

import io
from typing import Any
import matplotlib

matplotlib.use("Agg")  # Enforce headless rendering
import matplotlib.pyplot as plt
import numpy as np

# Brand Colors (DESIGN_SYSTEM.md)
COLOR_MAGENTA = "#D62978"
COLOR_LIME = "#B9D66C"
COLOR_CHARCOAL = "#111318"
COLOR_MUTED = "#636B7E"
COLOR_BORDER = "#D8D4CC"
COLOR_LIGHT_FILL = "#F8F7F4"
CANDIDATE_PALETTE = ["#D62978", "#4E7019", "#006699", "#E5A83B", "#7B3F00"]


def generate_player_radar_chart(
    dimensions: list[dict[str, Any]],
    player_name: str,
    width_in: float = 3.6,
    height_in: float = 2.8,
) -> io.BytesIO | None:
    """Generate a high-precision polar radar chart for player performance dimensions."""
    if not dimensions or len(dimensions) < 3:
        return None

    labels = [d.get("dimension_name", d.get("name", d.get("dimension_id", ""))) for d in dimensions]
    raw_scores = [float(d.get("dimension_score", d.get("score", 0.0))) for d in dimensions]

    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    # Complete the circular loop
    scores = raw_scores + raw_scores[:1]
    plot_angles = angles + angles[:1]

    fig, ax = plt.subplots(figsize=(width_in, height_in), subplot_kw=dict(polar=True))
    try:
        # Concentric Percentile Grid (25, 50, 75, 100)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(["25", "50", "75", "100"], size=5.5, color=COLOR_MUTED, fontfamily="sans-serif")
        ax.set_rlabel_position(45)

        ax.set_xticks(angles)
        ax.set_xticklabels(labels, size=6.5, color=COLOR_CHARCOAL, weight="bold", fontfamily="sans-serif")

        # Grid lines styling
        ax.grid(color=COLOR_BORDER, linestyle="--", linewidth=0.5, alpha=0.8)
        ax.spines["polar"].set_color(COLOR_BORDER)
        ax.spines["polar"].set_linewidth(0.8)

        # Polygon Plot
        ax.plot(plot_angles, scores, color=COLOR_MAGENTA, linewidth=1.6, solid_capstyle="round")
        ax.fill(plot_angles, scores, color=COLOR_MAGENTA, alpha=0.18)

        # Vertex Dots
        ax.scatter(angles, raw_scores, color=COLOR_LIME, s=20, zorder=5, edgecolors=COLOR_CHARCOAL, linewidth=0.5)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=250, bbox_inches="tight", transparent=False, facecolor="#FFFFFF")
        buf.seek(0)
        return buf
    finally:
        plt.close(fig)


def generate_comparison_bar_chart(
    dimensions: list[dict[str, Any]],
    players: list[dict[str, Any]],
    width_in: float = 6.2,
    height_in: float = 2.4,
) -> io.BytesIO | None:
    """Generate a grouped horizontal bar chart comparing 2 to 5 candidates across dimensions."""
    if not dimensions or not players:
        return None

    dim_names = [d.get("dimension_name", d.get("dimension_id", "")) for d in dimensions]
    num_dims = len(dim_names)
    num_players = len(players)
    if num_dims == 0 or num_players < 2:
        return None

    fig, ax = plt.subplots(figsize=(width_in, height_in))
    try:
        y_indices = np.arange(num_dims)
        bar_height = min(0.35, 0.75 / num_players)

        for p_idx, player in enumerate(players):
            p_id = player.get("player_id", "")
            p_name = player.get("player_name", p_id)
            scores = []
            for d in dimensions:
                p_scores = d.get("player_dimension_scores", d.get("player_scores", {}))
                scores.append(float(p_scores.get(p_id, 0.0)))

            offset = (p_idx - (num_players - 1) / 2) * bar_height
            color = CANDIDATE_PALETTE[p_idx % len(CANDIDATE_PALETTE)]

            ax.barh(
                y_indices + offset,
                scores,
                height=bar_height * 0.9,
                label=p_name,
                color=color,
                edgecolor=COLOR_CHARCOAL,
                linewidth=0.4,
                alpha=0.9,
            )

        ax.set_yticks(y_indices)
        ax.set_yticklabels(dim_names, size=7, color=COLOR_CHARCOAL, weight="bold", fontfamily="sans-serif")
        ax.set_xlim(0, 105)
        ax.set_xlabel("Normalized Percentile Score (0–100)", size=7, color=COLOR_MUTED, fontfamily="sans-serif")
        ax.xaxis.grid(True, linestyle=":", color=COLOR_BORDER, alpha=0.7)
        ax.set_axisbelow(True)

        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        for spine in ["left", "bottom"]:
            ax.spines[spine].set_color(COLOR_BORDER)
            ax.spines[spine].set_linewidth(0.6)

        ax.tick_params(axis="both", labelsize=6.5)
        ax.legend(
            loc="upper right",
            bbox_to_anchor=(1.0, 1.15),
            ncol=num_players,
            frameon=False,
            fontsize=6.5,
        )

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=250, bbox_inches="tight", transparent=False, facecolor="#FFFFFF")
        buf.seek(0)
        return buf
    finally:
        plt.close(fig)


def generate_shortlist_composition_chart(
    role_counts: dict[str, int],
    width_in: float = 3.2,
    height_in: float = 2.0,
) -> io.BytesIO | None:
    """Generate a clean horizontal bar chart of shortlisted talent by role."""
    if not role_counts or sum(role_counts.values()) == 0:
        return None

    roles = list(role_counts.keys())
    counts = [role_counts[r] for r in roles]

    fig, ax = plt.subplots(figsize=(width_in, height_in))
    try:
        y_pos = np.arange(len(roles))
        ax.barh(
            y_pos,
            counts,
            color=COLOR_MAGENTA,
            edgecolor=COLOR_CHARCOAL,
            linewidth=0.5,
            height=0.55,
            alpha=0.88,
        )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(roles, size=7, color=COLOR_CHARCOAL, weight="bold", fontfamily="sans-serif")
        max_c = max(counts) if counts else 5
        ax.set_xlim(0, max_c + 1)
        ax.xaxis.grid(True, linestyle=":", color=COLOR_BORDER, alpha=0.7)
        ax.set_axisbelow(True)

        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        for spine in ["left", "bottom"]:
            ax.spines[spine].set_color(COLOR_BORDER)
            ax.spines[spine].set_linewidth(0.6)

        ax.tick_params(axis="both", labelsize=6.5)
        ax.set_xlabel("Shortlisted Candidates", size=7, color=COLOR_MUTED, fontfamily="sans-serif")

        # Value annotations on bar ends
        for i, v in enumerate(counts):
            ax.text(v + 0.1, i, str(v), va="center", size=6.5, weight="bold", color=COLOR_CHARCOAL)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=250, bbox_inches="tight", transparent=False, facecolor="#FFFFFF")
        buf.seek(0)
        return buf
    finally:
        plt.close(fig)
