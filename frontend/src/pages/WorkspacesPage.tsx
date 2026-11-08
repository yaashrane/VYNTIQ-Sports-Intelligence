import React, { useState } from 'react';
import { Plus, Layers } from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import type { WorkspaceStatus } from '../api/types';
import { Button } from '../components/common/Button';
import { SearchInput } from '../components/common/SearchInput';
import { WorkspaceCard } from '../components/workspaces/WorkspaceCard';
import { CreateWorkspaceModal } from '../components/workspaces/CreateWorkspaceModal';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';

export const WorkspacesPage: React.FC = () => {
  const { workspaces, isLoading, refreshWorkspaces } = useWorkspace();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const statuses: Array<{ label: string; value: string }> = [
    { label: 'All', value: 'ALL' },
    { label: 'Draft', value: 'DRAFT' },
    { label: 'Active', value: 'ACTIVE' },
    { label: 'Completed', value: 'COMPLETED' },
    { label: 'Archived', value: 'ARCHIVED' },
  ];

  const filteredWorkspaces = workspaces.filter((ws) => {
    const matchesSearch =
      ws.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ws.competition_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ws.season_or_edition.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === 'ALL' || ws.status === (statusFilter as WorkspaceStatus);

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-border">
        <div>
          <h1 className="text-xl font-display font-bold text-text-primary">
            Competition Workspaces
          </h1>
          <p className="text-xs text-text-secondary mt-0.5">
            Manage multi-tenant recruitment sandboxes, competition rules, and shortlist iterations.
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          icon={<Plus className="w-4 h-4" />}
          onClick={() => setIsCreateModalOpen(true)}
        >
          Create Workspace
        </Button>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Status Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {statuses.map((s) => (
            <button
              key={s.value}
              onClick={() => setStatusFilter(s.value)}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                statusFilter === s.value
                  ? 'bg-accent-magenta text-white font-semibold'
                  : 'bg-surface-card text-text-secondary hover:text-text-primary hover:bg-surface-elevated border border-surface-border'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <SearchInput
          value={searchTerm}
          onChange={setSearchTerm}
          placeholder="Filter by name or competition..."
          className="w-full sm:w-72"
        />
      </div>

      {/* Grid or Empty/Loading States */}
      {isLoading ? (
        <LoadingState message="Loading workspaces..." />
      ) : filteredWorkspaces.length === 0 ? (
        <EmptyState
          icon={Layers}
          title={searchTerm ? 'No Matching Workspaces' : 'No Workspaces Found'}
          description={
            searchTerm
              ? `No workspaces matched query "${searchTerm}". Try adjusting your search or filters.`
              : 'Create a new competition workspace sandbox to begin evaluating prospects.'
          }
          actionLabel={searchTerm ? 'Clear Search' : 'Create Workspace'}
          onAction={
            searchTerm ? () => setSearchTerm('') : () => setIsCreateModalOpen(true)
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredWorkspaces.map((ws) => (
            <WorkspaceCard key={ws.workspace_id} workspace={ws} />
          ))}
        </div>
      )}

      {/* Create Modal */}
      <CreateWorkspaceModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={() => refreshWorkspaces()}
      />
    </div>
  );
};
