"""Report template modules for VYNTIQ PDF reporting engine."""

from backend.app.services.reporting.templates.competition_overview import (
    build_competition_overview_flowables,
)
from backend.app.services.reporting.templates.individual_player import (
    build_individual_player_flowables,
)
from backend.app.services.reporting.templates.player_comparison import (
    build_player_comparison_flowables,
)
from backend.app.services.reporting.templates.shortlist import (
    build_shortlist_flowables,
)

__all__ = [
    "build_competition_overview_flowables",
    "build_individual_player_flowables",
    "build_player_comparison_flowables",
    "build_shortlist_flowables",
]
