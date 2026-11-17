# Limitations and Production Roadmap

This document outlines the architectural trade-offs, current boundaries, and future expansion roadmap for BrandSentinel.

---

## 1. Current Boundaries & Limitations

### 1.1 Local Database vs. Distributed Scale
- **Current State:** The default local deployment runs on SQLite with an in-memory cosine-similarity `VectorStore`. A Docker Compose profile (`docker compose --profile postgres up`) is provided for PostgreSQL and pgvector.
- **Limitation:** In SQLite mode, file concurrency is limited by SQLite's single-writer lock during heavy write spikes.

### 1.2 OCR and Visual Processing Dependencies
- **Current State:** Visual inspection leverages Pillow and OpenCV for dominant color extraction and CIELAB color distances. Document text extraction supports DOCX and PDF natively. OCR via Tesseract is supported but configured to degrade gracefully if the Windows binary is uninstalled.
- **Limitation:** Complex multi-page scanned PDF brochures without digital text layers require the host machine to have Tesseract OCR installed in PATH.

### 1.3 Asynchronous Job Queueing
- **Current State:** Review runs execute synchronously within FastAPI request cycles or simulated background jobs.
- **Limitation:** For extremely large documents (> 50 pages or high-resolution video storyboards), an external message broker (Celery / RabbitMQ / Redis) would be required to prevent HTTP timeout.

---

## 2. Production Roadmap

```
+-----------------------------------------------------------------------------------+
| Phase 1 (Completed): Core Governance & Improvements I-1, I-2, I-3                 |
| - Verifier Grounding, Suggestion Engine, Vision CIELAB, Insights Ambiguity        |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Phase 2 (Enterprise Integrations): CMS & Design Webhooks                          |
| - Figma Plugin: Live brand checking inside design canvasses                      |
| - Contentful / WordPress CMS Webhooks: Pre-publish validation gates              |
| - Slack / Teams Escalation Notifications: Interactive approval cards             |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Phase 3 (Scale & Enterprise Compliance): Global Distributed Governance            |
| - SAML 2.0 / Okta Enterprise Single Sign-On                                      |
| - Distributed pgvector indexing with horizontal read replicas                    |
| - Multi-region data sovereignty pinning for global multinational brands           |
+-----------------------------------------------------------------------------------+
```

### Key Milestones
1. **CMS Publishing Hooks:** Native integrations with WordPress, Contentful, and Webflow to block publishing until a valid cryptographic `signature_hash` is verified.
2. **Real-time Figma Plugin:** Instant design canvas validation checking typography scales, bounding box margins, and CIELAB palette compliance live during design creation.
3. **Automated KB Ingestion Pipeline:** Automated crawlers monitoring corporate press releases and regulatory filings to update verified `facts` and `claims` automatically with audit alerts.
