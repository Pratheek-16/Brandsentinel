import os
import json
import pytest
from backend.app.modules.deterministic.checks import run_deterministic_checks
from backend.app.modules.verification import verify_findings

def test_brandbench_dataset_conformance():
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "..", "benchmark", "dataset.json")
    assert os.path.exists(dataset_path), "BrandBench dataset.json must exist"

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    assert len(dataset) == 150, f"Expected 150 BrandBench cases, found {len(dataset)}"

    categories = set(d["category"] for d in dataset)
    expected_categories = {"tone", "terminology", "messaging", "claim", "accessibility", "clean", "injection"}
    assert expected_categories.issubset(categories), f"Missing categories: {expected_categories - categories}"

    # Evaluate deterministic review engine on all clean and injection cases
    for item in dataset:
        findings = run_deterministic_checks(item["text"])
        clean_findings = verify_findings(findings, item["text"])
        if item["category"] == "clean":
            assert len(clean_findings) == 0, f"Clean case {item['id']} falsely flagged: {clean_findings}"
        elif item["expected_violation"]:
            assert len(clean_findings) > 0, f"Violation case {item['id']} [{item['category']}] not flagged: {item['text']}"
