import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Search,
  ArrowUpDown,
  GitCompare,
  Eye,
  ShieldCheck,
  AlertCircle,
} from 'lucide-react';
import { playerApi } from '../api/players';
import type { RankedPlayer } from '../api/types';
import { Button } from '../components/common/Button';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorState } from '../components/common/ErrorState';

export const PlayerExplorerPage: React.FC = () => {
  const navigate = useNavigate();

  const [players, setPlayers] = useState<RankedPlayer[]>([]);
  const [quarantined, setQuarantined] = useState<RankedPlayer[]>([]);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [roleFilter, setRoleFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [sortBy, setSortBy] = useState<'rank' | 'vor' | 'name'>('rank');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [showQuarantined, setShowQuarantined] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const roles: Array<{ label: string; value: string }> = [
    { label: 'All Roles', value: 'ALL' },
    { label: 'Batters', value: 'BATTER' },
    { label: 'Bowlers', value: 'BOWLER' },
    { label: 'All-Rounders', value: 'ALL_ROUNDER' },
    { label: 'Wicketkeepers', value: 'WICKETKEEPER' },
  ];

  const loadRankings = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await playerApi.getRankings({
        role: roleFilter !== 'ALL' ? roleFilter : undefined,
      });
      setPlayers(res.rankings || []);
      setQuarantined(res.quarantined || []);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load player rankings from scoring engine.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [roleFilter]);

  useEffect(() => {
    loadRankings();
  }, [loadRankings]);

  const toggleCompare = (playerId: string) => {
    setSelectedForCompare((prev) => {
      if (prev.includes(playerId)) {
        return prev.filter((id) => id !== playerId);
      }
      if (prev.length >= 5) {
        alert('Maximum of 5 players can be compared simultaneously.');
        return prev;
      }
      return [...prev, playerId];
    });
  };

  const handleLaunchComparison = () => {
    if (selectedForCompare.length < 2) return;
    navigate(`/comparisons?players=${selectedForCompare.join(',')}`);
  };

  const displayedList = showQuarantined ? quarantined : players;

  const filteredPlayers = displayedList
    .filter((p) =>
      p.player_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.player_id.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === 'rank') {
        return sortOrder === 'asc' ? a.rank - b.rank : b.rank - a.rank;
      }
      if (sortBy === 'vor') {
        return sortOrder === 'asc' ? a.vor_score - b.vor_score : b.vor_score - a.vor_score;
      }
      return sortOrder === 'asc'
        ? a.player_name.localeCompare(b.player_name)
        : b.player_name.localeCompare(a.player_name);
    });

  return (
    <div className="space-y-6 animate-fade-in pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-border">
        <div>
          <h1 className="text-xl sm:text-2xl font-display font-bold text-text-primary">
            Player Intelligence Explorer
          </h1>
          <p className="text-xs text-text-secondary mt-0.5">
            Discover evaluated talent, inspect verified VOR scores, and audit evidence-based factor attributions.
          </p>
        </div>

        {selectedForCompare.length >= 2 && (
          <Button
            variant="primary"
            size="sm"
            icon={<GitCompare className="w-4 h-4" />}
            onClick={handleLaunchComparison}
          >
            Compare ({selectedForCompare.length}) Candidates
          </Button>
        )}
      </div>

      {/* Filter and Control Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Role Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
          {roles.map((r) => (
            <button
              key={r.value}
              onClick={() => setRoleFilter(r.value)}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors whitespace-nowrap ${
                roleFilter === r.value
                  ? 'bg-accent-magenta text-white font-semibold'
                  : 'bg-surface-card text-text-secondary hover:text-text-primary hover:bg-surface-elevated border border-surface-border'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>

        {/* Search & Qualification Toggle */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-text-secondary pointer-events-none" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by player name..."
              className="w-full pl-9 pr-3 py-2 text-xs bg-surface-card border border-surface-border rounded text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent-magenta focus:ring-1 focus:ring-accent-magenta"
            />
          </div>

          <button
            onClick={() => setShowQuarantined(!showQuarantined)}
            className={`px-3 py-2 text-xs font-medium rounded border transition-colors flex items-center gap-1.5 ${
              showQuarantined
                ? 'bg-status-warning/15 text-status-warning border-status-warning/30 font-semibold'
                : 'bg-surface-card text-text-secondary hover:text-text-primary border-surface-border'
            }`}
            title="Toggle between qualified candidates and sample-quarantined prospects"
          >
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Quarantine ({quarantined.length})</span>
          </button>
        </div>
      </div>

      {/* Main Table or Loading/Empty States */}
      {isLoading ? (
        <LoadingState message="Querying verified VOR leaderboards from scoring engine..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadRankings} />
      ) : filteredPlayers.length === 0 ? (
        <EmptyState
          icon={Users}
          title={searchTerm ? 'No Players Found' : 'No Evaluated Players'}
          description={
            searchTerm
              ? `No evaluated candidates matched "${searchTerm}".`
              : 'Execute a scoring calculation run in a competition workspace to populate player leaderboards.'
          }
          actionLabel={searchTerm ? 'Clear Search' : undefined}
          onAction={searchTerm ? () => setSearchTerm('') : undefined}
        />
      ) : (
        <div className="bg-surface-card border border-surface-border rounded overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs tabular-nums">
              <thead className="bg-surface-elevated text-text-secondary font-semibold uppercase text-[10px] tracking-wider border-b border-surface-border">
                <tr>
                  <th className="px-4 py-3 w-10 text-center">
                    <span className="sr-only">Compare</span>
                  </th>
                  <th
                    className="px-4 py-3 cursor-pointer hover:text-text-primary"
                    onClick={() => {
                      setSortBy('rank');
                      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                    }}
                  >
                    <div className="flex items-center gap-1">
                      <span>Rank</span>
                      <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th
                    className="px-4 py-3 cursor-pointer hover:text-text-primary"
                    onClick={() => {
                      setSortBy('name');
                      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                    }}
                  >
                    <div className="flex items-center gap-1">
                      <span>Athlete</span>
                      <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th className="px-4 py-3">Role</th>
                  <th
                    className="px-4 py-3 cursor-pointer hover:text-text-primary"
                    onClick={() => {
                      setSortBy('vor');
                      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                    }}
                  >
                    <div className="flex items-center gap-1">
                      <span>VOR Rating</span>
                      <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th className="px-4 py-3">Raw Composite</th>
                  <th className="px-4 py-3">Reliability C(N)</th>
                  <th className="px-4 py-3">Tiebreaker</th>
                  <th className="px-4 py-3">Eligibility</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {filteredPlayers.map((player) => {
                  const isChecked = selectedForCompare.includes(player.player_id);

                  return (
                    <tr
                      key={player.player_id}
                      className={`hover:bg-surface-elevated/40 transition-colors ${
                        isChecked ? 'bg-accent-magenta/5' : ''
                      }`}
                    >
                      {/* Compare Checkbox */}
                      <td className="px-4 py-3 text-center">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggleCompare(player.player_id)}
                          className="w-3.5 h-3.5 accent-accent-magenta rounded cursor-pointer"
                          aria-label={`Select ${player.player_name} for comparison`}
                        />
                      </td>

                      {/* Rank */}
                      <td className="px-4 py-3 font-display font-bold text-text-primary">
                        #{player.rank}
                      </td>

                      {/* Name */}
                      <td className="px-4 py-3 font-semibold text-text-primary">
                        <button
                          onClick={() => navigate(`/players/${player.player_id}`)}
                          className="hover:text-accent-magenta transition-colors text-left"
                        >
                          {player.player_name}
                        </button>
                      </td>

                      {/* Role */}
                      <td className="px-4 py-3 text-text-secondary">
                        <span className="px-2 py-0.5 rounded text-[10px] uppercase font-medium bg-surface-elevated border border-surface-border">
                          {player.role}
                        </span>
                      </td>

                      {/* VOR Score */}
                      <td className="px-4 py-3 font-display font-bold text-accent-magenta text-sm">
                        {(player.vor_score ?? 0).toFixed(1)}
                      </td>

                      {/* Raw Composite */}
                      <td className="px-4 py-3 text-text-secondary">
                        {player.raw_composite_score !== undefined
                          ? player.raw_composite_score.toFixed(1)
                          : '—'}
                      </td>

                      {/* Reliability C(N) */}
                      <td className="px-4 py-3">
                        <span
                          className={`text-[10px] font-medium px-2 py-0.5 rounded border ${
                            player.reliability_status === 'ADEQUATE'
                              ? 'text-accent-lime border-accent-lime/30 bg-accent-lime/10'
                              : player.reliability_status === 'INSUFFICIENT_SAMPLE'
                              ? 'text-status-negative border-status-negative/30 bg-status-negative/10'
                              : 'text-status-warning border-status-warning/30 bg-status-warning/10'
                          }`}
                        >
                          {(player.reliability_factor ?? 1).toFixed(2)} ({player.reliability_status || 'ADEQUATE'})
                        </span>
                      </td>

                      {/* Primary Tiebreaker */}
                      <td className="px-4 py-3 text-text-tertiary">
                        {player.primary_tiebreaker !== undefined && player.primary_tiebreaker > 0
                          ? player.primary_tiebreaker.toFixed(2)
                          : '—'}
                      </td>

                      {/* Eligibility */}
                      <td className="px-4 py-3">
                        {player.is_eligible ? (
                          <span className="inline-flex items-center gap-1 text-[11px] text-accent-lime">
                            <ShieldCheck className="w-3.5 h-3.5" />
                            <span>Eligible</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] text-status-negative">
                            <AlertCircle className="w-3.5 h-3.5" />
                            <span>Ineligible</span>
                          </span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Eye className="w-3.5 h-3.5" />}
                          onClick={() => navigate(`/players/${player.player_id}`)}
                        >
                          Profile
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Floating Comparison Drawer if players selected */}
      {selectedForCompare.length > 0 && (
        <div className="fixed bottom-6 right-6 z-40 bg-surface-card border border-accent-magenta/50 rounded shadow-elevated p-3 sm:p-4 flex items-center gap-4 animate-fade-in">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-accent-magenta animate-pulse" />
            <span className="text-xs font-semibold text-text-primary">
              {selectedForCompare.length} Selected for Comparison
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedForCompare([])}
            >
              Clear
            </Button>
            <Button
              variant="primary"
              size="sm"
              disabled={selectedForCompare.length < 2}
              icon={<GitCompare className="w-4 h-4" />}
              onClick={handleLaunchComparison}
            >
              Launch Comparison
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
