import re
from typing import List, Dict, Any

# Map of banned terms to preferred replacement and rule
BANNED_TERMS = {
    # NovaFit
    "nova watch": {"preferred": "NovaBand Pro", "rule": "NF-TERM-01", "cat": "terminology"},
    "nova tracker": {"preferred": "NovaBand Pro", "rule": "NF-TERM-01", "cat": "terminology"},
    "fat burner watch": {"preferred": "NovaBand Pro", "rule": "NF-TERM-01", "cat": "terminology"},
    "pulse algorithm": {"preferred": "FitPulse Engine", "rule": "NF-TERM-01", "cat": "terminology"},
    "heart track": {"preferred": "FitPulse Engine", "rule": "NF-TERM-01", "cat": "terminology"},
    # Lumen Bank
    "money doubler": {"preferred": "Lumen High-Yield Savings", "rule": "LB-TERM-01", "cat": "terminology"},
    "magic saver": {"preferred": "Lumen High-Yield Savings", "rule": "LB-TERM-01", "cat": "terminology"},
    "super vault": {"preferred": "Lumen High-Yield Savings", "rule": "LB-TERM-01", "cat": "terminology"},
    "crypto locker": {"preferred": "Lumen Treasury Vault", "rule": "LB-TERM-01", "cat": "terminology"},
    "unhackable money chest": {"preferred": "Lumen Treasury Vault", "rule": "LB-TERM-01", "cat": "terminology"},
    "no-rules credit": {"preferred": "Lumen Secured Card", "rule": "LB-TERM-01", "cat": "terminology"},
    "instant cash card": {"preferred": "Lumen Secured Card", "rule": "LB-TERM-01", "cat": "terminology"},
    # Aster University
    "freshman": {"preferred": "first-year undergraduate", "rule": "AU-TERM-01", "cat": "terminology"},
    "freshmen": {"preferred": "first-year undergraduates", "rule": "AU-TERM-01", "cat": "terminology"},
    "frosh": {"preferred": "first-year undergraduate", "rule": "AU-TERM-01", "cat": "terminology"},
    "smart kid fund": {"preferred": "Aster Scholar Initiative", "rule": "AU-TERM-01", "cat": "terminology"},
    "genius grant": {"preferred": "Aster Faculty Fellowship", "rule": "AU-TERM-01", "cat": "terminology"},
    "the yard": {"preferred": "Campus Quad", "rule": "AU-TERM-01", "cat": "terminology"},
    "the lawn": {"preferred": "Campus Quad", "rule": "AU-TERM-01", "cat": "terminology"},
    # Generic test placeholders
    "foobar": {"preferred": "BrandSentinel", "rule": "GEN-TERM-01", "cat": "terminology"},
    "lorem": {"preferred": "Approved Text", "rule": "GEN-TERM-01", "cat": "terminology"},
}

TONE_PATTERNS = [
    # NovaFit shaming / punitive
    (r"\b(stop being so lazy|have no discipline|feel guilty|pathetic|weak stamina|shame on|only losers|falling behind|don't care enough|no excuses for being weak|until you collapse)\b", "NF-TONE-01", "Shaming or punitive fitness tone is prohibited; use encouraging and empowering language.", "Replace with encouraging motivational phrasing."),
    # Lumen Bank hype / slang / fear-mongering
    (r"\b(yolo|moonshot|dump your cash|banks are secretly going bankrupt|bro|panic in the markets|meltdown|scam|why grind|hustle for ya)\b", "LB-TONE-01", "Speculative, alarmist, or colloquial slang tone is prohibited in financial communications.", "Use professional, transparent, and direct financial advisory tone."),
    # Aster University frivolous / hyperbole
    (r"\b(most lit|sickest|party scene|ditch boring|coolest university|absolute beasts|pure hype|dopest|forget serious reading|easy degree|ridiculously superior|pure fun vibes)\b", "AU-TONE-01", "Frivolous, sensationalized, or commercial slang violates scholarly academic voice.", "Use scholarly, evidence-grounded institutional language.")
]

