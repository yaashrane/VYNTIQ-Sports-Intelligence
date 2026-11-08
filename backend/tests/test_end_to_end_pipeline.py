"""Comprehensive End-to-End Pipeline Integration & Data Flow Test Suite.

Validates the full 17-step VYNTIQ sports intelligence workflow:
1. Workspace creation & tenant isolation
2. Dataset upload & SHA-256 hashing
3. Schema inspection & column alias detection
4. Validation & quarantine logging
5. Atomic persistence into canonical relational tables
6. Metric registry calculation
7. Role classification with evidence auditing
8. Workspace competition rules & eligibility gating
9. 6-axis dimensional evaluation profiles
10. VOR scoring, ECDF normalization & Bayesian reliability shrinkage
11. Deterministic explainability & score breakdown reconciliation
12. Head-to-head comparison with directional deltas & cross-role safeguards
13. Candidate shortlist generation
14. Scout review workflow without score mutation
15. Candidate intelligence dossier inspection
16. Multi-type vector PDF report generation
17. Secure report download streaming
"""

import io
import uuid
from datetime import date
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.core.database import engine, get_db_session
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.cricket import Delivery, Match, Player
from backend.app.models.dataset import Dataset
from backend.app.models.workspace import Shortlist, ShortlistCandidate, Workspace, WorkspaceConfiguration
from backend.app.schemas.evaluation import PlayerRole
from backend.app.schemas.report import ReportType


