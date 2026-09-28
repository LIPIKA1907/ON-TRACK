"""
OnTrack AI — Machine Learning Risk Prediction Training Pipeline
Smart India Hackathon 2026 | Problem Statement: SIH26103

Trains, evaluates, and serializes risk classification models:
- Time Overrun Risk (XGBoost + Random Forest baseline)
- Cost Overrun Risk (XGBoost + Random Forest baseline)
- Implementation Risk (XGBoost + Random Forest baseline)

Serializes preprocessors and models to the models/ directory.
"""

import os
import sys
import json
import shutil
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Auto-delegate to Windows 'py' launcher if invoked from an environment without ML libraries
try:
    import pandas as pd
    import numpy as np
    import sklearn
    import xgboost
    import joblib
except ModuleNotFoundError as e:
    if "msys64" in sys.executable.lower() and shutil.which("py"):
        sys.exit(subprocess.call(["py"] + sys.argv))
    else:
        raise e

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from xgboost import XGBClassifier

# -------------------------------------------------------------
# FEATURE CONFIGURATION
# -------------------------------------------------------------

CATEGORICAL_FEATURES = [
    "Sector",
    "Project_Type",
    "Contractor_Performance",
]

NUMERICAL_FEATURES = [
    "Approved_Cost",
    "Planned_Duration",
    "Elapsed_Duration",
    "Physical_Progress",
    "Planned_Progress",
    "Financial_Progress",
    "Expenditure",
    "Milestones_Total",
    "Milestones_Delayed",
    "Average_Milestone_Delay_Days",
    "Procurement_Delay_Days",
    "Land_Acquisition_Progress",
    "Approvals_Pending",
    "Scope_Changes",
]

TARGET_COLUMNS = [
    "Time_Overrun_Flag",
    "Cost_Overrun_Flag",
    "Implementation_Risk_Flag",
]

EXCLUDED_COLUMNS = [
    "Project_ID",
    "Time_Overrun_Months",
    "Cost_Overrun_Pct",
] + TARGET_COLUMNS

# Risk Score Weights & Thresholds
RISK_WEIGHTS = {
    "time": 0.40,
    "cost": 0.35,
    "impl": 0.25,
}

RISK_THRESHOLDS = {
    "low_max": 35.0,     # score < 35.0 -> LOW
    "medium_max": 65.0,  # 35.0 <= score < 65.0 -> MEDIUM, >= 65.0 -> HIGH
}


def calculate_overall_risk(p_time: float, p_cost: float, p_impl: float) -> tuple:
    """
    Calculate composite overall risk score (0-100) and risk level.
    """
    raw_score = (
        RISK_WEIGHTS["time"] * p_time +
        RISK_WEIGHTS["cost"] * p_cost +
        RISK_WEIGHTS["impl"] * p_impl
    ) * 100.0
    score = round(max(0.0, min(100.0, raw_score)), 1)

    if score < RISK_THRESHOLDS["low_max"]:
        level = "LOW"
    elif score < RISK_THRESHOLDS["medium_max"]:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return score, level


def build_preprocessor() -> ColumnTransformer:
    """
    Create a robust Scikit-learn ColumnTransformer for numerical and categorical features.
    """
    num_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
    ])

    cat_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, NUMERICAL_FEATURES),
            ("cat", cat_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return preprocessor


def evaluate_model(model, X_test, y_test, model_name: str) -> dict:
    """
    Compute comprehensive classification metrics.
    """
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "model_name": model_name,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
    }
    return metrics


