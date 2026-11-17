import React, { useState, useEffect } from 'react';
import { BookOpen, Plus, Sparkles, Check, Trash2, Layers, Tag, DollarSign, Bookmark, Image } from 'lucide-react';
import { api } from '../api';
import { RuleItem, FactItem, TermItem, ClaimKBItem } from '../types';

export const KnowledgeBaseScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'rules' | 'facts' | 'terms' | 'claims' | 'import'>('rules');
  const [rules, setRules] = useState<RuleItem[]>([]);
  const [facts, setFacts] = useState<FactItem[]>([]);
  const [terms, setTerms] = useState<TermItem[]>([]);
  const [claims, setClaims] = useState<ClaimKBItem[]>([]);
  const [versions, setVersions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Atomise state
  const [guidelinesText, setGuidelinesText] = useState('');
  const [candidates, setCandidates] = useState<any[]>([]);
  const [importStatus, setImportStatus] = useState<string | null>(null);

  const loadKB = async () => {
    try {
      setLoading(true);
      const [r, f, t, c, v] = await Promise.all([
        api.listRules(),
        api.listFacts(),
        api.listTerms(),
        api.listClaimsKB(),
        api.listVersions(),
      ]);
      setRules(r || []);
      setFacts(f || []);
      setTerms(t || []);
      setClaims(c || []);
      setVersions(v || []);
    } catch (err) {
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
      setLoading(true);
      const res = await api.atomise(guidelinesText);
      setCandidates(res.candidates || []);
    } catch (err: any) {
      alert(err.message || 'Atomisation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmImport = async () => {
    try {
      setLoading(true);
      const res = await api.confirmImport({ rules: candidates });
      setImportStatus(`Successfully imported ${res.saved_rules} atomic rules into active KB!`);
      setCandidates([]);
      setGuidelinesText('');
      await loadKB();
    } catch (err: any) {
      alert(err.message || 'Import failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSnapshot = async () => {
    const label = prompt('Enter version snapshot label (e.g. v1.1.0-release):');
    if (!label) return;
    try {
      await api.createVersion(label);
      await loadKB();
      alert(`Created snapshot ${label}!`);
    } catch (err: any) {
      alert(err.message || 'Version creation failed');
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
            Ground-truth guidelines, approved facts, terminology, claims, and atomic rule repository.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCreateSnapshot}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-md shadow-sm transition-colors flex items-center space-x-1"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Create Version Snapshot</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="flex border-b border-slate-200 px-6 pt-3 space-x-6 overflow-x-auto">
          {[
            { id: 'rules', label: `Rules (${rules.length})`, icon: Bookmark },
            { id: 'facts', label: `Facts (${facts.length})`, icon: DollarSign },
            { id: 'terms', label: `Terminology (${terms.length})`, icon: Tag },
            { id: 'claims', label: `Claims (${claims.length})`, icon: Sparkles },
            { id: 'import', label: 'Import & Atomise Guidelines', icon: Plus },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`pb-3 text-xs font-bold uppercase transition-colors border-b-2 flex items-center space-x-1.5 whitespace-nowrap ${
                  activeTab === tab.id ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
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
              {rules.map((r) => (
                <div key={r.id} className="p-3.5 border rounded-lg bg-slate-50 flex items-start justify-between text-xs">
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-mono font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        {r.code}
                      </span>
                      <span className="uppercase text-[10px] font-bold text-slate-500">{r.category}</span>
                      <span className="text-[10px] font-bold uppercase text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded">
                        {r.severity_default}
                      </span>
                    </div>
                    <div className="text-slate-800 font-medium">{r.text}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* FACTS TAB */}
          {activeTab === 'facts' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              {facts.map((f) => (
                <div key={f.id} className="p-3 border rounded-lg bg-slate-50 space-y-1">
                  <div className="font-mono font-bold text-slate-700">{f.code}: {f.key}</div>
                  <div className="text-sm font-semibold text-emerald-700">
                    {f.value} {f.unit || ''}
                  </div>
                  {f.source && <div className="text-[10px] text-slate-400">Source: {f.source}</div>}
                </div>
              ))}
            </div>
          )}

          {/* TERMS TAB */}
          {activeTab === 'terms' && (
            <div className="space-y-3 text-xs">
              {terms.map((t) => (
                <div key={t.id} className="p-3 border rounded-lg bg-slate-50 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-emerald-800 font-mono">Preferred: {t.preferred}</div>
                    {t.banned && (
                      <div className="text-[11px] text-red-600 font-mono mt-0.5">
                        Banned variants: {Array.isArray(t.banned) ? t.banned.join(', ') : t.banned}
                      </div>
                    )}
                  </div>
                  {t.case_rule && (
                    <span className="text-[10px] font-mono bg-slate-200 px-2 py-0.5 rounded">
                      Case: {t.case_rule}
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
                <div key={c.id} className="p-3.5 border rounded-lg bg-slate-50 space-y-1">
                  <div className="font-bold text-slate-800 font-mono">"{c.approved_text}"</div>
                  {c.required_disclaimer && (
                    <div className="text-amber-800 font-medium text-[11px]">
                      Required Disclaimer: {c.required_disclaimer}
                    </div>
                  )}
                  {c.evidence_ref && <div className="text-[10px] text-slate-400">Evidence Ref: {c.evidence_ref}</div>}
                </div>
              ))}
            </div>
          )}

          {/* IMPORT & ATOMISE TAB */}
          {activeTab === 'import' && (
            <div className="space-y-6">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Paste Raw Brand Guidelines / Document
                </label>
                <textarea
                  rows={6}
                  value={guidelinesText}
                  onChange={(e) => setGuidelinesText(e.target.value)}
                  placeholder="Paste unstructured brand guideline text, bullet points, tone policies, or pricing specs..."
                  className="w-full p-3 text-xs font-mono border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <button
                  onClick={handleAtomise}
                  disabled={loading}
                  className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors flex items-center space-x-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{loading ? 'Atomising...' : 'Atomise Guidelines into Rules'}</span>
                </button>
              </div>

              {importStatus && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-800 font-medium">
                  {importStatus}
                </div>
              )}

              {candidates.length > 0 && (
                <div className="space-y-3 pt-4 border-t border-slate-200">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase text-slate-700">
                      Candidate Atomic Rules ({candidates.length})
                    </span>
                    <button
                      onClick={handleConfirmImport}
                      className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors flex items-center space-x-1"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Confirm Import to Active KB</span>
                    </button>
                  </div>

                  <div className="space-y-2">
                    {candidates.map((c, idx) => (
                      <div key={idx} className="p-3 border rounded-lg bg-blue-50/50 text-xs">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="font-mono font-bold text-blue-700">{c.code}</span>
                          <span className="uppercase text-[10px] font-bold text-slate-500">{c.category}</span>
                          <span className="text-[10px] font-bold uppercase text-amber-700 bg-amber-50 px-1 py-0.5 rounded">
                            {c.severity_default}
                          </span>
                        </div>
                        <div className="text-slate-800">{c.text}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
