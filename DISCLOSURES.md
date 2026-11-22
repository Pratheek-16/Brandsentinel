# Disclosures and Transparency Ledger (`DISCLOSURES.md`)

This document discloses all third-party libraries, templates, datasets, AI models, APIs, and AI-assisted development tools used in the development of **BrandSentinel** for the Inkloom AI Brand-Governance Hackathon (Round 3: "The Finish").

---

## 1. AI Assistance and Pair-Programming

- **AI Pair-Programmer:** Antigravity (Google DeepMind)
- **Role:** Sole pair-programming partner for participant **Pratheek (Team of One)**.
- **Scope:** Co-authoring system design, writing backend FastAPI modules, frontend React components, deterministic rule sets, test harnesses, benchmark suites, and documentation within the official build window.
- **Supervision & Human Control:** Every algorithmic design decision, code commit, test run, and benchmark execution was reviewed, tested, and validated by the human participant.

---

## 2. Artificial Intelligence Models & Providers

| Model / Service | Provider | Purpose | Status in Local Run |
| :--- | :--- | :--- | :--- |
| **Gemini 2.5 Flash / 1.5 Flash** | Google DeepMind | Structured brand governance finding extraction and claim reasoning via HTTPS REST | Activated when `GEMINI_API_KEY` is provided in `.env` |
| **MockLLM / MockProvider** | BrandSentinel Engine | Deterministic, offline rule-based extraction, grounding, and suggestion engine | Default fallback when `GEMINI_API_KEY` is unset; labeled in UI & AI usage ledger |
| **Vector Store (In-Memory)** | BrandSentinel Engine | Dense semantic retrieval using cosine similarity and cached embeddings | Native, zero-network fallback |

---

## 3. Benchmark Datasets & Brand Data

- **BrandBench v1.0:** 150 labelled content cases covering all six governance categories (`tone`, `terminology`, `messaging`, `claim`, `accessibility`, `clean`, `injection`).
- **BrandBench v2.0 (Held-Out):** 60 novel held-out test items across 4 brands (NovaFit 20, Lumen Bank 20, Aster University 10, Solaria Solar 10), including 10 adversarial prompt injection attacks.
- **Brand Kits:** 100% fictional brand identities created specifically for BrandSentinel:
  1. **NovaFit** (Health & Fitness Wearable / Nutrition)
  2. **Lumen Bank** (Regulated Retail & Commercial Fintech)
  3. **Aster University** (Higher Education & Research Institution)
  4. **Solaria Solar** (Renewable Energy Provider — zero-code evaluation brand)
  5. **QuantumDine** (Smart Kitchen Appliances — zero-code test workspace)
- **Confidentiality:** **Zero real, proprietary, or scraped corporate data** is used. All entities, claims, and regulatory statements are synthetic.

---

## 4. Backend Dependencies (`backend/requirements.txt`)

All backend libraries use permissive, commercial-friendly open-source licenses compatible with the project's **MIT License**:

| Library | Version | License | Purpose |
| :--- | :--- | :--- | :--- |
| `fastapi` | 0.111.0 | MIT | Core REST API framework |
| `uvicorn[standard]` | 0.30.0 | BSD-3-Clause | ASGI production HTTP server |
| `pydantic` | 2.7.1 | MIT | Schema validation and settings management |
| `pydantic-settings` | 2.16.3 | MIT | Environment variable loading |
| `SQLAlchemy` | 2.0.30 | MIT | Relational ORM & database abstractions |
| `alembic` | 1.13.2 | MIT | Database migrations |
| `python-dotenv` | 1.0.1 | BSD-3-Clause | Environment configuration |
| `python-multipart` | 0.0.9 | Apache-2.0 | Multipart form & file upload parsing |
| `httpx` | 0.27.0 | BSD-3-Clause | HTTP client for integration testing & direct REST LLM calls |
| `cryptography` | 43.0.1 | Apache-2.0 | SHA-256 hash chaining and digital signatures |
| `passlib[bcrypt]` | 1.7.4 | BSD-2-Clause | Password hashing abstractions |
| `argon2-cffi` | 23.1.0 | MIT | High-security Argon2id password hashing |
| `pytesseract` | 0.3.13 | Apache-2.0 | OCR extraction (degrades gracefully if binary missing) |
| `pdfplumber` | 0.11.2 | MIT | PDF text extraction and page metadata auditing |
| `python-docx` | 1.1.2 | MIT | DOCX text extraction, heading, and table auditing |
| `Pillow` | 10.3.0 | HPND | Image manipulation and color sampling |
| `opencv-python` | 4.9.0.80 | Apache-2.0 | Image and computer vision processing |
| `scikit-image` | 0.24.0 | BSD-3-Clause | Image quality and color analysis |
| `rapidfuzz` | 3.9.5 | MIT | Fuzzy string matching for KB rule atomisation |
| `textstat` | 0.7.3 | MIT | Readability and linguistic metrics |
| `numpy` | 2.0.0 | BSD-3-Clause | Vector mathematics, normalized cross-correlation & ΔE calculation |
| `scipy` | 1.14.0 | BSD-3-Clause | Color space conversions and statistical metrics |
| `pytest` | 8.2.2 | MIT | Automated test framework |
| `pytest-asyncio` | 0.23.7 | Apache-2.0 | Asynchronous test execution |

---

## 5. Frontend Dependencies (`frontend/package.json`)

| Package | Version | License | Purpose |
| :--- | :--- | :--- | :--- |
| `react` | 19.3.1 | MIT | Modern declarative UI framework |
| `react-dom` | 19.3.1 | MIT | React DOM renderer |
| `lucide-react` | 1.74.0 | ISC | Accessible UI iconography |
| `vite` | 8.3.6 | MIT | Modern frontend bundler and dev server |
| `tailwindcss` | 4.3.5 | MIT | Utility-first CSS styling |
| `@tailwindcss/vite` | 4.3.5 | MIT | Vite plugin for Tailwind CSS v4 |
| `typescript` | 7.0.2 | Apache-2.0 | Type safety |

---

## 6. Templates and Scaffolding

- **Templates:** None. All application architectures, database models, frontend interfaces, state machines, and hash-chain algorithms were authored specifically for this project from clean files.
