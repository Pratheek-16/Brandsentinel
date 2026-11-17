import os
import sys
import datetime
from sqlalchemy.orm import Session

# Allow running from project root or inside backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db import models, session
from app.core.config import settings
from app.core.security import hash_password

DEMO_PASSWORD = "Demo@12345"

def seed_demo_data(db: Session):
    models.Base.metadata.create_all(bind=session.engine)
    pwd_hash = hash_password(DEMO_PASSWORD)

    brand_kits = [
        {
            "name": "NovaFit",
            "slug": "novafit",
            "palette": ["#FF5722", "#212121", "#FFFFFF", "#4CAF50"],
            "rules": [
                {
                    "code": "NF-TONE-01",
                    "category": "tone",
                    "text": "Empowering, energetic, and encouraging; never shaming, preachy, or punitive.",
                    "severity_default": "medium",
                    "examples_good": ["Crush your personal best today!", "Every step counts toward your wellness journey."],
                    "examples_bad": ["Stop being lazy and get off the couch.", "You'll regret eating that calorie bomb."]
                },
                {
                    "code": "NF-CLAIM-01",
                    "category": "claim",
                    "text": "Do not claim guaranteed weight loss or cures for chronic medical conditions.",
                    "severity_default": "high",
                    "examples_good": ["Helps support an active metabolism alongside regular exercise."],
                    "examples_bad": ["Guaranteed to burn 10kg in 10 days!", "Cures metabolic syndrome permanently."]
                },
                {
                    "code": "NF-PRICE-01",
                    "category": "messaging",
                    "text": "Always specify currency (USD) and billing cadence (per month or annually billed).",
                    "severity_default": "medium",
                    "examples_good": ["Only $19.99/month, billed annually.", "$9.99 per month cancel anytime."],
                    "examples_bad": ["Costs just 20 bucks!"]
                },
                {
                    "code": "NF-A11Y-01",
                    "category": "accessibility",
                    "text": "Marketing imagery and digital texts must maintain WCAG 2.2 AA contrast ratio >= 4.5:1 for standard text.",
                    "severity_default": "high",
                    "examples_good": ["Dark slate text on off-white background."],
                    "examples_bad": ["Light grey text on white background."]
                },
                {
                    "code": "NF-TERM-01",
                    "category": "terminology",
                    "text": "Use approved fitness wearable terminology; never describe smart sensors with unscientific slang.",
                    "severity_default": "low",
                    "examples_good": ["NovaBand Pro smart fitness tracker."],
                    "examples_bad": ["Fat-melting electric wristband."]
                }
            ],
            "facts": [
                {"code": "NF-FACT-01", "key": "battery_life_days", "value": "14", "unit": "days", "source": "Hardware Spec v4"},
                {"code": "NF-FACT-02", "key": "waterproof_rating", "value": "5 ATM", "unit": "ATM", "source": "ISO 22810:2010 Certification"},
                {"code": "NF-FACT-03", "key": "app_version", "value": "4.2.0", "unit": "semver", "source": "Release Notes 2026"}
            ],
            "terms": [
                {"preferred": "NovaBand Pro", "banned": ["Nova Watch", "Nova Tracker", "Fat Burner Watch"], "notes": "Official brand device name"},
                {"preferred": "FitPulse Engine", "banned": ["pulse algorithm", "heart track"], "notes": "Proprietary biometric algorithm"}
            ],
            "claims": [
                {
                    "approved_text": "Clinical trials showed 84% of participants increased cardiovascular endurance within 8 weeks.",
                    "evidence_ref": "Study NF-2025-A",
                    "required_disclaimer": "Results may vary based on individual workout intensity and diet.",
                    "valid_to": datetime.datetime(2027, 12, 31)
                }
            ],
            "risk_rules": [
                {"condition_json": {"min_severity": "high"}, "route_to": "reviewer", "description": "High severity findings require Authorised Reviewer sign-off."},
                {"condition_json": {"category": "claim"}, "route_to": "reviewer", "description": "All health claims require Authorised Reviewer validation."}
            ]
        },
        {
            "name": "Lumen Bank",
            "slug": "lumenbank",
            "palette": ["#0A2540", "#00D4B2", "#F8F9FA", "#FFFFFF"],
            "rules": [
                {
                    "code": "LB-REG-01",
                    "category": "claim",
                    "text": "All loan or credit card promotions must display APR with representative example and regulatory warning.",
                    "severity_default": "high",
                    "examples_good": ["Representative 4.85% APR Variable. Credit subject to status."],
                    "examples_bad": ["Get free cash instantly with no interest ever!"]
                },
                {
                    "code": "LB-TONE-01",
                    "category": "tone",
                    "text": "Professional, trustworthy, transparent, and direct; strictly no colloquial slang, speculative hype, or fear-mongering.",
                    "severity_default": "medium",
                    "examples_good": ["We safeguard your capital with institutional-grade risk management."],
                    "examples_bad": ["YOLO your savings into this moonshot asset!", "Banks are crashing, move your money here!"]
                },
                {
                    "code": "LB-TERM-01",
                    "category": "terminology",
                    "text": "Always use regulated banking product terminology; never refer to deposit accounts as crypto lockers or speculative pools.",
                    "severity_default": "high",
                    "examples_good": ["Lumen High-Yield Savings Account", "Lumen Treasury Vault"],
                    "examples_bad": ["Crypto Locker", "Unhackable Money Chest", "Money Doubler"]
                },
                {
                    "code": "LB-A11Y-01",
                    "category": "accessibility",
                    "text": "Account statements and loan disclosures must provide semantic table structures and minimum 4.5:1 contrast.",
                    "severity_default": "high",
                    "examples_good": ["High contrast navy on white with explicit row headers."],
                    "examples_bad": ["Light blue text on white table background."]
                }
            ],
            "facts": [
                {"code": "LB-FACT-01", "key": "fdic_insured_amount", "value": "250,000", "unit": "USD", "source": "FDIC Certificate #94821"},
                {"code": "LB-FACT-02", "key": "fixed_apr_rate", "value": "4.85", "unit": "percent", "source": "Lumen Asset-Liability Committee June 2026"},
                {"code": "LB-FACT-03", "key": "routing_number", "value": "021000021", "unit": "ABA", "source": "Federal Reserve Routing Registry"}
            ],
            "terms": [
                {"preferred": "Lumen High-Yield Savings", "banned": ["Money Doubler", "Magic Saver", "Super Vault"], "notes": "Official regulated deposit account name"},
                {"preferred": "Lumen Secured Card", "banned": ["No-rules credit", "Instant Cash Card"], "notes": "Collateral-backed credit product"}
            ],
            "claims": [
                {
                    "approved_text": "Earn up to 4.85% APY on balances over $5,000 with zero monthly maintenance fees.",
                    "evidence_ref": "Schedule APY-2026-Q3",
                    "required_disclaimer": "Rates variable and subject to change. Member FDIC.",
                    "valid_to": datetime.datetime(2027, 6, 30)
                }
            ],
            "risk_rules": [
                {"condition_json": {"min_severity": "high"}, "route_to": "reviewer", "description": "High severity financial disclosures require Authorised Reviewer sign-off."},
                {"condition_json": {"category": "claim"}, "route_to": "reviewer", "description": "Any claim regarding APY or credit risk mandates compliance sign-off."}
            ]
        },
        {
            "name": "Aster University",
            "slug": "asteruniversity",
            "palette": ["#7B1113", "#D4AF37", "#1C1C1C", "#FFFFFF"],
            "rules": [
                {
                    "code": "AU-TONE-01",
                    "category": "tone",
                    "text": "Inspiring, scholarly, inclusive, and evidence-grounded; avoid hyperbole, sensationalism, or commercial marketing tropes.",
                    "severity_default": "medium",
                    "examples_good": ["Fostering discovery through rigorous interdisciplinary inquiry."],
                    "examples_bad": ["The most lit campus with the sickest dorms in America!"]
                },
                {
                    "code": "AU-FACT-01",
                    "category": "messaging",
                    "text": "Only quote official registrar census statistics for acceptance rates, enrollment sizes, and endowment values.",
                    "severity_default": "high",
                    "examples_good": ["Aster welcomed an incoming class selected from an applicant pool with a 12.4% acceptance rate."],
                    "examples_bad": ["Virtually impossible to get in, we reject everyone!"]
                },
                {
                    "code": "AU-TERM-01",
                    "category": "terminology",
                    "text": "Use inclusive institutional terminology; refer to new students as 'first-year undergraduates' rather than 'freshmen'.",
                    "severity_default": "low",
                    "examples_good": ["First-year undergraduate orientation program."],
                    "examples_bad": ["Freshman dorm mixer."]
                },
                {
                    "code": "AU-A11Y-01",
                    "category": "accessibility",
                    "text": "All academic course syllabi and course portal documents must comply with Section 508 and WCAG 2.2 AA.",
                    "severity_default": "high",
                    "examples_good": ["Accessible tagged PDF with alt tags on diagrams."],
                    "examples_bad": ["Scanned photocopies of book pages without OCR."]
                }
            ],
            "facts": [
                {"code": "AU-FACT-01", "key": "acceptance_rate", "value": "12.4", "unit": "percent", "source": "Office of Admissions Census 2026"},
                {"code": "AU-FACT-02", "key": "student_faculty_ratio", "value": "7:1", "unit": "ratio", "source": "Provost Academic Report 2026"},
                {"code": "AU-FACT-03", "key": "endowment_value", "value": "3.2", "unit": "billion_usd", "source": "Treasury Annual Audit 2025"}
            ],
            "terms": [
                {"preferred": "first-year undergraduate", "banned": ["freshman", "frosh"], "notes": "Inclusive academic nomenclature"},
                {"preferred": "Aster Scholar Initiative", "banned": ["Smart Kid Fund", "Genius Grant"], "notes": "Merit-based financial aid program"}
            ],
            "claims": [
                {
                    "approved_text": "Ranked #8 in Undergraduate Research Opportunities nationwide by Academic Review 2026.",
                    "evidence_ref": "Registrar Survey Doc AR-2026",
                    "required_disclaimer": "Source: Academic Review 2026 Survey of Higher Education.",
                    "valid_to": datetime.datetime(2027, 8, 31)
                }
            ],
            "risk_rules": [
                {"condition_json": {"min_severity": "high"}, "route_to": "reviewer", "description": "High risk university communications require Authorised Reviewer sign-off."}
            ]
        }
    ]

    for kit in brand_kits:
        ws = db.query(models.Workspace).filter(models.Workspace.name == kit["name"]).first()
        if not ws:
            ws = models.Workspace(name=kit["name"])
            db.add(ws)
            db.flush()

        # Seed 5 accounts per brand
        roles = [
            ("admin", "admin"),
            ("manager", "manager"),
            ("reviewer", "reviewer"),
            ("creator1", "creator"),
            ("creator2", "creator"),
        ]
        created_users = {}
        for prefix, role in roles:
            email = f"{prefix}@{kit['slug']}.local"
            user = db.query(models.User).filter(models.User.email == email).first()
            if not user:
                user = models.User(
                    workspace_id=ws.id,
                    email=email,
                    name=f"{kit['name']} {prefix.title()}",
                    role=role,
                    password_hash=pwd_hash,
                    active=True
                )
                db.add(user)
                db.flush()
            created_users[role] = user

        # Active KB Version
        kb_ver = db.query(models.KBVersion).filter(
            models.KBVersion.workspace_id == ws.id,
            models.KBVersion.is_active == True
        ).first()

        if not kb_ver:
            kb_ver = models.KBVersion(
                workspace_id=ws.id,
                label=f"{kit['name']} Approved Guidelines v1.0",
                created_by=created_users["admin"].id,
                is_active=True
            )
            db.add(kb_ver)
            db.flush()

        # Add Rules
        for r_spec in kit["rules"]:
            existing = db.query(models.Rule).filter(
                models.Rule.kb_version_id == kb_ver.id,
                models.Rule.code == r_spec["code"]
            ).first()
            if not existing:
                db.add(models.Rule(
                    kb_version_id=kb_ver.id,
                    code=r_spec["code"],
                    category=r_spec["category"],
                    text=r_spec["text"],
                    severity_default=r_spec["severity_default"],
                    examples_good=r_spec.get("examples_good"),
                    examples_bad=r_spec.get("examples_bad"),
                    source_doc=f"{kit['name']} Brand Guide 2026"
                ))

        # Add Facts
        for f_spec in kit["facts"]:
            existing = db.query(models.Fact).filter(
                models.Fact.kb_version_id == kb_ver.id,
                models.Fact.code == f_spec["code"]
            ).first()
            if not existing:
                db.add(models.Fact(
                    kb_version_id=kb_ver.id,
                    code=f_spec["code"],
                    key=f_spec["key"],
                    value=f_spec["value"],
                    unit=f_spec.get("unit"),
                    source=f_spec.get("source"),
                    owner="Brand Operations"
                ))

        # Add Terms
        for t_spec in kit["terms"]:
            existing = db.query(models.Term).filter(
                models.Term.kb_version_id == kb_ver.id,
                models.Term.preferred == t_spec["preferred"]
            ).first()
            if not existing:
                db.add(models.Term(
                    kb_version_id=kb_ver.id,
                    preferred=t_spec["preferred"],
                    banned=t_spec.get("banned"),
                    notes=t_spec.get("notes")
                ))

        # Add Claims
        for c_spec in kit["claims"]:
            existing = db.query(models.Claim).filter(
                models.Claim.kb_version_id == kb_ver.id,
                models.Claim.approved_text == c_spec["approved_text"]
            ).first()
            if not existing:
                db.add(models.Claim(
                    kb_version_id=kb_ver.id,
                    approved_text=c_spec["approved_text"],
                    evidence_ref=c_spec.get("evidence_ref"),
                    required_disclaimer=c_spec.get("required_disclaimer"),
                    valid_to=c_spec.get("valid_to")
                ))

        # Add Palette Asset
        existing_asset = db.query(models.Asset).filter(
            models.Asset.kb_version_id == kb_ver.id,
            models.Asset.type == "palette"
        ).first()
        if not existing_asset:
            db.add(models.Asset(
                kb_version_id=kb_ver.id,
                type="palette",
                spec_json={"colors": kit["palette"]},
                file_ref=None
            ))

        # Add Risk Rules
        for rr_spec in kit.get("risk_rules", []):
            existing_rr = db.query(models.RiskRule).filter(
                models.RiskRule.workspace_id == ws.id,
                models.RiskRule.description == rr_spec.get("description")
            ).first()
            if not existing_rr:
                db.add(models.RiskRule(
                    workspace_id=ws.id,
                    condition_json=rr_spec["condition_json"],
                    route_to=rr_spec["route_to"],
                    description=rr_spec.get("description")
                ))

    db.commit()

if __name__ == "__main__":
    db = session.SessionLocal()
    try:
        seed_demo_data(db)
        print("Demo data seeded successfully for NovaFit, Lumen Bank, and Aster University.")
    finally:
        db.close()
