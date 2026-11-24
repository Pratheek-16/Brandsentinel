import React, { useState } from 'react';
import {
  PenTool,
  FileCheck2,
  Eye,
  Layers,
  AlertCircle,
  BarChart3,
  BookOpen,
  History,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Building2,
  ShieldAlert,
} from 'lucide-react';
import { User } from '../types';

export const PilcrowShieldLogo: React.FC<{ className?: string; size?: number }> = ({
  className = 'w-6 h-6',
  size = 24,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    aria-label="BrandSentinel Logo"
  >
    {/* Shield-shaped pilcrow bowl on the left */}
    <path
      d="M13 3H7.5C5 3 3.5 5 3.5 7.5C3.5 11 7 13.5 9.5 14.5L13 15V3Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      fill="currentColor"
      fillOpacity="0.14"
    />
    {/* Primary vertical stem */}
    <path d="M13 3V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    {/* Secondary vertical stem */}
    <path d="M17 3V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    {/* Top cross bar */}
    <path d="M7.5 3H19.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

interface NavigationRailProps {
  user: User | null;
  brand: string;
  onSelectBrand: (brand: string) => void;
  currentTab: string;
  onSelectTab: (tab: string) => void;
  onLogout: () => void;
}

export const NavigationRail: React.FC<NavigationRailProps> = ({
  user,
  brand,
  onSelectBrand,
  currentTab,
  onSelectTab,
  onLogout,
}) => {
  const [collapsed, setCollapsed] = useState(false);

  // Role-aware navigation definitions per spec
  const getNavItems = () => {
    const role = user?.role || 'creator';

    if (role === 'creator') {
      return [
        { id: 'submissions', label: 'Drafts', icon: PenTool, description: 'Write & proof content' },
        { id: 'review', label: 'My reviews', icon: FileCheck2, description: 'Track ongoing reviews' },
        { id: 'vision', label: 'Visual check', icon: Eye, description: 'Color & logo contrast' },
      ];
    }

    if (role === 'manager') {
      return [
        { id: 'review', label: 'Review queue', icon: Layers, description: 'Submissions awaiting review' },
        { id: 'submissions', label: 'Drafts', icon: PenTool, description: 'Direct composition' },
        { id: 'insights', label: 'Insights', icon: BarChart3, description: 'Failure rates & trends' },
        { id: 'vision', label: 'Visual check', icon: Eye, description: 'Color & asset audit' },
      ];
    }

    if (role === 'reviewer') {
      return [
        { id: 'review', label: 'High-risk queue', icon: ShieldAlert, description: 'Escalated items' },
        { id: 'submissions', label: 'Drafts', icon: PenTool, description: 'Draft review' },
        { id: 'vision', label: 'Visual check', icon: Eye, description: 'Visual compliance' },
        { id: 'insights', label: 'Insights', icon: BarChart3, description: 'Review intelligence' },
      ];
    }

    // Admin role has full access
    return [
      { id: 'kb', label: 'Brand rules', icon: BookOpen, description: 'Facts, terms & guidelines' },
      { id: 'submissions', label: 'Drafts', icon: PenTool, description: 'Authoring & checks' },
      { id: 'review', label: 'Review queue', icon: Layers, description: 'Active approvals' },
      { id: 'insights', label: 'Insights', icon: BarChart3, description: 'Rule performance' },
      { id: 'audit', label: 'Audit trail', icon: History, description: 'Cryptographic ledger' },
      { id: 'vision', label: 'Visual check', icon: Eye, description: 'Palette & contrast' },
    ];
  };

  const navItems = getNavItems();

  const getRoleDisplayName = (role?: string) => {
    switch (role) {
      case 'admin':
        return 'Administrator';
      case 'reviewer':
        return 'Authorised Reviewer';
      case 'manager':
        return 'Brand Manager';
      default:
        return 'Creator';
    }
  };

  return (
    <aside
      className={`h-screen sticky top-0 flex flex-col justify-between shrink-0 transition-all duration-200 ease-out z-40 select-none ${
        collapsed ? 'w-[72px]' : 'w-[240px]'
      }`}
      style={{
        backgroundColor: 'var(--sheet)',
        borderRight: '1px solid var(--hairline)',
      }}
      aria-label="Sidebar navigation"
    >
      {/* Top: Logo & Platform Identity + Scrollable nav items */}
      <div className="flex flex-col min-h-0 flex-1 overflow-hidden">
        <div
          className={`flex items-center h-16 border-b px-4 shrink-0 ${
            collapsed ? 'justify-center' : 'justify-between'
          }`}
          style={{ borderColor: 'var(--hairline)' }}
        >
          <div
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => onSelectTab(navItems[0].id)}
            title="BrandSentinel - The Proofing Desk"
          >
            <div
              className="p-1.5 rounded-[2px] transition-colors"
              style={{
                backgroundColor: 'var(--accent-surface)',
                color: 'var(--accent)',
              }}
            >
              <PilcrowShieldLogo size={22} />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span
                  className="font-serif font-bold text-base tracking-tight leading-tight"
                  style={{ color: 'var(--ink)' }}
                >
                  BrandSentinel
                </span>
                <span
                  className="text-[10px] tracking-wide"
                  style={{ color: 'var(--muted)' }}
                >
                  Proofing desk
                </span>
              </div>
            )}
          </div>

          {!collapsed && (
            <button
              onClick={() => setCollapsed(true)}
              aria-label="Collapse navigation rail"
              className="p-1.5 rounded-[2px] hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
              style={{ color: 'var(--muted)' }}
            >
              <ChevronLeft size={16} />
            </button>
          )}
        </div>

        {/* Collapsed expansion trigger button */}
        {collapsed && (
          <div className="flex justify-center py-2 border-b" style={{ borderColor: 'var(--hairline-subtle)' }}>
            <button
              onClick={() => setCollapsed(false)}
              aria-label="Expand navigation rail"
              className="p-1 rounded-[2px] hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
              style={{ color: 'var(--muted)' }}
              title="Expand rail"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        )}

        {/* Navigation Items (Scrollable if viewport is short) */}
        <nav className="p-2 space-y-1 overflow-y-auto flex-1 min-h-0" aria-label="Main menu">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                title={collapsed ? item.label : undefined}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-[2px] text-sm font-medium transition-all text-left group cursor-pointer ${
                  isActive ? 'shadow-xs' : 'hover:bg-black/4 dark:hover:bg-white/4'
                }`}
                style={{
                  backgroundColor: isActive ? 'var(--accent-surface)' : 'transparent',
                  color: isActive ? 'var(--accent-ink)' : 'var(--graphite)',
                  borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
                }}
              >
                <Icon
                  size={18}
                  className="shrink-0 transition-transform group-hover:scale-105"
                  style={{
                    color: isActive ? 'var(--accent)' : 'var(--muted)',
                  }}
                />
                {!collapsed && (
                  <div className="flex-1 min-w-0">
                    <span className="block truncate text-[13px] font-medium">{item.label}</span>
                  </div>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom: Workspace Switcher & User Profile (Permanently docked & visible) */}
      <div className="p-3 border-t space-y-3 shrink-0" style={{ borderColor: 'var(--hairline)' }}>
        {/* Workspace Kit Switcher */}
        {!collapsed ? (
          <div
            className="p-2 rounded-[2px] border text-xs"
            style={{
              backgroundColor: 'var(--paper)',
              borderColor: 'var(--hairline)',
            }}
          >
            <div className="flex items-center gap-1.5 mb-1 text-[11px]" style={{ color: 'var(--muted)' }}>
              <Building2 size={12} />
              <span>Brand workspace</span>
            </div>
            <select
              value={brand}
              onChange={(e) => onSelectBrand(e.target.value)}
              aria-label="Active brand kit"
              className="w-full bg-transparent font-medium cursor-pointer text-xs focus:outline-none"
              style={{ color: 'var(--ink)' }}
            >
              <option value="NovaFit">NovaFit</option>
              <option value="Lumen Bank">Lumen Bank</option>
              <option value="Aster University">Aster University</option>
            </select>
          </div>
        ) : (
          <div
            className="flex justify-center p-2 rounded-[2px] border"
            title={`Active brand: ${brand}`}
            style={{
              backgroundColor: 'var(--paper)',
              borderColor: 'var(--hairline)',
              color: 'var(--graphite)',
            }}
          >
            <Building2 size={16} />
          </div>
        )}

        {/* User Card */}
        {user && (
          <div
            className={`flex items-center gap-2 pt-2 border-t ${
              collapsed ? 'justify-center' : 'justify-between'
            }`}
            style={{ borderColor: 'var(--hairline-subtle)' }}
          >
            {!collapsed ? (
              <div className="min-w-0 flex-1">
                <p
                  className="text-xs font-semibold truncate leading-tight"
                  style={{ color: 'var(--ink)' }}
                  title={user.email}
                >
                  {user.email}
                </p>
                <div className="flex items-center gap-1 mt-0.5">
                  <span
                    className="inline-block px-1.5 py-0.5 rounded-[2px] text-[10px] font-mono tracking-tight capitalize"
                    style={{
                      backgroundColor: 'var(--accent-surface)',
                      color: 'var(--accent-ink)',
                      border: '1px solid var(--accent)',
                      opacity: 0.9,
                    }}
                  >
                    {getRoleDisplayName(user.role)}
                  </span>
                </div>
              </div>
            ) : null}

            <button
              onClick={onLogout}
              title="Sign out of workspace"
              aria-label="Sign out"
              className="p-1.5 rounded-[2px] hover:bg-red-50 dark:hover:bg-red-950/30 hover:text-red-700 transition-colors shrink-0"
              style={{ color: 'var(--muted)' }}
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
};
