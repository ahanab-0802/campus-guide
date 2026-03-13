"""
datasets/generate_dataset.py
-----------------------------
Generates a synthetic resume dataset for training all ML models.
Run this FIRST before training any models.

Output: datasets/resume_data.csv
"""

import os
import pandas as pd
import numpy as np
import random

random.seed(42)
np.random.seed(42)

# ─── Output path ─────────────────────────────────────────────────────────────
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "resume_data.csv")

# ─── Config ───────────────────────────────────────────────────────────────────
N_SAMPLES = 2000

JOB_ROLES = [
    "Machine Learning Engineer",
    "Full Stack Developer",
    "DevOps / Cloud Engineer",
    "Data Analyst",
    "Backend Developer",
    "Frontend Developer",
    "Cybersecurity Engineer",
    "Embedded Systems Engineer"
]

SALARY_BANDS = [
    "3-5 LPA", "5-8 LPA", "8-12 LPA", "12-20 LPA"
]

COMPANY_TYPES = [
    "Service-Based Company",
    "Product-Based Company",
    "Mid-Size Tech / Startup",
    "Government / PSU"
]


def generate_sample(i: int) -> dict:
    """Generate one synthetic resume feature record."""
    # ── Base features (randomized) ────────────────────────────────────────────
    skill_count       = random.randint(1, 18)
    has_projects      = random.random() > 0.2
    has_internship    = random.random() > 0.35
    has_education     = random.random() > 0.05
    has_certifications = random.random() > 0.45
    action_verb_count = random.randint(0, 12)
    quantified        = random.random() > 0.4
    experience_years  = round(random.uniform(0, 4), 1)
    word_count        = random.randint(100, 900)

    # ── Derived: quality score for label generation ────────────────────────────
    quality = (
        skill_count * 0.3 +
        int(has_projects) * 2.5 +
        int(has_internship) * 2.5 +
        int(has_education) * 1.5 +
        int(has_certifications) * 1.0 +
        action_verb_count * 0.2 +
        int(quantified) * 1.5 +
        experience_years * 0.8
    )

    # ── Shortlisted label (threshold ~7.5) ────────────────────────────────────
    shortlisted = int(quality >= 7.5 + random.gauss(0, 1.5))
    shortlisted = int(bool(shortlisted))

    # ── Job role label ────────────────────────────────────────────────────────
    if skill_count >= 10 and action_verb_count >= 6:
        job_role_idx = 0   # ML Engineer
    elif skill_count >= 8:
        job_role_idx = random.choice([1, 4, 5])
    elif has_certifications and skill_count >= 6:
        job_role_idx = 2   # DevOps
    elif word_count > 400:
        job_role_idx = random.choice([3, 4])
    else:
        job_role_idx = random.randint(0, len(JOB_ROLES) - 1)

    # ── Salary label ─────────────────────────────────────────────────────────
    if quality >= 12 and experience_years >= 2:   salary_idx = 3
    elif quality >= 9:                             salary_idx = 2
    elif quality >= 6:                             salary_idx = 1
    else:                                          salary_idx = 0

    # ── Company type label ────────────────────────────────────────────────────
    if shortlisted and skill_count >= 9 and has_internship:  company_idx = 1  # Product
    elif shortlisted and has_internship:                      company_idx = 2  # Startup
    elif shortlisted:                                         company_idx = 0  # Service
    else:                                                     company_idx = random.randint(0, 3)

    return {
        "skill_count":        skill_count,
        "has_projects":       int(has_projects),
        "has_internship":     int(has_internship),
        "has_education":      int(has_education),
        "has_certifications": int(has_certifications),
        "action_verb_count":  action_verb_count,
        "quantified":         int(quantified),
        "experience_years":   experience_years,
        "word_count_norm":    min(word_count / 1000, 1.0),
        # Labels
        "shortlisted":        shortlisted,
        "job_role":           JOB_ROLES[job_role_idx],
        "salary_band":        SALARY_BANDS[salary_idx],
        "company_type":       COMPANY_TYPES[company_idx],
    }


if __name__ == "__main__":
    print(f"Generating {N_SAMPLES} synthetic resume records...")
    records = [generate_sample(i) for i in range(N_SAMPLES)]
    df = pd.DataFrame(records)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Dataset saved to: {OUTPUT_PATH}")
    print(f"Shape: {df.shape}")
    print(f"\nShortlisted distribution:\n{df['shortlisted'].value_counts()}")
    print(f"\nJob roles:\n{df['job_role'].value_counts()}")
    print(f"\nSalary bands:\n{df['salary_band'].value_counts()}")
    print(f"\nCompany types:\n{df['company_type'].value_counts()}")