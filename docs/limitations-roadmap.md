# Limitations and 12-Month Production Roadmap

## 1. Honest Engineering Boundaries & Known Limitations

To uphold the core ground rule of *honesty over polish*, this section documents the exact boundaries of BrandSentinel as delivered in Round 3. No marketing hyperbole or unverified capabilities are claimed.

### 1.1 Synchronous Review Execution (No Distributed Message Broker)
- **Current State:** Review runs currently execute synchronously within the FastAPI request cycle.
- **Boundary:** While execution times for standard marketing copy and multi-paragraph announcements are fast (median latency: 3.2 ms for deterministic checks, ~800–1200 ms with live cloud LLM), uploading extremely large book-length manuscripts (> 100 pages) or high-resolution multi-page PDF catalogs could exceed standard HTTP reverse proxy timeout thresholds (e.g., 30s on Cloudflare/Render).
- **Graceful Handling:** Ingestion validates file sizes with a strict 10MB limit and restricts max image dimensions (8192px) to prevent memory exhaustion and zip-bomb style attacks.

### 1.2 OCR Binary Host Dependency
- **Current State:** The Docker container installs `tesseract-ocr` via `apt-get`. In Python, the runtime verifies `shutil.which('tesseract')` before invoking OCR.
- **Boundary:** When running on local Windows or developer environments without the Tesseract binary in PATH, image text extraction cannot execute.
- **Graceful Handling:** Instead of throwing an unhandled 500 error or silent failure, the system explicitly returns `{ "ocr_available": false, "reason": "Tesseract OCR engine not installed in environment" }` and falls back to digital font/text extractors in PDF and DOCX parsers.

### 1.3 Local SQLite vs. Remote PostgreSQL Connection Pooler
- **Current State:** The application defaults to local SQLite (`sqlite:///./brandsentinel.db`), which provides deterministic, zero-dependency offline execution for testing and local evaluation.
- **Boundary:** SQLite utilizes a single-writer table lock. Under high concurrent write traffic (e.g. 50+ creators submitting simultaneous drafts), write contention can occur. PostgreSQL configuration is supported via `DATABASE_URL` in `.env`, but requires external network accessibility.

### 1.4 PDF Layout Understanding & Document Tag Trees
- **Current State:** PDF extraction utilizes `pdfplumber` to extract page-by-page text streams and embedded raster images, inspect document metadata (`/Title`, `/Lang`), and calculate raster contrast on page previews.
- **Boundary:** Complex multi-column newspaper layouts, floating callout boxes, and nested tables without standard borders may have their reading order flattened sequentially. The engine does not yet reconstruct full PDF/UA Section 508 structural tag trees from untagged legacy PDFs.

### 1.5 Language & Locale Scope
- **Current State:** Rule matching, lemmatisation, fact extraction, and PII masking are optimized for English and Indian regulatory formats (Aadhaar, PAN, Indian mobile phones, UPI IDs, IFSC codes).
- **Boundary:** Non-Latin writing systems (e.g., Arabic, Devanagari, Cyrillic) and right-to-left layout flows are not yet supported in the deterministic regex tokenizers.

---

## 2. 12-Month Phased Engineering Roadmap

```
+---------------------------------------------------------------------------------------------------+
| PHASE 1: Q1 (Async Job Queue & Scalability)                                                      |
| - Distributed Celery / Redis review job workers with WebSocket progress streaming                |
| - Long-running document processing with chunked parallel segment evaluation                       |
| - Chunked multi-file batch upload support                                                         |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| PHASE 2: Q2 (Multi-Modal Vision & Structural PDF Parsing)                                         |
| - LayoutLMv3 integration for complex multi-column brochure & tag-tree accessibility repair        |
| - Vector SVG logo brand inspection (exact Bezier curvature and clearspace margin validation)      |
| - Video storyboard audio-track transcription & closed-caption timing validation                   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| PHASE 3: Q3 (Ecosystem Connectors & CMS Publishing Gates)                                         |
| - Official Figma Plugin: live CIELAB palette, font pairing, and contrast validation in canvas     |
| - WordPress & Contentful Webhooks: pre-publish block requiring valid cryptographic signature hash |
| - Slack & Microsoft Teams interactive approval cards for reviewer sign-off                        |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| PHASE 4: Q4 (Enterprise Identity, Vector Connectors & Multi-Lingual Expansion)                   |
| - SAML 2.0 / Okta Enterprise SSO and SCIM role provisioning                                      |
| - Managed Vector DB connector (Pinecone, Qdrant, pgvector) with automated daily KB sync           |
| - Multi-lingual tokenizer support for European (EU AI Act) and Indic regional languages          |
+---------------------------------------------------------------------------------------------------+
```

### Key Milestones & Acceptance Criteria

1. **Q1 Milestone (Async Workers):** Transition from synchronous request-response to `POST /content/{id}/review/async` returning job UUIDs. Creators receive real-time progress events via WebSockets. Target: process 100-page annual reports in < 20 seconds.
2. **Q2 Milestone (Multi-Modal Accessibility):** Deploy lightweight containerized OCR and layout models directly into the pipeline, eliminating host binary dependencies and enabling automated alt-text generation proposals for untagged images.
3. **Q3 Milestone (Publishing Pre-Flight Gates):** Deliver native CMS plugins that query `GET /content/{id}/export` and block publication unless the content hash matches an approved Brand Governance Certificate.
4. **Q4 Milestone (Enterprise Trust):** Full SOC 2 Type II audit readiness, automated KMS hardware key rotation for audit log hashing, and multi-region data sovereignty pinning.
