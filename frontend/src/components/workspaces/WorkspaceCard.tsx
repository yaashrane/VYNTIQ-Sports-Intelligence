import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, ArrowUpRight, Trophy } from 'lucide-react';
import type { Workspace } from '../../api/types';
import { StatusBadge } from '../common/StatusBadge';

export interface WorkspaceCardProps {
  workspace: Workspace;
}

export const WorkspaceCard: React.FC<WorkspaceCardProps> = ({ workspace }) => {
  const navigate = useNavigate();

  const formattedDate = new Date(workspace.updated_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div
      onClick={() => navigate(`/workspaces/${workspace.workspace_id}`)}
      className="group relative bg-surface-card hover:bg-surface-elevated border border-surface-border hover:border-accent-magenta/40 rounded p-5 transition-all duration-150 cursor-pointer flex flex-col justify-between"
    >
      <div>
        {/* Top Badges & Status */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-semibold tracking-wider text-text-tertiary uppercase bg-surface-elevated border border-surface-border px-2 py-0.5 rounded">
              {workspace.sport_type}
            </span>
            <StatusBadge status={workspace.status} size="sm" />
          </div>
          <ArrowUpRight className="w-4 h-4 text-text-tertiary group-hover:text-accent-magenta transition-colors" />
        </div>

        {/* Workspace Title & Description */}
        <h3 className="text-base font-semibold text-text-primary tracking-tight group-hover:text-accent-magenta transition-colors mb-1.5">
          {workspace.name}
        </h3>
        <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed mb-4">
          {workspace.description || 'No description provided for this workspace sandbox.'}
        </p>
      </div>

      {/* Metadata Footer */}
      <div className="pt-3 border-t border-surface-border/70 flex items-center justify-between text-[11px] text-text-tertiary tabular-nums">
        <div className="flex items-center gap-1.5">
          <Trophy className="w-3.5 h-3.5 text-text-secondary" />
          <span className="text-text-secondary font-medium">
            {workspace.competition_name} ({workspace.season_or_edition})
          </span>
        </div>
        <div className="flex items-center gap-1 text-text-tertiary">
          <Calendar className="w-3 h-3" />
          <span>{formattedDate}</span>
        </div>
      </div>
    </div>
  );
};
