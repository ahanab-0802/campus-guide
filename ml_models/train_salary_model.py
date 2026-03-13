"""
train_salary_model.py
----------------------
Trains Random Forest classifiers to predict:
  1. Salary band (e.g., "8-12 LPA")
  2. Company type (e.g., "Product-Based Company")

Usage:
    python train_salary_model.py

Outputs:
    ml_models/salary_model.joblib
    ml_models/company_model.joblib
"""

import os
import sys
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DATA_PATH       = os.path.join(BASE_DIR, "datasets", "resume_data.csv")
MODEL_DIR       = os.path.join(BASE_DIR, "ml_models")
SALARY_MODEL    = os.path.join(MODEL_DIR, "salary_model.joblib")
COMPANY_MODEL   = os.path.join(MODEL_DIR, "company_model.joblib")

os.makedirs(MODEL_DIR, exist_ok=True)

FEATURES = [
    "skill_count", "has_projects", "has_internship", "has_education",
    "has_certifications", "action_verb_count", "quantified",
    "experience_years", "word_count_norm"
]


def load_data():
    if not os.path.exists(DATA_PATH):
        print("[Error] Dataset not found. Run: python datasets/generate_dataset.py")
        sys.exit(1)
    return pd.read_csv(DATA_PATH)


def train_rf_classifier(X, y, target_name: str) -> Pipeline:
    """
    Train a Random Forest classifier on features X with labels y.
    
    Args:
        X:           Feature matrix (numpy array)
        y:           Label array (string labels)
        target_name: Name of what we're predicting (for logging)
    
    Returns:
        Trained sklearn Pipeline (scaler + Random Forest)
    """
    print(f"\n── Training RandomForest for: {target_name} ─────────────")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    rf = RandomForestClassifier(
        n_estimators   = 300,
        max_depth      = 10,
        min_samples_leaf = 3,
        class_weight   = "balanced",
        random_state   = 42,
        n_jobs         = -1
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("rf",     rf)
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {acc:.4f}")
    print(classification_report(y_test, y_pred))

    cv = cross_val_score(pipeline, X, y, cv=5, scoring="accuracy")
    print(f"5-Fold CV: {cv.mean():.4f} ± {cv.std():.4f}")

    return pipeline


if __name__ == "__main__":
    print("=" * 55)
    print("  Campus Guide — Salary & Company Type Model Training")
    print("=" * 55)

    df = load_data()
    print(f"Loaded {len(df)} rows")

    X = df[FEATURES].values

    # ── 1. Salary model ───────────────────────────────────────────────────────
    y_salary   = df["salary_band"].values
    salary_mdl = train_rf_classifier(X, y_salary, "Salary Band")
    joblib.dump(salary_mdl, SALARY_MODEL)
    print(f"\n✓ Salary model saved: {SALARY_MODEL}")

    # ── 2. Company type model ─────────────────────────────────────────────────
    y_company   = df["company_type"].values
    company_mdl = train_rf_classifier(X, y_company, "Company Type")
    joblib.dump(company_mdl, COMPANY_MODEL)
    print(f"\n✓ Company model saved: {COMPANY_MODEL}")

    print("\n All salary/company models trained successfully!")