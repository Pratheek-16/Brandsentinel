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
} from 'lucide-react';
import { api } from '../api';
import { AmbiguityRule } from '../types';

export const InsightsScreen: React.FC = () => {
  const [summary, setSummary] = useState<any>(null);
  const [ambiguity, setAmbiguity] = useState<AmbiguityRule[]>([]);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sum, amb] = await Promise.all([
        api.getInsightsSummary().catch(() => null),
        api.getAmbiguity().catch(() => ({ flagged_rules: [] })),
      ]);
      setSummary(sum);
      setAmbiguity(amb?.flagged_rules || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h1 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-blue-600" />
          <span>Governance Analytics & Ambiguity Detector (Improvement I-3)</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Real-time compliance analytics, privacy ledger metrics, and automated detection of ambiguous brand guidelines with high human dismissal rates (&gt;40%).
        </p>
      </div>

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
              Under Review
            </span>
            <div className="text-3xl font-extrabold text-blue-600">
              {summary.content_counts?.in_review || 0}
            </div>
            <div className="text-[11px] text-blue-700">Awaiting sign-off</div>
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

      {/* Breakdown Grid */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center justify-between">
              <span>Findings by Category</span>
              <span className="text-slate-400 font-normal">Deterministic & LLM</span>
            </h2>
            <div className="space-y-2.5">
              {Object.entries(summary.findings_by_category || {}).length === 0 ? (
                <div className="text-xs text-slate-400 py-6 text-center">No findings recorded.</div>
              ) : (
                Object.entries(summary.findings_by_category).map(([cat, count]: [string, any]) => (
                  <div key={cat} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-100">
                    <span className="capitalize font-semibold text-slate-700">{cat}</span>
                    <span className="font-mono font-bold bg-slate-100 px-2.5 py-0.5 rounded text-slate-800">
                      {count}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center justify-between">
              <span>Findings by Severity</span>
              <span className="text-slate-400 font-normal">Escalation Triggers</span>
            </h2>
            <div className="space-y-2.5">
              {Object.entries(summary.findings_by_severity || {}).length === 0 ? (
                <div className="text-xs text-slate-400 py-6 text-center">No findings recorded.</div>
              ) : (
                Object.entries(summary.findings_by_severity).map(([sev, count]: [string, any]) => (
                  <div key={sev} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-100">
                    <div className="flex items-center space-x-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          sev === 'blocker'
                            ? 'bg-red-500'
                            : sev === 'major'
                            ? 'bg-amber-500'
                            : 'bg-yellow-400'
                        }`}
                      />
                      <span className="capitalize font-semibold text-slate-700">{sev}</span>
                    </div>
                    <span className="font-mono font-bold bg-slate-100 px-2.5 py-0.5 rounded text-slate-800">
                      {count}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Improvement I-3: Ambiguity Detector */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <div>
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                Improvement I-3: Rule Ambiguity Signal Engine
              </h2>
              <p className="text-[11px] text-slate-500">
                Identifies guidelines where creators and reviewers frequently dismiss findings (&gt;40% dismissal rate).
              </p>
            </div>
          </div>

          <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-amber-50 text-amber-800 border border-amber-200">
            {ambiguity.length} Rules Flagged
          </span>
        </div>

        <div className="space-y-3">
          {ambiguity.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400 space-y-1">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-1" />
              <div className="font-semibold text-slate-700">All Brand Rules Healthy</div>
              <div>No guideline exhibits anomalous human dismissal rates.</div>
            </div>
          ) : (
            ambiguity.map((rule, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-xl border text-xs space-y-2.5 transition-all ${
                  rule.status === 'flagged_ambiguous'
                    ? 'bg-amber-50/70 border-amber-300 text-amber-950 shadow-2xs'
                    : 'bg-slate-50 border-slate-200 text-slate-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold px-2 py-0.5 rounded bg-white border border-slate-300 text-slate-900">
                      {rule.rule_code}
                    </span>
                    <span className="text-[11px] font-semibold text-slate-700">
                      {rule.dismissals_count} Human Dismissals ({rule.dismissal_rate_pct}% dismissal rate)
                    </span>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono ${
                      rule.status === 'flagged_ambiguous'
                        ? 'bg-amber-200 text-amber-950 border border-amber-300'
                        : 'bg-emerald-100 text-emerald-800'
                    }`}
                  >
                    {rule.status === 'flagged_ambiguous' ? 'Flagged Ambiguous' : 'Healthy'}
                  </span>
                </div>

                <div className="text-[11px] leading-relaxed flex items-start space-x-1.5">
                  <ArrowUpRight className="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5" />
                  <span>
                    <strong>Brand Guardian Recommendation:</strong> {rule.recommendation}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
