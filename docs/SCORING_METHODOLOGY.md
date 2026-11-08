# VYNTIQ — Scoring Methodology & Evaluation Framework

**Document Reference:** METHOD-VYNTIQ-001  
**Document Version:** 1.0.0  
**Status:** Approved Architectural Baseline  

---

## 1. Overview & Core Philosophy

VYNTIQ's evaluation framework is founded on the principle that **"Every Metric Tells a Story."** In professional sports scouting, raw unadjusted statistics (e.g., career batting average, overall strike rate, aggregate economy) routinely fail because they ignore:
1. **Match Phase Context:** Scoring 24 runs off 12 balls in the Death overs (16–20) is vastly different from scoring 24 runs off 12 balls in the Powerplay (1–6).
2. **Scoring Environment & Venue Factors:** An economy of 8.5 at a high-scoring batting venue (e.g., Chinnaswamy or Wankhede) represents elite run suppression, whereas an economy of 8.5 on a turning pitch represents poor control.
3. **Sample Size Reliability:** An unproven player with a strike rate of 220 across 15 balls cannot be treated as statistically equivalent to an established performer with a strike rate of 155 across 300 balls.

To eliminate subjective scouting bias and opaque "black-box" ML predictions, VYNTIQ establishes a **four-stage transparent evaluation pipeline**:
$$\text{Raw Event Data} \longrightarrow \text{Contextual Features} \longrightarrow \text{ECDF Normalization} \longrightarrow \text{Reliability-Adjusted Composite (VOR)}$$

---

## 2. Standard Cricket Metric Definitions & Specifications

Every metric below is evaluated on whether it can be computed from **standard ball-by-ball data** (runs, balls, extras, dismissals, bowler styles). Tracking-dependent metrics (wagon wheels, pitch maps) are explicitly isolated as optional extensions.

### 2.1 Batting Metrics

#### M-BAT-01: Strike Rate (SR)
* **Formula:**
  $$\text{SR} = \left( \frac{\text{Runs Scored by Batter}}{\text{Balls Faced (excluding Wides)}} \right) \times 100$$
* **Required Source Fields:** `runs_batter`, `extras_type` (to exclude `wides`).
* **Interpretation:** Baseline scoring velocity per 100 legal deliveries.
* **Directionality:** **Higher is Better**.
* **Calculable from Standard Ball-by-Ball:** **Yes**.
* **Limitations:** Does not adjust for match phase, ground size, or target par score.

#### M-BAT-02: True Strike Rate (TSR)
* **Formula:**
  $$\text{TSR} = \text{Actual SR}_{\text{player, phase}} - \text{Expected SR}_{\text{cohort, phase, venue}}$$
  where $\text{Expected SR}_{\text{cohort, phase, venue}}$ is the average strike rate of all batters in that specific phase (Powerplay, Middle, Death) at that venue during the tournament cohort.
* **Required Source Fields:** `runs_batter`, `over_delivery`, `venue_name`, `extras_type`.
* **Interpretation:** Net scoring acceleration relative to match context. A TSR of $+18.5$ means the batter scores 18.5 runs faster per 100 balls than an average peer facing the identical phase and pitch conditions.
* **Directionality:** **Higher is Better**.
* **Calculable from Standard Ball-by-Ball:** **Yes**.
* **Limitations:** Requires adequate match volume at the venue to compute a stable venue-phase baseline par.

#### M-BAT-03: Boundary Percentage (BP) & Frequency
* **Formula:**
  $$\text{Boundary \% (Runs)} = \left( \frac{(\text{Fours} \times 4) + (\text{Sixes} \times 6)}{\text{Total Runs Scored}} \right) \times 100$$
  $$\text{Balls per Boundary} = \frac{\text{Balls Faced}}{\text{Fours} + \text{Sixes}}$$
