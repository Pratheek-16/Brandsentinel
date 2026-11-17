# BrandSentinel Architecture Documentation

## 1. System Overview

**BrandSentinel** is an enterprise pre-publication brand-governance platform designed to review digital content against approved brand guidelines, facts, terminology, claims, and visual assets before public release.

The platform prevents brand decay, regulatory penalties, and reputational risk by combining:
1. **Automated Verification:** Strict grounding against verified knowledge-base assets.
2. **Intent-Preserving Correction:** Automated rewrite suggestions that resolve violations without altering authorial intent.
3. **Role-Based Governance:** Human-in-the-loop review state machine enforcing separation of duties and cryptographic audit logs.

```
+----------------------------------------------------------------------------------+
|                                Frontend (React + Vite + TS)                     |
|  [Content Editor]  [Review Screen]  [KB Manager]  [Vision Lab]  [Audit & Insights]|
+----------------------------------------------------------------------------------+
                                        | (REST / JWT Auth)
                                        v
+----------------------------------------------------------------------------------+
|                               FastAPI Modular Monolith                            |
|                                                                                  |
|  +----------------+   +----------------+   +----------------+   +--------------+ |
|  | Auth & RBAC    |   | Knowledge Base |   | Review Engine  |   | Suggestions  | |
|  | (4 User Roles) |   | (Rules, Facts) |   | (Redact + Gen) |   | (Engine I-1) | |
|  +----------------+   +----------------+   +----------------+   +--------------+ |
|                                                    |                             |
|  +----------------+   +----------------+           v            +--------------+ |
|  | Vision Analysis|   | Workflow & Risk|   +----------------+   | Hash-Chained | |
|  | (CIELAB I-2)   |   | State Machine  |   | Grounding      |   | Audit Log    | |
|  +----------------+   +----------------+   | Verifier       |   | (SHA-256)    | |
|                                            +----------------+   +--------------+ |
+----------------------------------------------------------------------------------+
                                        |
                 +----------------------+----------------------+
                 |                                             |
                 v                                             v
     +-----------------------+                     +-----------------------+
     |   Relational DB       |                     | In-Memory VectorStore |
     | (SQLite / PostgreSQL) |                     | (Cosine Similarity)   |
     +-----------------------+                     +-----------------------+
```

---

## 2. Core Architectural Principles

### 2.1 Modular Monolith
The backend is structured into clear, decoupled domain modules under `backend/app/modules/`:
- `auth`: Security, JWT tokens, RBAC dependencies (`require_roles`).
- `kb`: Knowledge base CRUD, rule atomisation engine, version snapshots.
- `content`: Content ingestion (text, DOCX), versioning, review dispatch, and comment threads.
- `workflow`: Formal state machine validator, risk evaluation, and multi-stage routing.
- `audit`: Hash-chained audit event generation and cryptographic verification.
- `redact`: Pre-LLM confidential data and PII tokenization.
- `ai_providers`: Abstract AIProvider interface with `GeminiProvider`, `MockProvider`, and `VectorStore`.
- `verification`: Grounding verifier ensuring zero ungrounded findings.
- `suggestions`: Improvement I-1 intent-preserving rewrite and verification engine.
- `vision`: Improvement I-2 CIELAB color analysis and WCAG 2.2 AA contrast calculation.
- `insights`: Improvement I-3 summary metrics and Rule Ambiguity Detector.

### 2.2 Human-in-the-Loop Governance
- The AI never unilaterally approves or publishes content.
- Every finding surfaces citing an approved rule or fact with direct source quotes.
- Every suggested edit requires explicit Creator acceptance (`/accept`) or dismissal (`/dismiss`).
- **No-Self-Approval Rule:** Creators cannot approve their own submissions.

---

## 3. Workflow State Machine & Lifecycle

Content progresses through discrete, audited lifecycle states:

```
[Draft] ---> (Run Review) ---> [Reviewing]
   |                                 |
   v                                 v
[Changes Requested] <------- (Review Returned Findings)
   |
   +---> (Resubmit Revision) ---> [Submitted]
                                    |
                    +---------------+---------------+
                    | (Low Risk)                    | (High Risk / Claim)
                    v                               v
            [Manager Review]              [Authorised Reviewer]
                    |                               |
                    +---------------+---------------+
                                    |
                             (Sign & Approve)
                                    |
                                    v
                               [Approved]
                                    |
                                    v
                               [Published]
```

### Risk Escalation Rules
- If content has `blocker` or `major` severity findings, it is routed to **Authorised Reviewer**.
- If a promotional claim is flagged (`unsupported` or `missing_disclaimer`), approval requires Authorised Reviewer sign-off.
- All decisions record cryptographic signatures (`signature_hash`).

---

## 4. Cryptographic Hash-Chained Audit Trail

To guarantee tamper evidence, every administrative, content, and approval event is written to an immutable append-only hash chain:

$$H_i = \text{SHA-256}(H_{i-1} \parallel \text{WorkspaceID} \parallel \text{ActorID} \parallel \text{Action} \parallel \text{PayloadJSON} \parallel \text{Timestamp})$$

The endpoint `GET /audit/verify` traverses the chain from Genesis ($H_0 = \text{"0" * 64}$) to the latest block. Any modified payload or inserted record breaks hash continuity and is detected immediately.

---

## 5. Three Named Improvements

### Improvement I-1: Suggestion Engine with Self-Verification
- When a finding is surfaced, candidate replacements are generated.
- The candidate replacement is spliced into the text at the exact span.
- The spliced text is run through the Grounding Verifier to confirm:
  1. The original violation is completely resolved.
  2. No new brand violations are introduced (regression check).

### Improvement I-2: Vision & Contrast Analyzer
- Uploaded brand graphics and raster images are analyzed using PIL and OpenCV.
- Dominant colors are extracted using spatial k-means clustering.
- Color distances to the brand palette are calculated using **CIELAB $\Delta E^*$**.
- Foreground-to-background contrast ratios are computed against **WCAG 2.2 AA standards** ($\ge 4.5:1$ for body text, $\ge 3:1$ for large headings).

### Improvement I-3: Insights Dashboard & Ambiguity Detector
- Aggregates review metrics across creators and content types.
- **Rule Ambiguity Detector:** Analyzes human feedback on AI findings. If creators dismiss findings for a specific rule more than 40% of the time, the rule is flagged as "ambiguous" with a recommendation for brand guardians to clarify its wording.
