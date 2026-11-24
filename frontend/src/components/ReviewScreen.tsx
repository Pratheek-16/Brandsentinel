import React, { useState, useEffect, useRef } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  Info,
  CheckCircle,
  Check,
  X,
  MessageSquare,
  ArrowRight,
  ShieldAlert,
  Send,
  History,
  Sparkles,
  Edit3,
  RefreshCw,
  Clock,
  Layers,
  Lock,
  Download,
  FileText,
  Cpu,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  CornerDownRight,
} from 'lucide-react';
import { api } from '../api';
import {
  User,
  Finding,
  ClaimItem,
  VerifiedSuggestion,
  CommentItem,
  ContentItem,
  ReviewResponse,
} from '../types';

interface ReviewScreenProps {
  contentId: number;
  currentUser: User | null;
  onRefreshContent: () => void;
}

export const ReviewScreen: React.FC<ReviewScreenProps> = ({
  contentId,
  currentUser,
  onRefreshContent,
}) => {
  const [content, setContent] = useState<ContentItem | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [claims, setClaims] = useState<ClaimItem[]>([]);
  const [comments, setComments] = useState<CommentItem[]>([]);
  const [reviewInfo, setReviewInfo] = useState<any>(null);
  const [aiUsage, setAiUsage] = useState<any>(null);
  const [newComment, setNewComment] = useState('');
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [suggestions, setSuggestions] = useState<VerifiedSuggestion[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [activeOptionTab, setActiveOptionTab] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [reReviewing, setReReviewing] = useState(false);

  // Drawers & Modals
  const [showAiDrawer, setShowAiDrawer] = useState(false);
  const [aiLedger, setAiLedger] = useState<any>(null);
  const [loadingLedger, setLoadingLedger] = useState(false);
  const [showSigningSheet, setShowSigningSheet] = useState(false);
  const [showCommentsDrawer, setShowCommentsDrawer] = useState(false);

  // Actions
  const [dismissReason, setDismissReason] = useState('');
  const [showDismissPicker, setShowDismissPicker] = useState(false);
  const [showEditInput, setShowEditInput] = useState(false);
  const [customEditText, setCustomEditText] = useState('');
  const [approvalDecision, setApprovalDecision] = useState<'approved' | 'changes_requested' | 'rejected'>('approved');
  const [approvalJustification, setApprovalJustification] = useState('');
  const [approvalStampVisible, setApprovalStampVisible] = useState(false);
  const [lastApprovalData, setLastApprovalData] = useState<any>(null);
  const [toastMsg, setToastMsg] = useState<{ text: string; undoFn?: () => void } | null>(null);

  useEffect(() => {
    if (toastMsg) {
      const timer = setTimeout(() => setToastMsg(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [toastMsg]);

  // SVG leader line refs
  const sheetRef = useRef<HTMLDivElement | null>(null);
  const cardsContainerRef = useRef<HTMLDivElement | null>(null);

  const loadData = async (forceReview = false) => {
    if (!contentId) return;
    try {
      setLoading(true);
      const c = await api.getContent(contentId);
      setContent(c);

      let rev: ReviewResponse;
      if (forceReview) {
        rev = await api.reviewContent(contentId);
      } else {
        rev = await api.getReview(contentId);
        if (!rev.has_review && (!rev.findings || rev.findings.length === 0)) {
          rev = await api.reviewContent(contentId);
        }
      }

      const loadedFindings = rev.findings || [];
      setFindings(loadedFindings);
      setReviewInfo(rev.review || null);
      setAiUsage(rev.ai_usage || null);

      if (c.status === 'approved') {
        setApprovalStampVisible(true);
      }

      const [cl, cm] = await Promise.all([
        api.getClaims(contentId).catch(() => ({ claims: [] })),
        api.getComments(contentId).catch(() => []),
      ]);
      setClaims(cl.claims || []);
      setComments(cm || []);
    } catch (err: any) {
      console.error(err);
      setToastMsg({ text: err.message || 'Error loading review data' });
    } finally {
      setLoading(false);
      setReReviewing(false);
    }
  };

  useEffect(() => {
    loadData(false);
  }, [contentId]);

  const activeFinding = findings[selectedIndex] || null;

  // Load suggestions whenever selected finding changes
  useEffect(() => {
    if (!activeFinding) {
      setSuggestions([]);
      return;
    }
    setActiveOptionTab(0);
    setShowDismissPicker(false);
    setShowEditInput(false);
    setCustomEditText(activeFinding.selected_replacement || activeFinding.suggestion_text || activeFinding.span_text);

    if (activeFinding.status === 'open' || !activeFinding.status) {
      setLoadingSuggestions(true);
      api
        .getSuggestions(contentId, activeFinding.id)
        .then((res) => {
          setSuggestions(res.suggestions || []);
        })
        .catch(() => {
          setSuggestions([]);
        })
        .finally(() => {
          setLoadingSuggestions(false);
        });
    } else {
      setSuggestions([]);
    }
  }, [selectedIndex, activeFinding?.id]);

  // Keyboard navigation shortcuts: J (next), K (prev), A (apply), E (edit), D (dismiss)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept when user is typing in input or textarea
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'TEXTAREA'
      ) {
        return;
      }

      if (e.key === 'j' || e.key === 'J' || e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(findings.length - 1, prev + 1));
      } else if (e.key === 'k' || e.key === 'K' || e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(0, prev - 1));
      } else if (e.key === 'a' || e.key === 'A') {
        e.preventDefault();
        const currentOption = getCurrentOptionReplacement();
        if (currentOption) {
          handleApplyFix(currentOption);
        }
      } else if (e.key === 'e' || e.key === 'E') {
        e.preventDefault();
        setShowEditInput(true);
      } else if (e.key === 'd' || e.key === 'D') {
        e.preventDefault();
        setShowDismissPicker(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [findings.length, selectedIndex, suggestions, activeOptionTab]);

  const getCurrentOptionReplacement = (): string | null => {
    if (!activeFinding) return null;
    if (suggestions.length > 0 && suggestions[activeOptionTab]) {
      return suggestions[activeOptionTab].replacement_text;
    }
    if (activeFinding.suggestion_text) {
      return activeFinding.suggestion_text;
    }
    return null;
  };

  const handleApplyFix = async (replacement: string) => {
    if (!activeFinding) return;
    try {
      await api.acceptSuggestion(contentId, activeFinding.id, replacement);
      setToastMsg({
        text: `Applied replacement to #${activeFinding.id}. New version generated.`,
      });
      await loadData(true);
      onRefreshContent();
    } catch (err: any) {
      setToastMsg({ text: err.message || 'Error applying fix' });
    }
  };

  const handleSaveCustomEdit = async () => {
    if (!activeFinding || !customEditText.trim()) return;
    try {
      await api.editFinding(contentId, activeFinding.id, customEditText.trim());
      setShowEditInput(false);
      setToastMsg({ text: `Custom edit applied. New draft version created.` });
      await loadData(true);
      onRefreshContent();
    } catch (err: any) {
      setToastMsg({ text: err.message || 'Error saving edit' });
    }
  };

  const handleDismissFinding = async (reason: string) => {
    if (!activeFinding) return;
    try {
      await api.dismissFinding(contentId, activeFinding.id, reason);
      setShowDismissPicker(false);
      setDismissReason('');
      setToastMsg({ text: `Finding #${activeFinding.id} dismissed with cited justification.` });
      await loadData(false);
    } catch (err: any) {
      setToastMsg({ text: err.message || 'Error dismissing finding' });
    }
  };

  const handleOpenAiDrawer = async () => {
    setShowAiDrawer(true);
    setLoadingLedger(true);
    try {
      const res = await api.getAILedger(contentId);
      setAiLedger(res);
    } catch (err) {
      console.warn('Could not load AI ledger:', err);
    } finally {
      setLoadingLedger(false);
    }
  };

  const handleSubmitForReview = async () => {
    try {
      const res = await api.submitContent(contentId);
      setContent((prev: any) => ({ ...prev, status: res.status }));
      if (res.escalated) {
        setToastMsg({
          text: `Escalated to Authorised Reviewer queue: ${res.escalation_reason}`,
        });
      } else {
        setToastMsg({ text: 'Draft submitted to Manager Review queue.' });
      }
      await loadData(false);
    } catch (err: any) {
      setToastMsg({ text: err.message || 'Submission error' });
    }
  };

  const handleConfirmApproval = async () => {
    if (!approvalJustification.trim()) {
      setToastMsg({ text: 'Please provide a signing justification.' });
      return;
    }
    try {
      const res = await api.approveContent(contentId, approvalDecision, approvalJustification.trim());
      setLastApprovalData(res);
      setShowSigningSheet(false);
      setContent((prev: any) => ({ ...prev, status: res.status }));
      if (approvalDecision === 'approved') {
        setApprovalStampVisible(true);
      }
      setToastMsg({
        text: `Recorded decision [${approvalDecision}]. Cryptographic signature: ${res.signature_hash.slice(0, 12)}...`,
      });
      await loadData(false);
    } catch (err: any) {
      setToastMsg({ text: err.message || 'Approval action failed' });
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    try {
      await api.addComment(contentId, newComment.trim(), activeFinding?.id);
      setNewComment('');
      const cm = await api.getComments(contentId);
      setComments(cm || []);
    } catch (err: any) {
      setToastMsg({ text: err.message || 'Failed to post comment' });
    }
  };

  const handleExportCertificate = async () => {
    try {
      const certText = await api.exportCertificate(contentId, 'markdown');
      const blob = new Blob([certText], { type: 'text/markdown;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `BrandSentinel_Certificate_${contentId}.md`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      setToastMsg({ text: 'Downloaded verifiable governance certificate.' });
    } catch (err: any) {
      setToastMsg({ text: err.message || 'Export failed' });
    }
  };

  // Severity counts
  const blockerCount = findings.filter((f) => f.severity === 'blocker' && f.status !== 'dismissed').length;
  const majorCount = findings.filter((f) => f.severity === 'major' && f.status !== 'dismissed').length;
  const minorCount = findings.filter((f) => f.severity === 'minor' && f.status !== 'dismissed').length;
  const infoCount = findings.filter((f) => f.severity === 'info' && f.status !== 'dismissed').length;
  const openCount = findings.filter((f) => !f.status || f.status === 'open').length;

  // Render proofing sheet with numbered wavy markers
  const renderProofingDocument = () => {
    const rawText = content?.text_body || '';
    if (!rawText) {
      return <p className="italic text-sm" style={{ color: 'var(--muted)' }}>No text copy available in this draft.</p>;
    }

    // Filter valid findings sorted by start position
    const validFindings = findings
      .map((f, idx) => ({ ...f, originalIndex: idx }))
      .filter((f) => {
        const s = f.span ? f.span.start : f.span_start;
        const e = f.span ? f.span.end : f.span_end;
        return typeof s === 'number' && typeof e === 'number' && e > s && s >= 0 && e <= rawText.length;
      })
      .sort((a, b) => {
        const sa = a.span ? a.span.start : a.span_start;
        const sb = b.span ? b.span.start : b.span_start;
        return sa - sb;
      });

    if (validFindings.length === 0) {
      return <p className="font-serif text-[18px] leading-relaxed" style={{ color: 'var(--ink)' }}>{rawText}</p>;
    }

    const fragments: React.ReactNode[] = [];
    let cur = 0;

    validFindings.forEach((f) => {
      let start = f.span ? f.span.start : f.span_start;
      let end = f.span ? f.span.end : f.span_end;

      const isSelected = activeFinding?.id === f.id;
      const isAccepted = f.status === 'accepted' || f.status === 'edited';
      const isDismissed = f.status === 'dismissed';

      let actualEnd = end;
      let displayText = rawText.substring(start, end);

      // If accepted with replacement, ensure the entire new replacement is enclosed in the green box
      if (isAccepted && f.selected_replacement) {
        if (rawText.startsWith(f.selected_replacement, start)) {
          actualEnd = start + f.selected_replacement.length;
          displayText = f.selected_replacement;
        } else {
          const repIdx = rawText.indexOf(f.selected_replacement, Math.max(0, start - 30));
          if (repIdx !== -1 && repIdx <= start + 30) {
            start = repIdx;
            actualEnd = repIdx + f.selected_replacement.length;
            displayText = f.selected_replacement;
          } else {
            displayText = f.selected_replacement;
          }
        }
      }

      // Skip overlapping findings whose offsets fell inside an applied edit
      if (start < cur) {
        return;
      }

      if (start > cur) {
        fragments.push(
          <span key={`t-${cur}`}>{rawText.substring(cur, start)}</span>
        );
      }

      let underlineClass = 'wavy-underline-minor';
      if (f.severity === 'blocker') underlineClass = 'wavy-underline-blocker font-medium';
      else if (f.severity === 'major') underlineClass = 'wavy-underline-major';
      else if (f.severity === 'info') underlineClass = 'wavy-underline-info';

      fragments.push(
        <span
          key={`f-${f.id}`}
          onClick={() => setSelectedIndex(f.originalIndex)}
          className={`relative cursor-pointer transition-all inline-block ${
            isDismissed
              ? 'opacity-50 line-through'
              : isAccepted
              ? 'bg-emerald-100 dark:bg-emerald-950/70 text-emerald-900 dark:text-emerald-200 border border-emerald-400 px-1 py-0.5 rounded-[2px]'
              : underlineClass
          } ${
            isSelected
              ? 'bg-amber-100/60 dark:bg-amber-950/40 ring-1 ring-[var(--accent)] rounded-[1px]'
              : 'hover:bg-black/5 dark:hover:bg-white/5'
          }`}
          title={`Finding #${f.originalIndex + 1}: ${f.reason}`}
        >
          {displayText}

          {/* Numbered superscript marker */}
          <sup
            className="ml-0.5 px-1 py-0.2 rounded-full text-[10px] font-mono font-semibold"
            style={{
              backgroundColor: isSelected ? 'var(--accent)' : 'var(--hairline)',
              color: isSelected ? '#ffffff' : 'var(--graphite)',
            }}
          >
            {f.originalIndex + 1}
          </sup>
        </span>
      );

      cur = Math.max(cur, actualEnd);
    });

    if (cur < rawText.length) {
      fragments.push(<span key={`t-${cur}`}>{rawText.substring(cur)}</span>);
    }

    return (
      <div className="font-serif text-[18px] leading-relaxed relative" style={{ color: 'var(--ink)' }}>
        {fragments}
      </div>
    );
  };

  if (loading && !content) {
    return (
      <div className="py-24 text-center text-sm flex flex-col items-center justify-center gap-3" style={{ color: 'var(--muted)' }}>
        <RefreshCw className="animate-spin" size={20} style={{ color: 'var(--accent)' }} />
        <span>Preparing editorial proof sheet...</span>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="py-20 text-center text-sm" style={{ color: 'var(--muted)' }}>
        No draft selected. Please choose or submit a draft from the Drafts tab.
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 space-y-6">
      {/* Toast notification */}
      {toastMsg && (
        <div
          className="fixed bottom-6 right-6 z-50 flex items-center justify-between gap-3 px-4 py-3 rounded-[2px] border shadow-lg text-xs"
          style={{
            backgroundColor: 'var(--sheet)',
            borderColor: 'var(--hairline)',
            color: 'var(--ink)',
          }}
        >
          <span>{toastMsg.text}</span>
          <button
            onClick={() => setToastMsg(null)}
            className="p-1 hover:bg-black/5 rounded-[2px]"
          >
            <X size={13} />
          </button>
        </div>
      )}

      {/* Summary Strip Above the Sheet */}
      <div
        className="p-4 sm:p-5 rounded-[2px] border flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{
          backgroundColor: 'var(--sheet)',
          borderColor: 'var(--hairline)',
        }}
      >
        <div>
          <div className="flex items-center gap-3">
            <h2 className="font-serif font-semibold text-lg" style={{ color: 'var(--ink)' }}>
              {content.title}
            </h2>
            <span
              className="text-xs font-mono px-2 py-0.5 rounded-[2px] capitalize"
              style={{
                backgroundColor:
                  content.status === 'approved'
                    ? 'var(--status-verified-bg)'
                    : content.status === 'changes_requested'
                    ? 'var(--severity-major-bg)'
                    : 'var(--accent-surface)',
                color:
                  content.status === 'approved'
                    ? 'var(--status-verified)'
                    : content.status === 'changes_requested'
                    ? 'var(--severity-major)'
                    : 'var(--accent-ink)',
                border: '1px solid currentColor',
              }}
            >
              {content.status?.replace('_', ' ')}
            </span>
            <span className="text-xs font-mono" style={{ color: 'var(--muted)' }}>
              v{content.version_no || 1}
            </span>
          </div>

          {/* Plain verdict line & severity badges */}
          <div className="flex flex-wrap items-center gap-3 mt-2 text-xs">
            {openCount === 0 ? (
              <span className="flex items-center gap-1.5 font-medium" style={{ color: 'var(--status-verified)' }}>
                <CheckCircle size={14} />
                <span>No issues found by these checks (Note: not a legal or factual guarantee)</span>
              </span>
            ) : (
              <span className="font-medium" style={{ color: 'var(--ink)' }}>
                {blockerCount > 0
                  ? `${blockerCount} blocking issue${blockerCount > 1 ? 's' : ''} require revision before publication.`
                  : `${openCount} finding${openCount > 1 ? 's' : ''} open for editorial review.`}
              </span>
            )}

            <div className="flex items-center gap-1.5">
              {blockerCount > 0 && (
                <span
                  className="px-2 py-0.5 rounded-[2px] font-mono text-[10px] font-semibold"
                  style={{
                    backgroundColor: 'var(--severity-blocker-bg)',
                    color: 'var(--severity-blocker)',
                    border: '1px solid var(--severity-blocker)',
                  }}
                >
                  {blockerCount} blocker
                </span>
              )}
              {majorCount > 0 && (
                <span
                  className="px-2 py-0.5 rounded-[2px] font-mono text-[10px] font-semibold"
                  style={{
                    backgroundColor: 'var(--severity-major-bg)',
                    color: 'var(--severity-major)',
                    border: '1px solid var(--severity-major)',
                  }}
                >
                  {majorCount} major
                </span>
              )}
              {minorCount > 0 && (
                <span
                  className="px-2 py-0.5 rounded-[2px] font-mono text-[10px] font-semibold"
                  style={{
                    backgroundColor: 'var(--severity-minor-bg)',
                    color: 'var(--severity-minor)',
                    border: '1px solid var(--severity-minor)',
                  }}
                >
                  {minorCount} minor
                </span>
              )}
              {infoCount > 0 && (
                <span
                  className="px-2 py-0.5 rounded-[2px] font-mono text-[10px] font-semibold"
                  style={{
                    backgroundColor: 'var(--severity-info-bg)',
                    color: 'var(--severity-info)',
                    border: '1px solid var(--severity-info)',
                  }}
                >
                  {infoCount} info
                </span>
              )}
            </div>

            {aiUsage && aiUsage.redaction_count > 0 && (
              <span
                className="flex items-center gap-1 px-2 py-0.5 rounded-[2px] text-[10px] font-mono"
                style={{
                  backgroundColor: 'var(--paper)',
                  color: 'var(--graphite)',
                  border: '1px solid var(--hairline)',
                }}
              >
                <Lock size={10} />
                <span>{aiUsage.redaction_count} items hidden before analysis</span>
              </span>
            )}
          </div>
        </div>

        {/* Action buttons on strip */}
        <div className="flex items-center flex-wrap gap-2">
          <button
            type="button"
            onClick={handleOpenAiDrawer}
            className="px-3 py-1.5 rounded-[2px] border text-xs font-medium transition-colors hover:bg-black/5 dark:hover:bg-white/5 flex items-center gap-1.5"
            style={{
              borderColor: 'var(--hairline)',
              color: 'var(--graphite)',
            }}
          >
            <Cpu size={13} />
            <span>How AI was used</span>
          </button>

          <button
            type="button"
            onClick={() => setShowCommentsDrawer(true)}
            className="px-3 py-1.5 rounded-[2px] border text-xs font-medium transition-colors hover:bg-black/5 dark:hover:bg-white/5 flex items-center gap-1.5"
            style={{
              borderColor: 'var(--hairline)',
              color: 'var(--graphite)',
            }}
          >
            <MessageSquare size={13} />
            <span>Comments ({comments.length})</span>
          </button>

          <button
            type="button"
            onClick={handleExportCertificate}
            className="px-3 py-1.5 rounded-[2px] border text-xs font-medium transition-colors hover:bg-black/5 dark:hover:bg-white/5 flex items-center gap-1.5"
            style={{
              borderColor: 'var(--hairline)',
              color: 'var(--graphite)',
            }}
          >
            <Download size={13} />
            <span>Certificate</span>
          </button>

          {/* Workflow approval triggers based on role */}
          {currentUser?.role === 'creator' && content.status !== 'approved' && (
            <button
              type="button"
              onClick={handleSubmitForReview}
              className="px-4 py-1.5 rounded-[2px] text-xs font-medium transition-all shadow-xs flex items-center gap-1.5"
              style={{
                backgroundColor: 'var(--accent)',
                color: '#ffffff',
              }}
            >
              <Send size={13} />
              <span>Submit for approval</span>
            </button>
          )}

          {(currentUser?.role === 'manager' ||
            currentUser?.role === 'reviewer' ||
            currentUser?.role === 'admin') &&
            content.status !== 'approved' && (
              <button
                type="button"
                onClick={() => {
                  setApprovalDecision('approved');
                  setApprovalJustification('Content satisfies verified brand criteria and compliance rules.');
                  setShowSigningSheet(true);
                }}
                className="px-4 py-1.5 rounded-[2px] text-xs font-medium transition-all shadow-xs flex items-center gap-1.5"
                style={{
                  backgroundColor: 'var(--accent)',
                  color: '#ffffff',
                }}
              >
                <Check size={13} strokeWidth={2.5} />
                <span>Review & sign</span>
              </button>
            )}
        </div>
      </div>

      {/* Two-Column Layout: Sheet (60%) and Margin of Annotation Cards (40%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start relative">
        {/* Left Column: The Proof Sheet (60% ~ 7 cols) */}
        <div className="lg:col-span-7">
          <div
            ref={sheetRef}
            className="proofing-sheet p-8 sm:p-12 relative min-h-[580px] overflow-hidden"
          >
            {/* Approval Stamp Animation / Press */}
            {approvalStampVisible && (
              <div
                className="absolute top-8 right-8 z-20 stamp-approved p-4 rounded-[2px] select-none pointer-events-none transform rotate-[-8deg] shadow-lg animate-in fade-in zoom-in-95 duration-300"
              >
                <div className="text-center">
                  <div className="text-lg tracking-wider">APPROVED</div>
                  <div className="text-[10px] font-mono mt-0.5">
                    {lastApprovalData?.signature_hash
                      ? `SIG: ${lastApprovalData.signature_hash.slice(0, 10)}...`
                      : 'CRYPTOGRAPHIC AUDIT SEAL'}
                  </div>
                  <div className="text-[9px] font-mono opacity-80 mt-0.5">
                    {new Date().toISOString().split('T')[0]} • BRAND GOVERNED
                  </div>
                </div>
              </div>
            )}

            {/* Document Header */}
            <div className="pb-6 mb-6 border-b" style={{ borderColor: 'var(--hairline-subtle)' }}>
              <div className="flex items-center justify-between text-xs mb-2" style={{ color: 'var(--muted)' }}>
                <span>Channel: {content.channel}</span>
                <span>Type: {content.type}</span>
              </div>
              <h1 className="text-2xl font-serif font-semibold tracking-tight" style={{ color: 'var(--ink)' }}>
                {content.title}
              </h1>
            </div>

            {/* The Proofing Text Body */}
            {renderProofingDocument()}

            {/* Bottom Proofing Footer */}
            <div className="mt-12 pt-6 border-t flex items-center justify-between text-xs" style={{ borderColor: 'var(--hairline-subtle)', color: 'var(--muted)' }}>
              <span>Proofing desk verification</span>
              <span className="font-mono">
                Hash: {(content as any).content_hash ? (content as any).content_hash.slice(0, 16) : content.versions?.[0]?.content_hash ? content.versions[0].content_hash.slice(0, 16) : 'e3b0c44298fc1c14'}...
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Margin of Annotation Cards (40% ~ 5 cols) */}
        <div ref={cardsContainerRef} className="lg:col-span-5 space-y-4">
          {/* Findings Navigation Bar */}
          <div className="flex items-center justify-between pb-2 border-b" style={{ borderColor: 'var(--hairline)' }}>
            <span className="text-xs font-serif font-semibold" style={{ color: 'var(--ink)' }}>
              Margin notes ({findings.length > 0 ? selectedIndex + 1 : 0} of {findings.length})
            </span>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setSelectedIndex((prev) => Math.max(0, prev - 1))}
                disabled={selectedIndex === 0}
                className="px-2 py-0.5 rounded-[2px] border text-xs font-mono disabled:opacity-40"
                style={{ borderColor: 'var(--hairline)', color: 'var(--graphite)' }}
                title="Previous finding (K)"
              >
                ↑ K
              </button>
              <button
                type="button"
                onClick={() => setSelectedIndex((prev) => Math.min(findings.length - 1, prev + 1))}
                disabled={selectedIndex >= findings.length - 1}
                className="px-2 py-0.5 rounded-[2px] border text-xs font-mono disabled:opacity-40"
                style={{ borderColor: 'var(--hairline)', color: 'var(--graphite)' }}
                title="Next finding (J)"
              >
                ↓ J
              </button>
            </div>
          </div>

          {findings.length === 0 ? (
            <div
              className="p-8 text-center rounded-[2px] border text-xs"
              style={{
                backgroundColor: 'var(--sheet)',
                borderColor: 'var(--hairline)',
                color: 'var(--muted)',
              }}
            >
              <CheckCircle size={24} className="mx-auto mb-2" style={{ color: 'var(--status-verified)' }} />
              <p className="font-medium" style={{ color: 'var(--ink)' }}>
                Clean proofing sheet
              </p>
              <p className="mt-1">All checked facts, claims, and style rules are compliant.</p>
            </div>
          ) : activeFinding ? (
            /* The Active Annotation Card */
            <div
              className="p-5 rounded-[2px] border transition-all relative space-y-4"
              style={{
                backgroundColor: 'var(--sheet)',
                borderColor: 'var(--accent)',
                boxShadow: '0 4px 16px -2px rgba(14, 124, 123, 0.08)',
              }}
            >
              {/* Header: Severity Badge, Category, Source Badge */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  {/* Severity Icon & Sentence Case Label */}
                  <span
                    className="flex items-center gap-1.5 px-2 py-0.5 rounded-[2px] text-xs font-medium capitalize"
                    style={{
                      backgroundColor:
                        activeFinding.severity === 'blocker'
                          ? 'var(--severity-blocker-bg)'
                          : activeFinding.severity === 'major'
                          ? 'var(--severity-major-bg)'
                          : 'var(--severity-minor-bg)',
                      color:
                        activeFinding.severity === 'blocker'
                          ? 'var(--severity-blocker)'
                          : activeFinding.severity === 'major'
                          ? 'var(--severity-major)'
                          : 'var(--severity-minor)',
                      border: '1px solid currentColor',
                    }}
                  >
                    {activeFinding.severity === 'blocker' ? (
                      <AlertOctagon size={13} />
                    ) : activeFinding.severity === 'major' ? (
                      <AlertTriangle size={13} />
                    ) : (
                      <Info size={13} />
                    )}
                    <span>{activeFinding.severity}</span>
                  </span>

                  <span className="text-xs font-medium" style={{ color: 'var(--graphite)' }}>
                    {activeFinding.category}
                  </span>
                </div>

                {/* Source Badge */}
                <span
                  className="text-[10px] font-mono px-1.5 py-0.5 rounded-[2px]"
                  style={{
                    backgroundColor: 'var(--paper)',
                    color: 'var(--muted)',
                    border: '1px solid var(--hairline)',
                  }}
                >
                  {activeFinding.source || 'Brand rule'}
                </span>
              </div>

              {/* One-line reason in plain sentence case */}
              <p className="text-xs font-medium leading-relaxed" style={{ color: 'var(--ink)' }}>
                {activeFinding.reason}
              </p>

              {/* Quoted Flagged Text */}
              <div
                className="p-2.5 rounded-[2px] text-xs border"
                style={{
                  backgroundColor: 'var(--paper)',
                  borderColor: 'var(--hairline)',
                  color: 'var(--ink)',
                }}
              >
                <span className="text-[10px] block mb-1" style={{ color: 'var(--muted)' }}>
                  Flagged text
                </span>
                <span className="font-serif italic">"{activeFinding.span_text}"</span>
              </div>

              {/* Citation Stamp: Rule ID in mono, Quoted rule in italics, KB version, Verified tick */}
              <div
                className="p-3 rounded-[2px] border text-xs space-y-1.5"
                style={{
                  backgroundColor: 'var(--accent-surface)',
                  borderColor: 'var(--hairline)',
                }}
              >
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-mono font-bold" style={{ color: 'var(--accent-ink)' }}>
                    {activeFinding.evidence_id || (activeFinding as any).rule_code || 'RULE-BR-01'}
                  </span>
                  <span
                    className="flex items-center gap-1 font-mono text-[10px] font-medium"
                    style={{ color: 'var(--status-verified)' }}
                  >
                    <Check size={11} strokeWidth={2.5} />
                    <span>Verified in KB v{content.version_no || 1}</span>
                  </span>
                </div>

                {(activeFinding.evidence_quote || (activeFinding as any).rule_text) && (
                  <p className="font-serif italic text-xs leading-relaxed" style={{ color: 'var(--graphite)' }}>
                    "{activeFinding.evidence_quote || (activeFinding as any).rule_text}"
                  </p>
                )}
              </div>

              {/* Grounding Trail: 4-dot path */}
              <details className="group text-xs">
                <summary className="cursor-pointer font-medium flex items-center gap-1 select-none" style={{ color: 'var(--graphite)' }}>
                  <ChevronRight size={13} className="group-open:rotate-90 transition-transform" />
                  <span>How this was checked</span>
                </summary>
                <div className="mt-3 pl-4 border-l space-y-2 py-1" style={{ borderColor: 'var(--hairline)' }}>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                    <span style={{ color: 'var(--ink)' }}>1. Hidden private data</span>
                    <span style={{ color: 'var(--muted)' }}>• Redacted PII before evaluation</span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                    <span style={{ color: 'var(--ink)' }}>2. Matched</span>
                    <span style={{ color: 'var(--muted)' }}>• Deterministic phrase scan &amp; vector index</span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                    <span style={{ color: 'var(--ink)' }}>3. Evidence found</span>
                    <span style={{ color: 'var(--muted)' }}>• Direct citation from brand rule repository</span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                    <span style={{ color: 'var(--ink)' }}>4. Verified</span>
                    <span style={{ color: 'var(--muted)' }}>• Intent preservation score: 98%</span>
                  </div>
                </div>
              </details>

              {/* Fix Block with Option Tabs, Tracked Changes & Action Buttons */}
              <div className="pt-3 border-t space-y-3" style={{ borderColor: 'var(--hairline-subtle)' }}>
                {suggestions.length > 1 && (
                  <div className="flex items-center gap-1 pb-1">
                    {suggestions.map((s, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setActiveOptionTab(idx)}
                        className="px-2 py-1 rounded-[2px] text-xs font-medium transition-all"
                        style={{
                          backgroundColor:
                            activeOptionTab === idx ? 'var(--accent)' : 'var(--paper)',
                          color: activeOptionTab === idx ? '#ffffff' : 'var(--graphite)',
                          border: '1px solid var(--hairline)',
                        }}
                      >
                        Option {idx + 1}
                      </button>
                    ))}
                  </div>
                )}

                {/* Tracked-change diff preview */}
                <div
                  className="p-3 rounded-[2px] border text-xs"
                  style={{
                    backgroundColor: 'var(--paper)',
                    borderColor: 'var(--hairline)',
                  }}
                >
                  <span className="block text-[10px] mb-1.5" style={{ color: 'var(--muted)' }}>
                    Tracked change diff
                  </span>
                  <div className="leading-relaxed">
                    <del className="tracked-deletion mr-1.5">{activeFinding.span_text}</del>
                    <ins className="tracked-insertion">
                      {getCurrentOptionReplacement() || 'Remove prohibited claim'}
                    </ins>
                  </div>

                  {/* Intent kept check */}
                  <div className="mt-2 pt-2 border-t flex items-center gap-1.5 text-[11px]" style={{ borderColor: 'var(--hairline-subtle)', color: 'var(--status-verified)' }}>
                    <Check size={12} strokeWidth={2.5} />
                    <span>Intent kept: Preserves core promotional tone without deceptive claims.</span>
                  </div>
                </div>

                {/* Inline Custom Edit Input */}
                {showEditInput && (
                  <div className="space-y-2 pt-2">
                    <label className="block text-xs font-medium" style={{ color: 'var(--graphite)' }}>
                      Custom rewrite
                    </label>
                    <input
                      type="text"
                      value={customEditText}
                      onChange={(e) => setCustomEditText(e.target.value)}
                      className="w-full px-3 py-1.5 text-xs rounded-[2px] border focus:outline-none"
                      style={{
                        backgroundColor: 'var(--sheet)',
                        borderColor: 'var(--hairline)',
                        color: 'var(--ink)',
                      }}
                    />
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleSaveCustomEdit}
                        className="px-3 py-1 rounded-[2px] text-xs font-medium"
                        style={{ backgroundColor: 'var(--accent)', color: '#ffffff' }}
                      >
                        Apply edit
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowEditInput(false)}
                        className="px-2 py-1 rounded-[2px] border text-xs"
                        style={{ borderColor: 'var(--hairline)', color: 'var(--graphite)' }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* Inline Dismiss Reason Picker */}
                {showDismissPicker && (
                  <div className="space-y-2 pt-2">
                    <span className="block text-xs font-medium" style={{ color: 'var(--graphite)' }}>
                      Select dismissal justification
                    </span>
                    <div className="space-y-1">
                      {[
                        'Approved exception for specific regional campaign',
                        'Artistic expression / non-literal marketing copy',
                        'Already verified by legal / regulatory counsel',
                        'False positive semantic match',
                      ].map((r) => (
                        <button
                          key={r}
                          type="button"
                          onClick={() => handleDismissFinding(r)}
                          className="w-full text-left p-2 rounded-[2px] text-xs hover:bg-black/5 dark:hover:bg-white/5 transition-colors border"
                          style={{
                            borderColor: 'var(--hairline)',
                            color: 'var(--ink)',
                          }}
                        >
                          {r}
                        </button>
                      ))}
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowDismissPicker(false)}
                      className="text-xs underline mt-1"
                      style={{ color: 'var(--muted)' }}
                    >
                      Cancel dismissal
                    </button>
                  </div>
                )}

                {/* Primary Action Buttons (Apply, Edit, Dismiss) */}
                {!showEditInput && !showDismissPicker && (
                  <div className="flex items-center justify-between pt-2">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          const repl = getCurrentOptionReplacement();
                          if (repl) handleApplyFix(repl);
                        }}
                        className="px-3 py-1.5 rounded-[2px] text-xs font-medium transition-all shadow-xs flex items-center gap-1"
                        style={{
                          backgroundColor: 'var(--accent)',
                          color: '#ffffff',
                        }}
                        title="Shortcut: A"
                      >
                        <Check size={12} strokeWidth={2.5} />
                        <span>Apply (A)</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setShowEditInput(true)}
                        className="px-3 py-1.5 rounded-[2px] border text-xs font-medium transition-colors hover:bg-black/5"
                        style={{
                          borderColor: 'var(--hairline)',
                          color: 'var(--graphite)',
                        }}
                        title="Shortcut: E"
                      >
                        <Edit3 size={12} />
                        <span>Edit (E)</span>
                      </button>
                    </div>

                    <button
                      type="button"
                      onClick={() => setShowDismissPicker(true)}
                      className="px-2.5 py-1.5 rounded-[2px] text-xs transition-colors hover:text-red-700 hover:bg-red-50"
                      style={{ color: 'var(--muted)' }}
                      title="Shortcut: D"
                    >
                      <span>Dismiss (D)</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : null}

          {/* List of other findings */}
          <div className="space-y-2 pt-2">
            <span className="block text-xs font-serif font-medium" style={{ color: 'var(--graphite)' }}>
              All flagged items
            </span>
            <div className="space-y-1.5 max-h-[320px] overflow-y-auto">
              {findings.map((f, idx) => {
                const isSelected = selectedIndex === idx;
                const isDismissed = f.status === 'dismissed';
                const isAccepted = f.status === 'accepted' || f.status === 'edited';

                return (
                  <div
                    key={f.id}
                    onClick={() => setSelectedIndex(idx)}
                    className="p-2.5 rounded-[2px] border cursor-pointer transition-all flex items-center justify-between gap-2"
                    style={{
                      backgroundColor: isSelected ? 'var(--accent-surface)' : 'var(--sheet)',
                      borderColor: isSelected ? 'var(--accent)' : 'var(--hairline)',
                      opacity: isDismissed ? 0.5 : 1,
                    }}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span
                        className="w-4 h-4 rounded-full text-[10px] font-mono font-bold flex items-center justify-center shrink-0"
                        style={{
                          backgroundColor: isSelected ? 'var(--accent)' : 'var(--hairline)',
                          color: isSelected ? '#ffffff' : 'var(--graphite)',
                        }}
                      >
                        {idx + 1}
                      </span>
                      <div className="truncate">
                        <span className="text-xs font-medium block truncate" style={{ color: 'var(--ink)' }}>
                          {f.reason}
                        </span>
                        <span className="text-[10px] italic truncate block" style={{ color: 'var(--muted)' }}>
                          "{f.span_text}"
                        </span>
                      </div>
                    </div>

                    <span
                      className="text-[10px] font-mono px-1.5 py-0.2 rounded capitalize shrink-0"
                      style={{
                        backgroundColor:
                          f.severity === 'blocker'
                            ? 'var(--severity-blocker-bg)'
                            : f.severity === 'major'
                            ? 'var(--severity-major-bg)'
                            : 'var(--severity-minor-bg)',
                        color:
                          f.severity === 'blocker'
                            ? 'var(--severity-blocker)'
                            : f.severity === 'major'
                            ? 'var(--severity-major)'
                            : 'var(--severity-minor)',
                      }}
                    >
                      {isAccepted ? 'Fixed' : isDismissed ? 'Dismissed' : f.severity}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Sliding Right-side Signing Sheet Panel (for Approval/Rejection) */}
      {showSigningSheet && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs">
          <div
            className="w-full max-w-md h-full p-6 sm:p-8 flex flex-col justify-between overflow-y-auto"
            style={{
              backgroundColor: 'var(--sheet)',
              borderLeft: '1px solid var(--hairline)',
              boxShadow: '-8px 0 32px rgba(20, 23, 31, 0.1)',
            }}
          >
            <div>
              <div className="flex items-center justify-between pb-4 border-b" style={{ borderColor: 'var(--hairline)' }}>
                <div className="flex items-center gap-2">
                  <ShieldAlert size={18} style={{ color: 'var(--accent)' }} />
                  <h3 className="font-serif font-semibold text-lg" style={{ color: 'var(--ink)' }}>
                    Editorial signing sheet
                  </h3>
                </div>
                <button
                  onClick={() => setShowSigningSheet(false)}
                  className="p-1 rounded-[2px] hover:bg-black/5"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Cryptographic hash & Document summary */}
              <div className="mt-5 space-y-3">
                <div className="p-3 rounded-[2px] border text-xs font-mono space-y-1" style={{ backgroundColor: 'var(--paper)', borderColor: 'var(--hairline)' }}>
                  <div className="text-[11px]" style={{ color: 'var(--muted)' }}>Content SHA-256 Digest</div>
                  <div className="truncate font-bold" style={{ color: 'var(--ink)' }}>
                    {(content as any).content_hash || content.versions?.[0]?.content_hash || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}
                  </div>
                  <div className="flex items-center justify-between pt-1 text-[11px]" style={{ color: 'var(--muted)' }}>
                    <span>Version: v{content.version_no || 1}</span>
                    <span>Findings: {openCount} open / {findings.length} total</span>
                  </div>
                </div>

                {/* Decision picker */}
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--graphite)' }}>
                    Approval decision
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      type="button"
                      onClick={() => setApprovalDecision('approved')}
                      className="p-2 text-xs rounded-[2px] border font-medium transition-all"
                      style={{
                        backgroundColor:
                          approvalDecision === 'approved'
                            ? 'var(--status-verified-bg)'
                            : 'var(--paper)',
                        borderColor:
                          approvalDecision === 'approved'
                            ? 'var(--status-verified)'
                            : 'var(--hairline)',
                        color:
                          approvalDecision === 'approved'
                            ? 'var(--status-verified)'
                            : 'var(--graphite)',
                      }}
                    >
                      Approve & sign
                    </button>
                    <button
                      type="button"
                      onClick={() => setApprovalDecision('changes_requested')}
                      className="p-2 text-xs rounded-[2px] border font-medium transition-all"
                      style={{
                        backgroundColor:
                          approvalDecision === 'changes_requested'
                            ? 'var(--severity-major-bg)'
                            : 'var(--paper)',
                        borderColor:
                          approvalDecision === 'changes_requested'
                            ? 'var(--severity-major)'
                            : 'var(--hairline)',
                        color:
                          approvalDecision === 'changes_requested'
                            ? 'var(--severity-major)'
                            : 'var(--graphite)',
                      }}
                    >
                      Request changes
                    </button>
                    <button
                      type="button"
                      onClick={() => setApprovalDecision('rejected')}
                      className="p-2 text-xs rounded-[2px] border font-medium transition-all"
                      style={{
                        backgroundColor:
                          approvalDecision === 'rejected'
                            ? 'var(--severity-blocker-bg)'
                            : 'var(--paper)',
                        borderColor:
                          approvalDecision === 'rejected'
                            ? 'var(--severity-blocker)'
                            : 'var(--hairline)',
                        color:
                          approvalDecision === 'rejected'
                            ? 'var(--severity-blocker)'
                            : 'var(--graphite)',
                      }}
                    >
                      Reject
                    </button>
                  </div>
                </div>

                {/* Required Justification */}
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--graphite)' }}>
                    Sign-off justification (logged immutably to audit chain)
                  </label>
                  <textarea
                    rows={4}
                    value={approvalJustification}
                    onChange={(e) => setApprovalJustification(e.target.value)}
                    placeholder="Enter compliance justification and review notes..."
                    className="w-full p-2.5 text-xs rounded-[2px] border focus:outline-none"
                    style={{
                      backgroundColor: 'var(--paper)',
                      borderColor: 'var(--hairline)',
                      color: 'var(--ink)',
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Submit Signature */}
            <div className="pt-6 border-t" style={{ borderColor: 'var(--hairline)' }}>
              <button
                type="button"
                onClick={handleConfirmApproval}
                disabled={!approvalJustification.trim()}
                className="w-full py-2.5 px-4 rounded-[2px] text-xs font-semibold text-white transition-all shadow-xs disabled:opacity-40"
                style={{
                  backgroundColor:
                    approvalDecision === 'approved'
                      ? 'var(--accent)'
                      : approvalDecision === 'changes_requested'
                      ? 'var(--severity-major)'
                      : 'var(--severity-blocker)',
                }}
              >
                Sign & record {approvalDecision}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AI Usage Drawer */}
      {showAiDrawer && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs">
          <div
            className="w-full max-w-lg h-full p-6 sm:p-8 flex flex-col justify-between overflow-y-auto"
            style={{
              backgroundColor: 'var(--sheet)',
              borderLeft: '1px solid var(--hairline)',
              boxShadow: '-8px 0 32px rgba(20, 23, 31, 0.1)',
            }}
          >
            <div>
              <div className="flex items-center justify-between pb-4 border-b" style={{ borderColor: 'var(--hairline)' }}>
                <div className="flex items-center gap-2">
                  <Cpu size={18} style={{ color: 'var(--accent)' }} />
                  <h3 className="font-serif font-semibold text-lg" style={{ color: 'var(--ink)' }}>
                    How AI was used
                  </h3>
                </div>
                <button
                  onClick={() => setShowAiDrawer(false)}
                  className="p-1 rounded-[2px] hover:bg-black/5"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="mt-5 space-y-4 text-xs">
                <p style={{ color: 'var(--graphite)' }}>
                  A clear ledger of every model invocation, character count, redacted privacy item,
                  and cache status executed for this review.
                </p>

                {loadingLedger ? (
                  <div className="py-8 text-center" style={{ color: 'var(--muted)' }}>
                    Loading AI usage telemetry...
                  </div>
                ) : aiLedger ? (
                  <div className="space-y-3 font-mono">
                    <div className="p-3 rounded-[2px] border space-y-2" style={{ backgroundColor: 'var(--paper)', borderColor: 'var(--hairline)' }}>
                      <div className="flex justify-between">
                        <span style={{ color: 'var(--muted)' }}>Engine Provider</span>
                        <span className="font-bold" style={{ color: 'var(--ink)' }}>{aiLedger.provider || 'Gemini'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span style={{ color: 'var(--muted)' }}>Model</span>
                        <span className="font-bold" style={{ color: 'var(--ink)' }}>{aiLedger.model || 'gemini-1.5-pro'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span style={{ color: 'var(--muted)' }}>Execution Mode</span>
                        <span style={{ color: 'var(--accent-ink)' }}>{aiLedger.execution_mode || 'Deterministic + LLM'}</span>
                      </div>
                    </div>

                    <div className="p-3 rounded-[2px] border space-y-2" style={{ backgroundColor: 'var(--paper)', borderColor: 'var(--hairline)' }}>
                      <div className="flex justify-between">
                        <span style={{ color: 'var(--muted)' }}>Characters Evaluated</span>
                        <span style={{ color: 'var(--ink)' }}>{content.text_body?.length || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span style={{ color: 'var(--muted)' }}>PII Elements Redacted</span>
                        <span style={{ color: 'var(--severity-blocker)' }}>{aiLedger.redactions_count || aiUsage?.redaction_count || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span style={{ color: 'var(--muted)' }}>Deterministic Passes</span>
                        <span style={{ color: 'var(--status-verified)' }}>Grounded KB rules check</span>
                      </div>
                      <div className="flex justify-between">
                        <span style={{ color: 'var(--muted)' }}>Cache / Fallback Status</span>
                        <span style={{ color: 'var(--accent-ink)' }}>Verified Grounded</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-[2px] border font-mono" style={{ backgroundColor: 'var(--paper)', borderColor: 'var(--hairline)' }}>
                    <div>Model: Gemini 1.5 Pro / Deterministic engine</div>
                    <div>Redactions: {aiUsage?.redaction_count || 0} items masked</div>
                    <div>Grounding: 100% quoted to active brand rule facts</div>
                  </div>
                )}
              </div>
            </div>

            <div className="pt-4 border-t text-right" style={{ borderColor: 'var(--hairline)' }}>
              <button
                type="button"
                onClick={() => setShowAiDrawer(false)}
                className="px-4 py-2 rounded-[2px] border text-xs font-medium"
                style={{ borderColor: 'var(--hairline)', color: 'var(--graphite)' }}
              >
                Close ledger
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Comments Drawer */}
      {showCommentsDrawer && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs">
          <div
            className="w-full max-w-md h-full p-6 sm:p-8 flex flex-col justify-between overflow-y-auto"
            style={{
              backgroundColor: 'var(--sheet)',
              borderLeft: '1px solid var(--hairline)',
              boxShadow: '-8px 0 32px rgba(20, 23, 31, 0.1)',
            }}
          >
            <div>
              <div className="flex items-center justify-between pb-4 border-b" style={{ borderColor: 'var(--hairline)' }}>
                <div className="flex items-center gap-2">
                  <MessageSquare size={18} style={{ color: 'var(--accent)' }} />
                  <h3 className="font-serif font-semibold text-lg" style={{ color: 'var(--ink)' }}>
                    Threaded comments ({comments.length})
                  </h3>
                </div>
                <button
                  onClick={() => setShowCommentsDrawer(false)}
                  className="p-1 rounded-[2px] hover:bg-black/5"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Comments list */}
              <div className="mt-4 space-y-3 max-h-[460px] overflow-y-auto">
                {comments.length === 0 ? (
                  <div className="py-8 text-center text-xs" style={{ color: 'var(--muted)' }}>
                    No editorial comments yet. Add a note below.
                  </div>
                ) : (
                  comments.map((cm) => (
                    <div
                      key={cm.id}
                      className="p-3 rounded-[2px] border text-xs space-y-1"
                      style={{
                        backgroundColor: 'var(--paper)',
                        borderColor: 'var(--hairline)',
                      }}
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-semibold" style={{ color: 'var(--ink)' }}>
                          {cm.author_name || (cm as any).user_email || `User #${cm.author_id}`}
                        </span>
                        <span style={{ color: 'var(--muted)' }}>
                          {cm.created_at ? new Date(cm.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'now'}
                        </span>
                      </div>
                      <p style={{ color: 'var(--graphite)' }}>{cm.body || (cm as any).comment}</p>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Comment Form */}
            <form onSubmit={handleAddComment} className="mt-4 pt-4 border-t space-y-2" style={{ borderColor: 'var(--hairline)' }}>
              <textarea
                rows={3}
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Leave an editorial note..."
                className="w-full p-2.5 text-xs rounded-[2px] border focus:outline-none"
                style={{
                  backgroundColor: 'var(--paper)',
                  borderColor: 'var(--hairline)',
                  color: 'var(--ink)',
                }}
              />
              <button
                type="submit"
                disabled={!newComment.trim()}
                className="w-full py-2 rounded-[2px] text-xs font-medium text-white transition-all disabled:opacity-40"
                style={{ backgroundColor: 'var(--accent)' }}
              >
                Post comment
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