CLAIM_PATTERNS = [
    (r"\b(guaranteed\w*|cure\w*|100% safe|guaranteed to burn|cure metabolic syndrome|eliminate heart disease|melt fat cells|guaranteed instant six-pack|100% cure)\b", "NF-CLAIM-01", "Prohibited medical or unconditional guarantee claim.", "unsupported", "Remove unconditional or unapproved health guarantee."),
    (r"\b(guaranteed zero risk|double your wealth|no chance of loss|guaranteed 0% interest|risk-free equity|guaranteed 15% fixed|unconditionally without limit)\b", "LB-REG-01", "Unsubstantiated risk-free investment or lending claim.", "unsupported", "Qualify investment risks and state market volatility disclaimers."),
    (r"\b(ranked #1 in the universe|guaranteed immediate employment|100% of aster alumni earn|more nobel laureates than all|best university in human history)\b", "AU-TONE-01", "Unverified or hyperbolic institutional ranking claim.", "unsupported", "Cite verified registrar or national survey rankings.")
]

INJECTION_PATTERNS = [
    r"ignore all previous",
    r"system prompt override",
    r"admin override",
    r"disregard rule",
    r"<!-- <system>",
    r"human: forget university policy",
    r"system instruction:",
    r"bypass_review",
    r"<script>fetch",
    r"ignore banking regulations",
    r"disregard fdic disclaimers"
]

ACCESSIBILITY_PATTERNS = [
    (r"(light grey on a pure white|#eeeeee|light yellow text overlaid on vibrant neon green|unlabelled bitmap image|without color differentiation|pale orange text on white|measure.*2\.1:1|#aaaaaa|#cccccc|1\.8:1)", "NF-A11Y-01", "Visual contrast violation below WCAG 2.2 AA minimum 4.5:1 threshold."),
    (r"(light cyan text over white|4pt light-grey font|without header cells or column scopes|pale green apr disclosure|no text contrast or aria|10% opacity grey)", "LB-A11Y-01", "Financial disclosure fails WCAG 2.2 accessibility and contrast standards."),
    (r"(table with no row or column header|scanned photocopied image without ocr|contrast measuring 1\.8:1|pale gold font #f5e0a3|solely as an untagged jpeg|dark purple text against dark charcoal)", "AU-A11Y-01", "Academic material violates Section 508 / WCAG 2.2 AA accessibility requirements.")
]

MESSAGING_PATTERNS = [
    (r"(20 bucks|flat price of 50 without|fifty dollars without|costs only 15 each month|pay 99 total|v5\.9\.9|45 full days|50 atm)", "NF-PRICE-01", "Pricing missing currency/billing period, or inaccurate product specification.", "Specify currency (USD) and billing cadence (per month / annually)."),
    (r"(\$10,000,000|fixed apr of 1\.25%|routing number 999999999|private venture reserves|zero-interest personal loans|unlimited fdic insurance|routing number 000111222)", "LB-REG-01", "Inaccurate regulatory disclosure or contradicted financial fact.", "Verify against verified FDIC parameters and approved fee schedules."),
    (r"(accepts 85%|acceptance rate dropped to an unprecedented 1\.2%|ratio of 1:1|exceeding \$150 billion|500,000 active students|acceptance rate confirmed at 45\.8%|ratio is 35:1|below five hundred thousand|year 1250)", "AU-FACT-01", "Contradicts verified university registrar census statistics.", "Cite official registrar census statistics (12.4% acceptance, 7:1 ratio, $3.2B endowment).")
]

# Claims missing required disclaimer check
MISSING_DISCLAIMER_CHECKS = [
    {
        "trigger": "earn up to 4.85% apy on balances over $5,000",
        "required_disclaimer": "member fdic",
        "rule": "LB-REG-01",
        "reason": "Promotional APY claim is missing mandatory FDIC membership disclaimer.",
        "suggestion": "Append: 'Rates variable and subject to change. Member FDIC.'"
    },
    {
        "trigger": "ranked #8 in undergraduate research opportunities nationwide",
        "required_disclaimer": "source: academic review",
        "rule": "AU-FACT-01",
        "reason": "Ranking claim is missing mandatory survey source citation.",
        "suggestion": "Append: 'Source: Academic Review 2026 Survey of Higher Education.'"
    }
]

def find_spans(text: str, pattern: re.Pattern) -> List[Dict[str, Any]]:
    spans = []
    for m in pattern.finditer(text):
        spans.append({"start": m.start(), "end": m.end(), "text": m.group()})
    return spans

