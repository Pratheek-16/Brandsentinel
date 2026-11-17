"""SQLAlchemy session handling for BrandSentinel.

Creates an engine based on the DATABASE_URL setting and provides a scoped session
factory. The same session is used throughout the app via dependency injection.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from ..core.config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
