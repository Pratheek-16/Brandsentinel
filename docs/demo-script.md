# BrandSentinel — Round 3 Demo Script & Live Judging Walkthrough

**Problem Statement:** Inkloom AI — Intelligent Brand-Governance Platform  
**Participant:** Pratheek (Team of One)  
**Pair-Programmer:** Antigravity (Google DeepMind)  
**Demo Duration:** ~5–7 Minutes  
**Demo URL (Local):** `http://localhost:5173` (Frontend) | `http://localhost:8000` (Backend)  
**Default Credentials:** All seeded demo accounts use password `Demo@12345`

---

## Pre-Flight Checklist for Presenter

1. Start backend: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` (from `backend/` or repo root).
2. Start frontend: `npm run dev` (from `frontend/`).
3. Ensure seeded data is present: run `python scripts/seed_demo.py` if resetting the database.
4. Verify backend health: open `http://localhost:8000/health` (verify `"status": "ok"` and `"ai_provider"` indicator).
5. Open browser at `http://localhost:5173`.

---

## Walkthrough Overview

| Scene | Persona | Route | Key Feature Demonstrated |
| :--- | :--- | :--- | :--- |
| **Scene 1** | Creator (`creator1@novafit.local`) | `/editor` | 1-Click sample load, KB-driven rule matching, numeric fact-checking, I-1 verified suggestions |
| **Scene 2** | Reviewer (`reviewer1@novafit.local`) | `/review` | Review queue, claim ledger statuses, dual-source badges (`Rule` vs `AI`), cryptographic approval |
| **Scene 3** | Designer / Compliance | `/vision` | Improvement I-2: CIELAB ΔE, WCAG contrast, alt-text deductions, 0–100 Accessibility Score |
| **Scene 4** | Brand Guardian (`admin@novafit.local`) | `/insights` | Improvement I-3: 4 live signals, ambiguity detector, 1-click **Accept Clarification** (`vNext` KB) |
| **Scene 5** | Auditor / Compliance Officer | `/review` & Export | Transparent AI Usage Ledger, PII masking proof, signed Brand Governance Certificate export |

---

## Scene 1: The Creator Experience (Pre-Publication Review)

### Goal
Demonstrate how a marketing copywriter catches brand violations in real time with grounded citations and accepts meaning-preserving corrections before submitting.

### Steps:
1. **Login:**
   - Go to `http://localhost:5173`.
   - Log in with `creator1@novafit.local` / `Demo@12345`.
   - Highlight the top navigation bar: notice the **AI Provider Status Indicator** (Green for active LLM, Amber for offline deterministic/mock provider).
2. **Load Sample Copy:**
   - In the Content Editor screen, click the **"NovaFit Summer Campaign"** sample button.
   - Text loads into the editor:
     > *"Introducing the all-new PulseBand 3 with a revolutionary 14-day battery life! It's the best fitness tracker ever made. Order now!"*
   - Select Channel: `Social Media` or `Web Copy`.
   - Click **"Analyze Content"**.
3. **Inspect KB-Driven Findings:**
   - Point out finding #1: **Banned Term** (`PulseBand` flagged under rule `NF-TERM-01`).
     - Point to the **Evidence Quote**: `"PulseBand is deprecated; use NovaBand."` loaded directly from the active Knowledge Base version.
   - Point out finding #2: **Numeric Fact Contradiction** (`14-day` flagged under fact `NF-FACT-01`).
     - Point to the grounded comparison: Stated value `14 days` contradicts active KB fact `up to 10 days`.
   - Point out finding #3: **Unsupported Superlative Claim** (`best fitness tracker ever made` flagged under claim `NF-CLAIM-01`).
     - Shows missing approved evidence citation and missing mandatory health disclaimer.
