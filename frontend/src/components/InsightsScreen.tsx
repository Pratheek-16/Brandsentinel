import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  TrendingUp,
  HelpCircle,
  Lock,
  Layers,
  Sparkles,
  ArrowUpRight,
  GitMerge,
  Clock,
  Cpu,
  RefreshCw,
} from 'lucide-react';
import { api } from '../api';

export const InsightsScreen: React.FC = () => {
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
        `Clarification accepted! Activated new KB version ${res.new_kb_version_id} (${res.new_kb_label}). Guideline ambiguity resolved.`
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
  const aiDisagreements = ambiguityData?.ai_disagreements || [];

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <span>Governance Analytics & Ambiguity Signal Engine (Improvement I-3)</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time compliance analytics across 4 live signals: high creator dismissal rates, active KB conflicts, stale facts, and AI-vs-human disagreement.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="p-2 text-slate-400 hover:text-blue-600 hover:bg-slate-50 rounded-lg transition-colors border border-slate-200"
          title="Refresh analytics"
          aria-label="Refresh insights"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-600' : ''}`} />
        </button>
      </div>

      {successBanner && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-medium flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successBanner}</span>
          </div>
          <button onClick={() => setSuccessBanner(null)} className="text-emerald-700 font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Summary KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Total Submissions
            </span>
            <div className="text-3xl font-extrabold text-slate-900">
              {summary.content_counts?.total || 0}
            </div>
            <div className="text-[11px] text-slate-500">Across all channels</div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Approval Rate
            </span>
            <div className="text-3xl font-extrabold text-emerald-600">
              {summary.content_counts?.total > 0
                ? Math.round(
                    ((summary.content_counts.approved || 0) / summary.content_counts.total) * 100
                  )
                : 100}
              %
            </div>
            <div className="text-[11px] text-emerald-700">
              {summary.content_counts?.approved || 0} approved drafts
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Governance Health
            </span>
            <div className={`text-2xl font-extrabold uppercase ${
              ambiguityData?.health_status === 'healthy' ? 'text-emerald-600' : 'text-amber-600'
            }`}>
              {ambiguityData?.health_status || 'healthy'}
            </div>
            <div className="text-[11px] text-slate-500">
              {ambiguityData?.total_ambiguity_signals || 0} active signals
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              PII Redacted
            </span>
            <div className="text-3xl font-extrabold text-purple-600">
              {summary.total_pii_redacted || 0}
            </div>
            <div className="text-[11px] text-purple-700">Privacy ledger elements</div>
          </div>
        </div>
      )}

      {/* Improvement I-3: 4 Ambiguity Signals Grid */}
      <div className="space-y-6">
        {/* Signal 1: High Creator Dismissals */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <div>
                <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                  Signal 1: Rules with High Creator Dismissal Rates (&gt;40%)
                </h2>
                <p className="text-[11px] text-slate-500">
                  Flags guidelines where creators frequently override automated findings (minimum sample size: 3).
                </p>
              </div>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-amber-50 text-amber-800 border border-amber-200">
              {flaggedRules.length} Flagged
            </span>
          </div>

          <div className="space-y-3">
            {flaggedRules.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto mb-1" />
                <span>No rules exceeding the 40% dismissal threshold.</span>
              </div>
            ) : (
              flaggedRules.map((r: any, idx: number) => {
                const code = r.rule_code;
                const isResolved = resolvedCodes[code];
                return (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border bg-amber-50/60 border-amber-300 text-xs space-y-2.5 shadow-2xs"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold px-2 py-0.5 rounded bg-white border border-slate-300 text-slate-900">
                          {r.rule_code}
                        </span>
                        <span className="text-[11px] font-semibold text-slate-700">
                          {r.dismissed_count} Dismissals of {r.total_surfaced} ({r.dismissal_rate_pct}%)
                        </span>
                      </div>

                      {isResolved ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">
                          Resolved in {isResolved}
                        </span>
                      ) : (
                        <button
                          onClick={() => handleAcceptClarification(r)}
                          disabled={resolvingCode === code}
                          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded text-xs transition-colors flex items-center space-x-1"
                        >
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>{resolvingCode === code ? 'Updating KB...' : 'Accept Clarification'}</span>
                        </button>
                      )}
                    </div>

                    <p className="text-[11px] text-slate-700">
                      <strong>Recommendation:</strong> {r.recommendation}
                    </p>

                    {r.suggested_clarification && (
                      <div className="p-2.5 bg-white rounded border border-amber-200 text-slate-800 font-mono text-[11px]">
                        <strong>Proposed Clarified Wording:</strong> "{r.suggested_clarification}"
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Signal 2: Conflicting Rules & Facts in Active KB */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <GitMerge className="w-5 h-5 text-indigo-500" />
              <div>
                <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                  Signal 2: Conflicting Rules, Terms & Facts in Active Knowledge Base
                </h2>
                <p className="text-[11px] text-slate-500">
                  Detects terms marked both banned and preferred, or facts with overlapping dates and contradictory values.
                </p>
              </div>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-indigo-50 text-indigo-800 border border-indigo-200">
              {conflictingItems.length} Conflicts
            </span>
          </div>

          <div className="space-y-3">
            {conflictingItems.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto mb-1" />
                <span>Active Knowledge Base contains zero contradictory rules or terms.</span>
              </div>
            ) : (
              conflictingItems.map((c: any, idx: number) => {
                const code = c.term || c.key || `conflict-${idx}`;
                const isResolved = resolvedCodes[code];
                return (
                  <div key={idx} className="p-4 rounded-xl border bg-indigo-50/50 border-indigo-200 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold uppercase text-indigo-900">{c.signal_type}</span>
                      {isResolved ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800">
                          Resolved in {isResolved}
                        </span>
                      ) : (
                        <button
                          onClick={() => handleAcceptClarification(c)}
                          disabled={resolvingCode === code}
                          className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded text-xs transition-colors"
                        >
                          {resolvingCode === code ? 'Harmonizing...' : 'Accept Resolution'}
                        </button>
                      )}
                    </div>
                    <p className="text-slate-700">{c.description}</p>
                    {c.suggested_clarification && (
                      <div className="p-2 bg-white rounded border border-indigo-200 font-mono text-[11px] text-slate-800">
                        "{c.suggested_clarification}"
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Signal 3 & 4: Stale Facts & AI Disagreements */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Signal 3: Stale Facts */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <Clock className="w-5 h-5 text-amber-500" />
                <h3 className="text-sm font-bold text-slate-900 uppercase">Signal 3: Stale Facts</h3>
              </div>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                {staleFacts.length}
              </span>
            </div>

            <div className="space-y-2.5">
              {staleFacts.length === 0 ? (
                <div className="p-4 text-center text-xs text-slate-400">All product facts within valid date window.</div>
              ) : (
                staleFacts.map((sf: any, idx: number) => (
                  <div key={idx} className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg text-xs space-y-1">
                    <div className="flex items-center justify-between font-bold text-amber-950 font-mono">
                      <span>{sf.code || sf.key}</span>
                      <span className="text-red-700 text-[10px]">EXPIRED</span>
                    </div>
                    <div className="text-[11px] text-slate-700">{sf.warning}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Signal 4: AI Disagreements */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-purple-500" />
                <h3 className="text-sm font-bold text-slate-900 uppercase">Signal 4: AI vs Human Disagreement</h3>
              </div>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                {aiDisagreements.length}
              </span>
            </div>

            <div className="space-y-2.5">
              {aiDisagreements.length === 0 ? (
                <div className="p-4 text-center text-xs text-slate-400">Zero AI false-positive overrides recorded.</div>
              ) : (
                aiDisagreements.map((ad: any, idx: number) => (
                  <div key={idx} className="p-3 bg-purple-50/70 border border-purple-200 rounded-lg text-xs space-y-1">
                    <div className="font-bold text-purple-950 font-mono text-[11px]">
                      Finding #{ad.finding_id} ({ad.rule_code})
                    </div>
                    <div className="text-[11px] text-slate-700">{ad.description}</div>
                    {ad.human_dismissal_reason && (
                      <div className="text-[10px] text-purple-700 font-mono">
                        Dismissal reason: "{ad.human_dismissal_reason}"
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
