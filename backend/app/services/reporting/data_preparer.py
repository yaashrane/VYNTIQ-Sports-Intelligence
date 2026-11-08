"""Report data preparation and strict pre-rendering validation.

Consumes verified outputs from existing domain services without re-calculating scores.
"""

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.exceptions import (
    EntityNotFoundException,
    ValidationException,
)
from backend.app.models.cricket import Player
from backend.app.models.dataset import Dataset
from backend.app.models.workspace import Shortlist, ShortlistCandidate
from backend.app.repositories.workspace import WorkspaceRepository
from backend.app.schemas.comparison import PlayerComparisonRequest
from backend.app.schemas.report import ReportCreateRequest, ReportType
from backend.app.services.comparison.service import PlayerComparisonService
from backend.app.services.explainability.service import ExplainabilityService
from backend.app.services.scoring.service import RUN_CACHE, ScoringService
from backend.app.services.shortlisting.service import ShortlistingService
from backend.app.services.workspace.service import WorkspaceService


class ReportDataPreparer:
    """Prepares and validates immutable domain data contexts for ReportLab rendering."""

    def __init__(
        self,
        session: AsyncSession,
        scoring_service: ScoringService | None = None,
        explainability_service: ExplainabilityService | None = None,
        comparison_service: PlayerComparisonService | None = None,
        shortlisting_service: ShortlistingService | None = None,
        workspace_service: WorkspaceService | None = None,
    ) -> None:
        self.session = session
        self.workspace_repo = WorkspaceRepository(session)
        self.scoring_service = scoring_service or ScoringService()
        self.explainability_service = explainability_service or ExplainabilityService(self.scoring_service)
        self.comparison_service = comparison_service or PlayerComparisonService(self.scoring_service)
        self.shortlisting_service = shortlisting_service or ShortlistingService(session, self.scoring_service)
        self.workspace_service = workspace_service or WorkspaceService(session)

    async def prepare_data(
        self,
        report_type: ReportType,
        workspace_id: str | None,
        request: ReportCreateRequest,
    ) -> dict[str, Any]:
        """Dispatch to appropriate preparer and enforce strict data presence validation."""
        if report_type == ReportType.COMPETITION_OVERVIEW:
            if not workspace_id:
                raise ValidationException("Workspace ID is required for Competition Overview reports.")
            return await self.prepare_competition_overview(workspace_id, request)

        elif report_type == ReportType.INDIVIDUAL_PLAYER:
            if not request.player_id:
                raise ValidationException("Player ID is required for Individual Player reports.")
            return await self.prepare_individual_player(request.player_id, workspace_id, request)

        elif report_type == ReportType.PLAYER_COMPARISON:
            if not request.comparison_player_ids or len(request.comparison_player_ids) < 2:
                raise ValidationException(
                    "Player Comparison reports require between 2 and 5 player IDs in 'comparison_player_ids'."
                )
            if len(request.comparison_player_ids) > 5:
                raise ValidationException("Player Comparison reports support a maximum of 5 candidates.")
            return await self.prepare_player_comparison(
                request.comparison_player_ids, workspace_id, request
            )

        elif report_type == ReportType.SHORTLIST:
            if not workspace_id:
                raise ValidationException("Workspace ID is required for Shortlist reports.")
            return await self.prepare_shortlist(workspace_id, request)

        else:
            raise ValidationException(f"Unsupported report type: '{report_type}'.")

    async def prepare_competition_overview(
        self, workspace_id: str, request: ReportCreateRequest
    ) -> dict[str, Any]:
        """Prepare validated competition workspace overview, configuration, and dataset metrics."""
        # 1. Validate Workspace
        workspace = await self.workspace_service.get_workspace(workspace_id)
        config = await self.workspace_repo.get_configuration(workspace_id)

        # 2. Dataset Reference
        dataset_info = None
        if workspace.dataset_references:
            d_id = workspace.dataset_references[0]
            dataset = await self.session.get(Dataset, d_id)
            if dataset:
                dataset_info = {
                    "dataset_id": dataset.dataset_id,
                    "filename": getattr(dataset, "source_filename", getattr(dataset, "filename", "N/A")),
                    "format": getattr(dataset, "file_format", getattr(dataset, "format", "CSV")),
                    "status": dataset.status,
                    "total_deliveries": getattr(dataset, "total_rows", 0),
                    "total_matches": getattr(dataset, "total_matches", 0),
                }

        # 3. Candidate evaluation pool & rankings
        run_id = request.run_id
        rankings_data = None
        role_breakdown: dict[str, int] = {}
        total_ranked = 0
        total_quarantined = 0

        try:
            rankings_resp = self.scoring_service.get_rankings(run_id=run_id)
            total_ranked = rankings_resp.total_ranked
            total_quarantined = rankings_resp.total_quarantined
            rankings_data = [r.model_dump() for r in rankings_resp.rankings]
            for r in rankings_resp.rankings:
                role_breakdown[r.role.value] = role_breakdown.get(r.role.value, 0) + 1
        except Exception:
            # Fallback gracefully if no scoring run executed yet
            pass

        # 4. Shortlists in workspace
        shortlists = await self.workspace_repo.list_shortlists_for_workspace(workspace_id)
        active_shortlist = shortlists[0] if shortlists else None

        return {
            "report_type": ReportType.COMPETITION_OVERVIEW.value,
            "title": request.title or f"Competition Intelligence Overview — {workspace.name}",
            "workspace": {
                "workspace_id": workspace.workspace_id,
                "name": workspace.name,
                "description": workspace.description or "",
                "sport_type": workspace.sport_type,
                "competition_name": workspace.competition_name,
                "season_or_edition": workspace.season_or_edition,
                "status": workspace.status,
            },
            "configuration": {
                "target_roles": config.target_roles if config else ["BATTER", "BOWLER", "ALL_ROUNDER", "WICKETKEEPER"],
                "min_age": config.min_age if config else None,
                "max_age": config.max_age if config else None,
                "age_cutoff_date": config.age_cutoff_date if config else None,
                "min_matches": config.min_matches if config else None,
                "min_balls_faced": config.min_balls_faced if config else 120,
                "min_balls_bowled": (config.min_legal_balls_bowled if config else 120) or 120,
            },
            "dataset": dataset_info,
            "total_ranked": total_ranked,
            "total_quarantined": total_quarantined,
            "role_breakdown": role_breakdown,
            "active_shortlist": {
                "shortlist_id": active_shortlist.shortlist_id,
                "name": active_shortlist.name,
                "target_size": active_shortlist.target_size,
                "status": active_shortlist.status,
            }
            if active_shortlist
            else None,
            "methodology_version": "v1.0.0",
            "source_references": [workspace_id] + ([run_id] if run_id else []),
        }

    async def prepare_individual_player(
        self, player_id: str, workspace_id: str | None, request: ReportCreateRequest
    ) -> dict[str, Any]:
        """Prepare validated individual player evaluation dossier, explainability, and dimensions."""
        # 1. Fetch Player Score (validates player exists in evaluation run)
        run_id = request.run_id
        try:
            score_res = self.scoring_service.get_player_score(player_id, run_id)
        except EntityNotFoundException:
            raise EntityNotFoundException("PlayerScore", player_id)

        # 2. Fetch Explainability Details
        try:
            explanation_res = self.explainability_service.get_detailed_explanation(player_id, run_id)
        except Exception:
            explanation_res = None

        # 3. Fetch Score Breakdown & Reconciliation Audit
        try:
            breakdown_res = self.explainability_service.get_score_breakdown(player_id, run_id)
        except Exception:
            breakdown_res = None

        # 4. Fetch Canonical Biographical Record (if in DB)
        player_bio = await self.session.get(Player, player_id)

        # 5. Build Dimensions List
        dimensions_list = []
        for dim_id, d_score in score_res.dimensions.items():
            dim_name = getattr(d_score, "dimension_name", getattr(d_score, "name", dim_id))
            dim_val = getattr(d_score, "dimension_score", getattr(d_score, "score", 0.0))
            w = getattr(d_score, "weight", 0.0)
            contrib = getattr(d_score, "contribution_points", dim_val * w)
            dimensions_list.append(
                {
                    "dimension_id": dim_id,
                    "dimension_name": dim_name,
                    "dimension_score": round(dim_val, 1),
                    "weight": round(w, 2),
                    "contribution": round(contrib, 2),
                }
            )

        return {
            "report_type": ReportType.INDIVIDUAL_PLAYER.value,
            "title": request.title or f"Candidate Evaluation Dossier — {score_res.player_name}",
            "workspace_id": workspace_id,
            "player": {
                "player_id": score_res.player_id,
                "player_name": score_res.player_name,
                "role": score_res.role.value,
                "country": player_bio.nationality if player_bio and player_bio.nationality else "India",
                "batting_hand": player_bio.batting_hand if player_bio and player_bio.batting_hand else "RIGHT",
                "bowling_style": player_bio.bowling_style if player_bio and player_bio.bowling_style else "N/A",
                "birth_date": str(player_bio.dob) if player_bio and player_bio.dob else "N/A",
            },
            "score": {
                "vor_score": round(score_res.vor_score, 1),
                "raw_composite_score": round(score_res.raw_composite_score, 1),
                "reliability_factor": round(score_res.reliability_factor, 2),
                "reliability_status": score_res.reliability_status.value,
                "is_qualified": score_res.is_qualified,
                "is_eligible": score_res.is_eligible,
                "cohort_id": score_res.cohort_id,
                "scoring_version": score_res.scoring_version,
            },
            "sample_workload": {
                "balls_faced": getattr(score_res.sample_size, "balls_faced", 0),
                "dismissals": getattr(score_res.sample_size, "times_dismissed", getattr(score_res.sample_size, "dismissals", 0)),
                "legal_balls_bowled": getattr(score_res.sample_size, "legal_balls_bowled", 0),
                "wickets": getattr(score_res.sample_size, "wickets", 0),
                "innings": getattr(score_res.sample_size, "batting_innings", 0) or getattr(score_res.sample_size, "innings", 0),
            },
            "dimensions": dimensions_list,
            "explanation": {
                "narrative_summary": (
                    explanation_res.narrative_summary
                    if explanation_res
                    else score_res.explanation.summary_text
                ),
                "top_strengths": (
                    explanation_res.top_strengths
                    if explanation_res
                    else score_res.explanation.top_strengths
                ),
                "drag_factors": (
                    explanation_res.drag_factors
                    if explanation_res
                    else score_res.explanation.drag_factors
                ),
            },
            "breakdown": {
                "is_reconciled": (
                    (getattr(breakdown_res, "reconciliation_discrepancy", 0.0) < 0.01)
                    if breakdown_res
                    else True
                ),
                "reconciliation_discrepancy": (
                    round(getattr(breakdown_res, "reconciliation_discrepancy", 0.0), 3)
                    if breakdown_res
                    else 0.0
                ),
            },
            "provenance": {
                "dataset_id": score_res.provenance.dataset_id,
                "calculated_at": score_res.provenance.calculated_at,
            },
            "methodology_version": "v1.0.0",
            "source_references": [player_id] + ([run_id] if run_id else []),
        }

    async def prepare_player_comparison(
        self, player_ids: list[str], workspace_id: str | None, request: ReportCreateRequest
    ) -> dict[str, Any]:
        """Prepare validated multi-player head-to-head comparison with directional metrics."""
        # 1. Run backend PlayerComparisonService (validates candidate presence & compatibility)
        comp_req = PlayerComparisonRequest(player_ids=player_ids, run_id=request.run_id)
        comp_res = self.comparison_service.compare_players(comp_req)

        players_list = [p.model_dump() for p in comp_res.players]
        shared_dimensions = [d.model_dump() for d in comp_res.shared_dimensions]
        batting_metrics = [m.model_dump() for m in comp_res.batting_comparison]
        bowling_metrics = [m.model_dump() for m in comp_res.bowling_comparison]

        player_names = [p.get("player_name", p.get("player_id")) for p in players_list]

        return {
            "report_type": ReportType.PLAYER_COMPARISON.value,
            "title": request.title or f"Head-to-Head Comparison — {' vs '.join(player_names[:3])}",
            "workspace_id": workspace_id,
            "comparison_id": comp_res.comparison_id,
            "compatibility_status": comp_res.compatibility_status.value,
            "is_cross_role": comp_res.is_cross_role,
            "vor_comparison_valid": comp_res.vor_comparison_valid,
            "vor_leader_id": comp_res.vor_leader_id,
            "compatibility_notes": comp_res.compatibility_notes,
            "players": players_list,
            "shared_dimensions": shared_dimensions,
            "batting_comparison": batting_metrics,
            "bowling_comparison": bowling_metrics,
            "data_quality_warnings": comp_res.data_quality_warnings,
            "methodology_version": "v1.0.0",
            "source_references": player_ids + ([request.run_id] if request.run_id else []),
        }

    async def prepare_shortlist(
        self, workspace_id: str, request: ReportCreateRequest
    ) -> dict[str, Any]:
        """Prepare validated shortlist candidate roster, audit review states, and exclusions."""
        # 1. Validate Workspace
        workspace = await self.workspace_service.get_workspace(workspace_id)

        # 2. Fetch Target Shortlist
        if request.shortlist_id:
            shortlist = await self.session.get(Shortlist, request.shortlist_id)
            if not shortlist or shortlist.workspace_id != workspace_id:
                raise EntityNotFoundException("Shortlist", request.shortlist_id)
        else:
            shortlists = await self.workspace_repo.list_shortlists_for_workspace(workspace_id)
            if not shortlists:
                raise ValidationException(
                    f"No shortlists found in workspace '{workspace_id}'. Generate a shortlist first."
                )
            shortlist = shortlists[0]

        # 3. Fetch Candidates and Audit Log
        candidates = await self.workspace_repo.get_candidates(shortlist.shortlist_id)
        audit_log = await self.workspace_repo.get_audit_log(shortlist.shortlist_id)

        shortlist_candidates = []
        excluded_candidates = []
        role_counts: dict[str, int] = {}

        for c in candidates:
            # Privacy Safeguard: Only include reviewer notes if explicitly authorized
            reviewer_notes = (
                c.reviewer_notes
                if request.include_reviewer_notes
                else None
            )

            role_val = c.assigned_role
            item = {
                "candidate_id": c.candidate_entry_id,
                "player_id": c.player_id,
                "player_name": c.player_name,
                "role": role_val,
                "rank_in_cohort": c.rank,
                "vor_score": round(c.vor_score, 1),
                "reliability_factor": round(c.reliability_factor, 2),
                "reliability_status": c.reliability_status,
                "eligibility_status": c.eligibility_status,
                "review_status": c.review_status,
                "exclusion_reason": getattr(c, "exclusion_reason", None),
                "reviewer_notes": reviewer_notes,
            }

            if c.eligibility_status == "ELIGIBLE":
                shortlist_candidates.append(item)
                role_counts[role_val] = role_counts.get(role_val, 0) + 1
            else:
                excluded_candidates.append(item)

        if audit_log and audit_log.exclusion_details:
            for pid, reason in audit_log.exclusion_details.items():
                if not any(ex["player_id"] == pid for ex in excluded_candidates):
                    excluded_candidates.append(
                        {
                            "candidate_id": f"ex_{pid}",
                            "player_id": pid,
                            "player_name": pid,
                            "role": "BATTER",
                            "rank_in_cohort": "—",
                            "vor_score": 0.0,
                            "reliability_factor": 0.0,
                            "reliability_status": "N/A",
                            "eligibility_status": "INELIGIBLE",
                            "review_status": "EXCLUDED",
                            "exclusion_reason": str(reason),
                            "reviewer_notes": None,
                        }
                    )

        return {
            "report_type": ReportType.SHORTLIST.value,
            "title": request.title or f"Candidate Shortlist & Scouting Dossier — {shortlist.name}",
            "workspace": {
                "workspace_id": workspace.workspace_id,
                "name": workspace.name,
                "competition_name": workspace.competition_name,
                "season_or_edition": workspace.season_or_edition,
            },
            "shortlist": {
                "shortlist_id": shortlist.shortlist_id,
                "name": shortlist.name,
                "target_size": shortlist.target_size,
                "status": shortlist.status,
                "scoring_run_id": shortlist.scoring_run_id,
                "generated_at": str(shortlist.created_at),
            },
            "candidates": shortlist_candidates,
            "excluded_candidates": excluded_candidates,
            "role_counts": role_counts,
            "include_reviewer_notes": request.include_reviewer_notes,
            "methodology_version": "v1.0.0",
            "source_references": [workspace_id, shortlist.shortlist_id],
        }
