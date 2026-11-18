"""SQLAlchemy session handling for BrandSentinel.

Creates an engine based on the DATABASE_URL setting and provides a scoped session
factory. The same session is used throughout the app via dependency injection.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from urllib.parse import quote

from ..core.config import settings

def normalize_database_url(database_url: str) -> str:
    """Normalize PostgreSQL URLs when an unencoded @ appears in the password."""
    if "://" not in database_url or database_url.lstrip().startswith("sqlite"):
        return database_url

    scheme, remainder = database_url.split("://", 1)
    if scheme not in ("postgresql", "postgresql+psycopg2", "postgres"):
        return database_url

    if "@" not in remainder:
        return database_url

    # Supabase passwords may contain '@'; use the final @ as the host separator.
    authority, sep, rest = remainder.rpartition("@")
    if ":" not in authority:
        return database_url

    username, password = authority.split(":", 1)
    if "%" in password:
        return database_url
    normalized_authority = f"{username}:{quote(password, safe='')}@{rest}"
    return f"{scheme}://{normalized_authority}"


database_url = normalize_database_url(settings.database_url)
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    pool_pre_ping=True,
)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
