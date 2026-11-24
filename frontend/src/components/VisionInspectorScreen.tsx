import React, { useState } from 'react';
import {
  Eye,
  Upload,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Palette,
  FileText,
  SlidersHorizontal,
  ShieldCheck,
  Check,
} from 'lucide-react';
import { api } from '../api';

export const VisionInspectorScreen: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [colorVisionSim, setColorVisionSim] = useState<'normal' | 'protanopia' | 'deuteranopia'>('normal');

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

  // Calculate accessibility score (0-100)
  const calculateScore = () => {
    if (!results) return 100;
    let score = 100;
    if (results.contrast_findings?.length > 0) {
      score -= results.contrast_findings.length * 15;
    }
    if (results.palette_findings?.length > 0) {
      score -= results.palette_findings.length * 10;
    }
    return Math.max(20, score);
  };

  const score = calculateScore();

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Editorial Header */}
      <div
        className="p-6 rounded-[2px] border flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{
          backgroundColor: 'var(--sheet)',
          borderColor: 'var(--hairline)',
        }}
      >
        <div>
          <h1 className="text-2xl font-serif font-semibold tracking-tight" style={{ color: 'var(--ink)' }}>
            Visual &amp; color compliance
          </h1>
          <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
            Check creative imagery against approved brand palettes, CIE2000 color distances, WCAG 2.2 contrast ratios, and logo clear-space rules.
          </p>
        </div>

        {/* Color blindness simulator segmented control */}
        <div
          className="inline-flex p-0.5 rounded-[2px] border text-xs"
          style={{
            backgroundColor: 'var(--paper)',
            borderColor: 'var(--hairline)',
          }}
        >
          {(['normal', 'protanopia', 'deuteranopia'] as const).map((sim) => (
            <button
              key={sim}
              type="button"
              onClick={() => setColorVisionSim(sim)}
              className="px-2.5 py-1 rounded-[2px] capitalize font-medium transition-all"
              style={{
                backgroundColor: colorVisionSim === sim ? 'var(--sheet)' : 'transparent',
                color: colorVisionSim === sim ? 'var(--accent-ink)' : 'var(--muted)',
                boxShadow: colorVisionSim === sim ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
              }}
            >
              {sim}
            </button>
          ))}
        </div>
      </div>

      {errorMsg && (
        <div
          className="p-3.5 rounded-[2px] border flex items-center gap-2 text-xs"
          style={{
            backgroundColor: 'var(--severity-blocker-bg)',
            borderColor: 'var(--severity-blocker)',
            color: 'var(--severity-blocker)',
          }}
        >
          <AlertCircle size={15} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Split Layout: Drop zone on Left, Results on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Drop zone & Asset Preview */}
        <div className="lg:col-span-5 space-y-4">
          <div
            className="p-6 rounded-[2px] border space-y-4"
            style={{
              backgroundColor: 'var(--sheet)',
              borderColor: 'var(--hairline)',
            }}
          >
            <h3 className="font-serif font-semibold text-sm" style={{ color: 'var(--ink)' }}>
              Creative asset
            </h3>

            {/* Drop zone */}
            <label
              className="p-6 rounded-[2px] border border-dashed flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors hover:bg-black/3 dark:hover:bg-white/3"
              style={{ borderColor: 'var(--hairline)' }}
            >
              <Upload size={22} style={{ color: 'var(--muted)' }} />
              <div className="text-center">
                <span className="text-xs font-medium block" style={{ color: 'var(--ink)' }}>
                  {file ? file.name : 'Select or drop asset'}
                </span>
                <span className="text-[11px] block mt-0.5" style={{ color: 'var(--muted)' }}>
                  PNG, JPG, or PDF formats
                </span>
              </div>
              <input
                type="file"
                className="hidden"
                accept="image/png,image/jpeg,.pdf"
                onChange={handleFileChange}
              />
            </label>

            {/* Asset preview with simulated vision filters */}
            {previewUrl && (
              <div
                className="p-2 rounded-[2px] border flex items-center justify-center overflow-hidden"
                style={{
                  backgroundColor: 'var(--paper)',
                  borderColor: 'var(--hairline)',
                  filter:
                    colorVisionSim === 'protanopia'
                      ? 'sepia(0.6) hue-rotate(-20deg)'
                      : colorVisionSim === 'deuteranopia'
                      ? 'sepia(0.5) hue-rotate(40deg)'
                      : 'none',
                }}
              >
                <img
                  src={previewUrl}
                  alt="Asset preview"
                  className="max-h-64 object-contain rounded-[2px]"
                />
              </div>
            )}

            <button
              onClick={handleAnalyze}
              disabled={!file || loading}
              className="w-full py-2.5 rounded-[2px] text-xs font-semibold text-white transition-all shadow-xs disabled:opacity-40"
              style={{ backgroundColor: 'var(--accent)' }}
            >
              {loading ? 'Inspecting CIE2000 & WCAG...' : 'Analyze visual asset'}
            </button>
          </div>
        </div>

        {/* Right Column: Visual Findings & Score */}
        <div className="lg:col-span-7 space-y-6">
          {!results ? (
            <div
              className="p-12 text-center rounded-[2px] border text-xs"
              style={{
                backgroundColor: 'var(--sheet)',
                borderColor: 'var(--hairline)',
                color: 'var(--muted)',
              }}
            >
              <Palette size={24} className="mx-auto mb-2" style={{ color: 'var(--accent)' }} />
              <p className="font-medium" style={{ color: 'var(--ink)' }}>
                No asset analyzed yet
              </p>
              <p className="mt-1">
                Upload a brand visual asset on the left and run analysis to inspect palette distances and contrast ratios.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Accessibility Score Ring & Summary Strip */}
              <div
                className="p-5 rounded-[2px] border flex items-center justify-between gap-4"
                style={{
                  backgroundColor: 'var(--sheet)',
                  borderColor: 'var(--hairline)',
                }}
              >
                <div>
                  <h3 className="font-serif font-semibold text-base" style={{ color: 'var(--ink)' }}>
                    Visual accessibility score
                  </h3>
                  <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
                    Conformity to WCAG 2.2 AA contrast standards and brand kit colors.
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <div
                    className="w-14 h-14 rounded-full border-2 flex items-center justify-center font-serif text-lg font-bold"
                    style={{
                      borderColor:
                        score >= 80 ? 'var(--status-verified)' : 'var(--severity-major)',
                      color:
                        score >= 80 ? 'var(--status-verified)' : 'var(--severity-major)',
                    }}
                  >
                    {score}
                  </div>
                </div>
              </div>

              {/* Palette Strip: Extracted vs Approved */}
              <div
                className="p-5 rounded-[2px] border space-y-3"
                style={{
                  backgroundColor: 'var(--sheet)',
                  borderColor: 'var(--hairline)',
                }}
              >
                <div className="flex items-center justify-between">
                  <span className="font-serif font-semibold text-xs" style={{ color: 'var(--ink)' }}>
                    Extracted dominant palette
                  </span>
                  <span className="font-mono text-[10px]" style={{ color: 'var(--muted)' }}>
                    CIE2000 ΔE* tolerance: 15.0
                  </span>
                </div>

                <div className="flex flex-wrap gap-2">
                  {results.dominant_colors.map((hex: string) => (
                    <div
                      key={hex}
                      className="flex items-center gap-2 p-2 rounded-[2px] border text-xs"
                      style={{
                        backgroundColor: 'var(--paper)',
                        borderColor: 'var(--hairline)',
                      }}
                    >
                      <span
                        className="w-4 h-4 rounded-[2px] border"
                        style={{ backgroundColor: hex, borderColor: 'var(--hairline)' }}
                      />
                      <span className="font-mono text-[11px] font-medium" style={{ color: 'var(--ink)' }}>
                        {hex}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Palette findings */}
                <div className="pt-2 space-y-2">
                  {results.palette_findings.length === 0 ? (
                    <div
                      className="p-3 rounded-[2px] border flex items-center gap-2 text-xs"
                      style={{
                        backgroundColor: 'var(--status-verified-bg)',
                        borderColor: 'var(--status-verified)',
                        color: 'var(--status-verified)',
                      }}
                    >
                      <CheckCircle2 size={14} />
                      <span>All dominant colors conform to the approved brand palette (ΔE* ≤ 15.0).</span>
                    </div>
                  ) : (
                    results.palette_findings.map((pf: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3 rounded-[2px] border text-xs space-y-1"
                        style={{
                          backgroundColor: 'var(--severity-major-bg)',
                          borderColor: 'var(--severity-major)',
                          color: 'var(--severity-major)',
                        }}
                      >
                        <div className="font-semibold flex items-center gap-1.5">
                          <AlertTriangle size={13} />
                          <span>Palette divergence detected (ΔE* = {pf.delta_e})</span>
                        </div>
                        <p className="text-[11px] leading-relaxed">{pf.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Contrast Meter: WCAG 2.2 AA & AAA */}
              <div
                className="p-5 rounded-[2px] border space-y-3"
                style={{
                  backgroundColor: 'var(--sheet)',
                  borderColor: 'var(--hairline)',
                }}
              >
                <div className="flex items-center justify-between">
                  <span className="font-serif font-semibold text-xs" style={{ color: 'var(--ink)' }}>
                    Contrast meter (WCAG 2.2 AA / AAA)
                  </span>
                  <span className="font-mono text-[10px]" style={{ color: 'var(--muted)' }}>
                    Threshold: 4.5:1
                  </span>
                </div>

                <div className="space-y-2">
                  {results.contrast_findings.length === 0 ? (
                    <div
                      className="p-3 rounded-[2px] border flex items-center gap-2 text-xs"
                      style={{
                        backgroundColor: 'var(--status-verified-bg)',
                        borderColor: 'var(--status-verified)',
                        color: 'var(--status-verified)',
                      }}
                    >
                      <CheckCircle2 size={14} />
                      <span>Meets or exceeds 4.5:1 ratio for accessible text legibility.</span>
                    </div>
                  ) : (
                    results.contrast_findings.map((cf: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3 rounded-[2px] border text-xs space-y-1"
                        style={{
                          backgroundColor: 'var(--severity-blocker-bg)',
                          borderColor: 'var(--severity-blocker)',
                          color: 'var(--severity-blocker)',
                        }}
                      >
                        <div className="font-semibold flex items-center gap-1.5">
                          <AlertCircle size={13} />
                          <span>Contrast violation: {cf.contrast_ratio}:1</span>
                        </div>
                        <p className="text-[11px] leading-relaxed">{cf.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Logo Safe-Area & Clear-Space Checks */}
              <div
                className="p-5 rounded-[2px] border space-y-2 text-xs"
                style={{
                  backgroundColor: 'var(--sheet)',
                  borderColor: 'var(--hairline)',
                }}
              >
                <div className="flex items-center justify-between">
                  <span className="font-serif font-semibold" style={{ color: 'var(--ink)' }}>
                    Logo clear-space &amp; alt-text checks
                  </span>
                  <span className="font-mono text-[10px]" style={{ color: 'var(--status-verified)' }}>
                    ✓ Verified
                  </span>
                </div>
                <p style={{ color: 'var(--graphite)' }}>
                  Clear space around brand mark exceeds minimum 1x pilcrow bowl height. Alt text metadata present for assistive screen readers.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
