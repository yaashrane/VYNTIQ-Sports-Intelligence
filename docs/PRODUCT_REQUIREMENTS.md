# VYNTIQ — Product Requirements Document (PRD)

**Document Reference:** PRD-VYNTIQ-001  
**Target Release:** Version 1.0 (Cricket & SuperRR Workspace Release)  
**Status:** Architecture Baseline  

---

## 1. Functional Requirements (FR)

### Module 1: Player Database & Discovery Engine
* **FR-1.1 Universal Search & Retrieval:** Support sub-second search by athlete name, nationality, primary role, bowling style, batting handedness, current franchise/team, and age range.
* **FR-1.2 Faceted Multi-Dimensional Filter:**
  * Role filters: Specialist Batter, Top-Order Anchor, Powerplay Striker, Middle-Overs Finisher, All-Rounder (Batting/Bowling bias), Pace Bowler (Express, Hit-the-Deck, Swing), Spin Bowler (Wrist, Finger, Mystery), Wicketkeeper-Batter.
  * Quantitative slider thresholds: Minimum innings, minimum balls bowled/faced, minimum strike rate, maximum economy, boundary % threshold, dot ball % ceiling.
  * Era & Competition filters: Filter by specific tournaments (e.g., IPL 2021–2024, Domestic T20, International T20) or date ranges.
* **FR-1.3 Cohort Benchmarking:** Enable dynamic cohort definition (e.g., "Middle-order batters facing >= 150 balls of spin in overs 7–15 between 2022 and 2024") and compute on-the-fly percentile ranks across all discovery metrics.
* **FR-1.4 Data Lineage Tagging:** Every player record must clearly display its underlying data source (Canonical Historical Database vs. Workspace Uploaded Dataset).

### Module 2: Historical Performance Analytics & Split Engine
* **FR-2.1 Match-Phase Splits:** Deconstruct career and season performance into granular cricket phases:
  * Batting & Bowling in **Powerplay (Overs 1–6)**
  * Batting & Bowling in **Middle Overs (Overs 7–15)**
  * Batting & Bowling in **Death Overs (Overs 16–20)**
* **FR-2.2 Tactical Splits & Matchups:**
  * Pace vs. Spin breakdowns (Average, Strike Rate, Dot Ball %, Boundary %, Dismissal type).
  * First Innings vs. Second Innings (Chasing pressure index).
  * Home vs. Away / Specific venue clusters (Pace-friendly, Spin-friendly, High-altitude scoring venues).
* **FR-2.3 Temporal Trajectory & Form Curves:** Rolling 5-match and 10-match weighted moving averages for performance index to detect rising talent vs. declining trends.

### Module 3: Player Performance Profiles
* **FR-3.1 Identity & Metadata Card:** Player biodata (DOB, current age, height, playing arm, domestic team, international caps, contract tier).
* **FR-3.2 Multi-Dimensional Capability Radar:** 6-axis visual and statistical footprint normalized to cohort deciles:
  * Batting: *Explosiveness (Strike Rate/Boundary %)*, *Stability (Balls per Dismissal)*, *Phase Adaptability*, *Spin Dominance*, *Pace Dominance*, *Finishing Leverage*.
  * Bowling: *Wicket-Taking Threat (Strike Rate)*, *Control (Dot Ball % & Economy)*, *Powerplay Restraint*, *Death Execution (Yorker/Hard Length Efficiency)*, *Matchup Neutrality*, *Discipline (Extras per ball)*.
* **FR-3.3 Shot & Delivery Distribution:** Aggregated heatmaps and zone distributions (e.g., wagon wheel zones, pitch length & line distributions where tracking data is available).
* **FR-3.4 Metric Detail Table with Tabular Numerals:** High-density, precision-formatted data grid featuring sortable, search-filtered historical season-by-season rows.

### Module 4: Role-Specific Evaluation Engines

#### 4.1 Batting Evaluation Metrics
* **True Strike Rate (TSR):** Strike rate adjusted for match phase run rate baseline and venue scoring index:
  $$\text{TSR} = \text{Actual SR} - \text{Expected Phase SR}_{\text{venue, phase}}$$
* **Boundary Percentage (BP):** $(\text{Fours} \times 4 + \text{Sixes} \times 6) / \text{Total Runs} \times 100$ and Boundary frequency (Balls per Boundary).
* **Dot Ball Suppression (DBS):** Percentage of non-scoring deliveries faced ($100 - \text{Dot \%}$).
* **Clutch Finishing Index (CFI):** Scoring velocity in high-leverage death overs (16–20) when required run rate $\ge 9.5$.

#### 4.2 Bowling Evaluation Metrics
* **True Economy Rate (TER):** Economy rate adjusted for phase baselines:
  $$\text{TER} = \text{Expected Phase Economy}_{\text{venue, phase}} - \text{Actual Economy}$$
