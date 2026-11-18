import React, { useState, useEffect } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  FileCheck,
  Check,
  X,
  MessageSquare,
  ArrowRight,
  ShieldAlert,
  Send,
  History,
  Scale,
  Sparkles,
  Edit3,
  RefreshCw,
  Clock,
  Layers,
  Lock,
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
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [suggestions, setSuggestions] = useState<VerifiedSuggestion[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [reReviewing, setReReviewing] = useState(false);
  const [activeTab, setActiveTab] = useState<'findings' | 'claims' | 'comments' | 'versions'>('findings');
  
  // Modals & custom edits
  const [dismissReason, setDismissReason] = useState('');
  const [showDismissModal, setShowDismissModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [customEditText, setCustomEditText] = useState('');
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [approvalDecision, setApprovalDecision] = useState<'approved' | 'changes_requested' | 'rejected'>('approved');
  const [approvalNote, setApprovalNote] = useState('');
  const [approvalResult, setApprovalResult] = useState<any>(null);
  const [actionAlert, setActionAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Load content & existing review without duplicate runs
  const loadData = async (forceReview = false) => {
    if (!contentId) return;
    try {
      setLoading(true);
      setActionAlert(null);

      const c = await api.getContent(contentId);
      setContent(c);

      let rev: ReviewResponse;
      if (forceReview) {
        rev = await api.reviewContent(contentId);
      } else {
        rev = await api.getReview(contentId);
        // If content has not been reviewed yet, perform first review
        if (!rev.has_review && (!rev.findings || rev.findings.length === 0)) {
          rev = await api.reviewContent(contentId);
        }
      }

      setFindings(rev.findings || []);
      setReviewInfo(rev.review || null);
      setAiUsage(rev.ai_usage || null);

      // Claims & Comments
      const [cl, cm] = await Promise.all([
        api.getClaims(contentId).catch(() => ({ claims: [] })),
        api.getComments(contentId).catch(() => []),
      ]);
      setClaims(cl.claims || []);
      setComments(cm || []);
    } catch (err: any) {
      console.error(err);
      setActionAlert({ type: 'error', message: err.message || 'Error loading review data' });
    } finally {
      setLoading(false);
      setReReviewing(false);
    }
  };

  useEffect(() => {
    loadData(false);
  }, [contentId]);

  const handleSelectFinding = async (f: Finding) => {
    setSelectedFinding(f);
    setCustomEditText(f.selected_replacement || f.suggestion_text || f.span_text);
    if (f.status === 'open' || !f.status) {
      try {
        setLoadingSuggestions(true);
        const res = await api.getSuggestions(contentId, f.id);
        setSuggestions(res.suggestions || []);
      } catch {
        setSuggestions([]);
      } finally {
        setLoadingSuggestions(false);
      }
    } else {
      setSuggestions([]);
    }
  };

  const handleAcceptSuggestion = async (replacement: string) => {
    if (!selectedFinding) return;
    try {
      setActionAlert(null);
      await api.acceptSuggestion(contentId, selectedFinding.id, replacement);
      setActionAlert({
        type: 'success',
        message: `Accepted replacement! Created new revised Content Version (v2).`,
      });
      await loadData(false);
      setSelectedFinding(null);
      setSuggestions([]);
      onRefreshContent();
    } catch (err: any) {
      setActionAlert({ type: 'error', message: err.message || 'Error accepting suggestion' });
    }
  };

  const handleSaveCustomEdit = async () => {
    if (!selectedFinding || !customEditText.trim()) return;
    try {
      setActionAlert(null);
      await api.editFinding(contentId, selectedFinding.id, customEditText.trim());
      setShowEditModal(false);
      setActionAlert({
        type: 'success',
        message: `Custom rewrite applied! Created new revised Content Version.`,
      });
      await loadData(false);
      setSelectedFinding(null);
      onRefreshContent();
    } catch (err: any) {
      setActionAlert({ type: 'error', message: err.message || 'Error saving custom edit' });
    }
  };

  const handleDismissFinding = async () => {
    if (!selectedFinding || !dismissReason.trim()) return;
    try {
      setActionAlert(null);
      await api.dismissFinding(contentId, selectedFinding.id, dismissReason.trim());
      setShowDismissModal(false);
      setDismissReason('');
      setActionAlert({
        type: 'success',
        message: `Finding #${selectedFinding.id} dismissed with justification. Logged to audit trail.`,
      });
      await loadData(false);
      setSelectedFinding(null);
    } catch (err: any) {
      setActionAlert({ type: 'error', message: err.message || 'Error dismissing finding' });
    }
  };

  const handleSubmitForReview = async () => {
    try {
      setActionAlert(null);
      const res = await api.submitContent(contentId);
      setContent((prev: any) => ({ ...prev, status: res.status }));
      if (res.escalated) {
        setActionAlert({
          type: 'error',
          message: `ESCALATED: Submitted to Authorised Reviewer queue.\nReason: ${res.escalation_reason}`,
        });
      } else {
        setActionAlert({
          type: 'success',
          message: 'Draft submitted successfully to Manager Review queue.',
        });
      }
      await loadData(false);
    } catch (err: any) {
      setActionAlert({ type: 'error', message: err.message || 'Submission error' });
    }
  };

  const openApprovalModal = (decision: 'approved' | 'changes_requested' | 'rejected') => {
    setApprovalDecision(decision);
    if (decision === 'approved') {
      setApprovalNote('Verified compliant with brand guidelines and approved for publication.');
    } else if (decision === 'changes_requested') {
      setApprovalNote('Please address flagged brand guidelines and resubmit.');
    } else {
      setApprovalNote('Rejected: Content does not meet required brand compliance standards.');
    }
    setShowApprovalModal(true);
  };

  const handleConfirmApproval = async () => {
    try {
      setActionAlert(null);
      const res = await api.approveContent(contentId, approvalDecision, approvalNote.trim());
      setApprovalResult(res);
      setShowApprovalModal(false);
      setContent((prev: any) => ({ ...prev, status: res.status }));
      setActionAlert({
        type: 'success',
        message: `Decision recorded: [${approvalDecision.toUpperCase()}]. Status: ${res.status}. Cryptographic Signature: ${res.signature_hash.slice(0, 16)}...`,
      });
      await loadData(false);
    } catch (err: any) {
      setShowApprovalModal(false);
      setActionAlert({ type: 'error', message: err.message || 'Approval action failed' });
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    try {
      await api.addComment(contentId, newComment.trim(), selectedFinding?.id);
      setNewComment('');
      const cm = await api.getComments(contentId);
      setComments(cm || []);
    } catch (err: any) {
      setActionAlert({ type: 'error', message: err.message || 'Failed to post comment' });
    }
  };

  // Render text with interactive spans
  const renderHighlightedText = () => {
    const text = content?.text_body || '';
    if (!text) return <span className="text-slate-400 italic">No text body available.</span>;

    // Filter and sort findings that have valid spans
    const validFindings = findings
      .filter((f) => {
        const s = f.span ? f.span.start : f.span_start;
        const e = f.span ? f.span.end : f.span_end;
        return typeof s === 'number' && typeof e === 'number' && e > s && s >= 0 && e <= text.length;
      })
      .sort((a, b) => {
        const sa = a.span ? a.span.start : a.span_start;
        const sb = b.span ? b.span.start : b.span_start;
        return sa - sb;
      });

    if (validFindings.length === 0) {
      return <span>{text}</span>;
    }

    const elements: React.ReactNode[] = [];
    let lastIndex = 0;

    validFindings.forEach((f, idx) => {
      const start = f.span ? f.span.start : f.span_start;
      const end = f.span ? f.span.end : f.span_end;

      if (start > lastIndex) {
        elements.push(
          <span key={`text-${lastIndex}`}>{text.substring(lastIndex, start)}</span>
        );
      }

      const isSelected = selectedFinding?.id === f.id;
      const isAccepted = f.status === 'accepted' || f.status === 'edited';
      const isDismissed = f.status === 'dismissed';

      let bgClass = 'bg-yellow-200 text-yellow-950 border-yellow-400';
      if (f.severity === 'blocker') {
        bgClass = 'bg-red-200 text-red-950 border-red-500 font-bold';
      } else if (f.severity === 'major') {
        bgClass = 'bg-amber-200 text-amber-950 border-amber-500 font-semibold';
      }

      if (isAccepted) {
        bgClass = 'bg-emerald-100 text-emerald-900 border-emerald-400 line-through';
      } else if (isDismissed) {
        bgClass = 'bg-slate-200 text-slate-600 border-slate-300 line-through';
      }

      elements.push(
        <mark
          key={`finding-${f.id}-${idx}`}
          onClick={() => handleSelectFinding(f)}
          title={`[${f.severity.toUpperCase()}] ${f.category}: ${f.reason}`}
          className={`px-1 py-0.5 rounded cursor-pointer border transition-all ${bgClass} ${
            isSelected ? 'ring-2 ring-blue-600 ring-offset-1 shadow-md' : 'hover:opacity-80'
          }`}
        >
          {text.substring(start, end)}
          {isAccepted && (
            <span className="no-underline ml-1 text-[10px] font-mono font-bold text-emerald-800 bg-emerald-200 px-1 rounded">
              ✓ {f.selected_replacement}
            </span>
          )}
        </mark>
      );

      lastIndex = Math.max(lastIndex, end);
    });

    if (lastIndex < text.length) {
      elements.push(<span key={`text-${lastIndex}`}>{text.substring(lastIndex)}</span>);
    }

    return elements;
  };

  const renderSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'blocker':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-bold bg-red-100 text-red-900 border border-red-300">
            <AlertOctagon className="w-3.5 h-3.5 text-red-700" />
            <span>BLOCKER</span>
          </span>
        );
      case 'major':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
            <span>MAJOR</span>
          </span>
        );
      case 'minor':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-bold bg-yellow-100 text-yellow-900 border border-yellow-300">
            <Info className="w-3.5 h-3.5 text-yellow-700" />
            <span>MINOR</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-bold bg-slate-100 text-slate-800 border border-slate-300">
            <Info className="w-3.5 h-3.5 text-slate-600" />
            <span>INFO</span>
          </span>
        );
    }
  };

  const renderStatusBadge = (status?: string) => {
    switch (status) {
      case 'accepted':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">
            Accepted
          </span>
        );
      case 'edited':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-100 text-blue-800 border border-blue-300">
            Edited
          </span>
        );
      case 'dismissed':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-200 text-slate-700 border border-slate-300">
            Dismissed
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-50 text-amber-800 border border-amber-300">
            Open
          </span>
        );
    }
  };

  if (loading && !content) {
    return (
      <div className="py-20 text-center text-slate-500 text-sm flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
        <span>Loading brand review workspace...</span>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="py-16 text-center text-slate-500 text-sm">
        Select or submit a draft copy from the Submissions screen to inspect review findings.
      </div>
    );
  }

  const openFindingsCount = findings.filter((f) => !f.status || f.status === 'open').length;

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 space-y-6">
      {/* Top Banner: Status, Metadata & Actions */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold text-slate-900">{content.title}</h1>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase font-mono border ${
                content.status === 'approved'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                  : content.status === 'in_review' || content.status === 'ai_checked'
                  ? 'bg-blue-50 text-blue-800 border-blue-300'
                  : content.status === 'changes_requested'
                  ? 'bg-amber-50 text-amber-800 border-amber-300'
                  : 'bg-slate-100 text-slate-700 border-slate-300'
              }`}
            >
              {content.status}
            </span>
            <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
              Version {content.version_no || 1}
            </span>
          </div>

          <div className="flex items-center space-x-4 text-xs text-slate-500 mt-1">
            <span>Creator: <strong className="text-slate-700">{content.creator_name || content.creator_email || 'Author'}</strong></span>
            <span>•</span>
            <span>Channel: <strong className="text-slate-700">{content.channel}</strong></span>
            <span>•</span>
            <span>Findings: <strong className="text-slate-700">{openFindingsCount} open</strong> / {findings.length} total</span>
            {aiUsage && (
              <>
                <span>•</span>
                <span className="text-purple-700 font-mono">
                  {aiUsage.redaction_count} PII elements redacted
                </span>
              </>
            )}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              setReReviewing(true);
              loadData(true);
            }}
            disabled={reReviewing}
            title="Explicitly rerun grounding verification checks"
            className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg border border-slate-300 transition-colors flex items-center space-x-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reReviewing ? 'animate-spin' : ''}`} />
            <span>Re-verify</span>
          </button>

          {currentUser?.role === 'creator' && (
            <button
              onClick={handleSubmitForReview}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center space-x-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Submit for Approval</span>
            </button>
          )}

          {(currentUser?.role === 'manager' ||
            currentUser?.role === 'reviewer' ||
            currentUser?.role === 'admin') && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => openApprovalModal('approved')}
                className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center space-x-1"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Approve & Sign</span>
              </button>
              <button
                onClick={() => openApprovalModal('changes_requested')}
                className="px-3.5 py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
              >
                Request Changes
              </button>
              <button
                onClick={() => openApprovalModal('rejected')}
                className="px-3.5 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
              >
                Reject
              </button>
            </div>
          )}
        </div>
      </div>

      {actionAlert && (
        <div
          className={`p-4 rounded-xl border flex items-center space-x-2.5 text-xs font-medium ${
            actionAlert.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
              : 'bg-red-50 border-red-200 text-red-900'
          }`}
        >
          {actionAlert.type === 'success' ? (
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          )}
          <span className="whitespace-pre-line">{actionAlert.message}</span>
        </div>
      )}

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Interactive Highlighted Draft Copy */}
        <div className="lg:col-span-6 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                Draft Review Canvas
              </h2>
              <p className="text-[11px] text-slate-400">
                Click highlighted text to inspect grounding evidence and verified alternatives.
              </p>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {content.text_body?.length || 0} characters
            </span>
          </div>

          <div className="text-sm font-mono leading-relaxed p-4 bg-slate-50/80 border border-slate-200 rounded-lg whitespace-pre-wrap select-text">
            {renderHighlightedText()}
          </div>
        </div>

        {/* Right: Findings, Claims Ledger, Comments, Versions */}
        <div className="lg:col-span-6 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col">
          {/* Subtabs */}
          <div className="flex border-b border-slate-200 px-4 pt-3 space-x-4 overflow-x-auto">
            <button
              onClick={() => setActiveTab('findings')}
              className={`pb-2.5 text-xs font-bold uppercase transition-colors border-b-2 whitespace-nowrap ${
                activeTab === 'findings'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              Findings ({openFindingsCount} open / {findings.length})
            </button>
            <button
              onClick={() => setActiveTab('claims')}
              className={`pb-2.5 text-xs font-bold uppercase transition-colors border-b-2 whitespace-nowrap ${
                activeTab === 'claims'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              Claim Ledger ({claims.length})
            </button>
            <button
              onClick={() => setActiveTab('comments')}
              className={`pb-2.5 text-xs font-bold uppercase transition-colors border-b-2 whitespace-nowrap ${
                activeTab === 'comments'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              Comments ({comments.length})
            </button>
            <button
              onClick={() => setActiveTab('versions')}
              className={`pb-2.5 text-xs font-bold uppercase transition-colors border-b-2 whitespace-nowrap ${
                activeTab === 'versions'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              Versions ({content.versions?.length || 1})
            </button>
          </div>

          <div className="p-4 flex-1 overflow-y-auto max-h-[640px] space-y-4">
            {/* FINDINGS TAB */}
            {activeTab === 'findings' && (
              <div className="space-y-3">
                {findings.length === 0 ? (
                  <div className="text-center py-12 text-xs text-slate-400">
                    <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                    <span className="font-semibold text-slate-600 block text-sm">
                      Zero Brand Violations Detected
                    </span>
                    <span>All content strictly adheres to active brand guidelines and verified facts.</span>
                  </div>
                ) : (
                  findings.map((f) => {
                    const isSelected = selectedFinding?.id === f.id;
                    const evidenceQuote = f.evidence?.quote || f.evidence_quote;
                    const evidenceId = f.evidence?.id || f.evidence_id;

                    return (
                      <div
                        key={f.id}
                        onClick={() => handleSelectFinding(f)}
                        className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${
                          isSelected
                            ? 'border-blue-500 bg-blue-50/50 shadow-sm ring-1 ring-blue-500'
                            : 'border-slate-200 hover:border-slate-300 bg-white'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            {renderSeverityBadge(f.severity)}
                            <span className="font-bold uppercase tracking-wider text-slate-700 text-[11px]">
                              {f.category}
                            </span>
                          </div>
                          <div className="flex items-center space-x-2">
                            {renderStatusBadge(f.status)}
                            <span className="text-[10px] font-mono text-slate-400">
                              {(Number(f.confidence) * 100).toFixed(0)}% conf
                            </span>
                          </div>
                        </div>

                        <div className="text-slate-800 font-medium my-1.5">
                          Span: <span className="font-mono bg-red-50 text-red-700 px-1.5 py-0.5 rounded font-bold border border-red-200">"{f.span_text}"</span>
                        </div>
                        <div className="text-slate-600 leading-relaxed">{f.reason}</div>

                        {evidenceQuote && (
                          <div className="mt-2.5 p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-slate-600 font-mono text-[11px] leading-snug">
                            <strong className="text-slate-800 block text-[10px] uppercase font-bold text-blue-600">
                              Grounded Source Evidence [{evidenceId || 'Rule'}]:
                            </strong>
                            "{evidenceQuote}"
                          </div>
                        )}

                        {/* Status detail when decided */}
                        {f.status === 'accepted' || f.status === 'edited' ? (
                          <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-emerald-800">
                            <span>Replacement: <strong>"{f.selected_replacement}"</strong></span>
                            <span className="text-slate-400">Decided by User #{f.decided_by}</span>
                          </div>
                        ) : f.status === 'dismissed' ? (
                          <div className="mt-2 pt-2 border-t border-slate-100 text-[11px] text-slate-500">
                            Dismissal Reason: <em>"{f.dismissal_reason}"</em>
                          </div>
                        ) : null}
                      </div>
                    );
                  })
                )}

                {/* Verified Suggestions Panel (Improvement I-1) */}
                {selectedFinding && (
                  <div className="mt-4 p-4 bg-blue-50/70 border border-blue-200 rounded-xl space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-1.5">
                        <Sparkles className="w-4 h-4 text-blue-600" />
                        <span className="text-xs font-bold text-blue-900 uppercase">
                          I-1: Verified Alternatives for Finding #{selectedFinding.id}
                        </span>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setShowEditModal(true)}
                          className="text-xs text-blue-700 hover:underline font-semibold flex items-center space-x-1"
                        >
                          <Edit3 className="w-3 h-3" />
                          <span>Custom Edit...</span>
                        </button>
                        <button
                          onClick={() => setShowDismissModal(true)}
                          className="text-xs text-red-600 hover:underline font-semibold"
                        >
                          Dismiss...
                        </button>
                      </div>
                    </div>

                    {loadingSuggestions ? (
                      <div className="text-xs text-slate-500 flex items-center space-x-2 py-2">
                        <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-600" />
                        <span>Generating intent-preserving candidates & verifying diffs...</span>
                      </div>
                    ) : suggestions.length === 0 ? (
                      <div className="text-xs text-slate-500">
                        {selectedFinding.status && selectedFinding.status !== 'open'
                          ? `This finding is already marked as ${selectedFinding.status}.`
                          : 'No automated suggestion passed verification. Use "Custom Edit" to rewrite manually.'}
                      </div>
                    ) : (
                      <div className="space-y-2.5">
                        {suggestions.map((s, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-white border border-blue-200 rounded-lg flex items-center justify-between text-xs shadow-2xs"
                          >
                            <div className="pr-3 space-y-1">
                              <div className="font-semibold text-emerald-800 font-mono text-[12px]">
                                Replace: "{s.replacement_text}"
                              </div>
                              <div className="text-[11px] text-slate-500 flex items-center space-x-1">
                                <CheckCircle className="w-3 h-3 text-emerald-600 shrink-0" />
                                <span>{s.verification_reason}</span>
                              </div>
                            </div>

                            {currentUser?.role === 'creator' && (
                              <button
                                onClick={() => handleAcceptSuggestion(s.replacement_text)}
                                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-md text-xs transition-colors shrink-0 shadow-2xs"
                              >
                                Accept Fix (v2)
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* CLAIMS LEDGER TAB */}
            {activeTab === 'claims' && (
              <div className="space-y-3">
                {claims.length === 0 ? (
                  <div className="text-center py-8 text-xs text-slate-400">
                    No promotional claims, pricing figures, or guarantees detected in this draft.
                  </div>
                ) : (
                  claims.map((c, idx) => (
                    <div key={idx} className="p-3.5 border rounded-xl text-xs space-y-1.5 bg-white">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800 font-mono text-xs">
                          "{c.claim_text}"
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            c.status === 'approved'
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                              : c.status === 'missing_disclaimer'
                              ? 'bg-amber-100 text-amber-800 border border-amber-300'
                              : 'bg-red-100 text-red-800 border border-red-300'
                          }`}
                        >
                          {c.status.replace('_', ' ')}
                        </span>
                      </div>

                      <div className="text-slate-600 text-[11px] leading-relaxed">{c.reason}</div>

                      {c.required_disclaimer && (
                        <div className="text-[11px] font-mono text-amber-900 bg-amber-50 p-2 rounded border border-amber-200">
                          <strong>Mandatory Disclaimer:</strong> {c.required_disclaimer}
                        </div>
                      )}

                      {c.evidence_ref && (
                        <div className="text-[10px] font-mono text-slate-400">
                          Evidence Reference: {c.evidence_ref}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}

            {/* COMMENTS TAB */}
            {activeTab === 'comments' && (
              <div className="space-y-4">
                <div className="space-y-2.5">
                  {comments.length === 0 ? (
                    <div className="text-center py-8 text-xs text-slate-400">
                      No comments yet. Collaborate with creators and reviewers here.
                    </div>
                  ) : (
                    comments.map((cm) => (
                      <div key={cm.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-700">
                            {cm.author_name || `User #${cm.author_id}`}
                          </span>
                          <span className="text-[10px] text-slate-400">
                            {new Date(cm.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <div className="text-slate-800 leading-relaxed">{cm.body}</div>
                      </div>
                    ))
                  )}
                </div>

                <form onSubmit={handleAddComment} className="flex space-x-2 pt-2 border-t border-slate-100">
                  <input
                    type="text"
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Leave comment or guidance on this draft..."
                    className="flex-1 px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  />
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition-colors"
                  >
                    Post
                  </button>
                </form>
              </div>
            )}

            {/* VERSION HISTORY TAB */}
            {activeTab === 'versions' && (
              <div className="space-y-3">
                {(!content.versions || content.versions.length === 0) ? (
                  <div className="p-3 bg-slate-50 rounded-lg border text-xs text-slate-600 font-mono">
                    Version 1 (Initial Draft)
                  </div>
                ) : (
                  content.versions.map((v) => (
                    <div key={v.id} className="p-3 bg-slate-50 border rounded-lg text-xs space-y-1 font-mono">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800">Version {v.version_no}</span>
                        <span className="text-[10px] text-slate-400">
                          {v.created_at ? new Date(v.created_at).toLocaleString() : 'Active'}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-500 truncate">
                        SHA-256: {v.content_hash}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Custom Edit Modal */}
      {showEditModal && selectedFinding && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <div className="bg-white max-w-md w-full p-6 rounded-2xl shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900">Custom Manual Rewrite</h3>
            <p className="text-xs text-slate-500">
              Provide replacement copy for <code className="text-red-700 font-bold">"{selectedFinding.span_text}"</code>.
              Saving will create a new revised content version.
            </p>

            <textarea
              rows={3}
              value={customEditText}
              onChange={(e) => setCustomEditText(e.target.value)}
              className="w-full p-2.5 text-xs font-mono border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setShowEditModal(false)}
                className="px-3.5 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveCustomEdit}
                className="px-4 py-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm"
              >
                Apply Custom Rewrite (v2)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dismissal Reason Modal */}
      {showDismissModal && selectedFinding && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <div className="bg-white max-w-md w-full p-6 rounded-2xl shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900">Dismiss Finding Reason</h3>
            <p className="text-xs text-slate-500">
              Provide justification. Dismissals are logged in the audit trail and tracked by the Ambiguity Detector.
            </p>

            <textarea
              rows={3}
              value={dismissReason}
              onChange={(e) => setDismissReason(e.target.value)}
              placeholder="e.g. Legal exception approved for Q3 partner campaign..."
              className="w-full p-2.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setShowDismissModal(false)}
                className="px-3.5 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleDismissFinding}
                className="px-4 py-1.5 text-xs bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg shadow-sm"
              >
                Confirm Dismissal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Approval & Decision Modal */}
      {showApprovalModal && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <div className="bg-white max-w-md w-full p-6 rounded-2xl shadow-2xl space-y-4">
            <div className="flex items-center space-x-2">
              {approvalDecision === 'approved' ? (
                <FileCheck className="w-5 h-5 text-emerald-600" />
              ) : approvalDecision === 'changes_requested' ? (
                <AlertTriangle className="w-5 h-5 text-amber-600" />
              ) : (
                <AlertOctagon className="w-5 h-5 text-red-600" />
              )}
              <h3 className="text-base font-bold text-slate-900 capitalize">
                {approvalDecision === 'approved'
                  ? 'Approve & Cryptographically Sign'
                  : approvalDecision === 'changes_requested'
                  ? 'Request Changes'
                  : 'Reject Submission'}
              </h3>
            </div>

            <p className="text-xs text-slate-500">
              Provide justification notes. An immutable cryptographic SHA-256 signature will be registered in the audit ledger under your verified reviewer identity.
            </p>

            <div>
              <label className="block text-[11px] font-bold uppercase text-slate-700 mb-1">
                Justification Notes
              </label>
              <textarea
                rows={3}
                value={approvalNote}
                onChange={(e) => setApprovalNote(e.target.value)}
                placeholder="Enter justification notes..."
                className="w-full p-2.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-slate-50/50"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setShowApprovalModal(false)}
                className="px-3.5 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmApproval}
                className={`px-4 py-2 text-xs font-semibold text-white rounded-lg shadow-sm transition-colors ${
                  approvalDecision === 'approved'
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : approvalDecision === 'changes_requested'
                    ? 'bg-amber-600 hover:bg-amber-700'
                    : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                {approvalDecision === 'approved'
                  ? 'Confirm & Sign Approval'
                  : approvalDecision === 'changes_requested'
                  ? 'Submit Change Request'
                  : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
