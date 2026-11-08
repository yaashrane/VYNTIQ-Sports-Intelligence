# VYNTIQ — Product Requirements Document (PRD)

**Document Reference:** PRD-VYNTIQ-002  
**Document Version:** 2.0.0 (Post-Architecture Review & Competition MVP Alignment)  
**Status:** Approved Architectural Baseline  

---

## 1. Scope Partitioning: Track A (MVP) vs. Track B (Full Platform)

To ensure delivery for the **SuperRR Selector Season 2** competition (deadline: November 18, 2026) while maintaining architectural foundations for the enterprise platform, every requirement is tagged with its delivery scope:
* `[Track A: Competition MVP]` — Must be implemented, tested, and verified by November 18, 2026.
* `[Track B: Full Platform]` — Post-competition enhancements for the commercial VYNTIQ product.
* `[Track B: Future Extension]` — Long-term multi-sport and advanced tracking capabilities.

---

## 2. Functional Requirements (FR)

### Module 1: Data Ingestion & Flexible Validation Pipeline

* **FR-1.1 Multi-Format File Ingestion `[Track A: Competition MVP]`:**
  * Accept structured CSV and JSON ball-by-ball and match scorecard files via upload.
  * Ingest without hardcoding a proprietary column schema; accommodate naming variations across historical sources (e.g., Cricsheet) and official competition releases (e.g., SuperRR Season 2).
* **FR-1.2 Adaptable Column Mapping & Schema Detection `[Track A: Competition MVP]`:**
  * Inspect source file headers and detect column mappings to VYNTIQ's internal canonical model (e.g., mapping `striker` $\to$ `batter_name`, `bowling_team` $\to$ `bowler_team`).
  * Support user/analyst confirmation of ambiguous column mappings before import.
* **FR-1.3 Two-Tiered Data Validation Gate `[Track A: Competition MVP]`:**
  * **Tier 1 (Structural):** Pydantic v2 validation of field data types, mandatory keys, date parsing, and non-empty rows.
  * **Tier 2 (Cricket Domain Logic):** Verify delivery sequence monotonically increases ($0.1 \dots 19.6$), extras reconcile with total runs, wicket events include dismissal types, and legal ball counts do not exceed over limits (accounting for wides/no-balls).
* **FR-1.4 Quarantine & Diagnostic Error Reporting `[Track A: Competition MVP]`:**
  * Quarantined rows are written to a structured diagnostic log with exact row numbers, field names, and violation reasons.
  * Valid records are committed atomically; invalid records are isolated without aborting the entire dataset if isolated row errors occur.
* **FR-1.5 Data Provenance & Lineage Tagging `[Track A: Competition MVP]`:**
  * Every ingested record is tagged with `workspace_id`, `dataset_origin` (`CANONICAL_HISTORICAL` vs. `COMPETITION_SANDBOX`), upload timestamp, and file checksum hash.
* **FR-1.6 Real-Time Ingestion Progress & Telemetry `[Track B: Full Platform]`:**
  * Visual upload progress bar, batch processing status, and interactive UI column mapper.

---

### Module 2: Player Identity Resolution & Eligibility Filtering

* **FR-2.1 Canonical Entity Resolution `[Track A: Competition MVP]`:**
  * Match player names across varying representations (e.g., "V Kohli", "Virat Kohli", "V. Kohli") using fuzzy matching and a canonical alias registry.
* **FR-2.2 Competition Eligibility Filtering `[Track A: Competition MVP]`:**
  * Filter candidate pools based on competition-specific eligibility rules (e.g., uncapped players, specific age brackets, overseas status, minimum domestic match appearances).
* **FR-2.3 Duplicate Entity Detection & Merge `[Track B: Full Platform]`:**
  * Interactive UI to resolve ambiguous duplicate player records and merge historical aliases.

---

### Module 3: Cricket Feature Engineering & Contextual Metrics

* **FR-3.1 Match-Phase Categorization `[Track A: Competition MVP]`:**
  * Deconstruct all innings deliveries into three standardized T20 phases:
    * **Powerplay:** Overs 0.1 to 5.6 (Overs 1–6)
    * **Middle Overs:** Overs 6.1 to 14.6 (Overs 7–15)
    * **Death Overs:** Overs 15.1 to 19.6 (Overs 16–20)
* **FR-3.2 Standard Ball-by-Ball Metric Extraction `[Track A: Competition MVP]`:**
  * Compute the following core metrics from standard match data:
    * **Batting:** Runs, Balls Faced, Strike Rate, Dismissals, Batting Average, Dot Ball %, Boundary % (4s and 6s), Balls per Boundary, Phase-Specific Strike Rates.
    * **Bowling:** Balls Bowled, Overs Bowled, Runs Conceded, Wickets Taken (excluding run-outs), Economy Rate, Bowling Strike Rate, Dot Ball %, Boundary Conceded %, Phase-Specific Economy Rates.
* **FR-3.3 True Metric Normalization `[Track A: Competition MVP]`:**
  * Compute **True Strike Rate (TSR)**: Difference between a batter's actual strike rate in a phase and the competition average strike rate for that phase and venue.
  * Compute **True Economy Rate (TER)**: Difference between the competition average economy in a phase and the bowler's actual economy in that phase (where positive indicates run suppression).
