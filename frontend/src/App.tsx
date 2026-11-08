import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { WorkspaceProvider } from './context/WorkspaceContext';
import { AppLayout } from './components/layout/AppLayout';
import { OverviewPage } from './pages/OverviewPage';
import { WorkspacesPage } from './pages/WorkspacesPage';
import { WorkspaceDetailPage } from './pages/WorkspaceDetailPage';
import { PlayerExplorerPage } from './pages/PlayerExplorerPage';
import { PlayerProfilePage } from './pages/PlayerProfilePage';
import { PlayerComparisonPage } from './pages/PlayerComparisonPage';
import { ComingSoonPage } from './pages/ComingSoonPage';
import { NotFoundPage } from './pages/NotFoundPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <WorkspaceProvider>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<OverviewPage />} />
            <Route path="workspaces" element={<WorkspacesPage />} />
            <Route path="workspaces/:workspaceId" element={<WorkspaceDetailPage />} />
            <Route path="players" element={<PlayerExplorerPage />} />
            <Route path="players/:playerId" element={<PlayerProfilePage />} />
            <Route path="comparisons" element={<PlayerComparisonPage />} />
            <Route
              path="shortlists"
              element={
                <ComingSoonPage
                  title="Candidate Shortlists"
                  description="View and manage generated shortlists within specific competition workspace sandboxes."
                  scheduledPhase="Available in Workspaces"
                />
              }
            />
            <Route
              path="reports"
              element={
                <ComingSoonPage
                  title="Scouting Reports & Dossiers"
                  description="Export audit-ready competition dossiers, executive PDF summaries, and event-level raw delivery lineage manifests."
                  scheduledPhase="Track B"
                />
              }
            />
            <Route
              path="settings"
              element={
                <ComingSoonPage
                  title="Platform Settings"
                  description="Manage API keys, environment configurations, and tenant isolation policies."
                  scheduledPhase="Track B"
                />
              }
            />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </WorkspaceProvider>
    </BrowserRouter>
  );
};

export default App;
