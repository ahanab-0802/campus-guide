"""
services/ats_scorer.py
-----------------------
Calculates an ATS (Applicant Tracking System) score for a resume.
Uses rule-based scoring across 5 categories: keywords, formatting,
skills, education, and experience. Returns a score out of 100.
"""

from typing import Dict
from app.utils.resume_parser import TECH_SKILLS, ACTION_VERBS


# ─── Scoring Weights ─────────────────────────────────────────────────────────
WEIGHTS = {
    "keywords":   25,   # Presence of tech keywords
    "formatting": 20,   # Structure signals (sections, lengths)
    "skills":     25,   # Number of recognized skills
    "education":  15,   # Education section presence
    "experience": 15,   # Project / internship presence
}


def calculate_ats_score(parsed: Dict) -> Dict:
    """
    Calculate ATS score from parsed resume features.
    
    Args:
        parsed: Output from resume_parser.parse_resume()
    
    Returns:
        dict with total ats_score and per-category breakdown
    """
    breakdown = {}

    # ── 1. Keywords (25 pts) ─────────────────────────────────────────────────
    # Count action verbs and quantified achievements
    verb_score   = min(parsed["action_verb_count"] / 5, 1.0)   # max out at 5 verbs
    quant_score  = 1.0 if parsed["quantified"] else 0.5
    kw_score     = round((verb_score * 0.5 + quant_score * 0.5) * WEIGHTS["keywords"], 1)
    breakdown["keywords"] = {"score": kw_score, "max": WEIGHTS["keywords"]}

    # ── 2. Formatting (20 pts) ───────────────────────────────────────────────
    # Good resumes: 300-800 words, has linkedin/github, has email/phone
    wc     = parsed["word_count"]
    wc_ok  = 1.0 if 300 <= wc <= 900 else (0.5 if wc > 150 else 0.2)
    social = (0.5 if parsed["has_linkedin"] else 0) + (0.5 if parsed["has_github"] else 0)
    contact = 1.0 if (parsed["email"] and parsed["phone"]) else 0.5
    fmt_score = round(((wc_ok + social + contact) / 3) * WEIGHTS["formatting"], 1)
    breakdown["formatting"] = {"score": fmt_score, "max": WEIGHTS["formatting"]}

    # ── 3. Skills (25 pts) ───────────────────────────────────────────────────
    skill_count = parsed["skill_count"]
    skill_ratio = min(skill_count / 10, 1.0)   # Expect at least 10 skills for full marks
    skill_score = round(skill_ratio * WEIGHTS["skills"], 1)
    breakdown["skills"] = {"score": skill_score, "max": WEIGHTS["skills"],
                           "found": parsed["skills"]}

    # ── 4. Education (15 pts) ────────────────────────────────────────────────
    edu_score = WEIGHTS["education"] if parsed["has_education"] else 5
    if parsed["has_certifications"]:
        edu_score = min(edu_score + 3, WEIGHTS["education"])
    breakdown["education"] = {"score": edu_score, "max": WEIGHTS["education"]}

    # ── 5. Experience (15 pts) ───────────────────────────────────────────────
    exp = 0
    if parsed["has_internship"]:  exp += 8
    if parsed["has_projects"]:    exp += 7
    exp_score = min(exp, WEIGHTS["experience"])
    breakdown["experience"] = {"score": exp_score, "max": WEIGHTS["experience"]}

    # ── Total ────────────────────────────────────────────────────────────────
    total = sum(v["score"] for v in breakdown.values())
    total = round(min(total, 100), 1)

    return {
        "ats_score": total,
        "breakdown": breakdown
    }
