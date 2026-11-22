# BrandSentinel

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.3-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6.svg)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.3-38B2AC.svg)](https://tailwindcss.com)
[![Test Suite](https://img.shields.io/badge/Tests-46%20Passed-brightgreen.svg)](backend/tests)
[![Benchmark F1](https://img.shields.io/badge/BrandBench%20v2%20F1-86.8%25-blue.svg)](benchmark/report.md)
[![SUS Score](https://img.shields.io/badge/Usability%20SUS-87.5%20(Grade%20A)-success.svg)](docs/research/summary.md)

**BrandSentinel** is an intelligent, pre-publication brand-governance and compliance platform built for the **Inkloom AI Brand-Governance Hackathon (Round 3: "The Finish")**.

It enables marketing, copy, and legal review teams to audit pre-publication text, documents (DOCX, PDF), and visual assets against approved brand guidelines, factual records, approved terminology, regulatory claim registers, and visual palettes. Every finding is mathematically grounded with direct citations, paired with verified intent-preserving rewrite suggestions, and routed through a tamper-evident, role-based review workflow.

---

## Deliverables & Documentation Index

- **Round 3 Final Report:** [`docs/round3-report.md`](docs/round3-report.md) (~8 pages: Problem, Users, Architecture, 3 Improvements, Reliability, Security, Roadmap)
- **Live Judging Walkthrough Script:** [`docs/demo-script.md`](docs/demo-script.md) (Step-by-step walkthrough for all personas)
- **BrandBench v2 Evaluation Report:** [`benchmark/report.md`](benchmark/report.md) (60 held-out cases, 0.0% injection bypass, F1 86.8%)
- **Accessibility & WCAG 2.2 AA Audit:** [`docs/accessibility.md`](docs/accessibility.md) (Contrast, focus, ARIA, and asset inspector specs)
- **User Research & SUS Summary:** [`docs/research/summary.md`](docs/research/summary.md) (N=5 pilot participants, SUS 87.5, median task times)
- **Changes Since Round 2:** [`docs/changes-since-round-2.md`](docs/changes-since-round-2.md) (Commit-by-commit changelog)
- **Responsible Design & Privacy:** [`docs/responsible-design.md`](docs/responsible-design.md) (Redaction, human agency, no dark patterns)
- **Limitations & 12-Month Roadmap:** [`docs/limitations-roadmap.md`](docs/limitations-roadmap.md) (Honest known boundaries and phased plans)
- **Submission Checklist:** [`docs/submission-checklist.md`](docs/submission-checklist.md) (Audit against all 100 judging points)
- **Disclosures & Attribution:** [`DISCLOSURES.md`](DISCLOSURES.md) (AI tools, open-source libraries, and licenses)

---

## System Architecture

```
                    +------------------------------------------+
                    |  Pre-Publication Draft Copy or Document  |
                    |       (Plain Text, Markdown, DOCX, PDF)  |
                    +------------------------------------------+
                                          |
                                          v
                    +------------------------------------------+
                    | PII Redaction & Indian Data Protection   |
                    | (Aadhaar, PAN, UPI, IFSC, Phone, Secrets)|
                    +------------------------------------------+
                                          |
                     +--------------------+--------------------+
                     |                                         |
                     v                                         v
   +------------------------------------+   +------------------------------------+
   |   LAYER 1: DETERMINISTIC ENGINE    |   |     LAYER 2: GROUNDED LLM JUDGE    |
   | Dynamic KB Rule, Fact & Term Match |   |  RAG Top-k Semantic Vector Search  |
   | Exact, Lemmatised & RapidFuzz Match|   |  Prompt-Injection-Resistant Judge  |
   | Numeric Fact & Unit Contradictions |   |  Low Temp, Strict Pydantic Schema  |
   +------------------------------------+   +------------------------------------+
                     |                                         |
                     |                                         v
                     |                      +------------------------------------+
                     |                      |        GROUNDING VERIFIER          |
                     |                      | 1. Cited Rule/Fact exists in KB    |
                     |                      | 2. Quote matches stored KB text    |
                     |                      | 3. Span offsets locate exact text  |
                     |                      | * Drops ungrounded hallucinations  |
                     |                      +------------------------------------+
                     |                                         |
                     +--------------------+--------------------+
                                          |
                                          v
                    +------------------------------------------+
                    |   DEDUPLICATION & PROVENANCE MERGING     |
                    | Source: "Rule (Deterministic)" vs "AI"   |
                    +------------------------------------------+
                                          |
         +--------------------------------+--------------------------------+
         |                                |                                |
         v                                v                                v
+-------------------+           +--------------------+           +-------------------+
|  IMPROVEMENT I-1  |           |   IMPROVEMENT I-2  |           |  IMPROVEMENT I-3  |
| Verified Suggest- |           | Visual Palette dE, |           | Governance In-    |
| ion Engine with   |           | WCAG 2.2 AA Con-   |           | sights & Ambiguity|
| Meaning Preserv-  |           | trast, DOCX/PDF    |           | Detector (4 Real  |
| ation Checking    |           | Accessibility (0-  |           | Signals + Accept  |
|                   |           | 100 Score Breakdown|           | Clarification vNext|
+-------------------+           +--------------------+           +-------------------+
         |                                |                                |
         +--------------------------------+--------------------------------+
                                          |
                                          v
                    +------------------------------------------+
                    |      FOUR-EYES RBAC & AUDIT LEDGER       |
                    | No Self-Approval (Creator != Reviewer)   |
                    | SHA-256 Chained Immutable Audit Log      |
                    | Brand Governance Certificate Export      |
                    +------------------------------------------+
```

---

## The Three Hackathon Improvements

### Improvement I-1: Intent-Preserving Suggestion Engine
- Generates up to 3 verified alternatives per finding using active KB preferred terms, approved claims, and contextual minimal rewrites.
- **3-Branch Verification:** Slices each candidate fix into the text and runs the full pipeline:
  1. The original violation must be completely resolved.
  2. No new blocker or major severity violations may be introduced.
  3. Meaning preservation check ensures numbers and factual quantities outside the flagged span remain unmodified.
- Surfaced in the UI with a distinct `verified: meaning preserved` badge and 1-click application.

### Improvement I-2: Multi-Format Visual & Accessibility Review
- **Palette Adherence:** CIELAB $\Delta E^*$ (CIE76 Euclidean distance) calculation against approved brand colors ($\Delta E^* \le 12.0$ matches; $> 15.0$ flagged).
- **WCAG 2.2 AA Contrast:** Evaluates relative luminance contrast ratio against the statutory 4.5:1 standard.
- **Alt-Text Audit:** Validates presence and descriptiveness on raster images, DOCX embedded drawings (`wp:docPr`), and PDF page rasters.
- **Document Structure:** Detects heading-level skips (Heading 1 -> Heading 3), vague hyperlink anchors ("click here"), and tables missing assistive header rows (`tblHeader`).
- **Transparent Accessibility Score (0-100):** Displayed with full itemized deductions breakdown (`-15` contrast, `-10` alt-text, `-10` heading skip, `-10` table header, `-5` title/language).

### Improvement I-3: Governance Insights & Ambiguity Signal Engine
- Evaluates four real operational signals across workspace activity:
  1. **High Creator Dismissals:** Guidelines with $> 40\%$ dismissal rate (minimum sample size $\ge 3$).
  2. **Active KB Conflicts:** Prohibited terms that are also listed as preferred, or facts with overlapping dates and contradictory values.
  3. **Stale Facts:** Product specifications whose `valid_to` date has passed or unreviewed for $> 90$ days.
  4. **AI-vs-Human Disagreement:** Findings flagged by automated models but dismissed by human reviewers as contextually permissible.
- **1-Click Actionability:** `POST /insights/accept-clarification` clones the active KB version, applies the clarified policy, marks it active (`vNext`), deactivates the old version, and logs an immutable audit event.

---

## Seeded Demo Accounts

All seeded demo accounts use the standard password: `Demo@12345`

| Workspace | Role | Email | Best For Testing |
|---|---|---|---|
| **NovaFit** | Creator | `creator1@novafit.local` | Draft submission, sample loader, verified suggestions |
| **NovaFit** | Reviewer | `reviewer1@novafit.local` | Escalation queue, four-eyes approval, signing |
| **NovaFit** | Manager | `manager1@novafit.local` | Manager review queue, approval with notes |
| **NovaFit** | Admin | `admin@novafit.local` | KB editing, Insights ambiguity detector, accept clarification |
| **Lumen Bank** | Creator | `creator1@lumenbank.local` | Financial copy with missing APR disclaimers |
| **Lumen Bank** | Reviewer | `reviewer1@lumenbank.local` | High-risk financial claims evaluation |
| **Lumen Bank** | Manager | `manager1@lumenbank.local` | Regulatory review and change requests |
| **Lumen Bank** | Admin | `admin@lumenbank.local` | Banking KB configuration |
| **Aster University** | Creator | `creator1@aster.local` | Academic marketing, outdated accreditation facts |
| **Aster University** | Reviewer | `reviewer1@aster.local` | Scholarly tone verification |
| **Aster University** | Manager | `manager1@aster.local` | Convocation and admissions copy approval |
| **Aster University** | Admin | `admin@aster.local` | Higher-ed KB configuration |

---

## Quickstart Guide

### Option 1: Native Local Run (Windows, macOS, Linux)

#### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Pratheek-16/Brandsentinel.git
cd Brandsentinel

# Python Virtual Environment
python -m venv .venv

# Activate Virtual Environment:
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations and seed demo data
alembic -c backend/alembic.ini upgrade head
python scripts/seed_demo.py

# Start Backend Server (runs on http://localhost:8000)
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

#### 2. Frontend Setup (in a separate terminal)
```bash
cd frontend
npm install
npm run build
npm run dev
# Frontend runs on http://localhost:5173
```

---

### Option 2: Docker Setup (Self-Contained)

```bash
docker build -t brandsentinel .
docker run -p 10000:10000 -e PORT=10000 brandsentinel
# Access web app and API documentation at http://localhost:10000
```

---

## Running the Verification Test Suite

All 46 unit and integration tests run deterministically:

```bash
# Run complete test suite
python -m pytest backend/tests/ -v

# Run BrandBench v2 held-out evaluation runner
python benchmark/run_benchmark.py
```

---

## Verification & Reliability Highlights

- **46 Unit & Integration Tests Passing:** Across 14 test modules verifying RBAC, KB versioning, suggestion verification, visual scoring, ambiguity detection, Indian PII redaction, and startup security.
- **BrandBench v2 Evaluation:** Evaluated on 60 novel held-out test cases across 4 brands with **86.8% Combined F1 Score** and **0.0% Prompt Injection Bypass Rate**.
- **Cryptographic Tamper-Evidence:** All review decisions, KB updates, and findings dismissals are recorded in a SHA-256 hash-chained immutable audit log.
- **Exportable Governance Certificate:** Downloadable Markdown, HTML, and JSON compliance certificate signed with a verification hash for regulatory archiving.
