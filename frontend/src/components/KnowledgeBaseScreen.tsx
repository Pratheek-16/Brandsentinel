import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Plus,
  Sparkles,
  Check,
  Trash2,
  Layers,
  Tag,
  DollarSign,
  Bookmark,
  Palette,
  AlertTriangle,
  RefreshCw,
  Clock,
  CheckCircle2,
  Lock,
} from 'lucide-react';
import { api } from '../api';
import { RuleItem, FactItem, TermItem, ClaimKBItem, AssetItem, KBVersionItem } from '../types';

export const KnowledgeBaseScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'rules' | 'facts' | 'terms' | 'claims' | 'assets' | 'versions' | 'import'>('rules');
  const [rules, setRules] = useState<RuleItem[]>([]);
  const [facts, setFacts] = useState<FactItem[]>([]);
  const [terms, setTerms] = useState<TermItem[]>([]);
  const [claims, setClaims] = useState<ClaimKBItem[]>([]);
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [versions, setVersions] = useState<KBVersionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Atomise state
  const [guidelinesText, setGuidelinesText] = useState('');
  const [candidates, setCandidates] = useState<any[]>([]);
  const [atomising, setAtomising] = useState(false);

  // New Entity Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [newRuleCode, setNewRuleCode] = useState('');
  const [newRuleCategory, setNewRuleCategory] = useState('tone');
  const [newRuleSeverity, setNewRuleSeverity] = useState('major');
  const [newRuleText, setNewRuleText] = useState('');

  const loadKB = async () => {
    try {
      setLoading(true);
      const [r, f, t, c, a, v] = await Promise.all([
        api.listRules().catch(() => []),
        api.listFacts().catch(() => []),
        api.listTerms().catch(() => []),
        api.listClaimsKB().catch(() => []),
        api.listAssets().catch(() => []),
        api.listVersions().catch(() => []),
      ]);
      setRules(r || []);
      setFacts(f || []);
      setTerms(t || []);
      setClaims(c || []);
      setAssets(a || []);
      setVersions(v || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKB();
  }, []);

  const handleAtomise = async () => {
    if (!guidelinesText.trim()) return;
    try {
      setAtomising(true);
      setActionMsg(null);
      const res = await api.atomise(guidelinesText);
      setCandidates(res.candidates || []);
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Atomisation failed' });
    } finally {
      setAtomising(false);
    }
  };

  const handleConfirmImport = async () => {
    try {
      setLoading(true);
      const res = await api.confirmImport({ rules: candidates });
      setActionMsg({
        type: 'success',
        text: `Successfully imported ${res.saved_rules} atomic rules into active KB!`,
      });
      setCandidates([]);
      setGuidelinesText('');
      await loadKB();
      setActiveTab('rules');
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Import failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSnapshot = async () => {
    const label = prompt('Enter version snapshot label (e.g. v1.1.0-release):');
    if (!label) return;
    try {
      setLoading(true);
      await api.createVersion(label);
      setActionMsg({ type: 'success', text: `Created snapshot "${label}" with cloned entities!` });
      await loadKB();
      setActiveTab('versions');
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Snapshot creation failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleActivateVersion = async (verId: number) => {
    try {
      setLoading(true);
      await api.activateVersion(verId);
      setActionMsg({ type: 'success', text: `Activated KB Version #${verId}!` });
      await loadKB();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Version activation failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRule = async (id: number) => {
    if (!confirm(`Are you sure you want to delete rule #${id}?`)) return;
    try {
      await api.deleteRule(id);
      setRules((prev) => prev.filter((r) => r.id !== id));
      setActionMsg({ type: 'success', text: `Deleted rule #${id}` });
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Failed to delete rule' });
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRuleCode.trim() || !newRuleText.trim()) return;
    try {
      setLoading(true);
      await api.createRule({
        code: newRuleCode.trim().toUpperCase(),
        category: newRuleCategory,
        severity_default: newRuleSeverity,
        text: newRuleText.trim(),
      });
      setShowAddModal(false);
      setNewRuleCode('');
      setNewRuleText('');
      setActionMsg({ type: 'success', text: 'Created new brand guideline rule!' });
      await loadKB();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Failed to create rule' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
            <BookOpen className="w-5 h-5 text-blue-600" />
            <span>Brand Knowledge Base & Governance Rules</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Ground-truth guidelines, approved facts, terminology, claims, palette assets, and version snapshots.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center space-x-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Rule</span>
          </button>

          <button
            onClick={handleCreateSnapshot}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center space-x-1.5"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Create Version Snapshot</span>
          </button>
        </div>
      </div>

      {actionMsg && (
        <div
          className={`p-4 rounded-xl border flex items-center space-x-2 text-xs font-semibold ${
            actionMsg.type === 'success'
              ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
              : 'bg-red-50 text-red-900 border-red-200'
          }`}
        >
          {actionMsg.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
          )}
          <span>{actionMsg.text}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="flex border-b border-slate-200 px-6 pt-3 space-x-6 overflow-x-auto">
          {[
            { id: 'rules', label: `Rules (${rules.length})`, icon: Bookmark },
            { id: 'facts', label: `Facts (${facts.length})`, icon: DollarSign },
            { id: 'terms', label: `Terminology (${terms.length})`, icon: Tag },
            { id: 'claims', label: `Claims (${claims.length})`, icon: Sparkles },
            { id: 'assets', label: `Palette & Assets (${assets.length})`, icon: Palette },
            { id: 'versions', label: `Versions (${versions.length})`, icon: Layers },
            { id: 'import', label: 'Import & Atomise Guidelines', icon: Plus },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`pb-3 text-xs font-bold uppercase transition-colors border-b-2 flex items-center space-x-1.5 whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="p-6">
          {/* RULES TAB */}
          {activeTab === 'rules' && (
            <div className="space-y-3">
              {rules.length === 0 ? (
                <div className="text-center py-10 text-xs text-slate-400">
                  No active rules in this KB version. Use "Add Rule" or "Import & Atomise" to seed rules.
                </div>
              ) : (
                rules.map((r) => (
                  <div
                    key={r.id}
                    className="p-4 border rounded-xl bg-slate-50/70 hover:bg-slate-50 transition-colors flex items-start justify-between text-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                          {r.code}
                        </span>
                        <span className="uppercase text-[10px] font-bold text-slate-500">
                          {r.category}
                        </span>
                        <span
                          className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${
                            r.severity_default === 'blocker'
                              ? 'bg-red-100 text-red-800'
                              : r.severity_default === 'major'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {r.severity_default}
                        </span>
                      </div>
                      <div className="text-slate-800 font-medium leading-relaxed">{r.text}</div>
                    </div>

                    <button
                      onClick={() => handleDeleteRule(r.id)}
                      title="Delete rule"
                      className="p-1.5 text-slate-400 hover:text-red-500 transition-colors shrink-0"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          )}

          {/* FACTS TAB */}
          {activeTab === 'facts' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              {facts.map((f) => (
                <div key={f.id} className="p-4 border rounded-xl bg-slate-50/70 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-slate-800">{f.code}: {f.key}</span>
                    {f.is_stale && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-100 text-amber-900 border border-amber-300 flex items-center space-x-1">
                        <AlertTriangle className="w-3 h-3 text-amber-600" />
                        <span>Stale Fact</span>
                      </span>
                    )}
                  </div>
                  <div className="text-base font-bold text-emerald-700 font-mono">
                    {f.value} {f.unit || ''}
                  </div>
                  {f.source && <div className="text-[11px] text-slate-500">Source: {f.source}</div>}
                  {f.valid_to && <div className="text-[10px] text-slate-400">Valid to: {f.valid_to}</div>}
                </div>
              ))}
            </div>
          )}

          {/* TERMS TAB */}
          {activeTab === 'terms' && (
            <div className="space-y-3 text-xs">
              {terms.map((t) => (
                <div key={t.id} className="p-4 border rounded-xl bg-slate-50/70 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-emerald-800 font-mono text-sm">
                      Preferred: "{t.preferred}"
                    </div>
                    {t.banned && (
                      <div className="text-xs text-red-600 font-mono mt-1">
                        Banned variations: {Array.isArray(t.banned) ? t.banned.join(', ') : t.banned}
                      </div>
                    )}
                  </div>
                  {t.case_rule && (
                    <span className="text-[11px] font-mono bg-slate-200 px-2 py-0.5 rounded text-slate-700">
                      Rule: {t.case_rule}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* CLAIMS TAB */}
          {activeTab === 'claims' && (
            <div className="space-y-3 text-xs">
              {claims.map((c) => (
                <div key={c.id} className="p-4 border rounded-xl bg-slate-50/70 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 font-mono text-sm">
                      "{c.approved_text}"
                    </span>
                    {c.is_expired && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-red-100 text-red-800">
                        Expired Claim
                      </span>
                    )}
                  </div>
                  {c.required_disclaimer && (
                    <div className="text-amber-900 bg-amber-50 p-2 rounded border border-amber-200 text-xs font-medium">
                      Mandatory Disclaimer: {c.required_disclaimer}
                    </div>
                  )}
                  {c.evidence_ref && (
                    <div className="text-[11px] text-slate-400">Reference: {c.evidence_ref}</div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* ASSETS / PALETTE TAB */}
          {activeTab === 'assets' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {assets.map((a) => (
                  <div key={a.id} className="p-4 border rounded-xl bg-white shadow-2xs space-y-2">
                    <div className="flex items-center space-x-3">
                      {a.asset_type === 'palette_color' ? (
                        <div
                          className="w-10 h-10 rounded-lg border shadow-inner shrink-0"
                          style={{ backgroundColor: a.value }}
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center font-bold text-slate-500 text-xs">
                          ASSET
                        </div>
                      )}
                      <div className="truncate">
                        <div className="font-bold text-slate-800 text-xs">{a.name}</div>
                        <div className="font-mono text-xs font-semibold text-slate-600">{a.value}</div>
                      </div>
                    </div>
                    {a.description && (
                      <p className="text-[11px] text-slate-500">{a.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* VERSIONS TAB */}
          {activeTab === 'versions' && (
            <div className="space-y-3">
              {versions.map((v) => (
                <div
                  key={v.id}
                  className={`p-4 border rounded-xl flex items-center justify-between text-xs ${
                    v.active ? 'bg-blue-50/70 border-blue-300' : 'bg-slate-50 border-slate-200'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-sm text-slate-900">{v.label}</span>
                      {v.active && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-600 text-white">
                          Active Version
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      Created: {new Date(v.created_at).toLocaleString()} • ID #{v.id}
                    </div>
                  </div>

                  {!v.active && (
                    <button
                      onClick={() => handleActivateVersion(v.id)}
                      className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors"
                    >
                      Activate Version
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* IMPORT & ATOMISE TAB */}
          {activeTab === 'import' && (
            <div className="space-y-6">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-700 mb-1.5">
                  Paste Unstructured Brand Guidelines
                </label>
                <textarea
                  rows={6}
                  value={guidelinesText}
                  onChange={(e) => setGuidelinesText(e.target.value)}
                  placeholder="Paste unstructured brand guideline text, bullet points, tone policies, or pricing specs..."
                  className="w-full p-3.5 text-xs font-mono border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-slate-50/50"
                />
                <button
                  onClick={handleAtomise}
                  disabled={atomising}
                  className="mt-2.5 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center space-x-1.5 disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{atomising ? 'Atomising with AI...' : 'Atomise Guidelines into Rules'}</span>
                </button>
              </div>

              {candidates.length > 0 && (
                <div className="space-y-3 pt-4 border-t border-slate-200">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase text-slate-700">
                      Candidate Atomic Rules ({candidates.length})
                    </span>
                    <button
                      onClick={handleConfirmImport}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center space-x-1"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Confirm & Import into Active KB</span>
                    </button>
                  </div>

                  <div className="space-y-2">
                    {candidates.map((c, idx) => (
                      <div key={idx} className="p-3.5 border rounded-xl bg-blue-50/50 text-xs space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono font-bold text-blue-700">{c.code}</span>
                          <span className="uppercase text-[10px] font-bold text-slate-500">
                            {c.category}
                          </span>
                          <span className="text-[10px] font-bold uppercase text-amber-700 bg-amber-50 px-1 py-0.5 rounded">
                            {c.severity_default}
                          </span>
                        </div>
                        <div className="text-slate-800 leading-relaxed">{c.text}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Add Rule Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleCreateRule}
            className="bg-white max-w-md w-full p-6 rounded-2xl shadow-2xl space-y-4"
          >
            <h3 className="text-base font-bold text-slate-900">Add Brand Rule</h3>

            <div>
              <label className="block text-xs font-bold uppercase text-slate-700 mb-1">
                Rule Code (e.g. NF-TONE-003)
              </label>
              <input
                type="text"
                required
                value={newRuleCode}
                onChange={(e) => setNewRuleCode(e.target.value)}
                placeholder="NF-TONE-003"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none font-mono"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-700 mb-1">
                  Category
                </label>
                <select
                  value={newRuleCategory}
                  onChange={(e) => setNewRuleCategory(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
                >
                  <option value="tone">Tone</option>
                  <option value="terminology">Terminology</option>
                  <option value="claim">Claim</option>
                  <option value="visual">Visual</option>
                  <option value="accessibility">Accessibility</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-slate-700 mb-1">
                  Default Severity
                </label>
                <select
                  value={newRuleSeverity}
                  onChange={(e) => setNewRuleSeverity(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
                >
                  <option value="blocker">Blocker</option>
                  <option value="major">Major</option>
                  <option value="minor">Minor</option>
                  <option value="info">Info</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase text-slate-700 mb-1">
                Rule Statement / Policy
              </label>
              <textarea
                rows={3}
                required
                value={newRuleText}
                onChange={(e) => setNewRuleText(e.target.value)}
                placeholder="State the guideline clearly..."
                className="w-full p-2.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="px-3.5 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm"
              >
                Create Rule
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
