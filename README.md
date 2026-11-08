# VYNTIQ — Sports Intelligence

> **"Every Metric Tells a Story."**  
> An independent, premium sports intelligence and scouting platform transforming granular play-by-play statistics into explainable, contextual, and decision-ready recruitment intelligence.

---

## 1. Executive Overview

VYNTIQ bridges the gap between raw match data and high-stakes recruitment decisions. Designed initially for cricket analytics and talent scouting (with multi-sport extensibility), VYNTIQ eliminates two core failures in existing sports analytics tooling:

1. **The "Black Box" Problem:** Predictive AI tools offer rankings without transparent mathematical reasoning, preventing coaching staff and executives from trusting recommendations.
2. **The "Stat Sheet" Problem:** Traditional dashboards display uncontextualized aggregate statistics (career averages, overall strike rates) that fail to adjust for match phases, scoring environments, or sample reliability.

VYNTIQ provides **role-specific, context-aware evaluations** where every composite rating is mathematically deconstructed, transparently weighted, and traceable down to raw ball-by-ball delivery records.

---

## 2. System Architecture & Topology

VYNTIQ Version 1.0 is architected as a **modular monolith** with clean layer boundaries:

```text
VYNTIQ/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entry point & lifespan
│   │   ├── api/
│   │   │   ├── api_v1.py            # Root v1 router mounting versioned endpoints
│   │   │   ├── dependencies.py      # Dependency injection (DB session, settings, workspace scope)
│   │   │   └── routes/              # Analytics, datasets, evaluation, scoring, explainability, comparisons, workspaces
│   │   ├── core/                    # Config, logging, exceptions, database
│   │   ├── models/                  # Base, cricket, dataset, and workspace SQLAlchemy models
│   │   ├── schemas/                 # Pydantic v2 schemas across all domains
│   │   ├── repositories/            # Generic BaseRepository & WorkspaceRepository
│   │   ├── services/                # Analytics, comparison, evaluation, explainability, ingestion, scoring, shortlisting, workspace
│   │   └── utils/                   # Shared mathematical and data utilities
│   ├── tests/                       # 100 automated backend unit, integration & e2e pipeline tests
│   ├── requirements.txt             # Pinned backend dependencies
│   └── .env.example                 # Environment configuration template
│
├── frontend/                        # Editorial Sports Analytics Web Application
│   ├── src/
│   │   ├── api/                     # Centralized API client, types, and endpoints
│   │   ├── components/              # Buttons, badges, modals, empty states, cards, charts
│   │   ├── context/                 # Workspace selection state provider
│   │   ├── pages/                   # Overview, Workspaces, Player Explorer, Profiles, Comparison
│   │   ├── test/                    # 10 Vitest + RTL component and navigation tests
│   │   ├── App.tsx                  # React Router configuration
│   │   └── index.css                # Tailwind directives & design tokens
│   ├── tailwind.config.js           # VYNTIQ design system token definitions
│   ├── vite.config.ts               # Vite bundler & proxy configuration
│   └── package.json                 # React, TypeScript, Tailwind, Lucide dependencies
│
├── docs/                            # Comprehensive architectural & QA documentation
│   ├── PRODUCT_VISION.md            # Vision, positioning, and two-track strategy
│   ├── PRODUCT_REQUIREMENTS.md      # Functional & non-functional requirements
│   ├── SYSTEM_ARCHITECTURE.md       # Architecture blueprint & layer topology
│   ├── FEATURE_MAP.md               # Capabilities, inputs/outputs & prioritization
│   ├── DESIGN_SYSTEM.md             # Editorial design tokens & role-adaptive radars
│   ├── TECH_STACK.md                # Technology choices & dependency constraints
│   ├── DEVELOPMENT_ROADMAP.md       # 10-day competition sprint vs post-MVP roadmap
│   ├── SCORING_METHODOLOGY.md       # Exact formulas, ECDF scaling & reliability
│   ├── DATA_DICTIONARY.md           # Canonical schemas & ingestion mapping
│   ├── ARCHITECTURE_DECISIONS.md    # Formal Architecture Decision Records (ADRs)
│   ├── WORKSPACE_AND_SHORTLIST_SPECIFICATION.md # Workspace & shortlisting spec
│   ├── PLAYER_INTELLIGENCE_UI.md    # Player Explorer, Profile & Comparison UI spec
│   ├── REPORTING_AND_EXPORT_SPECIFICATION.md # PDF Reports & Export Engine spec
│   ├── FRONTEND_ARCHITECTURE.md     # Frontend architecture & token mapping
│   ├── END_TO_END_TEST_REPORT.md    # 17-step pipeline & data flow verification
│   ├── SECURITY_REVIEW.md           # Tenant isolation, path safety & error shielding
│   ├── RELEASE_READINESS_CHECKLIST.md # Release gates & measured benchmarks
│   └── KNOWN_LIMITATIONS.md         # Operational boundaries & data status
│
├── .gitignore                       # Python, Node & environment gitignore
└── README.md                        # Project documentation
```

