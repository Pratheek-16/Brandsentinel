import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Upload,
  Clock,
  Lock,
  ChevronDown,
  CheckCircle2,
  AlertCircle,
  FileSearch,
  FileText,
  FileCheck2,
  Save,
  ArrowRight,
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
  const [bodyText, setBodyText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState('text');
  const [loading, setLoading] = useState(false);
  const [reviewStage, setReviewStage] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [existingDrafts, setExistingDrafts] = useState<ContentItem[]>([]);
  const [loadingDrafts, setLoadingDrafts] = useState(false);
  const [showExamplesPopover, setShowExamplesPopover] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Auto-resize textarea like a document sheet
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.max(260, textareaRef.current.scrollHeight)}px`;
    }
  }, [bodyText]);

  // Brand-tailored named samples organized by brand & issue type
  const brandExamples: Record<
    string,
    Array<{
      title: string;
      category: string;
      issueType: string;
      channel: string;
      body: string;
    }>
  > = {
    NovaFit: [
      {
        title: 'NovaFit Pulse Summer Launch',
        category: 'Product Launch',
        issueType: 'Superlative claim + battery spec + Indian phone PII',
        channel: 'social',
        body: 'The new PulseBand is the best fitness wearable in the world! Delivers 14 days of battery life on a single charge. Contact +91 9876543210 or support@novafit.local to pre-order.',
      },
      {
        title: 'NovaFit Member Coaching Update',
        category: 'Newsletter',
        issueType: 'Compliant copy with minor tone guidelines',
        channel: 'email',
        body: 'Welcome to NovaFit. Our pulse tracking hardware delivers up to 10 days of continuous battery life with certified guidance. Terms and conditions apply.',
      },
      {
        title: 'PulseBand Endurance Promo',
        category: 'Social Ad',
        issueType: 'Prohibited health claim + unverified medical efficacy',
        channel: 'social',
        body: 'Guaranteed to prevent cardiovascular fatigue with clinically proven metabolic tracking. Pre-order at our flagship studio today.',
      },
    ],
    'Lumen Bank': [
      {
        title: 'Lumen High-Yield Account Campaign',
        category: 'Ad Campaign',
        issueType: 'Missing APR disclaimer + guaranteed return claim',
        channel: 'web',
        body: 'Earn an unprecedented 7.5% APY with Lumen Bank savings! Guaranteed risk-free returns on all deposits up to $500,000. Contact wealth@lumenbank.local.',
      },
      {
        title: 'Lumen Secure Banking Statement',
        category: 'Web Announcement',
        issueType: 'Compliant FDIC disclosure & APR caveats',
        channel: 'web',
        body: 'Lumen Bank is dedicated to protecting your assets. Member FDIC. Loans subject to credit approval and underwriting guidelines. Annual Percentage Rate varies.',
      },
    ],
    'Aster University': [
      {
        title: 'Aster Green Campus Initiative',
        category: 'Press Release',
        issueType: 'Sustainability claim with outdated 2023 cert fact',
        channel: 'press',
        body: 'Aster University operates on 100% renewable power under our 2023 Green Campus ISO-14001 certification. Join the autumn student cohort today.',
      },
      {
        title: 'Aster Convocation Address',
        category: 'Academic Speech',
        issueType: 'Compliant scholarly tone & verified faculty facts',
        channel: 'web',
        body: 'Aster University warmly welcomes our incoming students. Grounded in scholarly rigor, our faculty empowers students to lead with purpose.',
      },
    ],
  };

  const currentExamples = brandExamples[brand] || brandExamples['NovaFit'];

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

  // Word & read-time counts
  const wordCount = bodyText.trim() ? bodyText.trim().split(/\s+/).length : 0;
  const readTimeMin = Math.max(1, Math.ceil(wordCount / 200));

  const channels = [
    { id: 'social', label: 'Social' },
    { id: 'email', label: 'Email' },
    { id: 'web', label: 'Web' },
    { id: 'press', label: 'Press' },
    { id: 'other', label: 'Other' },
  ];

  const handleSelectExample = (ex: (typeof currentExamples)[0]) => {
    setTitle(ex.title);
    setChannel(ex.channel);
    setBodyText(ex.body);
    setFile(null);
    setShowExamplesPopover(false);
  };

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const processFile = (f: File) => {
    setFile(f);
    setTitle(f.name.replace(/\.[^/.]+$/, ''));
    if (f.name.endsWith('.docx')) setFileType('docx');
    else if (f.name.endsWith('.pdf')) setFileType('pdf');
    else if (f.type.startsWith('image/')) setFileType('image');
    else setFileType('text');
  };

  const handleCheckDraft = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setStatusMsg(null);
    setReviewStage('Hiding personal data and masking PII before analysis...');

    try {
      let contentId: number;
      if (file) {
        const formData = new FormData();
        formData.append('title', title || file.name);
        formData.append('type', fileType);
        formData.append('channel', channel);
        formData.append('file', file);
        const res = await api.uploadContent(formData);
        contentId = res.content_id;
      } else {
        if (!bodyText.trim()) {
          throw new Error('Please write or paste your draft copy first.');
        }
        const res = await api.createContent({
          title: title.trim() || `${brand} Draft (${new Date().toLocaleDateString()})`,
          type: 'text',
          channel,
          body: bodyText,
        });
        contentId = res.content_id;
      }

      setReviewStage('Checking draft against approved brand facts & guidelines...');
      await api.reviewContent(contentId);

      setStatusMsg({
        type: 'success',
        text: 'Checks completed. Opening the proofing desk...',
      });

      await loadDrafts();
      setTimeout(() => {
        onReviewCreated(contentId);
      }, 500);
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Draft check failed' });
    } finally {
      setLoading(false);
      setReviewStage(null);
    }
  };

  const handleSaveDraft = async () => {
    if (!bodyText.trim() && !file) return;
    setLoading(true);
    try {
      await api.createContent({
        title: title.trim() || `${brand} Draft (Unchecked)`,
        type: 'text',
        channel,
        body: bodyText,
      });
      setStatusMsg({ type: 'success', text: 'Draft saved to your workspace desk.' });
      await loadDrafts();
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Could not save draft' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (Desktop): Collapsible Drafts Queue */}
        <div className="lg:col-span-4 order-2 lg:order-1 space-y-4">
          <div
            className="p-4 rounded-[2px] border"
            style={{
              backgroundColor: 'var(--sheet)',
              borderColor: 'var(--hairline)',
            }}
          >
            <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: 'var(--hairline-subtle)' }}>
              <div className="flex items-center gap-2">
                <FileCheck2 size={16} style={{ color: 'var(--accent)' }} />
                <h3 className="font-serif font-semibold text-sm" style={{ color: 'var(--ink)' }}>
                  Workspace drafts
                </h3>
              </div>
              <span className="text-xs font-mono" style={{ color: 'var(--muted)' }}>
                {existingDrafts.length}
              </span>
            </div>

            {loadingDrafts ? (
              <div className="py-8 text-center text-xs" style={{ color: 'var(--muted)' }}>
                Loading workspace drafts...
              </div>
            ) : existingDrafts.length === 0 ? (
              <div className="py-8 text-center text-xs leading-relaxed" style={{ color: 'var(--muted)' }}>
                No drafts yet in this workspace. Place a draft on the sheet to begin.
              </div>
            ) : (
              <div className="divide-y mt-2 max-h-[580px] overflow-y-auto" style={{ borderColor: 'var(--hairline-subtle)' }}>
                {existingDrafts.map((d) => (
                  <div
                    key={d.id}
                    className="py-3 px-1 hover:bg-black/3 dark:hover:bg-white/3 transition-colors cursor-pointer group"
                    onClick={() => onReviewCreated(d.id)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4
                        className="text-xs font-medium truncate flex-1 group-hover:underline"
                        style={{ color: 'var(--ink)' }}
                      >
                        {d.title}
                      </h4>
                      <span
                        className="text-[10px] font-mono px-1.5 py-0.2 rounded-[2px] shrink-0 capitalize"
                        style={{
                          backgroundColor:
                            d.status === 'approved'
                              ? 'var(--status-verified-bg)'
                              : d.status === 'changes_requested'
                              ? 'var(--severity-major-bg)'
                              : 'var(--accent-surface)',
                          color:
                            d.status === 'approved'
                              ? 'var(--status-verified)'
                              : d.status === 'changes_requested'
                              ? 'var(--severity-major)'
                              : 'var(--accent-ink)',
                          border: '1px solid currentColor',
                        }}
                      >
                        {d.status?.replace('_', ' ')}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 mt-1 text-[11px]" style={{ color: 'var(--muted)' }}>
                      <span>{d.channel}</span>
                      <span>•</span>
                      <span>v{d.version_no || 1}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1 group-hover:text-[var(--accent)] transition-colors">
                        Inspect
                        <ArrowRight size={10} />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right / Center: The Editorial Writing Sheet (760px centered) */}
        <div className="lg:col-span-8 order-1 lg:order-2">
          <div
            className="w-full max-w-[760px] mx-auto proofing-sheet p-8 sm:p-12 relative flex flex-col justify-between"
            style={{ minHeight: '620px' }}
          >
            {/* Top Toolbar: Example Popover & Status feedback */}
            <div className="flex items-center justify-between pb-4 border-b mb-6" style={{ borderColor: 'var(--hairline)' }}>
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowExamplesPopover(!showExamplesPopover)}
                  className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1.5 rounded-[2px] border transition-colors hover:bg-black/5 dark:hover:bg-white/5"
                  style={{
                    backgroundColor: 'var(--paper)',
                    borderColor: 'var(--hairline)',
                    color: 'var(--graphite)',
                  }}
                >
                  <Sparkles size={13} style={{ color: 'var(--accent)' }} />
                  <span>Try an example</span>
                  <ChevronDown size={13} />
                </button>

                {/* Popover */}
                {showExamplesPopover && (
                  <div
                    className="absolute left-0 mt-1 w-80 p-2 rounded-[2px] border shadow-lg z-50 text-left"
                    style={{
                      backgroundColor: 'var(--sheet)',
                      borderColor: 'var(--hairline)',
                    }}
                  >
                    <div className="px-2 py-1 text-[11px] font-semibold tracking-wide border-b mb-1" style={{ borderColor: 'var(--hairline-subtle)', color: 'var(--muted)' }}>
                      {brand} curated draft samples
                    </div>
                    {currentExamples.map((ex) => (
                      <button
                        key={ex.title}
                        type="button"
                        onClick={() => handleSelectExample(ex)}
                        className="w-full text-left p-2 rounded-[2px] hover:bg-black/5 dark:hover:bg-white/5 transition-colors block"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium" style={{ color: 'var(--ink)' }}>
                            {ex.title}
                          </span>
                          <span className="text-[10px] font-mono px-1 rounded" style={{ backgroundColor: 'var(--accent-surface)', color: 'var(--accent-ink)' }}>
                            {ex.category}
                          </span>
                        </div>
                        <p className="text-[11px] mt-0.5 line-clamp-1" style={{ color: 'var(--muted)' }}>
                          {ex.issueType}
                        </p>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Status Message */}
              {statusMsg && (
                <div
                  className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-[2px]"
                  style={{
                    backgroundColor:
                      statusMsg.type === 'success'
                        ? 'var(--status-verified-bg)'
                        : 'var(--severity-blocker-bg)',
                    color:
                      statusMsg.type === 'success'
                        ? 'var(--status-verified)'
                        : 'var(--severity-blocker)',
                  }}
                >
                  {statusMsg.type === 'success' ? (
                    <CheckCircle2 size={13} />
                  ) : (
                    <AlertCircle size={13} />
                  )}
                  <span>{statusMsg.text}</span>
                </div>
              )}
            </div>

            {/* Title: Large borderless serif input */}
            <div className="mb-4">
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Untitled draft"
                className="w-full text-2xl sm:text-3xl font-serif font-semibold bg-transparent border-none p-0 focus:outline-none placeholder:opacity-30"
                style={{ color: 'var(--ink)' }}
              />
            </div>

            {/* Channel Segmented Control & Reading Metric Strip */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-6 border-b mb-6" style={{ borderColor: 'var(--hairline-subtle)' }}>
              {/* Segmented Channel Control */}
              <div
                className="inline-flex p-0.5 rounded-[2px] border text-xs"
                style={{
                  backgroundColor: 'var(--paper)',
                  borderColor: 'var(--hairline)',
                }}
              >
                {channels.map((c) => {
                  const isActive = channel === c.id;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => setChannel(c.id)}
                      className="px-2.5 py-1 rounded-[2px] font-medium transition-all"
                      style={{
                        backgroundColor: isActive ? 'var(--sheet)' : 'transparent',
                        color: isActive ? 'var(--accent-ink)' : 'var(--muted)',
                        boxShadow: isActive ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
                      }}
                    >
                      {c.label}
                    </button>
                  );
                })}
              </div>

              {/* Reading Stats */}
              <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--muted)' }}>
                <span>{wordCount} words</span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Clock size={12} />
                  <span>~{readTimeMin} min read</span>
                </span>
              </div>
            </div>

            {/* Document Body: Autosizing serif textarea, 18px */}
            <div className="flex-1 mb-6">
              <textarea
                ref={textareaRef}
                value={bodyText}
                onChange={(e) => {
                  setBodyText(e.target.value);
                  if (file) setFile(null);
                }}
                placeholder="Paste or write your draft. Nothing is published from here."
                className="w-full bg-transparent border-none p-0 resize-none font-serif text-[18px] leading-relaxed focus:outline-none placeholder:text-[var(--muted)] placeholder:opacity-50"
                style={{
                  color: 'var(--ink)',
                  minHeight: '220px',
                }}
              />
            </div>

            {/* Dashed Hairline File Drop Zone */}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
              className="mt-4 p-4 rounded-[2px] border border-dashed transition-all cursor-pointer flex items-center justify-between"
              style={{
                borderColor: file ? 'var(--accent)' : 'var(--hairline)',
                backgroundColor: file ? 'var(--accent-surface)' : 'transparent',
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".docx,.pdf,.png,.jpg,.jpeg,.txt"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    processFile(e.target.files[0]);
                  }
                }}
              />
              <div className="flex items-center gap-3">
                <Upload size={16} style={{ color: 'var(--muted)' }} />
                <div>
                  <span className="text-xs font-medium" style={{ color: 'var(--ink)' }}>
                    {file ? file.name : 'Upload a document or asset'}
                  </span>
                  <span className="block text-[11px]" style={{ color: 'var(--muted)' }}>
                    {file
                      ? `${(file.size / 1024).toFixed(1)} KB ready for inspection`
                      : 'Drag, drop or select DOCX, PDF, or text files'}
                  </span>
                </div>
              </div>
              <span className="text-xs font-mono" style={{ color: 'var(--accent-ink)' }}>
                {file ? 'Replace' : 'Browse'}
              </span>
            </div>

            {/* Sticky Bottom Bar: Check Draft, Save Draft, Redaction Promise */}
            <div className="pt-6 mt-6 border-t flex flex-col sm:flex-row sm:items-center justify-between gap-4" style={{ borderColor: 'var(--hairline)' }}>
              {/* Redaction promise */}
              <div className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--muted)' }}>
                <Lock size={13} style={{ color: 'var(--accent)' }} />
                <span>
                  {reviewStage || 'Personal data is hidden before anything is analysed'}
                </span>
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleSaveDraft}
                  disabled={loading || (!bodyText.trim() && !file)}
                  className="px-3 py-2 rounded-[2px] border text-xs font-medium transition-colors hover:bg-black/5 dark:hover:bg-white/5 disabled:opacity-40"
                  style={{
                    borderColor: 'var(--hairline)',
                    color: 'var(--graphite)',
                  }}
                >
                  <span className="flex items-center gap-1.5">
                    <Save size={13} />
                    <span>Save draft</span>
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => handleCheckDraft()}
                  disabled={loading || (!bodyText.trim() && !file)}
                  className="px-4 py-2 rounded-[2px] text-xs font-medium transition-all shadow-xs disabled:opacity-40"
                  style={{
                    backgroundColor: 'var(--accent)',
                    color: '#ffffff',
                  }}
                >
                  <span className="flex items-center gap-1.5">
                    <Sparkles size={13} />
                    <span>{loading ? 'Checking...' : 'Check draft'}</span>
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
