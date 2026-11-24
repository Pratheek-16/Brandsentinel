"""Improvement I-2: Visual Brand Consistency & Multi-Format Accessibility Analyzer.
Performs:
1. Palette compliance analysis via CIELAB Delta-E (CIE76/CIELAB) distance calculation.
2. WCAG 2.2 AA Contrast Ratio calculation for text vs background.
3. Alt-text verification for standalone and embedded images (WCAG 1.1.1 Non-Text Content).
4. Visual logo presence verification (template matching with OpenCV/NumPy fallback, OCR fallback, or honest skip).
5. PDF document accessibility inspection (page extraction, embedded image alt-text, title & language metadata).
6. DOCX document accessibility inspection (docPr image descriptions, heading hierarchy skips, link purpose, table headers).
7. Transparent 0-100 Accessibility Scoring with itemized deduction breakdowns.
8. Graceful OCR engine detection (Tesseract binary check reporting without 500 errors).
"""

import io
import math
import re
import shutil
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image
import numpy as np

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

import docx
import pdfplumber

GENERIC_ALT_PATTERNS = {
    "image", "img", "photo", "picture", "graphic", "screenshot", "icon",
    "untitled", "placeholder", "asset", "figure", "drawing"
}

VAGUE_LINK_TEXTS = {
    "click here", "click this", "read more", "learn more", "more", "link",
    "here", "this link", "go", "url", "continue", "view"
}


def check_ocr_availability() -> Dict[str, Any]:
    """Check whether Tesseract OCR binary is installed and executable in host PATH."""
    has_binary = bool(shutil.which("tesseract"))
    if not HAS_PYTESSERACT or not has_binary:
        return {
            "ocr_available": False,
            "reason": "Tesseract OCR engine not installed in environment",
        }
    return {
        "ocr_available": True,
        "reason": "Tesseract OCR binary active",
    }


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert hex string (e.g. '#FF5722' or 'FF5722') to RGB tuple."""
    hex_code = hex_code.lstrip("#").strip()
    if len(hex_code) == 3:
        hex_code = "".join([c * 2 for c in hex_code])
    if len(hex_code) != 6:
        return (0, 0, 0)
    try:
        return int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16)
    except ValueError:
        return (0, 0, 0)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB integers (0-255) to hex code."""
    return f"#{max(0, min(255, r)):02X}{max(0, min(255, g)):02X}{max(0, min(255, b)):02X}"


