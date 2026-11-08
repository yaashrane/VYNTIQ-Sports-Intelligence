# VYNTIQ — Architecture Decision Records (ADRs)

**Document Reference:** ADR-VYNTIQ-001  
**Document Version:** 1.0.0  
**Status:** Approved Architectural Baseline  

---

## Index of Architectural Decisions

* **ADR-001:** Workspace Isolation Strategy — Shared Tables with `workspace_id`
* **ADR-002:** Application Topology — Modular Monolith vs. Distributed Microservices
* **ADR-003:** Scoring Paradigm — Deterministic Statistical Modeling vs. Black-Box ML
* **ADR-004:** Ingestion Architecture — Schema-Agnostic Column Mapping with Two-Tiered Quarantine
* **ADR-005:** Persistence Engine Strategy — PostgreSQL 16 Target with SQLite Local Parity
* **ADR-006:** Two-Track Delivery Strategy — Competition MVP vs. Full Commercial Platform
* **ADR-007:** Reporting Pipeline — Headless Programmatic Vector PDFs (ReportLab) vs. Headless Browser

---

## ADR-001: Workspace Isolation Strategy

### Context
VYNTIQ serves two distinct analytical scopes:
1. Multi-year canonical historical cricket benchmarks (IPL, international, domestic T20).
2. Client- and competition-specific sandboxes (specifically `workspace_super_rr_s2` for the SuperRR Selector Season 2 competition).

We evaluated three architectural options for isolating competition data from canonical data:
* **Option A:** PostgreSQL Schema-per-workspace (`schema_canonical`, `schema_super_rr`).
* **Option B:** PostgreSQL native Row-Level Security (RLS) policies.
* **Option C:** Shared tables with explicit `workspace_id` foreign keys and `origin_type` provenance stamping.

### Decision
**Adopt Option C (Shared Tables with `workspace_id` + `origin_type` Scoping)** for Version 1.0.

### Rationale
* **Operational Simplicity:** Schema-per-workspace requires complex dynamic DDL and complicates Alembic migrations. RLS requires dynamic session variable configuration on connection pool checkouts.
* **Analytical Efficiency:** Computing True Metrics requires comparing competition candidates against historical cohort baselines. Single-query relational joins across shared partitioned tables are dramatically faster and more maintainable than cross-schema queries.
* **Tenant Protection:** Enforced at the application gateway layer via FastAPI dependency injection (`Depends(get_current_workspace)`). Canonical historical data has `workspace_id = NULL` and is strictly read-only.

### Consequences
* Requires consistent application of workspace filters in database repositories.
* Can seamlessly upgrade to PostgreSQL RLS in Track B without changing table schemas.

---

## ADR-002: Application Topology — Modular Monolith

### Context
We must decide whether to structure VYNTIQ as distributed microservices (e.g., Ingestion Service, Analytics Service, Scoring Service, Reporting Service) or as a structured modular monolith.

### Decision
**Adopt a Modular Monolith Architecture** within a single FastAPI application repository.

### Rationale
* **Team Feasibility:** A small student development team operating under a 10-day competition deadline (Nov 8–18, 2026) cannot afford the overhead of Docker Compose networking, API gateway routing, and distributed tracing.
* **Zero Latency:** In-process Python function calls between ingestion, feature engineering, and scoring execute in nanoseconds, eliminating serialization and network latency.
* **Clean Boundaries:** Internal modules (`core/`, `domains/cricket/`, `workspaces/`) maintain strict interface boundaries, allowing future extraction into standalone services if horizontal scale demands it.

### Consequences
* Monolithic deployments; all components deploy together.

---

## ADR-003: Scoring Paradigm — Deterministic Statistical Modeling vs. Black-Box ML

### Context
Sports recruitment tools often attempt to deploy deep neural networks or black-box predictive models to rank player potential.

### Decision
**Reject Black-Box Machine Learning in favor of Deterministic Statistical Modeling** (ECDF Percentile Normalization, Multi-Attribute Utility Theory, and Bayesian Reliability Shrinkage).

### Rationale
* **Trust & Boardroom Defensibility:** In high-stakes franchise auctions, scouts and coaching staff reject black-box scores. Every VYNTIQ recommendation must be traceable to underlying event data and plain-English factor attribution ("The Story Behind the Metric").
* **Small-Sample Robustness:** Machine learning models overfit drastically on small cricket tournament sample sizes. Deterministic formulas with Bayesian shrinkage handle sparse data gracefully.
* **Auditability:** Every metric score can be reconstructed mathematically in an Excel sheet or test harness with zero discrepancy.

