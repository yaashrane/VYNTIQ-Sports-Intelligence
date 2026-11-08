# VYNTIQ — Technology Stack & Engineering Specifications

**Document Reference:** TECH-VYNTIQ-001  
**Document Version:** 1.0.0  
**Status:** Approved Architectural Baseline  

---

## 1. Architectural Technology Stack Overview

In alignment with VYNTIQ's mandate to avoid unnecessary dependencies and maintain high mathematical precision and performance, the platform utilizes a tightly coupled, highly efficient technology stack.

```
┌────────────────────────────────────────────────────────────────────────┐
│ VYNTIQ FULL-STACK TECHNOLOGY ECOSYSTEM                                │
├────────────────────────────────────────────────────────────────────────┤
│ Frontend Presentation:                                                 │
│ • React 18+ (SPA with StrictMode)                                     │
│ • TypeScript 5.4+ (Strict typing, no implicit `any`)                   │
│ • Tailwind CSS 3.4+ (Custom design tokens & editorial theme)           │
│ • Lucide React (Disciplined, uniform icon set)                         │
│ • TanStack Query v5 (Server state caching & synchronization)          │
│ • Vitest & React Testing Library (Frontend unit & component tests)     │
├────────────────────────────────────────────────────────────────────────┤
│ Backend API & Gateway:                                                 │
│ • Python 3.11+ (High performance, typing improvements)                 │
│ • FastAPI 0.111+ (Async ASGI framework, OpenAPI documentation)         │
│ • Pydantic v2 (Rust-backed validation, schema serialization)           │
│ • Uvicorn (Lightning-fast ASGI web server)                             │
├────────────────────────────────────────────────────────────────────────┤
│ Analytics & Feature Engineering:                                       │
│ • Pandas 2.2+ (Vectorized dataframe aggregations & time splits)        │
│ • NumPy 1.26+ (Matrix calculations, percentile distributions)          │
│ • SciPy 1.13+ (Statistical distributions, ECDF, Bayesian shrinkage)   │
│ • Plotly 5.22+ (Interactive and headless chart generation)             │
├────────────────────────────────────────────────────────────────────────┤
│ Persistence & Storage:                                                 │
│ • PostgreSQL 16+ (Relational engine, JSONB, time partitioning)         │
│ • SQLAlchemy 2.0+ (Async ORM & core query builder)                     │
│ • Alembic (Database schema migrations)                                 │
│ • asyncpg (High-throughput async PostgreSQL driver)                    │
├────────────────────────────────────────────────────────────────────────┤
│ Reporting & Document Compilation:                                      │
│ • ReportLab 4.2+ (Headless, native programmatic vector PDF generator)  │
│ • Kaleido 0.2+ (Headless static vector export for Plotly figures)      │
├────────────────────────────────────────────────────────────────────────┤
│ Quality, Testing & CI/CD:                                              │
│ • Pytest 8.2+ & pytest-asyncio (Backend unit, integration tests)       │
│ • Ruff (Ultra-fast Python linter and formatter)                        │
│ • mypy (Static type checking for Python)                               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Justification & Dependency Boundary Analysis

### 2.1 Backend: FastAPI vs. Django / Flask
* **Decision:** FastAPI with Python 3.11+.
* **Rationale:**
  * Native asynchronous support (`async`/`await`) enables high-throughput streaming responses and parallel calculation queries.
  * Pydantic v2 provides Rust-backed, microsecond-level payload validation—critical when parsing thousands of delivery records during dataset ingestion.
  * Automatic OpenAPI (Swagger) schema generation ensures frontend TypeScript types can be generated directly from backend contracts.
* **Rejected Alternative:** Django (Too monolithic, heavy ORM overhead, excessive boilerplate for an analytical API-first architecture).

### 2.2 Analytics Core: Explainable Statistical Formulations vs. Black-Box ML
* **Decision:** Vectorized Pandas, NumPy, and SciPy for deterministic statistical modeling (MAUT, ECDF, True Metric deviation) rather than complex Deep Learning / Black-box models.
* **Rationale:**
  * Sports executives, coaching staff, and scouts require complete transparency. If a player is ranked #1 in a death-overs bowling cohort, the analyst must be able to explain the exact mathematical weights and percentile standings.
  * Statistical formulas execute deterministically in milliseconds without GPU requirements or inference latency.
  * Black-box ML models are prone to hallucination, overfitting on small sample sizes, and lack auditability.

### 2.3 Reporting: ReportLab vs. Headless Browser (Puppeteer/Playwright)
* **Decision:** ReportLab for programmatic vector PDF generation.
* **Rationale:**
  * **Memory & Reliability:** Headless Chrome instances consume 300MB–800MB per process and are notoriously unstable in containerized production environments.
  * **Vector Precision:** ReportLab produces genuine vector PDFs where text is selectable, crisp, and print-ready at any scale, using precise millimeter-based editorial layouts.
  * **Speed:** Programmatic PDF generation completes in $< 500\text{ ms}$, compared to $3–6\text{ seconds}$ required to boot a browser instance, render a DOM, and capture a print raster.

### 2.4 Persistence: PostgreSQL vs. NoSQL / Document Store
* **Decision:** PostgreSQL 16 with native JSONB and partition tables.
* **Rationale:**
  * Sports event data is fundamentally relational: `Matches` have `Innings`, `Innings` have `Deliveries`, `Deliveries` link to `Players`, `Teams`, and `Venues`.
  * Strong ACID guarantees are required to maintain strict data integrity during dataset uploads and validation runs.
  * Partitioning tables by tournament season ensures queries over 100,000+ deliveries execute with index-only scans in sub-millisecond timeframes.
  * JSONB columns offer flexible storage for sport-specific telemetry extensions without breaking core relational schemas.

### 2.5 Frontend: React 18 + TypeScript + Tailwind CSS
* **Decision:** React 18 Single-Page Application scaffolded with Vite.
* **Rationale:**
  * TypeScript guarantees strict compile-time safety across complex sports metric types (e.g., differentiating raw rates from phase-adjusted true rates).
  * Tailwind CSS enables strict adherence to the VYNTIQ design tokens (`surface-ground`, `accent-magenta`, `accent-lime`, `text-primary`) without CSS bloat or runtime style injection overhead.
  * Custom reusable component system guarantees editorial uniformity without the bloat of generic external UI kits.

---

## 3. Dependency Constraint Rules

To prevent architectural drift and dependency bloat:

1. **Zero External CSS Frameworks beyond Tailwind:** No Material-UI, Ant Design, or Bootstrap. All components are built custom from clean headless primitives.
2. **Strict Python Dependency Boundaries:** Any new Python package requires architectural justification demonstrating that it cannot be cleanly implemented with existing standard libraries, NumPy, or Pandas.
3. **No Unbounded Asynchronous Tasks:** All long-running ingestion or batch report jobs must run with bounded worker pools to prevent CPU starvation.
4. **Typed End-to-End Contracts:** Backend Pydantic schemas serve as the single source of truth for frontend API client interfaces.

