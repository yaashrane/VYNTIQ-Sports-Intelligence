# VYNTIQ — Canonical Sports Data Dictionary

**Document Reference:** DATA-VYNTIQ-001  
**Document Version:** 1.0.0  
**Status:** Approved Architectural Baseline  

---

## 1. Data Modeling Philosophy & Provenance Notice

> [!IMPORTANT]
> **Data Modeling Notice: Proposed Canonical Model**  
> All entity schemas, field names, and data types in this document represent **VYNTIQ's internal canonical data model**. They do **NOT** assume or claim that the official Rajasthan Royals (SuperRR) dataset uses these exact field names.
>
> The ingestion engine utilizes a dynamic **Header Inspector & Column Mapping Adapter** to translate arbitrary source headers (from CSV, JSON, or external repositories) into this unified internal schema upon ingestion.

---

## 2. Ingestion Mapping Strategy

To maintain complete independence from varying source data formats:

```
[Raw Source File: CSV / JSON]
         │ (e.g., "striker", "batter", "batsman_name", "Player")
         ▼
[Header Inspection & Fuzzy Token Resolver]
         │
         ▼
[Canonical Column Mapping] ──► { "striker" ➔ "batter_name" }
         │
         ▼
[Two-Tiered Validation Gate: Pydantic v2 Types + Cricket Constraints]
         │
         ├─► [Valid Records] ──► [PostgreSQL / SQLite Canonical Deliveries]
         └─► [Invalid Rows]  ──► [Quarantine Diagnostic Error Log]
```

---

## 3. Canonical Entity Specifications

### 3.1 Entity: `players` (Athlete Master Record)

| Field Name | Type | Constraint | Required? | Description & Validation Rules |
| :--- | :--- | :--- | :---: | :--- |
| `player_id` | `VARCHAR(64)` | PK | **Yes** | Unique identifier (e.g., hash or source UUID). |
| `canonical_name` | `VARCHAR(128)`| NOT NULL | **Yes** | Standardized display name (e.g., "Sanju Samson"). |
| `primary_role` | `VARCHAR(32)` | Enum | **Yes** | `BATTER`, `BOWLER`, `ALL_ROUNDER`, `WICKETKEEPER`. |
| `batting_hand` | `VARCHAR(16)` | Enum | Optional | `RIGHT_HAND`, `LEFT_HAND`, `UNKNOWN`. |
| `bowling_style` | `VARCHAR(32)` | Enum | Optional | `RIGHT_ARM_PACE`, `LEFT_ARM_PACE`, `RIGHT_ARM_OFF_SPIN`, `LEFT_ARM_ORTHODOX`, `WRIST_SPIN`, `UNKNOWN`. |
| `nationality` | `VARCHAR(64)` | Standard | Optional | Country of sporting nationality. |
| `dob` | `DATE` | ISO 8601 | Optional | Date of birth for age-category verification. |
| `is_eligible` | `BOOLEAN` | Default True | **Yes** | Flag for competition-specific eligibility (e.g., uncapped). |

---

### 3.2 Entity: `teams` (Team Master Record)

| Field Name | Type | Constraint | Required? | Description & Validation Rules |
| :--- | :--- | :--- | :---: | :--- |
| `team_id` | `VARCHAR(64)` | PK | **Yes** | Unique team identifier. |
| `team_name` | `VARCHAR(128)`| NOT NULL | **Yes** | Full team name (e.g., "Rajasthan Royals"). |
| `short_code` | `VARCHAR(8)`  | NOT NULL | Optional | 2–4 letter abbreviation (e.g., "RR"). |
| `competition` | `VARCHAR(64)` | NOT NULL | **Yes** | Tournament name (e.g., "IPL", "SuperRR_S2"). |

---

### 3.3 Entity: `venues` (Stadium / Pitch Record)

| Field Name | Type | Constraint | Required? | Description & Validation Rules |
| :--- | :--- | :--- | :---: | :--- |
| `venue_id` | `VARCHAR(64)` | PK | **Yes** | Unique venue identifier. |
| `venue_name` | `VARCHAR(128)`| NOT NULL | **Yes** | Stadium name (e.g., "Sawai Mansingh Stadium"). |
| `city` | `VARCHAR(64)` | Standard | Optional | City location. |
| `scoring_index` | `FLOAT` | Default 1.0 | Optional | Historical venue run-rate benchmark index. |

---

### 3.4 Entity: `matches` (Fixture Record)

