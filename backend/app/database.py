"""
database.py
-----------
Sets up SQLAlchemy engine, session, and base model for the application.
Supports both SQLite (default for dev) and PostgreSQL (production).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ─── Database URL ────────────────────────────────────────────────────────────
# Use environment variable in production; fall back to SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./campus_guide.db"           # SQLite for local dev
    # "postgresql://user:password@localhost/campus_guide"  # PostgreSQL
)

# ─── Engine ──────────────────────────────────────────────────────────────────
# connect_args only needed for SQLite (multi-thread safety)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ─── Session ─────────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ─── Base Model ──────────────────────────────────────────────────────────────
Base = declarative_base()


# ─── Dependency ──────────────────────────────────────────────────────────────
def get_db():
    """FastAPI dependency: yields a DB session and closes it after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