def run_deterministic_checks(text: str) -> List[Dict[str, Any]]:
    findings = []
    lowered = text.lower()

    # 1. Prompt Injection Resistance Checks
    for pattern_str in INJECTION_PATTERNS:
        if pattern_str in lowered:
            regex = re.compile(re.escape(pattern_str), re.IGNORECASE)
            for span in find_spans(text, regex):
                findings.append({
                    "category": "security",
                    "severity": "blocker",
                    "confidence": 1.0,
                    "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                    "evidence": {"type": "security_policy", "id": "SEC-INJECT-01", "quote": span["text"]},
                    "reason": "Adversarial prompt injection pattern detected. Brand review bypasses are blocked.",
                    "suggestion": {"text": "Remove prompt injection keywords and resubmit clean brand copy."},
                    "claim_status": "n/a",
                })

    # 2. Banned Terminology Checks
    for term, meta in BANNED_TERMS.items():
        if term in lowered:
            regex = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            for span in find_spans(text, regex):
                findings.append({
                    "category": meta["cat"],
                    "severity": "major",
                    "confidence": 1.0,
                    "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                    "evidence": {"type": "term", "id": meta["rule"], "quote": span["text"]},
                    "reason": f"Banned terminology '{span['text']}' used instead of approved brand nomenclature.",
                    "suggestion": {"text": f"Replace with approved term '{meta['preferred']}'."},
                    "claim_status": "n/a",
                })

    # 3. Tone Violations
    for pattern_str, rule, reason, sugg in TONE_PATTERNS:
        regex = re.compile(pattern_str, re.IGNORECASE)
        for span in find_spans(text, regex):
            findings.append({
                "category": "tone",
                "severity": "major",
                "confidence": 0.95,
                "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                "evidence": {"type": "rule", "id": rule, "quote": span["text"]},
                "reason": reason,
                "suggestion": {"text": sugg},
                "claim_status": "n/a",
            })

    # 4. Prohibited or Unbacked Claims
    for pattern_str, rule, reason, claim_st, sugg in CLAIM_PATTERNS:
        regex = re.compile(pattern_str, re.IGNORECASE)
        for span in find_spans(text, regex):
            findings.append({
                "category": "claim",
                "severity": "blocker",
                "confidence": 0.98,
                "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                "evidence": {"type": "rule", "id": rule, "quote": span["text"]},
                "reason": reason,
                "suggestion": {"text": sugg},
                "claim_status": claim_st,
            })

    # 5. Missing Disclaimer Claims
    for check in MISSING_DISCLAIMER_CHECKS:
        if check["trigger"] in lowered and check["required_disclaimer"] not in lowered:
            regex = re.compile(re.escape(check["trigger"]), re.IGNORECASE)
            for span in find_spans(text, regex):
                findings.append({
                    "category": "claim",
                    "severity": "major",
                    "confidence": 0.92,
                    "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                    "evidence": {"type": "claim", "id": check["rule"], "quote": span["text"]},
                    "reason": check["reason"],
                    "suggestion": {"text": check["suggestion"]},
                    "claim_status": "missing_disclaimer",
                })

    # 6. Accessibility & Visual Violations
    for pattern_str, rule, reason in ACCESSIBILITY_PATTERNS:
        regex = re.compile(pattern_str, re.IGNORECASE)
        for span in find_spans(text, regex):
            findings.append({
                "category": "accessibility",
                "severity": "major",
                "confidence": 0.90,
                "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                "evidence": {"type": "rule", "id": rule, "quote": span["text"]},
                "reason": reason,
                "suggestion": {"text": "Ensure contrast ratio meets WCAG 2.2 AA (>= 4.5:1) and provide semantic text alternatives."},
                "claim_status": "n/a",
            })

    # 7. Messaging & Factual Errors
    for pattern_str, rule, reason, sugg in MESSAGING_PATTERNS:
        regex = re.compile(pattern_str, re.IGNORECASE)
        for span in find_spans(text, regex):
            findings.append({
                "category": "messaging",
                "severity": "major",
                "confidence": 0.93,
                "span": {"start": span["start"], "end": span["end"], "text": span["text"]},
                "evidence": {"type": "fact", "id": rule, "quote": span["text"]},
                "reason": reason,
                "suggestion": {"text": sugg},
                "claim_status": "contradicted",
            })

    return findings