* **Wicket Threat Index (WTI):** Weighted dismissal efficiency adjusted for quality of dismissed batter (Top 1–3 vs. Tailenders).
* **Dot Ball Dominance (DBD):** Pure dot ball percentage across primary bowling spells.
* **Pressure Bowler Rating (PBR):** Economy and boundary concession rate under high leverage index scenarios.

#### 4.3 All-Rounder Evaluation Metrics
* **Net Value Contribution (NVC):** Balanced metric harmonizing Batting Run Value added vs. Bowling Run Value saved relative to replacement player.
* **Role Balance Coefficient:** Quantifies whether a player is a genuine dual-threat or a single-discipline specialist with secondary utility.

### Module 5: Player Comparison & Head-to-Head Matrix
* **FR-5.1 Multi-Player Side-by-Side (2 to 4 Players):** Direct metric-by-metric comparison table with absolute values, percentile rankings, and dynamic delta indicators ($+\Delta / -\Delta$).
* **FR-5.2 Overlaid Polygon Radar Comparison:** Multi-color overlaid radar visual allowing visual gap analysis across identical metric axes.
* **FR-5.3 Direct Head-to-Head Matchup Breakdown:** Historical head-to-head encounters between specific batter and bowler (balls faced, runs scored, strike rate, dismissals, dot ball count).

### Module 6: Statistical Scoring & Explainable Ranking Engine
* **FR-6.1 VYNTIQ Overall Rating (VOR):** 0–100 normalized composite score computed from weighted dimensional sub-scores.
* **FR-6.2 Weighting Customization Presets:** Ability for analysts to apply role-specific evaluation templates:
  * Preset A: *High-Impact T20 Disruptor* (80% weight on Boundary % and True SR).
  * Preset B: *Reliable Middle-Order Builder* (60% weight on Stability/Rotational Strike Rate).
  * Preset C: *Death Overs Specialist Bowler* (75% weight on Overs 16–20 Economy and Dot %).
  * Preset D: *Custom User-Defined Weights* with immediate client-side re-indexing.
* **FR-6.3 Explainability Cards (The "Story Behind the Metric"):**
  * Every score provides a deconstruction drawer explaining:
    1. Primary positive contributors (e.g., "+8.4 pts: Elite Death SR in top 2% of league").
    2. Primary drag factors (e.g., "-4.2 pts: Below median dot-ball % against left-arm spin").
    3. Underlying sample size ($N$ matches, $B$ balls) with statistical confidence interval.

### Module 7: Dataset Ingestion & Validation Pipeline
* **FR-7.1 Multi-Format Ingestion:** Support structured CSV and JSON ball-by-ball and match-summary dataset uploads.
* **FR-7.2 Ingestion Gate & Strict Schema Validation:**
  * Automatic schema verification using strict Pydantic definitions.
  * Validation rules: Check for missing delivery IDs, illegal ball counts, negative run values, non-existent player IDs, duplicate deliveries.
  * Immediate rejection or quarantine of corrupted files with an explicit validation error log (row number, field name, validation rule violated).
* **FR-7.3 Data Segregation & Deduplication:** Uploaded datasets can be tagged as:
  * Canonical Baseline (system-wide, admin only).
  * Workspace Sandbox (isolated to a specific competition/team project).

### Module 8: Shortlist & Scouting Workflow Management
* **FR-8.1 Custom Dynamic Shortlists:** Users can create named shortlists (e.g., "Target Overseas Quick Options - 2025", "Under-23 Spin Prospects").
* **FR-8.2 Scouting Dossier Annotations:** Secure analyst notes, scouting tags (e.g., "High Ceiling", "Medical Flag", "Auction Target"), and priority grading (Tier 1, Tier 2, Watchlist).
* **FR-8.3 Exportable Roster Profiles:** Quick export of shortlist summaries to CSV, JSON, and PDF.

### Module 9: Automated PDF Scouting Dossiers (ReportLab Engine)
* **FR-9.1 Headless Vector PDF Generation:** Fully automated, server-side compilation of multi-page PDF scouting dossiers.
* **FR-9.2 Editorial Document Layout:**
  * Page 1: Executive Summary, Player Hero Card, Biographical Summary, Key Ratings, Headline Narrative.
  * Page 2: Phase-of-Play Breakdown, Tactical Splits (Pace vs Spin), Detailed Form Guide.
  * Page 3: Visual Radar Chart, Historical Season Trends, Explainable Factor Attribution, Recommendation Verdict.
* **FR-9.3 High-Resolution Chart Rendering:** Seamless injection of vector or high-DPI rasterized charts matching the VYNTIQ design palette.
* **FR-9.4 Batch Export:** Ability to generate an aggregated competition scouting binder (multi-player consolidated dossier) in a single operation.

