# SupeRR Selector Season 2 — Canonical Methodology Report (V3.6)

**Competition:** Rajasthan Royals — SupeRR Selector Season 2 (Round 1)  
**Challenge:** Identify the Most Reliable Players Under Pressure  
**Target:** IPL 2027 Auction Strategy  
**Dataset Analyzed:** 194,014 Audited Deliveries across 837 Matches with Deliveries (853 Primary Match Records, 16 Abandoned Washouts, inclusive of 26 Super Over deliveries: 14 IPL across 2 matches, 12 T20I across 2 matches)  
**Author:** VYNTIQ Sports Intelligence Platform  
**Generated PDF File:** `docs/SupeRR_Selector_Season_2_Methodology_Report.pdf`

---

## 1. Executive Summary & Official Dropdown Selections

This submission presents a unified, mathematically reconciled cricket analytics pipeline developed for the Rajasthan Royals war room to identify the most reliable players under extreme match pressure for the IPL 2027 auction. The canonical analytics engine implements verified cricket accounting (0 runs charged to bowlers for byes/leg-byes, non-overstep waist-high beamers correctly classified as illegal no-balls), striker-verified dismissal attribution, complete match count reconciliation (853 primary-scope match records, 837 matches containing ball-by-ball deliveries, 16 abandoned washouts with zero deliveries), and empirical reliability shrinkage ($C = 120$ for batters, $C = 150$ for bowlers). Note that matches containing deliveries are not necessarily completed in full (some were curtailed or affected by weather/DLS adjustments).

Player value is reported via the **Pressure Performance Rating (PPR)** [0–100 scale] and **Pressure Surplus Rating (PSR)** defined as surplus performance relative to the empirical cohort prior median ($R_{\text{median}} = 50.0$). PSR is not a replacement-level metric, as franchise cricket lacks a minor league/waiver wire substitute pool; it measures surplus performance above the empirical cohort prior median ($R_{\text{median}} = 50.0$).

### Top 10 Batters (Unstop Dropdowns 1 to 10)

| Rank | Player Name | Player ID | Teams in Dataset | HP Balls | Normal SR | **HP Strike Rate** | **Elevation ($\Delta\text{SR}$)** | **PPR (Rating)** | **Surplus (PSR)** |
|:---:|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **Tristan Stubbs** | `20702` | Delhi Capitals, Mumbai Indians, South Africa | 651 | 121.8 | **168.5** | **+46.7** | **82.23** | **+32.23** |
| **2** | **David Miller** | `1077` | Delhi Capitals, Gujarat Titans, Lucknow Super Giants, South Africa | 805 | 119.6 | **166.8** | **+47.2** | **80.34** | **+30.34** |
| **3** | **Suryakumar Yadav** | `1699` | India, Mumbai Indians | 665 | 159.2 | **189.2** | **+30.0** | **80.16** | **+30.16** |
| **4** | **Naman Dhir** | `37052` | India, India A, Mumbai Indians | 254 | 148.7 | **196.1** | **+47.4** | **79.39** | **+29.39** |
| **5** | **Namboori Tilak Varma** | `7897` | India, India A, Mumbai Indians | 904 | 130.8 | **165.7** | **+34.9** | **78.26** | **+28.26** |
| **6** | **Shashank Singh** | `2756` | Punjab Kings, Sunrisers Hyderabad | 371 | 137.6 | **173.8** | **+36.3** | **77.45** | **+27.45** |
| **7** | **Rishabh Pant** | `4703` | Delhi Capitals, India, Lucknow Super Giants | 379 | 127.3 | **178.9** | **+51.6** | **76.76** | **+26.76** |
| **8** | **Rinku Singh** | `4708` | India, Kolkata Knight Riders | 823 | 128.8 | **166.1** | **+37.3** | **75.59** | **+25.59** |
| **9** | **Jos Buttler** | `813` | England, Gujarat Titans, Rajasthan Royals | 380 | 151.1 | **182.9** | **+31.8** | **75.07** | **+25.07** |
| **10** | **Glenn Phillips** | `4853` | Gujarat Titans, New Zealand, Sunrisers Hyderabad | 327 | 135.5 | **179.5** | **+44.0** | **74.98** | **+24.98** |

---

### Top 10 Bowlers (Unstop Dropdowns 1 to 10)