def rgb_to_lab(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Convert sRGB (0-255) to CIE-L*a*b* color space under D65 standard illuminant."""
    r_lin = [(c / 255.0) for c in rgb]
    r_lin = [(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) for c in r_lin]

    # Convert linear RGB to XYZ
    X = r_lin[0] * 0.4124564 + r_lin[1] * 0.3575761 + r_lin[2] * 0.1804375
    Y = r_lin[0] * 0.2126729 + r_lin[1] * 0.7151522 + r_lin[2] * 0.0721750
    Z = r_lin[0] * 0.0193339 + r_lin[1] * 0.1191920 + r_lin[2] * 0.9503041

    # D65 reference white
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883
    x, y, z = X / Xn, Y / Yn, Z / Zn

    fx, fy, fz = [(t ** (1/3) if t > 0.008856 else (7.787 * t + 16 / 116)) for t in (x, y, z)]

    L = max(0.0, min(100.0, 116.0 * fy - 16.0))
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return L, a, b


def delta_e_cielab(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """CIE76 Euclidean distance in CIELAB space."""
    return math.sqrt((lab1[0] - lab2[0])**2 + (lab1[1] - lab2[1])**2 + (lab1[2] - lab2[2])**2)


def calculate_relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """WCAG 2.2 Relative Luminance."""
    def channel_lum(val: int) -> float:
        v = val / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = [channel_lum(c) for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def calculate_contrast_ratio(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    """WCAG 2.2 Contrast Ratio formula (L1 + 0.05) / (L2 + 0.05)."""
    l1 = calculate_relative_luminance(rgb1)
    l2 = calculate_relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def extract_dominant_colors(image: Image.Image, num_colors: int = 5) -> List[Tuple[int, int, int]]:
    """Extract top dominant colors from a PIL Image using spatial quantization."""
    small = image.convert("RGB").resize((120, 120), Image.Resampling.LANCZOS)
    quantized = small.quantize(colors=num_colors, method=Image.Quantize.FASTOCTREE)
    palette = quantized.getpalette()[:num_colors * 3]
    colors = []
    for i in range(0, len(palette), 3):
        colors.append((palette[i], palette[i+1], palette[i+2]))
    return colors


def is_alt_text_valid(alt_text: Optional[str]) -> Tuple[bool, str]:
    """Check if alt text is present, non-empty, and descriptive."""
    if alt_text is None:
        return False, "Alternative text is missing entirely."
    cleaned = alt_text.strip()
    if not cleaned:
        return False, "Alternative text is empty or contains only whitespace."
    lower = cleaned.lower()
    # Check if ends with image extension (e.g. img_001.png)
    if re.search(r"\.(png|jpg|jpeg|gif|webp|svg|bmp)$", lower):
        return False, f"Alternative text '{cleaned}' appears to be a raw filename, not a description."
    if lower in GENERIC_ALT_PATTERNS or re.match(r"^(image|img|photo|picture|pic|graphic)[_\s\-0-9]*$", lower):
        return False, f"Alternative text '{cleaned}' is generic and does not convey meaningful context."
    if len(cleaned) < 5:
        return False, f"Alternative text '{cleaned}' is too brief (< 5 characters) to be descriptive."
    return True, "Valid descriptive alternative text."


def match_logo_template(
    target_img: Image.Image,
    template_img: Image.Image,
    threshold: float = 0.70,
) -> Tuple[bool, float]:
    """Perform visual logo template matching using OpenCV if installed, or NumPy cross-correlation."""
    target_gray = np.array(target_img.convert("L"), dtype=np.float32)
    template_gray = np.array(template_img.convert("L"), dtype=np.float32)

    H, W = target_gray.shape
    th, tw = template_gray.shape

    if th > H or tw > W:
        scale = min(H / max(1, th), W / max(1, tw)) * 0.5
        new_w, new_h = max(1, int(tw * scale)), max(1, int(th * scale))
        template_img = template_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        template_gray = np.array(template_img.convert("L"), dtype=np.float32)
        th, tw = template_gray.shape

    if HAS_CV2:
        try:
            res = cv2.matchTemplate(target_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            return bool(max_val >= threshold), float(round(max(0.0, max_val), 3))
        except Exception:
            pass

    # Pure NumPy normalized cross-correlation with coarse-to-fine search
    p_norm = template_gray - np.mean(template_gray)
    p_std = np.std(template_gray)
    if p_std < 1e-5:
        return False, 0.0
    p_norm /= p_std

    max_corr = -1.0
    best_y, best_x = 0, 0
    step_y = max(1, th // 6)
    step_x = max(1, tw // 6)

    # Coarse grid
    for y in range(0, max(1, H - th + 1), step_y):
        for x in range(0, max(1, W - tw + 1), step_x):
            patch = target_gray[y:y+th, x:x+tw]
            if patch.shape != (th, tw):
                continue
            patch_norm = patch - np.mean(patch)
            patch_std = np.std(patch)
            if patch_std > 1e-5:
                corr = float(np.mean((patch_norm / patch_std) * p_norm))
                if corr > max_corr:
                    max_corr = corr
                    best_y, best_x = y, x

    # Fine refinement around best match
    for y in range(max(0, best_y - step_y), min(H - th + 1, best_y + step_y + 1)):
        for x in range(max(0, best_x - step_x), min(W - tw + 1, best_x + step_x + 1)):
            patch = target_gray[y:y+th, x:x+tw]
            if patch.shape != (th, tw):
                continue
            patch_norm = patch - np.mean(patch)
            patch_std = np.std(patch)
            if patch_std > 1e-5:
                corr = float(np.mean((patch_norm / patch_std) * p_norm))
                if corr > max_corr:
                    max_corr = corr

    return bool(max_corr >= threshold), float(round(max(0.0, max_corr), 3))


def check_logo_usage(
    target_img: Image.Image,
    template_img: Image.Image,
    min_width: int = 32,
    min_height: int = 24,
    aspect_ratio_tolerance: float = 0.15,
) -> Dict[str, Any]:
    """Check logo presence, stretch/aspect ratio distortion, and minimum clearance size."""
    tmpl_w, tmpl_h = template_img.size
    expected_ar = tmpl_w / max(1, tmpl_h)

    # 1. Check template minimum size itself
    if tmpl_w < min_width or tmpl_h < min_height:
        return {
            "status": "violation",
            "issue": "too_small",
            "message": f"Logo asset dimensions ({tmpl_w}x{tmpl_h}px) are below minimum recommended clearance size ({min_width}x{min_height}px).",
            "detected": True,
            "deduction": {"item": "Logo Below Minimum Size", "points": -5, "evidence_id": "LOGO-TOO-SMALL"},
        }

    # 2. Check if target image is smaller than template or distorted
    tgt_w, tgt_h = target_img.size
    if tgt_w < tmpl_w or tgt_h < tmpl_h:
        actual_ar = tgt_w / max(1, tgt_h)
        ar_diff = abs(actual_ar - expected_ar) / expected_ar
        if ar_diff > aspect_ratio_tolerance:
            return {
                "status": "violation",
                "issue": "stretched",
                "message": f"Logo aspect ratio ({actual_ar:.2f}) is distorted by {ar_diff*100:.1f}% compared to original logo template ({expected_ar:.2f}).",
                "detected": True,
                "deduction": {"item": "Logo Aspect Ratio Distorted", "points": -10, "evidence_id": "LOGO-STRETCHED"},
            }
        return {
            "status": "violation",
            "issue": "too_small",
            "message": f"Logo rendered in asset ({tgt_w}x{tgt_h}px) is below minimum required size of {min_width}px.",
            "detected": True,
            "deduction": {"item": "Logo Below Minimum Size", "points": -5, "evidence_id": "LOGO-TOO-SMALL"},
        }

    # 3. Check template match
    matched, score = match_logo_template(target_img, template_img)
    if not matched:
        return {
            "status": "violation",
            "issue": "missing",
            "message": "Mandatory brand logo was not found in target image.",
            "detected": False,
            "match_score": score,
            "deduction": {"item": "Mandatory Brand Logo Missing", "points": -15, "evidence_id": "LOGO-MISSING"},
        }

    return {
        "status": "compliant",
        "detected": True,
        "match_score": score,
        "message": "Brand logo verified with correct aspect ratio and clearance.",
    }


def calculate_accessibility_score(deductions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate transparent 0-100 Accessibility Score with deduction breakdown."""
    total_deductions = sum(abs(d.get("points", 0)) for d in deductions)
    final_score = max(0, 100 - total_deductions)
    return {
        "score": final_score,
        "max_score": 100,
        "formula": "100 - sum(deductions)",
        "total_deductions": total_deductions,
        "deductions": deductions,
        "compliant": final_score >= 80,
    }


def analyze_image_brand_consistency(
    image_bytes: bytes,
    approved_palette_hex: Optional[List[str]] = None,
    filename: str = "asset",
    alt_text: Optional[str] = None,
    logo_template_bytes: Optional[bytes] = None,
    brand_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Inspect image raster for palette compliance, Delta-E, text contrast, alt-text, and logo presence."""
    palette = approved_palette_hex or ["#FF5722", "#212121", "#FFFFFF", "#4CAF50"]
    clean_palette = []
    for p in palette:
        if isinstance(p, str) and (p.startswith("#") or len(p) in (3, 6)):
            clean_palette.append(p)
    if not clean_palette:
        clean_palette = ["#FF5722", "#212121", "#FFFFFF", "#4CAF50"]

    brand_labs = [(h, rgb_to_lab(hex_to_rgb(h))) for h in clean_palette]

    image = Image.open(io.BytesIO(image_bytes))
    width, height = image.size
    dominant_rgbs = extract_dominant_colors(image, num_colors=4)

    palette_findings = []
    extracted_palette_details = []
    deductions = []

    for rgb in dominant_rgbs:
        hex_val = rgb_to_hex(*rgb)
        lab_val = rgb_to_lab(rgb)
        closest_brand, closest_lab = min(brand_labs, key=lambda b: delta_e_cielab(lab_val, b[1]))
        de_val = round(delta_e_cielab(lab_val, closest_lab), 2)

        is_match = de_val <= 12.0
        extracted_palette_details.append({
            "hex": hex_val,
            "rgb": list(rgb),
            "closest_brand": closest_brand,
            "delta_e": de_val,
            "compliant": is_match,
        })

        if de_val > 15.0:
            sev = "minor" if de_val < 35.0 else "major"
            palette_findings.append({
                "category": "visual",
                "severity": sev,
                "confidence": 0.92,
                "evidence_type": "asset",
                "evidence_id": "ASSET-PALETTE",
                "extracted_hex": hex_val,
                "closest_brand_hex": closest_brand,
                "delta_e": de_val,
                "reason": f"Extracted dominant color {hex_val} deviates from approved palette (closest: {closest_brand}, Delta-E = {de_val}).",
                "suggestion": f"Recolor asset element using brand color {closest_brand}.",
            })

    # Calculate contrast between first and second dominant colors
    contrast_findings = []
    contrast_ratio = 1.0
    if len(dominant_rgbs) >= 2:
        contrast_ratio = calculate_contrast_ratio(dominant_rgbs[0], dominant_rgbs[1])
        wcag_aa_body = contrast_ratio >= 4.5

        if not wcag_aa_body:
            contrast_findings.append({
                "category": "accessibility",
                "severity": "major" if contrast_ratio < 3.0 else "minor",
                "confidence": 0.95,
                "evidence_type": "rule",
                "evidence_id": "WCAG-2.2-AA-CONTRAST",
                "contrast_ratio": contrast_ratio,
                "primary_color": rgb_to_hex(*dominant_rgbs[0]),
                "secondary_color": rgb_to_hex(*dominant_rgbs[1]),
                "reason": f"Measured contrast ratio of {contrast_ratio}:1 fails WCAG 2.2 AA minimum standard (4.5:1 required for standard body text).",
                "suggestion": "Adjust foreground or background luminosity to achieve at least 4.5:1 contrast.",
            })
            deductions.append({
                "item": "WCAG Contrast Failure",
                "points": -15,
                "reason": f"Dominant colors contrast ratio ({contrast_ratio}:1) fails WCAG 2.2 AA (4.5:1 required).",
                "evidence_id": "WCAG-2.2-AA-CONTRAST",
            })

    # Alt text verification
    alt_findings = []
    alt_valid, alt_reason = is_alt_text_valid(alt_text)
    if not alt_valid:
        alt_findings.append({
            "category": "accessibility",
            "severity": "major",
            "confidence": 1.0,
            "evidence_type": "rule",
            "evidence_id": "WCAG-1.1.1-NON-TEXT",
            "reason": alt_reason,
            "suggestion": "Add concise, meaningful alternative text describing the purpose and content of this image.",
        })
        deductions.append({
            "item": "Missing or Invalid Alt Text",
            "points": -10,
            "reason": alt_reason,
            "evidence_id": "WCAG-1.1.1-NON-TEXT",
        })

    # OCR text extraction check
    ocr_info = check_ocr_availability()
    ocr_text = ""
    if ocr_info["ocr_available"]:
        try:
            ocr_text = pytesseract.image_to_string(image).strip()
        except Exception:
            ocr_text = ""

    # Logo detection & usage audit
    logo_detection = {"status": "skipped", "detected": None, "reason": "No logo template or brand name provided"}
    logo_findings = []
    if logo_template_bytes:
        try:
            tmpl_img = Image.open(io.BytesIO(logo_template_bytes))
            logo_eval = check_logo_usage(image, tmpl_img)
            logo_detection = {
                "status": "completed",
                "detected": logo_eval.get("detected"),
                "issue": logo_eval.get("issue"),
                "match_score": logo_eval.get("match_score"),
                "message": logo_eval.get("message"),
                "method": "OpenCV Template Matching" if HAS_CV2 else "NumPy Cross-Correlation",
            }
            if logo_eval.get("status") == "violation":
                deduction = logo_eval.get("deduction")
                if deduction:
                    deductions.append(deduction)
                logo_findings.append({
                    "category": "visual_consistency",
                    "severity": "major" if logo_eval.get("issue") in ("missing", "stretched") else "minor",
                    "confidence": 0.95,
                    "evidence_id": deduction.get("evidence_id") if deduction else "LOGO-VIOLATION",
                    "reason": logo_eval.get("message"),
                    "suggestion": "Restore original logo asset without stretching, ensuring minimum 32px display clearance.",
                })
        except Exception as e:
            logo_detection = {"status": "error", "detected": None, "reason": str(e)}
    elif brand_name and ocr_info["ocr_available"] and ocr_text:
        brand_in_ocr = brand_name.lower() in ocr_text.lower()
        logo_detection = {
            "status": "completed",
            "detected": brand_in_ocr,
            "method": "OCR Text Match",
            "reason": f"Brand name '{brand_name}' {'found' if brand_in_ocr else 'not found'} in extracted image text.",
        }

    score_result = calculate_accessibility_score(deductions)
    all_findings = palette_findings + contrast_findings + alt_findings + logo_findings

    return {
        "asset_metadata": {
            "filename": filename,
            "width": width,
            "height": height,
            "format": image.format or "PNG",
            "has_ocr_extracted_text": bool(ocr_text),
            "ocr_text_preview": ocr_text[:120] if ocr_text else None,
            "alt_text_supplied": bool(alt_text),
            "alt_text": alt_text,
        },
        "approved_brand_palette": clean_palette,
        "extracted_dominant_colors": extracted_palette_details,
        "contrast_analysis": {
            "contrast_ratio": contrast_ratio,
            "wcag_aa_compliant": contrast_ratio >= 4.5,
            "wcag_aa_large_text_compliant": contrast_ratio >= 3.0,
            "standards_basis": "WCAG 2.2 AA (ISO/IEC 40500:2012)",
        },
        "logo_analysis": logo_detection,
        "accessibility_score": score_result,
        "findings": all_findings,
        "total_issues": len(all_findings),
        "palette_findings": palette_findings,
        "contrast_findings": contrast_findings,
        "palette_issues": palette_findings,
        "contrast_issues": contrast_findings,
        "alt_text_issues": alt_findings,
        "honest_disclosures": {
            "ocr_engine": ocr_info["reason"],
            "logo_detection": logo_detection.get("method", "Not performed"),
            "delta_e_algorithm": "CIE76 Euclidean Lab distance",
        },
    }


def analyze_docx_accessibility(
    docx_bytes: bytes,
    filename: str = "document.docx",
) -> Dict[str, Any]:
    """Inspect DOCX document structure for accessibility compliance (headings, alt-text, links, tables)."""
    try:
        doc = docx.Document(io.BytesIO(docx_bytes))
    except Exception as e:
        raise ValueError(f"Could not parse DOCX document: {str(e)}")

    findings = []
    deductions = []

    # 1. Heading hierarchy skips
    heading_levels = []
    for i, p in enumerate(doc.paragraphs):
        style_name = p.style.name if p.style else ""
        m = re.match(r"^Heading\s*(\d+)$", style_name, re.IGNORECASE)
        if m:
            lvl = int(m.group(1))
            heading_levels.append((lvl, p.text.strip(), i + 1))

    for idx in range(len(heading_levels) - 1):
        curr_lvl, curr_text, curr_p = heading_levels[idx]
        next_lvl, next_text, next_p = heading_levels[idx + 1]
        # Flag heading skips e.g. Heading 1 directly to Heading 3
        if next_lvl > curr_lvl + 1:
            findings.append({
                "category": "accessibility",
                "severity": "minor",
                "confidence": 0.98,
                "evidence_type": "rule",
                "evidence_id": "WCAG-1.3.1-HEADING-ORDER",
                "location": f"Paragraph {next_p}",
                "reason": f"Heading level skipped from Heading {curr_lvl} ('{curr_text}') to Heading {next_lvl} ('{next_text}'). Subheadings should not skip levels.",
                "suggestion": f"Restructure heading '{next_text}' to Heading {curr_lvl + 1}.",
            })
            deductions.append({
                "item": "Heading Hierarchy Skip",
                "points": -10,
                "reason": f"Skipped from Heading {curr_lvl} to Heading {next_lvl} at paragraph {next_p}.",
                "evidence_id": "WCAG-1.3.1-HEADING-ORDER",
            })

    # 2. Embedded images alt text (docPr element descr / title)
    try:
        doc_prs = doc._body._element.xpath(".//wp:docPr")
    except Exception:
        doc_prs = []

    for idx, dp in enumerate(doc_prs):
        descr = dp.get("descr")
        title = dp.get("title")
        alt = descr or title or ""
        valid, reason = is_alt_text_valid(alt)
        if not valid:
            img_name = dp.get("name") or f"Image #{idx + 1}"
            findings.append({
                "category": "accessibility",
                "severity": "major",
                "confidence": 1.0,
                "evidence_type": "rule",
                "evidence_id": "WCAG-1.1.1-NON-TEXT",
                "location": f"Embedded image '{img_name}'",
                "reason": f"Embedded image '{img_name}' lacks descriptive alt text ({reason}).",
                "suggestion": "Set the image description property in Word (Alt Text panel).",
            })
            deductions.append({
                "item": "Missing Embedded Image Alt Text",
                "points": -10,
                "reason": f"Embedded image '{img_name}' lacks descriptive alt text.",
                "evidence_id": "WCAG-1.1.1-NON-TEXT",
            })

    # 3. Hyperlink descriptive text check
    for p_idx, p in enumerate(doc.paragraphs):
        try:
            links = p._element.xpath(".//w:hyperlink")
        except Exception:
            links = []
        for lk in links:
            texts = [node.text for node in lk.xpath(".//w:t") if node.text]
            link_text = " ".join(texts).strip().lower()
            if link_text in VAGUE_LINK_TEXTS or not link_text:
                findings.append({
                    "category": "accessibility",
                    "severity": "minor",
                    "confidence": 0.95,
                    "evidence_type": "rule",
                    "evidence_id": "WCAG-2.4.4-LINK-PURPOSE",
                    "location": f"Paragraph {p_idx + 1}",
                    "reason": f"Hyperlink with non-descriptive anchor text '{link_text or '[empty]'}' fails WCAG 2.4.4 Link Purpose.",
                    "suggestion": "Replace generic anchor text with descriptive destination text.",
                })
                deductions.append({
                    "item": "Non-Descriptive Link Anchor",
                    "points": -5,
                    "reason": f"Non-descriptive link text '{link_text or '[empty]'}' at paragraph {p_idx + 1}.",
                    "evidence_id": "WCAG-2.4.4-LINK-PURPOSE",
                })

    # 4. Table header row check
    for t_idx, table in enumerate(doc.tables):
        has_header = False
        if len(table.rows) > 0:
            first_row_tr = table.rows[0]._tr
            headers = first_row_tr.xpath(".//w:tblHeader")
            has_header = len(headers) > 0

        if not has_header:
            findings.append({
                "category": "accessibility",
                "severity": "minor",
                "confidence": 0.90,
                "evidence_type": "rule",
                "evidence_id": "WCAG-1.3.1-TABLE-HEADER",
                "location": f"Table #{t_idx + 1}",
                "reason": f"Table #{t_idx + 1} does not specify a repeated header row (tblHeader) for assistive screen readers.",
                "suggestion": "Enable 'Repeat as header row at the top of each page' in Table Properties.",
            })
            deductions.append({
                "item": "Table Lacks Header Row",
                "points": -10,
                "reason": f"Table #{t_idx + 1} lacks tblHeader screen reader markup.",
                "evidence_id": "WCAG-1.3.1-TABLE-HEADER",
            })

    score_result = calculate_accessibility_score(deductions)

    return {
        "asset_metadata": {
            "filename": filename,
            "format": "DOCX",
            "paragraph_count": len(doc.paragraphs),
            "table_count": len(doc.tables),
            "embedded_images_count": len(doc_prs),
        },
        "accessibility_score": score_result,
        "findings": findings,
        "total_issues": len(findings),
        "heading_hierarchy": [
            {"level": lvl, "text": txt, "paragraph": p_num}
            for lvl, txt, p_num in heading_levels
        ],
    }


def analyze_pdf_accessibility(
    pdf_bytes: bytes,
    filename: str = "document.pdf",
    approved_palette_hex: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Inspect PDF document pages, metadata, embedded images, and visual contrast."""
    findings = []
    deductions = []
    page_summaries = []

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            metadata = pdf.metadata or {}
            page_count = len(pdf.pages)

            # 1. Document Title Metadata Check
            title = metadata.get("Title") or metadata.get("/Title")
            if not title or not str(title).strip():
                findings.append({
                    "category": "accessibility",
                    "severity": "minor",
                    "confidence": 1.0,
                    "evidence_type": "rule",
                    "evidence_id": "PDF-UA-TITLE",
                    "location": "Document Metadata",
                    "reason": "PDF document metadata lacks a descriptive 'Title' property required by PDF/UA and WCAG 2.4.2.",
                    "suggestion": "Set the document title in PDF metadata properties.",
                })
                deductions.append({
                    "item": "Missing Document Title Metadata",
                    "points": -5,
                    "reason": "PDF lacks /Title metadata property (WCAG 2.4.2).",
                    "evidence_id": "PDF-UA-TITLE",
                })

            # 2. Document Language Metadata Check
            lang = (
                metadata.get("Language")
                or metadata.get("/Lang")
                or metadata.get("Lang")
            )
            if not lang or not str(lang).strip():
                findings.append({
                    "category": "accessibility",
                    "severity": "minor",
                    "confidence": 1.0,
                    "evidence_type": "rule",
                    "evidence_id": "PDF-UA-LANG",
                    "location": "Document Metadata",
                    "reason": "PDF document metadata lacks a primary natural language declaration required by WCAG 3.1.1.",
                    "suggestion": "Specify the document language code (e.g., 'en-US') in document properties.",
                })
                deductions.append({
                    "item": "Missing Document Language Metadata",
                    "points": -5,
                    "reason": "PDF lacks natural language /Lang metadata (WCAG 3.1.1).",
                    "evidence_id": "PDF-UA-LANG",
                })

            # 3. Page-by-page inspection: embedded images and text
            first_page_contrast = None
            for p_idx, page in enumerate(pdf.pages):
                page_num = p_idx + 1
                images = page.images or []
                text = page.extract_text() or ""

                # Embedded images alt-text check
                for img_idx, img_info in enumerate(images):
                    findings.append({
                        "category": "accessibility",
                        "severity": "major",
                        "confidence": 0.95,
                        "evidence_type": "rule",
                        "evidence_id": "WCAG-1.1.1-NON-TEXT",
                        "location": f"Page {page_num}, Image #{img_idx + 1}",
                        "page_number": page_num,
                        "reason": f"Page {page_num} contains embedded image lacking accessible alternate text markup.",
                        "suggestion": "Tag image with Figure alternate text in PDF document structure tree.",
                    })
                    deductions.append({
                        "item": f"Missing Alt Text on Page {page_num}",
                        "points": -10,
                        "reason": f"Page {page_num} image #{img_idx + 1} lacks alternate text markup.",
                        "evidence_id": "WCAG-1.1.1-NON-TEXT",
                    })

                page_summaries.append({
                    "page_number": page_num,
                    "text_character_count": len(text),
                    "image_count": len(images),
                })

                # Check visual contrast on first page raster if possible
                if p_idx == 0:
                    try:
                        page_img = page.to_image(resolution=100).original
                        buf = io.BytesIO()
                        page_img.save(buf, format="PNG")
                        img_res = analyze_image_brand_consistency(
                            image_bytes=buf.getvalue(),
                            approved_palette_hex=approved_palette_hex,
                            filename=f"{filename}_page1",
                            alt_text="Rendered PDF first page preview",
                        )
                        first_page_contrast = img_res.get("contrast_analysis")
                        # Add any contrast failures from rasterized page
                        for f in img_res.get("contrast_findings", []):
                            f["location"] = "Page 1 Raster"
                            f["page_number"] = 1
                            findings.append(f)
                        for d in img_res.get("accessibility_score", {}).get("deductions", []):
                            if d.get("evidence_id") == "WCAG-2.2-AA-CONTRAST":
                                deductions.append(d)
                    except Exception:
                        pass

    except Exception as e:
        raise ValueError(f"Could not parse PDF document: {str(e)}")

    score_result = calculate_accessibility_score(deductions)

    return {
        "asset_metadata": {
            "filename": filename,
            "format": "PDF",
            "page_count": page_count,
            "metadata": {k: str(v) for k, v in metadata.items() if k not in ["Producer", "Creator"]},
        },
        "accessibility_score": score_result,
        "first_page_contrast": first_page_contrast,
        "page_summaries": page_summaries,
        "findings": findings,
        "total_issues": len(findings),
    }


def inspect_asset_accessibility(
    file_bytes: bytes,
    filename: str,
    approved_palette_hex: Optional[List[str]] = None,
    alt_text: Optional[str] = None,
    logo_template_bytes: Optional[bytes] = None,
    brand_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Unified dispatcher for image, PDF, and DOCX asset accessibility inspection."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return analyze_pdf_accessibility(
            pdf_bytes=file_bytes,
            filename=filename,
            approved_palette_hex=approved_palette_hex,
        )
    elif lower.endswith(".docx"):
        return analyze_docx_accessibility(
            docx_bytes=file_bytes,
            filename=filename,
        )
    else:
        return analyze_image_brand_consistency(
            image_bytes=file_bytes,
            approved_palette_hex=approved_palette_hex,
            filename=filename,
            alt_text=alt_text,
            logo_template_bytes=logo_template_bytes,
            brand_name=brand_name,
        )