* **Required Source Fields:** `runs_batter`, `extras_type`.
* **Interpretation:** Ability to penetrate the field and clear the boundary ropes; critical indicator of boundary-hitting potency in modern T20.
* **Directionality:** **Higher is Better** for Boundary %; **Lower is Better** for Balls per Boundary.
* **Calculable from Standard Ball-by-Ball:** **Yes**.
* **Limitations:** High boundary % accompanied by excessive dot ball % can lead to inefficient innings momentum.

#### M-BAT-04: Dot Ball Suppression (DBS)
* **Formula:**
  $$\text{Dot Ball \%} = \left( \frac{\text{Deliveries Faced with 0 Batter Runs (excluding Wides)}}{\text{Total Balls Faced}} \right) \times 100$$
  $$\text{DBS} = 100 - \text{Dot Ball \%}$$
* **Required Source Fields:** `runs_batter`, `extras_type`.
* **Interpretation:** Measures strike rotation and ability to avoid wasted deliveries.
* **Directionality:** **Higher is Better** for DBS (Non-Dot %); **Lower is Better** for Dot Ball %.
* **Calculable from Standard Ball-by-Ball:** **Yes**.
* **Limitations:** Does not differentiate between a defensive block and an aggressive swing-and-miss.

#### M-BAT-05: Balls per Dismissal (BPD) / Batting Stability
* **Formula:**
  $$\text{BPD} = \frac{\text{Balls Faced}}{\max(1, \text{Times Dismissed})}$$
* **Required Source Fields:** `is_wicket`, `dismissed_player_name`.
* **Interpretation:** Measures wicket preservation and stability at the crease.
* **Directionality:** **Higher is Better**.
* **Calculable from Standard Ball-by-Ball:** **Yes**.
* **Limitations:** Can reward selfish accumulation if strike rate is sacrificed.

---

### 2.2 Bowling Metrics

#### M-BWL-01: Economy Rate (ECON)
* **Formula:**
  $$\text{ECON} = \left( \frac{\text{Runs Conceded by Bowler}}{\text{Legal Deliveries Bowled}} \right) \times 6$$
  *(Runs Conceded includes batter runs, wides, and no-balls; excludes byes and leg-byes).*
* **Required Source Fields:** `runs_batter`, `extras_runs`, `extras_type`, `over_delivery`.
* **Interpretation:** Raw run containment per 6 legal balls.
* **Directionality:** **Lower is Better**.
* **Calculable from Standard Ball-by-Ball:** **Yes**.
* **Limitations:** Penalizes bowlers tasked exclusively with high-scoring Death overs (16–20).

#### M-BWL-02: True Economy Rate (TER)
* **Formula:**
  $$\text{TER} = \text{Expected Economy}_{\text{cohort, phase, venue}} - \text{Actual Economy}_{\text{bowler, phase}}$$
* **Required Source Fields:** `runs_batter`, `extras_runs`, `over_delivery`, `venue_name`.
* **Interpretation:** Net run suppression relative to match phase difficulty. A TER of $+1.80$ means the bowler concedes 1.80 fewer runs per over than an average bowler in the identical phase and venue.
* **Directionality:** **Higher is Better** (Positive denotes superior run suppression).
* **Calculable from Standard Ball-by-Ball:** **Yes**.
* **Limitations:** Sensitive to small over samples at rare venues.

#### M-BWL-03: Bowling Strike Rate (BSR)
* **Formula:**
  $$\text{BSR} = \frac{\text{Legal Deliveries Bowled}}{\max(1, \text{Wickets Taken by Bowler})}$$
  *(Wickets credited to bowler exclude run-outs, timed-out, and retired out).*
* **Required Source Fields:** `is_wicket`, `dismissal_kind`.
* **Interpretation:** Frequency of taking wickets (deliveries needed per dismissal).
* **Directionality:** **Lower is Better**.
* **Calculable from Standard Ball-by-Ball:** **Yes**.
* **Limitations:** Volatile over small sample sizes.

#### M-BWL-04: Bowling Dot Ball Percentage (B-Dot %)
* **Formula:**
  $$\text{B-Dot \%} = \left( \frac{\text{Legal Deliveries with 0 Runs Conceded}}{\text{Legal Deliveries Bowled}} \right) \times 100$$
