import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

describe('VYNTIQ Application Shell & Navigation', () => {
  beforeEach(() => {
    // Mock global fetch for health check and initial workspace list
    globalThis.fetch = vi.fn().mockImplementation((url: string | URL | Request) => {
      const urlStr = String(url);
      if (urlStr.includes('/health')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            status: 'healthy',
            version: '1.0.0',
            environment: 'development',
          }),
        } as Response);
      }
      if (urlStr.includes('/workspaces')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => [
            {
              workspace_id: 'ws_rr_s2',
              name: 'Rajasthan Royals SuperRR S2',
              description: 'Official competition workspace.',
              sport_type: 'CRICKET',
              competition_name: 'SuperRR Selector',
              season_or_edition: 'Season 2',
              status: 'ACTIVE',
              dataset_references: [],
              created_at: '2026-11-08T12:00:00Z',
              updated_at: '2026-11-08T12:00:00Z',
            },
          ],
        } as Response);
      }
      return Promise.reject(new Error(`Unhandled URL: ${urlStr}`));
    });
  });

  it('renders the application shell with brand identity and tagline', async () => {
    render(<App />);

    // Brand and Tagline presence
    expect(await screen.findAllByText('VYNTIQ')).not.toHaveLength(0);
    expect(await screen.findAllByText('Sports Intelligence')).not.toHaveLength(0);
    expect(
      await screen.findAllByText(/Every Metric Tells a Story/i)
    ).not.toHaveLength(0);
  });

  it('renders primary navigation items with appropriate state', async () => {
    render(<App />);

    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Workspaces')).toBeInTheDocument();
    expect(screen.getByText('Player Explorer')).toBeInTheDocument();
    expect(screen.getByText('Shortlists')).toBeInTheDocument();
    expect(screen.getByText('Comparisons')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
  });
});

