import io
import pytest
from PIL import Image, ImageDraw
import docx

from backend.app.modules.vision.analyzer import (
    analyze_image_brand_consistency,
    analyze_docx_accessibility,
    analyze_pdf_accessibility,
    inspect_asset_accessibility,
    check_ocr_availability,
    match_logo_template,
    is_alt_text_valid,
    calculate_contrast_ratio,
)


def create_solid_image(color1: tuple, color2: tuple) -> bytes:
    """Generate image with two contrasting halves."""
    img = Image.new("RGB", (100, 100), color=color1)
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 0, 100, 100], fill=color2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_image_contrast_and_alt_text():
    # 1. Good contrast image: black and white (21:1 contrast)
    good_img = create_solid_image((0, 0, 0), (255, 255, 255))
    res_good = analyze_image_brand_consistency(
        image_bytes=good_img,
        approved_palette_hex=["#000000", "#FFFFFF"],
        alt_text="High contrast brand logo banner with black on white",
    )
    assert res_good["contrast_analysis"]["wcag_aa_compliant"] is True
    assert res_good["contrast_analysis"]["contrast_ratio"] >= 4.5
    assert res_good["accessibility_score"]["score"] == 100
    assert len(res_good["alt_text_issues"]) == 0

    # 2. Failing contrast image: light grey on white (~1.3:1)
    bad_img = create_solid_image((220, 220, 220), (255, 255, 255))
    res_bad = analyze_image_brand_consistency(
        image_bytes=bad_img,
        approved_palette_hex=["#DCDCDC", "#FFFFFF"],
        alt_text=None,  # Missing alt text
    )
    assert res_bad["contrast_analysis"]["wcag_aa_compliant"] is False
    # Deductions: -15 for contrast, -10 for missing alt text
    score_info = res_bad["accessibility_score"]
    assert score_info["score"] <= 75
    deduction_items = [d["evidence_id"] for d in score_info["deductions"]]
    assert "WCAG-2.2-AA-CONTRAST" in deduction_items
    assert "WCAG-1.1.1-NON-TEXT" in deduction_items


def test_alt_text_validation():
    valid, _ = is_alt_text_valid("Athlete wearing NovaFit pulse track in outdoor stadium")
    assert valid is True

    # Empty
    valid, r1 = is_alt_text_valid("")
    assert valid is False

    # Filename
    valid, r2 = is_alt_text_valid("banner_hero_01.png")
    assert valid is False
    assert "raw filename" in r2

    # Generic word
    valid, r3 = is_alt_text_valid("image")
    assert valid is False
    assert "generic" in r3


def test_docx_accessibility_analyzer():
    doc = docx.Document()
    # 1. Heading skip: Heading 1 -> Heading 3
    doc.add_heading("Product Overview", level=1)
    doc.add_heading("Hardware Specifications", level=3)  # Skip!

    # 2. Paragraph with vague hyperlink
    p = doc.add_paragraph("For more details ")
    # Insert hyperlink with text "click here"
    # In docx XML:
    p_elm = p._element
    hyperlink = docx.oxml.OxmlElement("w:hyperlink")
    run = docx.oxml.OxmlElement("w:r")
    t = docx.oxml.OxmlElement("w:t")
    t.text = "click here"
    run.append(t)
    hyperlink.append(run)
    p_elm.append(hyperlink)

    # 3. Embedded image without alt text
    img_raw = Image.new("RGB", (30, 30), color="blue")
    img_buf = io.BytesIO()
    img_raw.save(img_buf, format="PNG")
    img_buf.seek(0)
    doc.add_picture(img_buf)

    # 4. Table without header row
    table = doc.add_table(rows=3, cols=2)

    doc_buf = io.BytesIO()
    doc.save(doc_buf)
    docx_bytes = doc_buf.getvalue()

    result = analyze_docx_accessibility(docx_bytes, filename="spec.docx")
    assert result["total_issues"] >= 4
    evidence_ids = [f["evidence_id"] for f in result["findings"]]
    assert "WCAG-1.3.1-HEADING-ORDER" in evidence_ids
    assert "WCAG-1.1.1-NON-TEXT" in evidence_ids
    assert "WCAG-2.4.4-LINK-PURPOSE" in evidence_ids
    assert "WCAG-1.3.1-TABLE-HEADER" in evidence_ids

    # Verify score deductions formula
    score_info = result["accessibility_score"]
    expected_deduction = sum(abs(d["points"]) for d in score_info["deductions"])
    assert score_info["score"] == max(0, 100 - expected_deduction)
    assert score_info["formula"] == "100 - sum(deductions)"


def test_pdf_accessibility_analyzer():
    # Build 2-page PDF with no title/lang metadata and 2 embedded raster pages
    buf = io.BytesIO()
    img1 = Image.new("RGB", (100, 100), color=(255, 255, 255))
    img2 = Image.new("RGB", (100, 100), color=(20, 20, 20))
    img1.save(buf, format="PDF", save_all=True, append_images=[img2])
    pdf_bytes = buf.getvalue()

    result = analyze_pdf_accessibility(pdf_bytes, filename="brochure.pdf")
    assert result["asset_metadata"]["page_count"] == 2
    evidence_ids = [f["evidence_id"] for f in result["findings"]]
    assert "PDF-UA-TITLE" in evidence_ids
    assert "PDF-UA-LANG" in evidence_ids
    assert "WCAG-1.1.1-NON-TEXT" in evidence_ids

    # Verify page citation exists in findings
    page_citations = [f.get("page_number") for f in result["findings"] if "page_number" in f]
    assert 1 in page_citations
    assert 2 in page_citations


def test_ocr_availability_and_graceful_handling():
    ocr_status = check_ocr_availability()
    assert isinstance(ocr_status, dict)
    assert "ocr_available" in ocr_status
    assert "reason" in ocr_status
    assert isinstance(ocr_status["ocr_available"], bool)


def test_logo_template_matching():
    target = Image.new("RGB", (120, 120), color=(255, 255, 255))
    logo = Image.new("RGB", (30, 30), color=(255, 255, 255))
    draw = ImageDraw.Draw(logo)
    draw.rectangle([5, 5, 25, 25], fill=(0, 0, 0))
    target.paste(logo, (40, 40))

    found, score = match_logo_template(target, logo, threshold=0.70)
    assert found is True
    assert score >= 0.70

    # Unrelated pattern
    unrelated = Image.new("RGB", (30, 30), color=(255, 255, 255))
    draw2 = ImageDraw.Draw(unrelated)
    draw2.line([(0, 0), (30, 30)], fill=(0, 0, 0), width=1)
    found_bad, score_bad = match_logo_template(target, unrelated, threshold=0.90)
    assert found_bad is False
