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

# Auto-delegate to Windows 'py' launcher if invoked from an environment
# without ML libraries
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


# -------------------------------------------------------------
# MONOTONIC CONSTRAINTS
# -------------------------------------------------------------
#
# +1 = increasing the feature cannot decrease predicted risk
# -1 = increasing the feature cannot increase predicted risk
#  0 = no monotonic assumption
#
# These constraints encode domain-informed relationships for
# infrastructure project risk prediction.
# -------------------------------------------------------------

MONOTONIC_CONSTRAINTS = {
    "Approved_Cost": 0,
    "Planned_Duration": 0,
    "Elapsed_Duration": 0,

    # More progress should not increase risk
    "Physical_Progress": -1,
    "Planned_Progress": -1,

    # Financial progress is left unconstrained because higher
    # expenditure/progress does not necessarily mean lower risk.
    "Financial_Progress": 0,

    "Expenditure": 0,
    "Milestones_Total": 0,

    # More delays should not decrease risk
    "Milestones_Delayed": 1,
    "Average_Milestone_Delay_Days": 1,
    "Procurement_Delay_Days": 1,

    # More acquisition progress should not increase risk
    "Land_Acquisition_Progress": -1,

    # More pending approvals should not decrease risk
    "Approvals_Pending": 1,

    # More scope changes should not decrease risk
    "Scope_Changes": 1,
}


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


# -------------------------------------------------------------
# RISK SCORE WEIGHTS & THRESHOLDS
# -------------------------------------------------------------

RISK_WEIGHTS = {
    "time": 0.40,
    "cost": 0.35,
    "impl": 0.25,
}

RISK_THRESHOLDS = {
    "low_max": 35.0,
    # score < 35.0 -> LOW
    # 35.0 <= score < 65.0 -> MEDIUM
    # >= 65.0 -> HIGH
    "medium_max": 65.0,
}


def calculate_overall_risk(
    p_time: float,
    p_cost: float,
    p_impl: float
) -> tuple:
    """
    Calculate composite overall risk score (0-100) and risk level.
    """

    raw_score = (
        RISK_WEIGHTS["time"] * p_time
        + RISK_WEIGHTS["cost"] * p_cost
        + RISK_WEIGHTS["impl"] * p_impl
    ) * 100.0

    score = round(
        max(0.0, min(100.0, raw_score)),
        1
    )

    if score < RISK_THRESHOLDS["low_max"]:
        level = "LOW"
    elif score < RISK_THRESHOLDS["medium_max"]:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return score, level


# -------------------------------------------------------------
# PREPROCESSOR
# -------------------------------------------------------------

def build_preprocessor() -> ColumnTransformer:
    """
    Create a robust Scikit-learn ColumnTransformer for numerical
    and categorical features.
    """

    num_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    cat_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                num_pipeline,
                NUMERICAL_FEATURES,
            ),
            (
                "cat",
                cat_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    return preprocessor


# -------------------------------------------------------------
# MONOTONIC CONSTRAINT BUILDER
# -------------------------------------------------------------

def build_monotonic_constraints(preprocessor) -> list:
    """
    Build monotonic constraints matching the exact feature order
    produced by the fitted ColumnTransformer.

    Numerical features receive their domain-informed constraints.

    One-hot encoded categorical features receive 0 because no
    monotonic relationship is assumed for categorical variables.
    """

    feature_names = preprocessor.get_feature_names_out()

    constraints = []

    for feature_name in feature_names:

        # Numerical features appear as:
        # num__FeatureName
        if feature_name.startswith("num__"):

            original_feature = feature_name.replace(
                "num__",
                "",
                1
            )

            constraint = MONOTONIC_CONSTRAINTS.get(
                original_feature,
                0
            )

        else:
            # One-hot encoded categorical features
            constraint = 0

        constraints.append(constraint)

    return constraints


# -------------------------------------------------------------
# MODEL EVALUATION
# -------------------------------------------------------------

def evaluate_model(
    model,
    X_test,
    y_test,
    model_name: str
) -> dict:
    """
    Compute comprehensive classification metrics.
    """

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "model_name": model_name,
        "accuracy": round(
            float(accuracy_score(y_test, y_pred)),
            4
        ),
        "precision": round(
            float(
                precision_score(
                    y_test,
                    y_pred,
                    zero_division=0
                )
            ),
            4
        ),
        "recall": round(
            float(
                recall_score(
                    y_test,
                    y_pred,
                    zero_division=0
                )
            ),
            4
        ),
        "f1_score": round(
            float(
                f1_score(
                    y_test,
                    y_pred,
                    zero_division=0
                )
            ),
            4
        ),
        "roc_auc": round(
            float(
                roc_auc_score(
                    y_test,
                    y_prob
                )
            ),
            4
        ),
    }

    return metrics


