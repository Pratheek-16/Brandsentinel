# Testing Strategy and Benchmark Evaluation

BrandSentinel maintains a comprehensive automated testing suite encompassing unit tests, database migration tests, RBAC integration tests, workflow state validation, six end-to-end user journeys, and the BrandBench v3 held-out evaluation harness.

---

## 1. Test Architecture

The test suite is built on **pytest** and **Starlette TestClient**, located in `backend/tests/`:

| Test Suite | File | Focus Areas | Tests |
| :--- | :--- | :--- | :--- |
| **Health & Sanity** | `test_health.py` | Basic API uptime and OpenAPI schema availability | 1 |
| **Data Models** | `test_models_and_tables.py` | SQLite & PostgreSQL schema integrity and foreign keys | 1 |
| **Redaction & Review** | `test_redaction_and_review.py` | PII regex tokenization, placeholder restitution, AIUsage ledger | 2 |
| **RBAC & Isolation** | `test_rbac_and_isolation.py` | Role permissions, cross-workspace denial, no-self-approval rule | 3 |
| **Knowledge Base** | `test_kb_crud_and_versioning.py` | Rule CRUD, rule atomisation engine, version snapshots | 3 |
| **Dynamic Detection** | `test_kb_driven_detection.py` | Zero-code dynamic KB term additions and 4th workspace testing | 2 |
| **Retrieval & Claims** | `test_retrieval_gemini_and_claims.py` | VectorStore cosine similarity, claim ledger status classification | 3 |
| **Offline Semantic Engine** | `test_semantic_engine.py` | Paraphrased and reworded violation matching with 0 external keys | 1 |
| **Verifier Reliability** | `test_verifier_reliability.py` | Grounding verifier, quote matching, span offsets, hallucination drops | 5 |
| **Workflow & Audit** | `test_workflow_audit_and_escalation.py` | State machine transitions, risk escalation, SHA-256 hash chaining | 3 |
| **The Three Improvements** | `test_improvements.py` | I-1 (Suggestion Engine), I-2 (CIELAB & WCAG), I-3 (Ambiguity Detector) | 4 |
| **Ambiguity & Insights** | `test_insights_and_ambiguity.py` | 4 ambiguity signals and new KB version clarification acceptance | 2 |
| **Vision & Accessibility** | `test_vision_and_accessibility.py` | Contrast ratio, alt text, PDF/DOCX page citations, logo checks | 7 |
| **Comprehensive Audit** | `test_comprehensive_audit.py` | Real credentials, workspace isolation, lifecycle edits, upload security | 6 |
| **BrandBench Conformance** | `test_brandbench.py` | Dataset integrity (160 items, >=40% clean items, 4 brands) | 3 |
| **End-to-End User Journeys** | `test_e2e_journeys.py` | 6 full journeys: Creator, Escalation, Admin, Visual, Audit, Robustness | 6 |

**Total Test Count:** **55 passed in 6.53s** (100% green, 0 failures).

---

## 2. Running Automated Tests

### Windows (PowerShell)
```powershell
# Run full test suite
python -m pytest backend/tests/ -v
```

### Verified Output
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.2.2, pluggy-1.7.0
rootdir: C:\Users\sreep\Desktop\psp\codezen-project
plugins: anyio-4.16.0
collected 55 items

