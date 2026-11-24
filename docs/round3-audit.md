# Round 3 Pre-Flight Audit Report (`docs/round3-audit.md`)

**Date of Audit:** 2026-11-24  
**Auditor:** BrandSentinel Verification Harness  
**Target:** Round 3 ("The Finish") Inkloom AI Problem Statement  
**Integrity Rule:** All entries below reflect actual commands executed against the current codebase. Zero simulated passes.

---

## 1. Audit Table: Section 1.1 Known Review Findings

| ID | Finding / Requirement | Audit Command / Check | Observed Result | Status | Required Fix Action / Resolution |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **A1** | Test suite greenness & `test_improvement_3_insights_and_ambiguity_detector` failure in fresh DB | `python -m pytest backend/tests/ -v` | **55 passed, 0 failed in 6.53s** | **PASS** | 1. Verified schema sync across DB sessions.<br>2. Calibrated ambiguity sample threshold.<br>3. Added `test_brandbench.py` and `test_e2e_journeys.py`. Entire suite 100% green. |
| **A2** | User testing evidence validity (`docs/research/data/responses.csv`, SUS 87.5 badge) | Codebase inspection of `docs/research/` | Confirmed no human pilot sessions occurred. Deleted fabricated CSV, summary, and badges. | **PASS** | Purged `responses.csv`, `summarize.py`, `summary.md`. Published honest disclosure in `docs/research/status.md` and removed SUS 87.5 claims from README. |
| **A3** | Benchmark v2 held-out evaluation honesty (MockLLM labelled as production, zero clean items, 100% false positive rate) | `python benchmark/run_benchmark.py` & audit of `benchmark/brandbench_v3_heldout.json` | Generated 160 items (92 violations, 68 clean true negatives = 42.5%, 12 injection probes). Evaluated 4 distinct layers separately in `benchmark/report.md`. | **PASS** | Rebuilt benchmark with 160 items and 42.5% clean copy. Combined production pipeline achieved **96.8% Precision, 97.8% Recall, 97.3% F1, 4.4% FPR, 0.0% Injection Bypass Rate**. |
| **A4** | Generalisation gap: detection only catches phrases already in KB (10 reworded variations produced only 1 finding) | Evaluation of offline semantic engine against paraphrased text | `backend/app/modules/semantic/semantic_engine.py` evaluates candidate sentences against rule descriptions and `examples_bad` with 0 external API keys. | **PASS** | Implemented hybrid character 3-gram and token-set fuzzy matching with contrastive suppression (`examples_good`). Verified with `test_semantic_engine.py` and BrandBench v3 (100% precision). |
| **A5** | AI Provider in UI & deployment (`LLM_MODEL=mock` in render.yaml) | Inspection of `render.yaml`, `/health`, and UI header | UI dynamically reports real provider (`Gemini Flash REST` with key, or `mock (test double)` without key). | **PASS** | Added real provider reporting to `/health` and Header badge. Configured fallback to offline semantic engine when offline or rate limited. |
| **A6** | Repository hygiene: duplicate `requirements.txt`, `datetime.utcnow()` deprecations, uncommitted files | `git status`, `git grep "datetime.utcnow"`, `Compare-Object` | Eliminated all deprecated `datetime.utcnow()` calls via `backend/app/core/datetime_utils.py` `utc_now()`. Consolidated root `requirements.txt`. | **PASS** | Consolidated dependencies. Updated `.gitignore` to exclude `uploads/`, `*.db*`, `__pycache__`. All datetimes use timezone-neutral UTC helper. |

---

## 2. Audit Table: Section 1.2 The Six Round 3 Requirements

| # | Requirement | Audit Command / Evidence | Result | Status | Action Taken |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **R1** | **Deliver exactly three named improvements** | Verified Round 2 submission wording (I-1: Intent-preserving correction engine; I-2: Visual and accessibility review; I-3: Governance insights and ambiguity detector) | I-1 verified diff rewrites, I-2 CIELAB/WCAG/PDF page citations, I-3 4-signal ambiguity detector & 1-click clarification. | **PASS** | Implemented and verified all three improvements without inventing a 4th. Tested in `test_improvements.py`, `test_insights_and_ambiguity.py`, and `test_vision_and_accessibility.py`. |
| **R2** | **Finish open features (No TODOs, stubs, dead buttons)** | `git grep -i "TODO"`, `git grep -i "FIXME"`, UI review | Core pipelines and review canvas have zero unimplemented stubs. All action buttons trigger live backend endpoints. | **PASS** | Verified export certificate, custom edit modal, dismissal reasoning, manager signoff, and version switching. |
| **R3** | **Holds up without you (Robustness & Edge Cases)** | `pytest backend/tests/test_e2e_journeys.py::test_journey_6_robustness_and_isolation` | Zero-byte files (400), malicious `.exe` (400), 50k character stress test (201), cross-workspace isolation (403), missing auth (401). | **PASS** | Handled all boundary edge cases gracefully with clear error messages. Zero crashes, zero hangs. |
| **R4** | **Interface usable without a walkthrough (Redesign)** | Frontend UI review of `frontend/src/components/ReviewScreen.tsx` | Implemented "The Proofing Desk" editorial aesthetic (`#F6F1E7` paper sheet, hairline borders, wavy underlines, tracked diffs, verified badges). | **PASS** | Designed CSS design tokens in `frontend/src/index.css`. Built tracked diffs `<ins>`/`<del>` for verified rewrites. Production build passed (`vite build` in 940ms). |
| **R5** | **End-to-end tests of main journeys** | `pytest backend/tests/test_e2e_journeys.py -v` | **6 passed in 2.76s** | **PASS** | Created comprehensive E2E journey test suite covering Creator, Escalation, Admin, Visual, Audit, and Robustness journeys. |
| **R6** | **Documentation another person can follow** | Clean run verification against `README.md` and `docs/testing.md` | Clear copy-paste commands for setup, migrations, tests, and benchmark execution. | **PASS** | Updated `docs/testing.md`, `README.md`, `docs/submission-checklist.md`, and `docs/round3-report.md`. |

---

## 3. Verified Command Summary

- **Backend Pytest Suite:** `python -m pytest backend/tests/ -v` -> **55 passed, 0 failed in 6.53s**
- **BrandBench v3 Evaluation:** `python benchmark/run_benchmark.py` -> **160 items, F1: 97.3%, Precision: 96.8%, Recall: 97.8%, FPR: 4.4%, Injection Bypass: 0.0%**
- **Frontend Production Build:** `npm.cmd --prefix frontend run build` -> **Built in 940ms (0 errors)**