* **Required Source Fields:** `runs_batter`, `extras_runs`, `extras_type`.
* **Interpretation:** Direct pressure creation through consecutive non-scoring deliveries.
* **Directionality:** **Higher is Better**.
* **Calculable from Standard Ball-by-Ball:** **Yes**.
* **Limitations:** Bowlers who bowl dot balls followed by boundaries may have deceptive figures.

#### M-BWL-05: Balls per Boundary Conceded (BBC)
* **Formula:**
  $$\text{BBC} = \frac{\text{Legal Deliveries Bowled}}{\text{Fours Conceded} + \text{Sixes Conceded}}$$
* **Required Source Fields:** `runs_batter`.
* **Interpretation:** Resistance to boundary concession under attack.
* **Directionality:** **Higher is Better**.
* **Calculable from Standard Ball-by-Ball:** **Yes**.
* **Limitations:** Does not differentiate between a misfield boundary and a clean strike.

---

### 2.3 Advanced Contextual Metrics & Optional Extensions

#### M-CTX-01: Wicket Threat Index (WTI) `[Track A: Provisional]`
* **Formula:**
  $$\text{WTI} = \frac{\sum (\text{Wicket}_i \times \text{Batter Quality Weight}_i)}{\text{Overs Bowled}}$$
  * Batter Quality Weight: Top 1–3 batter = $1.5$, Middle 4–6 = $1.0$, Tailender 7–11 = $0.6$.
* **Required Source Fields:** `is_wicket`, `dismissal_kind`, `batting_order_position`.
* **Interpretation:** Rewards dismissing elite top-order batters over tailenders.
* **Calculable from Standard Ball-by-Ball:** **Yes**, if batting order is preserved.

#### M-CTX-02: Clutch Death Overs Scoring Index (CFI) `[Track A: Standard]`
* **Formula:** True Strike Rate strictly in overs 16–20 under required run rate $\ge 9.5$.
* **Calculable from Standard Ball-by-Ball:** **Yes**.

#### M-CTX-03: Pitch Length / Wagon Wheel Metrics `[Track B: Optional Extension]`
* **Status:** **OPTIONAL EXTENSION**. Pitch map coordinates, line/length clusters, and wagon wheel shot zones depend on optical tracking data. They are **NOT** assumed to be present in the standard competition dataset release.

---

## 3. Role-Specific Evaluation Dimensions

To prevent misleading comparisons (e.g., grading a death-overs bowler on boundary hitting), players are evaluated strictly across **role-appropriate dimensions**:

```
┌────────────────────────────────────────────────────────────────────────┐
│ BATTER EVALUATION DIMENSIONS (6 AXES)                                  │
├────┬─────────────────────────────┬─────────────────────────────────────┤
│ D1 │ Scoring Velocity            │ True Strike Rate (TSR) overall      │
│ D2 │ Boundary Potency            │ Boundary % and Balls per Boundary   │
│ D3 │ Stability / Preservation    │ Balls per Dismissal (BPD)           │
│ D4 │ Dot Ball Suppression        │ Non-Dot Ball % (100 - Dot %)        │
│ D5 │ Phase Adaptability          │ Harmonic mean of PP, Mid, Death SR  │
│ D6 │ Matchup Neutrality          │ Balance ratio: min(SR_pace, SR_spin)│
└────┴─────────────────────────────┴─────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ BOWLER EVALUATION DIMENSIONS (6 AXES)                                  │
├────┬─────────────────────────────┬─────────────────────────────────────┤
│ D1 │ Run Prevention              │ True Economy Rate (TER) overall     │
│ D2 │ Wicket Threat               │ Bowling Strike Rate (BSR)           │
│ D3 │ Pressure & Control          │ Dot Ball % Conceded                 │
│ D4 │ Boundary Suppression        │ Balls per Boundary Conceded (BBC)   │
│ D5 │ Phase Execution             │ Phase True Economy (PP / Death)     │
│ D6 │ Tactical Discipline         │ Inverse Extras Rate (Wides/NB per B)│
└────┴─────────────────────────────┴─────────────────────────────────────┘
```

