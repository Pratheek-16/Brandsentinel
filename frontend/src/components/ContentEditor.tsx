import React, { useState } from 'react';
import { FileText, Upload, Sparkles, Send, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../api';

interface ContentEditorProps {
  onReviewCreated: (contentId: number) => void;
}

export const ContentEditor: React.FC<ContentEditorProps> = ({ onReviewCreated }) => {
  const [title, setTitle] = useState('');
  const [channel, setChannel] = useState('social');
  const [contentType, setContentType] = useState('text');
  const [bodyText, setBodyText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const sampleCopies = [
    {
      label: 'Sample with Brand Issues',
      title: 'Q2 Promo Campaign',
      body: 'Reach out to support@novafit.local or call 555-019-2831. We promise 100% satisfaction guaranteed! Try the cheapest fitness tracker today for free forever.',
    },
    {
      label: 'Sample Clean Compliant',
      title: 'Spring Member Welcome',
      body: 'Welcome to NovaFit. Our premier training programs are designed to support your wellness journey with certified coaches. Terms apply.',
    },
  ];

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatusMsg(null);
    try {
      let contentId: number;
      if (file) {
        const formData = new FormData();
        formData.append('title', title || 'Uploaded Document');
        formData.append('type', contentType);
        formData.append('channel', channel);
        formData.append('file', file);
        const res = await api.uploadContent(formData);
        contentId = res.content_id;
      } else {
        if (!bodyText.trim()) throw new Error('Please enter draft copy text.');
        const res = await api.createContent({
          title: title || 'Draft Content',
          type: 'text',
          channel,
          body: bodyText,
        });
        contentId = res.content_id;
      }

      setStatusMsg({ type: 'success', text: `Draft created (ID: ${contentId}). Initiating AI Brand Review...` });

      // Automatically trigger AI review
      await api.reviewContent(contentId);
      onReviewCreated(contentId);
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to submit content' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Create & Submit Content</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Draft or upload materials. Content is pre-screened with PII redaction and checked against brand guidelines.
            </p>
          </div>
          <div className="flex space-x-2">
            {sampleCopies.map((s) => (
              <button
                key={s.label}
                type="button"
                onClick={() => {
                  setTitle(s.title);
                  setBodyText(s.body);
                  setFile(null);
                }}
                className="text-xs px-2.5 py-1 bg-white border border-slate-300 rounded hover:bg-slate-100 text-slate-700 font-medium transition-colors"
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {statusMsg && (
          <div
            className={`p-4 flex items-center space-x-2 text-xs font-medium ${
              statusMsg.type === 'success' ? 'bg-emerald-50 text-emerald-800 border-b border-emerald-200' : 'bg-red-50 text-red-800 border-b border-red-200'
            }`}
          >
            {statusMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
            <span>{statusMsg.text}</span>
          </div>
        )}

        <form onSubmit={handleCreate} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label htmlFor="content-title" className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Campaign / Document Title
              </label>
              <input
                id="content-title"
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Summer Health Launch - Email Newsletter"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label htmlFor="channel-select" className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Distribution Channel
              </label>
              <select
                id="channel-select"
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              >
                <option value="social">Social Media</option>
                <option value="email">Email Campaign</option>
                <option value="website">Website / Blog</option>
                <option value="ad">Digital Advertising</option>
                <option value="print">Print Collateral</option>
              </select>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="body-editor" className="block text-xs font-bold text-slate-700 uppercase">
                Content Body (Plain Text or Pasted Copy)
              </label>
              <span className="text-xs text-slate-400">{bodyText.length} characters</span>
            </div>
            <textarea
              id="body-editor"
              rows={8}
              value={bodyText}
              onChange={(e) => {
                setBodyText(e.target.value);
                if (file) setFile(null);
              }}
              placeholder="Paste draft copy here to evaluate tone, terminology, facts, claims, and accessibility..."
              className="w-full p-3 text-sm font-mono border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none leading-relaxed"
            />
          </div>

          <div className="border-t border-slate-200 pt-4">
            <label className="block text-xs font-bold text-slate-700 uppercase mb-2">
              Or Upload Asset Document (DOCX, PDF, PNG/JPG)
            </label>
            <div className="flex items-center space-x-4">
              <label className="cursor-pointer flex items-center space-x-2 px-4 py-2 border border-slate-300 rounded-md hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors">
                <Upload className="w-4 h-4 text-slate-500" />
                <span>Choose File</span>
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
                <span className="text-xs text-blue-600 font-mono bg-blue-50 px-2.5 py-1 rounded border border-blue-200">
                  {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </span>
              )}
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-md shadow-sm transition-colors disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'Processing & Redacting...' : 'Run AI Brand Review'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
