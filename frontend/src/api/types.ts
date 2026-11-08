/**
 * TypeScript type definitions mirroring VYNTIQ Backend API v1 models.
 */

export type WorkspaceStatus = 'DRAFT' | 'ACTIVE' | 'COMPLETED' | 'ARCHIVED';

export type SportType = 'CRICKET';

export type ReviewStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'NEEDS_REVIEW';

export type EligibilityStatus = 'ELIGIBLE' | 'EXCLUDED' | 'CONDITIONALLY_ELIGIBLE';

export type PlayerRole = 'BATTER' | 'BOWLER' | 'ALL_ROUNDER' | 'WICKETKEEPER' | 'UNKNOWN';

export type ReliabilityStatus =
  | 'ADEQUATE'
  | 'RELIABILITY_DISCOUNTED'
  | 'INSUFFICIENT_SAMPLE'
  | 'ZERO_SAMPLE';

export type MetricDirection = 'HIGHER_IS_BETTER' | 'LOWER_IS_BETTER' | 'NEUTRAL';

export type ComparisonCompatibilityStatus =
  | 'FULLY_COMPATIBLE'
  | 'CROSS_ROLE_PARTIAL'
  | 'CROSS_COHORT_CAUTION'
  | 'INSUFFICIENT_SAMPLE_WARNING';

// ==============================================================================
// ATHLETE MASTER
// ==============================================================================

export interface PlayerMaster {
  player_id: string;
  canonical_name: string;
  primary_role?: string | null;
  batting_hand?: string | null;
  bowling_style?: string | null;
  nationality?: string | null;
  dob?: string | null;
  is_eligible: boolean;
  created_at: string;
  updated_at: string;
}

export interface PlayerListResponse {
  total: number;
  limit: number;
  offset: number;
  players: PlayerMaster[];
}

// ==============================================================================
// VOR SCORING & RANKINGS
// ==============================================================================

export interface SampleSizeInfo {
  matches_count?: number;
  innings_count?: number;
  balls_faced?: number;
  legal_balls_bowled?: number;
  wickets?: number;
  dismissals?: number;
}

export interface NormalizedMetric {
  metric_id: string;
  display_name: string;
  raw_value?: number | null;
  percentile: number;
  directionality: MetricDirection;
  cohort_id: string;
  cohort_size: number;
  normalization_method: string;
}

export interface DimensionScore {
  dimension_id: string;
  dimension_name: string;
  dimension_score: number;
  weight: number;
  contribution_points: number;
  metrics: NormalizedMetric[];
}

export interface ScoreExplanation {
  final_vor: number;
  raw_composite: number;
  reliability_factor: number;
  reliability_status: ReliabilityStatus;
  top_strengths: string[];
  drag_factors: string[];
  missing_or_limited_dimensions: string[];
  summary_text: string;
}

export interface PlayerScoreResult {
  player_id: string;
  player_name: string;
  role: PlayerRole;
  cohort_id: string;
  vor_score: number;
  raw_composite_score: number;
  reliability_factor: number;
  reliability_status: ReliabilityStatus;
  sample_size: SampleSizeInfo;
  discipline_components?: Record<string, number>;
  dual_bonus_points?: number;
  dimensions: Record<string, DimensionScore>;
  is_qualified: boolean;
  is_eligible: boolean;
  explanation: ScoreExplanation;
  scoring_version: string;
  provenance: {
    dataset_id: string;
    calculated_at?: string;
  };
}

export interface RankedPlayer {
  rank: number;
  player_id: string;
  player_name: string;
  role: PlayerRole;
  vor_score: number;
  raw_composite_score: number;
  reliability_factor: number;
  reliability_status: ReliabilityStatus;
  primary_tiebreaker: number;
  is_qualified: boolean;
  is_eligible: boolean;
  quarantine_reasons: string[];
}

export interface RankingResponse {
  run_id: string;
  cohort_id: string;
  role_filter?: string | null;
  total_ranked: number;
  total_quarantined: number;
  rankings: RankedPlayer[];
  quarantined: RankedPlayer[];
}

// ==============================================================================
// EXPLAINABILITY
// ==============================================================================

export interface MetricContributionDetail {
  metric_id: string;
  display_name: string;
  raw_value?: number | null;
  normalized_percentile: number;
  directionality: MetricDirection;
  dimension_id: string;
  metric_weight_in_dimension: number;
  contribution_to_dimension: number;
  calculation_status: string;
  normalization_method: string;
  is_missing_or_fallback: boolean;
}

export interface DimensionContributionDetail {
  dimension_id: string;
  dimension_name: string;
  dimension_score: number;
  applied_weight: number;
  contribution_to_raw_composite: number;
  metrics: MetricContributionDetail[];
  sample_adequacy: string;
  is_limited: boolean;
}

export interface PlayerDetailedExplanation {
  player_id: string;
  player_name: string;
  role: PlayerRole;
  status: string;
  final_vor: number;
  raw_composite_score: number;
  reliability_factor: number;
  reliability_status: ReliabilityStatus;
  top_strengths: string[];
  drag_factors: string[];
  narrative_summary: string;
  dimensions: DimensionContributionDetail[];
  excluded_or_unsupported_metrics: string[];
  generated_at: string;
}

export interface PlayerScoreBreakdown {
  player_id: string;
  player_name: string;
  role: PlayerRole;
  cohort_id: string;
  run_id: string;
  dataset_id: string;
  final_vor: number;
  raw_composite_score: number;
  reliability_factor: number;
  sum_of_dimension_contributions: number;
  reconciliation_discrepancy: number;
  is_reconciled: boolean;
  dimensions: DimensionContributionDetail[];
}