### Module 10: Multi-Tenant Workspace & Competition Isolation
* **FR-10.1 Workspace Sandboxing:** Each workspace (e.g., `workspace_super_rr_s2`, `workspace_global_scout`) operates in logical data isolation.
* **FR-10.2 Custom Workspace Attributes:** Workspaces can define their own specific squad rules (e.g., Overseas limits, Purse caps, Role balance minimums).
* **FR-10.3 Brand Separation:** The SuperRR Selector workspace is strictly a workspace instance; the host UI remains VYNTIQ.

---

## 2. Non-Functional Requirements (NFR)

### 2.1 Performance & Latency
* **NFR-1.1 API Response Times:** Standard analytical queries and player profiles must return in $\le 200\text{ ms}$ (p95) for cached/indexed data, and $\le 1.5\text{ s}$ for dynamic cohort recalculations.
* **NFR-1.2 Ingestion Throughput:** Processing and validating a full season of ball-by-ball deliveries ($\approx 15,000$ balls) must complete within $\le 5\text{ seconds}$.
* **NFR-1.3 PDF Generation Speed:** A 3-page comprehensive player scouting dossier must compile in $\le 2.5\text{ seconds}$.

### 2.2 Data Integrity, Lineage & Precision
* **NFR-2.1 Precision Standards:** All floating-point rates (strike rates, economy) must be computed with double precision and rounded to 2 decimal places for display.
* **NFR-2.2 Auditability & Provenance:** Every metric card displayed on the UI must be queryable via an audit API endpoint returning the raw list of delivery IDs that formed the numerator and denominator.
* **NFR-2.3 Immutability:** Historical canonical match records are immutable; corrections create versioned revisions.

### 2.3 Usability & Design Integrity
* **NFR-3.1 Editorial Layout Rigor:** Clean visual hierarchy, zero clutter, tabular numeral alignment for all statistical tables, high-contrast readability in both ambient lighting and dark environments.
* **NFR-3.2 Responsive Behavior:** Full functionality on desktop displays ($\ge 1280\text{px}$) and read-only / scouting-review readiness on tablets and mobile devices ($\ge 768\text{px}$).

### 2.4 Security & Access Control
* **NFR-4.1 Workspace Isolation:** Row-Level Security (RLS) or explicit workspace tenancy scoping on all database queries preventing cross-workspace data leakage.
* **NFR-4.2 Input Sanitization:** Strict prevention of SQL injection, XSS, and payload tampering across all file upload and query endpoints.

---

## 3. Edge Cases & Boundary Conditions

| Edge Case | Description | System Handling & Enforcement |
| :--- | :--- | :--- |
| **Micro-Sample Noise** | Batter scores 24 runs off 6 balls in 1 match ($SR = 400$). | System displays a **"Low Sample Size"** badge ($N < \text{threshold}$). Metric is disqualified from top-percentile leaderboards until reaching minimum ball/over qualification. |
| **Missing Ball-by-Ball Tracking Data** | Older domestic games only have aggregate scorecard summaries without ball-by-ball records. | Metric calculation engine gracefully falls back to aggregate scorecard computations; Phase-of-play splits display an explicit "Data Unavailable for Match Format" state. |
| **Super Over Deliveries** | Deliveries occurring in Super Overs / Tie-breakers. | Deliveries are tagged as `is_super_over=True`. Excluded from standard career averages by default to avoid metric distortion; viewable under a "Super Over / High Pressure" toggle. |
| **Rain-Affected / DLS Adjusted Matches** | Matches truncated by weather where team run rates skew artificially high. | Normalization engine flags `dls_affected=True` and calculates expected rates using adjusted target par rates rather than raw 20-over denominators. |
| **Dual Role Reclassifications** | Player transitioned from top-order batter to finishing bowler across seasons. | Role archetypes are computed per-season and per-competition cohort, not pinned permanently to lifetime career tags. |

---

## 4. Out-of-Scope Declarations (Version 1.0)

1. **Computer Vision Video Tracking:** Real-time video optical tracking or pose estimation (VYNTIQ ingests structured telemetry, event logs, and tabular data, not raw broadcast video feeds).
2. **Live In-Play In-Game Streaming Updates:** Ingestion occurs post-match or via completed innings datasets; sub-second live in-stadium ball-by-ball streaming is deferred to Version 2.0.
3. **Public Social Media Sentiment Analytics:** Sentiment analysis of fan tweets/posts is out of scope; VYNTIQ is purely a sports performance and tactical scouting intelligence platform.
4. **Automated Contract Legal Negotiation:** The platform calculates recruitment value and auction strategy, but does not provide legal contract execution or player agency tooling.

