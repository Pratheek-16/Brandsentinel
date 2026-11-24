# BrandSentinel

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.3-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6.svg)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.3-38B2AC.svg)](https://tailwindcss.com)
[![Tests](https://img.shields.io/badge/Tests-55%20Passed-brightgreen.svg)](backend/tests)
[![Evaluation](https://img.shields.io/badge/BrandBench-97.3%25%20F1-blue.svg)](benchmark/report.md)

**BrandSentinel** is an enterprise-grade, pre-publication brand governance and compliance platform designed around the concept of **"The Proofing Desk"**. 

It enables marketing, copy, creative, and legal review teams to audit pre-publication copy, documents (DOCX, PDF), and visual assets against approved brand guidelines, factual records, terminology registers, regulatory claims, and visual design systems. Every finding is mathematically grounded with exact source citations, paired with verified intent-preserving rewrite suggestions, and routed through a tamper-evident, role-based review workflow.

---

## Table of Contents

- [Core Capabilities](#core-capabilities)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [User Personas & Workspaces](#user-personas--workspaces)
- [Prerequisites](#prerequisites)
- [Step-by-Step Installation & Quickstart](#step-by-step-installation--quickstart)
  - [1. Clone Repository](#1-clone-the-repository)
  - [2. Environment Configuration](#2-configure-environment-variables)
  - [3. Backend Setup](#3-set-up-the-python-backend)
  - [4. Database Migration & Demo Data](#4-run-database-migrations--seed-demo-data)
  - [5. Frontend Setup](#5-set-up-the-react-frontend)
  - [6. Access the Application](#6-access-the-application)
- [Alternative Run Modes](#alternative-run-modes)
  - [Single-Server Production Mode](#single-server-production-mode)
  - [Docker & Containerized Setup](#docker--containerized-setup)
- [Testing & Quality Assurance](#testing--quality-assurance)
  - [Backend Unit & Integration Tests](#backend-unit--integration-tests)
  - [Frontend Test Suite](#frontend-test-suite)
  - [Held-Out Evaluation Benchmark](#held-out-evaluation-benchmark)
- [API Reference](#api-reference)
- [Project Directory Structure](#project-directory-structure)
- [License](#license)

---

## Core Capabilities

### 1. The Editorial Proofing Desk
- **Distraction-Free Authoring:** A centered document canvas styled with warm paper tones, dark ink typography (Fraunces serif display and Instrument Sans UI), and hairline rules.
- **Interactive Margin Notes:** Violations are flagged with severity-coded wavy underlines in the text, visually linked to annotation cards in the margin with thin curved leader lines.
- **One-Click Verified Fixes:** Click any suggestion to immediately replace text in the draft, with tracked-change visual indicators and real-time re-evaluation.
- **Pre-Analysis PII Protection:** Automated redaction of sensitive identifiers (Aadhaar, PAN, UPI IDs, IFSC codes, phone numbers, and API keys) before any content reaches automated analysis engines.

### 2. Multi-Layer Verification & Grounding Engine
- **Layer 1 (Deterministic KB Matcher):** RapidFuzz exact and lemmatized token matching against active brand rules, prohibited terms, and numerical fact contradictions.
- **Layer 2 (Semantic RAG Evaluator):** Vector-based semantic search retrieving the most relevant active guidelines, evaluated by a prompt-injection-resistant evaluator.
- **Grounding Verifier:** Strictly validates all findings: ensures cited rule IDs exist in the active Knowledge Base, verifies exact quoted text, and confirms character span offsets. Dropping ungrounded hallucinations ensures zero false citations.

### 3. Intent-Preserving Suggestion Engine
- Generates up to three verified alternative rewrites for every flagged violation using preferred terminology, active brand claims, and contextual minimal edits.
- **Three-Branch Verification:**
  1. **Violation Resolution:** Verifies that applying the candidate fix completely eliminates the original violation.
  2. **Non-Regression:** Verifies that no new blocker or major severity violations are introduced.
  3. **Meaning Preservation:** Verifies that critical quantities, numbers, and core facts outside the flagged span remain unchanged.

### 4. Multi-Format Visual & Accessibility Inspector
- **Color Palette Adherence:** Calculates CIELAB $\Delta E^*$ (CIE76 Euclidean distance in $L^*a^*b^*$ color space) between asset colors and approved brand swatches.
- **WCAG 2.2 AA Contrast:** Evaluates relative luminance contrast ratios against statutory accessibility requirements (4.5:1 for normal text, 3:1 for large text).
- **Document Structure & Alt-Text Audit:** Inspects DOCX and PDF documents for missing image alt-text, heading-level skips (e.g., Heading 1 jumping to Heading 3), uninformative link anchors ("click here"), and tables lacking designated header rows.
- **Itemized Scoring (0–100):** Transparent score card showing exact point deductions with clear remediation advice.

### 5. Knowledge Base Management & Versioning
- Complete CRUD management for **Brand Rules**, **Prohibited & Preferred Terms**, **Factual Specifications**, **Regulatory Claims**, and **Visual Color Palettes**.
- **Immutable KB Versioning:** Every modification creates a versioned snapshot, allowing historical content reviews against the exact guidelines active at the time of creation.
- **Live Preview Simulator:** Test draft sentences in real-time within the Knowledge Base manager to see matched rules before publishing guideline updates.

### 6. Governance Insights & Ambiguity Detection
- Continuously analyzes four operational signals across workspace activity:
  1. **High Creator Dismissals:** Identifies guidelines with $>40\%$ dismissal rates where creators find rules unworkable.
  2. **Active KB Conflicts:** Automatically surfaces conflicting rules (e.g., terms simultaneously listed as prohibited and preferred).
  3. **Stale Factual Claims:** Alerts administrators when product claims or specifications exceed their validity dates or have not been reviewed in $>90$ days.
  4. **AI-vs-Human Divergence:** Highlights edge cases where automated models flagged items that human reviewers repeatedly dismissed.
- **One-Click Policy Clarification:** Administrators can accept suggested policy clarifications, automatically generating an active `vNext` KB version and retiring stale policies.

### 7. Four-Eyes Governance & Tamper-Evident Ledger
- **Separation of Duties:** Enforces strict four-eyes principles—a draft creator cannot review or approve their own submission.
- **Immutable Cryptographic Audit Trail:** Every event (draft creation, check, finding dismissal, comment, review decision, and KB update) is recorded in an immutable, SHA-256 hash-chained ledger.
- **Brand Governance Certificate:** Generates downloadable, cryptographically signed compliance certificates (Markdown, HTML, JSON) containing full review provenance for regulatory compliance.

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
                    | Privacy & Data Protection Layer          |
                    | (Aadhaar, PAN, UPI, IFSC, Phone, Secrets)|
                    +------------------------------------------+
                                          |
                                 +--------+--------+
                                 |                 |
                                 v                 v
               +-----------------------------+   +-----------------------------+
               | DETERMINISTIC ENGINE        |   | SEMANTIC EVALUATOR (RAG)    |
               | - Exact & Lemmatized Rules  |   | - Vector Retrieval Top-k    |
               | - Prohibited Term Matcher   |   | - Low-Temp Structured Judge |
               | - Numeric Contradictions    |   | - Injection-Resistant Prompt|
               +-----------------------------+   +-----------------------------+
                                 |                 |
                                 |                 v
                                 |               +-----------------------------+
                                 |               | GROUNDING VERIFIER          |
                                 |               | - Rule Existence Validation |
                                 |               | - Exact Quote Verification  |
                                 |               | - Span Boundary Validation  |
                                 |               +-----------------------------+
                                 |                 |
                                 +--------+--------+
                                          |
                                          v
                    +------------------------------------------+
                    | DEDUPLICATION & PROVENANCE MERGER        |
                    | (Source Attribution: Rule vs. AI Model)  |
                    +------------------------------------------+
                                          |
                                          v
                    +------------------------------------------+
                    | VERIFIED SUGGESTION ENGINE               |
                    | - 3 Candidate Fixes per Finding          |
                    | - Resolution & Non-Regression Checks     |
                    | - Meaning & Quantity Preservation Test   |
                    +------------------------------------------+
                                          |
                                          v
                    +------------------------------------------+
                    | FOUR-EYES GOVERNANCE & AUDIT LEDGER      |
                    | - Role-Based Workflow (Creator/Reviewer) |
                    | - SHA-256 Chained Immutable Ledger       |
                    | - Exportable Signed Certificate          |
                    +------------------------------------------+
```

---

## Technology Stack

- **Backend:** Python 3.10+, [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/) 2.0, [Pydantic](https://docs.pydantic.dev/) v2, [Alembic](https://alembic.sqlalchemy.org/)
- **Database:** SQLite (default for instant local run) or PostgreSQL / [Supabase](https://supabase.com/) with pgvector
- **Frontend:** [React](https://react.dev/) 18, [Vite](https://vitejs.dev/), [TypeScript](https://www.typescriptlang.org/), [Tailwind CSS](https://tailwindcss.com/) v4
- **Typography:** Self-hosted Fraunces (Variable Display Serif), Instrument Sans, JetBrains Mono
- **Document & Media Analysis:** `python-docx`, `pypdf`, `Pillow`, `colormath`
- **Testing & QA:** `pytest`, `pytest-asyncio`, `httpx`, Vitest

---

## User Personas & Workspaces

BrandSentinel includes three fully populated demo brand workspaces:
- **NovaFit:** Health & wellness consumer brand (medical claims, guarantees, and lifestyle tone).
- **Lumen Bank:** Financial services brand (statutory APR disclosures, guarantees, and regulatory terms).
- **Aster University:** Higher education institution (accreditation facts, tone, and visual guidelines).

### Seeded Demo Accounts
All seeded accounts share the default password: **`Demo@12345`**

| Brand Workspace | Role | Email | Responsibilities |
|---|---|---|---|
| **NovaFit** | Creator | `creator1@novafit.local` | Draft writing, file upload, running checks, applying fixes |
| **NovaFit** | Manager | `manager1@novafit.local` | Review queue triage, change requests, team approvals |
| **NovaFit** | Authorised Reviewer | `reviewer1@novafit.local` | High-risk escalation queue, signing & approval stamp |
| **NovaFit** | Administrator | `admin@novafit.local` | KB rule management, insights & ambiguity clarification |
| **Lumen Bank** | Creator | `creator1@lumenbank.local` | Drafting financial marketing & rate disclosures |
| **Lumen Bank** | Authorised Reviewer | `reviewer1@lumenbank.local` | Regulatory compliance review & signing |
| **Aster University** | Creator | `creator1@aster.local` | Academic marketing and admissions copy |
| **Aster University** | Administrator | `admin@aster.local` | Academic guidelines, fact verification, audit logs |

---

## Prerequisites

Before running BrandSentinel, ensure you have the following installed on your machine:

1. **Python:** Version 3.10, 3.11, or 3.12 (`python --version`)
2. **Node.js:** Version 18.x or 20.x+ (`node --version`)
3. **Package Manager:** `npm` (included with Node.js) or `pnpm`
4. **Git:** (`git --version`)

---

## Step-by-Step Installation & Quickstart

Follow these steps to clone, configure, and run the complete application locally.

### 1. Clone the Repository

```bash
git clone https://github.com/Pratheek-16/Brandsentinel.git
cd Brandsentinel
```

---

### 2. Configure Environment Variables

Copy the provided environment template to `.env`:

```bash
# On Linux / macOS:
cp .env.example .env

# On Windows PowerShell:
Copy-Item .env.example .env
```

The default `.env` is pre-configured to work immediately with local SQLite:

```ini
# Database: SQLite is used by default for zero-friction setup
DATABASE_URL=sqlite:///./brandsentinel.db

# LLM Model Configuration:
# Leave blank to use built-in intelligent deterministic & mock evaluator,
# or provide your Gemini API key to enable live Gemini analysis:
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=

# Authentication secret (change for production)
JWT_SECRET_KEY=brandsentinel_local_dev_secret_key_32chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480

# Auto-seed demo accounts on startup
SEED_DEMO=false
```

> **Note on Databases:** SQLite requires zero installation. If you prefer to use Supabase or PostgreSQL, simply update `DATABASE_URL` in `.env` to:  
> `DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>:5432/<dbname>`

---

### 3. Set Up the Python Backend

Create and activate a virtual environment, then install Python dependencies:

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4. Run Database Migrations & Seed Demo Data

Initialize the database schema and populate it with sample brands, rules, facts, and demo accounts:

```bash
# Apply database migrations
alembic -c backend/alembic.ini upgrade head

# Seed demo brands, rules, and user accounts
python scripts/seed_demo.py
```

You should see output confirming that `NovaFit`, `Lumen Bank`, and `Aster University` have been seeded with rules, terms, facts, claims, and users.

---

### 5. Set Up the React Frontend

Open a new terminal window, navigate to `frontend/`, install dependencies, and build:

```bash
cd frontend
npm install

# Build static assets
npm run build
```

---

### 6. Access the Application

You can now start both servers for active development:

#### Terminal 1: Backend Server
```bash
# From repository root with virtual environment activated:
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API is now running at `http://localhost:8000`.

#### Terminal 2: Frontend Server
```bash
# From frontend/ directory:
npm run dev
```
The frontend application is now running at **`http://localhost:5173`**.

Open your browser to **`http://localhost:5173`** and log in with any demo account (e.g., `creator1@novafit.local` with password `Demo@12345`).

---

## Alternative Run Modes

### Single-Server Production Mode

FastAPI is configured to serve the compiled React frontend directly from `frontend/dist/`. Once `npm run build` has run, you can run the entire application using only the backend command:

```bash
# 1. Build frontend once
cd frontend && npm install && npm run build && cd ..

# 2. Run backend
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
Open **`http://localhost:8000`** in your browser to access both the web application and API from a single port.

---

### Docker & Containerized Setup

BrandSentinel includes a multi-stage `Dockerfile` that packages both the frontend and backend into a self-contained image:

```bash
# Build the Docker image
docker build -t brandsentinel .

# Run the container
docker run -p 8000:10000 -e PORT=10000 brandsentinel
```

Access the application at **`http://localhost:8000`**.

---

## Testing & Quality Assurance

BrandSentinel is backed by a comprehensive suite of automated tests and benchmark evaluations.

### Backend Unit & Integration Tests

Run the complete test suite covering authentication, RBAC, knowledge base versioning, suggestion verification, visual scoring, ambiguity detection, and PII redaction:

```bash
python -m pytest backend/tests/ -v
```

To run a specific test suite:
```bash
# Test the 3-branch suggestion verification engine
python -m pytest backend/tests/test_verified_suggestions.py -v

# Test the visual palette and accessibility inspector
python -m pytest backend/tests/test_visual_accessibility.py -v

# Test governance insights and ambiguity detection
python -m pytest backend/tests/test_governance_insights.py -v

# Test end-to-end user journeys
python -m pytest backend/tests/test_e2e_journeys.py -v
```

### Frontend Test Suite

Run frontend unit and component tests:

```bash
cd frontend
npm test
```

### Held-Out Evaluation Benchmark

Evaluate the detection engine against the held-out evaluation dataset:

```bash
python benchmark/run_benchmark.py
```
This tests accuracy across multi-category violations, clean true-negative cases, adversarial edge cases, and prompt injection attempts. Detailed benchmark metrics and confusion matrices are generated in `benchmark/report.md`.

---

## API Reference

FastAPI automatically generates interactive OpenAPI documentation:

- **Interactive Swagger UI:** [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **ReDoc Documentation:** [`http://localhost:8000/redoc`](http://localhost:8000/redoc)
- **OpenAPI Schema (JSON):** [`http://localhost:8000/openapi.json`](http://localhost:8000/openapi.json)

### Key Endpoints

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **Auth** | `POST` | `/auth/login` | Authenticate user and issue JWT token |
| **Auth** | `GET` | `/auth/me` | Retrieve profile and permissions of current user |
| **Drafts** | `POST` | `/drafts/` | Create a new content draft |
| **Drafts** | `GET` | `/drafts/{draft_id}` | Retrieve draft content, status, and findings |
| **Drafts** | `POST` | `/drafts/{draft_id}/check` | Run multi-layer compliance analysis on draft |
| **Drafts** | `POST` | `/drafts/{draft_id}/action` | Apply rewrite fix or dismiss finding with justification |
| **Drafts** | `POST` | `/drafts/{draft_id}/submit` | Submit draft to review queue |
| **Reviews** | `GET` | `/reviews/queue` | List drafts pending review for current role |
| **Reviews** | `POST` | `/reviews/{draft_id}/decide` | Approve, reject, or request changes with notes |
| **Visual** | `POST` | `/visual/inspect` | Audit image, DOCX, or PDF for palette & WCAG 2.2 AA |
| **KB** | `GET` | `/kb/rules` | List active brand guidelines and rules |
| **KB** | `POST` | `/kb/rules` | Create a new brand rule |
| **Insights** | `GET` | `/insights/summary` | Retrieve operational ambiguity signals & conflicts |
| **Insights** | `POST` | `/insights/accept-clarification` | Apply policy clarification and advance KB version |
| **Audit** | `GET` | `/audit/trail` | Retrieve tamper-evident SHA-256 chained audit logs |
| **Certificate** | `GET` | `/drafts/{draft_id}/certificate` | Export cryptographically signed governance certificate |

---

## Project Directory Structure

```
Brandsentinel/
├── backend/
│   ├── alembic/                 # Database migration scripts
│   ├── app/
│   │   ├── api/                 # API route handlers (auth, drafts, reviews, kb, visual, insights)
│   │   ├── core/                # Config, security, hashing, JWT, database session
│   │   ├── models/              # SQLAlchemy database models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   └── services/            # Business logic:
│   │       ├── check_engine.py  # Multi-layer evaluation pipeline
│   │       ├── grounding.py     # Grounding verifier and citation checker
│   │       ├── suggestions.py   # Intent-preserving suggestion verifier
│   │       ├── visual_audit.py  # CIELAB Delta-E and WCAG contrast inspector
│   │       ├── insights.py      # Governance ambiguity signal engine
│   │       ├── redaction.py     # Indian PII redaction service
│   │       └── audit.py         # SHA-256 chained tamper-evident ledger
│   └── tests/                   # 55 automated pytest verification suites
├── frontend/
│   ├── src/
│   │   ├── components/          # Navigation rail, top strip, workflow ribbon, dialogs
│   │   ├── screens/             # Screen views:
│   │   │   ├── ContentEditor.tsx       # Writing desk & draft authoring
│   │   │   ├── ReviewScreen.tsx        # Signature proof canvas & margin notes
│   │   │   ├── ReviewQueueScreen.tsx   # Four-eyes review & escalation queue
│   │   │   ├── KnowledgeBaseScreen.tsx # Brand rules manager & live preview
│   │   │   ├── VisionInspectorScreen.tsx # Visual & document accessibility auditor
│   │   │   ├── InsightsScreen.tsx      # Ambiguity resolution & policy updates
│   │   │   ├── AuditTrailScreen.tsx    # Cryptographic ledger & export
│   │   │   └── LoginScreen.tsx         # Persona selector & authentication
│   │   ├── services/            # API client layer
│   │   └── styles/
│   │       └── tokens.css       # Design system tokens (Paper & Night Desk)
│   ├── package.json
│   └── vite.config.ts
├── benchmark/                   # Held-out evaluation dataset & test runner
├── scripts/
│   └── seed_demo.py             # Database seeding script for all demo brands
├── docs/                        # Architecture guides, accessibility specs, research protocol
├── Dockerfile                   # Multi-stage production container definition
├── docker-compose.yml           # Local multi-service orchestration
├── requirements.txt             # Python backend dependencies
└── README.md                    # Project documentation & quickstart guide
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
