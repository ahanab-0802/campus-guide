"""
services/ml_predictor.py
-------------------------
Loads trained ML models and provides prediction functions.
Models: XGBoost (shortlist), SVM (job role), Random Forest (salary + company).
Falls back to rule-based predictions if model files are missing.
"""

import os
import numpy as np
import joblib
from typing import Dict, List, Tuple

# ─── Model Paths ─────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR    = os.path.join(BASE_DIR, "../../ml_models")

SHORTLIST_MODEL_PATH  = os.path.join(MODEL_DIR, "shortlist_model.joblib")
JOBROLE_MODEL_PATH    = os.path.join(MODEL_DIR, "jobrole_model.joblib")
SALARY_MODEL_PATH     = os.path.join(MODEL_DIR, "salary_model.joblib")
COMPANY_MODEL_PATH    = os.path.join(MODEL_DIR, "company_model.joblib")

# ─── Lazy-loaded models (loaded once on first use) ───────────────────────────
_shortlist_model = None
_jobrole_model   = None
_salary_model    = None
_company_model   = None


def _load_model(path: str):
    """Load a joblib model file if it exists, else return None."""
    if os.path.exists(path):
        try:
            return joblib.load(path)
        except Exception as e:
            print(f"[MLPredictor] Failed to load model {path}: {e}")
    return None


def _get_models():
    """Lazy-load all ML models."""
    global _shortlist_model, _jobrole_model, _salary_model, _company_model
    if _shortlist_model is None:
        _shortlist_model = _load_model(SHORTLIST_MODEL_PATH)
    if _jobrole_model is None:
        _jobrole_model = _load_model(JOBROLE_MODEL_PATH)
    if _salary_model is None:
        _salary_model = _load_model(SALARY_MODEL_PATH)
    if _company_model is None:
        _company_model = _load_model(COMPANY_MODEL_PATH)


def _build_feature_vector(parsed: Dict) -> np.ndarray:
    """
    Convert parsed resume dict into a numeric feature vector.
    
    Features (9 total):
        0: skill_count
        1: has_projects (0/1)
        2: has_internship (0/1)
        3: has_education (0/1)
        4: has_certifications (0/1)
        5: action_verb_count
        6: quantified (0/1)
        7: experience_years
        8: word_count (normalized)
    """
    return np.array([[
        parsed.get("skill_count", 0),
        int(parsed.get("has_projects", False)),
        int(parsed.get("has_internship", False)),
        int(parsed.get("has_education", False)),
        int(parsed.get("has_certifications", False)),
        parsed.get("action_verb_count", 0),
        int(parsed.get("quantified", False)),
        parsed.get("experience_years", 0),
        min(parsed.get("word_count", 0) / 1000, 1.0),   # Normalize
    ]])


# ─── Rule-Based Fallbacks ────────────────────────────────────────────────────
def _rule_based_shortlist(parsed: Dict) -> Tuple[bool, float]:
    """Heuristic shortlisting when model not available."""
    score = 0
    if parsed.get("skill_count", 0) >= 5:   score += 2
    if parsed.get("has_projects"):           score += 2
    if parsed.get("has_internship"):         score += 2
    if parsed.get("has_education"):          score += 1
    if parsed.get("has_certifications"):     score += 1
    if parsed.get("quantified"):             score += 1
    if parsed.get("action_verb_count", 0) >= 3: score += 1
    shortlisted = score >= 6
    confidence  = round(min(score / 10, 1.0), 2)
    return shortlisted, confidence


def _rule_based_job_role(parsed: Dict) -> str:
    """Infer likely job role from skills."""
    skills = [s.lower() for s in parsed.get("skills", [])]
    if any(s in skills for s in ["machine learning", "tensorflow", "pytorch", "scikit-learn"]):
        return "Machine Learning Engineer"
    if any(s in skills for s in ["react", "javascript", "typescript", "node.js"]):
        return "Full Stack / Frontend Developer"
    if any(s in skills for s in ["aws", "docker", "kubernetes"]):
        return "DevOps / Cloud Engineer"
    if any(s in skills for s in ["sql", "postgresql", "mongodb"]):
        return "Data Analyst / Backend Developer"
    return "Software Engineer"


