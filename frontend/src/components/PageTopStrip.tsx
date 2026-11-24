import React, { useState, useEffect } from 'react';
import { Sun, Moon, HelpCircle, Check, Cpu, ShieldCheck } from 'lucide-react';
import { api } from '../api';

export type WorkflowStep =
  | 'draft'
  | 'checked'
  | 'revising'
  | 'submitted'
  | 'manager_review'
  | 'escalated'
  | 'approved';

interface PageTopStripProps {
  title: string;
  category?: string;
  currentStep?: WorkflowStep;
  nextStepText?: string;
  actionButtons?: React.ReactNode;
  onHelpClick?: () => void;
}

export const PageTopStrip: React.FC<PageTopStripProps> = ({
  title,
  category = 'Editorial Proofing',
  currentStep,
  nextStepText,
  actionButtons,
  onHelpClick,
}) => {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window !== 'undefined') {
      const explicit = localStorage.getItem('theme_explicit');
      if (explicit === 'true') {
        const stored = localStorage.getItem('theme');
        if (stored === 'dark' || stored === 'light') return stored;
      }
      // Clear legacy auto-saved dark mode
      localStorage.removeItem('theme');
    }
    // Default to the signature warm "Paper" editorial desk
    return 'light';
  });

  const [aiProvider, setAiProvider] = useState<{
    status: string;
    label: string;
    isOffline: boolean;
  }>({
    status: 'checking',
    label: 'Checking AI engine...',
    isOffline: false,
  });

  useEffect(() => {
    // Apply theme to document
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => {
      const next = prev === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme_explicit', 'true');
      return next;
    });
  };

  useEffect(() => {
    let mounted = true;
    api
      .getHealth()
      .then((data) => {
        if (!mounted) return;
        if (data.ai_provider) {
          const isMockOrDet =
            data.ai_provider.status === 'mock' ||
            data.ai_provider.status === 'deterministic' ||
            !data.ai_provider.has_key;
          const displayLabel = isMockOrDet
            ? 'Offline checks (deterministic fallback)'
            : `${data.ai_provider.name || 'Gemini'} 1.5`;
          setAiProvider({
            status: data.ai_provider.status,
            label: displayLabel,
            isOffline: isMockOrDet,
          });
        } else {
          setAiProvider({
            status: 'active',
            label: 'Gemini Pro 1.5',
            isOffline: false,
          });
        }
      })
      .catch(() => {
        if (mounted) {
          setAiProvider({
            status: 'fallback',
            label: 'Offline checks (rules engine)',
            isOffline: true,
          });
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  const workflowSteps: { key: WorkflowStep; label: string }[] = [
    { key: 'draft', label: 'Draft' },
    { key: 'checked', label: 'Checked' },
    { key: 'revising', label: 'Revising' },
    { key: 'submitted', label: 'Submitted' },
    { key: 'manager_review', label: 'Manager review' },
    { key: 'escalated', label: 'Escalated' },
    { key: 'approved', label: 'Approved' },
  ];

  const getStepIndex = (stepKey?: WorkflowStep) => {
    if (!stepKey) return -1;
    return workflowSteps.findIndex((s) => s.key === stepKey);
  };

  const activeIndex = getStepIndex(currentStep);

  return (
    <header className="px-8 pt-6 pb-4 border-b" style={{ borderColor: 'var(--hairline)' }}>
      {/* Top row: Title + Actions (AI Pill, Theme, Help) */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          {/* Breadcrumb category */}
          <div className="flex items-center gap-1.5 text-xs mb-1" style={{ color: 'var(--muted)' }}>
            <span>BrandSentinel</span>
            <span>/</span>
            <span style={{ color: 'var(--accent-ink)' }} className="font-medium">
              {category}
            </span>
          </div>

          {/* Fraunces serif headline */}
          <h1
            className="text-2xl md:text-3xl font-serif font-semibold tracking-tight"
            style={{ color: 'var(--ink)' }}
          >
            {title}
          </h1>
        </div>

        {/* Right tools: AI Provider, Theme Toggle, Help */}
        <div className="flex items-center gap-3">
          {/* Real AI Status Pill */}
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono border"
            style={{
              backgroundColor: aiProvider.isOffline ? 'var(--paper)' : 'var(--accent-surface)',
              borderColor: aiProvider.isOffline ? 'var(--hairline)' : 'var(--accent)',
              color: aiProvider.isOffline ? 'var(--graphite)' : 'var(--accent-ink)',
            }}
            title={
              aiProvider.isOffline
                ? 'Running deterministic rule engine without external AI calls'
                : 'Active verified model grounded to workspace KB'
            }
          >
            <span
              className={`w-2 h-2 rounded-full ${
                aiProvider.isOffline ? 'bg-amber-500' : 'bg-emerald-500 animate-pulse'
              }`}
            />
            <Cpu size={13} />
            <span className="truncate max-w-[210px]">{aiProvider.label}</span>
          </div>

          {/* Theme Toggle Button (Paper / Night Desk) */}
          <button
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'light' ? 'night' : 'paper'} mode`}
            title={`Switch to ${theme === 'light' ? 'night desk' : 'paper desk'} theme`}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-[2px] border transition-colors hover:bg-black/5 dark:hover:bg-white/5 text-xs font-medium cursor-pointer"
            style={{
              backgroundColor: 'var(--sheet)',
              borderColor: 'var(--hairline)',
              color: 'var(--graphite)',
            }}
          >
            {theme === 'light' ? <Moon size={13} /> : <Sun size={13} />}
            <span>{theme === 'light' ? 'Night mode' : 'Paper mode'}</span>
          </button>

          {/* Help Button */}
          <button
            onClick={onHelpClick}
            aria-label="Editorial proofing guide & keyboard shortcuts"
            title="Editorial proofing guide & shortcuts"
            className="p-2 rounded-[2px] border transition-colors hover:bg-black/5 dark:hover:bg-white/5"
            style={{
              backgroundColor: 'var(--sheet)',
              borderColor: 'var(--hairline)',
              color: 'var(--graphite)',
            }}
          >
            <HelpCircle size={15} />
          </button>
        </div>
      </div>

      {/* Workflow Ribbon (for draft and review pages) */}
      {currentStep && (
        <div className="mt-5 pt-4 border-t flex flex-col md:flex-row md:items-center justify-between gap-4" style={{ borderColor: 'var(--hairline-subtle)' }}>
          <div className="flex items-center flex-wrap gap-2 text-xs" aria-label="Workflow progress">
            {workflowSteps.map((step, idx) => {
              const isPast = activeIndex > idx;
              const isCurrent = activeIndex === idx;

              return (
                <div key={step.key} className="flex items-center gap-1.5">
                  <div
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-[2px] font-medium transition-all ${
                      isCurrent
                        ? 'font-semibold shadow-xs'
                        : isPast
                        ? 'opacity-80'
                        : 'opacity-40'
                    }`}
                    style={{
                      backgroundColor: isCurrent
                        ? 'var(--accent)'
                        : isPast
                        ? 'var(--accent-surface)'
                        : 'transparent',
                      color: isCurrent
                        ? '#ffffff'
                        : isPast
                        ? 'var(--accent-ink)'
                        : 'var(--muted)',
                      border: isPast || isCurrent ? '1px solid var(--accent)' : '1px solid var(--hairline)',
                    }}
                  >
                    {isPast && <Check size={12} strokeWidth={2.5} />}
                    <span>{step.label}</span>
                  </div>
                  {idx < workflowSteps.length - 1 && (
                    <span className="text-[10px]" style={{ color: 'var(--hairline)' }}>
                      →
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Next Allowed Action Buttons if passed */}
          {actionButtons && <div className="flex items-center gap-2">{actionButtons}</div>}
        </div>
      )}

      {/* Persistent English Next Step line */}
      {nextStepText && (
        <div
          className="mt-3 flex items-center gap-2 text-xs py-1.5 px-3 rounded-[2px]"
          style={{
            backgroundColor: 'var(--accent-surface)',
            color: 'var(--accent-ink)',
            borderLeft: '3px solid var(--accent)',
          }}
        >
          <span className="font-semibold tracking-wide">Next step:</span>
          <span>{nextStepText}</span>
        </div>
      )}
    </header>
  );
};