backend/tests/test_brandbench.py::test_brandbench_dataset_conformance PASSED [  1%]
backend/tests/test_brandbench.py::test_brandbench_v2_heldout_dataset PASSED [  3%]
backend/tests/test_brandbench.py::test_brandbench_v3_heldout_dataset_conformance PASSED [  5%]
backend/tests/test_comprehensive_audit.py::test_auth_real_credentials_and_me PASSED [  7%]
backend/tests/test_comprehensive_audit.py::test_workspace_isolation_and_no_leakage PASSED [  9%]
backend/tests/test_comprehensive_audit.py::test_kb_version_cloning_and_activation PASSED [ 10%]
backend/tests/test_comprehensive_audit.py::test_finding_status_lifecycle_and_tracked_edits PASSED [ 12%]
backend/tests/test_comprehensive_audit.py::test_upload_security_and_validation PASSED [ 14%]
backend/tests/test_comprehensive_audit.py::test_audit_hash_chain_tamper_verification PASSED [ 16%]
backend/tests/test_e2e_journeys.py::test_journey_1_creator_workflow PASSED [ 18%]
backend/tests/test_e2e_journeys.py::test_journey_2_escalation_and_no_self_approval PASSED [ 20%]
backend/tests/test_e2e_journeys.py::test_journey_3_admin_kb_and_ambiguity_clarification PASSED [ 21%]
backend/tests/test_e2e_journeys.py::test_journey_4_visual_and_accessibility PASSED [ 23%]
backend/tests/test_e2e_journeys.py::test_journey_5_audit_hash_chain_and_ledger PASSED [ 25%]
backend/tests/test_e2e_journeys.py::test_journey_6_robustness_and_isolation PASSED [ 27%]
backend/tests/test_governance_and_security.py::test_indian_pii_redaction PASSED [ 29%]
backend/tests/test_governance_and_security.py::test_jwt_secret_startup_protection PASSED [ 30%]
backend/tests/test_governance_and_security.py::test_ai_ledger_and_governance_export PASSED [ 32%]
backend/tests/test_health.py::test_health PASSED                         [ 34%]
backend/tests/test_improvements.py::test_improvement_1_suggestion_engine_and_actions PASSED [ 36%]
backend/tests/test_improvements.py::test_improvement_2_visual_consistency_and_accessibility PASSED [ 38%]
backend/tests/test_improvements.py::test_improvement_3_insights_and_ambiguity_detector PASSED [ 40%]
backend/tests/test_improvements.py::test_improvement_1_meaning_preservation_branches PASSED [ 41%]
backend/tests/test_insights_and_ambiguity.py::test_ambiguity_four_signals PASSED [ 43%]
backend/tests/test_insights_and_ambiguity.py::test_accept_clarification_activates_new_kb_version PASSED [ 45%]
backend/tests/test_kb_crud_and_versioning.py::test_kb_crud_and_permissions PASSED [ 47%]
backend/tests/test_kb_crud_and_versioning.py::test_rule_atomisation_and_confirm_import PASSED [ 49%]
backend/tests/test_kb_crud_and_versioning.py::test_kb_versioning PASSED  [ 50%]
backend/tests/test_kb_driven_detection.py::test_dynamic_kb_term_add_and_remove PASSED [ 52%]
backend/tests/test_kb_driven_detection.py::test_fourth_fictional_workspace_zero_code_changes PASSED [ 54%]
backend/tests/test_models_and_tables.py::test_all_remaining_tables_and_crud PASSED [ 56%]
backend/tests/test_rbac_and_isolation.py::test_rbac_creation_restrictions PASSED [ 58%]
backend/tests/test_rbac_and_isolation.py::test_cross_workspace_isolation PASSED [ 60%]
backend/tests/test_rbac_and_isolation.py::test_no_self_approval_and_manager_approval PASSED [ 61%]
backend/tests/test_redaction_and_review.py::test_redact_and_restore_unit PASSED [ 63%]
backend/tests/test_redaction_and_review.py::test_review_with_redaction_persisted_in_ai_usage PASSED [ 65%]
backend/tests/test_retrieval_gemini_and_claims.py::test_vector_store_retrieval_unit PASSED [ 67%]
backend/tests/test_retrieval_gemini_and_claims.py::test_ai_provider_factory PASSED [ 69%]
backend/tests/test_retrieval_gemini_and_claims.py::test_claim_ledger_evaluation PASSED [ 70%]
backend/tests/test_semantic_engine.py::test_semantic_engine_10_reworded_probe_and_clean_texts PASSED [ 72%]
backend/tests/test_verifier_reliability.py::test_verifier_blocks_hallucinated_rule_id PASSED [ 74%]
backend/tests/test_verifier_reliability.py::test_verifier_blocks_fabricated_quote PASSED [ 76%]
backend/tests/test_verifier_reliability.py::test_verifier_blocks_offset_mismatch PASSED [ 78%]
backend/tests/test_verifier_reliability.py::test_verifier_accepts_legitimate_grounded_finding PASSED [ 80%]
backend/tests/test_verifier_reliability.py::test_vector_store_retrieval_filtering PASSED [ 81%]
backend/tests/test_vision_and_accessibility.py::test_image_contrast_and_alt_text PASSED [ 83%]
backend/tests/test_vision_and_accessibility.py::test_alt_text_validation PASSED [ 85%]
backend/tests/test_vision_and_accessibility.py::test_docx_accessibility_analyzer PASSED [ 87%]
backend/tests/test_vision_and_accessibility.py::test_pdf_accessibility_analyzer PASSED [ 89%]
backend/tests/test_vision_and_accessibility.py::test_ocr_availability_and_graceful_handling PASSED [ 90%]
backend/tests/test_vision_and_accessibility.py::test_logo_template_matching PASSED [ 92%]
backend/tests/test_vision_and_accessibility.py::test_logo_usage_stretched_and_too_small PASSED [ 94%]
backend/tests/test_workflow_audit_and_escalation.py::test_workflow_state_machine_and_escalation PASSED [ 96%]
backend/tests/test_workflow_audit_and_escalation.py::test_comments_threading PASSED [ 98%]
backend/tests/test_workflow_audit_and_escalation.py::test_audit_log_and_tamper_verification PASSED [100%]

======================= 55 passed, 11 warnings in 6.53s =======================
```

---

## 3. BrandBench v3 Held-Out Benchmark Harness

**BrandBench v3** (`benchmark/brandbench_v3_heldout.json`) contains **160 rigorously labelled held-out test cases**:
- **4 Brands Evaluated:** NovaFit (40), Lumen Bank (40), Aster University (40), Solaria Solar (40 novel 4th workspace)
- **92 Violation Cases:** Spanning Tone, Terminology, Messaging/Facts, Claims, and Security
- **68 Clean True Negatives (42.5%):** Systematically verifying zero false positives on compliant brand copy
- **12 Adversarial Prompt Injection Probes:** Verifying prompt injection resistance and guideline enforcement

### Running BrandBench v3
```powershell
python benchmark/run_benchmark.py
```

### Verified Multi-Layer Benchmark Output (`benchmark/report.md`)
| Pipeline Layer | Precision | Recall | F1 Score | False Positive Rate | Latency (p50) | Latency (p95) | Injection Bypass Rate |
|---|---|---|---|---|---|---|---|
| **1. Deterministic Layer Alone** | 96.8% | 97.8% | 97.3% | 4.4% | 2.0 ms | 3.5 ms | 0.0% |
| **2. Offline Semantic Layer Alone** | 100.0% | 60.9% | 75.7% | 0.0% | 1.6 ms | 2.6 ms | 0.0% |
| **3. Grounded LLM Layer Alone** | 100.0% | 0.0% | 0.0% | 0.0% | 822.2 ms | 1021.7 ms | 100.0% |
| **4. Combined Production Pipeline** | **96.8%** | **97.8%** | **97.3%** | **4.4%** | 821.0 ms | 1228.2 ms | **0.0%** |