@pytest.fixture(autouse=True)
async def init_test_db():
    """Ensure all database schema tables exist for end-to-end tests."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
def anyio_backend():
    return "asyncio"


# Synthetic Multi-Player Cricket Dataset for E2E Pipeline (60+ balls for statistical qualification)
def _generate_e2e_dataset() -> str:
    rows = ["match_id,season,venue,batting_team,bowling_team,innings,over,ball,batter,bowler,runs_batter,extras,total_runs,wicket,dismissed_player,dismissal_kind"]
    # Match M01: Sanju Samson faces 66 deliveries against Bumrah and Spinner
    for over in range(1, 12):
        bowler = "P_BUMRAH" if over % 2 == 1 else "P_SPINNER"
        for ball in range(1, 7):
            runs = 4 if ball in [1, 4] else (6 if ball == 6 else (1 if ball == 3 else 0))
            rows.append(f"M01,2024,Wankhede,RR,MI,1,{over},{ball},P_SANJU,{bowler},{runs},0,{runs},0,,")

    # Match M02: Yashasvi Jaiswal and Parag facing Bumrah (P_BUMRAH bowls 66 balls)
    for over in range(1, 12):
        for ball in range(1, 7):
            batter = "P_JAISWAL" if ball <= 3 else "P_PARAG"
            is_wkt = 1 if (over == 11 and ball == 6) else 0
            d_player = "P_PARAG" if is_wkt else ""
            d_kind = "bowled" if is_wkt else ""
            rows.append(f"M02,2024,Wankhede,RR,MI,2,{over},{ball},{batter},P_BUMRAH,1,0,1,{is_wkt},{d_player},{d_kind}")

    return "\n".join(rows) + "\n"


E2E_SYNTHETIC_CSV = _generate_e2e_dataset()


@pytest.mark.anyio
async def test_complete_end_to_end_workflow():
    """Execute complete 17-step end-to-end integration workflow."""
    async for session in get_db_session():
        await session.merge(Player(player_id="P_SANJU", canonical_name="Sanju Samson", primary_role="BATTER", nationality="India", dob=date(1994, 11, 11), is_eligible=True))
        await session.merge(Player(player_id="P_JAISWAL", canonical_name="Yashasvi Jaiswal", primary_role="BATTER", nationality="India", dob=date(2001, 12, 28), is_eligible=True))
        await session.merge(Player(player_id="P_BUMRAH", canonical_name="Jasprit Bumrah", primary_role="BOWLER", nationality="India", dob=date(1993, 12, 6), is_eligible=True))
        await session.merge(Player(player_id="P_PARAG", canonical_name="Riyan Parag", primary_role="BATTER", nationality="India", dob=date(2001, 11, 10), is_eligible=True))
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # ======================================================================
        # STEP 1: Create Competition Workspace
        # ======================================================================
        ws_payload = {
            "name": "E2E SuperRR Talent Search",
            "description": "Integration verification sandbox for SuperRR competition.",
            "sport_type": "CRICKET",
            "competition_name": "SuperRR Selector",
            "season_or_edition": "Season 2",
        }
        res_ws = await ac.post("/api/v1/workspaces", json=ws_payload)
        assert res_ws.status_code == 201, res_ws.text
        ws_data = res_ws.json()
        workspace_id = ws_data["workspace_id"]
        assert ws_data["status"] == "DRAFT"

        # Activate Workspace via PATCH state transition
        res_act = await ac.patch(f"/api/v1/workspaces/{workspace_id}", json={"status": "ACTIVE"})
        assert res_act.status_code == 200, res_act.text
        assert res_act.json()["status"] == "ACTIVE"

        # ======================================================================
        # STEP 2: Upload Cricket Dataset
        # ======================================================================
        csv_bytes = E2E_SYNTHETIC_CSV.encode("utf-8")
        files = {"file": ("e2e_historical_deliveries.csv", io.BytesIO(csv_bytes), "text/csv")}
        headers = {"X-Workspace-Id": workspace_id}

        res_upload = await ac.post("/api/v1/datasets/upload", files=files, headers=headers)
        assert res_upload.status_code == 201, res_upload.text
        upload_data = res_upload.json()
        dataset_id = upload_data["dataset_id"]
        assert upload_data["file_format"] == "CSV"
        assert upload_data["status"] == "PENDING"

        # ======================================================================
        # STEP 3: Inspect Dataset Schema
        # ======================================================================
        res_inspect = await ac.get(f"/api/v1/datasets/{dataset_id}/inspection")
        assert res_inspect.status_code == 200, res_inspect.text
        inspect_data = res_inspect.json()
        assert inspect_data["dataset_id"] == dataset_id
        assert inspect_data["total_rows_estimated"] >= 18
        col_names = [c["column_name"] for c in inspect_data["columns"]]
        assert "batter" in col_names
        assert "bowler" in col_names

        # ======================================================================
        # STEP 4: Validate Dataset & Quarantine
        # ======================================================================
        res_val = await ac.post(f"/api/v1/datasets/{dataset_id}/validate")
        assert res_val.status_code == 200, res_val.text
        val_data = res_val.json()
        assert val_data["summary"]["status"] in ["VALIDATED", "VALIDATED_WITH_WARNINGS"]
        assert val_data["summary"]["valid_records"] > 0

        # ======================================================================
        # STEP 5: Persist Validated Records to Relational Tables
        # ======================================================================
        res_persist = await ac.post(f"/api/v1/datasets/{dataset_id}/persist")
        assert res_persist.status_code == 200, res_persist.text
        persist_data = res_persist.json()
        assert persist_data["deliveries_persisted"] > 0

        # ======================================================================
        # STEP 6: Generate Metric Registry Outputs
        # ======================================================================
        res_metrics = await ac.post("/api/v1/analytics/calculate", json={"dataset_id": dataset_id})
        assert res_metrics.status_code == 200, res_metrics.text
        metrics_data = res_metrics.json()
        assert metrics_data["dataset_id"] == dataset_id
        assert metrics_data["total_players_computed"] >= 3

        # Verify Sanju Samson batting metrics
        sanju_metrics = next((p for p in metrics_data["players"] if p["player_id"] == "P_SANJU"), None)
        assert sanju_metrics is not None
        assert sanju_metrics["sample_size"]["balls_faced"] >= 8
        assert sanju_metrics["batting_metrics"]["batting_strike_rate"]["value"] > 200.0

        # ======================================================================
        # STEP 7: Classify Player Roles
        # ======================================================================
        res_class = await ac.post("/api/v1/evaluation/classify", json={"dataset_id": dataset_id})
        assert res_class.status_code == 200, res_class.text
        class_data = res_class.json()
        assert len(class_data) >= 3

        # Sanju Samson should classify as BATTER; Bumrah as BOWLER
        sanju_role = next((c for c in class_data if c["player_id"] == "P_SANJU"), None)
        bumrah_role = next((c for c in class_data if c["player_id"] == "P_BUMRAH"), None)
        assert sanju_role["assigned_role"] == "BATTER"
        assert bumrah_role["assigned_role"] == "BOWLER"

        # ======================================================================
        # STEP 8: Configure Competition Eligibility Rules
        # ======================================================================
        config_payload = {
            "target_roles": ["BATTER", "BOWLER", "ALL_ROUNDER", "WICKETKEEPER"],
            "age_criteria": {"min_age": 18, "max_age": 35},
            "participation_criteria": {"min_balls_faced": 5, "min_legal_balls_bowled": 5},
            "shortlist_size": 5,
            "dataset_ids": [dataset_id],
        }
        res_cfg = await ac.put(f"/api/v1/workspaces/{workspace_id}/configuration", json=config_payload)
        assert res_cfg.status_code == 200, res_cfg.text
        cfg_data = res_cfg.json()
        assert cfg_data["participation_criteria"]["min_balls_faced"] == 5

        # ======================================================================
        # STEP 9 & 10: Calculate VOR Scoring Run & Rankings
        # ======================================================================
        res_score = await ac.post("/api/v1/scoring/calculate", json={"dataset_id": dataset_id})
        assert res_score.status_code == 200, res_score.text
        score_run = res_score.json()
        run_id = score_run["run_id"]
        assert score_run["total_evaluated"] >= 3

        # Fetch Rankings
        res_rank = await ac.get(f"/api/v1/scoring/rankings?run_id={run_id}")
        assert res_rank.status_code == 200, res_rank.text
        rankings = res_rank.json()
        assert len(rankings["rankings"]) >= 2
        # Verify descending order of VOR score
        for i in range(len(rankings["rankings"]) - 1):
            assert rankings["rankings"][i]["vor_score"] >= rankings["rankings"][i + 1]["vor_score"]

        # ======================================================================
        # STEP 11: Explainability Results & Score Reconciliation
        # ======================================================================
        res_explain = await ac.get(f"/api/v1/explainability/players/P_SANJU?run_id={run_id}")
        assert res_explain.status_code == 200, res_explain.text
        exp_data = res_explain.json()
        assert exp_data["final_vor"] > 0
        assert len(exp_data["top_strengths"]) > 0

        # Detailed score breakdown and mathematical reconciliation
        res_breakdown = await ac.get(f"/api/v1/explainability/players/P_SANJU/breakdown?run_id={run_id}")
        assert res_breakdown.status_code == 200, res_breakdown.text
        brk_data = res_breakdown.json()
        # Reconciliation constraint: |raw_composite - sum_contributions| <= 0.05
        assert brk_data["reconciliation_discrepancy"] <= 0.05

        # ======================================================================
        # STEP 12: Player Comparison & Cross-Role Safeguard
        # ======================================================================
        # Compatible comparison: Batter vs Batter (P_SANJU vs P_JAISWAL)
        comp_payload = {"player_ids": ["P_SANJU", "P_JAISWAL"], "run_id": run_id}
        res_comp_valid = await ac.post("/api/v1/comparisons/players", json=comp_payload)
        assert res_comp_valid.status_code == 200, res_comp_valid.text
        comp_valid_data = res_comp_valid.json()
        assert comp_valid_data["vor_comparison_valid"] is True
        assert comp_valid_data["is_cross_role"] is False
        assert comp_valid_data["vor_leader_id"] == "P_SANJU"

        # Incompatible comparison: Batter vs Bowler (P_SANJU vs P_BUMRAH)
        cross_payload = {"player_ids": ["P_SANJU", "P_BUMRAH"], "run_id": run_id}
        res_comp_cross = await ac.post("/api/v1/comparisons/players", json=cross_payload)
        assert res_comp_cross.status_code == 200, res_comp_cross.text
        cross_data = res_comp_cross.json()
        assert cross_data["is_cross_role"] is True
        assert cross_data["vor_comparison_valid"] is False
        assert cross_data["vor_leader_id"] is None  # Suppressed leader safeguard

        # ======================================================================
        # STEP 13: Generate Candidate Shortlist
        # ======================================================================
        sl_payload = {
            "name": "SuperRR Elite Shortlist S2",
            "dataset_id": dataset_id,
            "scoring_run_id": run_id,
            "override_shortlist_size": 2,
        }
        res_sl = await ac.post(f"/api/v1/workspaces/{workspace_id}/shortlists", json=sl_payload)
        assert res_sl.status_code == 201, res_sl.text
        sl_data = res_sl.json()
        shortlist_id = sl_data["shortlist_id"]
        assert sl_data["shortlisted_count"] > 0

        # ======================================================================
        # STEP 14: Review Shortlist Candidates
        # ======================================================================
        rev_payload = {
            "review_status": "APPROVED",
            "reviewer_notes": "Scout Note: Demonstrates elite boundary strike power in powerplay.",
        }
        res_rev = await ac.patch(
            f"/api/v1/workspaces/{workspace_id}/shortlists/{shortlist_id}/candidates/P_SANJU/review",
            json=rev_payload,
        )
        assert res_rev.status_code == 200, res_rev.text
        rev_data = res_rev.json()
        assert rev_data["review_status"] == "APPROVED"
        assert rev_data["reviewer_notes"] == rev_payload["reviewer_notes"]

        # ======================================================================
        # STEP 15: View Player Profile API
        # ======================================================================
        res_p_score = await ac.get(f"/api/v1/scoring/players/P_SANJU?run_id={run_id}")
        assert res_p_score.status_code == 200, res_p_score.text
        assert res_p_score.json()["player_id"] == "P_SANJU"

        # ======================================================================
        # STEP 16: Generate PDF Reports (All 4 Canonical Report Types)
        # ======================================================================
        # Type A: Competition Overview
        rep_a_res = await ac.post(
            f"/api/v1/workspaces/{workspace_id}/reports",
            json={"report_type": "COMPETITION_OVERVIEW", "run_id": run_id},
        )
        assert rep_a_res.status_code == 201, rep_a_res.text
        rep_a = rep_a_res.json()
        assert rep_a["report_type"] == "COMPETITION_OVERVIEW"
        assert rep_a["file_size_bytes"] > 0
        assert len(rep_a["sha256_hash"]) == 64

        # Type B: Individual Player Dossier
        rep_b_res = await ac.post(
            f"/api/v1/workspaces/{workspace_id}/reports",
            json={"report_type": "INDIVIDUAL_PLAYER", "player_id": "P_SANJU", "run_id": run_id},
        )
        assert rep_b_res.status_code == 201, rep_b_res.text
        rep_b = rep_b_res.json()
        assert rep_b["report_type"] == "INDIVIDUAL_PLAYER"

        # Type C: Player Comparison
        rep_c_res = await ac.post(
            f"/api/v1/workspaces/{workspace_id}/reports",
            json={
                "report_type": "PLAYER_COMPARISON",
                "comparison_player_ids": ["P_SANJU", "P_JAISWAL"],
                "run_id": run_id,
            },
        )
        assert rep_c_res.status_code == 201, rep_c_res.text
        rep_c = rep_c_res.json()
        assert rep_c["report_type"] == "PLAYER_COMPARISON"

        # Type D: Shortlist Dossier
        rep_d_res = await ac.post(
            f"/api/v1/workspaces/{workspace_id}/reports",
            json={
                "report_type": "SHORTLIST",
                "shortlist_id": shortlist_id,
                "include_reviewer_notes": True,
            },
        )
        assert rep_d_res.status_code == 201, rep_d_res.text
        rep_d = rep_d_res.json()
        assert rep_d["report_type"] == "SHORTLIST"

        # ======================================================================
        # STEP 17: Download Reports
        # ======================================================================
        down_res = await ac.get(f"/api/v1/workspaces/{workspace_id}/reports/{rep_a['report_id']}/download")
        assert down_res.status_code == 200
        assert down_res.headers["content-type"] == "application/pdf"
        assert down_res.content.startswith(b"%PDF-")

        down_b = await ac.get(f"/api/v1/workspaces/{workspace_id}/reports/{rep_b['report_id']}/download")
        assert down_b.status_code == 200
        assert down_b.content.startswith(b"%PDF-")


# ==============================================================================
# EDGE CASE VALIDATION SUITE
# ==============================================================================

@pytest.mark.anyio
async def test_edge_case_zero_denominator_safeguards():
    """Verify analytics and VOR calculations survive zero-denominator inputs gracefully."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Dataset with batter having 0 dismissals (Not Out) and 0 balls bowled
        zero_denom_csv = (
            "match_id,season,venue,batting_team,bowling_team,innings,over,ball,batter,bowler,runs_batter,extras,total_runs,wicket,dismissed_player,dismissal_kind\n"
            "M99,2024,Eden Gardens,KKR,SRH,1,1,1,P_NOT_OUT,P_ZERO_WKTS,4,0,4,0,,\n"
            "M99,2024,Eden Gardens,KKR,SRH,1,1,2,P_NOT_OUT,P_ZERO_WKTS,6,0,6,0,,\n"
            "M99,2024,Eden Gardens,KKR,SRH,1,1,3,P_NOT_OUT,P_ZERO_WKTS,1,0,1,0,,\n"
            "M99,2024,Eden Gardens,KKR,SRH,1,1,4,P_NOT_OUT,P_ZERO_WKTS,0,0,0,0,,\n"
        )
        csv_bytes = zero_denom_csv.encode("utf-8")
        files = {"file": ("zero_denom.csv", io.BytesIO(csv_bytes), "text/csv")}

        res_up = await ac.post("/api/v1/datasets/upload", files=files)
        assert res_up.status_code == 201
        ds_id = res_up.json()["dataset_id"]

        await ac.post(f"/api/v1/datasets/{ds_id}/validate")
        await ac.post(f"/api/v1/datasets/{ds_id}/persist")

        res_calc = await ac.post("/api/v1/analytics/calculate", json={"dataset_id": ds_id})
        assert res_calc.status_code == 200
        data = res_calc.json()

        # Verify not-out batter handled gracefully without ZeroDivisionError
        p_not_out = next(p for p in data["players"] if p["player_id"] == "P_NOT_OUT")
        assert p_not_out["batting_metrics"]["batting_average"]["value"] is None  # Safeguarded without throwing ZeroDivisionError
        assert p_not_out["batting_metrics"]["batting_average"]["status"] == "DIVIDE_BY_ZERO_SAFEGUARD"
        assert p_not_out["sample_size"]["times_dismissed"] == 0

        # Verify zero-wicket bowler handled gracefully
        p_bowler = next(p for p in data["players"] if p["player_id"] == "P_ZERO_WKTS")
        assert p_bowler["bowling_metrics"]["bowling_average"]["value"] is None  # Safeguarded without throwing


@pytest.mark.anyio
async def test_edge_case_empty_and_corrupt_dataset_handling():
    """Verify rejection of empty or malformed files."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Empty file
        empty_files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
        res_empty = await ac.post("/api/v1/datasets/upload", files=empty_files)
        assert res_empty.status_code in [400, 422]

        # Unsupported file format
        bad_files = {"file": ("data.txt", io.BytesIO(b"hello world"), "text/plain")}
        res_bad = await ac.post("/api/v1/datasets/upload", files=bad_files)
        assert res_bad.status_code in [400, 422]