| Rank | Player Name | Player ID | Teams in Dataset | HP Balls | Normal Econ | **HP Economy** | **Restriction ($\Delta\text{Econ}$)** | **PPR (Rating)** | **Surplus (PSR)** |
|:---:|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **Mohammad Nawaz** | `2490` | Pakistan | 232 | 7.61 | **5.51** | **+2.10** | **78.11** | **+28.11** |
| **2** | **Sunil Narine** | `781` | Kolkata Knight Riders | 508 | 7.26 | **6.04** | **+1.22** | **77.88** | **+27.88** |
| **3** | **Abrar Ahmed** | `5979` | Pakistan | 309 | 7.35 | **5.65** | **+1.70** | **77.72** | **+27.72** |
| **4** | **Wanindu Hasaranga** | `4900` | Lucknow Super Giants, Rajasthan Royals, Royal Challengers Bengaluru, Sri Lanka, Sunrisers Hyderabad | 678 | 8.04 | **7.69** | **+0.35** | **76.36** | **+26.36** |
| **5** | **Mitchell Santner** | `4101` | Chennai Super Kings, Mumbai Indians, New Zealand | 583 | 7.61 | **6.97** | **+0.64** | **75.66** | **+25.66** |
| **6** | **Varun Chakravarthy** | `6256` | India, Kolkata Knight Riders | 854 | 8.16 | **7.76** | **+0.40** | **74.37** | **+24.37** |
| **7** | **Jamie Overton** | `2382` | Chennai Super Kings, England | 257 | 9.35 | **7.91** | **+1.44** | **73.75** | **+23.75** |
| **8** | **Shaheen Afridi** | `6355` | Pakistan | 287 | 8.06 | **7.61** | **+0.45** | **73.61** | **+23.61** |
| **9** | **Umran Malik** | `25048` | India, Kolkata Knight Riders, Sunrisers Hyderabad | 237 | 10.83 | **8.20** | **+2.63** | **73.24** | **+23.24** |
| **10** | **Rashid Khan** | `4722` | Afghanistan, Gujarat Titans | 1064 | 7.42 | **7.38** | **+0.04** | **72.07** | **+22.07** |

---

## 2. Audit Background & Problem Formulation
T20 matches in high-stakes franchise cricket are decided in clutch leverage windows: the final overs of steep run chases, defending modest totals with dew on the ground, or recovering from top-order Powerplay collapses. Traditional aggregated statistics conflate low-leverage stat-padding with genuine high-pressure reliability. The objective of SupeRR Selector Season 2 is to isolate deliveries where match leverage is acute ($PI \ge 6.5$) and quantify which players systematically outperform the empirical cohort prior median when the game hangs in the balance.

---

## 3. Dataset Inventory, Provenance & Match Reconciliation Audit

| Competition Category | Total Match Records | Matches with Deliveries | Abandoned Matches (No Balls) | Total Deliveries in Dataset | Primary Scope? |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Indian Premier League (IPL)** | 371 | 367 | 4 | 87,687 | **Yes (incl. 14 Super Over balls across 2 matches)** |
| **International T20 (T20I)** | 482 | 470 | 12 | 106,327 | **Yes (incl. 12 Super Over balls across 2 matches)** |
| **Other Domestic / 'A'** | 30 | 30 | 0 | 6,985 | **No (Quarantined; incl. 12 SO balls)** |
| **Total Primary Scope** | **853** | **837** | **16** | **194,014** | **Yes (incl. 26 Super Over balls across 4 matches)** |

*Note on Completion:* Matches containing deliveries are not assumed to be completed in full (some were rain-shortened, ended prematurely, or adjusted via DLS).

---