4. **Demonstrate Improvement I-1 (Intent-Preserving Correction Engine):**
   - Click on the **Banned Term** finding card.
   - Show the suggestion: `"NovaBand 3"`.
   - Highlight the **`verified: meaning preserved`** badge:
     - Explain to judges: The engine spliced the fix into the copy, re-ran the entire deterministic pipeline, verified the violation was resolved, confirmed no new major violations were introduced, and checked numeric tokens outside the span were untouched.
   - Click **"Apply Fix"**. Notice the editor text automatically updates to `NovaBand 3` and the finding resolves.
5. **Submit for Review:**
   - Click **"Submit for Approval"**.
   - Content status transitions to `under_review`.

---

## Scene 2: The Reviewer Workflow (Claim Ledger & Cryptographic Sign-Off)

### Goal
Demonstrate role-based separation of concerns, the claims ledger with regulatory disclaimer tracking, and cryptographic non-repudiation.

### Steps:
1. **Login as Reviewer:**
   - Switch user: Log out and log in as `reviewer1@novafit.local` / `Demo@12345`.
2. **Review Queue:**
   - Open the **Review Queue**. Locate the NovaFit campaign submitted in Scene 1.
   - Open the submission detail.
3. **Inspect Dual-Source Findings (`Rule` vs `AI`):**
   - Show the badges next to each finding:
     - `Rule (Deterministic)`: Found by regex/lemmatized KB search.
     - `AI (Judge)`: Found by grounded LLM judge and verified by the schema/quote verifier.
   - Highlight that hallucinated rule IDs or ungrounded quotes are rejected before reaching this screen.
4. **Inspect Claims Ledger:**
   - Toggle the **Claims Ledger** tab.
   - Show the explicit statuses:
     - `supported`
     - `contradicted`
     - `outdated`
     - `unsupported`
     - `missing_disclaimer`
   - Point out the mandatory disclaimer rule: `*Results may vary based on usage.`
5. **Approve & Cryptographically Sign:**
   - Enter a review comment: `"Reviewed battery claim and verified disclaimers."`
   - Click **"Approve & Sign"**.
   - Show the generated **Cryptographic Signature**:
     - `SHA-256: e8b4...` computed over `(ReviewerID || VersionID || Timestamp || Comment)`.
     - Explain to judges that this signature guarantees non-repudiation and appends to the immutable audit ledger.

---

## Scene 3: Improvement I-2 (Visual & Document Accessibility Inspector)

### Goal
Demonstrate multi-modal governance beyond text: color delta-E, WCAG 2.2 AA contrast, missing alt-text, heading structure, and transparent 0–100 scoring.

### Steps:
1. **Navigate to Visual Inspector:**
   - Click **"Visual & Accessibility"** in the top navigation.
2. **Palette & Contrast Verification:**
   - Upload or inspect a sample brand asset.
   - Point to the **CIELAB Delta-E (ΔE2000)** metric:
     - Shows exact color distance between sampled asset hex and brand primary color (`#FF4500`).
     - Color tolerance threshold: $\Delta E \le 5.0$.
   - Point to the **WCAG 2.2 AA Contrast Ratio**:
     - Shows text-to-background luminance ratio (e.g., `4.8:1` passes normal text requirement of `4.5:1`).
3. **Alt-Text & Document Structure Inspection:**
   - Show the Alt-Text auditor:
     - Flags missing alt-text, empty strings, raw file names (e.g. `IMG_2026.png`), and generic placeholders (`"image"`).
   - For PDF/DOCX assets:
     - Highlights missing document title/language metadata, skipped heading levels (`H1` to `H3`), and unlabeled tables.
4. **Transparent 0–100 Accessibility Score:**
   - Point out the overall score (e.g., `85 / 100`).
   - Show the itemized deduction ledger:
     - `-10 pts`: 1 image missing alternative text
     - `-5 pts`: Heading level skipped
   - Reassure judges: Scoring is completely deterministic and reproducible.

---

## Scene 4: Improvement I-3 (Insights, Ambiguity Detection & 1-Click Clarification)

