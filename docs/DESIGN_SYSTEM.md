# VYNTIQ — Editorial Sports Analytics Design System

**Design Philosophy:** Editorial Sports Intelligence  
**Tone:** Analytical, High-Precision, Restrained, Boardroom-Ready  
**Document Version:** 1.0.0  
**Status:** Approved Architectural Baseline  

---

## 1. Visual Philosophy & Strict Editorial Rules

VYNTIQ is built for sports directors, elite scouts, and high-performance analysts. The visual language rejects decorative clutter, generic SaaS tropes, and flashy gamer aesthetics in favor of a **scholarly, high-density editorial sports journal**.

### Strict Anti-Patterns (BANNED from VYNTIQ)
- **NO Excessive KPI Cards:** Do not plaster the screen with 12 identical square boxes showing raw numbers without context.
- **NO Random Gradients & Glowing Borders:** No cyber/neon aesthetics or glowing drop shadows.
- **NO Unnecessary Glassmorphism:** Avoid blurry frosted-glass backgrounds that degrade text legibility.
- **NO Over-Rounded Containers:** Standardize on disciplined, subtle border radiuses ($4\text{px} \dots 8\text{px}$).
- **NO Decorative Charts Without Analytical Meaning:** Every chart must answer an explicit tactical question (e.g., phase split, pitch length distribution, radar gap).
- **NO Unformatted Monospace Strings:** Use tabular lining figures with proper decimal alignments for all statistical figures.

---

## 2. Color Palette & Token Architecture

The color system combines an authoritative dark ground with refined editorial accents. Accent colors are used sparingly for analytical emphasis (e.g., highlighting an outlier, indicating positive/negative delta) rather than mere decoration.

```
┌────────────────────────────────────────────────────────────────────────┐
│ PRIMARY FOUNDATION PALETTE                                             │
├─────────────────────┬─────────────────────┬────────────────────────────┤
│ Deep Charcoal       │ Royal Magenta       │ Sage Lime                  │
│ #111318             │ #D62978             │ #B9D66C                    │
│ [Primary Surface]   │ [Primary Accent]    │ [Positive Delta / Growth]  │
├─────────────────────┴─────────────────────┴────────────────────────────┤
│ Warm Ivory                                                             │
│ #F1EFEA                                                                │
│ [Primary Editorial Text / Light Surface Foundation]                    │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Complete Color Token Specifications

| Token Name | Hex Code | HSL / RGB | Purpose / Usage |
| :--- | :--- | :--- | :--- |
| `surface-ground` | `#111318` | `rgb(17, 19, 24)` | Primary application background; deep, non-fatiguing matte charcoal |
| `surface-card` | `#181B22` | `rgb(24, 27, 34)` | Primary container cards, data table wrappers, panel surfaces |
| `surface-elevated` | `#222630` | `rgb(34, 38, 48)` | Dropdown menus, modal dialogs, elevated hover states |
| `surface-border` | `#2D323E` | `rgb(45, 50, 62)` | 1px hairline dividing borders; subtle, high structural discipline |
| `text-primary` | `#F1EFEA` | `rgb(241, 239, 234)` | Warm Ivory; primary headers, critical data points, high-contrast text |
| `text-secondary` | `#9DA3B4` | `rgb(157, 163, 180)` | Muted slate; metadata labels, column headers, descriptive captions |
| `text-tertiary` | `#636B7E` | `rgb(99, 107, 126)` | Subtle gray; footnotes, inactive tabs, disabled states |
| `accent-magenta` | `#D62978` | `rgb(214, 41, 120)` | Royal Magenta; key interactive highlights, high-tier status, brand mark |
| `accent-lime` | `#B9D66C` | `rgb(185, 214, 108)` | Sage Lime; positive delta ($+\Delta$), elite efficiency, target match |
| `status-negative` | `#E05D52` | `rgb(224, 93, 82)` | Negative delta ($-\Delta$), high risk, defensive vulnerability |
| `status-warning` | `#E5A83B` | `rgb(229, 168, 59)` | Low sample size flag, borderline qualification, caution indicator |

---

## 3. Typography & Hierarchy System

Typography bridges academic sports journalism and high-density financial data terminals.

### 3.1 Typeface Families
* **Headings & Key Metrics:** **Manrope** (Google Fonts) — Geometric, modern, highly legible with sharp geometric proportions.
* **Body Text & UI Controls:** **Inter** (Google Fonts) — Exceptional legibility at micro-sizes, neutral personality.
* **Statistical Values & Numerical Grids:** **Inter / Manrope with `font-variant-numeric: tabular-nums`** — Ensures every digit shares identical horizontal advance width so decimal points and columns align vertically with micro-precision.

### 3.2 Type Scale

| Style / Token | Font | Weight | Size (px / rem) | Line Height | Tracking | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `display-1` | Manrope | 700 (Bold) | 36px / 2.25rem | 1.15 | -0.03em | Primary Player Profile Hero Name |
| `heading-1` | Manrope | 600 (SemiBold) | 24px / 1.5rem | 1.25 | -0.02em | Section Headings, Modal Titles |
| `heading-2` | Manrope | 600 (SemiBold) | 18px / 1.125rem | 1.30 | -0.01em | Card Titles, Comparison Subheaders |
| `body-editorial`| Inter | 400 (Regular) | 15px / 0.9375rem| 1.60 | 0.00em | Narrative Scouting Dossier Commentary |
| `body-ui` | Inter | 500 (Medium) | 13px / 0.8125rem| 1.40 | +0.01em | Table content, Filter labels, Buttons |
| `metric-stat` | Manrope | 700 (Bold) | 28px / 1.75rem | 1.10 | -0.02em | Core Rating Score (Tabular Numerals) |
| `metric-data` | Inter | 600 (SemiBold) | 13px / 0.8125rem| 1.00 | 0.00em | Table cell numbers (Tabular Numerals) |
| `caption` | Inter | 400 (Regular) | 11px / 0.6875rem| 1.30 | +0.02em | Column sub-labels, Footnotes, Sample sizes |

