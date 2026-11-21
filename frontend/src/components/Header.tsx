import React, { useState, useEffect } from 'react';
import { ShieldCheck, UserCircle, LogOut, Cpu, Building2 } from 'lucide-react';
import { User } from '../types';
import { api } from '../api';

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
  brand: string;
  onSelectBrand: (brand: string) => void;
  currentTab: string;
  onSelectTab: (tab: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  user,
  onLogout,
  brand,
  onSelectBrand,
  currentTab,
  onSelectTab,
}) => {
  const [aiStatus, setAiStatus] = useState<{ status: string; label: string }>({
    status: 'checking',
    label: 'Checking AI provider...',
  });

  useEffect(() => {
    let isMounted = true;
    api.getHealth()
      .then((data) => {
        if (!isMounted) return;
        if (data.ai_provider) {
          setAiStatus({
            status: data.ai_provider.status,
            label: data.ai_provider.label,
          });
        } else {
          setAiStatus({ status: 'active', label: 'AI Provider: Active' });
        }
      })
      .catch(() => {
        if (isMounted) setAiStatus({ status: 'error', label: 'AI Provider: Offline' });
      });
    return () => { isMounted = false; };
  }, []);

  const getAiBadgeColor = () => {
    switch (aiStatus.status) {
      case 'active':
        return 'text-emerald-400 border-emerald-900/80 bg-slate-800';
      case 'mock':
        return 'text-blue-400 border-blue-900/80 bg-slate-800';
      case 'deterministic':
        return 'text-amber-400 border-amber-900/80 bg-slate-800';
      case 'error':
        return 'text-red-400 border-red-900/80 bg-slate-800';
      default:
        return 'text-slate-400 border-slate-700 bg-slate-800';
    }
  };

  const getAiDotColor = () => {
    switch (aiStatus.status) {
      case 'active':
        return 'bg-emerald-400 animate-pulse';
      case 'mock':
        return 'bg-blue-400';
      case 'deterministic':
        return 'bg-amber-400';
      case 'error':
        return 'bg-red-400';
      default:
        return 'bg-slate-400';
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-900/60 text-purple-300 border-purple-700';
      case 'reviewer':
        return 'bg-cyan-900/60 text-cyan-300 border-cyan-700';
      case 'manager':
        return 'bg-amber-900/60 text-amber-300 border-amber-700';
      default:
        return 'bg-emerald-900/60 text-emerald-300 border-emerald-700';
    }
  };

  const navItems = [
    { id: 'submissions', label: 'Draft Submissions' },
    { id: 'review', label: 'Review & Approvals' },
    { id: 'kb', label: 'Brand Knowledge Base' },
    { id: 'vision', label: 'Visual & Contrast (I-2)' },
    { id: 'audit', label: 'Cryptographic Audit Trail' },
    { id: 'insights', label: 'Insights & Ambiguity (I-3)' },
  ];

  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Platform Name */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center p-2 bg-blue-600 rounded-lg text-white shadow-sm">
              <ShieldCheck className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <span className="font-extrabold text-lg tracking-tight text-white">BrandSentinel</span>
              <span className="ml-2 text-[10px] bg-slate-800 text-blue-400 px-2 py-0.5 rounded font-mono border border-slate-700">
                v1.0.0
              </span>
            </div>
          </div>

          {/* Controls: AI Provider, Workspace Selector, User Persona */}
          <div className="flex items-center space-x-4">
            <div className={`hidden sm:flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-mono border ${getAiBadgeColor()}`}>
              <span className={`w-2 h-2 rounded-full ${getAiDotColor()}`} />
              <Cpu className="w-3.5 h-3.5" />
              <span>{aiStatus.label}</span>
            </div>

            <div className="flex items-center space-x-1.5 bg-slate-800 border border-slate-700 rounded-lg px-2 py-1">
              <Building2 className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={brand}
                onChange={(e) => onSelectBrand(e.target.value)}
                aria-label="Select active brand kit"
                className="bg-transparent text-slate-200 text-xs font-semibold focus:outline-none cursor-pointer"
              >
                <option value="NovaFit" className="bg-slate-900 text-slate-100">NovaFit</option>
                <option value="Lumen Bank" className="bg-slate-900 text-slate-100">Lumen Bank</option>
                <option value="Aster University" className="bg-slate-900 text-slate-100">Aster University</option>
              </select>
            </div>

            {user && (
              <div className="flex items-center space-x-3 pl-3 border-l border-slate-800">
                <div className="flex items-center space-x-2">
                  <UserCircle className="w-6 h-6 text-slate-400" />
                  <div className="text-left text-xs leading-tight hidden md:block">
                    <div className="font-semibold text-slate-200 truncate max-w-[140px]">
                      {user.email}
                    </div>
                    <span
                      className={`inline-block text-[10px] uppercase font-bold px-1.5 py-0.2 rounded border ${getRoleBadge(
                        user.role
                      )}`}
                    >
                      {user.role}
                    </span>
                  </div>
                </div>

                <button
                  onClick={onLogout}
                  aria-label="Log out"
                  title="Sign out of console"
                  className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-md transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Navigation Tabs */}
        {user && (
          <nav className="flex space-x-1 overflow-x-auto pb-1 border-t border-slate-800/80 pt-1" aria-label="Main Navigation">
            {navItems.map((tab) => (
              <button
                key={tab.id}
                onClick={() => onSelectTab(tab.id)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-t-md transition-colors border-b-2 whitespace-nowrap ${
                  currentTab === tab.id
                    ? 'border-blue-500 text-blue-400 bg-slate-800/70'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        )}
      </div>
    </header>
  );
};
