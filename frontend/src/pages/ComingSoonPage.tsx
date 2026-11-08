import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Construction, ArrowLeft } from 'lucide-react';
import { Button } from '../components/common/Button';

export interface ComingSoonPageProps {
  title: string;
  description: string;
  scheduledPhase?: string;
}

export const ComingSoonPage: React.FC<ComingSoonPageProps> = ({
  title,
  description,
  scheduledPhase = 'Future Release',
}) => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center p-12 text-center max-w-lg mx-auto space-y-4 animate-fade-in my-12 bg-surface-card border border-surface-border rounded">
      <div className="w-12 h-12 rounded bg-accent-magenta/10 border border-accent-magenta/30 flex items-center justify-center text-accent-magenta mb-2">
        <Construction className="w-6 h-6" />
      </div>
      <span className="text-[11px] font-semibold tracking-wider text-accent-magenta uppercase bg-accent-magenta/10 px-2 py-0.5 rounded">
        {scheduledPhase}
      </span>
      <h1 className="text-xl font-display font-bold text-text-primary">{title}</h1>
      <p className="text-sm text-text-secondary leading-relaxed">{description}</p>
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

