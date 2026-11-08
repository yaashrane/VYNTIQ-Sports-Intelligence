import React, { useEffect, useState } from 'react';
import { Menu, ChevronDown, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { systemApi } from '../../api/system';

interface TopNavProps {
  onToggleSidebar: () => void;
  pageTitle: string;
}

export const TopNavigation: React.FC<TopNavProps> = ({
  onToggleSidebar,
  pageTitle,
}) => {
  const { workspaces, activeWorkspace, setActiveWorkspace } = useWorkspace();
  const [isWorkspaceDropdownOpen, setIsWorkspaceDropdownOpen] = useState(false);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await systemApi.checkHealth();
        setIsBackendHealthy(res.status === 'healthy');
      } catch {
        setIsBackendHealthy(false);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-surface-card/90 backdrop-blur-sm border-b border-surface-border sticky top-0 z-30 flex items-center justify-between px-4 lg:px-8">
      {/* Left: Hamburger & Page Title */}
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="p-1.5 text-text-secondary hover:text-text-primary rounded hover:bg-surface-elevated lg:hidden focus:outline-none"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2">
          <span className="text-xs text-text-tertiary hidden sm:inline">Platform /</span>
          <h1 className="text-sm font-semibold text-text-primary tracking-tight">
            {pageTitle}
          </h1>
        </div>
      </div>

      {/* Right: Active Workspace Selector & System Health Pill */}
      <div className="flex items-center gap-3">
        {/* Workspace Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsWorkspaceDropdownOpen(!isWorkspaceDropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-text-primary bg-surface-elevated hover:bg-[#2b313d] border border-surface-border rounded transition-colors focus:outline-none"
            aria-expanded={isWorkspaceDropdownOpen}
            aria-haspopup="listbox"
          >
            <Layers className="w-3.5 h-3.5 text-accent-magenta" />
            <span className="max-w-[140px] truncate">
              {activeWorkspace ? activeWorkspace.name : 'Select Workspace'}
            </span>
            <ChevronDown className="w-3 h-3 text-text-secondary" />
          </button>

          {isWorkspaceDropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-20"
                onClick={() => setIsWorkspaceDropdownOpen(false)}
              />
              <div className="absolute right-0 mt-1.5 w-64 bg-surface-card border border-surface-border rounded shadow-elevated z-30 py-1 text-xs">
                <div className="px-3 py-1.5 text-[10px] font-semibold text-text-tertiary uppercase tracking-wider border-b border-surface-border">
                  Available Workspaces ({workspaces.length})
                </div>
                <div className="max-h-56 overflow-y-auto">
                  {workspaces.length === 0 ? (
                    <div className="px-3 py-2 text-text-tertiary text-center">
                      No workspaces created
                    </div>
                  ) : (
                    workspaces.map((ws) => (
                      <button
                        key={ws.workspace_id}
                        onClick={() => {
                          setActiveWorkspace(ws);
                          setIsWorkspaceDropdownOpen(false);
                        }}
                        className={`w-full text-left px-3 py-2 flex items-center justify-between hover:bg-surface-elevated transition-colors ${
                          activeWorkspace?.workspace_id === ws.workspace_id
                            ? 'text-accent-magenta font-semibold bg-accent-magenta/5'
                            : 'text-text-primary'
                        }`}
                      >
                        <span className="truncate">{ws.name}</span>
                        <span className="text-[10px] text-text-tertiary uppercase ml-2">
                          {ws.competition_name}
                        </span>
                      </button>
                    ))
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Backend Health Pill */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-medium border tabular-nums ${
            isBackendHealthy === true
              ? 'bg-accent-lime/10 text-accent-lime border-accent-lime/30'
              : isBackendHealthy === false
              ? 'bg-status-negative/10 text-status-negative border-status-negative/30'
              : 'bg-surface-elevated text-text-tertiary border-surface-border'
          }`}
          title={
            isBackendHealthy === true
              ? 'Backend API online and healthy'
              : 'Backend API unreachable or offline'
          }
        >
          {isBackendHealthy === true ? (
            <CheckCircle2 className="w-3 h-3 text-accent-lime" />
          ) : (
            <AlertTriangle className="w-3 h-3 text-status-negative" />
          )}
          <span className="hidden sm:inline">
            {isBackendHealthy === true
              ? 'API Online'
              : isBackendHealthy === false
              ? 'API Offline'
              : 'Checking...'}
          </span>
        </div>
      </div>
    </header>
  );
};