---

## 4. Normalization Methodology (ECDF)

Raw metrics cannot be summed directly because units and distributions differ (e.g., Strike Rate $\approx 140$, Economy $\approx 8.2$). VYNTIQ employs **Empirical Cumulative Distribution Function (ECDF)** percentile normalization against the defined qualified peer cohort.

### 4.1 Directional Percentile Scaling
For any metric value $x$ of player $i$ within a cohort $X = \{x_1, x_2, \dots, x_M\}$:

1. **For "Higher is Better" Metrics (e.g., TSR, Boundary %, Dot Ball Suppression, BBC):**
   $$Z_i = \left( \frac{\sum_{j=1}^M \mathbf{1}_{x_j \le x_i}}{M} \right) \times 100$$
2. **For "Lower is Better" Metrics (e.g., Economy, Bowling Strike Rate, Dot % Faced):**
   $$Z_i = \left( \frac{\sum_{j=1}^M \mathbf{1}_{x_j \ge x_i}}{M} \right) \times 100$$

This guarantees that for every dimension:
* $Z_i \in [0.0, 100.0]$
* $100.0$ always represents the elite 99th+ percentile performer.
* $50.0$ represents the cohort median.

---

## 5. Sample Size Qualification & Bayesian Reliability Adjustment

A major statistical hazard in sports analytics is the **micro-sample anomaly** (e.g., a batter facing 8 balls in 1 match with a strike rate of 250).

### 5.1 Sample Size Qualification Thresholds
* **Batting Minimum ($N_{min}^{bat}$):** 60 legal balls faced in the cohort.
* **Batting Full Reliability ($N_{full}^{bat}$):** 180 legal balls faced in the cohort.
* **Bowling Minimum ($N_{min}^{bowl}$):** 72 legal balls (12 overs) bowled in the cohort.
* **Bowling Full Reliability ($N_{full}^{bowl}$):** 180 legal balls (30 overs) bowled in the cohort.

### 5.2 Reliability Discount Factor ($C$)
If a player has $N < N_{min}$, they are **quarantined from top-ranked leaderboards** and flagged as `INSUFFICIENT_SAMPLE`.

For players with $N_{min} \le N < N_{full}$, a continuous Bayesian reliability factor $C \in (0, 1]$ is applied:
$$C(N) = \frac{N}{N + K}$$
where $K$ is a shrinkage constant set to $K = \frac{N_{min}}{2}$.

This mathematically regresses the player's final composite rating toward the cohort median ($50.0$), penalizing small-sample volatility while acknowledging strong early indicators.

---

## 6. VYNTIQ Overall Rating (VOR) Composite Computation

The final VYNTIQ Overall Rating (VOR) is computed as:
$$\text{VOR} = 50.0 + C(N) \times \left( \sum_{k=1}^6 w_k Z_k - 50.0 \right)$$
where:
* $Z_k \in [0, 100]$ are the ECDF normalized dimension scores.
* $w_k$ are the role preset weights ($\sum w_k = 1.0$).
* $C(N) \in (0, 1]$ is the reliability discount factor.

### 6.1 Configurable Role Presets (Provisional Parameters)
> [!NOTE]
> Weights below are **configurable provisional parameters** designed for domain tuning during competition data exploration. They are not claimed to be permanently fixed axioms.

