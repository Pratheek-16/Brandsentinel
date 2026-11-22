# User Research & Usability Study Protocol: BrandSentinel

## 1. Study Overview & Goals
This protocol establishes an empirical evaluation framework for **BrandSentinel**, testing whether content creators, brand managers, and compliance reviewers can effectively govern marketing copy and digital assets before publication.

### Core Objectives
1. **Task Effectiveness:** Can creators resolve violations in under 3 minutes using verified suggestions?
2. **Usability & Learnability:** Does the system achieve an above-average System Usability Scale (SUS > 75)?
3. **Cognitive Load:** Does the grounded evidence display reduce reviewer verification effort (NASA-TLX)?
4. **Honest Scope Disclosure:** Document participant cohort as internal pilot evaluators and provide a standardized protocol for larger enterprise deployments.

---

## 2. Participant Recruitment & Cohort Profile

| Target Persona | Key Responsibilities | Criteria | Cohort Size (Pilot) |
|---|---|---|---|
| **Content Creator** | Drafting social copy, email campaigns, blog posts | Regularly writes promotional marketing copy; familiar with style guides | 2 |
| **Brand / Review Manager** | Approving campaign collateral, reviewing tone | Accountable for brand voice consistency and message alignment | 2 |
| **Compliance Officer** | Regulated claims audit, financial/medical disclosures | Reviews claims against statutory regulations (FTC, FDA, FDIC) | 1 |

*Note: For the Round 3 submission window, evaluation data was gathered via an intensive internal pilot cohort (peer developers, designers, and marketing testers) under identical protocol conditions.*

---

## 3. Evaluation Tasks (Timed Scenarios)

1. **Task 1 (Creator Remediation):** Ingest draft copy containing prohibited terminology (`PulseBand`) and contradicted numeric fact (`14 days` vs approved `10 days`). Inspect findings, review grounded citations, and apply an intent-preserving verified fix.
2. **Task 2 (Visual & Accessibility Audit):** Upload a campaign asset image and document (`.pdf` or `.docx`). Inspect automated WCAG 2.2 AA contrast calculation and missing alt-text deductions.
3. **Task 3 (Reviewer Queue & Cryptographic Sign-Off):** Review an escalated draft, evaluate grounded source citations, and approve the submission with digital signature recording.
4. **Task 4 (Ambiguity Detection & KB Clarification):** Open Governance Insights, identify a rule with high dismissal rates (>40%), and accept the suggested clarification into a newly activated KB version.
5. **Task 5 (Audit Certificate Export):** Export a cryptographically verified Brand Governance Certificate with SHA-256 signature for compliance archiving.

---

## 4. Survey Instruments

### A. System Usability Scale (SUS)
Standard 10-item questionnaire scored on a 5-point Likert scale (1 = Strongly Disagree, 5 = Strongly Agree):
1. I think that I would like to use this system frequently.
2. I found the system unnecessarily complex.
3. I thought the system was easy to use.
4. I think that I would need the support of a technical person to be able to use this system.
5. I found the various functions in this system were well integrated.
6. I thought there was too much inconsistency in this system.
7. I would imagine that most people would learn to use this system very quickly.
8. I found the system very cumbersome to use.
9. I felt very confident using the system.
10. I needed to learn a lot of things before I could get going with this system.

*Scoring: Formula `((Q1-1) + (5-Q2) + (Q3-1) + (5-Q4) + (Q5-1) + (5-Q6) + (Q7-1) + (5-Q8) + (Q9-1) + (5-Q10)) * 2.5` yields score 0-100.*

### B. NASA-TLX Cognitive Load (Selected Subscales)
Evaluated on a 1-10 scale:
- **Mental Demand:** How mentally demanding was it to verify whether a flagged finding was accurate?
- **Temporal Demand:** Did you feel hurried or rushed during review?
- **Frustration:** How insecure, discouraged, irritated, or stressed did you feel?
- **Effort:** How hard did you have to work to accomplish your level of performance?

---

## 5. Semi-Structured Debrief Questions
1. "When you reviewed the flagged span, did the quoted Knowledge Base snippet give you enough confidence to take action?"
2. "How did the 1-click verified suggestions compare to rewriting the sentence yourself?"
3. "What was the most confusing or friction-filled moment during your session?"
4. "Would you trust the SHA-256 Governance Certificate as an audit trail for your organization?"
