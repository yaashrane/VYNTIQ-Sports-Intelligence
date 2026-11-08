/**
 * System and health monitoring API endpoints.
 */

import { request } from './client';
import type { SystemHealth } from './types';

export const systemApi = {
  /**
   * Check backend operational health and database connection.
   */
  async checkHealth(): Promise<SystemHealth> {
    return request<SystemHealth>('/health');
  },
};
