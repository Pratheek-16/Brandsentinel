import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  TrendingUp,
  Sparkles,
  GitMerge,
  Clock,
  RefreshCw,
  Check,
  ArrowRight,
  Layers,
} from 'lucide-react';
import { api } from '../api';

export const InsightsScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'analytics' | 'ambiguity'>('analytics');
  const [summary, setSummary] = useState<any>(null);
  const [ambiguityData, setAmbiguityData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [resolvingCode, setResolvingCode] = useState<string | null>(null);
  const [resolvedCodes, setResolvedCodes] = useState<Record<string, string>>({});
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sum, amb] = await Promise.all([
        api.getInsightsSummary().catch(() => null),
        api.getAmbiguity().catch(() => null),
      ]);
      setSummary(sum);
      setAmbiguityData(amb);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAcceptClarification = async (signal: any) => {
    const code = signal.rule_code || signal.code || signal.key || signal.term || 'RULE';
    const proposal = signal.suggested_clarification || signal.recommendation || 'Clarified policy scope';
    try {
      setResolvingCode(code);
      const res = await api.acceptClarification({
        signal_type: signal.signal_type || 'high_dismissal',
        target_code: signal.rule_code || signal.code,
        term_preferred: signal.preferred,
        clarified_text: proposal,
      });

      setResolvedCodes((prev) => ({
        ...prev,
        [code]: res.new_kb_label || `vNext (ID: ${res.new_kb_version_id})`,
      }));

      setSuccessBanner(
        `Clarification accepted! Activated new KB version ${res.new_kb_version_id} (${res.new_kb_label}). Rule ambiguity resolved.`
      );

      await loadData();
    } catch (err: any) {
      alert(`Could not accept clarification: ${err.message || 'Error'}`);
    } finally {
      setResolvingCode(null);
    }
  };

  const flaggedRules = ambiguityData?.flagged_ambiguous_rules || [];
  const conflictingItems = ambiguityData?.conflicting_items || [];
  const staleFacts = ambiguityData?.stale_facts || [];
  const totalSignals =
    flaggedRules.length +
    conflictingItems.length +
    staleFacts.length +
    (ambiguityData?.ai_disagreements?.length || 0);

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Editorial Header */}
      <div
        className="p-6 rounded-[2px] border flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{
          backgroundColor: 'var(--sheet)',
          borderColor: 'var(--hairline)',
        }}
      >
        <div>
          <h1 className="text-2xl font-serif font-semibold tracking-tight" style={{ color: 'var(--ink)' }}>
            Governance insights &amp; ambiguity
          </h1>
          <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
            Monitor pre-publication pass rates, median review velocity, and detect rules that cause frequent overrides or contradictions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Segmented Tab Control */}
          <div
            className="inline-flex p-0.5 rounded-[2px] border text-xs"
            style={{
              backgroundColor: 'var(--paper)',
              borderColor: 'var(--hairline)',
            }}
          >
            <button
              onClick={() => setActiveTab('analytics')}
              className="px-3 py-1.5 rounded-[2px] font-medium transition-all"
              style={{
                backgroundColor: activeTab === 'analytics' ? 'var(--sheet)' : 'transparent',
                color: activeTab === 'analytics' ? 'var(--accent-ink)' : 'var(--muted)',
                boxShadow: activeTab === 'analytics' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
              }}
            >
              Analytics
            </button>
            <button
              onClick={() => setActiveTab('ambiguity')}
              className="px-3 py-1.5 rounded-[2px] font-medium transition-all flex items-center gap-1.5"
              style={{
                backgroundColor: activeTab === 'ambiguity' ? 'var(--sheet)' : 'transparent',
                color: activeTab === 'ambiguity' ? 'var(--accent-ink)' : 'var(--muted)',
                boxShadow: activeTab === 'ambiguity' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
              }}
            >
              <span>Ambiguity detector</span>
              {totalSignals > 0 && (
                <span
                  className="w-4 h-4 rounded-full text-[10px] font-mono font-bold flex items-center justify-center text-white"
                  style={{ backgroundColor: 'var(--severity-major)' }}
                >
                  {totalSignals}
                </span>
              )}
            </button>
          </div>

          <button
            onClick={loadData}
            disabled={loading}
            className="p-2 rounded-[2px] border hover:bg-black/5"
            style={{ borderColor: 'var(--hairline)', color: 'var(--graphite)' }}
            title="Refresh metrics"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {successBanner && (
        <div
          className="p-3.5 rounded-[2px] border flex items-center justify-between text-xs"
          style={{
            backgroundColor: 'var(--status-verified-bg)',
            borderColor: 'var(--status-verified)',
            color: 'var(--status-verified)',
          }}
        >
          <div className="flex items-center gap-2">
            <CheckCircle2 size={15} />
            <span>{successBanner}</span>
          </div>
          <button onClick={() => setSuccessBanner(null)} className="underline font-medium">
            Dismiss
          </button>
        </div>
      )}

      {/* ANALYTICS TAB: Big Fraunces Numerals, Sparkline Placeholders, Editorial Small Multiples */}
      {activeTab === 'analytics' && summary && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Submissions */}
            <div
              className="p-6 rounded-[2px] border space-y-2"
              style={{
                backgroundColor: 'var(--sheet)',
                borderColor: 'var(--hairline)',
              }}
            >
              <span className="block text-xs font-medium" style={{ color: 'var(--muted)' }}>
                Total submissions
              </span>
              <div
                className="text-4xl font-serif font-bold tracking-tight"
                style={{ color: 'var(--ink)' }}
              >
                {summary.content_counts?.total || 0}
              </div>
              <div className="text-[11px]" style={{ color: 'var(--graphite)' }}>
                Across all channels (Web, Social, Email)
              </div>
            </div>

            {/* Pass Rate */}
            <div
              className="p-6 rounded-[2px] border space-y-2"
              style={{
                backgroundColor: 'var(--sheet)',
                borderColor: 'var(--hairline)',
              }}
            >
              <span className="block text-xs font-medium" style={{ color: 'var(--muted)' }}>
                Publication pass rate
              </span>
              <div
                className="text-4xl font-serif font-bold tracking-tight"
                style={{ color: 'var(--status-verified)' }}
              >
                {summary.content_counts?.total > 0
                  ? Math.round(
                      ((summary.content_counts.approved || 0) / summary.content_counts.total) * 100
                    )
                  : 100}
                %
              </div>
              <div className="text-[11px]" style={{ color: 'var(--graphite)' }}>
                {summary.content_counts?.approved || 0} approved drafts signed
              </div>
            </div>

            {/* Median Review Velocity */}
            <div
              className="p-6 rounded-[2px] border space-y-2"
              style={{
                backgroundColor: 'var(--sheet)',
                borderColor: 'var(--hairline)',
              }}
            >
              <span className="block text-xs font-medium" style={{ color: 'var(--muted)' }}>
                Median review velocity
              </span>
              <div
                className="text-4xl font-serif font-bold tracking-tight"
                style={{ color: 'var(--accent-ink)' }}
              >
                3.4m
              </div>
              <div className="text-[11px]" style={{ color: 'var(--graphite)' }}>
                Automated proofing + sign-off
              </div>
            </div>

            {/* PII Shield Elements */}
            <div
              className="p-6 rounded-[2px] border space-y-2"
              style={{
                backgroundColor: 'var(--sheet)',
                borderColor: 'var(--hairline)',
              }}
            >
              <span className="block text-xs font-medium" style={{ color: 'var(--muted)' }}>
                Private data hidden
              </span>
              <div
                className="text-4xl font-serif font-bold tracking-tight"
                style={{ color: 'var(--ink)' }}
              >
                {summary.total_pii_redacted || 0}
              </div>
              <div className="text-[11px]" style={{ color: 'var(--graphite)' }}>
                Protected privacy elements
              </div>
            </div>
          </div>

          {/* Top Triggered Rules & Sparkline Ledger */}
          <div
            className="p-6 rounded-[2px] border space-y-4"
            style={{
              backgroundColor: 'var(--sheet)',
              borderColor: 'var(--hairline)',
            }}
          >
            <h3 className="font-serif font-semibold text-base" style={{ color: 'var(--ink)' }}>
              Top triggered brand guidelines
            </h3>
            <p className="text-xs" style={{ color: 'var(--graphite)' }}>
              Rules that account for the highest volume of automated margin notes across current drafts:
            </p>

            <div className="space-y-3 pt-2">
              {[
                { code: 'BR-SUPER-01', name: 'Superlative claims prohibited without third-party proof', count: 18, pct: 85 },
                { code: 'BR-SPEC-BATTERY', name: 'Battery specification standard: up to 10 days', count: 14, pct: 68 },
                { code: 'BR-FDIC-01', name: 'Mandatory Member FDIC disclaimer for deposit offers', count: 9, pct: 45 },
                { code: 'BR-TONE-WARM', name: 'Avoid aggressive scarcity language in consumer invitations', count: 6, pct: 30 },
              ].map((item) => (
                <div key={item.code} className="space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold" style={{ color: 'var(--accent-ink)' }}>
                        {item.code}
                      </span>
                      <span style={{ color: 'var(--ink)' }}>{item.name}</span>
                    </div>
                    <span className="font-mono" style={{ color: 'var(--muted)' }}>
                      {item.count} hits
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--hairline)' }}>
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${item.pct}%`, backgroundColor: 'var(--accent)' }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* AMBIGUITY DETECTOR TAB: Table-less Cards with Clarification Proposals */}
      {activeTab === 'ambiguity' && (
        <div className="space-y-6">
          {/* Signal 1: Rules with high creator dismissal rates */}
          <div
            className="p-6 rounded-[2px] border space-y-4"
            style={{
              backgroundColor: 'var(--sheet)',
              borderColor: 'var(--hairline)',
            }}
          >
            <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: 'var(--hairline-subtle)' }}>
              <div>
                <h3 className="font-serif font-semibold text-sm" style={{ color: 'var(--ink)' }}>
                  Signal 1: Rules with frequent reviewer dismissals (&gt;40%)
                </h3>
                <p className="text-[11px] mt-0.5" style={{ color: 'var(--muted)' }}>
                  Guidelines where authors or managers regularly override automated findings, indicating vague language.
                </p>
              </div>
              <span
                className="font-mono text-xs px-2 py-0.5 rounded-[2px]"
                style={{
                  backgroundColor: 'var(--severity-major-bg)',
                  color: 'var(--severity-major)',
                  border: '1px solid currentColor',
                }}
              >
                {flaggedRules.length} flagged
              </span>
            </div>

            {flaggedRules.length === 0 ? (
              <div className="py-6 text-center text-xs" style={{ color: 'var(--muted)' }}>
                <CheckCircle2 size={20} className="mx-auto mb-1.5" style={{ color: 'var(--status-verified)' }} />
                <span>No rules currently exceed the 40% dismissal threshold.</span>
              </div>
            ) : (
              <div className="space-y-3">
                {flaggedRules.map((r: any, idx: number) => {
                  const code = r.rule_code;
                  const isResolved = resolvedCodes[code];
                  return (
                    <div
                      key={idx}
                      className="p-4 rounded-[2px] border text-xs space-y-3"
                      style={{
                        backgroundColor: 'var(--paper)',
                        borderColor: 'var(--hairline)',
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold" style={{ color: 'var(--accent-ink)' }}>
                            {r.rule_code}
                          </span>
                          <span style={{ color: 'var(--graphite)' }}>
                            {r.dismissed_count} dismissals of {r.total_surfaced} ({r.dismissal_rate_pct}%)
                          </span>
                        </div>

                        {isResolved ? (
                          <span
                            className="px-2 py-0.5 rounded-[2px] font-mono text-[10px] font-bold"
                            style={{
                              backgroundColor: 'var(--status-verified-bg)',
                              color: 'var(--status-verified)',
                              border: '1px solid currentColor',
                            }}
                          >
                            Resolved in {isResolved}
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleAcceptClarification(r)}
                            disabled={resolvingCode === code}
                            className="px-3 py-1.5 rounded-[2px] text-xs font-medium text-white transition-all shadow-xs flex items-center gap-1.5"
                            style={{ backgroundColor: 'var(--accent)' }}
                          >
                            <Sparkles size={12} />
                            <span>
                              {resolvingCode === code ? 'Updating KB...' : 'Accept resolution into new version'}
                            </span>
                          </button>
                        )}
                      </div>

                      <div className="p-3 rounded-[2px] border space-y-1" style={{ backgroundColor: 'var(--sheet)', borderColor: 'var(--hairline-subtle)' }}>
                        <span className="block text-[10px]" style={{ color: 'var(--muted)' }}>
                          Proposed clarification
                        </span>
                        <p className="font-serif italic" style={{ color: 'var(--ink)' }}>
                          "{r.recommendation}"
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Signal 2: Conflicting rules / contradictory claims */}
          <div
            className="p-6 rounded-[2px] border space-y-4"
            style={{
              backgroundColor: 'var(--sheet)',
              borderColor: 'var(--hairline)',
            }}
          >
            <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: 'var(--hairline-subtle)' }}>
              <div>
                <h3 className="font-serif font-semibold text-sm" style={{ color: 'var(--ink)' }}>
                  Signal 2: Conflicting brand guidelines
                </h3>
                <p className="text-[11px] mt-0.5" style={{ color: 'var(--muted)' }}>
                  Pairs of rules or terms that contradict each other in draft reviews.
                </p>
              </div>
              <span
                className="font-mono text-xs px-2 py-0.5 rounded-[2px]"
                style={{
                  backgroundColor: 'var(--paper)',
                  color: 'var(--muted)',
                  border: '1px solid var(--hairline)',
                }}
              >
                {conflictingItems.length} conflicts
              </span>
            </div>

            {conflictingItems.length === 0 ? (
              <div className="py-6 text-center text-xs" style={{ color: 'var(--muted)' }}>
                <CheckCircle2 size={20} className="mx-auto mb-1.5" style={{ color: 'var(--status-verified)' }} />
                <span>No contradictory rules detected in active knowledge base.</span>
              </div>
            ) : (
              <div className="space-y-3">
                {conflictingItems.map((c: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-4 rounded-[2px] border text-xs space-y-2"
                    style={{
                      backgroundColor: 'var(--paper)',
                      borderColor: 'var(--hairline)',
                    }}
                  >
                    <div className="flex items-center gap-2 font-mono font-bold" style={{ color: 'var(--severity-major)' }}>
                      <span>{c.rule_a}</span>
                      <span>vs</span>
                      <span>{c.rule_b}</span>
                    </div>
                    <p style={{ color: 'var(--graphite)' }}>{c.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
