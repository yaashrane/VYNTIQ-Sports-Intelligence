import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Layers,
  Users,
  ListOrdered,
  GitCompare,
  FileText,
  Settings,
  Sparkles,
  X,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  isAvailable: boolean;
  badge?: string;
}

export const ApplicationSidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
}) => {
  const location = useLocation();

  const navigation: NavItem[] = [
    { name: 'Overview', href: '/', icon: LayoutDashboard, isAvailable: true },
    { name: 'Workspaces', href: '/workspaces', icon: Layers, isAvailable: true },
    {
      name: 'Player Explorer',
      href: '/players',
      icon: Users,
      isAvailable: false,
      badge: 'Phase A6',
    },
    {
      name: 'Shortlists',
      href: '/shortlists',
      icon: ListOrdered,
      isAvailable: false,
      badge: 'In Sandbox',
    },
    {
      name: 'Comparisons',
      href: '/comparisons',
      icon: GitCompare,
      isAvailable: false,
      badge: 'Backend API',
    },
    {
      name: 'Reports',
      href: '/reports',
      icon: FileText,
      isAvailable: false,
      badge: 'Track B',
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Settings,
      isAvailable: false,
      badge: 'Coming Soon',
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-surface-card border-r border-surface-border flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-surface-border">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded bg-accent-magenta/15 border border-accent-magenta/30 flex items-center justify-center text-accent-magenta font-display font-bold text-sm tracking-wider">
              V
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-display font-bold text-base tracking-tight text-text-primary">
                  VYNTIQ
                </span>
                <span className="text-[10px] uppercase font-semibold tracking-wider text-accent-magenta px-1 py-0.2 bg-accent-magenta/10 rounded">
                  Intel
                </span>
              </div>
              <p className="text-[10px] text-text-secondary tracking-wide">
                Sports Intelligence
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-text-secondary hover:text-text-primary lg:hidden"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Primary Navigation */}
        <div className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-text-tertiary uppercase">
            Platform Navigation
          </div>
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive =
              location.pathname === item.href ||
              (item.href !== '/' && location.pathname.startsWith(item.href));

            if (!item.isAvailable) {
              return (
                <div
                  key={item.name}
                  className="flex items-center justify-between px-3 py-2 text-xs font-medium text-text-tertiary rounded opacity-70 cursor-not-allowed group"
                  title={`${item.name} — ${item.badge || 'Coming Soon'}`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4 text-text-tertiary" />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-elevated text-text-tertiary border border-surface-border">
                      {item.badge}
                    </span>
                  )}
                </div>
              );
            }

            return (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={() => {
                  if (window.innerWidth < 1024) onClose();
                }}
                className={`flex items-center justify-between px-3 py-2 rounded text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-accent-magenta/10 text-accent-magenta border-l-2 border-accent-magenta font-semibold'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={`w-4 h-4 ${
                      isActive ? 'text-accent-magenta' : 'text-text-secondary'
                    }`}
                  />
                  <span>{item.name}</span>
                </div>
              </NavLink>
            );
          })}
        </div>

        {/* Editorial Tagline Footer */}
        <div className="p-4 border-t border-surface-border bg-surface-ground/40">
          <div className="flex items-start gap-2">
            <Sparkles className="w-3.5 h-3.5 text-accent-lime shrink-0 mt-0.5" />
            <div>
              <p className="text-[11px] font-medium text-text-primary leading-tight">
                "Every Metric Tells a Story."
              </p>
              <p className="text-[10px] text-text-tertiary mt-0.5">
                Independent Sports Analytics
              </p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