def _rule_based_salary(parsed: Dict) -> str:
    """Estimate salary band based on experience and skills."""
    exp    = parsed.get("experience_years", 0)
    skills = parsed.get("skill_count", 0)
    if exp >= 2 and skills >= 10:     return "12-20 LPA"
    if exp >= 1 and skills >= 7:      return "8-12 LPA"
    if skills >= 5:                   return "5-8 LPA"
    return "3-5 LPA"


def _rule_based_company(parsed: Dict) -> str:
    """Predict company type from profile."""
    skills = [s.lower() for s in parsed.get("skills", [])]
    product_skills = ["machine learning", "deep learning", "react", "kubernetes", "aws", "gcp"]
    if any(s in skills for s in product_skills) and parsed.get("has_internship"):
        return "Product-Based Company"
    if parsed.get("has_internship"):
        return "Mid-Size Tech / Startup"
    return "Service-Based Company"


# ─── Public API ───────────────────────────────────────────────────────────────

def predict_shortlisting(parsed: Dict) -> Tuple[bool, float]:
    """
    Predict whether a candidate will be shortlisted.
    
    Returns:
        (shortlisted: bool, confidence: float)
    """
    _get_models()
    if _shortlist_model:
        features = _build_feature_vector(parsed)
        pred     = _shortlist_model.predict(features)[0]
        prob     = _shortlist_model.predict_proba(features)[0]
        return bool(pred), round(float(max(prob)), 2)
    return _rule_based_shortlist(parsed)


def predict_job_role(parsed: Dict) -> str:
    """Predict most likely job role using SVM classifier."""
    _get_models()
    if _jobrole_model:
        features = _build_feature_vector(parsed)
        return _jobrole_model.predict(features)[0]
    return _rule_based_job_role(parsed)


def predict_salary(parsed: Dict) -> str:
    """Predict salary band using Random Forest regressor/classifier."""
    _get_models()
    if _salary_model:
        features = _build_feature_vector(parsed)
        return _salary_model.predict(features)[0]
    return _rule_based_salary(parsed)


def predict_company_type(parsed: Dict) -> str:
    """Predict company type using Random Forest classifier."""
    _get_models()
    if _company_model:
        features = _build_feature_vector(parsed)
        return _company_model.predict(features)[0]
    return _rule_based_company(parsed)


def get_improvement_suggestions(parsed: Dict, ats_score: float) -> Dict:
    """
    Generate NLP-based improvement suggestions for weak resumes.
    
    Returns:
        dict with missing_keywords, skill_gaps, suggestions
    """
    suggestions    = []
    missing_kw     = []
    skill_gaps     = []
    
    # Skill gap analysis
    core_skills = ["python", "sql", "git", "linux", "rest api"]
    for skill in core_skills:
        if skill not in [s.lower() for s in parsed.get("skills", [])]:
            skill_gaps.append(skill)
    
    # Missing sections
    if not parsed.get("has_projects"):
        suggestions.append("Add at least 2-3 technical projects with descriptions and tech stack used.")
        missing_kw.append("projects")
    if not parsed.get("has_internship"):
        suggestions.append("Include internship experience or freelance work to improve shortlisting chances.")
        missing_kw.append("internship experience")
    if not parsed.get("has_certifications"):
        suggestions.append("Add relevant certifications (AWS, Google, Coursera) to strengthen your profile.")
    if not parsed.get("quantified"):
        suggestions.append("Quantify your achievements: e.g., 'Reduced load time by 40%' or 'Served 10K+ users'.")
    if parsed.get("action_verb_count", 0) < 3:
        suggestions.append("Use strong action verbs: 'Developed', 'Optimized', 'Implemented', 'Designed'.")
    if parsed.get("skill_count", 0) < 5:
        suggestions.append("Expand your technical skills section — mention frameworks, tools, and languages.")
    if not parsed.get("has_linkedin"):
        suggestions.append("Add your LinkedIn profile URL for credibility.")
    if not parsed.get("has_github"):
        suggestions.append("Include your GitHub profile to showcase your code and projects.")
    if parsed.get("word_count", 0) < 200:
        suggestions.append("Your resume is too short. Aim for 300-600 words with detailed descriptions.")
    if ats_score < 60:
        suggestions.append("Your ATS score is below 60. Focus on adding keywords matching job descriptions.")
    
    return {
        "missing_keywords": missing_kw,
        "skill_gaps":       skill_gaps,
        "suggestions":      suggestions
    }
