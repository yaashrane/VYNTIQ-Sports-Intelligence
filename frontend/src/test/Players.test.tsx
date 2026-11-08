import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { PlayerExplorerPage } from '../pages/PlayerExplorerPage';
import { PlayerProfilePage } from '../pages/PlayerProfilePage';
import { PlayerComparisonPage } from '../pages/PlayerComparisonPage';

const mockRankings = {
  run_id: 'run_test_01',
  cohort_id: 'IPL_T20_2024',
  total_ranked: 2,
  total_quarantined: 1,
  rankings: [
    {
      rank: 1,
      player_id: 'P_001',
      player_name: 'Sanju Samson',
      role: 'BATTER',
      vor_score: 88.5,
      raw_composite_score: 89.2,
      reliability_factor: 0.99,
      reliability_status: 'ADEQUATE',
      primary_tiebreaker: 91.2,
      is_qualified: true,
      is_eligible: true,
      quarantine_reasons: [],
    },
    {
      rank: 2,
      player_id: 'P_002',
      player_name: 'Jasprit Bumrah',
      role: 'BOWLER',
      vor_score: 92.1,
      raw_composite_score: 93.0,
      reliability_factor: 0.99,
      reliability_status: 'ADEQUATE',
      primary_tiebreaker: 95.0,
      is_qualified: true,
      is_eligible: true,
      quarantine_reasons: [],
    },
  ],
  quarantined: [
    {
      rank: 0,
      player_id: 'P_QUAR',
      player_name: 'Rookie Prospect',
      role: 'BATTER',
      vor_score: 0.0,
      raw_composite_score: 0.0,
      reliability_factor: 0.25,
      reliability_status: 'INSUFFICIENT_SAMPLE',
      primary_tiebreaker: 0.0,
      is_qualified: false,
      is_eligible: false,
      quarantine_reasons: ['Balls faced below minimum requirement'],
    },
  ],
};

const mockBio = {
  player_id: 'P_001',
  name: 'Sanju Samson',
  country: 'India',
  birth_date: '1994-11-11',
  batting_hand: 'RIGHT',
  bowling_style: 'Right-arm offbreak',
  role: 'BATTER',
  is_active: true,
};

const mockScore = {
  player_id: 'P_001',
  player_name: 'Sanju Samson',
  role: 'BATTER',
  cohort_id: 'IPL_T20_2024',
  vor_score: 88.5,
  raw_composite_score: 89.2,
  reliability_factor: 0.99,
  reliability_status: 'ADEQUATE',
  sample_size: {
    innings: 16,
    balls_faced: 380,
    legal_balls_bowled: 0,
    dismissals: 12,
    wickets: 0,
  },
  dimensions: {
    SCORING_EFFICIENCY: {
      dimension_id: 'SCORING_EFFICIENCY',
      dimension_name: 'Scoring Efficiency',
      weight: 0.35,
      dimension_score: 91.2,
      contribution_points: 31.92,
      metrics: [],
    },
    BOUNDARY_ABILITY: {
      dimension_id: 'BOUNDARY_ABILITY',
      dimension_name: 'Boundary Ability',
      weight: 0.35,
      dimension_score: 89.0,
      contribution_points: 31.15,
      metrics: [],
    },
    ACCELERATION: {
      dimension_id: 'ACCELERATION',
      dimension_name: 'Acceleration',
      weight: 0.3,
      dimension_score: 85.5,
      contribution_points: 25.65,
      metrics: [],
    },
  },
  is_qualified: true,
  is_eligible: true,
  explanation: {
    summary_text: 'Sanju Samson demonstrates exceptional scoring velocity and boundary frequency.',
    top_strengths: [
      'Elite Boundary Ability (92nd percentile)',
      'Superior Scoring Efficiency',
    ],
    drag_factors: ['Occasional dot ball percentage in middle overs'],
  },
  scoring_version: '1.0.0',
  provenance: {
    dataset_id: 'IPL_HISTORICAL_2024',
    calculated_at: '2026-11-08T10:00:00Z',
  },
};

const mockExplanation = {
  player_id: 'P_001',
  player_name: 'Sanju Samson',
  role: 'BATTER',
  status: 'EVALUATED',
  final_vor: 88.5,
  raw_composite_score: 89.2,
  reliability_factor: 0.99,
  reliability_status: 'ADEQUATE',
  top_strengths: [
    'Elite Boundary Ability (92nd percentile)',
    'Superior Scoring Efficiency',
  ],
  drag_factors: ['Occasional dot ball percentage in middle overs'],
  narrative_summary: 'Sanju Samson demonstrates exceptional scoring velocity and boundary frequency.',
  dimensions: [],
  excluded_or_unsupported_metrics: [],
  generated_at: '2026-11-08T10:00:00Z',
};

