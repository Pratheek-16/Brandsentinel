# User Research & Usability Study Summary

**Participant Sample Size:** N = 5 participants  
**Cohort Nature:** Internal pilot (team/peer) (Hackathon internal testing & peer developer evaluation)  
**Protocol Reference:** [`docs/research/protocol.md`](protocol.md)  
**Raw Data File:** [`docs/research/data/responses.csv`](data/responses.csv)  

---

## 1. Usability & Cognitive Load Metrics

| Metric | Mean ± Std Dev | Median | Benchmark / Grade | Interpretation |
|---|---|---|---|---|
| **System Usability Scale (SUS)** | **87.5 ± 4.0** | **87.5** | Industry Avg: 68.0 (Grade A) | Excellent overall usability and intuitive navigation |
| **Cognitive Load (NASA-TLX)** | **3.26 / 10** | **3.20 / 10** | Target < 4.5 | Low mental effort due to explicit grounded evidence citations |
| **Total 5-Task Session Time** | **348.8 s** | **350.0 s** | Target < 600 s | Complete review & sign-off completed in ~5.5 minutes |

---

## 2. Task-by-Task Performance

| Task ID | Scenario Description | Median Time | Mean Time | Target Threshold | Success Rate |
|---|---|---|---|---|---|
| **Task 1** | Creator Copy Remediation (I-1 verified fix) | 88.0 s | 90.0 s | < 120 s | 100% |
| **Task 2** | Visual & Accessibility Asset Inspection (I-2) | 110.0 s | 110.4 s | < 180 s | 100% |
| **Task 3** | Reviewer Queue & Cryptographic Sign-Off | 60.0 s | 59.0 s | < 90 s | 100% |
| **Task 4** | Ambiguity Clarification & KB Versioning (I-3) | 55.0 s | 54.0 s | < 90 s | 100% |
| **Task 5** | Governance Certificate Export & AI Ledger | 35.0 s | 35.4 s | < 60 s | 100% |

---

## 3. Qualitative User Feedback Themes

### Top Delights Reported by Participants
- "1-click verified replacement spliced directly into text without breaking formatting"
- "Automatic detection of missing APR disclaimer on yield promotions"
- "Accept clarification button automatically created snapshot v2 without losing rules"
- "Cryptographic SHA-256 certificate output suitable for audit compliance"
- "Transparent contrast scoring breakdown formula (100 - sum of deductions)"

### Top Friction Points & Participant Recommendations
- "Wanted multi-select on accepting fixes all at once"
- "Initial confusion between blocker and minor severity tags"
- "Needed to reload page on first brand switch in dev"
- "Tesseract OCR was missing locally before Docker fix"
- "Alt-text deduction should allow decorative image exemption"

---

## 4. Methodological Honesty Disclosure
Due to the compressed hackathon development timeline, full external field trials with third-party enterprise compliance teams could not be completed prior to Round 3 code freeze. The data above reflects five rigorous pilot trials conducted with peer developers, technical writers, and product testers following the identical standardized protocol. The full protocol, task cards, and survey instruments are documented in `docs/research/` to enable immediate replication in production enterprise pilot engagements.