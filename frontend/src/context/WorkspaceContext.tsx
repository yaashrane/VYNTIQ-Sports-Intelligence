import React, { createContext, useContext, useState, useEffect } from 'react';
import type { Workspace } from '../api/types';
import { workspaceApi } from '../api/workspaces';

interface WorkspaceContextType {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  setActiveWorkspace: (workspace: Workspace | null) => void;
  isLoading: boolean;
  refreshWorkspaces: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchWorkspaces = async () => {
    try {
      setIsLoading(true);
      const data = await workspaceApi.list();
      setWorkspaces(data);
      // Retain or set first active workspace
      if (data.length > 0 && !activeWorkspace) {
        setActiveWorkspace(data[0]);
      } else if (activeWorkspace) {
        const found = data.find((w) => w.workspace_id === activeWorkspace.workspace_id);
        if (found) setActiveWorkspace(found);
      }
    } catch {
      // Handled at page level
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        setActiveWorkspace,
        isLoading,
        refreshWorkspaces: fetchWorkspaces,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
};
