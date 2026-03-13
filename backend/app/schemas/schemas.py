"""
schemas/schemas.py
------------------
Pydantic models used for request validation and response serialization.
Keeps API contracts clean and auto-documented in Swagger UI.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    role: Optional[str] = "user"
    college: Optional[str] = None
    graduation_year: Optional[int] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("admin", "user"):
            raise ValueError("role must be 'admin' or 'user'")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    role: str
    college: Optional[str]
    graduation_year: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    college: Optional[str] = None
    graduation_year: Optional[int] = None
    password: Optional[str] = None


# ─── Resume Builder Schemas ───────────────────────────────────────────────────

class Education(BaseModel):
    degree: str
    institution: str
    year: str
    cgpa: Optional[str] = None


class Project(BaseModel):
    title: str
    description: str
    technologies: str


class Internship(BaseModel):
    company: str
    role: str
    duration: str
    description: str


class ResumeBuildRequest(BaseModel):
    name: str
    email: str
    phone: str
    linkedin: Optional[str] = None
    github: Optional[str] = None
    education: List[Education]
    skills: List[str]
    projects: List[Project]
    internships: Optional[List[Internship]] = []
    achievements: Optional[List[str]] = []
    certifications: Optional[List[str]] = []


# ─── Resume Analysis Schemas ──────────────────────────────────────────────────

class ATSResponse(BaseModel):
    ats_score: float
    breakdown: dict


class ShortlistResponse(BaseModel):
    shortlisted: bool
    confidence: float


class JobPredictionResponse(BaseModel):
    job_role: str
    salary_prediction: str
    company_type: str


class ImprovementResponse(BaseModel):
    missing_keywords: List[str]
    skill_gaps: List[str]
    suggestions: List[str]


class FullAnalysisResponse(BaseModel):
    ats_score: float
    shortlisted: bool
    confidence: float
    job_role: Optional[str] = None
    salary_prediction: Optional[str] = None
    company_type: Optional[str] = None
    suggestions: Optional[List[str]] = None
    missing_keywords: Optional[List[str]] = None


# ─── PYQ Schemas ─────────────────────────────────────────────────────────────

class PYQOut(BaseModel):
    id: int
    subject: str
    question: str
    options: Optional[str]
    answer: Optional[str]
    difficulty: str
    explanation: Optional[str]

    class Config:
        from_attributes = True
