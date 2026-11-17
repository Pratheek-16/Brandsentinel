import React, { useState } from 'react';
import { Eye, Upload, CheckCircle2, AlertTriangle, AlertCircle, Palette } from 'lucide-react';
import { api } from '../api';

export const VisionInspectorScreen: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setFile(f);
      setPreviewUrl(URL.createObjectURL(f));
      setResults(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    try {
      setLoading(true);
      const res = await api.analyzeVision(file);
      setResults(res.results);
    } catch (err: any) {
      alert(err.message || 'Vision analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h1 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <Eye className="w-5 h-5 text-blue-600" />
          <span>Improvement I-2: Multimodal Visual Consistency & Contrast Inspector</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Evaluates images (PNG/JPG) for palette deviation (CIELAB ΔE) and WCAG 2.2 AA accessibility contrast ratios.
        </p>

        <div className="mt-6 flex flex-wrap items-center gap-4">
          <label className="cursor-pointer flex items-center space-x-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-md border border-slate-300 transition-colors">
            <Upload className="w-4 h-4 text-slate-500" />
            <span>Select Image File</span>
            <input type="file" className="hidden" accept="image/png,image/jpeg" onChange={handleFileChange} />
          </label>

          {file && (
            <span className="text-xs font-mono text-slate-600 bg-slate-50 px-2 py-1 rounded border">
              {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </span>
          )}

          <button
            onClick={handleAnalyze}
            disabled={!file || loading}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors disabled:opacity-50"
          >
            {loading ? 'Inspecting CIELAB & WCAG...' : 'Analyze Visual Compliance'}
          </button>
        </div>
      </div>

      {previewUrl && (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Image Preview */}
          <div className="md:col-span-5 bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center">
            <img src={previewUrl} alt="Upload preview" className="max-h-80 rounded object-contain border" />
          </div>

          {/* Results Inspector */}
          <div className="md:col-span-7 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-2">
              <Palette className="w-4 h-4 text-blue-600" />
              <span>Inspection Metrics</span>
            </h2>

            {!results ? (
              <div className="text-xs text-slate-400 py-8 text-center">
                Click "Analyze Visual Compliance" to extract dominant colors and compute ΔE distances.
              </div>
            ) : (
              <div className="space-y-4 text-xs">
                {/* Dominant Colors */}
                <div>
                  <span className="font-semibold text-slate-700 block mb-1">Extracted Dominant Colors:</span>
                  <div className="flex space-x-2">
                    {results.dominant_colors.map((hex: string) => (
                      <div key={hex} className="flex items-center space-x-1.5 p-1.5 border rounded bg-slate-50">
                        <span className="w-4 h-4 rounded-full border shadow-inner" style={{ backgroundColor: hex }} />
                        <span className="font-mono text-[11px] font-bold text-slate-700">{hex}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Palette Compliance Findings */}
                <div className="space-y-2">
                  <span className="font-semibold text-slate-700 block">CIELAB ΔE Palette Distance:</span>
                  {results.palette_findings.length === 0 ? (
                    <div className="p-3 bg-emerald-50 text-emerald-800 rounded border border-emerald-200 flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>All dominant colors conform to the approved brand palette (ΔE ≤ 15.0).</span>
                    </div>
                  ) : (
                    results.palette_findings.map((pf: any, idx: number) => (
                      <div key={idx} className="p-3 bg-amber-50 text-amber-900 rounded border border-amber-200 space-y-1">
                        <div className="flex items-center space-x-1.5 font-bold">
                          <AlertTriangle className="w-4 h-4 text-amber-600" />
                          <span>Palette Divergence Detected (ΔE = {pf.delta_e})</span>
                        </div>
                        <div>{pf.message}</div>
                      </div>
                    ))
                  )}
                </div>

                {/* Contrast Findings */}
                <div className="space-y-2">
                  <span className="font-semibold text-slate-700 block">WCAG 2.2 AA Contrast Compliance:</span>
                  {results.contrast_findings.length === 0 ? (
                    <div className="p-3 bg-emerald-50 text-emerald-800 rounded border border-emerald-200 flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>Meets or exceeds minimum 4.5:1 contrast requirement for legibility.</span>
                    </div>
                  ) : (
                    results.contrast_findings.map((cf: any, idx: number) => (
                      <div key={idx} className="p-3 bg-red-50 text-red-900 rounded border border-red-200 space-y-1">
                        <div className="flex items-center space-x-1.5 font-bold">
                          <AlertCircle className="w-4 h-4 text-red-600" />
                          <span>Accessibility Issue: {cf.contrast_ratio}:1 Contrast</span>
                        </div>
                        <div>{cf.message}</div>
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
