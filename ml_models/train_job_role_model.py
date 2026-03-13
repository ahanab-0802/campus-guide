"""
train_job_role_model.py
------------------------
Trains an SVM multiclass classifier to predict job roles from resume features.

Usage:
    python train_job_role_model.py

Output:
    ml_models/jobrole_model.joblib
"""

import os
import sys
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_PATH  = os.path.join(BASE_DIR, "datasets", "resume_data.csv")
MODEL_DIR  = os.path.join(BASE_DIR, "ml_models")
MODEL_PATH = os.path.join(MODEL_DIR, "jobrole_model.joblib")

FEATURES = [
    "skill_count", "has_projects", "has_internship", "has_education",
    "has_certifications", "action_verb_count", "quantified",
    "experience_years", "word_count_norm"
]
TARGET = "job_role"


def load_data():
    if not os.path.exists(DATA_PATH):
        print(f"[Error] Dataset not found. Run: python datasets/generate_dataset.py")
        sys.exit(1)
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows | {df[TARGET].nunique()} job role classes")
    return df


def train_model(df):
    X = df[FEATURES].values
    y = df[TARGET].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # ── SVM with RBF Kernel (good for multi-class, medium datasets) ───────────
    print("\nTraining SVM Classifier (RBF kernel)...")
    svm = SVC(
        kernel="rbf",
        C=10,
        gamma="scale",
        probability=True,       # Required for predict_proba
        random_state=42,
        class_weight="balanced"  # Handle class imbalance
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svm",    svm)
    ])

    pipeline.fit(X_train, y_train)

    # ── Evaluate ─────────────────────────────────────────────────────────────
    y_pred = pipeline.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)

    print(f"\nTest Accuracy: {acc:.4f}")
    print("\n── Classification Report ──────────────────────────────")
    print(classification_report(y_test, y_pred))

    # ── Cross-validation ─────────────────────────────────────────────────────
    cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring="accuracy")
    print(f"5-Fold CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    return pipeline


if __name__ == "__main__":
    print("=" * 55)
    print("  Campus Guide — Job Role SVM Model Training")
    print("=" * 55)

    df    = load_data()
    model = train_model(df)

    joblib.dump(model, MODEL_PATH)
    print(f"\n✓ Model saved to: {MODEL_PATH}")