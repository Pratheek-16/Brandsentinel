import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .db import models, session

app = FastAPI(
    title="BrandSentinel API",
    version="1.0.0",
    description="Evidence-grounded, human-controlled pre-publication brand-governance platform",
)

# Explicit CORS origins for development and production (no wildcard '*')
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ensure_schema_columns(engine):
    """Ensure all required columns exist in database tables across SQLite/PostgreSQL."""
    import sqlalchemy as sa
    with engine.connect() as conn:
        try:
            if "sqlite" in str(engine.url):
                res = conn.execute(sa.text("PRAGMA table_info(findings)")).fetchall()
                existing_cols = {row[1] for row in res}
                cols_to_add = [
                    ("status", "VARCHAR DEFAULT 'open'"),
                    ("selected_replacement", "TEXT"),
                    ("decided_by", "INTEGER"),
                    ("decided_at", "DATETIME"),
                    ("dismissal_reason", "TEXT"),
                    ("source", "VARCHAR DEFAULT 'rule'"),
                ]
                for col_name, col_type in cols_to_add:
                    if col_name not in existing_cols:
                        conn.execute(sa.text(f"ALTER TABLE findings ADD COLUMN {col_name} {col_type}"))
                conn.commit()
        except Exception:
            pass

# @app.on_event("startup")
# def startup():
#     os.makedirs(settings.upload_dir, exist_ok=True)
#     models.Base.metadata.create_all(bind=session.engine)
#     ensure_schema_columns(session.engine)
#     if settings.seed_demo:
#         db = session.SessionLocal()
#         try:
#             from scripts.seed_demo import seed_demo_data
#             seed_demo_data(db)
#         finally:
#             db.close()

from .modules.auth.router import router as auth_router
from .modules.kb.router import router as kb_router
from .modules.content.router import router as content_router
from .modules.audit.router import router as audit_router
from .modules.vision.router import router as vision_router
from .modules.insights.router import router as insights_router

app.include_router(auth_router)
app.include_router(kb_router)
app.include_router(content_router)
app.include_router(audit_router)
app.include_router(vision_router)
app.include_router(insights_router)

@app.get("/health")
async def health_check():
    import datetime
    has_gemini_key = bool(settings.gemini_api_key)
    provider_name = settings.llm_model or "mock"
    if has_gemini_key:
        ai_state = "active"
        ai_label = f"AI: {provider_name}"
    elif provider_name == "mock":
        ai_state = "mock"
        ai_label = "AI: mock (test double)"
    else:
        ai_state = "deterministic"
        ai_label = "Deterministic only"

    return {
        "status": "ok",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "environment": settings.environment,
        "ai_provider": {
            "name": provider_name,
            "status": ai_state,
            "label": ai_label,
            "has_key": has_gemini_key,
        }
    }

frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
