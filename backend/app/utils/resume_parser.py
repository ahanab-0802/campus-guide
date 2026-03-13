"""
utils/resume_parser.py
-----------------------
Parses uploaded PDF resumes and extracts structured features.
Uses PyPDF2 for text extraction and regex/spaCy for NLP parsing.
"""

import re
import io
from typing import Dict, List

# PDF text extraction
try:
    import pypdf
except ImportError:
    pypdf = None


# ─── Keyword Banks ────────────────────────────────────────────────────────────
TECH_SKILLS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "react", "node.js",
    "fastapi", "django", "flask", "spring boot", "sql", "mysql", "postgresql",
    "mongodb", "redis", "docker", "kubernetes", "aws", "azure", "gcp",
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
    "pandas", "numpy", "nlp", "computer vision", "git", "linux", "rest api",
    "graphql", "spark", "hadoop", "kafka", "airflow", "tableau", "power bi"
]

SOFT_SKILLS = [
    "leadership", "teamwork", "communication", "problem solving",
    "analytical", "creative", "adaptable", "time management"
]

ACTION_VERBS = [
    "developed", "designed", "built", "implemented", "optimized",
    "led", "managed", "created", "analyzed", "improved", "deployed",
    "architected", "engineered", "automated", "reduced", "increased"
]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract raw text from a PDF file.
    
    Args:
        file_bytes: Raw bytes of the uploaded PDF
    
    Returns:
        Concatenated text from all pages
    """
    if pypdf is None:
        return ""
    
    text = ""
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"[ResumeParser] PDF extraction error: {e}")
    
    return text


def extract_email(text: str) -> str:
    """Extract the first email address found in text."""
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    """Extract phone number using common Indian/international formats."""
    match = re.search(r'(\+91[-\s]?)?[6-9]\d{9}|(\+\d{1,3}[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}', text)
    return match.group(0) if match else ""


def extract_skills(text: str) -> List[str]:
    """Find all tech skills mentioned in the resume text."""
    text_lower = text.lower()
    found = [skill for skill in TECH_SKILLS if skill in text_lower]
    return list(set(found))


def extract_section(text: str, section_name: str) -> str:
    """
    Extract a named section from resume text using regex.
    
    Args:
        text: Full resume text
        section_name: Section header keyword (e.g. "experience", "projects")
    
    Returns:
        Extracted section text (up to 500 chars)
    """
    pattern = rf'(?i){section_name}.*?(?=\n[A-Z]{{2,}}|\Z)'
    match = re.search(pattern, text, re.DOTALL)
    return match.group(0)[:500] if match else ""


def count_action_verbs(text: str) -> int:
    """Count how many strong action verbs appear in the resume."""
    text_lower = text.lower()
    return sum(1 for verb in ACTION_VERBS if verb in text_lower)


def has_quantified_achievements(text: str) -> bool:
    """Check if the resume contains quantified metrics (numbers with % or x)."""
    return bool(re.search(r'\d+\s*(%|x|lpa|lakh|crore|users|projects|ms|hrs)', text.lower()))


def extract_years_of_experience(text: str) -> float:
    """Estimate years of experience from internship/work sections."""
    matches = re.findall(r'(\d+)\s*(year|yr|month)', text.lower())
    total_months = 0
    for val, unit in matches:
        if "year" in unit or "yr" in unit:
            total_months += int(val) * 12
        else:
            total_months += int(val)
    return round(total_months / 12, 1)


def parse_resume(file_bytes: bytes) -> Dict:
    """
    Master function: Extract all features from a resume PDF.
    
    Returns:
        Dictionary of parsed features ready for ML model input
    """
    text = extract_text_from_pdf(file_bytes)
    
    skills        = extract_skills(text)
    action_count  = count_action_verbs(text)
    quantified    = has_quantified_achievements(text)
    experience    = extract_years_of_experience(text)
    
    # Heuristic section detectors
    has_projects      = bool(re.search(r'project', text, re.IGNORECASE))
    has_internship    = bool(re.search(r'intern', text, re.IGNORECASE))
    has_education     = bool(re.search(r'b\.?tech|b\.?e|bsc|mca|mba|bachelor|master', text, re.IGNORECASE))
    has_certifications = bool(re.search(r'certif|aws|gcp|azure|coursera|udemy', text, re.IGNORECASE))
    has_linkedin      = bool(re.search(r'linkedin', text, re.IGNORECASE))
    has_github        = bool(re.search(r'github', text, re.IGNORECASE))
    
    return {
        "raw_text":          text,
        "email":             extract_email(text),
        "phone":             extract_phone(text),
        "skills":            skills,
        "skill_count":       len(skills),
        "action_verb_count": action_count,
        "quantified":        quantified,
        "experience_years":  experience,
        "has_projects":      has_projects,
        "has_internship":    has_internship,
        "has_education":     has_education,
        "has_certifications": has_certifications,
        "has_linkedin":      has_linkedin,
        "has_github":        has_github,
        "word_count":        len(text.split()),
    }
