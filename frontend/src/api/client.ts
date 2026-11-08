/**
 * Centralized fetch API client for VYNTIQ.
 */

import type { ApiError } from './types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class ApiException extends Error {
  public code: string;
  public status: number;
  public details?: Array<{ field?: string; message: string; type?: string }>;

  constructor(status: number, error: ApiError) {
    super(error.message || `API Error (${status})`);
    this.name = 'ApiException';
    this.status = status;
    this.code = error.code || 'UNKNOWN_ERROR';
    this.details = error.details;
  }
}

export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let apiError: ApiError = {
      code: 'HTTP_ERROR',
      message: response.statusText || `Request failed with status ${response.status}`,
    };

    try {
      const data = await response.json();
      if (data && data.error) {
        apiError = data.error;
      } else if (data && data.message) {
        apiError = { code: 'SERVER_ERROR', message: data.message };
      }
    } catch {
      // Non-JSON response, keep default message
    }

    throw new ApiException(response.status, apiError);
  }

  // Handle empty 204 responses
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
