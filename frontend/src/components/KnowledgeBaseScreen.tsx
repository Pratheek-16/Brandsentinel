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
  Search,
  ChevronRight,
  Upload,
  Calendar,
  X,
  SlidersHorizontal,
  ArrowRight,
} from 'lucide-react';
import { api } from '../api';
import { RuleItem, FactItem, TermItem, ClaimKBItem, AssetItem, KBVersionItem } from '../types';

export const KnowledgeBaseScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'rules' | 'terms' | 'facts' | 'claims' | 'assets' | 'versions' | 'import'>('rules');
  const [rules, setRules] = useState<RuleItem[]>([]);
  const [facts, setFacts] = useState<FactItem[]>([]);
  const [terms, setTerms] = useState<TermItem[]>([]);
  const [claims, setClaims] = useState<ClaimKBItem[]>([]);
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [versions, setVersions] = useState<KBVersionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Search & Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEntity, setSelectedEntity] = useState<any | null>(null);

  // Live preview box state
  const [previewSentence, setPreviewSentence] = useState('PulseBand is the best wearable in the world with 14 days battery.');
  const [triggeredMatches, setTriggeredMatches] = useState<Array<{ name: string; type: string; reason: string }>>([]);

  // Atomise state & 3-step import stepper
  const [importStep, setImportStep] = useState<1 | 2 | 3>(1);
  const [guidelinesText, setGuidelinesText] = useState('');
  const [candidates, setCandidates] = useState<any[]>([]);
  const [atomising, setAtomising] = useState(false);

  // Add rule modal
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

  // Live preview trigger calculation
  useEffect(() => {
    if (!previewSentence.trim()) {
      setTriggeredMatches([]);
      return;
    }
    const lower = previewSentence.toLowerCase();
    const matches: Array<{ name: string; type: string; reason: string }> = [];

    // Check terms
    terms.forEach((t) => {
      const bannedList = Array.isArray(t.banned) ? t.banned : t.banned ? [t.banned] : [];
      bannedList.forEach((b) => {
        if (b && lower.includes(b.toLowerCase())) {
          matches.push({
            name: b,
            type: 'Prohibited term',
            reason: `Use preferred term "${t.preferred || 'approved alternative'}"`,
          });
        }
      });
    });

    // Check superlative / claim rules
    rules.forEach((r) => {
      if (lower.includes('best') && (r.code.includes('SUPER') || r.category === 'claims')) {
        matches.push({
          name: r.code,
          type: 'Rule match',
          reason: r.text,
        });
      }
      if (lower.includes('battery') && r.text.toLowerCase().includes('battery')) {
        matches.push({
          name: r.code,
          type: 'Specification check',
          reason: r.text,
        });
      }
    });

    // Check facts
    facts.forEach((fc) => {
      if (lower.includes('battery') && (fc.key || '').toLowerCase().includes('battery')) {
        matches.push({
          name: fc.key,
          type: 'Ground fact',
          reason: `Verified value: ${fc.value}`,
        });
      }
    });

    setTriggeredMatches(matches);
  }, [previewSentence, rules, terms, facts]);

  const handleAtomise = async () => {
    if (!guidelinesText.trim()) return;
    try {
      setAtomising(true);
      setActionMsg(null);
      const res = await api.atomise(guidelinesText);
      setCandidates(res.candidates || []);
      setImportStep(2);
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Extraction failed' });
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
        text: `Successfully imported ${res.saved_rules} atomic rules into the active knowledge base.`,
      });
      setImportStep(3);
      await loadKB();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Import failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSnapshot = async () => {
    const label = prompt('Enter version snapshot tag (e.g. v1.2.0-approved):');
    if (!label) return;
    try {
      setLoading(true);
      await api.createVersion(label);
      setActionMsg({ type: 'success', text: `Created snapshot "${label}".` });
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
      setActionMsg({ type: 'success', text: `Activated KB Version #${verId}.` });
      await loadKB();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Version activation failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRule = async (id: number) => {
    if (!confirm(`Are you sure you want to remove rule #${id}?`)) return;
    try {
      await api.deleteRule(id);
      setRules((prev) => prev.filter((r) => r.id !== id));
      setActionMsg({ type: 'success', text: `Removed rule #${id}.` });
      if (selectedEntity?.id === id) setSelectedEntity(null);
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Failed to remove rule' });
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
      setActionMsg({ type: 'success', text: 'Brand guideline rule saved.' });
      await loadKB();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.message || 'Failed to create rule' });
    } finally {
      setLoading(false);
    }
  };

  const filteredRules = rules.filter(
    (r) =>
      r.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Top Banner */}
      <div
        className="p-6 rounded-[2px] border flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{
          backgroundColor: 'var(--sheet)',
          borderColor: 'var(--hairline)',
        }}
      >
        <div>
          <h1 className="text-2xl font-serif font-semibold tracking-tight" style={{ color: 'var(--ink)' }}>
            Brand rules &amp; knowledge base
          </h1>
          <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
            Ground-truth guidelines, verified facts, approved terminology, promotional claims, and immutable snapshots.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-2 rounded-[2px] text-xs font-medium text-white transition-all shadow-xs flex items-center gap-1.5"
            style={{ backgroundColor: 'var(--accent)' }}
          >
            <Plus size={14} />
            <span>Add rule</span>
          </button>

          <button
            onClick={handleCreateSnapshot}
            className="px-3.5 py-2 rounded-[2px] border text-xs font-medium transition-colors hover:bg-black/5 dark:hover:bg-white/5 flex items-center gap-1.5"
            style={{
              borderColor: 'var(--hairline)',
              color: 'var(--graphite)',
            }}
          >
            <Layers size={14} />
            <span>Create version snapshot</span>
          </button>
        </div>
      </div>

      {actionMsg && (
        <div
          className="p-3.5 rounded-[2px] border flex items-center gap-2 text-xs"
          style={{
            backgroundColor:
              actionMsg.type === 'success'
                ? 'var(--status-verified-bg)'
                : 'var(--severity-blocker-bg)',
            borderColor:
              actionMsg.type === 'success'
                ? 'var(--status-verified)'
                : 'var(--severity-blocker)',
            color:
              actionMsg.type === 'success'
                ? 'var(--status-verified)'
                : 'var(--severity-blocker)',
          }}
        >
          {actionMsg.type === 'success' ? (
            <CheckCircle2 size={15} />
          ) : (
            <AlertTriangle size={15} />
          )}
          <span>{actionMsg.text}</span>
        </div>
      )}

      {/* Live Preview Box: Test sentences against KB in real time */}
      <div
        className="p-5 rounded-[2px] border space-y-3"
        style={{
          backgroundColor: 'var(--sheet)',
          borderColor: 'var(--accent)',
          boxShadow: '0 2px 12px -2px rgba(14, 124, 123, 0.06)',
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles size={16} style={{ color: 'var(--accent)' }} />
            <h3 className="font-serif font-semibold text-sm" style={{ color: 'var(--ink)' }}>
              Live rule test box
            </h3>
          </div>
          <span className="text-[11px] font-mono" style={{ color: 'var(--muted)' }}>
            Instant matcher
          </span>
        </div>

        <p className="text-xs" style={{ color: 'var(--graphite)' }}>
          Type or edit a sentence to see which brand rules, terms, or facts it triggers immediately:
        </p>

        <div className="flex gap-2">
          <input
            type="text"
            value={previewSentence}
            onChange={(e) => setPreviewSentence(e.target.value)}
            placeholder="Type sample marketing copy to evaluate..."
            className="flex-1 px-3 py-2 text-sm rounded-[2px] border focus:outline-none"
            style={{
              backgroundColor: 'var(--paper)',
              borderColor: 'var(--hairline)',
              color: 'var(--ink)',
            }}
          />
        </div>

        {/* Triggered live matches */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          {triggeredMatches.length === 0 ? (
            <span className="text-xs italic" style={{ color: 'var(--muted)' }}>
              No rules triggered by this sentence.
            </span>
          ) : (
            triggeredMatches.map((m, idx) => (
              <div
                key={idx}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-[2px] border text-xs"
                style={{
                  backgroundColor: 'var(--accent-surface)',
                  borderColor: 'var(--hairline)',
                }}
              >
                <span className="font-mono font-semibold" style={{ color: 'var(--accent-ink)' }}>
                  {m.name}
                </span>
                <span style={{ color: 'var(--muted)' }}>•</span>
                <span style={{ color: 'var(--graphite)' }}>{m.reason}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Segmented Navigation Inside the Page */}
      <div
        className="rounded-[2px] border overflow-hidden"
        style={{
          backgroundColor: 'var(--sheet)',
          borderColor: 'var(--hairline)',
        }}
      >
        <div
          className="flex border-b px-6 pt-3 gap-6 overflow-x-auto"
          style={{ borderColor: 'var(--hairline)' }}
        >
          {[
            { id: 'rules', label: `Rules (${rules.length})`, icon: Bookmark },
            { id: 'terms', label: `Terms (${terms.length})`, icon: Tag },
            { id: 'facts', label: `Facts (${facts.length})`, icon: DollarSign },
            { id: 'claims', label: `Claims (${claims.length})`, icon: Sparkles },
            { id: 'assets', label: `Assets (${assets.length})`, icon: Palette },
            { id: 'versions', label: `Versions (${versions.length})`, icon: Layers },
            { id: 'import', label: 'Import guidelines', icon: Upload },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id as any);
                  setSelectedEntity(null);
                }}
                className="pb-3 text-xs font-medium transition-colors border-b-2 flex items-center gap-1.5 whitespace-nowrap"
                style={{
                  borderBottomColor: isActive ? 'var(--accent)' : 'transparent',
                  color: isActive ? 'var(--accent-ink)' : 'var(--muted)',
                  fontWeight: isActive ? 600 : 500,
                }}
              >
                <Icon size={14} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="p-6">
          {/* Search bar inside lists */}
          {activeTab !== 'import' && (
            <div className="flex items-center gap-3 mb-6">
              <div
                className="flex items-center gap-2 flex-1 px-3 py-1.5 rounded-[2px] border text-xs"
                style={{
                  backgroundColor: 'var(--paper)',
                  borderColor: 'var(--hairline)',
                }}
              >
                <Search size={14} style={{ color: 'var(--muted)' }} />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={`Search ${activeTab}...`}
                  className="w-full bg-transparent border-none focus:outline-none"
                  style={{ color: 'var(--ink)' }}
                />
              </div>
            </div>
          )}

          {/* RULES LEDGER & SIDE PANEL */}
          {activeTab === 'rules' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              <div className="lg:col-span-8 space-y-2">
                <div className="divide-y border rounded-[2px]" style={{ borderColor: 'var(--hairline)' }}>
                  {filteredRules.length === 0 ? (
                    <div className="py-12 text-center text-xs" style={{ color: 'var(--muted)' }}>
                      No rules matched your search query.
                    </div>
                  ) : (
                    filteredRules.map((r) => {
                      const isSelected = selectedEntity?.id === r.id;
                      return (
                        <div
                          key={r.id}
                          onClick={() => setSelectedEntity(r)}
                          className="p-3.5 hover:bg-black/3 dark:hover:bg-white/3 transition-colors cursor-pointer flex items-start justify-between gap-4"
                          style={{
                            backgroundColor: isSelected ? 'var(--accent-surface)' : 'transparent',
                          }}
                        >
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span
                                className="font-mono text-xs font-semibold px-1.5 py-0.5 rounded-[2px]"
                                style={{
                                  backgroundColor: 'var(--paper)',
                                  color: 'var(--accent-ink)',
                                  border: '1px solid var(--hairline)',
                                }}
                              >
                                {r.code}
                              </span>
                              <span className="text-xs font-medium capitalize" style={{ color: 'var(--graphite)' }}>
                                {r.category}
                              </span>
                            </div>
                            <p className="text-xs leading-relaxed" style={{ color: 'var(--ink)' }}>
                              {r.text}
                            </p>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <span
                              className="text-[10px] font-mono px-1.5 py-0.2 rounded capitalize"
                              style={{
                                backgroundColor:
                                  r.severity_default === 'blocker'
                                    ? 'var(--severity-blocker-bg)'
                                    : 'var(--severity-major-bg)',
                                color:
                                  r.severity_default === 'blocker'
                                    ? 'var(--severity-blocker)'
                                    : 'var(--severity-major)',
                              }}
                            >
                              {r.severity_default}
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteRule(r.id);
                              }}
                              className="p-1 hover:text-red-700"
                              title="Delete rule"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Side Panel for Details */}
              <div
                className="lg:col-span-4 p-5 rounded-[2px] border space-y-3"
                style={{
                  backgroundColor: 'var(--paper)',
                  borderColor: 'var(--hairline)',
                }}
              >
                <h4 className="font-serif font-semibold text-sm" style={{ color: 'var(--ink)' }}>
                  Rule details
                </h4>
                {selectedEntity ? (
                  <div className="space-y-3 text-xs">
                    <div>
                      <span className="block text-[11px]" style={{ color: 'var(--muted)' }}>Code</span>
                      <span className="font-mono font-bold" style={{ color: 'var(--ink)' }}>{selectedEntity.code}</span>
                    </div>
                    <div>
                      <span className="block text-[11px]" style={{ color: 'var(--muted)' }}>Category</span>
                      <span className="capitalize" style={{ color: 'var(--ink)' }}>{selectedEntity.category}</span>
                    </div>
                    <div>
                      <span className="block text-[11px]" style={{ color: 'var(--muted)' }}>Rule text</span>
                      <p className="font-serif italic text-xs leading-relaxed" style={{ color: 'var(--graphite)' }}>
                        "{selectedEntity.text}"
                      </p>
                    </div>
                    <div>
                      <span className="block text-[11px]" style={{ color: 'var(--muted)' }}>Severity</span>
                      <span className="font-mono capitalize" style={{ color: 'var(--ink)' }}>{selectedEntity.severity_default}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs italic" style={{ color: 'var(--muted)' }}>
                    Select any rule from the ledger to view full metadata and citations.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* TERMS TAB */}
          {activeTab === 'terms' && (
            <div className="divide-y border rounded-[2px]" style={{ borderColor: 'var(--hairline)' }}>
              {terms.map((t) => {
                const bannedStr = Array.isArray(t.banned) ? t.banned.join(', ') : (t.banned || 'None');
                return (
                  <div key={t.id} className="p-3.5 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-medium mr-2" style={{ color: 'var(--severity-blocker)' }}>
                        Prohibited: "{bannedStr}"
                      </span>
                      <span style={{ color: 'var(--status-verified)' }}>
                        → Preferred: "{t.preferred}"
                      </span>
                    </div>
                    <span className="font-mono text-[10px]" style={{ color: 'var(--muted)' }}>
                      {t.notes || 'Terminology standard'}
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {/* FACTS TAB (WITH VALIDITY BARS & EXPIRATION CHIPS) */}
          {activeTab === 'facts' && (
            <div className="space-y-3">
              {facts.map((fc) => (
                <div
                  key={fc.id}
                  className="p-4 rounded-[2px] border space-y-2 text-xs"
                  style={{
                    backgroundColor: 'var(--paper)',
                    borderColor: 'var(--hairline)',
                  }}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold" style={{ color: 'var(--ink)' }}>
                      {fc.code || fc.key}
                    </span>
                    <span
                      className="px-2 py-0.5 rounded-[2px] font-mono text-[10px]"
                      style={{
                        backgroundColor: 'var(--status-verified-bg)',
                        color: 'var(--status-verified)',
                        border: '1px solid var(--status-verified)',
                      }}
                    >
                      Active fact
                    </span>
                  </div>

                  <div className="text-sm font-semibold" style={{ color: 'var(--accent-ink)' }}>
                    {fc.value} {fc.unit || ''}
                  </div>

                  {/* Validity bar */}
                  <div className="pt-2">
                    <div className="flex justify-between text-[11px] mb-1" style={{ color: 'var(--muted)' }}>
                      <span>Validity timeline</span>
                      <span>Expires in 180 days</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--hairline)' }}>
                      <div className="h-full rounded-full" style={{ width: '70%', backgroundColor: 'var(--accent)' }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* CLAIMS TAB */}
          {activeTab === 'claims' && (
            <div className="divide-y border rounded-[2px]" style={{ borderColor: 'var(--hairline)' }}>
              {claims.map((cl) => (
                <div key={cl.id} className="p-3.5 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-serif font-semibold mr-2" style={{ color: 'var(--ink)' }}>
                      "{cl.approved_text}"
                    </span>
                    <span className="italic" style={{ color: 'var(--muted)' }}>
                      Required evidence: {cl.evidence_ref || 'Verified record'}
                    </span>
                  </div>
                  <span className="font-mono text-[10px]" style={{ color: 'var(--accent-ink)' }}>
                    {cl.required_disclaimer ? 'Disclaimer required' : 'Self-contained'}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* ASSETS TAB */}
          {activeTab === 'assets' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {assets.map((ast) => (
                <div
                  key={ast.id}
                  className="p-4 rounded-[2px] border space-y-2 text-xs"
                  style={{
                    backgroundColor: 'var(--paper)',
                    borderColor: 'var(--hairline)',
                  }}
                >
                  <span className="font-mono font-bold block" style={{ color: 'var(--ink)' }}>
                    {ast.name}
                  </span>
                  <div className="text-[11px]" style={{ color: 'var(--muted)' }}>
                    Type: {ast.asset_type}
                  </div>
                  {ast.asset_type === 'palette_color' && (
                    <div className="flex items-center gap-2 pt-1">
                      <div
                        className="w-5 h-5 rounded-[2px] border"
                        style={{ backgroundColor: ast.value, borderColor: 'var(--hairline)' }}
                      />
                      <span className="font-mono">{ast.value}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* VERSIONS TAB (TIMELINE & DIFF) */}
          {activeTab === 'versions' && (
            <div className="space-y-4">
              {versions.map((ver, idx) => (
                <div
                  key={ver.id}
                  className="p-4 rounded-[2px] border flex items-center justify-between text-xs"
                  style={{
                    backgroundColor: ver.active ? 'var(--accent-surface)' : 'var(--paper)',
                    borderColor: ver.active ? 'var(--accent)' : 'var(--hairline)',
                  }}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold" style={{ color: 'var(--ink)' }}>
                        {ver.label || `v${idx + 1}.0`}
                      </span>
                      {ver.active && (
                        <span
                          className="px-1.5 py-0.2 rounded-[2px] text-[10px] font-mono font-semibold"
                          style={{
                            backgroundColor: 'var(--status-verified)',
                            color: '#ffffff',
                          }}
                        >
                          ACTIVE
                        </span>
                      )}
                    </div>
                    <p className="text-[11px]" style={{ color: 'var(--muted)' }}>
                      Snapshot created {ver.created_at ? new Date(ver.created_at).toLocaleDateString() : 'recently'}
                    </p>
                  </div>

                  {!ver.active && (
                    <button
                      onClick={() => handleActivateVersion(ver.id)}
                      className="px-3 py-1.5 rounded-[2px] border text-xs font-medium hover:bg-black/5"
                      style={{ borderColor: 'var(--hairline)', color: 'var(--graphite)' }}
                    >
                      Roll back to this version
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* IMPORT 3-STEP FLOW */}
          {activeTab === 'import' && (
            <div className="max-w-2xl mx-auto space-y-6">
              {/* Stepper indicator */}
              <div className="flex items-center justify-between text-xs pb-4 border-b" style={{ borderColor: 'var(--hairline)' }}>
                <div className={`flex items-center gap-1.5 ${importStep >= 1 ? 'font-bold' : 'opacity-40'}`}>
                  <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] bg-[var(--accent)] text-white">1</span>
                  <span>1. Paste or upload</span>
                </div>
                <span>→</span>
                <div className={`flex items-center gap-1.5 ${importStep >= 2 ? 'font-bold' : 'opacity-40'}`}>
                  <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] bg-[var(--accent)] text-white">2</span>
                  <span>2. Review extracted rules</span>
                </div>
                <span>→</span>
                <div className={`flex items-center gap-1.5 ${importStep === 3 ? 'font-bold' : 'opacity-40'}`}>
                  <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] bg-[var(--accent)] text-white">3</span>
                  <span>3. Confirm to KB</span>
                </div>
              </div>

              {importStep === 1 && (
                <div className="space-y-4">
                  <p className="text-xs" style={{ color: 'var(--graphite)' }}>
                    Paste raw brand guideline text, PDF export copy, or tone document. The atomic parser will extract individual rules and constraints:
                  </p>
                  <textarea
                    rows={8}
                    value={guidelinesText}
                    onChange={(e) => setGuidelinesText(e.target.value)}
                    placeholder="e.g. Always refer to our battery life as 'up to 10 days'. Never promise medical cure or treatment. Disclaim APR on financial offers..."
                    className="w-full p-3 text-xs rounded-[2px] border focus:outline-none"
                    style={{
                      backgroundColor: 'var(--paper)',
                      borderColor: 'var(--hairline)',
                      color: 'var(--ink)',
                    }}
                  />
                  <button
                    onClick={handleAtomise}
                    disabled={atomising || !guidelinesText.trim()}
                    className="px-4 py-2 rounded-[2px] text-xs font-semibold text-white transition-all disabled:opacity-50"
                    style={{ backgroundColor: 'var(--accent)' }}
                  >
                    {atomising ? 'Extracting rules...' : 'Extract atomic rules'}
                  </button>
                </div>
              )}

              {importStep === 2 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-serif font-semibold text-sm" style={{ color: 'var(--ink)' }}>
                      Proposed rules ({candidates.length})
                    </h4>
                    <button
                      onClick={() => setImportStep(1)}
                      className="text-xs underline"
                      style={{ color: 'var(--muted)' }}
                    >
                      Back to edit
                    </button>
                  </div>

                  <div className="space-y-2 max-h-80 overflow-y-auto">
                    {candidates.map((c, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-[2px] border text-xs space-y-1"
                        style={{
                          backgroundColor: 'var(--paper)',
                          borderColor: 'var(--hairline)',
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono font-bold">{c.code || `PROPOSED-${idx + 1}`}</span>
                          <span className="capitalize text-[10px] font-mono">{c.category || 'tone'}</span>
                        </div>
                        <p>{c.text}</p>
                      </div>
                    ))}
                  </div>

                  <button
                    onClick={handleConfirmImport}
                    className="w-full py-2.5 rounded-[2px] text-xs font-semibold text-white"
                    style={{ backgroundColor: 'var(--accent)' }}
                  >
                    Confirm and save to active knowledge base
                  </button>
                </div>
              )}

              {importStep === 3 && (
                <div className="py-12 text-center space-y-3">
                  <CheckCircle2 size={32} className="mx-auto" style={{ color: 'var(--status-verified)' }} />
                  <h4 className="font-serif font-semibold text-base" style={{ color: 'var(--ink)' }}>
                    Rules successfully imported
                  </h4>
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>
                    All extracted rules are now actively enforced across all pre-publication checks.
                  </p>
                  <button
                    onClick={() => {
                      setImportStep(1);
                      setActiveTab('rules');
                    }}
                    className="px-4 py-2 rounded-[2px] border text-xs font-medium"
                    style={{ borderColor: 'var(--hairline)', color: 'var(--graphite)' }}
                  >
                    View rules ledger
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Add Rule Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div
            className="w-full max-w-md p-6 rounded-[2px] border space-y-4"
            style={{
              backgroundColor: 'var(--sheet)',
              borderColor: 'var(--hairline)',
              boxShadow: '0 8px 32px rgba(20, 23, 31, 0.15)',
            }}
          >
            <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: 'var(--hairline)' }}>
              <h3 className="font-serif font-semibold text-base" style={{ color: 'var(--ink)' }}>
                Add new brand rule
              </h3>
              <button onClick={() => setShowAddModal(false)} className="p-1 hover:bg-black/5">
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleCreateRule} className="space-y-3 text-xs">
              <div>
                <label className="block font-medium mb-1" style={{ color: 'var(--graphite)' }}>
                  Rule code (e.g. BR-TONE-01)
                </label>
                <input
                  type="text"
                  required
                  value={newRuleCode}
                  onChange={(e) => setNewRuleCode(e.target.value)}
                  className="w-full p-2 rounded-[2px] border focus:outline-none font-mono"
                  style={{ backgroundColor: 'var(--paper)', borderColor: 'var(--hairline)', color: 'var(--ink)' }}
                />
              </div>

              <div>
                <label className="block font-medium mb-1" style={{ color: 'var(--graphite)' }}>
                  Category
                </label>
                <select
                  value={newRuleCategory}
                  onChange={(e) => setNewRuleCategory(e.target.value)}
                  className="w-full p-2 rounded-[2px] border focus:outline-none"
                  style={{ backgroundColor: 'var(--paper)', borderColor: 'var(--hairline)', color: 'var(--ink)' }}
                >
                  <option value="tone">Tone &amp; Voice</option>
                  <option value="terminology">Terminology</option>
                  <option value="claims">Promotional Claims</option>
                  <option value="factual">Factual Specification</option>
                  <option value="safety">Safety &amp; Compliance</option>
                </select>
              </div>

              <div>
                <label className="block font-medium mb-1" style={{ color: 'var(--graphite)' }}>
                  Default severity
                </label>
                <select
                  value={newRuleSeverity}
                  onChange={(e) => setNewRuleSeverity(e.target.value)}
                  className="w-full p-2 rounded-[2px] border focus:outline-none"
                  style={{ backgroundColor: 'var(--paper)', borderColor: 'var(--hairline)', color: 'var(--ink)' }}
                >
                  <option value="blocker">Blocker (Prevents publication)</option>
                  <option value="major">Major (Requires justification)</option>
                  <option value="minor">Minor (Stylistic advice)</option>
                </select>
              </div>

              <div>
                <label className="block font-medium mb-1" style={{ color: 'var(--graphite)' }}>
                  Rule description &amp; guideline
                </label>
                <textarea
                  rows={4}
                  required
                  value={newRuleText}
                  onChange={(e) => setNewRuleText(e.target.value)}
                  placeholder="State the exact brand constraint or required phrasing..."
                  className="w-full p-2 rounded-[2px] border focus:outline-none"
                  style={{ backgroundColor: 'var(--paper)', borderColor: 'var(--hairline)', color: 'var(--ink)' }}
                />
              </div>

              <div className="pt-3 border-t flex justify-end gap-2" style={{ borderColor: 'var(--hairline)' }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 rounded-[2px] border"
                  style={{ borderColor: 'var(--hairline)', color: 'var(--graphite)' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-[2px] font-semibold text-white"
                  style={{ backgroundColor: 'var(--accent)' }}
                >
                  Save rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
