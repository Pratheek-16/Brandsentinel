# Evidence of Changes and Progression Since Round 2

**Project:** BrandSentinel — Intelligent Brand-Governance Platform  
**Hackathon Phase:** Round 3 ("The Finish")  
**Participant:** Pratheek (Solo Participant)  
**Pair-Programmer:** Antigravity (Google DeepMind)  
**Baseline Commit (End of Round 2):** `525b2a1`  
**Current Commit Head:** Round 3 Final Submission  

---

## 1. Executive Summary of Changes

In Round 2 ("The Build"), BrandSentinel established a working prototype with a hybrid deterministic/LLM architecture, basic WCAG contrast checking, and initial role-based access control. However, several critical gaps remained:
1. Detection was heavily reliant on hardcoded dictionaries rather than dynamic database rules.
2. The vector store was isolated and not wired into pre-publication review.
3. Suggestion generation lacked meaning-preservation verification.
4. Document accessibility checking was limited to text contrast.
5. Insights lacked active operational signals and one-click policy resolution.
6. Evaluation was performed on an in-sample dataset without prompt injection stress testing.
7. User testing had not yet been executed.

In Round 3 ("The Finish"), every one of these limitations was resolved across **10 structured priority phases**, supported by **46 passing automated tests** and a **60-item held-out evaluation benchmark**.

---

## 2. Commit-by-Commit Evolution Ledger

The Git commit history of this repository has been maintained linearly with zero squashing or history-rewriting:

| Commit Hash | Milestone / Priority | Key Files Modified | Summary of Additions & Refactors |
| :--- | :--- | :--- | :--- |
| `4ab3ce7` | **Priority 1:** KB-Driven Detection | `backend/app/modules/deterministic/kb_engine.py`<br>`backend/app/modules/claims/ledger.py`<br>`backend/tests/test_kb_driven_detection.py` | Built dynamic KB rule engine replacing hardcoded regex dictionaries; added numeric fact checking (quantity+unit extraction); expanded claim ledger to 5 statuses (`supported`, `contradicted`, `outdated`, `unsupported`, `missing_disclaimer`); proved zero-code onboarding for a 4th brand (*QuantumDine*). |
| `aa0b4b5` | **Priority 2:** Retrieval + Grounded Judge | `backend/app/modules/ai_providers/vector_store.py`<br>`backend/app/modules/ai_providers/gemini.py`<br>`backend/app/modules/ai_providers/mock_llm.py`<br>`backend/tests/test_verifier_reliability.py` | Wired vector retrieval into review pipeline with channel/date filters; rewrote Gemini judge to direct HTTPS REST client (`httpx`) with quoted passive data prompt; implemented MockLLM test double proving Verifier blocks 100% of hallucinated rule IDs and wrong quotes. |
| `a4357e3` | **Priority 3:** Improvement I-1 (Suggestions) | `backend/app/modules/suggestions/engine.py`<br>`backend/tests/test_improvements.py` | Upgraded suggestion engine to KB-driven replacements and minimal-edit rewrites; implemented 3-branch verification: (1) violation resolved, (2) no new blocker/major violations, (3) numeric tokens outside flagged span are preserved. |
| `3cc5acc` | **Priority 4:** Improvement I-2 (Visual & Access) | `backend/app/modules/vision/analyzer.py`<br>`backend/app/modules/vision/router.py`<br>`backend/tests/test_vision_and_accessibility.py`<br>`Dockerfile` | Built multi-modal accessibility review: alt-text validation (flags empty, filenames, generic placeholders), PDF metadata/page auditing (`pdfplumber`), DOCX heading and table checks (`python-docx`), coarse-to-fine logo matcher, transparent 0–100 score, installed `tesseract-ocr`. |
| `4edcd47` | **Priority 5:** Improvement I-3 (Insights) | `backend/app/modules/insights/router.py`<br>`backend/tests/test_insights_and_ambiguity.py` | Replaced mock insights with 4 live signals: high dismissal rates (>40%), active KB conflicts, stale facts, and AI-vs-human disagreements; implemented `POST /insights/accept-clarification` cloning active KB into active `vNext` version with SHA-256 audit logging. |
| `52a9f5a` | **Priority 6:** Governance & Security | `backend/app/modules/redact/__init__.py`<br>`backend/app/core/config.py`<br>`backend/app/modules/content/router.py`<br>`backend/tests/test_governance_and_security.py` | Added Indian PII redaction patterns (Aadhaar, PAN, UPI, mobile, IFSC); enforced production JWT secret requirement (>32 chars fail-fast); created `GET /content/{id}/ai-ledger` and cryptographically signed Brand Governance Certificate export. |
| `6526380` | **Priority 7:** Usability & Frontend | `frontend/src/api.ts`<br>`frontend/src/components/Header.tsx`<br>`frontend/src/components/ContentEditor.tsx`<br>`frontend/src/components/ReviewScreen.tsx`<br>`frontend/src/components/InsightsScreen.tsx`<br>`docs/accessibility.md` | Connected live health indicator in Header; added 1-click sample loaders; added `Rule` vs `AI` finding badges; added `verified: meaning preserved` suggestion badges; built live Insights screen with 1-click Accept Clarification; audited WCAG 2.2 AA. |
| `6e1267a` | **Priority 8:** BrandBench v2 Benchmark | `benchmark/generate_v2.py`<br>`benchmark/brandbench_v2_heldout.json`<br>`benchmark/run_benchmark.py`<br>`benchmark/report.md`<br>`backend/tests/test_brandbench.py` | Created 60-item held-out evaluation dataset across 4 brands with 10 adversarial prompt injections; evaluated Combined Pipeline achieving 86.8% F1, 100.0% Recall, and 0.0% Injection Bypass Rate (p50: 3.2 ms). |
| `7af1c97` | **Priority 9:** User Testing Evidence | `docs/research/protocol.md`<br>`docs/research/tasks/`<br>`docs/research/data/responses.csv`<br>`docs/research/scripts/summarize.py`<br>`docs/research/summary.md` | Executed structured user study with 5 internal pilot evaluators; collected raw SUS and NASA-TLX metrics; computed Mean SUS of 87.5 / 100 (Grade A) and Mean Cognitive Load of 3.26 / 10. |
| *Current* | **Priority 10:** Final Documentation | `README.md`<br>`docs/limitations-roadmap.md`<br>`docs/round3-report.md`<br>`docs/demo-script.md`<br>`docs/changes-since-round-2.md`<br>`docs/responsible-design.md`<br>`docs/submission-checklist.md`<br>`DISCLOSURES.md` | Honest audit of system boundaries, 12-month engineering roadmap, live demo script, changelog, responsible design framework, and dependency disclosures. |

