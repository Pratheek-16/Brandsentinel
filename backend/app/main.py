from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .db import models, session

app = FastAPI(title="BrandSentinel API", version="0.1.0")

# CORS (frontend runs on localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup for SQLite fallback
@app.on_event("startup")
async def startup():
    models.Base.metadata.create_all(bind=session.engine)

from .modules.auth.router import router as auth_router
from .modules.kb.router import router as kb_router
from .modules.content.router import router as content_router

app.include_router(auth_router)
app.include_router(kb_router)
app.include_router(content_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
