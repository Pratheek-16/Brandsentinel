import React, { useState, useEffect } from 'react';
import { ShieldCheck, Lock, UserCheck, AlertCircle, Building2, ChevronRight, Sparkles } from 'lucide-react';
import { api } from '../api';
import { WorkspaceInfoWithUsers, DemoAccountInfo } from '../types';

interface LoginScreenProps {
  onLoginSuccess: (token: string, user: any) => void;
  brand: string;
  onSelectBrand: (brand: string) => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({
  onLoginSuccess,
  brand,
  onSelectBrand,
}) => {
  const [workspaces, setWorkspaces] = useState<WorkspaceInfoWithUsers[]>([]);
  const [selectedBrand, setSelectedBrand] = useState<string>(brand || 'NovaFit');
  const [email, setEmail] = useState<string>('creator1@novafit.local');
  const [password, setPassword] = useState<string>('Demo@12345');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    api
      .listWorkspaces()
      .then((wsList) => {
        if (mounted && wsList && wsList.length > 0) {
          setWorkspaces(wsList);
        }
      })
      .catch((err) => {
        console.warn('Could not load workspaces list dynamically:', err);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const handleBrandChange = (newBrand: string) => {
    setSelectedBrand(newBrand);
    onSelectBrand(newBrand);
    const domain = newBrand.toLowerCase().replace(/\s+/g, '');
    setEmail(`creator1@${domain}.local`);
    setPassword('Demo@12345');
    setError(null);
  };

  const handleSelectAccount = (acc: { email: string; role: string }) => {
    setEmail(acc.email);
    setPassword('Demo@12345');
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please provide both email and password.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(email.trim(), password);
      onLoginSuccess(res.access_token, res.user);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  // Derive active workspace accounts
  const activeWs = workspaces.find(
    (w) => w.name.toLowerCase() === selectedBrand.toLowerCase()
  );
  const domain = selectedBrand.toLowerCase().replace(/\s+/g, '');

  const displayAccounts = activeWs?.accounts?.length
    ? activeWs.accounts
    : [
        { label: 'Creator 1', email: `creator1@${domain}.local`, role: 'creator' },
        { label: 'Creator 2', email: `creator2@${domain}.local`, role: 'creator' },
        { label: 'Manager', email: `manager@${domain}.local`, role: 'manager' },
        { label: 'Reviewer', email: `reviewer@${domain}.local`, role: 'reviewer' },
        { label: 'Admin (Guardian)', email: `admin@${domain}.local`, role: 'admin' },
      ];

  const brandOptions = [
    { name: 'NovaFit', tag: 'Health & Fitness', desc: 'Active lifestyle, direct-to-consumer athletic wear and wellness.' },
    { name: 'Lumen Bank', tag: 'Fintech & Banking', desc: 'Strict regulatory financial disclosures, APR claims, FDIC compliance.' },
    { name: 'Aster University', tag: 'Higher Education', desc: 'Academic excellence, faculty facts, tuition claims, formal style.' },
  ];

  return (
    <div className="min-h-[88vh] flex items-center justify-center py-10 px-4 sm:px-6 lg:px-8 bg-slate-900 text-slate-100">
      <div className="max-w-4xl w-full grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
        {/* Left Column: Context & Trust Value */}
        <div className="md:col-span-5 space-y-6">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-blue-950/80 border border-blue-800 rounded-full text-xs font-semibold text-blue-400">
              <ShieldCheck className="w-4 h-4 text-blue-400" />
              <span>Evidence-Grounded Brand Governance</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white">
              BrandSentinel
            </h1>
            <p className="text-sm text-slate-400 leading-relaxed">
              Pre-publication brand integrity platform. Enforcing deterministic grounding, privacy-preserving PII redaction, verified intent rewrites, and immutable cryptographic sign-offs.
            </p>
          </div>

          <div className="space-y-3 pt-2">
            <div className="text-xs uppercase font-bold tracking-wider text-slate-400">
              Select Brand Workspace
            </div>
            <div className="space-y-2">
              {brandOptions.map((b) => (
                <button
                  key={b.name}
                  type="button"
                  onClick={() => handleBrandChange(b.name)}
                  className={`w-full text-left p-3 rounded-lg border transition-all flex items-start justify-between ${
                    selectedBrand.toLowerCase() === b.name.toLowerCase()
                      ? 'border-blue-500 bg-slate-800/90 shadow-md ring-1 ring-blue-500'
                      : 'border-slate-800 bg-slate-900/60 hover:bg-slate-800/40 text-slate-300'
                  }`}
                >
                  <div>
                    <div className="flex items-center space-x-2">
                      <Building2 className="w-4 h-4 text-blue-400" />
                      <span className="font-semibold text-sm text-white">{b.name}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 font-mono text-slate-300">
                        {b.tag}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{b.desc}</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-500 mt-1 shrink-0" />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Authentication Card */}
        <div className="md:col-span-7 bg-white text-slate-900 p-8 rounded-2xl shadow-2xl border border-slate-200">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2.5 py-1 rounded">
                Workspace: {selectedBrand}
              </span>
              <span className="text-xs text-slate-500 font-mono">Real SHA-256 JWT Auth</span>
            </div>
            <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">
              Sign In to Console
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Select a seeded demo persona or sign in with your enterprise credentials.
            </p>
          </div>

          {/* Quick Demo Switcher */}
          <div className="mt-5">
            <label className="block text-xs font-bold uppercase text-slate-700 tracking-wider mb-2">
              Fast Persona Switcher (Password: Demo@12345)
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {displayAccounts.map((acc: any) => {
                const label = acc.label || acc.name || acc.email.split('@')[0];
                const isSelected = email.toLowerCase() === acc.email.toLowerCase();
                return (
                  <button
                    key={acc.email}
                    type="button"
                    onClick={() => handleSelectAccount(acc)}
                    className={`p-2 rounded-lg border text-left transition-all ${
                      isSelected
                        ? 'border-blue-600 bg-blue-50/80 ring-1 ring-blue-600'
                        : 'border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700'
                    }`}
                  >
                    <div className="font-semibold text-xs text-slate-900 truncate capitalize">
                      {label}
                    </div>
                    <div className="text-[10px] text-blue-700 font-bold uppercase mt-0.5">
                      {acc.role}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2 text-xs text-red-700">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="auth-email" className="block text-xs font-bold uppercase text-slate-700">
                Email Address
              </label>
              <input
                id="auth-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              />
            </div>

            <div>
              <label htmlFor="auth-password" className="block text-xs font-bold uppercase text-slate-700">
                Password
              </label>
              <input
                id="auth-password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-50"
            >
              <Lock className="w-4 h-4" />
              <span>{loading ? 'Authenticating...' : 'Authenticate Session'}</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
