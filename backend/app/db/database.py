"""
Database connection and session management.
Uses SQLAlchemy with PostgreSQL (or SQLite fallback for local dev).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import get_settings

settings = get_settings()

DATABASE_URL = settings.DATABASE_URL

if DATABASE_URL.startswith("postgres"):
    try:
        import psycopg2  # noqa: F401
        engine = create_engine(DATABASE_URL, echo=settings.DEBUG)
    except ImportError:
        # PostgreSQL driver not installed — fall back to a local SQLite file
        # so the app still runs for local development/evaluation.
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "careroute.db")
        DATABASE_URL = f"sqlite:///{db_path}"
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=settings.DEBUG,
        )
else:
    # Explicit non-PostgreSQL URL (e.g. sqlite:// in tests) — honor it as-is.
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
        echo=settings.DEBUG,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables."""
    from app.models import user, patient, health, document  # noqa
    from app.models import facility, community, emergency  # noqa
    Base.metadata.create_all(bind=engine)
