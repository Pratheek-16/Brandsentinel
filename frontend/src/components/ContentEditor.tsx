import React, { useState, useEffect } from 'react';
import {
  FileText,
  Upload,
  Sparkles,
  Send,
  AlertCircle,
  CheckCircle2,
  Clock,
  Layers,
  FileSearch,
  ExternalLink,
} from 'lucide-react';
import { api } from '../api';
import { ContentItem } from '../types';

interface ContentEditorProps {
  onReviewCreated: (contentId: number) => void;
  brand: string;
}

export const ContentEditor: React.FC<ContentEditorProps> = ({
  onReviewCreated,
  brand,
}) => {
  const [title, setTitle] = useState('');
  const [channel, setChannel] = useState('social');
  const [contentType, setContentType] = useState('text');
  const [bodyText, setBodyText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [reviewStage, setReviewStage] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [existingDrafts, setExistingDrafts] = useState<ContentItem[]>([]);
  const [loadingDrafts, setLoadingDrafts] = useState(false);

  // Brand-tailored realistic samples for foolproof judging walkthrough
  const brandSamples: Record<string, Array<{ label: string; title: string; channel: string; body: string }>> = {
    NovaFit: [
      {
        label: 'NovaFit Creator: PulseBand breach + battery claim + Indian PII',
        title: 'NovaFit Pulse Summer Launch',
        channel: 'social',
        body: 'The new PulseBand is the best fitness wearable in the world! Delivers 14 days of battery life on a single charge. Contact +91 9876543210 or support@novafit.local to pre-order.',
      },
      {
        label: 'NovaFit Reviewer: Pending approval queue item (Minor tone)',
        title: 'NovaFit Member Coaching Update',
        channel: 'email',
        body: 'Welcome to NovaFit. Our pulse tracking hardware delivers up to 10 days of continuous battery life with certified guidance. Terms and conditions apply.',
      },
    ],
    'Lumen Bank': [
      {
        label: 'Lumen Bank: Missing APR disclaimer & guaranteed returns',
        title: 'Lumen High-Yield Account Campaign',
        channel: 'website',
        body: 'Earn an unprecedented 7.5% APY with Lumen Bank savings! Guaranteed risk-free returns on all deposits up to $500,000. Contact wealth@lumenbank.local.',
      },
      {
        label: 'Lumen Bank: Compliant FDIC Disclosure',
        title: 'Lumen Secure Banking Statement',
        channel: 'email',
        body: 'Lumen Bank is dedicated to protecting your assets. Member FDIC. Loans subject to credit approval and underwriting guidelines. Annual Percentage Rate varies.',
      },
    ],
    'Aster University': [
      {
        label: 'Aster: Sustainability claim with outdated 2023 cert fact',
        title: 'Aster Green Campus Initiative',
        channel: 'social',
        body: 'Aster University operates on 100% renewable power under our 2023 Green Campus ISO-14001 certification. Join the autumn student cohort today.',
      },
      {
        label: 'Aster: Compliant Academic Welcome',
        title: 'Aster Convocation Address',
        channel: 'website',
        body: 'Aster University warmly welcomes our incoming students. Grounded in scholarly rigor, our faculty empowers students to lead with purpose.',
      },
    ],
  };

  const currentSamples = brandSamples[brand] || brandSamples['NovaFit'];

  const loadDrafts = async () => {
    try {
      setLoadingDrafts(true);
      const list = await api.listContents();
      setExistingDrafts(list || []);
    } catch (err) {
      console.warn('Could not load drafts:', err);
    } finally {
      setLoadingDrafts(false);
    }
  };

  useEffect(() => {
    loadDrafts();
  }, [brand]);

  // Reading metrics
  const wordCount = bodyText.trim() ? bodyText.trim().split(/\s+/).length : 0;
  const charCount = bodyText.length;
  const readTimeMin = Math.ceil(wordCount / 200);

  const handleCreateAndReview = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatusMsg(null);
    setReviewStage('Sanitizing and redacting sensitive PII/secrets...');

    try {
      let contentId: number;
      if (file) {
        const formData = new FormData();
        formData.append('title', title || file.name);
        formData.append('type', contentType);
        formData.append('channel', channel);
        formData.append('file', file);
        const res = await api.uploadContent(formData);
        contentId = res.content_id;
      } else {
        if (!bodyText.trim()) throw new Error('Please enter draft copy text.');
        const res = await api.createContent({
          title: title || `${brand} Draft Campaign`,
          type: 'text',
          channel,
          body: bodyText,
        });
        contentId = res.content_id;
      }

      setReviewStage('Executing deterministic checks and grounding verification...');
      await api.reviewContent(contentId);

      setStatusMsg({
        type: 'success',
        text: `Draft created & AI Review completed (ID: ${contentId}). Opening review console...`,
      });

      await loadDrafts();
      setTimeout(() => {
        onReviewCreated(contentId);
      }, 600);
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Submission failed' });
    } finally {
      setLoading(false);
      setReviewStage(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-8">
      {/* Drafting Panel */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-200 bg-slate-50 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
              <FileText className="w-5 h-5 text-blue-600" />
              <span>Drafting & Pre-Publication Screening</span>
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Draft or upload copy for <span className="font-semibold text-slate-700">{brand}</span>. PII is automatically redacted before AI evaluation.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mr-1">
              Test Presets:
            </span>
            {currentSamples.map((s) => (
              <button
                key={s.label}
                type="button"
                onClick={() => {
                  setTitle(s.title);
                  setChannel(s.channel);
                  setBodyText(s.body);
                  setFile(null);
                }}
                className="text-xs px-2.5 py-1 bg-white border border-slate-300 rounded hover:bg-slate-100 text-slate-700 font-medium transition-colors shadow-2xs"
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {statusMsg && (
          <div
            className={`p-4 flex items-center space-x-2 text-xs font-semibold ${
              statusMsg.type === 'success'
                ? 'bg-emerald-50 text-emerald-900 border-b border-emerald-200'
                : 'bg-red-50 text-red-900 border-b border-red-200'
            }`}
          >
            {statusMsg.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
            )}
            <span>{statusMsg.text}</span>
          </div>
        )}

        <form onSubmit={handleCreateAndReview} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label htmlFor="content-title" className="block text-xs font-bold uppercase text-slate-700 mb-1">
                Campaign / Document Title
              </label>
              <input
                id="content-title"
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Q3 Launch Announcement"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label htmlFor="channel-select" className="block text-xs font-bold uppercase text-slate-700 mb-1">
                Distribution Channel
              </label>
              <select
                id="channel-select"
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              >
                <option value="social">Social Media (Instagram/LinkedIn/X)</option>
                <option value="email">Email Campaign / Newsletter</option>
                <option value="website">Public Website / Landing Page</option>
                <option value="ad">Digital Advertising (Search/Display)</option>
                <option value="print">Print Collateral / Brochure</option>
              </select>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label htmlFor="body-editor" className="block text-xs font-bold uppercase text-slate-700">
                Draft Content Body
              </label>
              <div className="flex items-center space-x-3 text-xs text-slate-400 font-mono">
                <span>{charCount} chars</span>
                <span>•</span>
                <span>{wordCount} words</span>
                <span>•</span>
                <span className="flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>~{readTimeMin} min read</span>
                </span>
              </div>
            </div>

            <textarea
              id="body-editor"
              rows={8}
              value={bodyText}
              onChange={(e) => {
                setBodyText(e.target.value);
                if (file) setFile(null);
              }}
              placeholder={`Paste draft copy to evaluate ${brand} tone, terminology, pricing facts, promotional claims, and accessibility...`}
              className="w-full p-3.5 text-sm font-mono border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none leading-relaxed bg-slate-50/50"
            />
          </div>

          <div className="border-t border-slate-200 pt-4">
            <label className="block text-xs font-bold uppercase text-slate-700 mb-2">
              Or Upload Asset Document (DOCX, PDF, PNG/JPG)
            </label>
            <div className="flex items-center space-x-4">
              <label className="cursor-pointer flex items-center space-x-2 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors shadow-2xs">
                <Upload className="w-4 h-4 text-slate-500" />
                <span>Choose Document File</span>
                <input
                  type="file"
                  className="hidden"
                  accept=".docx,.pdf,.png,.jpg,.jpeg,.txt"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      const f = e.target.files[0];
                      setFile(f);
                      setTitle(f.name.replace(/\.[^/.]+$/, ''));
                      if (f.name.endsWith('.docx')) setContentType('docx');
                      else if (f.name.endsWith('.pdf')) setContentType('pdf');
                      else if (f.type.startsWith('image/')) setContentType('image');
                      else setContentType('text');
                    }
                  }}
                />
              </label>

              {file && (
                <span className="text-xs text-blue-700 font-mono bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200">
                  {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-100">
            <div className="text-xs text-slate-500 italic">
              {reviewStage || 'PII redactable: emails, phone numbers, SSNs, and API keys are masked.'}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-lg shadow-sm transition-colors disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'Redacting & Reviewing...' : 'Run Evidence-Grounded Review'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Existing Workspace Drafts Queue */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-blue-600" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800">
              {brand} Submissions & Review Queue
            </h2>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {existingDrafts.length} Documents
          </span>
        </div>

        <div className="divide-y divide-slate-100">
          {loadingDrafts ? (
            <div className="p-8 text-center text-xs text-slate-400">Loading workspace drafts...</div>
          ) : existingDrafts.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400">
              No content submitted in this workspace yet. Create a draft above to begin!
            </div>
          ) : (
            existingDrafts.map((d) => (
              <div
                key={d.id}
                className="p-4 hover:bg-slate-50 transition-colors flex items-center justify-between"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <span className="font-semibold text-sm text-slate-900">{d.title}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono ${
                        d.status === 'approved'
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                          : d.status === 'in_review' || d.status === 'ai_checked'
                          ? 'bg-blue-100 text-blue-800 border border-blue-300'
                          : d.status === 'changes_requested'
                          ? 'bg-amber-100 text-amber-800 border border-amber-300'
                          : 'bg-slate-100 text-slate-700 border border-slate-300'
                      }`}
                    >
                      {d.status}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">
                      v{d.version_no || 1}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 flex items-center space-x-3">
                    <span>Creator: {d.creator_name || d.creator_email || 'Author'}</span>
                    <span>•</span>
                    <span>Channel: {d.channel}</span>
                    <span>•</span>
                    <span>Type: {d.type}</span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => onReviewCreated(d.id)}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 text-xs font-semibold rounded-md border border-slate-300 transition-colors"
                >
                  <FileSearch className="w-3.5 h-3.5" />
                  <span>Inspect Review</span>
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