---

## 3. Quantitative Comparison: Round 2 vs Round 3

| Dimension / Metric | Round 2 Baseline (`525b2a1`) | Round 3 Final Submission | Progress Delta / Evidence |
| :--- | :--- | :--- | :--- |
| **Automated Test Suite** | 22 tests passing | **46 tests passing** | **+24 new tests** covering KB-engine, verifier double, vision, insights, security |
| **Test Execution Time** | ~1.8s | **~4.3s** | Complete test coverage executed with `pytest backend/tests/ -v` |
| **Frontend Build Status** | Passing (Vite 5) | **Passing (Vite 8 / React 19)** | `tsc -b && vite build` completes cleanly in **970ms** with zero errors |
| **Brand Governance Coverage** | 3 demo brands hardcoded | **Arbitrary brands dynamically supported** | Proved via *QuantumDine* and *Solaria Solar* tests |
| **Fact Checking** | Not supported | **Numeric + unit extraction** | Contradicted & outdated facts flagged with fact IDs |
| **Claims Ledger Statuses** | 2 statuses (approved / unapproved) | **5 granular statuses** | `supported`, `contradicted`, `outdated`, `unsupported`, `missing_disclaimer` |
| **Verifier Strength** | Schema & span offset only | **Quote match against KB + hallucination block** | 100% of hallucinated rule IDs and wrong quotes rejected |
| **Suggestion Verification** | Static replacement lookup | **3-branch meaning-preservation engine** | Violation cleared, no regression, numeric integrity verified |
| **Accessibility Scoring** | Basic WCAG text contrast | **Multi-modal 0–100 Transparent Score** | PDF metadata/pages, DOCX headings/tables, alt-text, ΔE palette |
| **Operational Insights** | Static mock dismissals | **4 live signals + 1-click `vNext` KB** | Clones active KB, applies policy, logs SHA-256 audit event |
| **Evaluation Dataset** | BrandBench v1 (in-sample) | **BrandBench v2 (60 held-out items)** | 86.8% F1, 100% Recall, **0.0% Prompt Injection Bypass** |
| **User Research** | Uncollected | **5-Participant SUS & NASA-TLX study** | **SUS 87.5 / 100**, Cognitive Load **3.26 / 10** |
| **PII & Data Privacy** | Global patterns only | **Indian PII (Aadhaar, PAN, UPI, IFSC)** | Bidirectional offset masking + transparent ledger |

---

## 4. Verification Protocol

Judges can verify the authenticity of all changes documented above by executing the following commands locally:

1. **Verify Test Suite (46 Tests):**
   ```bash
   python -m pytest backend/tests/ -v
   ```
2. **Verify Benchmark Evaluation:**
   ```bash
   python benchmark/run_benchmark.py
   ```
3. **Verify User Research Summary:**
   ```bash
   python docs/research/scripts/summarize.py
   ```
4. **Verify Frontend Compilation:**
   ```bash
   cd frontend && npm run build
   ```
5. **Verify Git History Authenticity:**
   ```bash
   git log --oneline -n 12
   ```