---

## 4. Spacing, Layout Grid & Structural Tokens

A strict 4px / 8px baseline grid maintains spatial discipline across views:

```
Space Tokens:
  --space-1:  4px
  --space-2:  8px
  --space-3:  12px
  --space-4:  16px
  --space-6:  24px
  --space-8:  32px
  --space-12: 48px
```

* **Grid System:** 12-column responsive fluid grid with fixed max-width container ($1440\text{px}$) on high-resolution displays.
* **Card Borders:** `1px solid var(--surface-border)`.
* **Border Radius:**
  * Small UI controls (Pills, Buttons, Badges): `4px`
  * Data Cards, Table Panels, Charts: `6px`
  * Modal Windows, Dossier Drawers: `8px`
  * *(Strictly no pill-shaped rounded containers greater than 8px for analytical surfaces)*.

---

## 5. Data Presentation & Table Standards

Data tables are the core workhorse of VYNTIQ. They must follow strict analytical formatting:

1. **Header Alignment:**
   * Text / Identifier columns: Left-aligned.
   * Numerical / Statistical columns: **Right-aligned** with headers aligned directly above the decimal positions.
   * Status / Tier badges: Center-aligned.
2. **Tabular Numerals:** Always apply `.font-tabular` (`font-variant-numeric: tabular-nums lining-nums`).
3. **Zebra Striping vs. Clean Hairlines:** Avoid dark/light zebra stripes that create optical illusions; use clean `1px` horizontal border dividers (`#2D323E`) with subtle hover highlight (`#1F232D`).
4. **Contextual Delta Indicators:**
   * $+5.2$ in Sage Lime (`#B9D66C`) with a crisp upward indicator `↑`.
   * $-3.8$ in Coral Red (`#E05D52`) with a downward indicator `↓`.
   * Flat $\pm 0.0$ in Muted Slate (`#9DA3B4`) with a neutral dash `—`.
5. **Sample Size Disclaimers:** Any metric derived from $< 30$ events must render a subtle warning dot with an analytical tooltip indicating the confidence interval.

---

## 6. Chart Presentation Guidelines (Plotly & Vector Styling)

Charts must integrate seamlessly with the editorial dark theme:

* **Background:** Transparent (`rgba(0,0,0,0)`) or matching `surface-card` (`#181B22`).
* **Grid Lines:** Hairline grid lines `#222630` at `0.5px` width; never prominent white or heavy lines.
* **Axis Labels:** Inter 11px in Muted Slate (`#9DA3B4`).
* **Radar Chart Standard:**
  * Web / Spoke Lines: `#2D323E`.
  * Polygon Stroke: Royal Magenta (`#D62978`) at 2px thickness.
  * Polygon Fill: `rgba(214, 41, 120, 0.15)` (restrained transparency).
  * Comparison Polygon: Sage Lime (`#B9D66C`) with fill `rgba(185, 214, 108, 0.15)`.
* **Tooltips:** Crisp dark card (`#111318` with `#2D323E` border), tabular formatting, displaying absolute value, cohort percentile, and sample size $N$.

---

## 7. Component Specifications

### 7.1 Metric Pill Component
```
┌─────────────────────────────────┐
│ DEATH OVERS SR                  │  ← 10px Inter Upper, Muted Slate
│ 188.42           +18.4% ↑       │  ← 18px Manrope Bold, Warm Ivory | 11px Lime
└─────────────────────────────────┘
```

### 7.2 Capability Radar Component
* Six normalized axes: *Powerplay Impact*, *Middle Overs Rotation*, *Death Finishing*, *Boundary Efficiency*, *Dot Ball Suppression*, *Pressure Leverage*.
* Every vertex displays the metric label and the 0–100 percentile score.

### 7.3 Head-to-Head Comparison Matrix
* Fixed left column for Metric Category and Metric Name.
* Dynamic columns for Player 1, Player 2, (Player 3, Player 4).
* The leading performer in each row receives a subtle Sage Lime accent highlight and bold tabular weight.

### 7.4 Explainability Accordion ("The Story Behind the Metric")
* Expandable row below every rating score.
* Deconstructs the overall rating into primary positive attributes ($+ \text{pts}$) and dragging factors ($-\text{pts}$) with clear plain-English tactical context.

---

## 8. State Specifications: Loading, Empty, and Error

| State | Visual Treatment & User Guidance |
| :--- | :--- |
| **Loading State** | Skeleton wireframe placeholders matching exact card/table proportions using a subtle `#181B22` to `#222630` pulse animation. No spinner wheels in primary data tables. |
| **Empty State** | Clean editorial message container: A precise geometric icon (e.g. search filter), a clear title (e.g., *"No Players Match Active Criteria"*), and a discrete secondary action (*"Reset Phase Filters"* or *"Broaden Sample Size"*). |
| **Error / Quarantine State** | High-visibility analytical alert: Deep charcoal card with a `#E05D52` hairline border, an explicit diagnostic code (e.g., `ERR_INGEST_INVALID_OVER_SEQUENCE`), and a structured line-by-line inspection log. |

