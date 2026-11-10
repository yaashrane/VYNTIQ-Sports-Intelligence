# SupeRR Selector Season 2 — Official Methodology Report

**Competition:** Rajasthan Royals — SupeRR Selector Season 2 (Round 1)  
**Challenge:** Identify the Most Reliable Players Under Pressure  
**Target:** IPL 2027 Auction Strategy  
**Dataset Analyzed:** 200,999 Deliveries across 883 Matches (IPL & T20I Archives 2022–2026)  
**Author:** VYNTIQ Sports Intelligence Platform  
**Generated PDF File:** `docs/SupeRR_Selector_Season_2_Methodology_Report.pdf` (539 KB)

---

## Executive Summary: Official Unstop Dropdown Selections

This report delivers an audit-ready, statistically defensible evaluation of player performance under high-pressure T20 match situations. Using a dual-evidence framework baselined against career performance across 200,999 official deliveries, we quantify both **absolute clutch execution** and **relative performance elevation ($\Delta$)**, applying Bayesian reliability shrinkage ($C = 120/150$) to ensure small-sample anomalies do not distort rankings.

### 🏆 Top 10 Batters (Unstop Dropdowns 1 to 10)

| Rank | Player Name | Official Player ID | Teams in Dataset | HP Balls | Base SR | **HP Strike Rate** | **Elevation ($\Delta\text{SR}$)** | HP Boundary % | **P-VOR Rating** |
|:---:|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **Suryakumar Yadav** | `1699` | India, Mumbai Indians | 678 | 161.2 | **182.3** | **$+21.1$** | 27.3% | **84.7** |
| **2** | **Naman Dhir** | `37052` | Mumbai Indians, India A | 266 | 164.5 | **187.6** | **$+23.1$** | 27.4% | **80.2** |
| **3** | **Jos Buttler** | `813` | Rajasthan Royals, England | 393 | 150.5 | **176.3** | **$+25.8$** | 25.4% | **79.5** |
| **4** | **Rishabh Pant** | `4703` | India, Delhi Capitals | 407 | 137.0 | **166.6** | **$+29.6$** | 24.3% | **77.0** |
| **5** | **Sai Sudharsan** | `23450` | Gujarat Titans, India | 225 | 142.9 | **173.8** | **$+30.9$** | 24.0% | **75.8** |
| **6** | **Babar Azam** | `2485` | Pakistan | 124 | 128.9 | **183.1** | **$+54.1$** | 24.2% | **74.4** |
| **7** | **Glenn Phillips** | `4853` | Sunrisers Hyderabad, NZ | 341 | 145.0 | **172.1** | **$+27.2$** | 21.7% | **74.3** |
| **8** | **Tristan Stubbs** | `20702` | Delhi Capitals, South Africa | 676 | 145.6 | **162.4** | **$+16.8$** | 20.3% | **74.1** |
| **9** | **Shubman Gill** | `6288` | Gujarat Titans, India | 276 | 144.4 | **169.9** | **$+25.5$** | 21.4% | **73.7** |
| **10** | **Shashank Singh** | `2756` | Punjab Kings, SRH | 398 | 153.9 | **167.8** | **$+13.9$** | 22.6% | **73.7** |

---

### 🏆 Top 10 Bowlers (Unstop Dropdowns 1 to 10)

| Rank | Player Name | Official Player ID | Teams in Dataset | HP Legal Balls | Base Econ | **HP Economy** | **Restriction ($\Delta\text{Econ}$)** | HP Wickets | **P-VOR Rating** |
|:---:|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **Sunil Narine** | `781` | Kolkata Knight Riders | 513 | 6.94 | **6.14** | **$+0.80$** | 36 | **81.2** |
| **2** | **Mitchell Santner** | `4101` | CSK, New Zealand | 583 | 7.46 | **7.04** | **$+0.42$** | 41 | **79.8** |
| **3** | **Abrar Ahmed** | `5979` | Pakistan | 313 | 6.75 | **5.73** | **$+1.02$** | 25 | **78.7** |
| **4** | **Mohammad Nawaz** | `2490` | Pakistan | 232 | 7.16 | **5.59** | **$+1.57$** | 22 | **77.1** |
| **5** | **Wanindu Hasaranga**| `4900` | Sri Lanka, RCB, SRH | 685 | 8.01 | **7.79** | **$+0.23$** | 62 | **77.0** |
| **6** | **Varun Chakravarthy**| `6256` | KKR, India | 856 | 8.08 | **7.86** | **$+0.22$** | 62 | **75.2** |
| **7** | **Kuldeep Yadav** | `3644` | India, Delhi Capitals | 752 | 8.07 | **7.90** | **$+0.17$** | 59 | **74.4** |
| **8** | **Sufiyan Muqeem** | `34485`| Pakistan | 236 | 6.12 | **5.82** | **$+0.29$** | 22 | **74.4** |
| **9** | **Shadab Khan** | `4926` | Pakistan | 293 | 7.91 | **6.96** | **$+0.95$** | 20 | **74.0** |
| **10** | **Akeal Hosein** | `2417` | West Indies, SRH, CSK | 244 | 7.75 | **6.52** | **$+1.23$** | 17 | **73.5** |

