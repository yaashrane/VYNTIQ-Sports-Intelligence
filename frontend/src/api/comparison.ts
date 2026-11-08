/**
 * Head-to-head multi-player comparison API endpoints.
 */

import { request } from './client';
import type { ComparisonMetadata, PlayerComparisonResponse } from './types';

export const comparisonApi = {
  /**
   * Execute multi-player comparison (2 to 5 players) with compatibility gating.
   */
  async comparePlayers(payload: {
    player_ids: string[];
    run_id?: string;
    baseline_player_id?: string;
  }): Promise<PlayerComparisonResponse> {
    return request<PlayerComparisonResponse>('/comparisons/players', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Retrieve stored comparison by ID.
   */
  async getComparison(comparisonId: string): Promise<PlayerComparisonResponse> {
    return request<PlayerComparisonResponse>(
      `/comparisons/${encodeURIComponent(comparisonId)}`
    );
  },

  /**
   * Retrieve comparison metadata and directionality guidelines.
   */
  async getMetadata(): Promise<ComparisonMetadata> {
    return request<ComparisonMetadata>('/comparisons/metadata');
  },
};