---

## 3. Technology Stack

* **Language & Runtime:** Python 3.11+ (Tested on Python 3.13)
* **API Framework:** FastAPI 0.111+ (Asynchronous ASGI framework, OpenAPI/Swagger)
* **Data Validation:** Pydantic v2 & Pydantic Settings
* **Persistence Layer:** SQLAlchemy 2.0+ (Modern typed async ORM)
  * Local Dev & Testing: SQLite via `aiosqlite` (Zero-dependency local database)
  * Production Target: PostgreSQL 16+ via `asyncpg` (Partitioned relational tables)
* **Analytics Core:** Pandas 2.2+, NumPy 1.26+, SciPy 1.13+
* **PDF Reporting & Export:** ReportLab 4.2+, Matplotlib 3.10+ (Headless `Agg` backend)
* **Testing:** Pytest 8.2+, anyio, httpx, vitest, React Testing Library

---

## 4. Getting Started & Local Development

### 4.1 Prerequisites
* Python 3.11 or higher
* Git

### 4.2 Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd "VYNTIQ Sports Intelligence"
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   # Copy template to active .env
   cp backend/.env.example backend/.env
   ```

### 4.3 Running the Backend API

Start the development server using Uvicorn:

```bash
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The service will be available at:
* **Root Info:** `http://localhost:8000/`
* **Health Endpoint:** `http://localhost:8000/api/v1/health`
* **Interactive OpenAPI Docs (Swagger UI):** `http://localhost:8000/api/v1/docs`
* **ReDoc Documentation:** `http://localhost:8000/api/v1/redoc`

### 4.4 Running the Frontend Application

In a separate terminal, install packages and start the Vite development server:

```bash
cd frontend
npm install
npm run dev
```

The frontend dashboard will be available at:
* **Dashboard URL:** `http://localhost:3000/`

---

## 5. Running Automated Tests

### 5.1 Backend Test Suite (Pytest)

Run all 100 backend domain, integration, and end-to-end pipeline tests:

```bash
python -m pytest backend/tests -v
```

### 5.2 Frontend Test Suite (Vitest)

Run all 10 frontend component, layout, and integration tests:

```bash
cd frontend
npm run test
```

---

## 6. Implementation Status (Current Phase)

| Milestone / Component | Track | Status | Description |
| :--- | :---: | :---: | :--- |
| **Architectural Documentation** | All | **Completed** | 12 comprehensive docs in `/docs/` establishing vision, PRD, ADRs, scoring, and data dictionary. |
| **Backend Foundation & Lifespan** | Track A | **Completed** | FastAPI modular monolith scaffold with centralized Pydantic Settings, CORS, and logging. |
| **Data Ingestion & Quarantine (Prompt 04)** | Track A | **Completed** | 6-stage ingestion pipeline with schema-agnostic column mapper and quarantine logger. |
| **Cricket Metrics Engine (Prompt 05)** | Track A | **Completed** | Vectorized batting/bowling calculators, True Strike Rate, True Economy Rate, and registry. |
| **Role Classification & Profiles (Prompt 06)** | Track A | **Completed** | Role archetypes, sample adequacy gates, and 6-axis evaluation profiles. |
| **VOR Scoring & Ranking Engine (Prompt 07)** | Track A | **Completed** | ECDF percentiles, Bayesian reliability shrinkage, and 3-tier tie-breaking ranking engine. |
| **Explainability & Comparison (Prompt 08)** | Track A | **Completed** | Factor attribution ($|\Delta| \le 0.05$) and multi-player comparison with cross-role gating. |
| **Competition Workspaces & Shortlisting (Prompt 09)** | Track A | **Completed** | Isolated workspaces, configurable eligibility, candidate shortlisting, and audit logs. |
| **Frontend Foundation & Dashboard (Prompt 10)** | Track A | **Completed** | React 19 + TypeScript + Vite + Tailwind CSS dashboard with workspace management. |
| **Player Intelligence UI (Prompt 11)** | Track A | **Completed** | Interactive Player Explorer, candidate profiles with polar radars, and multi-player comparison UI. |
| **PDF Reporting & Export Engine (Prompt 12)** | Track A | **Completed** | Vector PDF export engine with 4 canonical report types, audit records, charts, and REST API. |
| **End-to-End QA & Release Readiness (Prompt 13)** | Track A | **Completed** | 17-step pipeline test suite, zero-denominator safeguards, security review, benchmarks, and release gates. |

---

## 7. Release Governance & Official Competition Data Status

* **Release Status:** `v1.0.0-rc1` (Integration Complete — Ready for Staging Deployment)
* **Official Data Gate:** `BLOCKED — OFFICIAL DATA PENDING` (Awaiting delivery of official competition match records).
* **Automated Test Coverage:** 100/100 Backend Tests Passing (100%), 10/10 Frontend Tests Passing (100%).


