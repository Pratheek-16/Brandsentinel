import React, { useState, useEffect } from 'react';
import { Lock, AlertCircle, Building2, BookOpen, UserCheck, ShieldCheck, ArrowRight } from 'lucide-react';
import { api } from '../api';
import { WorkspaceInfoWithUsers } from '../types';
import { PilcrowShieldLogo } from './NavigationRail';

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
        { label: 'Creator', email: `creator1@${domain}.local`, role: 'creator' },
        { label: 'Manager', email: `manager@${domain}.local`, role: 'manager' },
        { label: 'Reviewer', email: `reviewer@${domain}.local`, role: 'reviewer' },
        { label: 'Admin', email: `admin@${domain}.local`, role: 'admin' },
      ];

  const brandOptions = [
    {
      name: 'NovaFit',
      tag: 'Athletics & DTC',
      desc: 'Active lifestyle, direct-to-consumer athletic wear and wellness.',
    },
    {
      name: 'Lumen Bank',
      tag: 'Fintech & Banking',
      desc: 'Strict regulatory financial disclosures, APR claims, FDIC compliance.',
    },
    {
      name: 'Aster University',
      tag: 'Higher Education',
      desc: 'Academic citations, faculty facts, tuition claims, formal style.',
    },
  ];

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4 sm:p-8"
      style={{
        backgroundColor: 'var(--paper)',
        backgroundImage: 'var(--paper-grain)',
      }}
    >
      <div className="max-w-5xl w-full grid grid-cols-1 md:grid-cols-12 gap-10 items-stretch">
        {/* Left Column: Editorial Proofing Desk Purpose & Trust Pillars */}
        <div
          className="md:col-span-5 flex flex-col justify-between p-8 rounded-[2px] border"
          style={{
            backgroundColor: 'var(--sheet)',
            borderColor: 'var(--hairline)',
          }}
        >
          <div>
            {/* Custom SVG Pilcrow Logo & Editorial Wordmark */}
            <div className="flex items-center gap-3 mb-6">
              <div
                className="p-2 rounded-[2px]"
                style={{
                  backgroundColor: 'var(--accent-surface)',
                  color: 'var(--accent)',
                }}
              >
                <PilcrowShieldLogo size={28} />
              </div>
              <div>
                <span
                  className="font-serif font-bold text-xl tracking-tight block leading-tight"
                  style={{ color: 'var(--ink)' }}
                >
                  BrandSentinel
                </span>
                <span className="text-xs" style={{ color: 'var(--muted)' }}>
                  The Proofing Desk
                </span>
              </div>
            </div>

            {/* Headline in Fraunces serif */}
            <h1
              className="text-2xl sm:text-3xl font-serif font-semibold leading-snug tracking-tight mb-4"
              style={{ color: 'var(--ink)' }}
            >
              Check content against your approved brand facts before it goes public.
            </h1>

            <p className="text-sm leading-relaxed mb-8" style={{ color: 'var(--graphite)' }}>
              An editorial proofing system that marks up drafts against grounded brand rules,
              safeguards private data, and attaches immutable citations to every change.
            </p>

            {/* 3 Reassurances */}
            <div className="space-y-4 pt-2 border-t" style={{ borderColor: 'var(--hairline-subtle)' }}>
              <div className="flex items-start gap-3">
                <div
                  className="p-1.5 rounded-[2px] mt-0.5"
                  style={{
                    backgroundColor: 'var(--accent-surface)',
                    color: 'var(--accent)',
                  }}
                >
                  <BookOpen size={16} />
                </div>
                <div>
                  <h2 className="text-sm font-medium" style={{ color: 'var(--ink)' }}>
                    Every finding cites its source
                  </h2>
                  <p className="text-xs mt-0.5 leading-relaxed" style={{ color: 'var(--muted)' }}>
                    Exact rule text, knowledge-base version, and verifiable grounding trail.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div
                  className="p-1.5 rounded-[2px] mt-0.5"
                  style={{
                    backgroundColor: 'var(--accent-surface)',
                    color: 'var(--accent)',
                  }}
                >
                  <UserCheck size={16} />
                </div>
                <div>
                  <h2 className="text-sm font-medium" style={{ color: 'var(--ink)' }}>
                    People approve
                  </h2>
                  <p className="text-xs mt-0.5 leading-relaxed" style={{ color: 'var(--muted)' }}>
                    Clear two-tier editorial review with role separation and tamper-proof approval seals.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div
                  className="p-1.5 rounded-[2px] mt-0.5"
                  style={{
                    backgroundColor: 'var(--accent-surface)',
                    color: 'var(--accent)',
                  }}
                >
                  <ShieldCheck size={16} />
                </div>
                <div>
                  <h2 className="text-sm font-medium" style={{ color: 'var(--ink)' }}>
                    Private data stays hidden
                  </h2>
                  <p className="text-xs mt-0.5 leading-relaxed" style={{ color: 'var(--muted)' }}>
                    Personal and sensitive information is redacted before analysis begins.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Brand Workspace Selector */}
          <div className="mt-8 pt-4 border-t" style={{ borderColor: 'var(--hairline-subtle)' }}>
            <span className="block text-xs font-medium mb-2.5" style={{ color: 'var(--muted)' }}>
              Brand workspace
            </span>
            <div className="grid grid-cols-3 gap-2">
              {brandOptions.map((b) => {
                const isSelected = selectedBrand.toLowerCase() === b.name.toLowerCase();
                return (
                  <button
                    key={b.name}
                    type="button"
                    onClick={() => handleBrandChange(b.name)}
                    className="p-2 text-left rounded-[2px] border transition-all"
                    style={{
                      backgroundColor: isSelected ? 'var(--accent-surface)' : 'var(--paper)',
                      borderColor: isSelected ? 'var(--accent)' : 'var(--hairline)',
                      color: isSelected ? 'var(--accent-ink)' : 'var(--graphite)',
                    }}
                  >
                    <span className="block text-xs font-semibold truncate">{b.name}</span>
                    <span className="block text-[10px] truncate" style={{ color: 'var(--muted)' }}>
                      {b.tag}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Editorial Sign-in Card */}
        <div
          className="md:col-span-7 p-8 rounded-[2px] border flex flex-col justify-between"
          style={{
            backgroundColor: 'var(--sheet)',
            borderColor: 'var(--hairline)',
            boxShadow: '0 4px 20px -2px rgba(20, 23, 31, 0.05)',
          }}
        >
          <div>
            <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: 'var(--hairline-subtle)' }}>
              <span
                className="text-xs font-mono px-2 py-0.5 rounded-[2px]"
                style={{
                  backgroundColor: 'var(--accent-surface)',
                  color: 'var(--accent-ink)',
                  border: '1px solid var(--accent)',
                }}
              >
                Workspace: {selectedBrand}
              </span>
              <span className="text-xs" style={{ color: 'var(--muted)' }}>
                Session credentials
              </span>
            </div>

            <h2
              className="mt-6 text-2xl font-serif font-semibold tracking-tight"
              style={{ color: 'var(--ink)' }}
            >
              Sign in to your desk
            </h2>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
              Choose a quick-fill role below or enter your credentials.
            </p>

            {/* Quick-fill Role Chips */}
            <div className="mt-5">
              <span className="block text-xs font-medium mb-2" style={{ color: 'var(--graphite)' }}>
                Quick-fill role chips
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {displayAccounts.map((acc: any) => {
                  const label = acc.label || acc.name || acc.email.split('@')[0];
                  const isSelected = email.toLowerCase() === acc.email.toLowerCase();
                  return (
                    <button
                      key={acc.email}
                      type="button"
                      onClick={() => handleSelectAccount(acc)}
                      className="p-2.5 rounded-[2px] border text-left transition-all"
                      style={{
                        backgroundColor: isSelected ? 'var(--accent-surface)' : 'var(--paper)',
                        borderColor: isSelected ? 'var(--accent)' : 'var(--hairline)',
                        color: isSelected ? 'var(--accent-ink)' : 'var(--graphite)',
                      }}
                    >
                      <div className="font-semibold text-xs truncate capitalize">{label}</div>
                      <div
                        className="text-[10px] font-mono mt-0.5 capitalize truncate"
                        style={{ color: isSelected ? 'var(--accent-ink)' : 'var(--muted)' }}
                      >
                        {acc.role}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {error && (
              <div
                className="mt-4 p-3 rounded-[2px] border flex items-center gap-2 text-xs"
                style={{
                  backgroundColor: 'var(--severity-blocker-bg)',
                  borderColor: 'var(--severity-blocker)',
                  color: 'var(--severity-blocker)',
                }}
              >
                <AlertCircle size={15} className="shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Form */}
            <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
              <div>
                <label
                  htmlFor="auth-email"
                  className="block text-xs font-medium mb-1"
                  style={{ color: 'var(--graphite)' }}
                >
                  Email address
                </label>
                <input
                  id="auth-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-[2px] border transition-colors focus:outline-none"
                  style={{
                    backgroundColor: 'var(--paper)',
                    borderColor: 'var(--hairline)',
                    color: 'var(--ink)',
                  }}
                />
              </div>

              <div>
                <label
                  htmlFor="auth-password"
                  className="block text-xs font-medium mb-1"
                  style={{ color: 'var(--graphite)' }}
                >
                  Password
                </label>
                <input
                  id="auth-password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-[2px] border transition-colors focus:outline-none"
                  style={{
                    backgroundColor: 'var(--paper)',
                    borderColor: 'var(--hairline)',
                    color: 'var(--ink)',
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-[2px] text-sm font-medium transition-all cursor-pointer disabled:opacity-50"
                style={{
                  backgroundColor: 'var(--accent)',
                  color: '#ffffff',
                }}
              >
                <Lock size={15} />
                <span>{loading ? 'Authenticating...' : 'Open proofing desk'}</span>
                <ArrowRight size={15} />
              </button>
            </form>
          </div>

          <div className="mt-6 pt-4 border-t text-center text-xs" style={{ borderColor: 'var(--hairline-subtle)', color: 'var(--muted)' }}>
            <span>Seeded credentials with deterministic role segregation &amp; zero-knowledge audit chain.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
