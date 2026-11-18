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
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    os.makedirs(settings.upload_dir, exist_ok=True)
    models.Base.metadata.create_all(bind=session.engine)

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
    return {"status": "ok"}

frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
