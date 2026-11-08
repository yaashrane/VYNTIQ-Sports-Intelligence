import React from 'react';
import { Search, X } from 'lucide-react';

export interface SearchInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  placeholder = 'Search...',
  className = '',
  ...props
}) => {
  return (
    <div className={`relative flex items-center ${className}`}>
      <Search className="absolute left-3 w-4 h-4 text-text-secondary pointer-events-none" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-9 pr-9 py-2 bg-surface-card border border-surface-border rounded text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-1 focus:ring-accent-magenta focus:border-accent-magenta transition-colors"
        {...props}
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange('')}
          className="absolute right-3 p-0.5 text-text-secondary hover:text-text-primary rounded focus:outline-none"
          aria-label="Clear search"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};
