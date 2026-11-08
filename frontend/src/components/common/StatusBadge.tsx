import React from 'react';
import type { WorkspaceStatus, ReviewStatus } from '../../api/types';

export interface StatusBadgeProps {
  status: WorkspaceStatus | ReviewStatus | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
}) => {
  const getBadgeStyle = (val: string) => {
    switch (val.toUpperCase()) {
      case 'ACTIVE':
      case 'APPROVED':
      case 'VALIDATED':
      case 'PERSISTED':
        return 'bg-accent-lime/10 text-accent-lime border-accent-lime/30';
      case 'DRAFT':
      case 'PENDING':
        return 'bg-surface-elevated text-text-secondary border-surface-border';
      case 'COMPLETED':
      case 'FINALIZED':
        return 'bg-accent-magenta/10 text-accent-magenta border-accent-magenta/30';
      case 'ARCHIVED':
      case 'REJECTED':
      case 'FAILED':
        return 'bg-status-negative/10 text-status-negative border-status-negative/30';
      case 'NEEDS_REVIEW':
      case 'WARNING':
      case 'VALIDATED_WITH_WARNINGS':
        return 'bg-status-warning/10 text-status-warning border-status-warning/30';
      default:
        return 'bg-surface-card text-text-secondary border-surface-border';
    }
  };

  const sizeStyles = {
    sm: 'text-[10px] px-2 py-0.5 tracking-wider',
    md: 'text-xs px-2.5 py-1 tracking-wide',
  };

  return (
    <span
      className={`inline-flex items-center font-medium uppercase border rounded ${getBadgeStyle(
        status
      )} ${sizeStyles[size]}`}
    >
      {status.replace(/_/g, ' ')}
    </span>
  );
};