| Field Name | Type | Constraint | Required? | Description & Validation Rules |
| :--- | :--- | :--- | :---: | :--- |
| `match_id` | `VARCHAR(64)` | PK | **Yes** | Unique fixture identifier. |
| `workspace_id` | `VARCHAR(64)` | FK | Optional | Scoped workspace (NULL for canonical historical). |
| `dataset_id` | `UUID` | FK | **Yes** | Source dataset reference. |
| `match_date` | `DATE` | ISO 8601 | **Yes** | Date of fixture. |
| `season` | `VARCHAR(16)` | NOT NULL | **Yes** | Season year (e.g., "2024", "2025"). |
| `venue_id` | `VARCHAR(64)` | FK | **Yes** | Venue reference. |
| `team1_id` | `VARCHAR(64)` | FK | **Yes** | Home / First listed team. |
| `team2_id` | `VARCHAR(64)` | FK | **Yes** | Away / Second listed team. |
| `toss_winner_id`| `VARCHAR(64)` | FK | Optional | Team that won the toss. |
| `toss_decision` | `VARCHAR(8)`  | Enum | Optional | `BAT` or `FIELD`. |
| `winner_id` | `VARCHAR(64)` | FK | Optional | Winning team (NULL if tied / no-result). |
| `dls_affected` | `BOOLEAN` | Default False| **Yes** | Weather-truncated match flag. |

---

### 3.5 Entity: `innings` (Innings Summary Record)

| Field Name | Type | Constraint | Required? | Description & Validation Rules |
| :--- | :--- | :--- | :---: | :--- |
| `innings_id` | `VARCHAR(64)` | PK | **Yes** | Composite key (`match_id` + `innings_num`). |
| `match_id` | `VARCHAR(64)` | FK | **Yes** | Match reference. |
| `innings_num` | `SMALLINT` | 1 or 2 | **Yes** | Innings index. |
| `batting_team_id`| `VARCHAR(64)`| FK | **Yes** | Batting team reference. |
| `bowling_team_id`| `VARCHAR(64)`| FK | **Yes** | Bowling team reference. |
| `total_runs` | `SMALLINT` | $\ge 0$ | **Yes** | Total innings score. |
| `total_wickets`| `SMALLINT` | $0 \dots 10$ | **Yes** | Total wickets fallen. |
| `total_legal_balls`| `SMALLINT`| $0 \dots 120$ | **Yes** | Total legal deliveries bowled. |

---

### 3.6 Entity: `deliveries` (Ball-by-Ball Atomic Event Record)

This is the primary analytical workhorse table of the platform:

| Field Name | Type | Constraint | Required? | Description & Validation Rules |
| :--- | :--- | :--- | :---: | :--- |
| `delivery_id` | `UUID` | PK | **Yes** | Unique delivery event UUID. |
| `workspace_id` | `VARCHAR(64)` | FK (Indexed) | Optional | Scoped workspace (NULL for canonical historical). |
| `dataset_id` | `UUID` | FK (Indexed) | **Yes** | Source dataset provenance hash. |
| `origin_type` | `VARCHAR(32)` | Enum | **Yes** | `CANONICAL_HISTORICAL` or `COMPETITION_SANDBOX`. |
| `match_id` | `VARCHAR(64)` | FK (Indexed) | **Yes** | Foreign key to `matches`. |
| `innings_num` | `SMALLINT` | 1 or 2 | **Yes** | Innings index. |
| `over_number` | `SMALLINT` | $0 \dots 19$ | **Yes** | Over integer index ($0$-indexed). |
| `ball_number` | `SMALLINT` | $1 \dots 6+$ | **Yes** | Ball index within over (can exceed 6 on extras). |
| `over_delivery`| `FLOAT` | $0.1 \dots 19.6+$| **Yes** | Standard cricket notation (e.g., 18.4). |
| `phase` | `VARCHAR(16)` | Enum | **Yes** | `POWERPLAY` (Overs 0–5), `MIDDLE` (Overs 6–14), `DEATH` (Overs 15–19). |
| `batter_id` | `VARCHAR(64)` | FK (Indexed) | **Yes** | Striker player reference. |
| `bowler_id` | `VARCHAR(64)` | FK (Indexed) | **Yes** | Delivery bowler reference. |
| `non_striker_id`| `VARCHAR(64)`| FK | Optional | Non-striker player reference. |
| `batter_runs` | `SMALLINT` | $0 \dots 6$ | **Yes** | Runs scored off the bat. |
| `extras_runs` | `SMALLINT` | $\ge 0$ | **Yes** | Total extras conceded on delivery. |
| `extras_type` | `VARCHAR(16)` | Enum | Optional | `WIDE`, `NO_BALL`, `BYE`, `LEG_BYE`, `PENALTY`, `NONE`. |
| `is_legal` | `BOOLEAN` | Calculated | **Yes** | False if `extras_type` in (`WIDE`, `NO_BALL`). |
| `total_runs` | `SMALLINT` | $0 \dots 7+$ | **Yes** | Sum of `batter_runs + extras_runs`. |
| `is_wicket` | `BOOLEAN` | Default False| **Yes** | Indicates whether a wicket fell on the delivery. |
| `dismissed_player_id`| `VARCHAR(64)`| FK | Optional | Player dismissed (Mandatory if `is_wicket = True`). |
| `dismissal_kind`| `VARCHAR(32)`| Enum | Optional | `BOWLED`, `CAUGHT`, `LBW`, `RUN_OUT`, `STUMPED`, `HIT_WICKET`, `CAUGHT_AND_BOWLED`. |
| `is_super_over`| `BOOLEAN` | Default False| **Yes** | Tie-breaker delivery flag. |

