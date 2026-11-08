/**
 * Reports and Export API client for VYNTIQ.
 */

import { request } from './client';

export interface ReportCreatePayload {
  report_type:
    | 'COMPETITION_OVERVIEW'
    | 'INDIVIDUAL_PLAYER'
    | 'PLAYER_COMPARISON'
    | 'SHORTLIST';
  title?: string;
  player_id?: string;
  comparison_player_ids?: string[];
  shortlist_id?: string;
  run_id?: string;
  dataset_id?: string;
  include_reviewer_notes?: boolean;
}

export interface ReportResponse {
  report_id: string;
  workspace_id?: string | null;
  report_type: string;
  title: string;
  filename: string;
  file_size_bytes: number;
  sha256_hash: string;
  dataset_reference?: string | null;
  scoring_run_id?: string | null;
  generation_status: string;
  created_at: string;
  download_url: string;
}

export const reportApi = {
  async generateWorkspaceReport(
    workspaceId: string,
    payload: ReportCreatePayload
  ): Promise<ReportResponse> {
    return request<ReportResponse>(
      `/workspaces/${encodeURIComponent(workspaceId)}/reports`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },

  async generateStandaloneReport(
    payload: ReportCreatePayload
  ): Promise<ReportResponse> {
    return request<ReportResponse>('/reports', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getDownloadUrl(reportId: string, workspaceId?: string | null): string {
    const base = import.meta.env.VITE_API_BASE_URL || '/api/v1';
    if (workspaceId) {
      return `${base}/workspaces/${encodeURIComponent(workspaceId)}/reports/${encodeURIComponent(reportId)}/download`;
    }
    return `${base}/reports/${encodeURIComponent(reportId)}/download`;
  },
};
