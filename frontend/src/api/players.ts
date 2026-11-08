/**
 * Player discovery, evaluation, explainability, and ranking endpoints.
 */

import { request } from './client';
import type {
  PlayerDetailedExplanation,
  PlayerListResponse,
  PlayerMaster,
  PlayerScoreBreakdown,
  PlayerScoreResult,
  RankingResponse,
} from './types';

export const playerApi = {
  /**
   * List and search canonical player master records.
   */
  async list(params?: {
    q?: string;
    role?: string;
    is_eligible?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<PlayerListResponse> {
    const query = new URLSearchParams();
    if (params?.q) query.append('q', params.q);
    if (params?.role) query.append('role', params.role);
    if (params?.is_eligible !== undefined)
      query.append('is_eligible', String(params.is_eligible));
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.offset) query.append('offset', String(params.offset));

    const qs = query.toString();
    return request<PlayerListResponse>(`/players${qs ? `?${qs}` : ''}`);
  },

  /**
   * Fetch canonical player master biographical record by ID.
   */
  async get(playerId: string): Promise<PlayerMaster> {
    return request<PlayerMaster>(`/players/${encodeURIComponent(playerId)}`);
  },

  /**
   * Fetch official VOR leaderboard with multi-criteria tie-breakers.
   */
  async getRankings(params?: {
    run_id?: string;
    role?: string;
  }): Promise<RankingResponse> {
    const query = new URLSearchParams();
    if (params?.run_id) query.append('run_id', params.run_id);
    if (params?.role && params.role !== 'ALL') query.append('role', params.role);

    const qs = query.toString();
    return request<RankingResponse>(`/scoring/rankings${qs ? `?${qs}` : ''}`);
  },

  /**
   * Fetch full VOR evaluation score, sample sizes, and dimension percentiles.
   */
  async getScore(playerId: string, runId?: string): Promise<PlayerScoreResult> {
    const query = runId ? `?run_id=${encodeURIComponent(runId)}` : '';
    return request<PlayerScoreResult>(
      `/scoring/players/${encodeURIComponent(playerId)}${query}`
    );
  },

  /**
   * Fetch explainability factor attribution, strengths, and narrative summary.
   */
  async getExplanation(
    playerId: string,
    runId?: string
  ): Promise<PlayerDetailedExplanation> {
    const query = runId ? `?run_id=${encodeURIComponent(runId)}` : '';
    return request<PlayerDetailedExplanation>(
      `/explainability/players/${encodeURIComponent(playerId)}${query}`
    );
  },

  /**
   * Fetch mathematical factor decomposition and reconciliation audit.
   */
  async getBreakdown(
    playerId: string,
    runId?: string
  ): Promise<PlayerScoreBreakdown> {
    const query = runId ? `?run_id=${encodeURIComponent(runId)}` : '';
    return request<PlayerScoreBreakdown>(
      `/explainability/players/${encodeURIComponent(playerId)}/breakdown${query}`
    );
  },
};

