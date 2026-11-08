/**
 * Workspace and shortlisting API endpoints.
 */

import { request } from './client';
import type {
  CompetitionConfig,
  CompetitionConfigUpdatePayload,
  DatasetSummary,
  ShortlistCandidate,
  ShortlistDetail,
  ShortlistSummary,
  Workspace,
  WorkspaceCreatePayload,
  WorkspaceDetail,
  WorkspaceStatus,
  WorkspaceUpdatePayload,
} from './types';

export const workspaceApi = {
  /**
   * List all workspaces with optional status filtering.
   */
  async list(status?: WorkspaceStatus): Promise<Workspace[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return request<Workspace[]>(`/workspaces${query}`);
  },

  /**
   * Fetch full workspace detail including its active configuration.
   */
  async get(workspaceId: string): Promise<WorkspaceDetail> {
    return request<WorkspaceDetail>(`/workspaces/${encodeURIComponent(workspaceId)}`);
  },

  /**
   * Create a new competition workspace sandbox.
   */
  async create(payload: WorkspaceCreatePayload): Promise<WorkspaceDetail> {
    return request<WorkspaceDetail>('/workspaces', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Update workspace metadata or lifecycle status.
   */
  async update(
    workspaceId: string,
    payload: WorkspaceUpdatePayload
  ): Promise<Workspace> {
    return request<Workspace>(`/workspaces/${encodeURIComponent(workspaceId)}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Archive a workspace.
   */
  async archive(workspaceId: string): Promise<Workspace> {
    return request<Workspace>(`/workspaces/${encodeURIComponent(workspaceId)}`, {
      method: 'DELETE',
    });
  },

  /**
   * Retrieve active competition configuration for a workspace.
   */
  async getConfiguration(workspaceId: string): Promise<CompetitionConfig> {
    return request<CompetitionConfig>(
      `/workspaces/${encodeURIComponent(workspaceId)}/configuration`
    );
  },

  /**
   * Update competition configuration parameters.
   */
  async updateConfiguration(
    workspaceId: string,
    payload: CompetitionConfigUpdatePayload
  ): Promise<CompetitionConfig> {
    return request<CompetitionConfig>(
      `/workspaces/${encodeURIComponent(workspaceId)}/configuration`,
      {
        method: 'PUT',
        body: JSON.stringify(payload),
      }
    );
  },

  /**
   * Retrieve datasets accessible to this workspace.
   */
  async getDatasets(workspaceId: string): Promise<DatasetSummary[]> {
    return request<DatasetSummary[]>(
      `/workspaces/${encodeURIComponent(workspaceId)}/datasets`
    );
  },

  /**
   * List shortlists generated for this workspace.
   */
  async listShortlists(workspaceId: string): Promise<ShortlistSummary[]> {
    return request<ShortlistSummary[]>(
      `/workspaces/${encodeURIComponent(workspaceId)}/shortlists`
    );
  },

  /**
   * Retrieve full details of a specific shortlist.
   */
  async getShortlist(
    workspaceId: string,
    shortlistId: string
  ): Promise<ShortlistDetail> {
    return request<ShortlistDetail>(
      `/workspaces/${encodeURIComponent(workspaceId)}/shortlists/${encodeURIComponent(
        shortlistId
      )}`
    );
  },

  /**
   * Submit scout review disposition on a candidate.
   */
  async reviewCandidate(
    workspaceId: string,
    shortlistId: string,
    playerId: string,
    reviewStatus: string,
    reviewerNotes?: string
  ): Promise<ShortlistCandidate> {
    return request<ShortlistCandidate>(
      `/workspaces/${encodeURIComponent(workspaceId)}/shortlists/${encodeURIComponent(
        shortlistId
      )}/candidates/${encodeURIComponent(playerId)}/review`,
      {
        method: 'POST',
        body: JSON.stringify({
          review_status: reviewStatus,
          reviewer_notes: reviewerNotes,
        }),
      }
    );
  },
};