* **FR-3.4 Tactical Splits (Pace vs. Spin) `[Track A: Competition MVP]`:**
  * Compute performance splits against Pace/Fast bowling vs. Spin bowling for all batters and bowlers where bowler sub-type is available in the dataset.
* **FR-3.5 Advanced Tracking Extensions `[Track B: Future Extension]`:**
  * Pitch maps, wagon-wheel zone distributions, and release speeds *(strictly marked as optional extensions contingent on external tracking data availability; not required for standard ball-by-ball analysis)*.

---

### Module 4: Role-Specific Player Evaluation Framework

* **FR-4.1 Role Archetype Classification `[Track A: Competition MVP]`:**
  * Classify players into distinct primary evaluation cohorts:
    * **Specialist Batter:** Top-Order Anchor, Powerplay Enforcer, Middle-Overs Rotator, Death Overs Finisher.
    * **Specialist Bowler:** Powerplay Strike Bowler, Middle-Overs Spin Enforcer, Death Overs Specialist, Defensive Containment Bowler.
    * **All-Rounder:** Batting All-Rounder (top-7 batter who bowls), Bowling All-Rounder (bowler batting $\ge 8$ with power-hitting capability).
* **FR-4.2 Separate, Role-Specific Evaluation Dimensions `[Track A: Competition MVP]`:**
  * **Batters** evaluated across 6 distinct batting dimensions:
    1. *Scoring Velocity & True Strike Rate (TSR)*
    2. *Boundary Potency (Boundary % & Frequency)*
    3. *Wicket Preservation / Stability (Balls per Dismissal)*
    4. *Dot Ball Suppression (Non-dot delivery %)*
    5. *Phase Adaptability (Powerplay vs Middle vs Death scoring balance)*
    6. *Matchup Neutrality (Pace vs Spin balance)*
  * **Bowlers** evaluated across 6 distinct bowling dimensions:
    1. *Run Prevention & True Economy Rate (TER)*
    2. *Wicket-Taking Threat (Bowling Strike Rate)*
    3. *Dot Ball Dominance (Dot Ball %)*
    4. *Boundary Concession Suppression (Balls per Boundary Conceded)*
    5. *Phase Execution (Powerplay control & Death overs restraint)*
    6. *Tactical Discipline (Extras suppression & consistency)*
  * **All-Rounders:** Evaluated on both batting and bowling dimensions independently; composite score computed via justified balance weighting plus a **Role Balance / Dual-Utility Bonus**.
* **FR-4.3 Role-Adaptive Visual Radar Models `[Track A: Competition MVP]`:**
  * Radar charts must adapt their axes to the player's primary role. Batting axes must never be plotted on a specialist bowler's radar, and vice-versa.

---

### Module 5: Transparent Scoring & Ranking Engine (VOR)

* **FR-5.1 Empirical Normalization (ECDF) `[Track A: Competition MVP]`:**
  * Transform raw metric values into percentile ranks ($0–100$) using the Empirical Cumulative Distribution Function against the player's qualified peer cohort.
  * Explicitly handle directionality (e.g., lower Economy Rate yields a higher normalized score).
* **FR-5.2 Minimum Sample-Size Qualification & Reliability Discounting `[Track A: Competition MVP]`:**
  * Enforce strict minimum thresholds (e.g., minimum 100 balls faced for batters, 120 balls bowled for bowlers).
  * For players meeting the lower boundary ($N_{min}$) but below full reliability threshold ($N_{full}$), apply a Bayesian shrinkage / reliability discount factor $C \in (0, 1]$.
  * Display a prominent "Low Sample Size" disclaimer badge on any profile where $N < N_{full}$.
* **FR-5.3 VYNTIQ Overall Rating (VOR) Composite Computation `[Track A: Competition MVP]`:**
  * Compute composite score as the reliability-adjusted, weighted sum of normalized dimensional scores:
    $$\text{VOR} = C \times \sum_{i=1}^k w_i \times Z_i$$
  * All weights $w_i$ are documented, normalized ($\sum w_i = 1.0$), and configured via transparent, role-specific evaluation presets.
* **FR-5.4 Explainability Cards ("The Story Behind the Metric") `[Track A: Competition MVP]`:**
  * Generate structured factor attribution for every rated player, identifying the top 2 positive drivers and top 2 drag factors relative to the cohort median.
* **FR-5.5 Dynamic Interactive Weight Customization `[Track B: Full Platform]`:**
  * UI sliders allowing analysts to modify dimension weights on the fly with instant client-side leaderboard re-ranking.

---

### Module 6: Player Comparison & Shortlist Management

* **FR-6.1 Head-to-Head Comparison Matrix `[Track A: Competition MVP]`:**
  * Side-by-side comparative table for 2 to 4 candidates within the same role archetype, featuring absolute metric values, cohort percentiles, and clear delta indicators ($+\Delta / -\Delta$).