// ==============================================================================
// PLAYER COMPARISON
// ==============================================================================

export interface PlayerComparisonHeader {
  player_id: string;
  player_name: string;
  role: PlayerRole;
  cohort_id: string;
  vor_score: number;
  raw_composite_score: number;
  reliability_factor: number;
  reliability_status: ReliabilityStatus;
  sample_size?: SampleSizeInfo;
}

export interface DimensionComparisonItem {
  dimension_id: string;
  dimension_name: string;
  player_dimension_scores: Record<string, number>;
  score_difference?: number | null;
  favorable_player_id?: string | null;
  metrics?: MetricComparisonItem[];
}

export interface MetricComparisonItem {
  metric_id: string;
  display_name: string;
  directionality: MetricDirection;
  unit?: string;
  player_values: Record<string, number | null>;
  player_percentiles?: Record<string, number | null>;
  absolute_difference?: number | null;
  relative_difference_pct?: number | null;
  favorable_player_id?: string | null;
  favorable_player_name?: string | null;
  notes?: string;
}

export interface PlayerComparisonResponse {
  comparison_id: string;
  created_at: string;
  compatibility_status: ComparisonCompatibilityStatus;
  compatibility_notes?: string[];
  players: PlayerComparisonHeader[];
  is_cross_role: boolean;
  vor_comparison_valid: boolean;
  vor_leader_id?: string | null;
  shared_dimensions: DimensionComparisonItem[];
  batting_comparison: MetricComparisonItem[];
  bowling_comparison: MetricComparisonItem[];
  data_quality_warnings?: string[];
  recommendation_narrative?: string;
}

export interface ComparisonMetadata {
  max_players_allowed: number;
  supported_roles: string[];
  compatibility_rules: string[];
  tie_breaking_rules: string[];
  directionality_conventions: Record<string, string>;
}

// ==============================================================================
// CONFIGURATION & WORKSPACES
// ==============================================================================

export interface AgeCriteria {
  min_age?: number | null;
  max_age?: number | null;
  age_cutoff_date?: string | null;
}

export interface ParticipationCriteria {
  min_matches?: number | null;
  min_balls_faced?: number | null;
  min_legal_balls_bowled?: number | null;
}

export interface CompetitionConfig {
  config_id: string;
  workspace_id: string;
  target_sport: string;
  target_roles: string[];
  age_criteria?: AgeCriteria | null;
  participation_criteria?: ParticipationCriteria | null;
  required_metrics: string[];
  evaluation_profile_version: string;
  shortlist_size: number;
  custom_eligibility_rules: Record<string, unknown>;
  dataset_ids: string[];
  version: string;
  created_at: string;
  updated_at: string;
}

export interface Workspace {
  workspace_id: string;
  name: string;
  description?: string | null;
  sport_type: string;
  competition_name: string;
  season_or_edition: string;
  status: WorkspaceStatus;
  dataset_references: string[];
  created_at: string;
  updated_at: string;
}

export interface WorkspaceDetail extends Workspace {
  configuration?: CompetitionConfig | null;
  shortlists_count: number;
}

export interface WorkspaceCreatePayload {
  workspace_id?: string;
  name: string;
  description?: string;
  sport_type?: SportType;
  competition_name: string;
  season_or_edition: string;
  initial_configuration?: {
    target_sport?: SportType;
    target_roles?: string[];
    shortlist_size?: number;
    age_criteria?: AgeCriteria;
    participation_criteria?: ParticipationCriteria;
  };
  dataset_references?: string[];
}

export interface WorkspaceUpdatePayload {
  name?: string;
  description?: string;
  competition_name?: string;
  season_or_edition?: string;
  status?: WorkspaceStatus;
  dataset_references?: string[];
}

export interface CompetitionConfigUpdatePayload {
  target_roles?: string[];
  age_criteria?: AgeCriteria;
  participation_criteria?: ParticipationCriteria;
  required_metrics?: string[];
  shortlist_size?: number;
  custom_eligibility_rules?: Record<string, unknown>;
  dataset_ids?: string[];
}

export interface DatasetSummary {
  dataset_id: string;
  workspace_id?: string | null;
  origin_type: string;
  source_filename: string;
  status: string;
  total_rows: number;
  valid_rows: number;
  quarantined_rows: number;
  created_at: string;
}

export interface ShortlistSummary {
  shortlist_id: string;
  workspace_id: string;
  name: string;
  dataset_id: string;
  scoring_run_id: string;
  config_version: string;
  methodology_version: string;
  target_size: number;
  eligible_count: number;
  excluded_count: number;
  shortlisted_count: number;
  status: string;
  created_at: string;
}

export interface ShortlistCandidate {
  candidate_entry_id: string;
  shortlist_id: string;
  workspace_id: string;
  player_id: string;
  player_name: string;
  assigned_role: string;
  rank: number;
  vor_score: number;
  raw_composite_score: number;
  reliability_factor: number;
  reliability_status: string;
  evaluation_ref: string;
  explainability_ref: string;
  eligibility_status: EligibilityStatus;
  review_status: ReviewStatus;
  reviewer_notes?: string | null;
  selection_timestamp: string;
}

export interface ShortlistDetail extends ShortlistSummary {
  candidates: ShortlistCandidate[];
  exclusion_summary: Record<string, string[]>;
}

export interface SystemHealth {
  status: string;
  timestamp: string;
  version: string;
  environment: string;
  database: {
    status: string;
    engine: string;
  };
}

export interface ApiError {
  code: string;
  message: string;
  details?: Array<{ field?: string; message: string; type?: string }>;
}