def train_and_evaluate_all():
    print("=" * 70)
    print("OnTrack AI — Machine Learning Training Pipeline (Checkpoint 2)")
    print("Smart India Hackathon 2026 | Problem Statement: SIH26103")
    print("=" * 70)

    # 1. Load Dataset
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "projects.csv")
    models_dir = os.path.join(script_dir, "..", "models")
    os.makedirs(models_dir, exist_ok=True)

    print(f"\n[1/6] Loading dataset from: {os.path.abspath(data_path)}")
    df = pd.read_csv(data_path)
    print(f"      Loaded {len(df)} records across {len(df.columns)} columns.")

    # 2. Extract Features and Targets
    X = df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES].copy()
    y_time = df["Time_Overrun_Flag"].values
    y_cost = df["Cost_Overrun_Flag"].values
    y_impl = df["Implementation_Risk_Flag"].values

    print(f"\n[2/6] Feature extraction:")
    print(f"      - Numerical Features:   {len(NUMERICAL_FEATURES)}")
    print(f"      - Categorical Features: {len(CATEGORICAL_FEATURES)}")
    print(f"      - Total Input Features: {len(NUMERICAL_FEATURES) + len(CATEGORICAL_FEATURES)}")
    print(f"      - Excluded from Inputs: {EXCLUDED_COLUMNS}")

    # 3. Train / Test Split (Reproducible 80/20 split, seed=42)
    indices = np.arange(len(df))
    train_idx, test_idx = train_test_split(
        indices,
        test_size=0.20,
        random_state=42,
        stratify=df["Time_Overrun_Flag"],
    )

    X_train, X_test = X.iloc[train_idx].copy(), X.iloc[test_idx].copy()
    print(f"\n[3/6] Split dataset:")
    print(f"      - Training records: {len(X_train)} (80%)")
    print(f"      - Testing records:  {len(X_test)} (20%)")

    # 4. Fit Preprocessor
    print(f"\n[4/6] Fitting feature preprocessor on training data...")
    preprocessor = build_preprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    # Save Preprocessor
    preprocessor_path = os.path.join(models_dir, "preprocessor.joblib")
    joblib.dump(preprocessor, preprocessor_path)
    print(f"      Saved preprocessor to: {os.path.abspath(preprocessor_path)}")

    # 5. Train Models for Each Target
    targets = [
        ("Time Overrun Risk", "Time_Overrun_Flag", y_time, "time_overrun_model.joblib"),
        ("Cost Overrun Risk", "Cost_Overrun_Flag", y_cost, "cost_overrun_model.joblib"),
        ("Implementation Risk", "Implementation_Risk_Flag", y_impl, "implementation_risk_model.joblib"),
    ]

    trained_models = {}
    evaluation_results = {}

    print(f"\n[5/6] Training XGBoost (Primary) & Random Forest (Baseline) models...")

    for display_name, target_col, y_all, save_filename in targets:
        y_train_t = y_all[train_idx]
        y_test_t = y_all[test_idx]

        # A. Baseline: Random Forest
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42,
        )
        rf.fit(X_train_proc, y_train_t)
        rf_metrics = evaluate_model(rf, X_test_proc, y_test_t, f"Random Forest ({display_name})")

        # B. Primary: XGBoost
        xgb = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
            eval_metric="logloss",
        )
        xgb.fit(X_train_proc, y_train_t)
        xgb_metrics = evaluate_model(xgb, X_test_proc, y_test_t, f"XGBoost ({display_name})")

        # Save Primary Model
        model_save_path = os.path.join(models_dir, save_filename)
        joblib.dump(xgb, model_save_path)
        trained_models[target_col] = xgb

        evaluation_results[target_col] = {
            "display_name": display_name,
            "saved_file": save_filename,
            "train_positive_count": int(y_train_t.sum()),
            "train_positive_pct": round(float(y_train_t.mean() * 100), 2),
            "test_positive_count": int(y_test_t.sum()),
            "test_positive_pct": round(float(y_test_t.mean() * 100), 2),
            "primary_model": "XGBoost",
            "primary_metrics": xgb_metrics,
            "baseline_model": "Random Forest",
            "baseline_metrics": rf_metrics,
        }

        print(f"\n  --- {display_name.upper()} ---")
        print(f"      Saved: {save_filename}")
        print(f"      [XGBoost]       Accuracy: {xgb_metrics['accuracy']:.4f} | Precision: {xgb_metrics['precision']:.4f} | Recall: {xgb_metrics['recall']:.4f} | F1: {xgb_metrics['f1_score']:.4f} | ROC-AUC: {xgb_metrics['roc_auc']:.4f}")
        print(f"      [Random Forest] Accuracy: {rf_metrics['accuracy']:.4f} | Precision: {rf_metrics['precision']:.4f} | Recall: {rf_metrics['recall']:.4f} | F1: {rf_metrics['f1_score']:.4f} | ROC-AUC: {rf_metrics['roc_auc']:.4f}")

    # 6. Save Model Metadata JSON
    metadata = {
        "project": "OnTrack AI",
        "sih_problem_statement": "SIH26103",
        "training_records": len(X_train),
        "test_records": len(X_test),
        "numerical_features": NUMERICAL_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "risk_weights": RISK_WEIGHTS,
        "risk_thresholds": RISK_THRESHOLDS,
        "models": evaluation_results,
    }

    metadata_path = os.path.join(models_dir, "model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"\n[6/6] Saved model metadata to: {os.path.abspath(metadata_path)}")

    # 7. Demonstrate Sample Predictions on 3 Project Records
    print("\n" + "=" * 70)
    print("SAMPLE EVALUATIONS ON 3 TEST PROJECTS")
    print("=" * 70)

    sample_indices = [test_idx[0], test_idx[10], test_idx[25]]
    sample_rows = df.iloc[sample_indices]

    for rank, (orig_idx, row) in enumerate(sample_rows.iterrows(), 1):
        record_df = pd.DataFrame([row[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]])
        record_proc = preprocessor.transform(record_df)

        p_time = float(trained_models["Time_Overrun_Flag"].predict_proba(record_proc)[0, 1])
        p_cost = float(trained_models["Cost_Overrun_Flag"].predict_proba(record_proc)[0, 1])
        p_impl = float(trained_models["Implementation_Risk_Flag"].predict_proba(record_proc)[0, 1])

        overall_score, risk_level = calculate_overall_risk(p_time, p_cost, p_impl)

        print(f"\n[Example Project {rank}] ID: {row['Project_ID']} | Sector: {row['Sector']} | Type: {row['Project_Type']}")
        print(f"  Physical Progress: {row['Physical_Progress']}% (Planned: {row['Planned_Progress']}%) | Milestone Delays: {row['Milestones_Delayed']}/{row['Milestones_Total']}")
        print(f"  Contractor: {row['Contractor_Performance']} | Approvals Pending: {row['Approvals_Pending']} | Scope Changes: {row['Scope_Changes']}")
        print(f"  -> Time Overrun Risk Prob:           {p_time:.4f}")
        print(f"  -> Cost Overrun Risk Prob:           {p_cost:.4f}")
        print(f"  -> Implementation Risk Prob:         {p_impl:.4f}")
        print(f"  => OVERALL RISK SCORE:               {overall_score:.1f} / 100 [{risk_level} RISK]")

    print("\n" + "=" * 70)
    print("Training pipeline finished successfully.")
    print("=" * 70)
    return metadata


if __name__ == "__main__":
    train_and_evaluate_all()