* **FR-6.2 SuperRR Selector Top 10 Shortlist `[Track A: Competition MVP]`:**
  * Curate, rank, and store the Top 10 recommended candidates for the SuperRR Season 2 competition, with scouting notes and tactical role tags.
* **FR-6.3 Head-to-Head Direct Matchup History `[Track B: Full Platform]`:**
  * Ball-by-ball analysis of historical batter-vs-bowler direct encounters.
* **FR-6.4 Multi-User Shortlist Collaboration `[Track B: Full Platform]`:**
  * Shared shortlist boards with role-based permissions and team annotations.

---

### Module 7: Automated Report Generation & Export

* **FR-7.1 SuperRR Top 10 Submission Report `[Track A: Competition MVP]`:**
  * Compile a comprehensive, audit-ready competition submission dossier (PDF or formatted Markdown/HTML report) presenting the Top 10 candidates, ranking rationale, role fit, metric breakdowns, and data provenance.
* **FR-7.2 Headless Vector PDF Dossier Engine (ReportLab) `[Track B: Full Platform]`:**
  * Fully automated, high-speed vector PDF generator for single-player dossiers and squad scouting binders with embedded vector radar charts.

---

### Module 8: Multi-Tenant Workspace & Sandboxing

* **FR-8.1 Workspace Tenant Scoping `[Track A: Competition MVP]`:**
  * All data mutations, shortlists, and competition uploads are strictly scoped by `workspace_id`.
  * The SuperRR Selector Season 2 environment operates under `workspace_id = 'workspace_super_rr_s2'`.
* **FR-8.2 Workspace Switcher & Access Control `[Track B: Full Platform]`:**
  * UI workspace switcher and multi-tenant authentication with team-level access control.

---

## 3. Non-Functional Requirements (NFR)

### 3.1 Performance & Latency
* **NFR-1.1 Ingestion Throughput `[Track A]`:** Ingest and validate a full multi-season tournament dataset ($\approx 50,000$ deliveries) in $\le 10\text{ seconds}$.
* **NFR-1.2 Query & Ranking Latency `[Track A]`:** Dynamic cohort ranking and player score computation must execute in $\le 500\text{ ms}$.
* **NFR-1.3 UI Responsiveness `[Track B]`:** Page transitions and filter updates in $\le 150\text{ ms}$.

### 3.2 Data Integrity, Auditability & Precision
* **NFR-2.1 Numerical Precision `[Track A]`:** Double precision floating-point storage for all intermediate calculations; rounded to 2 decimal places for display.
* **NFR-2.2 Auditability `[Track A]`:** Every metric must be queryable down to the underlying `delivery_id` records that formed its numerator and denominator.
* **NFR-2.3 Immutability `[Track A]`:** Raw uploaded datasets are preserved in their original state; all transformations occur in derived, versioned analytical tables.

### 3.3 Usability & Editorial Integrity
* **NFR-3.1 Editorial Aesthetics `[Track A & B]`:** Strict adherence to the VYNTIQ design system (Deep Charcoal `#111318`, Royal Magenta `#D62978`, Sage Lime `#B9D66C`, Warm Ivory `#F1EFEA`).
* **NFR-3.2 Zero Visual Clutter `[Track A & B]`:** Tabular numerals (`tabular-nums`) for all data columns, zero generic KPI cards, zero glowing borders, and zero decorative charts without analytical purpose.

---

## 4. Edge Cases & Boundary Conditions

| Scenario | System Handling & Enforcement | Track |
| :--- | :--- | :--- |
| **Micro-Sample Outlier** (e.g., 25 runs off 6 balls, SR = 416.7) | Flagged with a low-sample disclaimer; excluded from top-percentile leaderboards until meeting $N_{min}$; Bayesian shrinkage applied to regress score toward cohort median. | **Track A** |
| **Missing Player Metadata** (e.g., bowling style unknown) | Metric engine continues calculation using available ball-by-ball data; Matchup split defaults to "Unclassified / Unknown" without failing the pipeline. | **Track A** |
| **Super Over Deliveries** | Deliveries with `is_super_over = True` are isolated from standard career/season averages to prevent rate distortion. | **Track A** |
| **Truncated / DLS Matches** | Deliveries are indexed; expected rates for True Metrics use actual balls bowled rather than assuming standard 20-over denominator. | **Track A** |
| **Incomplete Competition Data Release** | Ingestion pipeline accepts partial tournament records, produces diagnostic summaries, and computes metrics on available verified subset. | **Track A** |

---

## 5. Explicit Out-of-Scope Declarations

1. **Computer Vision Video Tracking:** Real-time optical video tracking, biomechanical pose estimation, and player skeletal telemetry are out of scope.
2. **Live In-Stadium WebSockets:** Ingestion occurs batch-wise post-match or via complete tournament datasets; live millisecond-level in-game telemetry feeds are deferred to Version 2.0.
3. **Social Media & Sentiment Analytics:** Social sentiment, fan popularity, and commercial media buzz are strictly excluded. VYNTIQ evaluates on-field performance and tactical value only.
4. **Automated Auction Contract Execution:** The platform provides tactical valuation and scouting dossiers, but does not execute legal contracts or financial transactions.
