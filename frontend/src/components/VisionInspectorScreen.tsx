import React, { useState } from 'react';
import { Eye, Upload, CheckCircle2, AlertTriangle, AlertCircle, Palette, FileText, Info } from 'lucide-react';
import { api } from '../api';

export const VisionInspectorScreen: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setFile(f);
      setErrorMsg(null);
      if (f.type.startsWith('image/')) {
        setPreviewUrl(URL.createObjectURL(f));
      } else {
        setPreviewUrl(null);
      }
      setResults(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    try {
      setLoading(true);
      setErrorMsg(null);
      const res = await api.analyzeVision(file);
      setResults(res.results);
    } catch (err: any) {
      setErrorMsg(err.message || 'Vision analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
            <Eye className="w-5 h-5 text-blue-600" />
            <span>Multimodal Visual Consistency & Accessibility (Improvement I-2)</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Evaluates creative assets (PNG, JPG, PDF) for approved brand palette conformity (CIELAB ΔE* distance) and WCAG 2.2 AA accessibility contrast ratios.
          </p>
        </div>

        {/* Honest Disclosure Banner */}
        <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-lg flex items-start space-x-2.5 text-xs text-blue-900">
          <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <strong>Multimodal OCR Notice:</strong> If local Tesseract OCR binaries are not detected on Windows, visual inspection gracefully degrades to pure pixel CIELAB palette clustering and WCAG 2.2 AA contrast matrix calculations.
          </div>
        </div>

        <div className="pt-2 flex flex-wrap items-center gap-4">
          <label className="cursor-pointer flex items-center space-x-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-lg border border-slate-300 transition-colors shadow-2xs">
            <Upload className="w-4 h-4 text-slate-500" />
            <span>Select Image or PDF</span>
            <input
              type="file"
              className="hidden"
              accept="image/png,image/jpeg,.pdf"
              onChange={handleFileChange}
            />
          </label>

          {file && (
            <span className="text-xs font-mono text-slate-700 bg-slate-50 px-3 py-1.5 rounded-lg border">
              {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </span>
          )}

          <button
            onClick={handleAnalyze}
            disabled={!file || loading}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors disabled:opacity-50"
          >
            {loading ? 'Inspecting CIELAB & WCAG...' : 'Analyze Visual Asset'}
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center space-x-2 text-xs text-red-900">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
          <span>{errorMsg}</span>
        </div>
      )}

      {file && (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* File Preview */}
          <div className="md:col-span-5 bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center min-h-[260px]">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Upload preview"
                className="max-h-80 rounded-lg object-contain border shadow-2xs"
              />
            ) : (
              <div className="text-center p-6 text-slate-400 space-y-2">
                <FileText className="w-12 h-12 mx-auto text-slate-300" />
                <div className="text-xs font-semibold text-slate-600">{file.name}</div>
                <div className="text-[11px]">PDF Document Asset</div>
              </div>
            )}
          </div>

          {/* Results Inspector */}
          <div className="md:col-span-7 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-2">
              <Palette className="w-4 h-4 text-blue-600" />
              <span>Inspection Compliance Report</span>
            </h2>

            {!results ? (
              <div className="text-xs text-slate-400 py-12 text-center">
                Click "Analyze Visual Asset" to extract dominant colors and verify against brand palette.
              </div>
            ) : (
              <div className="space-y-5 text-xs">
                {/* Dominant Colors */}
                <div>
                  <span className="font-bold text-slate-700 block mb-2 uppercase text-[11px]">
                    Extracted Dominant Colors:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {results.dominant_colors.map((hex: string) => (
                      <div key={hex} className="flex items-center space-x-2 p-2 border rounded-lg bg-slate-50 shadow-2xs">
                        <span
                          className="w-5 h-5 rounded-full border shadow-inner shrink-0"
                          style={{ backgroundColor: hex }}
                        />
                        <span className="font-mono text-xs font-bold text-slate-800">{hex}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* CIELAB Delta E Findings */}
                <div className="space-y-2.5">
                  <span className="font-bold text-slate-700 block uppercase text-[11px]">
                    CIELAB ΔE* Brand Palette Conformity:
                  </span>
                  {results.palette_findings.length === 0 ? (
                    <div className="p-3 bg-emerald-50 text-emerald-900 rounded-lg border border-emerald-200 flex items-center space-x-2.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>All dominant colors conform strictly to the brand palette (ΔE* ≤ 15.0).</span>
                    </div>
                  ) : (
                    results.palette_findings.map((pf: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3 bg-amber-50 text-amber-950 rounded-lg border border-amber-200 space-y-1"
                      >
                        <div className="flex items-center space-x-2 font-bold">
                          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                          <span>Palette Divergence Detected (ΔE* = {pf.delta_e})</span>
                        </div>
                        <div className="text-[11px] leading-relaxed">{pf.message}</div>
                      </div>
                    ))
                  )}
                </div>

                {/* WCAG 2.2 AA Contrast Findings */}
                <div className="space-y-2.5">
                  <span className="font-bold text-slate-700 block uppercase text-[11px]">
                    WCAG 2.2 AA Accessibility Contrast:
                  </span>
                  {results.contrast_findings.length === 0 ? (
                    <div className="p-3 bg-emerald-50 text-emerald-900 rounded-lg border border-emerald-200 flex items-center space-x-2.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>Meets or exceeds 4.5:1 contrast requirement for accessible text legibility.</span>
                    </div>
                  ) : (
                    results.contrast_findings.map((cf: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3 bg-red-50 text-red-950 rounded-lg border border-red-200 space-y-1"
                      >
                        <div className="flex items-center space-x-2 font-bold">
                          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                          <span>Contrast Violation: {cf.contrast_ratio}:1 (Below 4.5:1 AA Threshold)</span>
                        </div>
                        <div className="text-[11px] leading-relaxed">{cf.message}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