### Consequences
* Does not offer automated unsupervised clustering until Track B.

---

## ADR-004: Ingestion Architecture — Schema-Agnostic Column Mapping

### Context
The exact CSV/JSON schema of the official SuperRR Season 2 dataset will not be revealed until the official release on November 8, 2026, at 6:00 PM IST. Building an ingestion engine tied to an assumed column naming convention would cause catastrophic pipeline failures.

### Decision
**Implement a Dynamic Header Inspector & Column Mapping Adapter** with a Two-Tiered Validation Gate (Pydantic structural validation followed by cricket domain logic validation) and a Quarantine Error Logger.

### Rationale
* Accommodates naming variations (`striker` vs. `batter`, `bowling_team` vs. `bowler_team`) without code changes.
* Quarantines corrupted rows without crashing the entire batch ingestion run.
* Produces an audit-ready diagnostic report showing exact row numbers and violation reasons.

### Consequences
* Analysts must review and confirm the proposed column mapping during initial dataset import if unknown headers appear.

---

## ADR-005: Persistence Engine Strategy — PostgreSQL Target with SQLite Local Parity

### Context
Developers need to run rapid unit tests and local analyses without complex local infrastructure setup, while production deployments require indexed partitioned tables.

### Decision
**Utilize SQLAlchemy 2.0 with unified declarative models supporting both SQLite (via `aiosqlite`) and PostgreSQL 16 (via `asyncpg`).**

### Rationale
* Developers can clone the repository, run tests, and execute the complete pipeline locally using lightweight SQLite file storage.
* Production deployments can switch to PostgreSQL simply by configuring the `DATABASE_URL` environment variable.

### Consequences
* Database models must avoid database-specific proprietary SQL dialects and utilize standard ANSI SQL / SQLAlchemy abstractions.

---

## ADR-006: Two-Track Delivery Strategy

### Context
The platform vision includes extensive enterprise SaaS features (multi-sport support, interactive weight sliders, ReportLab PDF compilers, and React frontend dashboards). Attempting to build all of these before November 18, 2026, would guarantee failure in the competition.

### Decision
**Establish Two Mutually Exclusive Development Timelines:**
* **Track A: Competition MVP (Nov 8–18, 2026):** Focus exclusively on ingestion, cricket feature engineering, role-specific scoring, candidate ranking, and submission report generation.
* **Track B: Full VYNTIQ Platform (Post-Competition):** Build the editorial React UI, vector PDF compilation engine, and multi-sport abstractions.

### Rationale
* Guarantees delivery of a winning, verified submission for the SuperRR Selector Season 2 competition within the strict 10-day window.

---

## ADR-007: Reporting Pipeline — Headless Programmatic PDFs (ReportLab)

### Context
Scouting reports must be distributed to coaching staff and team directors who require print-ready, professional dossiers.

### Decision
**Adopt Python ReportLab for native programmatic vector PDF generation** (scheduled for Track B), while utilizing formatted Markdown/HTML analytical dossiers for Track A.

### Rationale
* Avoids headless browser (Puppeteer/Chrome) memory leaks and container instability.
* Produces crisp vector typography and selectable text matching the VYNTIQ editorial brand standard.

---

## Status of Open Decisions & Assumptions

| Decision ID | Topic | Current Assumption | Status |
| :--- | :--- | :--- | :--- |
| **OPEN DECISION 01** | Official RR Dataset Structure | Assumed to be tabular ball-by-ball or match-summary data released as CSV or JSON. | **OPEN DECISION** (Pending release on Nov 8, 6:00 PM IST). |
| **OPEN DECISION 02** | Official Eligibility Rules | Assumed to focus on domestic / uncapped Indian players for the RR ecosystem. | **OPEN DECISION** (To be verified upon competition brief inspection). |
| **OPEN DECISION 03** | Tracking Telemetry Availability| Pitch maps, release speeds, and wagon wheels are assumed to be **unavailable** in standard files. | **OPEN DECISION** (Treated as optional extensions). |
| **OPEN DECISION 04** | Role Weight Presets | Current role weights are provisional baseline parameters for domain testing. | **OPEN DECISION** (To be tuned during candidate evaluation). |