#### Optional Tracking Extensions (Contingent on Tracking Data Availability):
| Field Name | Type | Constraint | Required? | Description |
| :--- | :--- | :--- | :---: | :--- |
| `pitch_x_coord`| `FLOAT` | Optional | No | Lateral pitch coordinate (line). |
| `pitch_y_coord`| `FLOAT` | Optional | No | Longitudinal pitch coordinate (length). |
| `wagon_x_coord`| `FLOAT` | Optional | No | Wagon wheel angle / 2D coordinate. |
| `release_speed`| `FLOAT` | Optional | No | Delivery release speed in km/h. |

---

## 4. Multi-Tenant Workspace & Ingestion Entities

### 4.1 Entity: `workspaces` (Tenant Registry)
* `workspace_id`: Primary Key (e.g., `'workspace_super_rr_s2'`).
* `name`: Workspace Name (`"SuperRR Selector Season 2"`).
* `description`: Workspace notes and purpose.
* `created_at`: Creation timestamp.

### 4.2 Entity: `workspace_datasets` (Ingested Upload Manifest)
* `dataset_id`: UUID Primary Key.
* `workspace_id`: Scoped Workspace FK.
* `origin_type`: `CANONICAL_HISTORICAL` or `COMPETITION_SANDBOX`.
* `source_filename`: Original uploaded filename.
* `file_sha256`: Cryptographic hash ensuring deduplication.
* `row_count`: Total rows parsed.
* `quarantine_count`: Count of rejected rows.
* `uploaded_at`: Upload timestamp.

### 4.3 Entity: `scouting_shortlists` (Candidate Shortlist)
* `shortlist_id`: UUID Primary Key.
* `workspace_id`: Scoped Workspace FK.
* `name`: Shortlist Name (e.g., `"SuperRR Final Top 10 Picks"`).
* `description`: Scouting objectives.
* `created_at`: Creation timestamp.

### 4.4 Entity: `shortlist_candidates` (Shortlist Item)
* `shortlist_id`: FK to `scouting_shortlists`.
* `player_id`: FK to `players`.
* `rank_order`: Position in shortlist ($1 \dots 10$).
* `role_badge`: Tagged role (e.g., `"Death Overs Finisher"`).
* `vor_score`: Composite VOR score at time of shortlisting.
* `analyst_notes`: Tactical markdown commentary.

---

## 5. Ingestion Validation Constraints & Rules

1. **Monotonic Delivery Progression:** Within any innings, `over_number` must not decrement, and legal deliveries per over must not exceed 6.
2. **Run Tally Consistency:** `total_runs` must strictly equal `batter_runs + extras_runs`. Any discrepancy triggers row quarantine.
3. **Dismissal Integrity:** If `is_wicket == True`, `dismissal_kind` must be recognized and `dismissed_player_id` cannot be null.
4. **Extras Accounting:** Deliveries with `extras_type == 'WIDE'` must not increment balls faced by the batter.
5. **Idempotent Ingestion:** Re-uploading a file with an identical `file_sha256` hash returns an `ALREADY_INGESTED` confirmation without duplicating records.
