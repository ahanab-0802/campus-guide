"""
train_shortlist_model.py
-------------------------
Trains an XGBoost binary classifier to predict resume shortlisting.

Usage:
    cd campus-guide
    python train_shortlist_model.py

Output:
    ml_models/shortlist_model.joblib
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.pipeline import Pipeline

try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    print("[Warning] XGBoost not installed. Falling back to RandomForestClassifier.")
    from sklearn.ensemble import RandomForestClassifier
    XGB_AVAILABLE = False

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_PATH  = os.path.join(BASE_DIR, "datasets", "resume_data.csv")
MODEL_DIR  = os.path.join(BASE_DIR, "ml_models")
MODEL_PATH = os.path.join(MODEL_DIR, "shortlist_model.joblib")

os.makedirs(MODEL_DIR, exist_ok=True)

# ─── Feature columns ──────────────────────────────────────────────────────────
FEATURES = [
    "skill_count", "has_projects", "has_internship", "has_education",
    "has_certifications", "action_verb_count", "quantified",
    "experience_years", "word_count_norm"
]
TARGET = "shortlisted"


def load_data():
    """Load dataset, check it exists, return X, y."""
    if not os.path.exists(DATA_PATH):
        print(f"[Error] Dataset not found at {DATA_PATH}")
        print("Run first: python datasets/generate_dataset.py")
        sys.exit(1)

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows from {DATA_PATH}")
    print(f"Positive class (shortlisted): {df[TARGET].sum()} ({df[TARGET].mean()*100:.1f}%)")

    X = df[FEATURES].values
    y = df[TARGET].values
    return X, y


def train_model(X, y):
    """Train XGBoost classifier with hyperparameter search."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    if XGB_AVAILABLE:
        # ── XGBoost with hyperparameter grid ─────────────────────────────────
        print("\nTraining XGBoost Classifier...")
        clf = XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1
        )
    else:
        # ── Fallback: Random Forest ────────────────────────────────────────────
        from sklearn.ensemble import RandomForestClassifier
        print("\nTraining RandomForest Classifier (XGBoost fallback)...")
        clf = RandomForestClassifier(
            n_estimators=200, max_depth=8, random_state=42, n_jobs=-1
        )

    # ── Wrap in pipeline with scaler ─────────────────────────────────────────
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    clf)
    ])

    pipeline.fit(X_train, y_train)

    # ── Evaluation ───────────────────────────────────────────────────────────
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    print("\n── Classification Report ──────────────────────────────")
    print(classification_report(y_test, y_pred, target_names=["Not Shortlisted", "Shortlisted"]))

    print("── Confusion Matrix ───────────────────────────────────")
    print(confusion_matrix(y_test, y_pred))

    auc = roc_auc_score(y_test, y_prob)
    print(f"\nROC-AUC Score: {auc:.4f}")

    # ── Cross-validation ─────────────────────────────────────────────────────
    cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring="roc_auc")
    print(f"5-Fold CV AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    return pipeline


if __name__ == "__main__":
    print("=" * 55)
    print("  Campus Guide — Shortlisting Model Training")
    print("=" * 55)

    X, y = load_data()
    model = train_model(X, y)

    joblib.dump(model, MODEL_PATH)
    print(f"\n✓ Model saved to: {MODEL_PATH}")