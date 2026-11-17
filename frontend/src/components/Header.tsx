import React from 'react';
import { ShieldCheck, UserCircle, LogOut, Cpu } from 'lucide-react';
import { User } from '../types';

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
  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center p-2 bg-blue-600 rounded-lg text-white">
              <ShieldCheck className="w-6 h-6" aria-hidden="true" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight">BrandSentinel</span>
              <span className="ml-2 text-xs bg-slate-800 text-blue-400 px-2 py-0.5 rounded font-mono">
                v1.0.0
              </span>
            </div>
          </div>

          {/* Brand Switcher & Provider Badge */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1.5 bg-slate-800 px-2.5 py-1 rounded-full text-xs font-mono text-emerald-400 border border-emerald-900">
              <Cpu className="w-3.5 h-3.5" />
              <span>AI provider: mock</span>
            </div>

            <select
              value={brand}
              onChange={(e) => onSelectBrand(e.target.value)}
              aria-label="Select active brand kit"
              className="bg-slate-800 text-slate-200 text-xs font-medium rounded-md px-3 py-1.5 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="NovaFit">NovaFit (Health & Fitness)</option>
              <option value="Lumen Bank">Lumen Bank (Fintech)</option>
              <option value="Aster University">Aster University (Higher Ed)</option>
            </select>

            {user && (
              <div className="flex items-center space-x-3 pl-2 border-l border-slate-800">
                <div className="flex items-center space-x-2">
                  <UserCircle className="w-5 h-5 text-slate-400" />
                  <div className="text-left text-xs leading-tight">
                    <div className="font-semibold text-slate-200">{user.email}</div>
                    <span className="inline-block text-[10px] uppercase font-bold text-blue-400">
                      {user.role}
                    </span>
                  </div>
                </div>

                <button
                  onClick={onLogout}
                  aria-label="Log out"
                  className="p-1.5 text-slate-400 hover:text-red-400 rounded transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Navigation Tabs */}
        {user && (
          <nav className="flex space-x-1 overflow-x-auto pb-1" aria-label="Main Navigation">
            {[
              { id: 'submissions', label: 'Draft Submissions' },
              { id: 'review', label: 'Review & Approvals' },
              { id: 'kb', label: 'Knowledge Base' },
              { id: 'vision', label: 'Visual & Contrast (I-2)' },
              { id: 'audit', label: 'Audit Trail' },
              { id: 'insights', label: 'Insights & Ambiguity (I-3)' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => onSelectTab(tab.id)}
                className={`px-3 py-2 text-xs font-medium rounded-t-md transition-colors border-b-2 whitespace-nowrap ${
                  currentTab === tab.id
                    ? 'border-blue-500 text-blue-400 bg-slate-800/60'
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
