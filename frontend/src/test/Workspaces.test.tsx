import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { WorkspaceProvider } from '../context/WorkspaceContext';
import { WorkspacesPage } from '../pages/WorkspacesPage';

describe('Workspaces Experience & Integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders loading state and displays workspace list on API success', async () => {
    const mockWorkspaces = [
      {
        workspace_id: 'ws_01',
        name: 'SuperRR Talent Hunt',
        description: 'Emerging domestic players.',
        sport_type: 'CRICKET',
        competition_name: 'SuperRR Selector',
        season_or_edition: 'Season 2',
        status: 'ACTIVE',
        dataset_references: [],
        created_at: '2026-11-08T10:00:00Z',
        updated_at: '2026-11-08T10:00:00Z',
      },
    ];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockWorkspaces,
    });

    render(
      <BrowserRouter>
        <WorkspaceProvider>
          <WorkspacesPage />
        </WorkspaceProvider>
      </BrowserRouter>
    );

    // Initial loading or immediate rendering
    expect(
      screen.getByText('Competition Workspaces')
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('SuperRR Talent Hunt')).toBeInTheDocument();
      expect(screen.getByText('Emerging domestic players.')).toBeInTheDocument();
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });
  });

  it('renders empty state when no workspaces exist', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    });

    render(
      <BrowserRouter>
        <WorkspaceProvider>
          <WorkspacesPage />
        </WorkspaceProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No Workspaces Found')).toBeInTheDocument();
    });
  });

  it('filters workspaces by search input', async () => {
    const mockWorkspaces = [
      {
        workspace_id: 'ws_01',
        name: 'Rajasthan Royals Scouting',
        description: 'First workspace.',
        sport_type: 'CRICKET',
        competition_name: 'SuperRR',
        season_or_edition: 'S2',
        status: 'ACTIVE',
        dataset_references: [],
        created_at: '2026-11-08T10:00:00Z',
        updated_at: '2026-11-08T10:00:00Z',
      },
      {
        workspace_id: 'ws_02',
        name: 'Mumbai Trials',
        description: 'Second workspace.',
        sport_type: 'CRICKET',
        competition_name: 'Domestic T20',
        season_or_edition: '2026',
        status: 'DRAFT',
        dataset_references: [],
        created_at: '2026-11-08T10:00:00Z',
        updated_at: '2026-11-08T10:00:00Z',
      },
    ];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockWorkspaces,
    });

    render(
      <BrowserRouter>
        <WorkspaceProvider>
          <WorkspacesPage />
        </WorkspaceProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Rajasthan Royals Scouting')).toBeInTheDocument();
      expect(screen.getByText('Mumbai Trials')).toBeInTheDocument();
    });

    // Enter search term
    const searchInput = screen.getByPlaceholderText(/Filter by name or competition/i);
    fireEvent.change(searchInput, { target: { value: 'Mumbai' } });

    expect(screen.queryByText('Rajasthan Royals Scouting')).not.toBeInTheDocument();
    expect(screen.getByText('Mumbai Trials')).toBeInTheDocument();
  });

  it('opens create workspace modal on action click', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    });

    render(
      <BrowserRouter>
        <WorkspaceProvider>
          <WorkspacesPage />
        </WorkspaceProvider>
      </BrowserRouter>
    );

    const createButtons = await screen.findAllByRole('button', {
      name: /Create Workspace/i,
    });
    fireEvent.click(createButtons[0]);

    expect(
      await screen.findByText('Create Competition Workspace')
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/Workspace Name/i)).toBeInTheDocument();
  });
});