### Goal
Demonstrate how the system detects ambiguous or conflicting rules from real operational feedback and updates the Knowledge Base in 1 click without code deployment.

### Steps:
1. **Login as Admin (Brand Guardian):**
   - Log in as `admin@novafit.local` / `Demo@12345`.
   - Click **"Insights & Ambiguity"** (`/insights`).
2. **Inspect the 4 Live Operational Signals:**
   - **Signal 1 — High Dismissal Rate:**
     - Shows rule `NF-TONE-01` ("Aggressive urgency words") dismissed >40% of the time by creators.
     - System diagnosis: The rule is overly broad and triggers false alarms on legitimate fitness phrases.
   - **Signal 2 — Active KB Conflicts:**
     - Shows contradictory rules (e.g. rule A mandates "NovaFit", rule B allows "Nova Fit").
   - **Signal 3 — Stale Facts:**
     - Shows fact `NF-FACT-02` whose `valid_to` date has expired or is overdue for quarterly review.
   - **Signal 4 — AI vs Human Disagreement:**
     - Shows areas where human reviewers consistently overturn AI-suggested findings.
3. **Execute 1-Click "Accept Clarification":**
   - On the `NF-TONE-01` card, show the proposed clarification:
     - Proposal: Exempt channel `Social Media` or narrow pattern regex.
   - Click **"Accept Clarification"**.
   - Show the instantaneous live update:
     - Old active KB version `v1.0` is archived (`is_active = False`).
     - New active KB version `v1.1` is cloned and activated (`is_active = True`) with the refined rule.
     - An immutable SHA-256 audit log event is recorded.
     - The card status immediately reflects `"Resolved (vNext Active)"`.

---

## Scene 5: Governance Completeness & Enterprise Compliance Export

### Goal
Demonstrate transparency, PII privacy masking, and verifiable export artifacts.

### Steps:
1. **View the AI Usage & Privacy Ledger:**
   - In the Review screen, click **"AI Usage Ledger"**.
   - Highlight:
     - Total characters processed.
     - Total LLM tokens used (input/output).
     - Estimated API cost (\$0.00012).
     - **PII Masking Counter:** Shows masked Indian & international entities (Aadhaar, PAN, UPI IDs, Phone, Email) with bidirectional offset alignment.
2. **Export Brand Governance Certificate:**
   - Click **"Export Certificate"** (or call `GET /content/{id}/export`).
   - View the formatted Brand Governance Certificate:
     - Document metadata, workspace name, approval timestamp.
     - Comprehensive finding audit trail (all accepted, resolved, and dismissed findings).
     - Cryptographic SHA-256 verification seal and public verification URL.
   - Show JSON and HTML export options for enterprise CI/CD integration.

---

## Summary Script for Judges Q&A

- **Q: "What happens if Gemini is offline or rate-limited?"**
  - *Answer:* "BrandSentinel follows a strict deterministic-first architecture. The regex and RapidFuzz KB engine runs locally inside the container with zero network dependency. If the LLM call fails or times out, the system degrades gracefully: deterministic findings are delivered with a source tag of `Rule`, and the UI indicates offline status without crashing."
- **Q: "How do you prevent prompt injection from bypassing brand governance?"**
  - *Answer:* "Content is passed to the LLM purely as quoted data, never as prompt instructions. More importantly, our parallel deterministic layer runs completely independent of the LLM. In our BrandBench v2 held-out evaluation of 10 adversarial attacks, our injection bypass rate was 0.0% because the deterministic KB engine catches brand violations regardless of what the LLM outputs."
- **Q: "Does editing the knowledge base really change review findings without code changes?"**
  - *Answer:* "Yes. We demonstrated this in test suite `test_kb_driven_detection.py` where a brand-new 4th workspace (*QuantumDine*) was governed with zero backend code changes, and dynamic terms added via API immediately trigger violations on subsequent reviews."