const mockBreakdown = {
  player_id: 'P_001',
  player_name: 'Sanju Samson',
  role: 'BATTER',
  cohort_id: 'IPL_T20_2024',
  run_id: 'run_test_01',
  dataset_id: 'IPL_HISTORICAL_2024',
  final_vor: 88.5,
  raw_composite_score: 89.2,
  reliability_factor: 0.99,
  sum_of_dimension_contributions: 89.2,
  reconciliation_discrepancy: 0.0,
  is_reconciled: true,
  dimensions: [],
};

const mockComparisonResponse = {
  comparison_id: 'comp_01',
  created_at: '2026-11-08T10:00:00Z',
  compatibility_status: 'FULLY_COMPATIBLE',
  compatibility_notes: ['Both athletes share identical role group (BATTER).'],
  players: [
    {
      player_id: 'P_001',
      player_name: 'Sanju Samson',
      role: 'BATTER',
      cohort_id: 'IPL_T20_2024',
      vor_score: 88.5,
      raw_composite_score: 89.2,
      reliability_factor: 0.99,
      reliability_status: 'ADEQUATE',
    },
    {
      player_id: 'P_003',
      player_name: 'Yashasvi Jaiswal',
      role: 'BATTER',
      cohort_id: 'IPL_T20_2024',
      vor_score: 86.0,
      raw_composite_score: 86.8,
      reliability_factor: 0.98,
      reliability_status: 'ADEQUATE',
    },
  ],
  is_cross_role: false,
  vor_comparison_valid: true,
  vor_leader_id: 'P_001',
  shared_dimensions: [
    {
      dimension_id: 'SCORING_EFFICIENCY',
      dimension_name: 'Scoring Efficiency',
      player_dimension_scores: { P_001: 91.2, P_003: 88.0 },
      score_difference: 3.2,
      favorable_player_id: 'P_001',
    },
  ],
  batting_comparison: [
    {
      metric_id: 'batting_strike_rate',
      display_name: 'Batting Strike Rate',
      directionality: 'HIGHER_IS_BETTER',
      unit: 'runs/100b',
      player_values: { P_001: 154.5, P_003: 162.0 },
      absolute_difference: 7.5,
      relative_difference_pct: 4.8,
      favorable_player_id: 'P_003',
      favorable_player_name: 'Yashasvi Jaiswal',
    },
  ],
  bowling_comparison: [],
  data_quality_warnings: [],
  recommendation_narrative: 'Sanju Samson possesses superior overall VOR stability.',
};

const mockCrossRoleComparison = {
  comparison_id: 'comp_cross_01',
  created_at: '2026-11-08T10:00:00Z',
  compatibility_status: 'CROSS_ROLE_PARTIAL',
  compatibility_notes: [
    'Cross-role comparison active. Candidates belong to different roles; VOR scores cannot be directly equated.',
  ],
  players: [
    {
      player_id: 'P_001',
      player_name: 'Sanju Samson',
      role: 'BATTER',
      cohort_id: 'IPL_T20_2024',
      vor_score: 88.5,
      raw_composite_score: 89.2,
      reliability_factor: 0.99,
      reliability_status: 'ADEQUATE',
    },
    {
      player_id: 'P_002',
      player_name: 'Jasprit Bumrah',
      role: 'BOWLER',
      cohort_id: 'IPL_T20_2024',
      vor_score: 92.1,
      raw_composite_score: 93.0,
      reliability_factor: 0.99,
      reliability_status: 'ADEQUATE',
    },
  ],
  is_cross_role: true,
  vor_comparison_valid: false,
  vor_leader_id: null,
  shared_dimensions: [],
  batting_comparison: [],
  bowling_comparison: [],
  data_quality_warnings: [],
};

