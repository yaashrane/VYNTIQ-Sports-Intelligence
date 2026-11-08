import React from 'react';

export interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading data...',
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-12 text-center ${className}`}
      role="status"
      aria-live="polite"
    >
      <div className="relative w-10 h-10 mb-4">
        <div className="absolute inset-0 rounded-full border-2 border-surface-border"></div>
        <div className="absolute inset-0 rounded-full border-2 border-accent-magenta border-t-transparent animate-spin"></div>
      </div>
      <p className="text-sm text-text-secondary">{message}</p>
    </div>
  );
};
