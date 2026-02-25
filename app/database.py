"""
database.py — SQLAlchemy engine and session setup.

WHAT CHANGED:
  - DATABASE_URL now comes from config.settings, not hardcoded here
  - No other logic changes; this file stays thin (single responsibility)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    # pool_pre_ping checks if DB connection is alive before using it.
    # Prevents "connection closed" errors after DB restarts.
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a DB session per request.
    Guarantees the session is closed even if an exception is raised.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()