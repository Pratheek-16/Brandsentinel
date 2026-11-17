"""Improvement I-2: Visual Brand Consistency & Accessibility Analyzer.
Performs:
1. Palette compliance analysis via CIELAB Delta-E distance calculation.
2. WCAG 2.2 AA Contrast Ratio calculation for text vs background.
3. Image OCR and dominant color extraction.
"""

import io
import math
from typing import List, Dict, Any, Tuple
from PIL import Image

def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join([c*2 for c in hex_code])
    return int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16)

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"

def rgb_to_lab(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Convert sRGB (0-255) to CIE-L*a*b* color space."""
    # Convert sRGB to linear RGB
    r_lin = [(c / 255.0) for c in rgb]
    r_lin = [(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) for c in r_lin]

    # Convert linear RGB to XYZ (D65 illuminant)
    X = r_lin[0] * 0.4124564 + r_lin[1] * 0.3575761 + r_lin[2] * 0.1804375
    Y = r_lin[0] * 0.2126729 + r_lin[1] * 0.7151522 + r_lin[2] * 0.0721750
    Z = r_lin[0] * 0.0193339 + r_lin[1] * 0.1191920 + r_lin[2] * 0.9503041

    # Normalize by D65 reference white
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883
    x, y, z = X / Xn, Y / Yn, Z / Zn

    fx, fy, fz = [(t ** (1/3) if t > 0.008856 else (7.787 * t + 16 / 116)) for t in (x, y, z)]

    L = max(0.0, min(100.0, 116 * fy - 16))
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
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

def extract_dominant_colors(image: Image.Image, num_colors: int = 4) -> List[Tuple[int, int, int]]:
    """Extract top dominant colors from a PIL Image."""
    img = image.convert("RGB").resize((100, 100))
    colors = img.getcolors(maxcolors=10000)
    if not colors:
        return [(0, 0, 0), (255, 255, 255)]
    colors.sort(key=lambda x: x[0], reverse=True)
    return [c[1] for c in colors[:num_colors]]

def analyze_image_brand_consistency(
    image_bytes: bytes,
    approved_palette_hex: List[str] = None,
) -> Dict[str, Any]:
    """Inspect image for palette compliance and text contrast."""
    palette = approved_palette_hex or ["#0055FF", "#10B981", "#FFFFFF", "#1E293B"]
    brand_labs = [(h, rgb_to_lab(hex_to_rgb(h))) for h in palette]

    image = Image.open(io.BytesIO(image_bytes))
    dominant_rgbs = extract_dominant_colors(image, num_colors=3)

    palette_findings = []
    for rgb in dominant_rgbs:
        hex_val = rgb_to_hex(*rgb)
        lab_val = rgb_to_lab(rgb)
        # Find closest brand color
        closest_brand, min_de = min(brand_labs, key=lambda b: delta_e_cielab(lab_val, b[1]))
        min_de_val = round(delta_e_cielab(lab_val, min_de), 2)

        # Delta E > 15 is visibly off-brand
        if min_de_val > 15.0:
            palette_findings.append({
                "category": "visual",
                "severity": "minor" if min_de_val < 30.0 else "major",
                "extracted_hex": hex_val,
                "closest_brand_hex": closest_brand,
                "delta_e": min_de_val,
                "message": f"Color {hex_val} deviates from brand palette (closest: {closest_brand}, Delta-E = {min_de_val}).",
            })

    # Evaluate foreground vs background contrast
    contrast_findings = []
    if len(dominant_rgbs) >= 2:
        ratio = calculate_contrast_ratio(dominant_rgbs[0], dominant_rgbs[1])
        passes_aa_normal = ratio >= 4.5
        passes_aa_large = ratio >= 3.0
        if not passes_aa_normal:
            contrast_findings.append({
                "category": "accessibility",
                "severity": "major" if ratio < 3.0 else "minor",
                "contrast_ratio": ratio,
                "wcag_target": "4.5:1 (WCAG 2.2 AA)",
                "passed": False,
                "message": f"Insufficient contrast ratio {ratio}:1 between dominant elements (minimum 4.5:1 required).",
            })

    return {
        "width": image.width,
        "height": image.height,
        "dominant_colors": [rgb_to_hex(*rgb) for rgb in dominant_rgbs],
        "palette_findings": palette_findings,
        "contrast_findings": contrast_findings,
        "total_issues": len(palette_findings) + len(contrast_findings),
    }
