# VYNTIQ — Known Limitations & Technical Roadmap

**Document ID:** VYNTIQ-LIM-001  
**Status:** ACTIVE  
**Date:** 2026-11-08  

---

## 1. Scope & Purpose

This document catalogs technical boundaries, known limitations, and operational trade-offs present in VYNTIQ v1.0.0-rc1. These items are tracked for transparent release governance and prioritization in subsequent product milestones.

---

## 2. Official Competition Data Status

### Status: `BLOCKED — OFFICIAL DATA PENDING`

- **Current State:** The end-to-end platform, data pipelines, scoring algorithms, and reporting engines have been verified using automated synthetic fixtures, historical delivery sets, and edge-case testing suites. No official external competition data files (e.g. SuperRR official candidate files) have been dropped or supplied into the repository.
- **Expected Data Format & Structure:**
  - File Format: Comma-Separated Values (`.csv`) or JSON delivery log (`.json`).
  - Required Columns / Keys:
    - `match_id` (string / int): Unique match identifier.
    - `season` (string / int): Tournament edition (e.g., `2024` or `Season 2`).
    - `innings` (int): `1` or `2`.
    - `over` (int): Over index (`0-19` or `1-20`).
    - `ball` (int): Delivery index within over (`1-6+`).
    - `batter` (string): Batter identifier or canonical name.
    - `bowler` (string): Bowler identifier or canonical name.
    - `runs_batter` (int): Runs scored off the bat.
    - `extras` (int): Sundries (wides, no-balls, leg-byes, byes).
    - `total_runs` (int): Total runs scored on the delivery.
    - `wicket` (int / bool): Binary wicket indicator (`0` or `1`).
    - `dismissed_player` (string | null): Name of dismissed player.
    - `dismissal_kind` (string | null): Type of dismissal (`caught`, `bowled`, `lbw`, `run out`, `stumped`).
  - Expected Player Master Catalog:
    - `player_id`, `canonical_name`, `dob`, `primary_role`, `nationality`, `is_eligible`.
- **Mitigation & Unblocking Procedure:** As soon as official competition files are supplied, upload them via `POST /api/v1/datasets/upload` with header `X-Workspace-Id: <workspace_id>`. The schema inspector will auto-resolve aliases and validate records.

---

## 3. Database & Concurrency Boundaries

### 3.1 SQLite Concurrency in Development Target
- **Limitation:** In the default developer configuration (`DATABASE_URL = "sqlite+aiosqlite:///./vyntiq.db"`), SQLite enforces single-writer locking. High-concurrency write operations (e.g. simultaneous bulk uploads across multiple workspaces) may encounter `sqlite3.OperationalError: database is locked`.
- **Target Resolution:** In accordance with **ADR-005**, staging and production environments must configure PostgreSQL (`DATABASE_URL = "postgresql+asyncpg://user:pass@host/vyntiq"`), which supports row-level locking, connection pooling, and multi-tenant concurrent writes.

---

## 4. PDF Generation & Document Exporting

### 4.1 Sync-to-Async ReportLab Execution
- **Limitation:** ReportLab document compilation is CPU-bound and synchronous. In the current release, it is dispatched via `asyncio.to_thread` to avoid blocking the FastAPI event loop.
- **Production Recommendation:** For enterprise multi-user production deployments with high volume, report generation should be offloaded to an asynchronous background worker queue (e.g. Celery + Redis or ARQ) with WebSocket notification or polling.

### 4.2 Candidate Table Page Budgets
- **Limitation:** Shortlist dossiers and competition overviews default to presenting the top 20 candidates. Datasets with > 50 shortlisted candidates will produce multi-page tables that expand document length.
- **Target Resolution:** Future iterations will support configurable PDF pagination caps and CSV data export alongside PDF dossiers.

---

## 5. Multi-Sport Extensibility

### 5.1 Sport Adapters
- **Current Support:** Cricket is the fully implemented and validated sport in v1.0.0. The platform's generic concepts (Workspaces, Datasets, Dimensions, VOR Scoring, Shortlists, Reports) are sport-agnostic.
- **Next Supported Sports:** Adding Football (Soccer) or Basketball requires adding sport-specific metric calculators (`football_metrics.py`), schema mappers, and dimensional profiles without changing the core VOR scoring engine or workspace architecture.

