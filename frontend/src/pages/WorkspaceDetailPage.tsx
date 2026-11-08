import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Calendar,
  Layers,
  ArrowLeft,
  Sliders,
  Database,
  ListOrdered,
  Archive,
  Trophy,
} from 'lucide-react';
import type {
  DatasetSummary,
  ShortlistSummary,
  WorkspaceDetail,
} from '../api/types';
import { workspaceApi } from '../api/workspaces';
import { StatusBadge } from '../components/common/StatusBadge';
import { Button } from '../components/common/Button';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';

export const WorkspaceDetailPage: React.FC = () => {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();

  const [workspace, setWorkspace] = useState<WorkspaceDetail | null>(null);
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [shortlists, setShortlists] = useState<ShortlistSummary[]>([]);
  const [activeTab, setActiveTab] = useState<'config' | 'datasets' | 'shortlists'>('config');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isArchiving, setIsArchiving] = useState(false);

  const loadData = useCallback(async () => {
    if (!workspaceId) return;
    try {
      setIsLoading(true);
      setError(null);
      const [ws, ds, sl] = await Promise.all([
        workspaceApi.get(workspaceId),
        workspaceApi.getDatasets(workspaceId),
        workspaceApi.listShortlists(workspaceId),
      ]);
      setWorkspace(ws);
      setDatasets(ds);
      setShortlists(sl);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load workspace detail.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleArchive = async () => {
    if (!workspaceId || !window.confirm('Are you sure you want to archive this workspace?')) return;
    try {
      setIsArchiving(true);
      await workspaceApi.archive(workspaceId);
      await loadData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to archive workspace.');
    } finally {
      setIsArchiving(false);
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading workspace specifications and rules..." />;
  }

  if (error || !workspace) {
    return (
      <ErrorState
        title="Workspace Not Found"
        message={error || `Workspace with ID '${workspaceId}' could not be retrieved.`}
        onRetry={loadData}
      />
    );
  }

  const config = workspace.configuration;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back button & Title Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-surface-border">
        <div className="space-y-2">
          <button
            onClick={() => navigate('/workspaces')}
            className="inline-flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Workspaces</span>
          </button>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-display font-bold text-text-primary">
              {workspace.name}
            </h1>
            <StatusBadge status={workspace.status} />
          </div>
          <div className="flex flex-wrap items-center gap-4 text-xs text-text-secondary tabular-nums">
            <div className="flex items-center gap-1.5">
              <Trophy className="w-3.5 h-3.5 text-accent-magenta" />
              <span>
                {workspace.competition_name} ({workspace.season_or_edition})
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-text-tertiary" />
              <span className="font-mono text-text-tertiary">
                ID: {workspace.workspace_id}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-text-tertiary" />
              <span>
                Created {new Date(workspace.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>

        {workspace.status !== 'ARCHIVED' && (
          <Button
            variant="outline"
            size="sm"
            icon={<Archive className="w-3.5 h-3.5" />}
            onClick={handleArchive}
            isLoading={isArchiving}
          >
            Archive Sandbox
          </Button>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-surface-border">
        <button
          onClick={() => setActiveTab('config')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors ${
            activeTab === 'config'
              ? 'border-accent-magenta text-accent-magenta font-semibold'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>Configuration & Eligibility</span>
        </button>
        <button
          onClick={() => setActiveTab('datasets')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors ${
            activeTab === 'datasets'
              ? 'border-accent-magenta text-accent-magenta font-semibold'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>Associated Datasets ({datasets.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('shortlists')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors ${
            activeTab === 'shortlists'
              ? 'border-accent-magenta text-accent-magenta font-semibold'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <ListOrdered className="w-3.5 h-3.5" />
          <span>Candidate Shortlists ({shortlists.length})</span>
        </button>
      </div>

      {/* Tab 1: Configuration & Rules */}
      {activeTab === 'config' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Target Roles & Shortlist Sizing */}
          <div className="bg-surface-card border border-surface-border rounded p-5 space-y-4">
            <h3 className="text-sm font-semibold text-text-primary pb-2 border-b border-surface-border">
              Scouting Scope & Sizing
            </h3>
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-text-secondary block mb-1.5">Target Player Roles:</span>
                <div className="flex flex-wrap gap-1.5">
                  {config?.target_roles?.map((role) => (
                    <span
                      key={role}
                      className="px-2.5 py-1 bg-surface-elevated border border-surface-border rounded font-semibold text-text-primary"
                    >
                      {role}
                    </span>
                  )) || <span className="text-text-tertiary">All Roles</span>}
                </div>
              </div>
              <div className="flex items-center justify-between pt-2">
                <span className="text-text-secondary">Default Shortlist Size:</span>
                <span className="font-semibold text-text-primary tabular-nums">
                  {config?.shortlist_size || 10} Candidates
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Evaluation Profile Version:</span>
                <span className="font-mono text-text-primary font-semibold">
                  v{config?.evaluation_profile_version || '1.0.0'}
                </span>
              </div>
            </div>
          </div>

          {/* Eligibility Rules */}
          <div className="bg-surface-card border border-surface-border rounded p-5 space-y-4">
            <h3 className="text-sm font-semibold text-text-primary pb-2 border-b border-surface-border">
              Eligibility & Workload Requirements
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Age Restrictions:</span>
                <span className="font-semibold text-text-primary tabular-nums">
                  {config?.age_criteria?.min_age || config?.age_criteria?.max_age
                    ? `${config.age_criteria.min_age || 0} to ${
                        config.age_criteria.max_age || 99
                      } years`
                    : 'None (Unrestricted)'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Min Balls Faced (Batting):</span>
                <span className="font-semibold text-text-primary tabular-nums">
                  {config?.participation_criteria?.min_balls_faced !== null &&
                  config?.participation_criteria?.min_balls_faced !== undefined
                    ? `${config.participation_criteria.min_balls_faced} balls`
                    : 'None (Evaluated via Bayesian Shrinkage)'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Min Legal Balls (Bowling):</span>
                <span className="font-semibold text-text-primary tabular-nums">
                  {config?.participation_criteria?.min_legal_balls_bowled !== null &&
                  config?.participation_criteria?.min_legal_balls_bowled !== undefined
                    ? `${config.participation_criteria.min_legal_balls_bowled} balls`
                    : 'None (Evaluated via Bayesian Shrinkage)'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Datasets */}
      {activeTab === 'datasets' && (
        <div className="space-y-4">
          {datasets.length === 0 ? (
            <EmptyState
              icon={Database}
              title="No Associated Datasets"
              description="No datasets are currently stamped or linked to this workspace sandbox."
            />
          ) : (
            <div className="bg-surface-card border border-surface-border rounded overflow-hidden">
              <table className="w-full text-left text-xs tabular-nums">
                <thead className="bg-surface-elevated text-text-secondary font-semibold uppercase text-[10px] tracking-wider border-b border-surface-border">
                  <tr>
                    <th className="px-4 py-3">Dataset ID</th>
                    <th className="px-4 py-3">Source File</th>
                    <th className="px-4 py-3">Rows</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Ingested</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {datasets.map((d) => (
                    <tr key={d.dataset_id} className="hover:bg-surface-elevated/40">
                      <td className="px-4 py-3 font-mono text-text-tertiary">
                        {d.dataset_id}
                      </td>
                      <td className="px-4 py-3 text-text-primary font-medium">
                        {d.source_filename}
                      </td>
                      <td className="px-4 py-3 text-text-secondary">
                        {d.total_rows}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={d.status} size="sm" />
                      </td>
                      <td className="px-4 py-3 text-text-secondary">
                        {new Date(d.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Shortlists */}
      {activeTab === 'shortlists' && (
        <div className="space-y-4">
          {shortlists.length === 0 ? (
            <EmptyState
              icon={ListOrdered}
              title="No Shortlists Generated Yet"
              description="Shortlists will appear here once candidate evaluations and scoring runs have been processed."
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {shortlists.map((sl) => (
                <div
                  key={sl.shortlist_id}
                  className="bg-surface-card border border-surface-border rounded p-4 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-text-primary">
                      {sl.name}
                    </span>
                    <StatusBadge status={sl.status} size="sm" />
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center py-2 bg-surface-elevated/50 rounded border border-surface-border tabular-nums text-xs">
                    <div>
                      <span className="text-[10px] text-text-tertiary block">Eligible</span>
                      <span className="font-semibold text-text-primary">{sl.eligible_count}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-text-tertiary block">Excluded</span>
                      <span className="font-semibold text-status-negative">{sl.excluded_count}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-text-tertiary block">Shortlisted</span>
                      <span className="font-semibold text-accent-lime">{sl.shortlisted_count}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-text-tertiary pt-1 border-t border-surface-border">
                    <span className="font-mono">ID: {sl.shortlist_id}</span>
                    <span>{new Date(sl.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
