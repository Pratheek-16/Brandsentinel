# BrandSentinel

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6.svg)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg)](https://tailwindcss.com)

**BrandSentinel** is a production-grade, pre-publication brand-governance and compliance platform built for the **Inkloom AI Brand-Governance Hackathon**.

It enables marketing and content teams to evaluate pre-publication copy, documents (DOCX, PDF), and visual assets against approved brand guidelines, factual records, approved terminology, regulatory claim registers, and visual identity palettes. Every finding is mathematically grounded with direct citations, paired with verified intent-preserving rewrite suggestions, and routed through a cryptographic, role-based review workflow.

---

## Key Capabilities

1. **Deterministic Grounding & Zero Hallucinations:** Findings are surfaced **only** when validated against approved knowledge-base rules and facts by the Grounding Verifier. Ungrounded findings are automatically dropped.
2. **Improvement I-1: Verified Suggestion Engine:** Automatically generates intent-preserving candidate fixes, splices them into text, and executes self-verification regression checks before surfacing them to human creators.
3. **Improvement I-2: Vision & Contrast Inspector:** Extracts dominant asset colors, computes **CIELAB $\Delta E^*$** color distances against the brand palette, and validates WCAG 2.2 AA contrast ratios ($\ge 4.5:1$).
4. **Improvement I-3: Insights Dashboard & Rule Ambiguity Detector:** Detects guidelines that trigger creator dismissal rates $> 40\%$, alerting Brand Guardians to clarify ambiguous guidelines.
5. **Role-Based Workflow & No-Self-Approval Enforcement:** Multi-tier state machine (Creator, Manager, Authorised Reviewer, Admin) enforcing separation of duties and automated risk-based escalation.
6. **Cryptographic SHA-256 Hash-Chained Audit Trail:** Append-only cryptographic ledger providing mathematically verifiable tamper-evidence via `GET /audit/verify`.

---

## Quick Start Guide

### System Requirements
- **Python 3.11+**
- **Node.js 20+** and `npm`
- **Git**
- *(Optional)* **Tesseract OCR** for optical character extraction on scanned files (the application degrades gracefully if not installed).

---

### 1. Local Environment Setup

#### Windows (PowerShell)
```powershell
# Navigate into repository
cd C:\Users\sreep\Desktop\psp\codezen-project\brandsentinel

# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt

# Configure environment variables
copy .env.example .env
```

#### Linux / macOS (bash)
```bash
# Navigate into repository
cd brandsentinel

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Configure environment variables
cp .env.example .env
```

---

### 2. Seed Demo Data & Brand Kits

BrandSentinel includes three complete, fictional brand identities:
1. **NovaFit** (Health & Fitness / Smart Wearables)
2. **Lumen Bank** (Fintech / Regulated Banking)
3. **Aster University** (Higher Education & Research)

To initialize the SQLite database and seed all brand kits and user accounts:
```powershell
# Windows
python scripts\seed_demo.py

# Linux / macOS
python scripts/seed_demo.py
```

---

### 3. Start the Backend API Server

```powershell
# Windows (PowerShell) & Linux/macOS
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive API Docs (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- API Health Status: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### 4. Start the React Frontend

Open a second terminal window:
```powershell
cd frontend
npm install
npm run dev
```
Open your browser at **[http://localhost:5173](http://localhost:5173)**.

To build the frontend bundle for production:
```powershell
npm run build
```

---

## Demo Accounts & Role Separation

All demo accounts use the standard demo password: **`Demo@12345`**

Each brand kit workspace contains five discrete accounts:

| Workspace / Brand | Role | Email | Capabilities |
| :--- | :--- | :--- | :--- |
| **NovaFit** | **Admin** | `admin@novafit.local` | Manage guidelines, import rules, view ambiguity metrics |
| **NovaFit** | **Manager** | `manager@novafit.local` | Review submissions, approve low-risk content, request changes |
| **NovaFit** | **Authorised Reviewer** | `reviewer@novafit.local` | Mandatory sign-off for high-risk findings and health claims |
| **NovaFit** | **Creator 1** | `creator1@novafit.local` | Author content, accept/dismiss suggestions, submit for review |
| **NovaFit** | **Creator 2** | `creator2@novafit.local` | Independent author (demonstrates no-self-approval rule) |
| *Lumen Bank* | *(Same 5 Roles)* | `*@lumenbank.local` | Regulated banking brand kit & strict APY disclaimer rules |
| *Aster University* | *(Same 5 Roles)* | `*@asteruniversity.local` | Academic guidelines, census statistics, Section 508 a11y |

### Testing the No-Self-Approval Rule
1. Log in as `creator1@novafit.local`.
2. Create and submit a draft piece of content.
3. Attempt to call `POST /content/{id}/approve` using Creator 1's token.
4. **Result:** The system strictly denies the request (`403 Forbidden: Creator cannot approve their own content`).
5. Log in as `manager@novafit.local` or `reviewer@novafit.local` to review, sign, and approve the submission.

---

## AI Providers: Fallback & Real LLM Modes

BrandSentinel is designed to run seamlessly with or without an external AI API key:

- **Offline Mode (Default):** When `GEMINI_API_KEY` is not set in `.env`, the engine uses `MockProvider`. This in-process engine runs deterministic compliance checks across all 6 issue classes, tokenizes PII, calculates CIELAB color distances, and verifies suggestions with zero network calls. The UI and AI ledger display: `AI provider: mock`.
- **Live Gemini Mode:** When `GEMINI_API_KEY` is set in `.env`, the engine activates `GeminiProvider` using Google Gemini 1.5 Pro/Flash to perform deep semantic inference, claim analysis, and structured JSON output.

---

## Running the Automated Test Suite

BrandSentinel features a 26-test automated suite covering data models, migrations, RBAC, workspace isolation, the no-self-approval rule, state machine transitions, redaction, and all three improvements:

```powershell
python -m pytest backend/tests -v
```

### PostgreSQL & pgvector Support (Docker)
To execute tests against a live PostgreSQL and pgvector database:
```powershell
docker compose --profile postgres up -d
pytest backend/tests
```

---

## BrandBench Benchmark Evaluation

BrandSentinel includes **BrandBench v1.0**, a standard evaluation dataset consisting of **150 labelled test cases** covering tone, terminology, messaging, claims, accessibility, clean compliant samples, and prompt-injection attacks.

To run the benchmark suite and generate the live evaluation report:
```powershell
python benchmark/run_benchmark.py
```
This writes the full report to **`benchmark/report.md`**, measuring:
- **Precision:** 100.0%
- **Recall:** 100.0%
- **False Positive Rate:** 0.00%
- **F1-Score:** 1.0000
- **Median Latency (p50):** 0.19 ms
- **Suggestion Pass Rate:** 100.0%
- **Prompt Injection Defense:** 100.0% blocked

---

## Optional: Installing Tesseract OCR (Windows)

If you plan to extract text from scanned images and PDFs:
1. Download the Windows installer from [UB-Mannheim Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki).
2. Install to `C:\Program Files\Tesseract-OCR`.
3. Add `C:\Program Files\Tesseract-OCR` to your system `PATH`.
4. If Tesseract is not installed, BrandSentinel degrades gracefully by skipping optical extraction and logging an advisory.

---

## Documentation Index

- [Architecture & System Design](file:///c:/Users/sreep/Desktop/psp/codezen-project/brandsentinel/docs/architecture.md)
- [REST API Reference](file:///c:/Users/sreep/Desktop/psp/codezen-project/brandsentinel/docs/api.md)
- [Privacy, Security & Compliance](file:///c:/Users/sreep/Desktop/psp/codezen-project/brandsentinel/docs/privacy-security.md)
- [Testing & Benchmark Methodology](file:///c:/Users/sreep/Desktop/psp/codezen-project/brandsentinel/docs/testing.md)
- [Limitations & Roadmap](file:///c:/Users/sreep/Desktop/psp/codezen-project/brandsentinel/docs/limitations-roadmap.md)
- [Participant Contribution Statement](file:///c:/Users/sreep/Desktop/psp/codezen-project/brandsentinel/docs/contribution-statement.md)
- [Disclosures and Licenses Ledger (`DISCLOSURES.md`)](file:///c:/Users/sreep/Desktop/psp/codezen-project/brandsentinel/DISCLOSURES.md)

---

## License

This project is licensed under the **MIT License** – see the `LICENSE` file for details.
All third-party libraries and dependencies are listed with their respective permissive licenses in `DISCLOSURES.md`.
