import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Layers,
  Plus,
  ArrowRight,
  Database,
  Activity,
  Sparkles,
  Server,
} from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import { Button } from '../components/common/Button';
import { WorkspaceCard } from '../components/workspaces/WorkspaceCard';
import { CreateWorkspaceModal } from '../components/workspaces/CreateWorkspaceModal';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';

export const OverviewPage: React.FC = () => {
  const { workspaces, isLoading, refreshWorkspaces } = useWorkspace();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="space-y-8 animate-fade-in">
      {/* 1. Welcome Section */}
      <section className="relative overflow-hidden bg-surface-card border border-surface-border rounded p-6 sm:p-8">
        <div className="max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-accent-magenta/10 border border-accent-magenta/25 text-accent-magenta text-xs font-semibold tracking-wider uppercase">
            <Sparkles className="w-3.5 h-3.5" />
            <span>VYNTIQ — Sports Intelligence</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-text-primary tracking-tight">
            Every Metric Tells a Story.
          </h1>
          <p className="text-sm sm:text-base text-text-secondary leading-relaxed">
            Discover talent. Decode performance. Make smarter decisions. VYNTIQ is an
            independent sports analytics platform engineered for elite recruitment,
            explainable VOR player evaluations, and competition intelligence sandboxes.
          </p>

          {/* Quick Actions */}
          <div className="flex flex-wrap items-center gap-3 pt-3">
            <Button
              variant="primary"
              size="sm"
              icon={<Plus className="w-4 h-4" />}
              onClick={() => setIsCreateModalOpen(true)}
            >
              Create Workspace
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon={<Layers className="w-4 h-4" />}
              onClick={() => navigate('/workspaces')}
            >
              View All Workspaces
            </Button>
          </div>
        </div>
      </section>

      {/* 2. Grid: Workspaces Overview & System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Workspaces List (2 cols) */}
        <section className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-text-primary">
                Active Competition Workspaces
              </h2>
              <p className="text-xs text-text-secondary">
                Independent analytical sandboxes for tournaments and scouting trials.
              </p>
            </div>
            {workspaces.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/workspaces')}
                icon={<ArrowRight className="w-3.5 h-3.5" />}
              >
                All ({workspaces.length})
              </Button>
            )}
          </div>

          {isLoading ? (
            <LoadingState message="Fetching active workspaces from backend..." />
          ) : workspaces.length === 0 ? (
            <EmptyState
              icon={Layers}
              title="No Workspaces Available"
              description="Create your first competition workspace sandbox (e.g. SuperRR Selector Season 2) to configure recruitment rules and generate shortlists."
              actionLabel="Create First Workspace"
              onAction={() => setIsCreateModalOpen(true)}
            />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {workspaces.slice(0, 4).map((ws) => (
                <WorkspaceCard key={ws.workspace_id} workspace={ws} />
              ))}
            </div>
          )}
        </section>

        {/* System & Data Status Column (1 col) */}
        <section className="space-y-6">
          {/* Data Status Card */}
          <div className="bg-surface-card border border-surface-border rounded p-5 space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-surface-border">
              <Database className="w-4 h-4 text-accent-magenta" />
              <h3 className="text-sm font-semibold text-text-primary">
                Data Architecture Status
              </h3>
            </div>
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Canonical Baselines:</span>
                <span className="font-semibold text-text-primary">Global (IPL / T20)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Tenant Isolation:</span>
                <span className="font-semibold text-accent-lime">ADR-001 Shared Tables</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Scoring Paradigm:</span>
                <span className="font-semibold text-text-primary">Deterministic VOR + ECDF</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Reliability Model:</span>
                <span className="font-semibold text-text-primary">Bayesian Shrinkage</span>
              </div>
            </div>
          </div>

          {/* Activity Status Card */}
          <div className="bg-surface-card border border-surface-border rounded p-5 space-y-3">
            <div className="flex items-center gap-2 pb-3 border-b border-surface-border">
              <Activity className="w-4 h-4 text-text-secondary" />
              <h3 className="text-sm font-semibold text-text-primary">
                Platform Activity
              </h3>
            </div>
            <div className="py-6 text-center text-xs text-text-tertiary">
              <Server className="w-5 h-5 mx-auto mb-2 text-text-tertiary opacity-60" />
              <p>No recent audit alerts logged in this session.</p>
              <p className="text-[11px] mt-1 text-text-tertiary">
                Shortlist generations and review transitions record automatically to SQLite.
              </p>
            </div>
          </div>
        </section>
      </div>

      {/* Modal */}
      <CreateWorkspaceModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={() => {
          refreshWorkspaces();
        }}
      />
    </div>
  );
};

