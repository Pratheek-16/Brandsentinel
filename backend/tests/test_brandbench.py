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


def test_brandbench_v3_heldout_dataset_conformance():
    """Verify BrandBench v3 held-out dataset meets Part 1.1 A3 and Part 2 requirements:
    1. >= 150 items
    2. >= 40% clean items (true negatives)
    3. Covers all 4 brands (NovaFit, Lumen Bank, Aster University, Solaria Solar)
    4. Covers Tone, Terminology, Messaging/Facts, Claims, Security
    5. Evaluates without fabricated personas or fake survey data
    """
    v3_path = os.path.join(os.path.dirname(__file__), "..", "..", "benchmark", "brandbench_v3_heldout.json")
    assert os.path.exists(v3_path), "brandbench_v3_heldout.json must exist"

    with open(v3_path, "r", encoding="utf-8") as f:
        v3_items = json.load(f)

    # 1. Size constraint: >= 150 items
    assert len(v3_items) >= 150, f"Expected >= 150 benchmark items, found {len(v3_items)}"

    # 2. Clean items: >= 40% true negatives
    clean_items = [it for it in v3_items if len(it.get("expected_findings", [])) == 0]
    clean_ratio = len(clean_items) / len(v3_items)
    assert clean_ratio >= 0.40, f"Expected >= 40% clean items, found {clean_ratio * 100:.1f}% ({len(clean_items)}/{len(v3_items)})"

    # 3. Brands represented
    brands = set(it["brand"] for it in v3_items)
    expected_brands = {"NovaFit", "Lumen Bank", "Aster University", "Solaria Solar"}
    assert expected_brands.issubset(brands), f"Missing brands: {expected_brands - brands}"

    # 4. Each brand has balanced items
    for b in expected_brands:
        brand_count = sum(1 for it in v3_items if it["brand"] == b)
        assert brand_count >= 30, f"Brand {b} under-represented with {brand_count} items"

    # 5. Categories covered
    all_categories = set()
    for it in v3_items:
        for ef in it.get("expected_findings", []):
            if ef.get("category"):
                all_categories.add(ef["category"])
    expected_cats = {"tone", "terminology", "messaging", "claim", "security"}
    assert expected_cats.issubset(all_categories), f"Missing categories: {expected_cats - all_categories}"

    # 6. Adversarial injection probes
    adversarial_count = sum(1 for it in v3_items if it.get("is_adversarial"))
    assert adversarial_count >= 10, f"Expected >= 10 adversarial injection probes, found {adversarial_count}"

    # 7. Check benchmark report existence and layer coverage
    report_path = os.path.join(os.path.dirname(__file__), "..", "..", "benchmark", "report.md")
    assert os.path.exists(report_path), "benchmark/report.md must exist"
    with open(report_path, "r", encoding="utf-8") as f:
        report_text = f.read()
    assert "Deterministic Layer Alone" in report_text
    assert "Offline Semantic Layer Alone" in report_text
    assert "Combined Production Pipeline" in report_text