# -------------------------------------------------------------
# MAIN TRAINING PIPELINE
# -------------------------------------------------------------

def train_and_evaluate_all():

    print("=" * 70)
    print(
        "OnTrack AI — Machine Learning Training Pipeline "
        "(Checkpoint 2)"
    )
    print(
        "Smart India Hackathon 2026 | "
        "Problem Statement: SIH26103"
    )
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. LOAD DATASET
    # ---------------------------------------------------------

    script_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    data_path = os.path.join(
        script_dir,
        "..",
        "data",
        "paimana",
        "paimana_normalized.csv"
    )

    models_dir = os.path.join(
        script_dir,
        "..",
        "models"
    )

    os.makedirs(
        models_dir,
        exist_ok=True
    )

    print(
        f"\n[1/6] Loading dataset from: "
        f"{os.path.abspath(data_path)}"
    )

    df = pd.read_csv(data_path)

    print(
        f"      Loaded {len(df)} records across "
        f"{len(df.columns)} columns."
    )

    # ---------------------------------------------------------
    # 2. EXTRACT FEATURES AND TARGETS
    # ---------------------------------------------------------

    X = df[
        NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    ].copy()

    y_time = df[
        "Time_Overrun_Flag"
    ].values

    y_cost = df[
        "Cost_Overrun_Flag"
    ].values

    y_impl = df[
        "Implementation_Risk_Flag"
    ].values

    print("\n[2/6] Feature extraction:")

    print(
        f"      - Numerical Features:   "
        f"{len(NUMERICAL_FEATURES)}"
    )

    print(
        f"      - Categorical Features: "
        f"{len(CATEGORICAL_FEATURES)}"
    )

    print(
        f"      - Total Input Features: "
        f"{len(NUMERICAL_FEATURES) + len(CATEGORICAL_FEATURES)}"
    )

    print(
        f"      - Excluded from Inputs: "
        f"{EXCLUDED_COLUMNS}"
    )

    # ---------------------------------------------------------
    # 3. TRAIN / TEST SPLIT
    # ---------------------------------------------------------

    indices = np.arange(len(df))

    train_idx, test_idx = train_test_split(
        indices,
        test_size=0.20,
        random_state=42,
        stratify=df["Time_Overrun_Flag"],
    )

    X_train = X.iloc[
        train_idx
    ].copy()

    X_test = X.iloc[
        test_idx
    ].copy()

    print("\n[3/6] Split dataset:")

    print(
        f"      - Training records: "
        f"{len(X_train)} (80%)"
    )

    print(
        f"      - Testing records:  "
        f"{len(X_test)} (20%)"
    )

    # ---------------------------------------------------------
    # 4. FIT PREPROCESSOR
    # ---------------------------------------------------------

    print(
        "\n[4/6] Fitting feature preprocessor "
        "on training data..."
    )

    preprocessor = build_preprocessor()

    X_train_proc = preprocessor.fit_transform(
        X_train
    )

    X_test_proc = preprocessor.transform(
        X_test
    )

    # Build constraints AFTER preprocessing so that
    # constraints exactly match the transformed feature order.
    monotonic_constraints = build_monotonic_constraints(
        preprocessor
    )

    print(
        "\n      Monotonic constraints:"
    )

    for feature_name, constraint in zip(
        preprocessor.get_feature_names_out(),
        monotonic_constraints
    ):

        if constraint != 0:

            direction = (
                "↑ risk"
                if constraint == 1
                else "↓ risk"
            )

            print(
                f"        {feature_name}: "
                f"{constraint} ({direction})"
            )

    # Save Preprocessor
    preprocessor_path = os.path.join(
        models_dir,
        "preprocessor.joblib"
    )

    joblib.dump(
        preprocessor,
        preprocessor_path
    )

    print(
        f"      Saved preprocessor to: "
        f"{os.path.abspath(preprocessor_path)}"
    )

    # ---------------------------------------------------------
    # 5. TRAIN MODELS FOR EACH TARGET
    # ---------------------------------------------------------

    targets = [
        (
            "Time Overrun Risk",
            "Time_Overrun_Flag",
            y_time,
            "time_overrun_model.joblib",
        ),
        (
            "Cost Overrun Risk",
            "Cost_Overrun_Flag",
            y_cost,
            "cost_overrun_model.joblib",
        ),
        (
            "Implementation Risk",
            "Implementation_Risk_Flag",
            y_impl,
            "implementation_risk_model.joblib",
        ),
    ]

    trained_models = {}
    evaluation_results = {}

    print(
        "\n[5/6] Training XGBoost (Primary) & "
        "Random Forest (Baseline) models..."
    )

    for (
        display_name,
        target_col,
        y_all,
        save_filename
    ) in targets:

        y_train_t = y_all[
            train_idx
        ]

        y_test_t = y_all[
            test_idx
        ]

        # -----------------------------------------------------
        # A. BASELINE: RANDOM FOREST
        # -----------------------------------------------------

        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42,
        )

        rf.fit(
            X_train_proc,
            y_train_t
        )

        rf_metrics = evaluate_model(
            rf,
            X_test_proc,
            y_test_t,
            f"Random Forest ({display_name})"
        )

        # -----------------------------------------------------
        # B. PRIMARY: XGBOOST
        # -----------------------------------------------------

        xgb = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
            eval_metric="logloss",

            # Domain-informed monotonic constraints
            monotone_constraints=tuple(
                monotonic_constraints
            ),
        )

        xgb.fit(
            X_train_proc,
            y_train_t
        )

        xgb_metrics = evaluate_model(
            xgb,
            X_test_proc,
            y_test_t,
            f"XGBoost ({display_name})"
        )

        # -----------------------------------------------------
        # SAVE PRIMARY MODEL
        # -----------------------------------------------------

        model_save_path = os.path.join(
            models_dir,
            save_filename
        )

        joblib.dump(
            xgb,
            model_save_path
        )

        trained_models[
            target_col
        ] = xgb

        evaluation_results[
            target_col
        ] = {
            "display_name": display_name,
            "saved_file": save_filename,

            "train_positive_count": int(
                y_train_t.sum()
            ),

            "train_positive_pct": round(
                float(
                    y_train_t.mean() * 100
                ),
                2
            ),

            "test_positive_count": int(
                y_test_t.sum()
            ),

            "test_positive_pct": round(
                float(
                    y_test_t.mean() * 100
                ),
                2
            ),

            "primary_model": "XGBoost",

            "primary_metrics": xgb_metrics,

            "baseline_model": "Random Forest",

            "baseline_metrics": rf_metrics,
        }

        print(
            f"\n  --- {display_name.upper()} ---"
        )

        print(
            f"      Saved: {save_filename}"
        )

        print(
            f"      [XGBoost]       "
            f"Accuracy: {xgb_metrics['accuracy']:.4f} | "
            f"Precision: {xgb_metrics['precision']:.4f} | "
            f"Recall: {xgb_metrics['recall']:.4f} | "
            f"F1: {xgb_metrics['f1_score']:.4f} | "
            f"ROC-AUC: {xgb_metrics['roc_auc']:.4f}"
        )

        print(
            f"      [Random Forest] "
            f"Accuracy: {rf_metrics['accuracy']:.4f} | "
            f"Precision: {rf_metrics['precision']:.4f} | "
            f"Recall: {rf_metrics['recall']:.4f} | "
            f"F1: {rf_metrics['f1_score']:.4f} | "
            f"ROC-AUC: {rf_metrics['roc_auc']:.4f}"
        )

    # ---------------------------------------------------------
    # 6. SAVE MODEL METADATA
    # ---------------------------------------------------------

    metadata = {
        "project": "OnTrack AI",

        "sih_problem_statement": "SIH26103",

        "training_records": len(X_train),

        "test_records": len(X_test),

        "numerical_features": NUMERICAL_FEATURES,

        "categorical_features": CATEGORICAL_FEATURES,

        "risk_weights": RISK_WEIGHTS,

        "risk_thresholds": RISK_THRESHOLDS,

        "monotonic_constraints": MONOTONIC_CONSTRAINTS,

        "models": evaluation_results,
    }

    metadata_path = os.path.join(
        models_dir,
        "model_metadata.json"
    )

    with open(
        metadata_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=2
        )

    print(
        f"\n[6/6] Saved model metadata to: "
        f"{os.path.abspath(metadata_path)}"
    )

    # ---------------------------------------------------------
    # 7. SAMPLE PREDICTIONS
    # ---------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "SAMPLE EVALUATIONS ON 3 TEST PROJECTS"
    )

    print(
        "=" * 70
    )

    sample_indices = [
        test_idx[0],
        test_idx[10],
        test_idx[25],
    ]

    sample_rows = df.iloc[
        sample_indices
    ]

    for rank, (
        orig_idx,
        row
    ) in enumerate(
        sample_rows.iterrows(),
        1
    ):

        record_df = pd.DataFrame(
            [
                row[
                    NUMERICAL_FEATURES
                    + CATEGORICAL_FEATURES
                ]
            ]
        )

        record_proc = preprocessor.transform(
            record_df
        )

        p_time = float(
            trained_models[
                "Time_Overrun_Flag"
            ].predict_proba(
                record_proc
            )[0, 1]
        )

        p_cost = float(
            trained_models[
                "Cost_Overrun_Flag"
            ].predict_proba(
                record_proc
            )[0, 1]
        )

        p_impl = float(
            trained_models[
                "Implementation_Risk_Flag"
            ].predict_proba(
                record_proc
            )[0, 1]
        )

        overall_score, risk_level = (
            calculate_overall_risk(
                p_time,
                p_cost,
                p_impl
            )
        )

        print(
            f"\n[Example Project {rank}] "
            f"ID: {row['Project_ID']} | "
            f"Sector: {row['Sector']} | "
            f"Type: {row['Project_Type']}"
        )

        print(
            f"  Physical Progress: "
            f"{row['Physical_Progress']}% "
            f"(Planned: {row['Planned_Progress']}%) | "
            f"Milestone Delays: "
            f"{row['Milestones_Delayed']}/"
            f"{row['Milestones_Total']}"
        )

        print(
            f"  Contractor: "
            f"{row['Contractor_Performance']} | "
            f"Approvals Pending: "
            f"{row['Approvals_Pending']} | "
            f"Scope Changes: "
            f"{row['Scope_Changes']}"
        )

        print(
            f"  -> Time Overrun Risk Prob: "
            f"{p_time:.4f}"
        )

        print(
            f"  -> Cost Overrun Risk Prob: "
            f"{p_cost:.4f}"
        )

        print(
            f"  -> Implementation Risk Prob: "
            f"{p_impl:.4f}"
        )

        print(
            f"  => OVERALL RISK SCORE: "
            f"{overall_score:.1f} / 100 "
            f"[{risk_level} RISK]"
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "Training pipeline finished successfully."
    )

    print(
        "=" * 70
    )

    return metadata


# -------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------

if __name__ == "__main__":
    train_and_evaluate_all()