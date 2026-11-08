import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { ApplicationSidebar } from './ApplicationSidebar';
import { TopNavigation } from './TopNavigation';

export const AppLayout: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const location = useLocation();

  const getPageTitle = (path: string): string => {
    if (path === '/') return 'Overview Dashboard';
    if (path.startsWith('/workspaces/') && path !== '/workspaces')
      return 'Workspace Detail';
    if (path.startsWith('/workspaces')) return 'Competition Workspaces';
    if (path.startsWith('/players')) return 'Player Explorer';
    if (path.startsWith('/shortlists')) return 'Candidate Shortlists';
    if (path.startsWith('/comparisons')) return 'Player Comparisons';
    if (path.startsWith('/reports')) return 'Scouting Reports';
    if (path.startsWith('/settings')) return 'Settings';
    return 'Sports Intelligence';
  };

  return (
    <div className="min-h-screen bg-surface-ground flex text-text-primary">
      {/* Sidebar */}
      <ApplicationSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        <TopNavigation
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          pageTitle={getPageTitle(location.pathname)}
        />
        <main className="flex-1 p-4 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