describe('Player Intelligence UI & Integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('PlayerExplorerPage renders player list, filtering, and comparison selection', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      const u = typeof url === 'string' ? url : '';
      if (u.includes('/scoring/rankings')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockRankings,
        } as Response);
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => [],
      } as Response);
    });

    render(
      <MemoryRouter initialEntries={['/players']}>
        <Routes>
          <Route path="/players" element={<PlayerExplorerPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Initial heading
    expect(screen.getByText('Player Intelligence Explorer')).toBeInTheDocument();

    // Verify player names rendered
    await waitFor(() => {
      expect(screen.getByText('Sanju Samson')).toBeInTheDocument();
      expect(screen.getByText('Jasprit Bumrah')).toBeInTheDocument();
    });

    // Verify search filter
    const searchInput = screen.getByPlaceholderText(/Search by player name/i);
    fireEvent.change(searchInput, { target: { value: 'Bumrah' } });

    expect(screen.queryByText('Sanju Samson')).not.toBeInTheDocument();
    expect(screen.getByText('Jasprit Bumrah')).toBeInTheDocument();

    // Clear search
    fireEvent.change(searchInput, { target: { value: '' } });
    expect(screen.getByText('Sanju Samson')).toBeInTheDocument();

    // Select players for comparison drawer
    const compareCheckboxes = screen.getAllByRole('checkbox');
    // Select two players
    fireEvent.click(compareCheckboxes[0]);
    fireEvent.click(compareCheckboxes[1]);

    // Comparison drawer shows selected button in header
    expect(screen.getByText(/Compare \(2\) Candidates/i)).toBeInTheDocument();
  });

  it('PlayerProfilePage renders complete evaluation, bio, explainability, and radar dimensions', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      const u = typeof url === 'string' ? url : '';
      if (u.includes('/explainability/players/P_001/breakdown')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockBreakdown,
        } as Response);
      }
      if (u.includes('/scoring/players/P_001')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockScore,
        } as Response);
      }
      if (u.includes('/explainability/players/P_001')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockExplanation,
        } as Response);
      }
      if (u.includes('/players/P_001')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockBio,
        } as Response);
      }
      return Promise.reject(new Error(`Unhandled URL: ${u}`));
    });

    render(
      <MemoryRouter initialEntries={['/players/P_001']}>
        <Routes>
          <Route path="/players/:playerId" element={<PlayerProfilePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Sanju Samson')).toBeInTheDocument();
      expect(screen.getByText('88.5')).toBeInTheDocument();
      expect(screen.getByText('Superior Scoring Efficiency')).toBeInTheDocument();
      expect(
        screen.getByText('Occasional dot ball percentage in middle overs')
      ).toBeInTheDocument();
    });

    // Radar chart title and accessible role dimension table
    expect(screen.getByText('Role Dimension Profile')).toBeInTheDocument();
    expect(screen.getAllByText('Scoring Efficiency')[0]).toBeInTheDocument();
  });

  it('PlayerComparisonPage enforces cross-role warning when incompatible roles are compared', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      const u = typeof url === 'string' ? url : '';
      if (u.includes('/scoring/rankings')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockRankings,
        } as Response);
      }
      if (u.includes('/comparisons/players')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockCrossRoleComparison,
        } as Response);
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({}),
      } as Response);
    });

    render(
      <MemoryRouter initialEntries={['/comparisons?players=P_001,P_002']}>
        <Routes>
          <Route path="/comparisons" element={<PlayerComparisonPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Cross-role banner must be displayed
    await waitFor(() => {
      expect(
        screen.getByText(/Cross-Role Statistical Advisory/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Cross-role comparison active/i)
      ).toBeInTheDocument();
    });

    expect(screen.getAllByText('Sanju Samson').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Jasprit Bumrah').length).toBeGreaterThan(0);
  });

  it('PlayerComparisonPage renders side-by-side metrics and dimension leaders for compatible roles', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      const u = typeof url === 'string' ? url : '';
      if (u.includes('/scoring/rankings')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockRankings,
        } as Response);
      }
      if (u.includes('/comparisons/players')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockComparisonResponse,
        } as Response);
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({}),
      } as Response);
    });

    render(
      <MemoryRouter initialEntries={['/comparisons?players=P_001,P_003']}>
        <Routes>
          <Route path="/comparisons" element={<PlayerComparisonPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('Sanju Samson').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Yashasvi Jaiswal').length).toBeGreaterThan(0);
      expect(screen.getByText('Role Dimension Matrix')).toBeInTheDocument();
      expect(screen.getByText('Batting Performance Metrics')).toBeInTheDocument();
    });

    // Verify dimension leader indicator
    expect(screen.getByText('Leader: Sanju Samson')).toBeInTheDocument();
  });
});
