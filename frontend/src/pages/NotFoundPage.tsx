import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileQuestion, ArrowLeft } from 'lucide-react';
import { Button } from '../components/common/Button';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center p-12 text-center max-w-md mx-auto space-y-4 my-12 bg-surface-card border border-surface-border rounded animate-fade-in">
      <div className="w-12 h-12 rounded bg-surface-elevated border border-surface-border flex items-center justify-center text-text-tertiary mb-2">
        <FileQuestion className="w-6 h-6" />
      </div>
      <h1 className="text-xl font-display font-bold text-text-primary">
        Page Not Found
      </h1>
      <p className="text-sm text-text-secondary leading-relaxed">
        The requested platform resource or navigation route does not exist.
      </p>
      <div className="pt-2">
        <Button
          variant="outline"
          size="sm"
          icon={<ArrowLeft className="w-3.5 h-3.5" />}
          onClick={() => navigate('/')}
        >
          Return to Dashboard
        </Button>
      </div>
    </div>
  );
};
