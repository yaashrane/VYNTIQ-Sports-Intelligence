import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  GitCompare,
  ArrowLeft,
  AlertTriangle,
  Plus,
  X,
  Info,
} from 'lucide-react';
import { comparisonApi } from '../api/comparison';
import { playerApi } from '../api/players';
import type {
  PlayerComparisonResponse,
  RankedPlayer,
} from '../api/types';
import { Button } from '../components/common/Button';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';

export const PlayerComparisonPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [comparisonResult, setComparisonResult] = useState<PlayerComparisonResponse | null>(null);
  const [availablePlayers, setAvailablePlayers] = useState<RankedPlayer[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize selected IDs from URL query params
  useEffect(() => {
    const pParam = searchParams.get('players');
    if (pParam) {
      const ids = pParam.split(',').map((s) => s.trim()).filter(Boolean);
      setSelectedIds(ids);
    }
  }, [searchParams]);

  // Load available leaderboard players for candidate picker
  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const rankRes = await playerApi.getRankings().catch(() => null);
        if (rankRes) setAvailablePlayers(rankRes.rankings || []);
      } catch {
        // Handled silently
      }
    };
    fetchLeaderboard();
  }, []);

  const runComparison = useCallback(async (ids: string[]) => {
    if (ids.length < 2) {
      setComparisonResult(null);
      return;
    }
    try {
      setIsLoading(true);
      setError(null);
      const rawRes = await comparisonApi.comparePlayers({
        player_ids: ids,
      }) as any;

      const normalized: PlayerComparisonResponse = {
        ...rawRes,
        dimension_comparisons: rawRes.dimension_comparisons || (rawRes.shared_dimensions || []).map((sd: any) => ({
          dimension_id: sd.dimension_id,
          dimension_name: sd.dimension_name,
          player_scores: sd.player_dimension_scores || {},
          delta_vs_baseline: sd.score_difference ?? null,
          advantage_player_id: sd.favorable_player_id ?? null,
        })),
        discipline_metrics: rawRes.discipline_metrics || {
          ...(rawRes.batting_comparison?.length ? {
            Batting: rawRes.batting_comparison.map((m: any) => ({
              metric_id: m.metric_id,
              display_name: m.display_name,
              directionality: m.directionality,
              player_values: m.player_values || {},
              delta_vs_baseline: m.absolute_difference ?? null,
              advantage_player_id: m.favorable_player_id ?? null,
            })),
          } : {}),
          ...(rawRes.bowling_comparison?.length ? {
            Bowling: rawRes.bowling_comparison.map((m: any) => ({
              metric_id: m.metric_id,
              display_name: m.display_name,
              directionality: m.directionality,
              player_values: m.player_values || {},
              delta_vs_baseline: m.absolute_difference ?? null,
              advantage_player_id: m.favorable_player_id ?? null,
            })),
          } : {}),
        },
      };

      setComparisonResult(normalized);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Comparison calculation failed.');
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedIds.length >= 2) {
      runComparison(selectedIds);
    }
  }, [selectedIds, runComparison]);

  const addPlayer = (id: string) => {
    if (selectedIds.includes(id)) return;
    if (selectedIds.length >= 5) {
      alert('Maximum of 5 players allowed in a single comparison.');
      return;
    }
    const updated = [...selectedIds, id];
    setSelectedIds(updated);
    setSearchParams({ players: updated.join(',') });
    setIsAddOpen(false);
  };

  const removePlayer = (id: string) => {
    const updated = selectedIds.filter((p) => p !== id);
    setSelectedIds(updated);
    setSearchParams(updated.length > 0 ? { players: updated.join(',') } : {});
    if (updated.length < 2) setComparisonResult(null);
  };

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-surface-border">
        <div className="space-y-1">
          <button
            onClick={() => navigate('/players')}
            className="inline-flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Explorer</span>
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-display font-bold text-text-primary">
              Head-to-Head Candidate Comparison
            </h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-accent-magenta/15 text-accent-magenta border border-accent-magenta/30">
              Multi-Player Delta Analysis
            </span>
          </div>
          <p className="text-xs text-text-secondary">
            Directionality-aware metrics, normalized dimension deltas, and cross-role compatibility safeguards.
          </p>
        </div>

        {/* Candidate Selector / Add button */}
        <div className="relative">
          <Button
            variant="outline"
            size="sm"
            icon={<Plus className="w-4 h-4" />}
            onClick={() => setIsAddOpen(!isAddOpen)}
            disabled={selectedIds.length >= 5}
          >
            Add Candidate ({selectedIds.length}/5)
          </Button>

          {isAddOpen && (
            <>
              <div className="fixed inset-0 z-20" onClick={() => setIsAddOpen(false)} />
              <div className="absolute right-0 mt-2 w-72 bg-surface-card border border-surface-border rounded shadow-elevated z-30 p-2 text-xs">
                <div className="px-2 py-1 text-[10px] font-semibold text-text-tertiary uppercase tracking-wider border-b border-surface-border mb-1">
                  Select Player to Add
                </div>
                <div className="max-h-60 overflow-y-auto space-y-1">
                  {availablePlayers
                    .filter((p) => !selectedIds.includes(p.player_id))
                    .map((p) => (
                      <button
                        key={p.player_id}
                        onClick={() => addPlayer(p.player_id)}
                        className="w-full text-left px-2.5 py-1.5 rounded hover:bg-surface-elevated transition-colors flex items-center justify-between"
                      >
                        <span className="font-medium text-text-primary truncate">
                          {p.player_name}
                        </span>
                        <span className="text-[10px] text-text-secondary uppercase">
                          {p.role} (VOR {p.vor_score.toFixed(1)})
                        </span>
                      </button>
                    ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Selected Players Strip */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-text-tertiary mr-1 font-medium">Comparing:</span>
        {selectedIds.length === 0 ? (
          <span className="text-xs text-text-tertiary italic">
            No players selected. Choose at least 2 players from the Player Explorer or click Add Candidate.
          </span>
        ) : (
          selectedIds.map((id) => {
            const header = comparisonResult?.players.find((p) => p.player_id === id);
            return (
              <span
                key={id}
                className="inline-flex items-center gap-1.5 px-3 py-1 bg-surface-card border border-surface-border rounded text-xs text-text-primary"
              >
                <span className="font-semibold">{header?.player_name || id}</span>
                {header && (
                  <span className="text-[10px] text-text-secondary uppercase">
                    ({header.role})
                  </span>
                )}
                <button
                  onClick={() => removePlayer(id)}
                  className="p-0.5 text-text-tertiary hover:text-text-primary"
                  aria-label={`Remove ${id}`}
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            );
          })
        )}
      </div>

      {/* Comparison Body */}
      {selectedIds.length < 2 ? (
        <div className="p-12 text-center bg-surface-card border border-surface-border rounded space-y-3">
          <GitCompare className="w-8 h-8 text-accent-magenta mx-auto opacity-70" />
          <h3 className="text-base font-semibold text-text-primary">
            Select At Least 2 Candidates
          </h3>
          <p className="text-xs text-text-secondary max-w-md mx-auto leading-relaxed">
            Choose comparable athletes from the Player Explorer or use the candidate selector to analyze side-by-side performance deltas and dimension ratings.
          </p>
        </div>
      ) : isLoading ? (
        <LoadingState message="Executing multi-player comparison and cross-role compatibility checks..." />
      ) : error ? (
        <ErrorState message={error} onRetry={() => runComparison(selectedIds)} />
      ) : comparisonResult ? (
        <div className="space-y-8">
          {/* Safeguard Alert for Cross-Role Comparisons */}
          {comparisonResult.is_cross_role && (
            <div className="p-4 bg-status-warning/10 border border-status-warning/30 rounded flex items-start gap-3 text-xs leading-relaxed">
              <AlertTriangle className="w-5 h-5 text-status-warning shrink-0 mt-0.5" />
              <div>
                <strong className="font-semibold text-text-primary block mb-0.5">
                  Cross-Role Statistical Advisory ({comparisonResult.compatibility_status})
                </strong>
                <p className="text-text-secondary">
                  {comparisonResult.compatibility_warning ||
                    (comparisonResult as any).compatibility_notes?.[0] ||
                    'Cross-role comparison active. Candidates belong to different roles; VOR scores cannot be directly equated.'}
                </p>
              </div>
            </div>
          )}

          {/* 1. Header Cards Grid */}
          <div
            className={`grid grid-cols-1 sm:grid-cols-${Math.min(
              comparisonResult.players.length,
              4
            )} gap-4`}
          >
            {comparisonResult.players.map((p) => {
              const isLeader = comparisonResult.vor_leader_id === p.player_id;

              return (
                <div
                  key={p.player_id}
                  className={`bg-surface-card border rounded p-5 relative space-y-3 ${
                    isLeader
                      ? 'border-accent-magenta/60 shadow-[0_0_12px_rgba(214,41,120,0.15)]'
                      : 'border-surface-border'
                  }`}
                >
                  {isLeader && comparisonResult.vor_comparison_valid && (
                    <span className="absolute top-3 right-3 text-[10px] font-bold text-accent-magenta bg-accent-magenta/10 border border-accent-magenta/30 px-2 py-0.5 rounded uppercase">
                      VOR Leader
                    </span>
                  )}

                  <div>
                    <span className="text-[10px] text-text-tertiary uppercase font-medium">
                      {p.role}
                    </span>
                    <h3 className="text-base font-display font-bold text-text-primary truncate">
                      {p.player_name}
                    </h3>
                  </div>

                  <div className="pt-2 border-t border-surface-border/70 flex items-baseline justify-between tabular-nums">
                    <div>
                      <span className="text-[10px] text-text-tertiary block">VOR Score</span>
                      <span className="text-xl font-display font-bold text-accent-magenta">
                        {p.vor_score.toFixed(1)}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-text-tertiary block">Reliability</span>
                      <span className="text-xs font-semibold text-accent-lime">
                        {p.reliability_factor.toFixed(2)} ({p.reliability_status})
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* 2. Recommendation Narrative */}
          {comparisonResult.recommendation_narrative && (
            <div className="bg-surface-card border border-surface-border rounded p-5 space-y-2">
              <div className="flex items-center gap-2 pb-2 border-b border-surface-border">
                <Info className="w-4 h-4 text-accent-magenta" />
                <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider">
                  Comparative Analysis Summary
                </h3>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed bg-surface-elevated/40 p-3 rounded border border-surface-border">
                {comparisonResult.recommendation_narrative}
              </p>
            </div>
          )}

          {/* 3. Dimension Comparison Matrix */}
          {(comparisonResult.dimension_comparisons?.length ?? 0) > 0 && (
            <div className="bg-surface-card border border-surface-border rounded overflow-hidden space-y-2">
              <div className="px-5 py-3 border-b border-surface-border flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider">
                    Role Dimension Matrix
                  </h3>
                  {comparisonResult.vor_leader_id && comparisonResult.vor_comparison_valid && (
                    <span className="text-[11px] font-semibold text-accent-magenta bg-accent-magenta/10 border border-accent-magenta/30 px-2 py-0.5 rounded">
                      Leader: {comparisonResult.players.find((p) => p.player_id === comparisonResult.vor_leader_id)?.player_name}
                    </span>
                  )}
                </div>
                {comparisonResult.baseline_player_id && (
                  <span className="text-[10px] text-text-tertiary tabular-nums">
                    Baseline: {comparisonResult.baseline_player_id}
                  </span>
                )}
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs tabular-nums">
                  <thead className="bg-surface-elevated text-text-secondary font-semibold uppercase text-[10px] tracking-wider border-b border-surface-border">
                    <tr>
                      <th className="px-4 py-3">Dimension</th>
                      {comparisonResult.players.map((p) => (
                        <th key={p.player_id} className="px-4 py-3">
                          {p.player_name}
                        </th>
                      ))}
                      <th className="px-4 py-3">Delta vs Baseline</th>
                      <th className="px-4 py-3 text-right">Advantage</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-border">
                    {comparisonResult.dimension_comparisons.map((dim) => {
                      const advPlayer = comparisonResult.players.find(
                        (p) => p.player_id === dim.advantage_player_id
                      );

                      return (
                        <tr key={dim.dimension_id} className="hover:bg-surface-elevated/40">
                          <td className="px-4 py-3 font-medium text-text-primary">
                            {dim.dimension_name}
                          </td>
                          {comparisonResult.players.map((p) => {
                            const val = dim.player_scores[p.player_id];
                            const isAdv = dim.advantage_player_id === p.player_id;

                            return (
                              <td
                                key={p.player_id}
                                className={`px-4 py-3 font-semibold ${
                                  isAdv ? 'text-accent-magenta font-bold' : 'text-text-secondary'
                                }`}
                              >
                                {val !== undefined ? val.toFixed(1) : '—'}
                              </td>
                            );
                          })}
                          <td className="px-4 py-3">
                            {dim.delta_vs_baseline !== null && dim.delta_vs_baseline !== undefined ? (
                              <span
                                className={`font-semibold ${
                                  dim.delta_vs_baseline > 0
                                    ? 'text-accent-lime'
                                    : dim.delta_vs_baseline < 0
                                    ? 'text-status-negative'
                                    : 'text-text-tertiary'
                                }`}
                              >
                                {dim.delta_vs_baseline > 0 ? '+' : ''}
                                {dim.delta_vs_baseline.toFixed(1)}
                              </span>
                            ) : (
                              '—'
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">
                            {advPlayer ? (
                              <span className="text-[11px] font-semibold text-accent-magenta">
                                {advPlayer.player_name}
                              </span>
                            ) : (
                              <span className="text-text-tertiary">Tied</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 4. Discipline Metrics Comparison (Batting / Bowling) */}
          {Object.entries(comparisonResult.discipline_metrics || {}).map(([discipline, metrics]) => (
            <div
              key={discipline}
              className="bg-surface-card border border-surface-border rounded overflow-hidden space-y-2"
            >
              <div className="px-5 py-3 border-b border-surface-border flex items-center justify-between">
                <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider">
                  {discipline} Performance Metrics
                </h3>
                <span className="text-[10px] text-text-tertiary uppercase">
                  Directionality-Aware Comparison
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs tabular-nums">
                  <thead className="bg-surface-elevated text-text-secondary font-semibold uppercase text-[10px] tracking-wider border-b border-surface-border">
                    <tr>
                      <th className="px-4 py-3">Metric</th>
                      <th className="px-4 py-3">Polarity</th>
                      {comparisonResult.players.map((p) => (
                        <th key={p.player_id} className="px-4 py-3">
                          {p.player_name}
                        </th>
                      ))}
                      <th className="px-4 py-3">Delta</th>
                      <th className="px-4 py-3 text-right">Advantage</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-border">
                    {metrics.map((m) => {
                      const advPlayer = comparisonResult.players.find(
                        (p) => p.player_id === m.advantage_player_id
                      );

                      return (
                        <tr key={m.metric_id} className="hover:bg-surface-elevated/40">
                          <td className="px-4 py-3 font-medium text-text-primary">
                            {m.display_name}
                          </td>
                          <td className="px-4 py-3 text-text-tertiary text-[10px]">
                            {m.directionality === 'LOWER_IS_BETTER'
                              ? 'Lower is better'
                              : m.directionality === 'HIGHER_IS_BETTER'
                              ? 'Higher is better'
                              : 'Neutral'}
                          </td>
                          {comparisonResult.players.map((p) => {
                            const val = m.player_values[p.player_id];
                            const isAdv = m.advantage_player_id === p.player_id;

                            return (
                              <td
                                key={p.player_id}
                                className={`px-4 py-3 font-semibold ${
                                  isAdv ? 'text-accent-magenta font-bold' : 'text-text-secondary'
                                }`}
                              >
                                {val !== null && val !== undefined ? val.toFixed(2) : '—'}
                              </td>
                            );
                          })}
                          <td className="px-4 py-3">
                            {m.delta_vs_baseline !== null && m.delta_vs_baseline !== undefined ? (
                              <span
                                className={`font-semibold ${
                                  (m.directionality === 'HIGHER_IS_BETTER' && m.delta_vs_baseline > 0) ||
                                  (m.directionality === 'LOWER_IS_BETTER' && m.delta_vs_baseline < 0)
                                    ? 'text-accent-lime'
                                    : (m.directionality === 'HIGHER_IS_BETTER' && m.delta_vs_baseline < 0) ||
                                      (m.directionality === 'LOWER_IS_BETTER' && m.delta_vs_baseline > 0)
                                    ? 'text-status-negative'
                                    : 'text-text-tertiary'
                                }`}
                              >
                                {m.delta_vs_baseline > 0 ? '+' : ''}
                                {m.delta_vs_baseline.toFixed(2)}
                              </span>
                            ) : (
                              '—'
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">
                            {advPlayer ? (
                              <span className="text-[11px] font-semibold text-accent-magenta">
                                {advPlayer.player_name}
                              </span>
                            ) : (
                              <span className="text-text-tertiary">Tied / None</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
};
