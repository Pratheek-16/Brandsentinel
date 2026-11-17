# Testing Strategy and Benchmark Evaluation

BrandSentinel maintains a comprehensive automated testing suite encompassing unit tests, database migration tests, RBAC integration tests, workflow state validation, and the BrandBench evaluation harness.

---

## 1. Test Architecture

The test suite is built on **pytest** and **Starlette TestClient**, located in `backend/tests/`:

| Test Suite | File | Focus Areas |
| :--- | :--- | :--- |
| **Health & Sanity** | `test_health.py` | Basic API uptime and OpenAPI schema availability |
| **Data Models** | `test_models_and_tables.py` | SQLite & PostgreSQL schema integrity and foreign keys |
| **Redaction & Review** | `test_redaction_and_review.py` | PII regex tokenization, placeholder restitution, AIUsage ledger |
| **RBAC & Isolation** | `test_rbac_and_isolation.py` | Role permissions, cross-workspace denial, no-self-approval rule |
| **Knowledge Base** | `test_kb_crud_and_versioning.py` | Rule CRUD, rule atomisation engine, version snapshots |
| **Retrieval & Claims** | `test_retrieval_gemini_and_claims.py` | VectorStore cosine similarity, claim ledger status classification |
| **Workflow & Audit** | `test_workflow_audit_and_escalation.py` | State machine transitions, risk escalation, SHA-256 hash chaining |
| **Improvements** | `test_improvements.py` | I-1 (Suggestion Engine), I-2 (CIELAB & WCAG), I-3 (Ambiguity Detector) |
| **BrandBench Conformance** | `test_brandbench.py` | 150-case benchmark dataset integrity and ground-truth validation |

---

## 2. Running Automated Tests

### Windows (PowerShell)
```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run full test suite
python -m pytest backend/tests -v
```

### Linux / macOS (bash)
```bash
# Activate virtual environment
source .venv/bin/activate

# Run full test suite
python -m pytest backend/tests -v
```

---

## 3. BrandBench Benchmark Harness

**BrandBench** is BrandSentinel's standard evaluation benchmark containing **150 systematically curated test cases**:
- **Tone Violations:** Punitive shaming, speculative hype, unscholarly commercial slang.
- **Terminology Violations:** Banned synonyms, unapproved brand marks, obsolete nomenclature.
- **Messaging & Factual Contradictions:** Unformatted pricing, contradicted census stats, fabricated regulatory limits.
- **Unsupported Promotional Claims:** Banned physiological cures, zero-risk financial guarantees, missing mandatory disclaimers.
- **Accessibility & Visual Issues:** Sub-4.5:1 contrast, untagged raster graphics, missing document headers.
- **Clean Compliant Samples:** Flawless brand copy verifying zero false positives.
- **Adversarial Prompt Injections:** Jailbreak attempts, system prompt overrides, and data exfiltration scripts.

### Running BrandBench
```powershell
python benchmark/run_benchmark.py
```

The script produces a detailed execution report at `benchmark/report.md` detailing:
- True Positives, False Positives, True Negatives, False Negatives
- Precision, Recall, Specificity, F1-Score
- Latency percentiles (P50, P90, P99)
- Suggestion verification pass rates
- Category-by-category breakdown tables
