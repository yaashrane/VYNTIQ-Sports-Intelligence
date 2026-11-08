import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Trophy,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  GitCompare,
  FileCheck2,
  Calendar,
  Globe,
  FileDown,
} from 'lucide-react';
import { reportApi } from '../api/reports';
import { playerApi } from '../api/players';
import type {
  PlayerDetailedExplanation,
  PlayerMaster,
  PlayerScoreBreakdown,
  PlayerScoreResult,
} from '../api/types';
import { RoleRadarChart } from '../components/analytics/RoleRadarChart';
import { Button } from '../components/common/Button';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';

export const PlayerProfilePage: React.FC = () => {
  const { playerId } = useParams<{ playerId: string }>();
  const navigate = useNavigate();

  const [playerBio, setPlayerBio] = useState<PlayerMaster | null>(null);
  const [scoreResult, setScoreResult] = useState<PlayerScoreResult | null>(null);
  const [explanation, setExplanation] = useState<PlayerDetailedExplanation | null>(null);
  const [breakdown, setBreakdown] = useState<PlayerScoreBreakdown | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPlayerData = useCallback(async () => {
    if (!playerId) return;
    try {
      setIsLoading(true);
      setError(null);

      // Concurrently fetch score, explainability, breakdown, and master bio
      const [scoreRes, expRes, brkRes] = await Promise.all([
        playerApi.getScore(playerId),
        playerApi.getExplanation(playerId).catch(() => null),
        playerApi.getBreakdown(playerId).catch(() => null),
      ]);
      setScoreResult(scoreRes);
      setExplanation(expRes);
      setBreakdown(brkRes);

      // Attempt bio fetch if available in DB
      try {
        const bioRes = await playerApi.get(playerId);
        setPlayerBio(bioRes);
      } catch {
        // Fallback gracefully if not in canonical master
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(`Unable to load player performance profile for ${playerId}.`);
      }
    } finally {
      setIsLoading(false);
    }
  }, [playerId]);

  useEffect(() => {
    loadPlayerData();
  }, [loadPlayerData]);

  const handleExportPdf = async () => {
    if (!playerId) return;
    try {
      setIsExporting(true);
      const res = await reportApi.generateStandaloneReport({
        report_type: 'INDIVIDUAL_PLAYER',
        player_id: playerId,
        title: `Player Evaluation Dossier — ${scoreResult?.player_name || playerId}`,
      });
      window.open(res.download_url, '_blank');
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to generate PDF report.');
    } finally {
      setIsExporting(false);
    }
  };

  if (isLoading) {
    return <LoadingState message="Decomposing player performance dimensions and factor attributions..." />;
  }

  if (error || !scoreResult) {
    return (
      <ErrorState
        title="Player Evaluation Not Found"
        message={error || `Player ${playerId} has no verified evaluation in the active scoring run.`}
        onRetry={loadPlayerData}
      />
    );
  }

  const sample = scoreResult.sample_size;
  const isBatter = scoreResult.role === 'BATTER' || scoreResult.role === 'ALL_ROUNDER';
  const isBowler = scoreResult.role === 'BOWLER' || scoreResult.role === 'ALL_ROUNDER';

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      {/* Top Header & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-surface-border">
        <div className="space-y-2">
          <button
            onClick={() => navigate('/players')}
            className="inline-flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Player Explorer</span>
          </button>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-display font-bold text-text-primary">
              {scoreResult.player_name}
            </h1>
            <span className="px-2.5 py-0.5 rounded text-xs uppercase font-semibold bg-accent-magenta/15 text-accent-magenta border border-accent-magenta/30">
              {scoreResult.role}
            </span>
            <StatusBadge
              status={scoreResult.is_qualified ? 'ACTIVE' : 'WARNING'}
              size="sm"
            />
          </div>

          {/* Biographical / Provenance Metadata */}
          <div className="flex flex-wrap items-center gap-4 text-xs text-text-secondary tabular-nums pt-1">
            <span className="font-mono text-text-tertiary">
              ID: {scoreResult.player_id}
            </span>
            <div className="flex items-center gap-1 text-text-tertiary">
              <Trophy className="w-3.5 h-3.5 text-accent-magenta" />
              <span>Cohort: {scoreResult.cohort_id}</span>
            </div>
            {playerBio?.nationality && (
              <div className="flex items-center gap-1 text-text-tertiary">
                <Globe className="w-3.5 h-3.5" />
                <span>{playerBio.nationality}</span>
              </div>
            )}
            {playerBio?.dob && (
              <div className="flex items-center gap-1 text-text-tertiary">
                <Calendar className="w-3.5 h-3.5" />
                <span>DOB: {String(playerBio.dob)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            icon={<FileDown className="w-4 h-4" />}
            onClick={handleExportPdf}
            isLoading={isExporting}
          >
            Export PDF Dossier
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={<GitCompare className="w-4 h-4" />}
            onClick={() => navigate(`/comparisons?players=${scoreResult.player_id}`)}
          >
            Compare Player
          </Button>
        </div>
      </div>

      {/* Grid: Ratings Summary & Radar Visualization */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 cols): VOR Evaluation Summary & Performance Metrics */}
        <div className="lg:col-span-2 space-y-6">
          {/* Executive Rating Card */}
          <div className="bg-surface-card border border-surface-border rounded p-6">
            <div className="flex items-center justify-between pb-4 border-b border-surface-border mb-4">
              <div>
                <span className="text-[10px] font-semibold tracking-wider text-text-tertiary uppercase">
                  Composite Rating
                </span>
                <div className="text-3xl font-display font-bold text-accent-magenta tabular-nums">
                  {scoreResult.vor_score.toFixed(1)}{' '}
                  <span className="text-sm font-sans font-normal text-text-secondary">
                    VOR Score
                  </span>
                </div>
              </div>
              <div className="text-right">
                <span className="text-[10px] font-semibold tracking-wider text-text-tertiary uppercase">
                  Raw Unadjusted
                </span>
                <div className="text-xl font-display font-semibold text-text-primary tabular-nums">
                  {scoreResult.raw_composite_score.toFixed(1)}
                </div>
              </div>
            </div>

            {/* Reliability Shrinkage Equation & Parameters */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs tabular-nums bg-surface-elevated/40 p-3 rounded border border-surface-border">
              <div>
                <span className="text-[10px] text-text-tertiary block">Reliability C(N)</span>
                <span className="font-semibold text-accent-lime">
                  {scoreResult.reliability_factor.toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-text-tertiary block">Sample Qualification</span>
                <span
                  className={`font-semibold ${
                    scoreResult.is_qualified ? 'text-accent-lime' : 'text-status-negative'
                  }`}
                >
                  {scoreResult.reliability_status}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-text-tertiary block">Engine Version</span>
                <span className="font-mono text-text-primary">
                  v{scoreResult.scoring_version}
                </span>
              </div>
            </div>
          </div>

          {/* Granular Sample Workloads & Performance Metrics */}
          <div className="bg-surface-card border border-surface-border rounded p-6 space-y-4">
            <h3 className="text-sm font-semibold text-text-primary pb-2 border-b border-surface-border">
              Sample Workload & Event Counts
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs tabular-nums">
              {isBatter && (
                <>
                  <div className="p-3 bg-surface-elevated rounded border border-surface-border">
                    <span className="text-text-tertiary block text-[10px]">Balls Faced</span>
                    <span className="text-lg font-bold text-text-primary">
                      {sample.balls_faced ?? '—'}
                    </span>
                  </div>
                  <div className="p-3 bg-surface-elevated rounded border border-surface-border">
                    <span className="text-text-tertiary block text-[10px]">Dismissals</span>
                    <span className="text-lg font-bold text-text-primary">
                      {sample.dismissals ?? '—'}
                    </span>
                  </div>
                </>
              )}
              {isBowler && (
                <>
                  <div className="p-3 bg-surface-elevated rounded border border-surface-border">
                    <span className="text-text-tertiary block text-[10px]">Legal Balls</span>
                    <span className="text-lg font-bold text-text-primary">
                      {sample.legal_balls_bowled ?? '—'}
                    </span>
                  </div>
                  <div className="p-3 bg-surface-elevated rounded border border-surface-border">
                    <span className="text-text-tertiary block text-[10px]">Wickets</span>
                    <span className="text-lg font-bold text-text-primary">
                      {sample.wickets ?? '—'}
                    </span>
                  </div>
                </>
              )}
              <div className="p-3 bg-surface-elevated rounded border border-surface-border">
                <span className="text-text-tertiary block text-[10px]">Dataset ID</span>
                <span className="text-xs font-mono text-text-secondary truncate block">
                  {scoreResult.provenance.dataset_id}
                </span>
              </div>
              <div className="p-3 bg-surface-elevated rounded border border-surface-border">
                <span className="text-text-tertiary block text-[10px]">Eligibility Status</span>
                <span className="text-xs font-semibold text-accent-lime flex items-center gap-1 mt-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Eligible</span>
                </span>
              </div>
            </div>
          </div>

          {/* Explainability Strengths & Drag Factors */}
          <div className="bg-surface-card border border-surface-border rounded p-6 space-y-4">
            <h3 className="text-sm font-semibold text-text-primary pb-2 border-b border-surface-border">
              The Story Behind the Metric
            </h3>

            {/* Narrative summary generated deterministically by backend */}
            <p className="text-xs text-text-secondary leading-relaxed bg-surface-elevated/30 p-3.5 rounded border border-surface-border">
              {explanation?.narrative_summary || scoreResult.explanation.summary_text}
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              {/* Strengths */}
              <div className="space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-accent-lime">
                  <TrendingUp className="w-4 h-4" />
                  <span>Primary Strengths</span>
                </div>
                {scoreResult.explanation.top_strengths.length === 0 ? (
                  <p className="text-xs text-text-tertiary italic">No outlier strengths identified.</p>
                ) : (
                  <ul className="space-y-1 text-xs">
                    {scoreResult.explanation.top_strengths.map((str, idx) => (
                      <li
                        key={idx}
                        className="px-2.5 py-1.5 bg-accent-lime/10 border border-accent-lime/20 rounded text-text-primary"
                      >
                        {str}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Drag Factors */}
              <div className="space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-status-warning">
                  <TrendingDown className="w-4 h-4" />
                  <span>Performance Drag Factors</span>
                </div>
                {scoreResult.explanation.drag_factors.length === 0 ? (
                  <p className="text-xs text-text-tertiary italic">No severe drag factors recorded.</p>
                ) : (
                  <ul className="space-y-1 text-xs">
                    {scoreResult.explanation.drag_factors.map((drag, idx) => (
                      <li
                        key={idx}
                        className="px-2.5 py-1.5 bg-status-warning/10 border border-status-warning/20 rounded text-text-primary"
                      >
                        {drag}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Mathematical Reconciliation Audit Status */}
            {breakdown && (
              <div className="pt-3 border-t border-surface-border flex items-center justify-between text-[11px] text-text-tertiary tabular-nums">
                <div className="flex items-center gap-1.5">
                  <FileCheck2 className="w-3.5 h-3.5 text-accent-lime" />
                  <span>
                    Audit Status:{' '}
                    <strong className="text-text-primary">
                      {breakdown.is_reconciled ? 'RECONCILED' : 'DISCREPANCY DETECTED'}
                    </strong>
                  </span>
                </div>
                <span>
                  Discrepancy: {breakdown.reconciliation_discrepancy.toFixed(3)} pts
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column (1 col): Role Radar Chart & Dimension Table */}
        <div className="space-y-6">
          <div className="bg-surface-card border border-surface-border rounded p-6 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-surface-border">
              <h3 className="text-sm font-semibold text-text-primary">
                Role Dimension Profile
              </h3>
              <span className="text-[10px] text-accent-magenta font-semibold uppercase">
                {scoreResult.role}
              </span>
            </div>
            <RoleRadarChart
              dimensions={scoreResult.dimensions}
              playerName={scoreResult.player_name}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
