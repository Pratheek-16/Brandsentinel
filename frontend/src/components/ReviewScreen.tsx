import React, { useState, useEffect } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
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
} from 'lucide-react';
import { api } from '../api';
import { User, Finding, ClaimItem, VerifiedSuggestion, CommentItem } from '../types';

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
  const [content, setContent] = useState<any>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [claims, setClaims] = useState<ClaimItem[]>([]);
  const [comments, setComments] = useState<CommentItem[]>([]);
  const [newComment, setNewComment] = useState('');
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [suggestions, setSuggestions] = useState<VerifiedSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'findings' | 'claims' | 'comments'>('findings');
  const [dismissReason, setDismissReason] = useState('');
  const [showDismissModal, setShowDismissModal] = useState(false);
  const [approvalResult, setApprovalResult] = useState<any>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const c = await api.getContent(contentId);
      setContent(c);

      // Re-fetch review findings
      const rev = await api.reviewContent(contentId);
      setFindings(rev.findings || []);

      // Fetch claims
      const cl = await api.getClaims(contentId);
      setClaims(cl.claims || []);

      // Fetch comments
      const cm = await api.getComments(contentId);
      setComments(cm || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (contentId) loadData();
  }, [contentId]);

  const handleSelectFinding = async (f: Finding) => {
    setSelectedFinding(f);
    try {
      const res = await api.getSuggestions(contentId, f.id);
      setSuggestions(res.suggestions || []);
    } catch {
      setSuggestions([]);
    }
  };

  const handleAcceptSuggestion = async (replacement: string) => {
    if (!selectedFinding) return;
    try {
      await api.acceptSuggestion(contentId, selectedFinding.id, replacement);
      await loadData();
      setSelectedFinding(null);
      setSuggestions([]);
      onRefreshContent();
    } catch (err: any) {
      alert(err.message || 'Error accepting suggestion');
    }
  };

  const handleDismissFinding = async () => {
    if (!selectedFinding || !dismissReason.trim()) return;
    try {
      await api.dismissFinding(contentId, selectedFinding.id, dismissReason);
      setShowDismissModal(false);
      setDismissReason('');
      setFindings((prev) => prev.filter((f) => f.id !== selectedFinding.id));
      setSelectedFinding(null);
    } catch (err: any) {
      alert(err.message || 'Error dismissing finding');
    }
  };

  const handleSubmitForReview = async () => {
    try {
      const res = await api.submitContent(contentId);
      setContent((prev: any) => ({ ...prev, status: res.status }));
      if (res.escalated) {
        alert(`Content Escalated to Authorised Reviewer!\nReason: ${res.escalation_reason}`);
      } else {
        alert('Submitted to Manager Review queue.');
      }
    } catch (err: any) {
      alert(err.message || 'Submission error');
    }
  };

  const handleApprove = async (decision: 'approved' | 'changes_requested' | 'rejected') => {
    const reason = prompt(`Enter reason for decision [${decision}]:`) || '';
    try {
      const res = await api.approveContent(contentId, decision, reason);
      setApprovalResult(res);
      setContent((prev: any) => ({ ...prev, status: res.status }));
      alert(`Decision recorded! Status: ${res.status}\nSignature Hash: ${res.signature_hash}`);
    } catch (err: any) {
      alert(err.message || 'Approval failed');
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    try {
      await api.addComment(contentId, newComment, selectedFinding?.id);
      setNewComment('');
      const cm = await api.getComments(contentId);
      setComments(cm || []);
    } catch (err: any) {
      alert(err.message || 'Failed to post comment');
    }
  };

  const renderSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'blocker':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-bold bg-red-100 text-red-900 border border-red-300">
            <AlertOctagon className="w-3.5 h-3.5 text-red-700" />
            <span>BLOCKER</span>
          </span>
        );
      case 'major':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
            <span>MAJOR</span>
          </span>
        );
      case 'minor':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-bold bg-yellow-100 text-yellow-900 border border-yellow-300">
            <Info className="w-3.5 h-3.5 text-yellow-700" />
            <span>MINOR</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-800 border border-slate-300">
            <Info className="w-3.5 h-3.5 text-slate-600" />
            <span>INFO</span>
          </span>
        );
    }
  };

  if (!content) {
    return (
      <div className="py-12 text-center text-slate-500 text-sm">
        {loading ? 'Analyzing brand compliance...' : 'Select or submit a draft to inspect review results.'}
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 space-y-6">
      {/* Top Banner: Status & Actions */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-lg font-bold text-slate-900">{content.title}</h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-bold uppercase bg-blue-50 text-blue-700 border border-blue-200">
              Status: {content.status}
            </span>
            <span className="text-xs font-mono text-slate-400">Version {content.version_id}</span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">Channel: {content.channel || 'All Channels'}</p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2">
          {currentUser?.role === 'creator' && (
            <button
              onClick={handleSubmitForReview}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors"
            >
              Submit for Approval
            </button>
          )}

          {(currentUser?.role === 'manager' || currentUser?.role === 'reviewer' || currentUser?.role === 'admin') && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleApprove('approved')}
                className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors"
              >
                Approve & Sign
              </button>
              <button
                onClick={() => handleApprove('changes_requested')}
                className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors"
              >
                Request Changes
              </button>
              <button
                onClick={() => handleApprove('rejected')}
                className="px-3.5 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors"
              >
                Reject
              </button>
            </div>
          )}
        </div>
      </div>

      {approvalResult && (
        <div className="p-4 bg-emerald-50 border border-emerald-300 rounded-lg text-xs text-emerald-900 font-mono">
          <div className="font-bold flex items-center space-x-1.5 text-emerald-800 mb-1">
            <FileCheck className="w-4 h-4" />
            <span>Cryptographic Sign-off Recorded</span>
          </div>
          <div>Decision: {approvalResult.decision}</div>
          <div className="truncate">Signature Hash: {approvalResult.signature_hash}</div>
        </div>
      )}

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Content Text with Highlighting */}
        <div className="lg:col-span-6 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Draft Copy</h2>
            <span className="text-xs text-slate-400">Click highlighted violation to view verified fixes</span>
          </div>

          <div className="text-sm font-mono leading-relaxed p-4 bg-slate-50 border border-slate-200 rounded-lg whitespace-pre-wrap">
            {content.text_body || 'No text content available.'}
          </div>
        </div>

        {/* Right: Tabs (Findings, Claims Ledger, Comments) */}
        <div className="lg:col-span-6 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col">
          {/* Subtabs */}
          <div className="flex border-b border-slate-200 px-4 pt-3 space-x-4">
            <button
              onClick={() => setActiveTab('findings')}
              className={`pb-2 text-xs font-bold uppercase transition-colors border-b-2 ${
                activeTab === 'findings' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500'
              }`}
            >
              Brand Findings ({findings.length})
            </button>
            <button
              onClick={() => setActiveTab('claims')}
              className={`pb-2 text-xs font-bold uppercase transition-colors border-b-2 ${
                activeTab === 'claims' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500'
              }`}
            >
              Claim Ledger ({claims.length})
            </button>
            <button
              onClick={() => setActiveTab('comments')}
              className={`pb-2 text-xs font-bold uppercase transition-colors border-b-2 ${
                activeTab === 'comments' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500'
              }`}
            >
              Comments ({comments.length})
            </button>
          </div>

          <div className="p-4 flex-1 overflow-y-auto max-h-[600px] space-y-4">
            {/* FINDINGS TAB */}
            {activeTab === 'findings' && (
              <div className="space-y-3">
                {findings.length === 0 ? (
                  <div className="text-center py-8 text-xs text-slate-400">
                    <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                    <span>No brand violations detected! Content adheres to all active rules.</span>
                  </div>
                ) : (
                  findings.map((f) => (
                    <div
                      key={f.id}
                      onClick={() => handleSelectFinding(f)}
                      className={`p-3.5 rounded-lg border text-xs cursor-pointer transition-all ${
                        selectedFinding?.id === f.id
                          ? 'border-blue-500 bg-blue-50/50 shadow-sm'
                          : 'border-slate-200 hover:border-slate-300 bg-white'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center space-x-2">
                          {renderSeverityBadge(f.severity)}
                          <span className="font-semibold uppercase tracking-wider text-slate-700 text-[11px]">
                            {f.category}
                          </span>
                        </div>
                        <span className="text-[11px] font-mono text-slate-400">
                          Confidence: {(parseFloat(f.confidence) * 100).toFixed(0)}%
                        </span>
                      </div>

                      <div className="text-slate-800 font-medium my-1">
                        Violation: <span className="font-mono bg-red-50 text-red-700 px-1.5 py-0.5 rounded font-bold">"{f.span_text}"</span>
                      </div>
                      <div className="text-slate-600 mt-1">{f.reason}</div>

                      {f.evidence_quote && (
                        <div className="mt-2 p-2 bg-slate-50 rounded border border-slate-200 text-slate-500 font-mono text-[11px]">
                          Cited Source [{f.evidence_id}]: "{f.evidence_quote}"
                        </div>
                      )}
                    </div>
                  ))
                )}

                {/* Verified Suggestions Panel (Improvement I-1) */}
                {selectedFinding && (
                  <div className="mt-4 p-4 bg-blue-50/60 border border-blue-200 rounded-xl space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-blue-900 uppercase">
                        Improvement I-1: Verified Suggestions
                      </span>
                      <button
                        onClick={() => setShowDismissModal(true)}
                        className="text-xs text-red-600 hover:underline font-semibold"
                      >
                        Dismiss Finding...
                      </button>
                    </div>

                    {suggestions.length === 0 ? (
                      <div className="text-xs text-slate-500">Generating intent-preserving candidate fixes...</div>
                    ) : (
                      <div className="space-y-2">
                        {suggestions.map((s, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-white border border-blue-200 rounded-lg flex items-center justify-between text-xs"
                          >
                            <div>
                              <div className="font-semibold text-emerald-700 font-mono">
                                Replace with: "{s.replacement_text}"
                              </div>
                              <div className="text-[11px] text-slate-500 mt-0.5 flex items-center space-x-1">
                                <CheckCircle className="w-3 h-3 text-emerald-500" />
                                <span>{s.verification_reason}</span>
                              </div>
                            </div>

                            {currentUser?.role === 'creator' && (
                              <button
                                onClick={() => handleAcceptSuggestion(s.replacement_text)}
                                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded text-xs transition-colors shrink-0"
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
                  <div className="text-center py-6 text-xs text-slate-400">
                    No promotional claims or guarantees detected in this draft.
                  </div>
                ) : (
                  claims.map((c, idx) => (
                    <div key={idx} className="p-3 border rounded-lg text-xs space-y-1 bg-white">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800 font-mono">"{c.claim_text}"</span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            c.status === 'approved'
                              ? 'bg-emerald-100 text-emerald-800'
                              : c.status === 'missing_disclaimer'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {c.status.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="text-slate-600 text-[11px]">{c.reason}</div>
                      {c.required_disclaimer && (
                        <div className="text-[10px] font-mono text-slate-500">
                          Required Disclaimer: {c.required_disclaimer}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}

            {/* COMMENTS TAB */}
            {activeTab === 'comments' && (
              <div className="space-y-3">
                <div className="space-y-2">
                  {comments.map((cm) => (
                    <div key={cm.id} className="p-2.5 bg-slate-50 border border-slate-200 rounded text-xs">
                      <div className="font-semibold text-slate-700">Author #{cm.author_id}</div>
                      <div className="text-slate-800 mt-1">{cm.body}</div>
                    </div>
                  ))}
                </div>

                <form onSubmit={handleAddComment} className="flex space-x-2 pt-2">
                  <input
                    type="text"
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Leave comment or guidance on this draft..."
                    className="flex-1 px-3 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="submit"
                    className="px-3 py-1.5 bg-blue-600 text-white rounded text-xs font-semibold hover:bg-blue-700"
                  >
                    Post
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dismissal Reason Modal */}
      {showDismissModal && (
        <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white max-w-sm w-full p-5 rounded-xl shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Dismiss Finding Reason</h3>
            <p className="text-xs text-slate-500">
              Provide justification. Dismissals are logged in the audit trail and tracked by the Ambiguity Detector.
            </p>
            <textarea
              rows={3}
              value={dismissReason}
              onChange={(e) => setDismissReason(e.target.value)}
              placeholder="e.g. Approved exception by Legal for this campaign..."
              className="w-full p-2 text-xs border border-slate-300 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowDismissModal(false)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleDismissFinding}
                className="px-3 py-1.5 text-xs bg-red-600 hover:bg-red-700 text-white font-semibold rounded"
              >
                Confirm Dismissal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
