import React, { useState, useEffect } from 'react';
import { BarChart3, AlertTriangle, ShieldCheck, CheckCircle2, TrendingUp, HelpCircle } from 'lucide-react';
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
        api.getInsightsSummary(),
        api.getAmbiguity(),
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
          <span>Governance Insights & Improvement I-3: Ambiguity Detector</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Aggregates compliance trends, privacy redaction ledger metrics, and automatically detects ambiguous rules with high human dismissal rates (&gt;40%).
        </p>
      </div>

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs font-semibold text-slate-500 uppercase">Total Submissions</span>
            <div className="text-2xl font-bold text-slate-900 mt-1">{summary.content_counts.total}</div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs font-semibold text-slate-500 uppercase">Approved Rate</span>
            <div className="text-2xl font-bold text-emerald-600 mt-1">
              {summary.content_counts.total > 0
                ? Math.round((summary.content_counts.approved / summary.content_counts.total) * 100)
                : 100}
              %
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs font-semibold text-slate-500 uppercase">Under Review</span>
            <div className="text-2xl font-bold text-blue-600 mt-1">{summary.content_counts.in_review}</div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs font-semibold text-slate-500 uppercase">PII Elements Redacted</span>
            <div className="text-2xl font-bold text-purple-600 mt-1">{summary.total_pii_redacted}</div>
          </div>
        </div>
      )}

      {/* Breakdown Grid */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Findings by Category</h2>
            <div className="space-y-2">
              {Object.entries(summary.findings_by_category || {}).length === 0 ? (
                <div className="text-xs text-slate-400 py-4">No findings recorded.</div>
              ) : (
                Object.entries(summary.findings_by_category).map(([cat, count]: [string, any]) => (
                  <div key={cat} className="flex items-center justify-between text-xs py-1 border-b border-slate-100">
                    <span className="capitalize font-medium text-slate-700">{cat}</span>
                    <span className="font-mono font-bold bg-slate-100 px-2 py-0.5 rounded text-slate-800">{count}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Findings by Severity</h2>
            <div className="space-y-2">
              {Object.entries(summary.findings_by_severity || {}).length === 0 ? (
                <div className="text-xs text-slate-400 py-4">No findings recorded.</div>
              ) : (
                Object.entries(summary.findings_by_severity).map(([sev, count]: [string, any]) => (
                  <div key={sev} className="flex items-center justify-between text-xs py-1 border-b border-slate-100">
                    <span className="capitalize font-medium text-slate-700">{sev}</span>
                    <span className="font-mono font-bold bg-slate-100 px-2 py-0.5 rounded text-slate-800">{count}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Improvement I-3: Ambiguity Detector */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
            Ambiguity Detector: High-Dismissal Brand Rules
          </h2>
        </div>

        <div className="space-y-3">
          {ambiguity.map((rule, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-lg border text-xs space-y-2 ${
                rule.status === 'flagged_ambiguous'
                  ? 'bg-amber-50/70 border-amber-300 text-amber-950'
                  : 'bg-slate-50 border-slate-200 text-slate-800'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="font-mono font-bold px-2 py-0.5 rounded bg-white border border-slate-300">
                    {rule.rule_code}
                  </span>
                  <span className="text-[11px] font-semibold text-slate-600">
                    {rule.dismissals_count} Human Dismissals ({rule.dismissal_rate_pct}% dismissal rate)
                  </span>
                </div>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    rule.status === 'flagged_ambiguous' ? 'bg-amber-200 text-amber-900' : 'bg-emerald-100 text-emerald-800'
                  }`}
                >
                  {rule.status === 'flagged_ambiguous' ? 'Requires Revision' : 'Healthy'}
                </span>
              </div>

              <div className="text-[11px] font-medium leading-relaxed">
                <span className="font-bold">Guardian Action Recommendation:</span> {rule.recommendation}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
