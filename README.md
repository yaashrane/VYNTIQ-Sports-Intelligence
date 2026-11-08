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
│   │   │   └── routes/
│   │   │       └── health.py        # System health & availability endpoint
│   │   ├── core/
│   │   │   ├── config.py            # Centralized Pydantic Settings configuration
│   │   │   ├── logging.py           # Unified standard library logging configuration
│   │   │   ├── exceptions.py        # Domain exception hierarchy & global error handlers
│   │   │   └── database.py          # SQLAlchemy 2.0 async engine, sessionmaker & health checks
│   │   ├── models/
│   │   │   └── base.py              # DeclarativeBase & TimestampMixin audit primitives
│   │   ├── schemas/
│   │   │   ├── common.py            # Standardized error envelopes & responses
│   │   │   └── health.py            # Health check response schemas
│   │   ├── repositories/
│   │   │   └── base.py              # Generic async repository pattern
│   │   ├── services/                # Domain services (Feature engineering, scoring)
│   │   └── utils/                   # Shared mathematical and data utilities
│   ├── tests/
│   │   ├── conftest.py              # Pytest fixtures & async HTTP test client
│   │   ├── test_config.py           # Configuration validation tests
│   │   ├── test_database.py         # DB connection & BaseRepository CRUD tests
│   │   ├── test_errors.py           # Exception handling & 500 masking tests
│   │   └── test_health.py           # Health endpoint & schema verification tests
│   ├── requirements.txt             # Pinned backend dependencies
│   └── .env.example                 # Environment configuration template
│
├── docs/                            # Comprehensive architectural documentation
│   ├── PRODUCT_VISION.md            # Vision, positioning, and two-track strategy
│   ├── PRODUCT_REQUIREMENTS.md      # Functional & non-functional requirements
│   ├── SYSTEM_ARCHITECTURE.md       # Architecture blueprint & layer topology
│   ├── FEATURE_MAP.md               # Capabilities, inputs/outputs & prioritization
│   ├── DESIGN_SYSTEM.md             # Editorial design tokens & role-adaptive radars
│   ├── TECH_STACK.md                # Technology choices & dependency constraints
│   ├── DEVELOPMENT_ROADMAP.md       # 10-day competition sprint vs post-MVP roadmap
│   ├── SCORING_METHODOLOGY.md       # Exact formulas, ECDF scaling & reliability
│   ├── DATA_DICTIONARY.md           # Canonical schemas & ingestion mapping
│   └── ARCHITECTURE_DECISIONS.md    # 7 formal Architecture Decision Records (ADRs)
│
├── .gitignore                       # Python & environment gitignore
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
* **Testing:** Pytest 8.2+, anyio, httpx

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

### 4.4 Health Check Verification

Test application availability via `curl` or browser:

```bash
curl http://localhost:8000/api/v1/health
```

Expected JSON response:
```json
{
  "status": "healthy",
  "service": "vyntiq-api",
  "version": "1.0.0"
}
```

---

## 5. Running Automated Tests

Run the test suite with Pytest:

```bash
# Run all tests with verbose output
python -m pytest backend/tests -v

# Run with test summary output
python -m pytest backend/tests -q
```

---

## 6. Implementation Status (Current Phase)

| Milestone / Component | Track | Status | Description |
| :--- | :---: | :---: | :--- |
| **Architectural Documentation** | All | **Completed** | 10 comprehensive docs in `/docs/` establishing vision, PRD, ADRs, scoring, and data dictionary. |
| **Backend Foundation & Lifespan** | Track A | **Completed** | FastAPI modular monolith scaffold with centralized Pydantic Settings, CORS, and logging. |
| **Exception Hierarchy & Handlers** | Track A | **Completed** | Global exception handlers returning standardized error envelopes (`error: {code, message, details}`). |
| **Database & Repository Layer** | Track A | **Completed** | SQLAlchemy 2.0 async engine supporting SQLite dev parity & PostgreSQL target; generic `BaseRepository`. |
| **Health & Core Endpoints** | Track A | **Completed** | `GET /api/v1/health` responding with service availability and semantic version. |
| **Automated Test Suite** | Track A | **Completed** | 15 automated unit & integration tests covering config, DB, health, and error handling (100% pass rate). |
| **Data Ingestion & Quarantine** | Track A | *Next Phase* | Dynamic header inspection, column mapping, and two-tiered validation gate. |
| **Cricket Feature Engineering** | Track A | *Next Phase* | Phase-of-play extraction (PP/Mid/Death), True Strike Rate (TSR), and True Economy Rate (TER). |
| **Role Scoring & VOR Engine** | Track A | *Next Phase* | ECDF percentile normalization, Bayesian reliability shrinkage, and Top 10 candidate ranking. |
| **Editorial Web UI & PDF Engine** | Track B | *Deferred* | React 18 frontend and ReportLab programmatic vector PDF compiler (Post-competition). |
