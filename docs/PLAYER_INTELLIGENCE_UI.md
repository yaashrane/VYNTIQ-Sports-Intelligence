# VYNTIQ Player Intelligence Interface Specification

**Platform:** VYNTIQ — Sports Intelligence  
**Slogan:** *"Every Metric Tells a Story."*  
**Module:** Player Discovery, Profile Intelligence, and Head-to-Head Comparison UI  
**Phase:** Prompt 11 Implementation  
**Status:** Approved & Verified

---

## 1. Architectural Philosophy & Principles

The Player Intelligence Interface transforms complex statistical models, empirical distributions, Bayesian reliability shrinkages, and multi-dimensional performance profiles into an intuitive, evidence-based exploration experience.

### Core Tenets

1. **Zero Client-Side Calculation (Backend as Single Source of Truth):**
   - No frontend code re-implements, estimates, or recalculates Value Over Replacement (VOR), Empirical Cumulative Distribution Function (ECDF) percentiles, Bayesian shrinkage factors $C(N)$, or tiebreaker ranking orders.
   - All scores, ranking tiers, confidence intervals, and comparison deltas originate deterministically from backend domain services.

2. **Sports Intelligence, Not Generic Dashboard AI:**
   - Strict adherence to the VYNTIQ design system: Deep Charcoal ground (`#111318`), elevated surface (`#181B22`), Royal Magenta primary accent (`#D62978`), Sage Lime secondary accent (`#B9D66C`), and Warm Ivory typography (`#F1EFEA`).
   - High-density tabular representations with tabular-nums formatting (`font-variant-numeric: tabular-nums`).
   - Complete avoidance of AI buzzwords, ungrounded statistical hallucinations, or arbitrary decorative gradients.

3. **Multi-Sport Agnostic Platform Architecture:**
   - The platform application shell is multi-sport capable.
   - Cricket-specific metrics (strike rate, boundary percentage, economy rate, dot ball percentage) are strictly encapsulated in role-adaptive cricket presentation components and discipline adapters.

4. **Transparent Explainability & Mathematical Auditability:**
   - Every evaluated player displays not only their composite VOR score, but the full narrative attribution, top performance strengths, drag factors, and mathematical reconciliation check ensuring the sum of weighted dimension contributions equals the raw composite score within $0.001$ pts.

---

## 2. Player Explorer Interface (`/players`)

The Player Explorer serves as the primary discovery and audit directory for athletes evaluated across competition cohorts.

### Features

- **Global Search & Real-Time Filtering:**
  - Case-insensitive search matching against athlete names or canonical identifiers (`player_id`).
  - Single-click role filtering pills (`All Roles`, `Batters`, `Bowlers`, `All-Rounders`, `Wicketkeepers`).
  - Active role pill highlighted in Royal Magenta (`#D62978`).

- **Multi-Factor Sorting:**
  - Sortable by Rank (`#`), VOR Rating, or Athlete Name.
  - Direction toggling (Ascending / Descending) with visual direction indicators.

- **Sample Adequacy & Quarantine Gating:**
  - Athletes with inadequate match sample sizes (e.g. fewer than 120 balls faced or legal balls bowled) are quarantined from the official leaderboard.
  - Dedicated Quarantine toggle (`Quarantine (N)`) allows analysts to inspect sample-deficient prospects separately without corrupting competitive rankings.

- **Head-to-Head Comparison Drawer:**
  - Interactive selection checkbox for every candidate.
  - Candidate selection state tracks up to 5 concurrent athletes.
  - Dynamic Action Button: `Compare (N) Candidates` triggers seamless transition to `/comparisons?players=P_001,P_002`.

### Column Data Mapping

| Column | Data Field | Display Format | Notes |
| :--- | :--- | :--- | :--- |
| **Compare** | `player_id` | Checkbox | Toggles comparison queue (max 5) |
| **Rank** | `rank` | `#1`, `#2`, ... | Tiebroken rank from scoring engine |
| **Athlete** | `player_name` | Name link | Navigates to `/players/:playerId` |
| **Role** | `role` | Pill badge | E.g., `BATTER`, `BOWLER`, `ALL_ROUNDER` |
| **VOR Rating** | `vor_score` | `88.5` | Bayesian-shrunk composite VOR score |
| **Raw Composite** | `raw_composite_score` | `89.2` | Pre-shrinkage percentile composite |
| **Reliability $C(N)$** | `reliability_factor` | `0.99 (ADEQUATE)` | Color-coded reliability status |
| **Tiebreaker** | `primary_tiebreaker` | `91.20` | Secondary metric for ranking resolution |
| **Eligibility** | `is_eligible` | Shield badge | Rule-based competition eligibility |

---

## 3. Player Profile Experience (`/players/:playerId`)

The Player Profile delivers an exhaustive, evidence-backed dossier of an individual candidate's evaluation run.

### Page Sections

