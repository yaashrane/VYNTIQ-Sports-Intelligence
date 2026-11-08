# VYNTIQ — Frontend Architecture & Design System Implementation

**Document Reference:** ARCH-FE-VYNTIQ-001  
**Document Version:** 1.0.0 (Prompt 10 Implementation)  
**Parent Product:** VYNTIQ — Sports Intelligence ("Every Metric Tells a Story.")  
**Status:** Approved Architectural Specification  

---

## 1. Overview & Technology Stack

The VYNTIQ presentation layer is a high-density, editorial sports analytics interface engineered with strict architectural discipline. The platform rejects generic SaaS/AI dashboard tropes (random gradients, glowing borders, unnecessary cards, fake statistics) in favor of a scholarly, high-precision sports journal aesthetic.

### Core Stack
- **Framework:** React 19+ (Strict Mode SPA)
- **Language:** TypeScript 5.4+ with `verbatimModuleSyntax`
- **Build Tool:** Vite 8+
- **Styling & Tokens:** Tailwind CSS 3.4+ configured with approved design tokens
- **Routing:** React Router v7
- **Icons:** Lucide React (Disciplined, uniform stroke width of 1.5–2)
- **Testing:** Vitest + React Testing Library + jsdom

---

## 2. Directory & Component Architecture

```
frontend/
├── public/
│   └── favicon.svg
├── src/
│   ├── api/                     # Centralized API layer
│   │   ├── client.ts            # Fetch wrapper with status & error envelope handling
│   │   ├── types.ts             # TypeScript models mirroring backend Pydantic schemas
│   │   ├── workspaces.ts        # Workspace, configuration, dataset, & shortlist endpoints
│   │   └── system.ts            # Health and monitoring endpoints
│   ├── components/
│   │   ├── common/              # Reusable design system primitives
│   │   │   ├── Button.tsx       # Primary magenta, secondary elevated, outline, ghost
│   │   │   ├── StatusBadge.tsx  # Categorical status badges (ACTIVE, DRAFT, APPROVED, etc.)
│   │   │   ├── SearchInput.tsx  # Controlled filter input with clear trigger
│   │   │   ├── LoadingState.tsx # Minimalist non-layout-shifting loader
│   │   │   ├── EmptyState.tsx   # Informative empty states with actionable triggers
│   │   │   ├── ErrorState.tsx   # Structured error banner with retry handlers
│   │   │   └── Modal.tsx        # Accessible dialog backdrop with Esc/click-outside dismiss
│   │   ├── layout/              # Shell and navigation wrappers
│   │   │   ├── ApplicationSidebar.tsx # Brand mark, nav links, coming-soon tags
│   │   │   ├── TopNavigation.tsx      # Breadcrumbs, active workspace selector, API health
│   │   │   └── AppLayout.tsx          # Master shell layout with responsive mobile drawer
│   │   └── workspaces/          # Domain-specific workspace components
│   │       ├── WorkspaceCard.tsx      # Editorial card with competition and status badges
│   │       └── CreateWorkspaceModal.tsx # Workspace creation dialog
│   ├── context/
│   │   └── WorkspaceContext.tsx # Global active workspace selection & sync provider
│   ├── pages/                   # Route-level views
│   │   ├── OverviewPage.tsx     # Executive dashboard (welcome, quick actions, workspaces, data status)
│   │   ├── WorkspacesPage.tsx   # Workspace directory with search and status filters
│   │   ├── WorkspaceDetailPage.tsx # Tabbed view: Configuration, Datasets, Shortlists
│   │   ├── ComingSoonPage.tsx   # Clean placeholders for upcoming modules
│   │   └── NotFoundPage.tsx     # 404 handler
│   ├── test/                    # Frontend test suite
│   │   ├── setup.ts             # Vitest jest-dom setup
│   │   ├── App.test.tsx         # Shell rendering and navigation tests
│   │   └── Workspaces.test.tsx  # Workspace listing, search, empty state, and modal tests
│   ├── App.tsx                  # BrowserRouter and Route declarations
│   ├── main.tsx                 # DOM root mount
│   └── index.css                # Tailwind directives and Manrope/Inter font imports
├── index.html                   # HTML entry point with dark-mode class
├── tailwind.config.js           # Design system tokens configuration
├── tsconfig.json                # TypeScript compiler configuration
└── vite.config.ts               # Vite server and Vitest test configuration
```