#### Batting Archetype Presets:
| Dimension | Powerplay Enforcer | Middle-Overs Rotator | Death Overs Finisher | Balanced Batter |
| :--- | :---: | :---: | :---: | :---: |
| D1: Scoring Velocity (TSR) | 0.30 | 0.20 | 0.35 | 0.25 |
| D2: Boundary Potency | 0.30 | 0.15 | 0.35 | 0.25 |
| D3: Stability (Balls/Dismissal) | 0.10 | 0.25 | 0.05 | 0.15 |
| D4: Dot Ball Suppression | 0.15 | 0.25 | 0.10 | 0.15 |
| D5: Phase Adaptability | 0.10 | 0.10 | 0.10 | 0.10 |
| D6: Matchup Neutrality | 0.05 | 0.05 | 0.05 | 0.10 |

#### Bowling Archetype Presets:
| Dimension | Powerplay Bowler | Middle Spin Enforcer | Death Specialist | Balanced Bowler |
| :--- | :---: | :---: | :---: | :---: |
| D1: Run Prevention (TER) | 0.25 | 0.20 | 0.35 | 0.25 |
| D2: Wicket Threat (BSR) | 0.25 | 0.25 | 0.20 | 0.25 |
| D3: Dot Ball Dominance | 0.25 | 0.25 | 0.15 | 0.20 |
| D4: Boundary Concession Supp.| 0.10 | 0.10 | 0.20 | 0.15 |
| D5: Phase Execution | 0.10 | 0.10 | 0.05 | 0.10 |
| D6: Tactical Discipline | 0.05 | 0.10 | 0.05 | 0.05 |

---

## 7. All-Rounder Evaluation Framework

All-rounders must never be evaluated on a single flattened 6-axis metric. A genuine all-rounder provides dual tactical optionality.

### 7.1 Separate Discipline Ratings
1. Compute $\text{VOR}_{bat}$ using the batter dimension engine.
2. Compute $\text{VOR}_{bowl}$ using the bowler dimension engine.

### 7.2 Combined All-Rounder Composite ($\text{VOR}_{ar}$)
$$\text{VOR}_{ar} = \left( \alpha \times \text{VOR}_{bat} + (1 - \alpha) \times \text{VOR}_{bowl} \right) + \text{Bonus}_{dual}$$
where:
* $\alpha \in [0.4, 0.6]$ reflects role bias (e.g., $\alpha = 0.55$ for Batting All-Rounder, $\alpha = 0.45$ for Bowling All-Rounder).
* $\text{Bonus}_{dual}$ is a **Dual-Utility Bonus** awarding up to $+5.0$ rating points if both disciplines meet minimum qualification thresholds:
  $$\text{Bonus}_{dual} = 5.0 \times \left( \frac{\min(\text{VOR}_{bat}, \text{VOR}_{bowl})}{50.0} \right) \quad \text{if both meet } N_{min}$$

This mathematically guarantees that an elite dual-threat player ranks higher than a specialist with superficial secondary skills.

---

## 8. Ranking & Tie-Breaking Rules

When generating the Top 10 Candidate Leaderboard:
1. **Primary Sort:** VYNTIQ Overall Rating ($\text{VOR}$) descending.
2. **Secondary Tie-Breaker:** Reliability Factor ($C(N)$) descending (favoring the candidate with larger verified sample volume).
3. **Tertiary Tie-Breaker:** True Metric Primary Dimension (TSR for batters, TER for bowlers).
4. **Quarantine Exclusion:** Any candidate flagged with `is_eligible = False` or $N < N_{min}$ is strictly excluded from the Top 10 submission ranking.

---

## 9. Analytical Biases & Documented Limitations

Every scouting recommendation must account for known statistical limitations:
1. **Venue Distortion:** Scoring rates at altitude or small-boundary grounds (e.g., Bengaluru, Sharjah) naturally inflate strike rates. Mitigated by True Strike Rate venue subtraction.
2. **Opposition Quality Variance:** Deliveries against world-class pace vs. domestic reserves are treated equally in standard scorecards unless weighted by batter/bowler quality indices.
3. **Chasing Pressure / Game State:** Batters chasing 12+ RPO take higher dismissal risks, which artificially depresses raw balls per dismissal.
4. **Toss and Dew Factors:** Second innings wet-ball conditions significantly impair finger spin grip and defensive bowling economy.

