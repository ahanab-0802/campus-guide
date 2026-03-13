"""
models/user.py
--------------
SQLAlchemy ORM models.
Defines tables: users, resume_metadata, pyq_questions
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    """Stores user account information."""
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    email           = Column(String(150), unique=True, index=True, nullable=False)
    phone           = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(String(10), default="user")          # admin / user
    college         = Column(String(200), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("ResumeMetadata", back_populates="owner")


class ResumeMetadata(Base):
    """Stores metadata about each resume analyzed or built."""
    __tablename__ = "resume_metadata"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"))
    filename       = Column(String(255), nullable=True)
    ats_score      = Column(Float, nullable=True)
    shortlisted    = Column(Boolean, nullable=True)
    job_role       = Column(String(100), nullable=True)
    salary         = Column(String(50), nullable=True)
    company_type   = Column(String(100), nullable=True)
    uploaded_at    = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="resumes")


class PYQQuestion(Base):
    """Stores previous year questions for placement prep."""
    __tablename__ = "pyq_questions"

    id          = Column(Integer, primary_key=True, index=True)
    subject     = Column(String(50), index=True)   # aptitude, dsa, oop, os, dbms, cn
    question    = Column(Text, nullable=False)
    options     = Column(Text, nullable=True)       # JSON string of options list
    answer      = Column(String(500), nullable=True)
    difficulty  = Column(String(20), default="medium")  # easy / medium / hard
    explanation = Column(Text, nullable=True)