```
+-----------------------------------------------------------------------------------+
| Back to Explorer | Player Name [Role Badge] [Status Badge] | [Compare Player Button] |
| ID: P_001 | Cohort: IPL_T20_2024 | Nationality: India | DOB: 1994-11-11           |
+---------------------------------------------------+-------------------------------+
| LEFT COLUMN (2 Cols)                              | RIGHT COLUMN (1 Col)          |
| 1. Composite Rating & Bayesian Reliability        | Role Dimension Profile        |
|    - VOR Score (88.5) vs Raw Composite (89.2)     | - Pure SVG Radar Chart        |
|    - Reliability Factor C(N): 0.99 (ADEQUATE)     |   Concentric Rings (25-100)   |
|    - Scoring Engine Version: v1.0.0               |   Role-adaptive axes          |
| 2. Sample Workload & Event Counts                 | - Tabular Dimension Table     |
|    - Batter: Balls Faced, Dismissals              |   Dimension Name              |
|    - Bowler: Legal Balls, Wickets                 |   Percentile / Applied Weight |
|    - Dataset ID & Eligibility Status              |                               |
| 3. "The Story Behind the Metric" (Explainability) |                               |
|    - Narrative summary of player profile          |                               |
|    - Primary Strengths (Sage Lime badges)         |                               |
|    - Performance Drag Factors (Warning badges)    |                               |
|    - Mathematical Reconciliation Audit Status     |                               |
|      (Discrepancy: 0.000 pts -> RECONCILED)       |                               |
+---------------------------------------------------+-------------------------------+
```

### Role-Adaptive Pure SVG Radar Chart (`RoleRadarChart.tsx`)

- **Rendering Technology:** Pure SVG without heavy third-party charting libraries (Recharts/Chart.js) for instantaneous load times and zero hydration mismatch.
- **Coordinate Geometry:**
  $$\theta_i = i \cdot \frac{2\pi}{N} - \frac{\pi}{2}, \quad r_i = \left(\frac{\text{score}_i}{100}\right) \cdot R$$
  $$x_i = C_x + r_i \cdot \cos(\theta_i), \quad y_i = C_y + r_i \cdot \sin(\theta_i)$$
- **Concentric Grid Levels:** 4 calibrated rings at $25, 50, 75, 100$ percentiles.
- **Accessibility:** Accompanied by an accessible tabular fallback listing dimensions, normalized percentile scores, and applied evaluation weights.

---

## 4. Head-to-Head Comparison UI (`/comparisons`)

The Comparison Engine allows scouts and analysts to compare 2 to 5 candidates side-by-side with statistical rigor.

### Safeguards & Cross-Role Compatibility

> [!WARNING]
> **Cross-Role Safeguard Enforced:** When comparing players across differing tactical roles (e.g., a Batter vs a Bowler), the comparison engine enforces strict statistical boundaries:
> 1. Displays a prominent warning banner: `Cross-Role Statistical Advisory (CROSS_ROLE_PARTIAL)`.
> 2. Direct VOR equivalence is suppressed (`vor_comparison_valid: false`).
> 3. Individual performance metrics are partitioned by discipline (Batting metrics compared separately from Bowling metrics).

### Comparison Matrix Breakdown

1. **Candidate Header Cards:**
   - Side-by-side cards displaying athlete name, role, VOR score, and reliability status.
   - For compatible roles, the top-rated candidate receives the `VOR Leader` badge.
2. **Role Dimension Matrix:**
   - Displays shared dimension scores across candidates.
   - Computes score differentials (`score_difference`) and identifies the dimension leader (`Leader: Athlete Name`).
3. **Discipline Performance Metrics:**
   - Directionality-aware advantage attribution:
     - `HIGHER_IS_BETTER` (e.g. Strike Rate, Average): Higher value receives the Sage Lime advantage badge.
     - `LOWER_IS_BETTER` (e.g. Economy Rate, Bowling Average): Lower value receives the Sage Lime advantage badge.
     - Displays absolute metric difference and favorable player attribution.

---

## 5. API Integration Mapping

| UI Component | Backend Endpoint | HTTP Method | Payload / Response |
| :--- | :--- | :--- | :--- |
| **Player Explorer** | `/api/v1/scoring/rankings` | `GET` | `RankingResponse` (rankings, quarantined) |
| **Player Bio** | `/api/v1/players/{id}` | `GET` | `PlayerMaster` (nationality, dob, active status) |
| **Player Score** | `/api/v1/scoring/players/{id}` | `GET` | `PlayerScoreResult` (VOR, dimensions, C(N)) |
| **Explainability** | `/api/v1/explainability/players/{id}` | `GET` | `PlayerDetailedExplanation` (strengths, narrative) |
| **Audit Breakdown** | `/api/v1/explainability/players/{id}/breakdown` | `GET` | `PlayerScoreBreakdown` (discrepancy, reconciled) |
| **Comparison Run** | `/api/v1/comparisons/players` | `POST` | `PlayerComparisonResponse` (deltas, leaders) |
| **Engine Metadata** | `/api/v1/comparisons/metadata` | `GET` | `ComparisonMetadataResponse` (rules, directions) |

---

## 6. Verification & Test Suite Status

- **Frontend Tests (`Vitest`):**
  - `src/test/Players.test.tsx` (4 tests):
    - `PlayerExplorerPage renders player list, filtering, and comparison selection` (PASSED)
    - `PlayerProfilePage renders complete evaluation, bio, explainability, and radar dimensions` (PASSED)
    - `PlayerComparisonPage enforces cross-role warning when incompatible roles are compared` (PASSED)
    - `PlayerComparisonPage renders side-by-side metrics and dimension leaders for compatible roles` (PASSED)
  - Full suite: **10 tests passed across 3 test files**.
  - Production build: `npm run build` completed cleanly in **1.62s** with 0 errors.

- **Backend Tests (`Pytest`):**
  - Full backend suite: **89 tests passed** with zero regressions.
