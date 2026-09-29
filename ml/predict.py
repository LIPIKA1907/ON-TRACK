"""
OnTrack AI — Machine Learning Risk Prediction Inference Module
Smart India Hackathon 2026 | Problem Statement: SIH26103

Provides a clean, reusable prediction function that accepts a project record,
applies identical preprocessing, and outputs:
- time_risk_probability
- cost_risk_probability
- implementation_risk_probability
- overall_risk_score (0-100)
- risk_level (LOW, MEDIUM, HIGH)
"""

import os
import sys
import shutil
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Auto-delegate to Windows 'py' launcher if invoked from an environment without ML libraries
try:
    import pandas as pd
    import joblib
except ModuleNotFoundError as e:
    if "msys64" in sys.executable.lower() and shutil.which("py"):
        sys.exit(subprocess.call(["py"] + sys.argv))
    else:
        raise e

# Feature Schema
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

CATEGORICAL_FEATURES = [
    "Sector",
    "Project_Type",
    "Contractor_Performance",
]

ALL_INPUT_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

# Composite Risk Weights & Decision Thresholds
RISK_WEIGHTS = {
    "time": 0.40,
    "cost": 0.35,
    "impl": 0.25,
}

RISK_THRESHOLDS = {
    "low_max": 35.0,     # score < 35.0 -> LOW
    "medium_max": 65.0,  # 35.0 <= score < 65.0 -> MEDIUM, >= 65.0 -> HIGH
}

# Model artifacts cache
_LOADED_ARTIFACTS = None


def load_model_artifacts(models_dir: str = None) -> dict:
    """
    Load preprocessor and trained XGBoost classification models.
    Cached in memory for high-performance reuse.
    """
    global _LOADED_ARTIFACTS
    if _LOADED_ARTIFACTS is not None:
        return _LOADED_ARTIFACTS

    if models_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(script_dir, "..", "models")

    preprocessor_path = os.path.join(models_dir, "preprocessor.joblib")
    time_model_path = os.path.join(models_dir, "time_overrun_model.joblib")
    cost_model_path = os.path.join(models_dir, "cost_overrun_model.joblib")
    impl_model_path = os.path.join(models_dir, "implementation_risk_model.joblib")

    for path, name in [
        (preprocessor_path, "Preprocessor"),
        (time_model_path, "Time Overrun Model"),
        (cost_model_path, "Cost Overrun Model"),
        (impl_model_path, "Implementation Risk Model"),
    ]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Required model artifact '{name}' not found at: {os.path.abspath(path)}. "
                f"Please run 'ml/train_models.py' first."
            )

    preprocessor = joblib.load(preprocessor_path)
    # Ensure backwards compatibility for SimpleImputer if unpickled in newer scikit-learn
    for _, trans, _ in getattr(preprocessor, "transformers_", []):
        if hasattr(trans, "named_steps"):
            for step in trans.named_steps.values():
                if hasattr(step, "_fit_dtype") and not hasattr(step, "_fill_dtype"):
                    step._fill_dtype = step._fit_dtype
        elif hasattr(trans, "_fit_dtype") and not hasattr(trans, "_fill_dtype"):
            trans._fill_dtype = trans._fit_dtype

    artifacts = {
        "preprocessor": preprocessor,
        "time_model": joblib.load(time_model_path),
        "cost_model": joblib.load(cost_model_path),
        "impl_model": joblib.load(impl_model_path),
    }

    _LOADED_ARTIFACTS = artifacts
    return artifacts


def calculate_overall_risk(p_time: float, p_cost: float, p_impl: float) -> tuple:
    """
    Calculate composite overall risk score (0-100) and risk level.
    
    Formula:
        Overall Risk Score = (0.40 * p_time + 0.35 * p_cost + 0.25 * p_impl) * 100.0
    
    Risk Level Categories:
        - LOW:    score < 35.0
        - MEDIUM: 35.0 <= score < 65.0
        - HIGH:   score >= 65.0
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


def predict_project_risk(project_record: dict) -> dict:
    """
    Accepts one project record as a dictionary and returns:
    {
        "time_risk_probability": ...,
        "cost_risk_probability": ...,
        "implementation_risk_probability": ...,
        "overall_risk_score": ...,
        "risk_level": ...
    }
    """
    artifacts = load_model_artifacts()
    preprocessor = artifacts["preprocessor"]
    time_model = artifacts["time_model"]
    cost_model = artifacts["cost_model"]
    impl_model = artifacts["impl_model"]

    # Convert to single-row DataFrame with required feature columns
    if isinstance(project_record, pd.DataFrame):
        df_record = project_record[ALL_INPUT_FEATURES].copy()
    else:
        # Dictionary input: ensure all expected feature columns exist
        row_dict = {feat: project_record.get(feat, None) for feat in ALL_INPUT_FEATURES}
        df_record = pd.DataFrame([row_dict])

    # Ensure numerical types are numeric
    for col in NUMERICAL_FEATURES:
        df_record[col] = pd.to_numeric(df_record[col], errors="coerce")

    # Apply identical ColumnTransformer preprocessing
    processed_features = preprocessor.transform(df_record)

    # Compute probability of positive class (Class 1) for each model
    p_time = float(time_model.predict_proba(processed_features)[0, 1])
    p_cost = float(cost_model.predict_proba(processed_features)[0, 1])
    p_impl = float(impl_model.predict_proba(processed_features)[0, 1])

    overall_score, risk_level = calculate_overall_risk(p_time, p_cost, p_impl)

    return {
        "time_risk_probability": round(p_time, 4),
        "cost_risk_probability": round(p_cost, 4),
        "implementation_risk_probability": round(p_impl, 4),
        "overall_risk_score": overall_score,
        "risk_level": risk_level,
    }


def main():
    print("=" * 65)
    print("OnTrack AI — Risk Prediction Testing (Checkpoint 2)")
    print("=" * 65)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "projects.csv")

    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    df = pd.read_csv(data_path)

    # Select 3 distinct project records across different sectors/conditions
    sample_ids = [df.iloc[0]["Project_ID"], df.iloc[4]["Project_ID"], df.iloc[9]["Project_ID"]]
    samples = df[df["Project_ID"].isin(sample_ids)]

    print(f"\nEvaluating {len(samples)} representative project records from projects.csv:\n")

    for _, row in samples.iterrows():
        record = row.to_dict()
        pred = predict_project_risk(record)

        print("-" * 65)
        print(f"Project ID: {record['Project_ID']} | Sector: {record['Sector']} | Type: {record['Project_Type']}")
        print(f"Cost: INR {record['Approved_Cost']} Cr | Physical: {record['Physical_Progress']}% (Planned: {record['Planned_Progress']}%)")
        print(f"Milestones Delayed: {record['Milestones_Delayed']}/{record['Milestones_Total']} | Contractor: {record['Contractor_Performance']}")
        print(f"Prediction Results:")
        print(f"  - Time Risk Probability:           {pred['time_risk_probability']:.4f}")
        print(f"  - Cost Risk Probability:           {pred['cost_risk_probability']:.4f}")
        print(f"  - Implementation Risk Probability: {pred['implementation_risk_probability']:.4f}")
        print(f"  -> OVERALL RISK SCORE:             {pred['overall_risk_score']} / 100 [{pred['risk_level']} RISK]")

    print("-" * 65)
    print("Inference verification completed successfully.")


if __name__ == "__main__":
    main()
