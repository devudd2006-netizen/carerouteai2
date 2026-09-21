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


def run_light_migrations():
    """Additive column migrations for dev databases created before new columns
    existed. CREATE TABLE won't alter existing tables, so use direct ALTERs and
    swallow the 'duplicate column' error on fresh databases. Test databases are
    always fresh so this is only exercised by long-lived dev databases."""
    from sqlalchemy import text
    migrations = [
        ("medication_reminders", "source", "VARCHAR(20) DEFAULT 'doctor' NOT NULL"),
        ("medication_reminders", "added_by", "INTEGER"),
        ("medication_reminders", "instructions", "TEXT"),
    ]
    with engine.connect() as conn:
        for table, column, ddl in migrations:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
                conn.commit()
            except Exception:
                # Column already exists (fresh DB or previously migrated)
                pass
