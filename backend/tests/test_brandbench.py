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


def test_brandbench_v2_heldout_dataset():
    v2_path = os.path.join(os.path.dirname(__file__), "..", "..", "benchmark", "brandbench_v2_heldout.json")
    assert os.path.exists(v2_path), "brandbench_v2_heldout.json must exist"

    with open(v2_path, "r", encoding="utf-8") as f:
        v2_items = json.load(f)

    assert len(v2_items) >= 60, f"Expected >= 60 held-out cases, found {len(v2_items)}"

    brands = set(item["brand"] for item in v2_items)
    expected_brands = {"NovaFit", "Lumen Bank", "Aster University", "Solaria Solar"}
    assert expected_brands.issubset(brands), f"Missing brands: {expected_brands - brands}"

    adversarial_count = sum(1 for item in v2_items if item.get("is_adversarial"))
    assert adversarial_count >= 10, f"Expected >= 10 adversarial injection cases, found {adversarial_count}"

    report_path = os.path.join(os.path.dirname(__file__), "..", "..", "benchmark", "report.md")
    assert os.path.exists(report_path), "benchmark/report.md must exist"