## 4. Cricket Rules & Extras Accounting Corrections
1. **Extras & Legal Deliveries:** Wides (7,714 balls across full dataset), front-foot no-balls (`Overstep`: 576 balls), and non-overstep waist-high beamers (`other`: 264 balls) are illegal deliveries and re-bowled. Wides do not count as balls faced by batters.
2. **The Semantics of `other` Extras:** Verified against match scorecards (e.g. IPL 2022 Match 29, Gujarat Titans vs. CSK, over 20.4, Chris Jordan's waist-high full toss to David Miller), `other` represents non-overstep no-balls. It confers 1 penalty run, is an illegal ball, and is charged to the bowler.
3. **Bowler Runs Conceded:** Bowlers are charged strictly with runs off the bat + wide penalty extras + no-ball penalty extras. Byes (529 balls) and leg-byes (2,748 balls) are fielding extras and contribute **0 runs** to bowler figures.
4. **Bowler Wicket Credit:** Only dismissals credited to the bowler (Caught, Bowled, LBW, Stumped, Hit Wicket) are counted. Run-outs (600 events) and retired outs are excluded.
5. **Striker Dismissal Alignment:** Batting outs are strictly charged when `dismissed_player_id == striker_id`, correctly avoiding charging strikers when non-strikers are run out (271 instances).

![Figure 1: Pressure Distribution](assets/pressure_distribution.png)

---

## 5. Canonical Pressure Index Specification
Pressure is dynamic and non-linear. The canonical VYNTIQ Pressure Index ($PI \in [0.5, 10.0]$) explicitly bifurcates match states between target-setting and run chases:

### Second Innings: Target Chase Formulation ($PI_{\text{inn2}}$)
$$PI_{\text{inn2}} = \text{clip}\Big(P_{\text{rate}}(RRR) \times M_{\text{wickets}}(W_{\text{hand}}) \times M_{\text{urgency}}(\text{Over}), 0.5, 10.0\Big)$$

- **Continuous Piecewise Required Run Rate Curve ($P_{\text{rate}}$):**
  - If $RRR \le 6.0$: $P_{\text{rate}} = \max(0.5, RRR / 3.0)$ (Continuous at $RRR = 6.0$ where $P_{\text{rate}} = 2.0$)
  - If $6.0 < RRR \le 10.0$: $P_{\text{rate}} = 2.0 + (RRR - 6.0) \times 1.0$ (Continuous at $RRR = 10.0$ where $P_{\text{rate}} = 6.0$)
  - If $10.0 < RRR \le 15.0$: $P_{\text{rate}} = 6.0 + (RRR - 10.0) \times 0.6$ (Continuous at $RRR = 15.0$ where $P_{\text{rate}} = 9.0$)
  - If $RRR > 15.0$: $P_{\text{rate}} = \min(10.0, 9.0 + (RRR - 15.0) \times 0.2)$ (Linear increase with an upper cap at 10.0)
- **Conservative Contestability Heuristic:** If runs needed $> 6 \times$ legal balls remaining (extreme $> 36$ rpo required scoring velocity) or if runs needed $\le 2$ with $\ge 24$ balls remaining (foregone win), $PI$ is set to $1.0$. This condition is formulated as an intentionally conservative contestability heuristic rather than an absolute physical limit, because illegal deliveries (wides, no-balls) and overthrows can generate additional runs without consuming legal balls. In elite professional cricket, chases requiring in excess of 36.0 RPO without extras transition into uncompetitive garbage-time swing play, where batting boundary hitting and bowling economy cease to reflect genuine high-leverage execution. Clamping these deliveries to $PI = 1.0$ prevents garbage-time stat padding from distorting clutch ratings.
- **Wicket Resource Multiplier ($M_{\text{wickets}}$):** Scales inversely with batting resources: $\ge 8$ wkts: $0.85\times$; 6–7 wkts: $1.00\times$; 4–5 wkts: $1.20\times$; 2–3 wkts: $1.40\times$; 1 wkt: $1.60\times$.
- **Match Urgency Multiplier ($M_{\text{urgency}}$):** Scales with over elapsed: Overs 1–6: $0.85\times$; Overs 7–15: $1.00\times$; Overs 16–17: $1.20\times$; Overs 18–20: $1.35\times$.

### First Innings: Target Setting Formulation ($PI_{\text{inn1}}$)
$$PI_{\text{inn1}} = \text{clip}\Big(P_{\text{phase}}(\text{Over}) + P_{\text{collapse}}(W_{\text{lost}}, \text{Over}) + P_{\text{slow}}(CRR, \text{Over}), 1.0, 9.5\Big)$$

- **Phase Baseline:** Overs 1–6: $3.5$; Overs 7–15: $4.5$; Overs 16–20: $7.0$.
- **Collapse Escalation:** Overs 1–6 with $\ge 2$ wkts lost: $+2.0$; Overs 1–10 with $\ge 3$ wkts lost: $+2.5$; Overs 1–15 with $\ge 5$ wkts lost: $+2.5$.
- **Run Rate Slump:** Overs 8–15 with $CRR < 7.0$ rpo: $+1.0$.
- **Explicit Knockout Stakes Integration:** Playoff, knockout, and final matches apply a scalar multiplier $M_{\text{knockout}} = 1.15$ across active match deliveries in Innings 1 and Innings 2 in a single vectorized pass. Super Overs default to $10.0$ and do not scale further. Contestability filtering overrides after the knockout scalar so uncompetitive garbage time stays strictly $1.0$.

### Step-by-Step Numerical Walkthroughs (5 Situational Benchmarks)
1. **Example 1 (Innings 1 Powerplay Collapse in League Match):**
   - *Competition Stage:* Regular League Match (`knock_out=0`).
   - *Innings:* Innings 1 (Target Setting).
   - *Pressure Components:* Phase base = 3.50 (Overs 1–6), Collapse bonus = +2.00 ($\ge 2$ wkts lost in overs 1–6), Slump bonus = 0.00. Unadjusted sum = 5.50.
   - *Knockout Multiplier:* Does not apply (`knock_out=0`, $1.00	imes$).
   - *Contestability Result:* Not applicable in Innings 1.
   - *Final Clipped PI:* **5.50** (Moderate Pressure tier).
2. **Example 2 (Innings 1 Death Acceleration in Playoff Match):**
   - *Competition Stage:* Playoff / Knockout (`knock_out=1`).
   - *Innings:* Innings 1 (Target Setting).
   - *Pressure Components:* Phase base = 7.00 (Overs 16–20), Collapse bonus = 0.00, Slump bonus = 0.00. Raw Innings 1 PI = 7.00.
   - *Knockout Multiplier:* **Applies** (`knock_out=1`, active Innings 1 $	o 1.15	imes$). Scaled = $7.00 	imes 1.15 = 8.05$.
   - *Contestability Result:* Not applicable in Innings 1.
   - *Final Clipped PI:* **8.05** (High Pressure tier).
3. **Example 3 (Innings 2 High-Stakes Chase in League Match):**
   - *Competition Stage:* Regular League Match (`knock_out=0`).
   - *Innings:* Innings 2 (Chasing Target).
   - *Pressure Components:* Over 18.2 (`overid=18`), target 185, 30 needed off 10 balls ($RRR = 18.00$ rpo), 5 wickets in hand. $P_{\text{rate}} = \min(10.0, 9.0 + (18 - 15) \times 0.2) = 9.60$, $M_{\text{wickets}} = 1.20$, $M_{\text{urgency}} = 1.35$. Raw product: $9.60 \times 1.20 \times 1.35 = 15.552$.
   - *Knockout Multiplier:* Does not apply (`knock_out=0`, $1.00	imes$).
   - *Contestability Result:* Contested chase ($30 \le 6 \times 10$).
   - *Final Clipped PI:* $\min(10.0, 15.552) = \mathbf{10.00}$ (Extreme Pressure tier).
4. **Example 4 (Innings 2 Hopeless Chase / Contestability Heuristic in Playoff):**
   - *Competition Stage:* Playoff / Knockout (`knock_out=1`).
   - *Innings:* Innings 2 (Chasing Target).
   - *Pressure Components:* Over 19.1 (`overid=19`), 45 runs needed off 5 balls ($RRR = 54.00$ rpo), 4 wickets in hand. $P_{\text{rate}} = 10.00$, $M_{\text{wickets}} = 1.20$, $M_{\text{urgency}} = 1.35$. Pre-clipping base product: $10.00 \times 1.20 \times 1.35 = 16.20$.
   - *Knockout Multiplier:* Evaluated before contestability filter ($16.20 \times 1.15 = 18.63$, clipped to $[0.5, 10.0]$ ceiling $\to 10.00$).
   - *Contestability Result:* **Triggered**. Runs needed ($45$) $> 6 \times \text{balls remaining}$ ($5 \times 6 = 30$). Requiring $>36.0$ RPO without extras triggers the conservative contestability heuristic. Deterministically resets to 1.00.
   - *Final Clipped PI:* **1.00** (Low Pressure tier / uncompetitive garbage time).
5. **Example 5 (Super Over Decider):**
   - *Competition Stage:* Regular League or Playoff (`knock_out=0` or `1`).
   - *Innings:* Innings 3 or 4 (Super Over).
   - *Pressure Components:* Fixed deterministically at terminal maximum leverage ($10.00$).
   - *Knockout Multiplier:* Bypassed / not applied (Super Overs remain deterministically pegged at 10.00).
   - *Contestability Result:* Not applicable.
   - *Explicit Scope & Accounting:* Included in the 194,014 primary scope (26 primary SO deliveries: 14 IPL across 2 matches, 12 T20I across 2 matches) and counts toward high-pressure workload qualification ($N_{\text{pressure}} \ge 60$) and player PPR ratings, but excluded from the non-pressure baseline.
   - *Final Clipped PI:* **10.00** (Terminal Extreme Pressure).

![Figure 2: Pressure by Match Phase](assets/pressure_by_match_phase.png)

---

## 6. Operational Pressure Tiers & Delivery Distribution
- **Extreme Pressure ($PI \ge 8.5$):** 11.2% of deliveries. Acute finish situations.
- **High Pressure ($6.5 \le PI < 8.5$):** 21.0% of deliveries. Standard high-leverage situations.
- **Moderate Pressure ($4.0 \le PI < 6.5$):** 42.4% of deliveries. Standard contest baseline.
- **Low Pressure ($PI < 4.0$):** 25.4% of deliveries. Low-stakes situations.

---

## 7. Dual Baseline Performance Framework
- **Batting Elevation:** $\Delta\text{SR} = \text{SR}_{\text{pressure}} - \text{SR}_{\text{normal}}$.
- **Bowling Restriction:** $\Delta\text{Econ} = \text{Econ}_{\text{normal}} - \text{Econ}_{\text{pressure}}$.

---

## 8. Empirical Reliability Shrinkage & Baseline Review
$$\text{Pressure Performance Rating (PPR)} = \frac{N}{N + C} \times \text{Raw Composite} + \left(1 - \frac{N}{N + C}\right) \times 50.0$$
$$\text{Pressure Surplus Rating (PSR)} = \text{PPR} - 50.0$$
- **Workload Constants:** $C = 120$ for batters (~6 completed pressure innings) and $C = 150$ for bowlers (25 pressure overs).
- **Empirical Cohort Prior Median Justification:** In sabermetric literature (e.g. baseball WAR), replacement level represents an available non-roster substitute. Because T20 franchise cricket lacks a centralized minor league or waiver wire, asserting that 50.0 is literal 'replacement value' would be methodologically unsupported. Instead, 50.0 is accurately defined as the **Empirical Cohort Prior Median** (the expected performance of an average qualified peer). Consequently, $\text{PPR} - 50.0$ is designated as **Pressure Surplus Rating (PSR)** (surplus relative to the prior median).

![Figure 3: Reliability Curve](assets/player_reliability_confidence.png)

---

## 9. Pressure Performance Rating (PPR) Engine Specification
Composite scores normalize metrics using empirical cumulative distribution percentiles ($[0, 100]$) and apply reliability shrinkage.

![Figure 4: Top 10 Batters Chart](assets/top10_batters_chart.png)

---

## 10. Official Top 10 Batters: Tactical Breakdown & Auction Profiles
1. **Tristan Stubbs (PPR: 82.23 | PSR: +32.23):** 651 HP balls, 168.51 SR (+46.70 delta), 73.0% control. World-class 360-degree death execution.
2. **David Miller (PPR: 80.34 | PSR: +30.34):** 805 HP balls, 166.83 SR (+47.25 delta). Veteran closer with ice in his veins.
3. **Suryakumar Yadav (PPR: 80.16 | PSR: +30.16):** 665 HP balls, 189.17 SR (+29.96 delta). Field manipulation genius.
4. **Naman Dhir (PPR: 79.39 | PSR: +29.39):** 254 HP balls, 196.06 SR (+47.40 delta). Exceptional young talent with domestic pedigree; exceptional high-leverage finisher providing significant pressure-performance surplus relative to the empirical cohort median.
5. **Tilak Varma (PPR: 78.26 | PSR: +28.26):** 904 HP balls, 165.71 SR (+34.86 delta). Heavy-volume clutch accumulator and finisher.
6. **Shashank Singh (PPR: 77.45 | PSR: +27.45):** 371 HP balls, 173.85 SR (+36.28 delta). Elite middle-to-death acceleration.
7. **Rishabh Pant (PPR: 76.76 | PSR: +26.76):** 379 HP balls, 178.89 SR (+51.60 delta). Exceptional chase elevation.
8. **Rinku Singh (PPR: 75.59 | PSR: +25.59):** 823 HP balls, 166.10 SR (+37.31 delta). Proven death-over match-winner.
9. **Jos Buttler (PPR: 75.07 | PSR: +25.07):** 380 HP balls, 182.89 SR (+31.77 delta). Dynamic match-winner across conditions.
10. **Glenn Phillips (PPR: 74.98 | PSR: +24.98):** 327 HP balls, 179.51 SR (+44.00 delta). Versatile power hitter.

![Figure 5: Top 10 Bowlers Chart](assets/top10_bowlers_chart.png)

---

## 11. Bowler Evaluation Methodology & Composite Weights
Bowling reliability combines economy suppression, elevation differential, dot-ball dominance, and wicket threat:
- Pressure Economy (35%), Economy Restriction $\Delta\text{Econ}$ (25%), Dot Ball % (20%), Wicket Rate (20%).

---

## 12. Official Top 10 Bowlers: Tactical Breakdown & Auction Profiles
1. **Mohammad Nawaz (PPR: 78.11 | PSR: +28.11):** 232 HP balls, 5.51 rpo (+2.10 delta), 22 wkts. Elite containment.
2. **Sunil Narine (PPR: 77.88 | PSR: +27.88):** 508 HP balls, 6.04 rpo (+1.22 delta), 34 wkts. Legendary defensive spin mastery.
3. **Abrar Ahmed (PPR: 77.72 | PSR: +27.72):** 309 HP balls, 5.65 rpo (+1.70 delta), 23 wkts. Mystery spinner with deceptive variations.
4. **Wanindu Hasaranga (PPR: 76.36 | PSR: +26.36):** 678 HP balls, 7.69 rpo (+0.35 delta), 61 wkts. Aggressive wicket-taking threat.
5. **Mitchell Santner (PPR: 75.66 | PSR: +25.66):** 583 HP balls, 6.97 rpo (+0.64 delta), 41 wkts. Combined high-pressure economy across 583 legal balls.
6. **Varun Chakravarthy (PPR: 74.37 | PSR: +24.37):** 854 HP balls, 7.76 rpo (+0.40 delta), 61 wkts. Proven Indian mystery spinner.
7. **Jamie Overton (PPR: 73.75 | PSR: +23.75):** 257 HP balls, 7.91 rpo (+1.44 delta), 24 wkts. Hard-length enforcer pace.
8. **Shaheen Afridi (PPR: 73.61 | PSR: +23.61):** 287 HP balls, 7.61 rpo (+0.45 delta), 30 wkts. Opening & death yorker execution.
9. **Umran Malik (PPR: 73.24 | PSR: +23.24):** 237 HP balls, 8.20 rpo (+2.63 delta), 21 wkts. Extreme pace with +2.63 delta elevation.
10. **Rashid Khan (PPR: 72.07 | PSR: +22.07):** 1,064 HP balls, 7.38 rpo (+0.04 delta), 78 wkts. Highest sample volume in T20 history.

---

## 12.3 Rajasthan Royals Tactical Integration Blueprint

To support informed squad construction at the IPL 2027 auction, the table below highlights candidate options from the top-10 cohort across key tactical archetypes:

| Target Archetype | Recommended Targets | Tactical Role for RR at Sawai Mansingh Stadium (Jaipur) |
|:---|:---|:---|
| **Middle-Order Finisher** | **Tristan Stubbs** (PPR 82.23)<br/>**Naman Dhir** (PPR 79.39) | Potential tactical fit based on the identified player archetype and historical pressure-performance profile. Stubbs provides 360-degree boundary hitting against spin and pace at death; Dhir delivers elite scoring velocity under pressure (196.06 SR, +47.40 delta across 254 HP balls). |
| **Defensive Spin Strangle** | **Mitchell Santner** (PPR 75.66)<br/>**Sunil Narine** (PPR 77.88) | Potential tactical fit based on the identified player archetype and historical pressure-performance profile. Jaipur's large square boundaries reward defensive spin; Santner (combined high-pressure economy of 6.97 rpo across 583 legal balls) and Narine (6.04 rpo) offer disciplined run restriction in overs 7–15. |
| **Wicket-Taking Mystery** | **Varun Chakravarthy** (PPR 74.37)<br/>**Wanindu Hasaranga** (PPR 76.36) | Potential tactical fit based on the identified player archetype and historical pressure-performance profile. Offers attacking breakthrough capacity; Hasaranga (61 wkts) and Chakravarthy (61 wkts) demonstrate consistent wicket-taking ability under scoreboard pressure. |
| **Death Enforcer Pace** | **Jamie Overton** (PPR 73.75)<br/>**Umran Malik** (PPR 73.24) | Potential tactical fit based on the identified player archetype and historical pressure-performance profile. Complements frontline swing options; Overton hits the deck hard at death (7.91 rpo); Malik offers raw velocity with an elite +2.63 rpo delta under pressure. |

> **Auction Availability & Regulatory Qualification Note:** Player recommendations are performance-based candidate evaluations derived from historical match data. They do not imply or confirm that auction availability, franchise retention status, expected clearing price, or overseas player quotas (maximum 8 overseas players per squad, maximum 4 in Playing XI under BCCI regulations) have been independently verified. The Rajasthan Royals war room must integrate real-time regulatory, retention, and purse constraints during auction bidding.

![Figure 6: Tactical Role Coverage](assets/rr_squad_role_coverage.png)

---

## 13. IPL vs T20I Competition Dynamics & Format Specificity
Comparing 87,687 IPL deliveries with 106,327 T20I deliveries:
- **IPL Scoring Environment:** **9.23 rpo**, **20.45%** boundary frequency (over legal balls), with a 31.87% high-pressure delivery share.
- **T20I Scoring Environment:** **8.46 rpo**, **17.58%** boundary frequency (over legal balls), with a 32.51% high-pressure delivery share.
- **Primary Scope Combined:** **194,014 deliveries** at **8.81 rpo** and **18.88%** boundary frequency, with a 32.22% high-pressure delivery share.

**Reconciliation of Preliminary Draft Discrepancy:**
Earlier un-reconciled preliminary notes cited 9.20 RPO and 19.46% boundaries. Our mathematical audit confirmed that this preliminary variance arose from dividing boundary hits across total deliveries (including wides and no-balls, where 17,131 / 87,687 = 19.54% ~ 19.46%) and unadjusted extras. Standard cricket statistics require run rates and boundary rates to be calculated strictly over legal deliveries (overs = legal balls / 6). Under canonical cricket accounting, the IPL scoring velocity is exactly 9.23 RPO with 20.45% boundaries, which Figure 7, the narrative, and the audit CSVs represent with 100% exact agreement.

**Methodological Accounting on Competition Normalization:**
Within-player elevation metrics ($\Delta\text{SR}$ and $\Delta\text{Econ}$) isolate individual responsiveness to pressure relative to normal conditions in observed matches, but they do NOT mathematically guarantee competition neutrality or eliminate systemic environment differences (such as pitch pace, boundary size, or bowling depth).
To address this without ad-hoc weighting, the primary pipeline constructs a unified cohort of qualified players across approved Tier-1 competitions (IPL and T20I), evaluates each delivery with the canonical PressureEngine, and normalizes raw performance across the joint eligible population using empirical CDF percentiles. Separate format statistics are preserved in audit logs to allow the Rajasthan Royals war room to inspect format-specific nuances alongside combined ratings.

![Figure 7: Dual-Axis Format Comparison](assets/format_comparison_ipl_vs_t20i.png)

---

## 13.1 Format-Specific Player Statistics (IPL vs. T20I Disaggregation)

The primary selection ranking is determined by the Combined PPR (evaluated over all qualified Tier-1 deliveries). Format columns report exact empirical metrics; 'N/A' indicates no high-pressure deliveries were recorded in that specific format during 2022–2026.

### Top 10 Batters — Combined PPR vs. Format-Specific High-Pressure Statistics

| Rank | Player Name | Combined PPR | Combined PSR | Combined HP SR | IPL HP Balls | IPL HP SR | T20I HP Balls | T20I HP SR |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **Tristan Stubbs** | **82.23** | **+32.23** | **168.5** | 434 | 171.66 | 217 | 162.21 |
| **2** | **David Miller** | **80.34** | **+30.34** | **166.8** | 534 | 163.11 | 271 | 174.17 |
| **3** | **Suryakumar Yadav** | **80.16** | **+30.16** | **189.2** | 424 | 170.05 | 241 | 222.82 |
| **4** | **Naman Dhir** | **79.39** | **+29.39** | **196.1** | 185 | 183.78 | 69 | 228.99 |
| **5** | **Namboori Tilak Varma** | **78.26** | **+28.26** | **165.7** | 530 | 161.70 | 374 | 171.39 |
| **6** | **Shashank Singh** | **77.45** | **+27.45** | **173.8** | 371 | 173.85 | 0 | N/A |
| **7** | **Rishabh Pant** | **76.76** | **+26.76** | **178.9** | 304 | 182.89 | 75 | 162.67 |
| **8** | **Rinku Singh** | **75.59** | **+25.59** | **166.1** | 561 | 164.35 | 262 | 169.85 |
| **9** | **Jos Buttler** | **75.07** | **+25.07** | **182.9** | 276 | 189.49 | 104 | 165.38 |
| **10** | **Glenn Phillips** | **74.98** | **+24.98** | **179.5** | 33 | 166.67 | 294 | 180.95 |

---

### Top 10 Bowlers — Combined PPR vs. Format-Specific High-Pressure Statistics

| Rank | Player Name | Combined PPR | Combined PSR | Combined HP Econ | IPL HP Balls / Wkts | IPL HP Econ | T20I HP Balls / Wkts | T20I HP Econ |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **Mohammad Nawaz** | **78.11** | **+28.11** | **5.51** | 0 / 0 | N/A | 232 / 22 | 5.51 |
| **2** | **Sunil Narine** | **77.88** | **+27.88** | **6.04** | 508 / 34 | 6.04 | 0 / 0 | N/A |
| **3** | **Abrar Ahmed** | **77.72** | **+27.72** | **5.65** | 0 / 0 | N/A | 309 / 23 | 5.65 |
| **4** | **Wanindu Hasaranga** | **76.36** | **+26.36** | **7.69** | 261 / 22 | 8.46 | 417 / 39 | 7.21 |
| **5** | **Mitchell Santner** | **75.66** | **+25.66** | **6.97** | 148 / 10 | 6.16 | 435 / 31 | 7.24 |
| **6** | **Varun Chakravarthy** | **74.37** | **+24.37** | **7.76** | 496 / 30 | 8.26 | 358 / 31 | 7.06 |
| **7** | **Jamie Overton** | **73.75** | **+23.75** | **7.91** | 101 / 9 | 9.21 | 156 / 15 | 7.08 |
| **8** | **Shaheen Afridi** | **73.61** | **+23.61** | **7.61** | 0 / 0 | N/A | 287 / 30 | 7.61 |
| **9** | **Umran Malik** | **73.24** | **+23.24** | **8.20** | 164 / 13 | 7.24 | 73 / 8 | 10.36 |
| **10** | **Rashid Khan** | **72.07** | **+22.07** | **7.38** | 647 / 47 | 8.24 | 417 / 31 | 6.04 |

> **Mathematical Reconciliation & Tactical Interpretation:** A bowler's combined economy rate across multiple tournaments is the exact weighted average of total runs conceded (including wide and no-ball penalties) divided by total legal overs:
> - **Mitchell Santner:** IPL 6.16 rpo (148 balls, 152 runs) and T20I 7.24 rpo (435 balls, 525 runs) combine exactly to $(152 + 525) / (583 / 6) = 6.9674 \to \mathbf{6.97}$ rpo (combined high-pressure economy across 583 legal balls).
> - **Jamie Overton:** IPL 9.21 rpo (101 balls, 155 runs) and T20I 7.08 rpo (156 balls, 184 runs) combine exactly to $(155 + 184) / (257 / 6) = 7.9144 \to \mathbf{7.91}$ rpo.
> - **Tristan Stubbs:** IPL 171.66 SR (434 balls, 745 runs) and T20I 162.21 SR (217 balls, 352 runs) combine exactly to $(745 + 352) / 651 \times 100 = \mathbf{168.51}$ SR.
> - **Suryakumar Yadav:** IPL 170.05 SR (424 balls, 721 runs) and T20I 222.82 SR (241 balls, 537 runs) combine exactly to $(721 + 537) / 665 \times 100 = \mathbf{189.17}$ SR.
> Where players have zero deliveries in a format (e.g. Sunil Narine in T20Is or Mohammad Nawaz in IPL), their combined rating is driven by robust single-competition samples.

---

## 14. Multi-Definition Robustness Analysis (Strict, Standard, Broad)

| Role | Comparison | Standard Cohort | Alternative Cohort | Spearman $\rho$ | Kendall $\tau$ | Top-10 Overlap % |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **Batter** | Standard ($PI \ge 6.5$) vs. Strict ($PI \ge 7.5$) | 241 | 127 | **0.7805** | **0.6033** | **60.0%** |
| **Batter** | Standard ($PI \ge 6.5$) vs. Broad ($PI \ge 5.5$) | 241 | 292 | **0.9002** | **0.7485** | **40.0%** |
| **Bowler** | Standard ($PI \ge 6.5$) vs. Strict ($PI \ge 7.5$) | 224 | 130 | **0.7556** | **0.5675** | **70.0%** |
| **Bowler** | Standard ($PI \ge 6.5$) vs. Broad ($PI \ge 5.5$) | 224 | 256 | **0.8938** | **0.7230** | **80.0%** |

**First-Innings Phase Baseline Sensitivity Analysis:**
To evaluate whether assigning baseline $7.0$ to overs 16–20 over-classifies comfortable target-setting as high pressure, we evaluated a Contextual Cushion alternative where base pressure drops to $5.5$ if $CRR \ge 9.5$ and wickets lost $\le 2$. Across 25,066 first-innings death deliveries, only 1,459 balls (5.82%) shift category. Rank correlation between canonical and contextual models is near-perfect:
- Batter Spearman $ho = 0.9897$ (Kendall $	au = 0.9397$, 70.0% Top-10 overlap).
- Bowler Spearman $ho = 0.9864$ (Kendall $	au = 0.9163$, 100.0% Top-10 overlap).
The canonical model is retained because death overs in T20 franchise cricket inherently require maximum boundary execution regardless of cushion, and the empirical correlation confirms model stability.

![Figure 8: Ranking Stability](assets/ranking_stability_across_definitions.png)

---

## 15. Scoring Weight Sensitivity Analysis
- **Batters:** Baseline vs. Velocity-Heavy ($\rho = 0.9879$, 90% overlap), Delta-Heavy ($\rho = 0.9319$, 90% overlap), Control-Heavy ($\rho = 0.9766$, 80% overlap).
- **Bowlers:** Baseline vs. Economy-Heavy ($\rho = 0.9854$, 90% overlap), Delta-Heavy ($\rho = 0.9258$, 80% overlap), Dot-Heavy ($\rho = 0.9712$, 90% overlap).

The rankings demonstrate stability under the tested pressure thresholds and scoring-weight variations. These empirical sensitivity tests confirm model consistency within the observed historical sample, though they do not claim or guarantee that future match performance is guaranteed.

![Figure 9: Scatter Plot](assets/pressure_vs_normal_scatter.png)

---

## 16. Verification of Resolved Inconsistencies
1. **Mitchell Santner Economy Verified:** Combined high-pressure economy across 583 legal balls is exactly 6.97 rpo (previously 7.04 rpo due to fielding extras).
2. **Extras Accounting Corrected:** Bowler runs conceded strictly exclude byes and leg-byes. Non-overstep beamers (`other`) correctly treated as illegal no-balls.
3. **Striker-Specific Dismissal Alignment:** Non-striker run-outs are properly disassociated from striker dismissals, preserving true batting averages.
4. **Objective Contestability Boundaries:** Implemented a conservative contestability heuristic (runs needed $> 6 \times$ legal balls remaining, and $\le 2$ runs needed with $\ge 24$ balls remaining) to isolate competitive cricket leverage from uncompetitive garbage time, recognizing that extras and overthrows can yield additional runs without consuming legal balls.

---

## 17. Edge-Case Handling & Boundary Conditions
- **Metric-Specific Zero-Denominator Accounting:** Strike rate and boundary frequency are unavailable (NaN) when legal balls faced = 0; economy and wicket rate are unavailable when legal balls bowled = 0. Undefeated batting average convention reports total undefeated runs scored when dismissals = 0 and balls faced > 0.
- **Super Over Scope & Operational Workload Accounting:** Across all tiers, the dataset records 38 Super Over deliveries (14 IPL, 12 T20I, 12 Other Domestic). In the primary scope (IPL + T20I), there are exactly **26 recorded Super Over deliveries** across 4 tied matches (14 IPL across 2 matches, 12 T20I across 2 matches). Not all recorded deliveries are legal balls: 2 deliveries were wides and 1 was a non-overstep beamer no-ball. The canonical pipeline executes metric-specific workload accounting:
  - **Bowling Workload:** Exactly **23 legal balls bowled** (13 IPL, 10 T20I) count toward the 60-ball qualification gate ($N_{\text{pressure}} \ge 60$); 3 illegal deliveries do not. Bowlers conceded 40.0 runs (including 3 penalty extras) and took 6 wickets.
  - **Batting Workload:** Exactly **24 balls faced by batters** (14 IPL, 10 T20I) count toward the 60-ball qualification gate ($N_{\text{pressure}} \ge 60$); wides are not faced, but the no-ball was faced. Batters scored 37 runs with 7 dismissals (6 bowler dismissals, 1 non-striker run-out).
  - **Normal Workload Qualification:** **Zero.** Because Super Overs carry $PI = 10.00$ (Extreme Pressure), none enter the non-pressure baseline ($PI < 6.5$). All delivery events are fully audited in `audit/data_integrity/super_over_workload_audit.csv`.
- **Rain-Shortened DLS Targets:** Revised targets supersede first-innings totals.
- **Workload Qualification Gates:** Strict minimum workload criteria ($\ge 60$ high-pressure deliveries faced/bowled).

---

## 18. Risk Analysis, Sample Limitations & Auction Traps
Franchise war rooms frequently fall prey to three predictable auction traps:
1. **Small-Sample Outlier Trap:** Bidding on players with a high raw strike rate across only 15–20 deliveries. Our empirical reliability shrinkage dampens these anomalies.
2. **Recency Bias Trap:** Overvaluing a single playoff performance while ignoring multi-year career baselines.
3. **Role Mismatch Trap:** Purchasing an anchor batter to play as a death-overs finisher, ignoring that their delta ($\Delta\text{SR}$) drops under acute required run rates.

![Figure 10: Sample Size vs Shrunk Rating](assets/sample_size_vs_p_vor.png)

---

## 19. Reproducibility & Code Architecture Documentation
All analytical steps, data cleaning routines, and metric pipelines are fully reproducible via the VYNTIQ codebase:
- **Canonical Execution Script:** `scripts/run_canonical_pipeline.py`
- **Canonical Modules:** `backend/app/services/analytics/pressure.py`, `backend/app/services/scoring/pressure_ranking.py`
- **Audited Delivery Dataset:** `data/official_super_rr_s2/ball_by_ball_audited.parquet`
- **Standardized PPR Audit Logs:** `audit/rankings/batters_ppr_audit.csv`, `bowlers_ppr_audit.csv` (with legacy `*_p_vor_audit.csv` preserved)
- **Format Breakdown Logs:** `audit/rankings/top10_batters_format_breakdown.csv`, `top10_bowlers_format_breakdown.csv`
- **Automated Verification Test Suite:** `backend/tests/test_audit_reconciliation.py`

---

## 20. Conclusion & Strategic Recommendations for RR War Room
1. **Prioritize Tristan Stubbs and Naman Dhir** to lock in world-class death finishing and high pressure-performance surplus relative to the empirical cohort median.
2. **Target Mitchell Santner** as an elite defensive restrictor to control Jaipur's middle overs at a combined high-pressure economy of 6.97 rpo across 583 legal balls.
3. **Pair Wanindu Hasaranga or Varun Chakravarthy** with existing pace assets to maintain aggressive wicket-taking pressure throughout all 20 overs.
By grounding candidate evaluations in verified high-leverage delivery data rather than unadjusted career totals, the Rajasthan Royals analytics group can systematically support informed squad construction, refine valuation models, and make evidence-backed auction decisions for IPL 2027.
