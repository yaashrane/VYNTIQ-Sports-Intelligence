# VYNTIQ — Technology Stack & Engineering Specifications

**Document Reference:** TECH-VYNTIQ-002  
**Document Version:** 2.0.0 (Post-Architecture Review & Competition MVP Alignment)  
**Status:** Approved Architectural Baseline  

---

## 1. Technical Simplicity & Team Feasibility Mandate

To ensure the architecture is realistically achievable by a small, focused student development team within the 10-day competition window (November 8–18, 2026), VYNTIQ enforces a **disciplined modular monolith architecture**.

We strictly avoid premature enterprise overhead:
* **NO Kubernetes or Microservice Meshes:** The backend runs as a single, well-structured FastAPI service.
* **NO Distributed Message Brokers (Kafka / RabbitMQ):** Ingestion runs synchronously or via lightweight Python background tasks.
* **NO Heavy AI/ML Frameworks (PyTorch, TensorFlow):** Scoring relies on deterministic, auditable statistical formulas (ECDF, Bayesian shrinkage, MAUT) executed via NumPy and SciPy.
* **NO Complex Caching Infrastructure (Redis):** In-memory dictionaries and LRU caches suffice for sub-second performance during the competition.

---

## 2. Dependency Partitioning: Track A (MVP) vs. Track B (Full Platform)

```
┌────────────────────────────────────────────────────────────────────────┐
│ TRACK A: COMPETITION MVP DEPENDENCY SET (IMMEDIATELY REQUIRED)         │
├────────────────────────────────────────────────────────────────────────┤
│ Application Framework & Validation:                                    │
│ • Python 3.11+ (High-performance runtime, modern typing)               │
│ • FastAPI 0.111+ (Async REST API, dependency injection, OpenAPI)       │
│ • Pydantic v2 (Rust-accelerated structural validation & schemas)       │
│ • Uvicorn (Lightweight ASGI server)                                    │
├────────────────────────────────────────────────────────────────────────┤
│ Analytics & Feature Engineering:                                       │
│ • Pandas 2.2+ (Vectorized dataframe aggregations & phase splits)        │
│ • NumPy 1.26+ (Matrix calculations, percentile distributions)          │
│ • SciPy 1.13+ (ECDF empirical normalization, Bayesian shrinkage)       │
├────────────────────────────────────────────────────────────────────────┤
│ Persistence Layer:                                                     │
│ • SQLAlchemy 2.0+ (Modern typed async ORM with SQLite & Postgres)      │
│ • SQLite (aiosqlite) (Zero-dependency local database for dev/testing)  │
│ • PostgreSQL 16+ (asyncpg) (Production database via config toggle)     │
├────────────────────────────────────────────────────────────────────────┤
│ Testing & Quality Assurance:                                           │
│ • Pytest 8.2+ & pytest-asyncio (Unit, domain, and integration tests)   │
│ • Ruff (High-speed linting and code formatting)                        │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ TRACK B: FULL PLATFORM DEPENDENCY SET (POST-COMPETITION ROADMAP)       │
├────────────────────────────────────────────────────────────────────────┤
│ Frontend Presentation Layer:                                           │
│ • React 18+ (Strict Mode Single-Page Application)                      │
│ • TypeScript 5.4+ (Strict typing, no implicit `any`)                   │
│ • Tailwind CSS 3.4+ (Custom design tokens & editorial theme)           │
│ • Lucide React (Disciplined, uniform icon set)                         │
│ • TanStack Query v5 (Server state caching & synchronization)          │
│ • Vitest & React Testing Library (Frontend unit & component tests)     │
├────────────────────────────────────────────────────────────────────────┤
│ Enterprise Reporting Engine:                                           │
│ • ReportLab 4.2+ (Headless, native programmatic vector PDF compiler)   │
│ • Kaleido 0.2+ (Static vector image export for complex distributions)  │
├────────────────────────────────────────────────────────────────────────┤
│ Database Migrations & Distributed Caching:                             │
│ • Alembic (Production database schema migrations)                      │
│ • Redis (Distributed query caching for multi-tenant SaaS)              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Selection & Trade-Off Analysis

### 3.1 Persistence Engine: SQLite / PostgreSQL Dual Support
* **Decision:** Utilize SQLAlchemy 2.0 with unified models that support both SQLite (via `aiosqlite`) and PostgreSQL (via `asyncpg`).
* **Rationale:**
  * Allows the team to develop, run unit tests, and execute the complete competition evaluation pipeline on developer laptops without requiring a running Docker daemon or local PostgreSQL server.
  * Setting `DATABASE_URL=postgresql+asyncpg://...` instantly switches to production PostgreSQL with partitioned tables for multi-user hosting.

### 3.2 Analytics Core: Deterministic Statistics vs. Black-Box Machine Learning
* **Decision:** Vectorized Pandas, NumPy, and SciPy for deterministic statistical modeling (ECDF percentiles, True Strike Rate deviations, Bayesian shrinkage).
* **Rationale:**
  * Sports executives and competition evaluators demand 100% transparency. If a candidate is recommended for the Top 10, the analyst must be able to explain the exact mathematical weights, confidence interval, and underlying event counts.
  * Statistical formulas execute deterministically in milliseconds without GPU requirements or inference latency.
  * Machine learning black-boxes are vulnerable to hallucination, overfitting on small sample sizes, and lack auditability.

### 3.3 Application Gateway: FastAPI vs. Flask / Django
* **Decision:** FastAPI with Python 3.11+.
* **Rationale:**
  * Provides dependency injection (`Depends(get_current_workspace)`) which cleanly enforces workspace isolation across all routes without boilerplate.
  * Native Pydantic v2 integration guarantees microsecond-level payload validation during dataset ingestion.
  * Automatic OpenAPI documentation allows frontend clients to generate TypeScript contracts automatically in Track B.

---

## 4. Dependency Constraint Rules

1. **Strict Core Boundaries:** No additional Python packages may be added without architectural review demonstrating that standard libraries, NumPy, or Pandas cannot solve the requirement.
2. **Zero External CSS Frameworks beyond Tailwind:** Material-UI, Ant Design, and Bootstrap are strictly prohibited to preserve the unique VYNTIQ editorial brand identity.
3. **Traceable Numerical Computation:** All mathematical calculations must be implemented as pure, deterministic functions accompanied by unit tests with known input-output baselines.
