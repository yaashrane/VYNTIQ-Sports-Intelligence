import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { workspaceApi } from '../../api/workspaces';
import type { WorkspaceDetail } from '../../api/types';

interface CreateWorkspaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (workspace: WorkspaceDetail) => void;
}

export const CreateWorkspaceModal: React.FC<CreateWorkspaceModalProps> = ({
  isOpen,
  onClose,
  onCreated,
}) => {
  const [name, setName] = useState('');
  const [workspaceId, setWorkspaceId] = useState('');
  const [competitionName, setCompetitionName] = useState('');
  const [season, setSeason] = useState('');
  const [description, setDescription] = useState('');
  const [shortlistSize, setShortlistSize] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError('Workspace name is required.');
      return;
    }
    if (!competitionName.trim()) {
      setError('Competition name is required.');
      return;
    }
    if (!season.trim()) {
      setError('Season or edition is required.');
      return;
    }

    try {
      setIsLoading(true);
      const created = await workspaceApi.create({
        workspace_id: workspaceId.trim() || undefined,
        name: name.trim(),
        competition_name: competitionName.trim(),
        season_or_edition: season.trim(),
        description: description.trim() || undefined,
        initial_configuration: {
          target_sport: 'CRICKET',
          shortlist_size: Number(shortlistSize),
          target_roles: ['BATTER', 'BOWLER', 'ALL_ROUNDER', 'WICKETKEEPER'],
        },
      });

      // Reset form
      setName('');
      setWorkspaceId('');
      setCompetitionName('');
      setSeason('');
      setDescription('');
      setShortlistSize(10);

      onCreated(created);
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to create workspace.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create Competition Workspace"
      description="Provision an independent sandbox for scouting, candidate eligibility, and shortlist generation."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 text-xs text-status-negative bg-status-negative/10 border border-status-negative/20 rounded">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="ws-name-input" className="block text-xs font-semibold text-text-primary mb-1">
            Workspace Name <span className="text-accent-magenta">*</span>
          </label>
          <input
            id="ws-name-input"
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Rajasthan Royals SuperRR Season 2"
            className="w-full px-3 py-2 text-xs bg-surface-ground border border-surface-border rounded text-text-primary focus:outline-none focus:border-accent-magenta focus:ring-1 focus:ring-accent-magenta"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="ws-comp-input" className="block text-xs font-semibold text-text-primary mb-1">
              Competition Name <span className="text-accent-magenta">*</span>
            </label>
            <input
              id="ws-comp-input"
              type="text"
              required
              value={competitionName}
              onChange={(e) => setCompetitionName(e.target.value)}
              placeholder="e.g. SuperRR Selector"
              className="w-full px-3 py-2 text-xs bg-surface-ground border border-surface-border rounded text-text-primary focus:outline-none focus:border-accent-magenta focus:ring-1 focus:ring-accent-magenta"
            />
          </div>
          <div>
            <label htmlFor="ws-season-input" className="block text-xs font-semibold text-text-primary mb-1">
              Season / Edition <span className="text-accent-magenta">*</span>
            </label>
            <input
              id="ws-season-input"
              type="text"
              required
              value={season}
              onChange={(e) => setSeason(e.target.value)}
              placeholder="e.g. Season 2"
              className="w-full px-3 py-2 text-xs bg-surface-ground border border-surface-border rounded text-text-primary focus:outline-none focus:border-accent-magenta focus:ring-1 focus:ring-accent-magenta"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="ws-id-input" className="block text-xs font-semibold text-text-primary mb-1">
              Workspace ID (Optional Slug)
            </label>
            <input
              id="ws-id-input"
              type="text"
              value={workspaceId}
              onChange={(e) => setWorkspaceId(e.target.value)}
              placeholder="e.g. workspace_super_rr_s2"
              className="w-full px-3 py-2 text-xs bg-surface-ground border border-surface-border rounded text-text-primary focus:outline-none focus:border-accent-magenta focus:ring-1 focus:ring-accent-magenta"
            />
            <p className="text-[10px] text-text-tertiary mt-1">
              Leave blank to automatically generate a secure identifier.
            </p>
          </div>
          <div>
            <label htmlFor="ws-size-input" className="block text-xs font-semibold text-text-primary mb-1">
              Target Shortlist Size
            </label>
            <input
              id="ws-size-input"
              type="number"
              min={1}
              max={100}
              value={shortlistSize}
              onChange={(e) => setShortlistSize(Number(e.target.value))}
              className="w-full px-3 py-2 text-xs bg-surface-ground border border-surface-border rounded text-text-primary focus:outline-none focus:border-accent-magenta focus:ring-1 focus:ring-accent-magenta tabular-nums"
            />
          </div>
        </div>

        <div>
          <label htmlFor="ws-desc-input" className="block text-xs font-semibold text-text-primary mb-1">
            Description
          </label>
          <textarea
            id="ws-desc-input"
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Analytical scope, recruitment requirements, target metrics..."
            className="w-full px-3 py-2 text-xs bg-surface-ground border border-surface-border rounded text-text-primary focus:outline-none focus:border-accent-magenta focus:ring-1 focus:ring-accent-magenta"
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-surface-border">
          <Button type="button" variant="outline" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" size="sm" isLoading={isLoading}>
            Create Workspace
          </Button>
        </div>
      </form>
    </Modal>
  );
};