---

## 3. Design System & Token Integration

All visual elements conform to `docs/DESIGN_SYSTEM.md`:

```css
/* Core Color Tokens mapped in tailwind.config.js */
surface-ground:   #111318  /* Deep Charcoal background */
surface-card:     #181B22  /* Container card foundation */
surface-elevated: #222630  /* Elevated dropdowns, modals, hover states */
surface-border:   #2D323E  /* 1px subtle dividing hairlines */
text-primary:     #F1EFEA  /* Warm Ivory - editorial headers & high contrast text */
text-secondary:   #9DA3B4  /* Muted slate - labels, metadata, secondary captions */
text-tertiary:    #636B7E  /* Subtle gray - footnotes, disabled states */
accent-magenta:   #D62978  /* Royal Magenta - brand mark & primary actions */
accent-lime:      #B9D66C  /* Sage Lime - positive delta, verified status, active pills */
status-negative:  #E05D52  /* Disqualified, failed, archived states */
status-warning:   #E5A83B  /* Insufficient sample, review alerts */
```

### Typography Hierarchy
- **Headings & Ratings**: `font-display` (`Manrope`, semi-bold to bold).
- **Body & Controls**: `font-sans` (`Inter`, regular to medium).
- **Numerical Alignments**: `tabular-nums` applied across all scores, row counts, and dates to ensure micro-precise vertical decimal alignment.

---

## 4. Routing Table

| Route | Component | Status | Description |
| :--- | :--- | :---: | :--- |
| `/` | `OverviewPage` | **Active** | Primary dashboard: welcome hero, active workspaces grid, data status, quick actions. |
| `/workspaces` | `WorkspacesPage` | **Active** | Workspace directory with live search, status filter pills, and creation modal. |
| `/workspaces/:workspaceId` | `WorkspaceDetailPage` | **Active** | Full sandbox details: Configuration & Rules, Datasets, Shortlists, Archive action. |
| `/players` | `ComingSoonPage` | *Coming Soon* | Unified player database & radar distributions (Scheduled Phase A6). |
| `/shortlists` | `ComingSoonPage` | *In Sandbox* | Shortlists linked within active workspace sandboxes. |
| `/comparisons` | `ComingSoonPage` | *Coming Soon* | Head-to-head multi-player comparison UI (Backend API verified). |
| `/reports` | `ComingSoonPage` | *Track B* | PDF dossiers and raw event lineage manifests. |
| `/settings` | `ComingSoonPage` | *Track B* | Tenant management and platform API keys. |
| `*` | `NotFoundPage` | **Active** | Graceful 404 error page with navigation return action. |

---

## 5. State Management & API Integration

### Workspace Context (`WorkspaceContext.tsx`)
Provides shared state for:
- `workspaces`: Array of workspaces loaded from `GET /api/v1/workspaces`.
- `activeWorkspace`: Currently active workspace across top-navigation dropdown and session views.
- `refreshWorkspaces`: Callback invoked after workspace creation or status mutation.

### API Client (`client.ts`)
- Uses `fetch` with configurable base URL via `VITE_API_BASE_URL` (defaults to `/api/v1` for Vite reverse-proxying to `http://localhost:8000`).
- Translates HTTP errors into typed `ApiException` instances with structured error codes and field-level validation details.

---

## 6. Environment Variables

Create `.env` in `frontend/` if overriding defaults:

```bash
# Target backend API base URL (Default proxy uses /api/v1)
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 7. Testing & Verification

### Running Frontend Tests
```bash
cd frontend
npm run test
```

### Building for Production
```bash
cd frontend
npm run build
```
Generates production-optimized assets in `frontend/dist/`.