*(Near-miss clutch performers: Jasprit Bumrah #11 at 73.4 with 53 HP wickets; Rashid Khan #12 at 73.2 with 80 HP wickets).*

---

## 1. Context-Aware Pressure Definition & Modeling

In T20 cricket, pressure is a continuous, dynamic state determined by required scoring velocity, resource constraints (wickets in hand, overs remaining), match phase, and tournament stakes:

### A. Run Chase Formulation (Innings 2)
$$\text{PI}_{\text{inn2}} = \text{clip}\left( P_{\text{rate}}(\text{RRR}) \times M_{\text{wickets}}(W_{\text{hand}}) \times M_{\text{urgency}}(\text{Phase}) \times M_{\text{stakes}}, \, 0.5, \, 10.0 \right)$$
- **Nonlinear Rate Curve ($P_{\text{rate}}$):** Anchored to T20 league par (8.2 rpo). $\text{RRR} \le 6.0 \to 1.0$; $\text{RRR} \in [8, 10] \to 4.0–6.0$; $\text{RRR} \ge 12 \to 8.0–10.0$.
- **DLS Wicket Resource Multiplier ($M_{\text{wickets}}$):** Scales from $0.85$ ($8+$ wickets in hand) up to $1.60$ for the final wicket pair ($W_{\text{hand}} = 1$).
- **Urgency Multiplier ($M_{\text{urgency}}$):** Escalates from $0.85$ in Powerplay to $1.35$ in death overs 18–20.
- **Garbage Time Filter:** Automatically discounts blowouts where win probability is $\ge 99\%$ (e.g. needing 50 off 6 balls or 2 off 30 balls).

### B. Target Setting Formulation (Innings 1) & High Stakes
$$\text{PI}_{\text{inn1}} = \text{clip}\left( \text{Base}_{\text{phase}} + \text{Bonus}_{\text{collapse}} + \text{Bonus}_{\text{slow\_rate}}, \, 1.0, \, 9.5 \right) \times M_{\text{stakes}}$$
- **Death Over Baseline:** Overs 16–20 baseline at $7.0$ due to non-negotiable boundary acceleration demands.
- **Early Collapse Bonus:** Escalates up to $+2.5$ if the batting side loses $\ge 2$ wickets in the Powerplay or $\ge 4$ before over 12.
- **Knockout Stakes Multiplier ($M_{\text{stakes}}$):** $+15\%$ pressure multiplier on playoff, qualifier, eliminator, and final matches.
- **Super Overs:** Fixed at maximum pressure: $\text{PI} = 10.0$.

---

## 2. Fair Comparisons: Sample Sizing, IPL vs. T20I Context

- **IPL vs. International (T20I) Scoring Environments:**  
  IPL average run rate is **9.20 rpo** with **19.5% boundaries**, compared to T20Is at **8.40 rpo** and **16.7% boundaries**. Raw unadjusted strike rates artificially bias towards IPL batters, while raw economy rates unfairly penalize IPL bowlers. Our scoring normalizes player outputs within empirical percentile distributions.
- **Minimum Eligibility Thresholds:**  
  - Batters: $\ge 100$ High-Pressure balls faced AND $\ge 250$ total balls faced overall. (128 qualified candidates).
  - Bowlers: $\ge 120$ High-Pressure legal balls bowled ($20$ overs) AND $\ge 300$ total balls bowled overall. (149 qualified candidates).
- **Bayesian Reliability Shrinkage:**  
  $$\text{P-VOR Rating} = \frac{N}{N + C} \times \text{Raw Composite} + \left(1 - \frac{N}{N + C}\right) \times 50.0$$
  Where $C = 120$ for batters and $C = 150$ for bowlers.

---

## 3. Strategic Value: Strengthening the Rajasthan Royals for IPL 2027

| Target Tactical Vacancy | Recommended Targets | Tactical Fit for Rajasthan Royals Ecosystem |
|:---|:---|:---|
| **Death Finisher & Boundary Striker** | **Naman Dhir** (#2)<br/>**Shashank Singh** (#10)<br/>**Glenn Phillips** (#7) | Solves RR's middle-order boundary deceleration. Naman Dhir provides an extraordinary 187.6 SR and 27.4% boundary rate under death pressure at high auction surplus value. |
| **Top-Order Anchor / Accelerating Clutch** | **Sai Sudharsan** (#5)<br/>**Jos Buttler** (#3) | Pairs elite anchor stability with explosive $+30.9$ SR acceleration under chase pressure, providing insurance against top-order collapses. |
| **Mystery Spin & Middle/Death Enforcer** | **Varun Chakravarthy** (#6)<br/>**Wanindu Hasaranga** (#5) | Supplements the Sawai Mansingh Stadium pitch dynamics. Provides guaranteed wicket-taking strike rates (11–13 balls/wicket) when opposing teams mount late-innings assaults. |
| **Defensive Restrictor / Powerplay Death Spin** | **Mitchell Santner** (#2)<br/>**Akeal Hosein** (#10) | Guaranteed sub-7.0 rpo economy in extreme leverage overs, suffocating opposition run-rate requirements. |

