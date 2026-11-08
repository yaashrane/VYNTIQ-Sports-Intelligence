/**
 * TypeScript type definitions mirroring VYNTIQ Backend API v1 models.
 */

export type WorkspaceStatus = 'DRAFT' | 'ACTIVE' | 'COMPLETED' | 'ARCHIVED';

export type SportType = 'CRICKET';

export type ReviewStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'NEEDS_REVIEW';

export type EligibilityStatus = 'ELIGIBLE' | 'EXCLUDED' | 'CONDITIONALLY_ELIGIBLE';

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
