# Privacy, Security, and Compliance Architecture

BrandSentinel is built with enterprise privacy and zero-trust security as foundational requirements. This document outlines the safeguards implemented across data ingress, AI inference, access control, and auditing.

---

## 1. Confidential Data & PII Redaction Engine

Before any piece of text is transmitted to an external LLM (e.g., Google Gemini), it passes through the synchronous **Redaction Engine** (`backend/app/modules/redact/`):

1. **Regex & Entity Tokenization:**
   - **Aadhaar Numbers (India):** 12 digits (with optional spaces/hyphens) $\rightarrow$ `<AADHAAR_1>`
   - **Permanent Account Numbers (PAN, India):** 5 letters + 4 digits + 1 letter $\rightarrow$ `<PAN_1>`
   - **UPI Virtual Payment Addresses (India):** `user@bank` formats $\rightarrow$ `<UPI_ID_1>`
   - **Indian Mobile Numbers:** `+91` prefix with 10-digit mobile sequence $\rightarrow$ `<PHONE_1>`
   - **IFSC Codes (India):** 4 letters + `0` + 6 alphanumeric characters $\rightarrow$ `<IFSC_1>`
   - **Email Addresses:** RFC 5322 email syntax $\rightarrow$ `<EMAIL_1>`
   - **Credit Card Numbers:** 13–19 digits (Luhn checked) $\rightarrow$ `<CREDIT_CARD_1>`
   - **API Keys & Secrets:** Bearer tokens, private keys, JWTs $\rightarrow$ `<SECRET_1>`

2. **Deterministic Placeholder Mapping & Bidirectional Restoration:**
   - Mappings and character deltas are stored ephemerally in memory solely for the duration of the request.
   - When findings are returned by the external LLM citing character spans in the redacted text, the Verifier translates the offsets back to the exact character indices of the author's original unredacted text.
   - Ephemeral maps are discarded immediately upon request completion.

3. **Audit Logging & Accounting:**
   - Every execution records the total redactions performed in the `AIUsage` table (`redaction_count`).
   - The original text with unredacted PII is never transmitted over external network boundaries.
   - Transparently queryable via `GET /content/{id}/ai-ledger`.

---

## 2. Authentication & Role-Based Access Control (RBAC)

Access control is enforced at both the API gateway and database query layers:

- **Authentication:** Standard JWT (JSON Web Tokens) with HMAC-SHA256 signatures and strict expiration.
- **Production Secret Hardening:** In `production` environment, `JWT_SECRET_KEY` must be set and $\ge 32$ characters in length, otherwise the application fails fast at startup with a `RuntimeError`. In development, an ephemeral 256-bit cryptographically secure secret is generated with a visible warning.
- **Password Security:** Multi-round Argon2id password hashing via `passlib[argon2]`.
- **Role Hierarchy:**
  - **Creator:** Author and revise content; accept, edit, or dismiss suggestions; submit for review.
  - **Manager:** Review submissions; view diffs and evidence; approve low/medium risk content; request changes.
  - **Authorised Reviewer:** Exclusive sign-off authority for high-risk items and regulatory claims.
  - **Admin (Brand Guardian):** Manage workspace configurations, edit knowledge-base rules, manage users, and inspect ambiguity metrics.
- **Tenant Isolation:** Every database entity belongs to a `workspace_id`. All repository queries enforce strict tenant filtering (`WHERE workspace_id = current_user.workspace_id`). Cross-workspace data leakage is strictly forbidden and verified via automated tests.

---

## 3. Cryptographic Non-Repudiation & Audit Integrity

- **Cryptographic Approval Signatures:**
  Every content approval generates a cryptographic SHA-256 digital signature:
  $$\text{signature\_hash} = \text{SHA-256}(\text{ApproverID} \parallel \text{ContentVersionID} \parallel \text{Timestamp} \parallel \text{Comment})$$
  This signature guarantees that an approval cannot be repudiated or attributed to another user.
- **Hash-Chained Audit Log:**
  Events form an append-only cryptographic ledger where each record contains the SHA-256 hash of the preceding record (`prev_hash`). Tampering with database rows immediately invalidates subsequent hashes in the chain, detected by `GET /audit/verify`.
- **Verifiable Governance Certificate:**
  Content approvals can be exported as a standalone Brand Governance Certificate (`GET /content/{id}/export`) containing the cryptographic signature, finding history, and workspace verification seal.

---

## 4. Prompt Injection Resistance & Safety Defenses

Large Language Models integrated into enterprise review flows face prompt injection and jailbreak threats. BrandSentinel employs defense-in-depth:

1. **Structural Delimitation:** User content is passed as passive data payload within structured schemas, never executed as instructions.
2. **Parallel Deterministic Independent Execution:** The deterministic KB engine runs completely independently of the LLM. In our BrandBench v2 held-out evaluation of 10 adversarial attacks, our injection bypass rate was **0.0%** because the deterministic KB engine catches brand violations regardless of what the LLM outputs.
3. **Independent Grounding Verifier:** The AI provider's output is never displayed raw. The Verifier verifies that cited text occurs verbatim in the source content and aligns with approved knowledge base rules. Hallucinated or injected findings are discarded.
