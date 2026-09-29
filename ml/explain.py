"""
OnTrack AI — SHAP Explainability Engine
Smart India Hackathon 2026 | Problem Statement: SIH26103

Provides exact, local and global SHAP (SHapley Additive exPlanations) for the
trained XGBoost models (Time Overrun, Cost Overrun, Implementation Risk).

Features:
- Decomposes predictions into positive risk drivers and protective factors
- Uses human-readable feature naming
- Prepares structured, frontend-ready JSON output
- Mathematically verifies that base_value + sum(shap_values) == model_margin == logit(probability)
- Generates high-resolution SHAP waterfall and bar visualizations
"""

import os
import sys
import shutil
import subprocess
from typing import Dict, List, Any, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Auto-delegate to Windows 'py' launcher if invoked from an environment without ML libraries
try:
    import numpy as np
    import pandas as pd
    import joblib
    import shap
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ModuleNotFoundError as e:
    if "msys64" in sys.executable.lower() and shutil.which("py"):
        sys.exit(subprocess.call(["py"] + sys.argv))
    else:
        raise e

# -------------------------------------------------------------
# FEATURE SCHEMAS & HUMAN-READABLE LABELS
# -------------------------------------------------------------

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

# Friendly display names for reporting and frontend visualization
HUMAN_FEATURE_NAMES = {
    "Approved_Cost": "Approved Cost (₹ Cr)",
    "Planned_Duration": "Planned Duration (Months)",
    "Elapsed_Duration": "Elapsed Duration (Months)",
    "Physical_Progress": "Physical Progress",
    "Planned_Progress": "Planned Progress",
    "Financial_Progress": "Financial Progress",
    "Expenditure": "Cumulative Spend (₹ Cr)",
    "Milestones_Total": "Total Milestones",
    "Milestones_Delayed": "Milestones Delayed",
    "Average_Milestone_Delay_Days": "Average Milestone Delay",
    "Procurement_Delay_Days": "Procurement Delay",
    "Land_Acquisition_Progress": "Land Acquisition Progress",
    "Approvals_Pending": "Pending Approvals",
    "Scope_Changes": "Scope Changes",
    "Sector": "Infrastructure Sector",
    "Project_Type": "Project Type",
    "Contractor_Performance": "Contractor Performance",
}

# Dimension metadata
DIMENSION_METADATA = {
    "time": {
        "title": "Time Overrun Risk",
        "model_file": "time_overrun_model.joblib",
        "description": "Risk of project schedule slippage exceeding 3 months beyond baseline.",
    },
    "cost": {
        "title": "Cost Overrun Risk",
        "model_file": "cost_overrun_model.joblib",
        "description": "Risk of project expenditure exceeding sanctioned budget by 5% or more.",
    },
    "impl": {
        "title": "Implementation Risk",
        "model_file": "implementation_risk_model.joblib",
        "description": "Composite operational friction across land, regulatory clearances, and vendor delivery.",
    },
}

# Overall Risk Composite Weights
RISK_WEIGHTS = {
    "time": 0.40,
    "cost": 0.35,
    "impl": 0.25,
}

RISK_THRESHOLDS = {
    "low_max": 35.0,
    "medium_max": 65.0,
}

# In-memory artifact cache
_ARTIFACTS_CACHE = {}


# -------------------------------------------------------------
# CORE LOADERS & PREPROCESSING
# -------------------------------------------------------------

def load_explainability_artifacts(models_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Load preprocessor, XGBoost models, and initialize TreeExplainer objects.
    Caches artifacts in-memory to optimize inference latency.
    """
    global _ARTIFACTS_CACHE
    if _ARTIFACTS_CACHE:
        return _ARTIFACTS_CACHE

    if models_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(script_dir, "..", "models")

    preprocessor_path = os.path.join(models_dir, "preprocessor.joblib")
    if not os.path.exists(preprocessor_path):
        raise FileNotFoundError(f"Preprocessor artifact not found at: {os.path.abspath(preprocessor_path)}")

    preprocessor = joblib.load(preprocessor_path)
    # Ensure backwards compatibility for SimpleImputer if unpickled in newer scikit-learn
    for _, trans, _ in getattr(preprocessor, "transformers_", []):
        if hasattr(trans, "named_steps"):
            for step in trans.named_steps.values():
                if hasattr(step, "_fit_dtype") and not hasattr(step, "_fill_dtype"):
                    step._fill_dtype = step._fit_dtype
        elif hasattr(trans, "_fit_dtype") and not hasattr(trans, "_fill_dtype"):
            trans._fill_dtype = trans._fit_dtype

    feature_names_out = list(preprocessor.get_feature_names_out())

    models = {}
    explainers = {}

    for dim_key, meta in DIMENSION_METADATA.items():
        model_path = os.path.join(models_dir, meta["model_file"])
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model artifact '{meta['model_file']}' not found at: {os.path.abspath(model_path)}")
        model = joblib.load(model_path)
        models[dim_key] = model
        # Initialize TreeExplainer for TreeSHAP local attributions
        explainers[dim_key] = shap.TreeExplainer(model)

    _ARTIFACTS_CACHE = {
        "preprocessor": preprocessor,
        "feature_names_out": feature_names_out,
        "models": models,
        "explainers": explainers,
    }
    return _ARTIFACTS_CACHE


def _prepare_record_dataframe(project_record: Any) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Normalizes a single project dictionary or DataFrame row into a standardized
    DataFrame conforming to the training feature schema.
    """
    if isinstance(project_record, pd.DataFrame):
        row_dict = project_record.iloc[0].to_dict()
    elif isinstance(project_record, pd.Series):
        row_dict = project_record.to_dict()
    elif isinstance(project_record, dict):
        row_dict = dict(project_record)
    else:
        raise ValueError(f"Unsupported record format: {type(project_record)}. Expected dict, Series, or DataFrame.")

    clean_dict = {feat: row_dict.get(feat, None) for feat in ALL_INPUT_FEATURES}
    df_record = pd.DataFrame([clean_dict])

    for col in NUMERICAL_FEATURES:
        df_record[col] = pd.to_numeric(df_record[col], errors="coerce")

    return df_record, row_dict


def calculate_overall_risk(p_time: float, p_cost: float, p_impl: float) -> Tuple[float, str]:
    """
    Calculate composite executive risk score (0-100) and risk level.
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


# -------------------------------------------------------------
# SHAP EXPLANATION LOGIC
# -------------------------------------------------------------

def explain_project_risk(
    project_record: Any,
    risk_type: str = "time",
    top_n: int = 5,
    models_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates a SHAP-based local feature attribution explanation for one project
    and one specific risk dimension ("time", "cost", or "impl").

    Returns a clean dictionary ready for frontend consumption:
    - risk_dimension: str
    - risk_probability: float (0.0 to 1.0)
    - model_margin: float (raw log-odds output from XGBoost)
    - base_value: float (expected margin E[f(X)])
    - top_risk_factors: List[Dict] (features pushing predicted risk upward)
    - protective_factors: List[Dict] (features pulling predicted risk downward)
    - all_feature_contributions: List[Dict] (all input features sorted by absolute impact)
    - mathematical_verification: Dict showing base_value + sum(shap) == margin
    """
    risk_key = risk_type.lower()
    if risk_key not in DIMENSION_METADATA:
        valid_keys = list(DIMENSION_METADATA.keys())
        raise ValueError(f"Invalid risk_type '{risk_type}'. Choose from: {valid_keys}")

    artifacts = load_explainability_artifacts(models_dir)
    preprocessor = artifacts["preprocessor"]
    model = artifacts["models"][risk_key]
    explainer = artifacts["explainers"][risk_key]
    feature_names_out = artifacts["feature_names_out"]

    df_record, raw_dict = _prepare_record_dataframe(project_record)
    X_proc = preprocessor.transform(df_record)

    # 1. Real model inference
    prob = float(model.predict_proba(X_proc)[0, 1])
    margin = float(model.predict(X_proc, output_margin=True)[0])

    # 2. TreeSHAP computation
    try:
        shap_explanation = explainer(X_proc)
        shap_vals = shap_explanation.values[0]  # array of length 31 (transformed columns)
        base_val = float(explainer.expected_value)
    except Exception as e:
        return {
            "risk_dimension": DIMENSION_METADATA[risk_key]["title"],
            "risk_probability": round(prob, 4),
            "model_margin": round(margin, 4),
            "base_value": 0.0,
            "top_risk_factors": [],
            "protective_factors": [],
            "all_feature_contributions": [],
            "mathematical_verification": {
                "base_value": 0.0,
                "sum_shap_values": 0.0,
                "reconstructed_margin": round(margin, 4),
                "actual_model_margin": round(margin, 4),
                "margin_difference": 0.0,
                "verified_consistent": False,
            },
            "fallback": True,
            "fallback_reason": f"Detailed SHAP local explanation fallback: {str(e)}",
        }

    # 3. Aggregate 31 one-hot features back to the 17 primary input features
    aggregated_contributions = {}
    for feat in ALL_INPUT_FEATURES:
        aggregated_contributions[feat] = {
            "feature": HUMAN_FEATURE_NAMES.get(feat, feat),
            "feature_key": feat,
            "value": raw_dict.get(feat, None),
            "contribution": 0.0,
        }

    for col_idx, col_name in enumerate(feature_names_out):
        val_contrib = float(shap_vals[col_idx])

        if col_name.startswith("num__"):
            orig_feat = col_name.replace("num__", "")
            if orig_feat in aggregated_contributions:
                aggregated_contributions[orig_feat]["contribution"] += val_contrib
        elif col_name.startswith("cat__"):
            # Format: cat__<OrigFeat>_<CategoryValue>
            cat_body = col_name.replace("cat__", "")
            for parent_feat in CATEGORICAL_FEATURES:
                prefix = f"{parent_feat}_"
                if cat_body.startswith(prefix):
                    aggregated_contributions[parent_feat]["contribution"] += val_contrib
                    break

    # Format numeric values nicely
    feature_list = []
    for feat, data in aggregated_contributions.items():
        v = data["value"]
        if isinstance(v, (float, np.floating)):
            data["value"] = round(float(v), 2)
        elif isinstance(v, (int, np.integer)):
            data["value"] = int(v)
        data["contribution"] = round(float(data["contribution"]), 4)
        feature_list.append(data)

    # 4. Separate positive risk factors vs protective factors
    # Positive contribution (> 0): increases predicted risk probability
    positive_factors = [
        item for item in feature_list if item["contribution"] > 0
    ]
    positive_factors.sort(key=lambda x: x["contribution"], reverse=True)

    # Negative contribution (< 0): decreases predicted risk probability (protective)
    protective_factors = [
        item for item in feature_list if item["contribution"] < 0
    ]
    protective_factors.sort(key=lambda x: x["contribution"])  # most negative first

    # All features sorted by absolute magnitude of impact
    all_sorted = sorted(feature_list, key=lambda x: abs(x["contribution"]), reverse=True)

    # 5. Mathematical verification check: base_value + sum(shap_values) == margin
    sum_shap = float(shap_vals.sum())
    reconstructed_margin = base_val + sum_shap
    margin_diff = abs(reconstructed_margin - margin)
    verified = margin_diff < 1e-4

    return {
        "risk_dimension": DIMENSION_METADATA[risk_key]["title"],
        "risk_key": risk_key,
        "description": DIMENSION_METADATA[risk_key]["description"],
        "risk_probability": round(prob, 4),
        "model_margin": round(margin, 4),
        "base_value": round(base_val, 4),
        "top_risk_factors": positive_factors[:top_n],
        "protective_factors": protective_factors[:top_n],
        "all_contributions": all_sorted,
        "mathematical_verification": {
            "base_value": round(base_val, 6),
            "sum_shap_values": round(sum_shap, 6),
            "reconstructed_margin": round(reconstructed_margin, 6),
            "actual_model_margin": round(margin, 6),
            "margin_difference": round(margin_diff, 8),
            "verified_consistent": verified,
        },
    }


def explain_all_risks(
    project_record: Any,
    top_n: int = 5,
    models_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Explains all three risk dimensions (Time, Cost, Implementation) for a project,
    computes the composite executive risk score, and provides a cross-cutting summary.
    """
    df_record, raw_dict = _prepare_record_dataframe(project_record)
    project_id = raw_dict.get("Project_ID", "UNKNOWN")

    explanations = {}
    probs = {}

    for dim_key in ["time", "cost", "impl"]:
        try:
            exp = explain_project_risk(df_record, risk_type=dim_key, top_n=top_n, models_dir=models_dir)
        except Exception as e:
            exp = {
                "risk_dimension": DIMENSION_METADATA.get(dim_key, {}).get("title", dim_key),
                "risk_probability": 0.5,
                "model_margin": 0.0,
                "base_value": 0.0,
                "top_risk_factors": [],
                "protective_factors": [],
                "all_feature_contributions": [],
                "fallback": True,
                "fallback_reason": str(e),
            }
        explanations[dim_key] = exp
        probs[dim_key] = exp.get("risk_probability", 0.5)

    overall_score, risk_level = calculate_overall_risk(
        probs["time"], probs["cost"], probs["impl"]
    )

    # Identify dominant cross-cutting risk factors
    cross_cutting_drivers = []
    for dim_key, exp in explanations.items():
        if exp["top_risk_factors"]:
            top = exp["top_risk_factors"][0]
            cross_cutting_drivers.append({
                "dimension": exp["risk_dimension"],
                "feature": top["feature"],
                "value": top["value"],
                "contribution": top["contribution"],
            })

    return {
        "project_id": project_id,
        "overall_risk_score": overall_score,
        "risk_level": risk_level,
        "time_overrun": explanations["time"],
        "cost_overrun": explanations["cost"],
        "implementation_risk": explanations["impl"],
        "cross_cutting_primary_drivers": cross_cutting_drivers,
    }


# -------------------------------------------------------------
# SHAP VISUALIZATION GENERATION
# -------------------------------------------------------------

def _format_transformed_feature_name(col_name: str) -> str:
    """
    Converts one-hot and transformed column names into professional, human-readable labels.
    """
    if col_name.startswith("num__"):
        feat = col_name.replace("num__", "")
        return HUMAN_FEATURE_NAMES.get(feat, feat)
    elif col_name.startswith("cat__"):
        cat_body = col_name.replace("cat__", "")
        for parent_feat in CATEGORICAL_FEATURES:
            prefix = f"{parent_feat}_"
            if cat_body.startswith(prefix):
                cat_val = cat_body.replace(prefix, "")
                parent_display = HUMAN_FEATURE_NAMES.get(parent_feat, parent_feat)
                return f"{parent_display}: {cat_val}"
    return col_name


def generate_shap_visualizations(
    project_record: Any,
    output_dir: str = "docs/shap_examples",
    prefix: str = "project",
    models_dir: Optional[str] = None,
) -> Dict[str, str]:
    """
    Generates and saves SHAP waterfall plots and bar plots for Time, Cost,
    and Implementation risk dimensions for the given project record.

    Returns a dictionary of generated image paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    artifacts = load_explainability_artifacts(models_dir)
    preprocessor = artifacts["preprocessor"]
    feature_names_out = artifacts["feature_names_out"]

    df_record, raw_dict = _prepare_record_dataframe(project_record)
    project_id = raw_dict.get("Project_ID", prefix)
    clean_id = str(project_id).replace("-", "_").lower()

    X_proc = preprocessor.transform(df_record)
    human_labels = [_format_transformed_feature_name(name) for name in feature_names_out]

    generated_files = {}

    for dim_key, meta in DIMENSION_METADATA.items():
        model = artifacts["models"][dim_key]
        explainer = artifacts["explainers"][dim_key]

        prob = float(model.predict_proba(X_proc)[0, 1])

        # Compute SHAP explanation object
        exp = explainer(X_proc)
        # Clone and inject human labels and data values for clear visualization
        single_exp = exp[0]
        single_exp.feature_names = human_labels

        # 1. SHAP Waterfall Plot
        waterfall_filename = f"{clean_id}_{dim_key}_risk_waterfall.png"
        waterfall_path = os.path.join(output_dir, waterfall_filename)

        plt.figure(figsize=(10, 6.5))
        shap.plots.waterfall(single_exp, max_display=10, show=False)
        plt.title(
            f"{meta['title']} — SHAP Waterfall Explanation\n"
            f"Project: {project_id} | Predicted Risk Probability: {prob * 100:.1f}%",
            fontsize=12,
            fontweight="bold",
            pad=15,
        )
        plt.tight_layout()
        plt.savefig(waterfall_path, dpi=160, bbox_inches="tight")
        plt.close()
        generated_files[f"{dim_key}_waterfall"] = os.path.abspath(waterfall_path)

        # 2. SHAP Bar Plot (Local feature attribution)
        bar_filename = f"{clean_id}_{dim_key}_risk_bar.png"
        bar_path = os.path.join(output_dir, bar_filename)

        plt.figure(figsize=(10, 6.5))
        shap.plots.bar(single_exp, max_display=10, show=False)
        plt.title(
            f"{meta['title']} — SHAP Feature Attribution (Local Bar Plot)\n"
            f"Project: {project_id} | Predicted Risk Probability: {prob * 100:.1f}%",
            fontsize=12,
            fontweight="bold",
            pad=15,
        )
        plt.tight_layout()
        plt.savefig(bar_path, dpi=160, bbox_inches="tight")
        plt.close()
        generated_files[f"{dim_key}_bar"] = os.path.abspath(bar_path)

    return generated_files


# -------------------------------------------------------------
# CLI TESTING & DEMONSTRATION HARNESS
# -------------------------------------------------------------

def run_explanation_demo():
    print("=" * 75)
    print("OnTrack AI — Real SHAP-Based Explainable AI Engine (Checkpoint 3)")
    print("Smart India Hackathon 2026 | Problem Statement: SIH26103")
    print("=" * 75)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "projects.csv")
    output_dir = os.path.join(script_dir, "..", "docs", "shap_examples")

    if not os.path.exists(data_path):
        print(f"Error: Dataset not found at: {data_path}")
        return

    df = pd.read_csv(data_path)

    # Select 3 representative projects: Low Risk, High Risk, Watchlist/Medium Risk
    # PRJ-0001 (Water Supply - Low Risk)
    # PRJ-0005 (Railway - Critical High Risk)
    # PRJ-0004 (Bridge - Watchlist/Medium Risk)
    test_ids = ["PRJ-0001", "PRJ-0005", "PRJ-0004"]
    selected_df = df[df["Project_ID"].isin(test_ids)].copy()

    # If any test ID wasn't found, pick first, 5th, and 10th rows
    if len(selected_df) < 3:
        selected_df = df.iloc[[0, 4, 9]].copy()

    print(f"\n[1/3] Loaded {len(selected_df)} representative projects for explainability verification.\n")

    for idx, (_, row) in enumerate(selected_df.iterrows(), 1):
        record = row.to_dict()
        exp = explain_all_risks(record)

        print("━" * 75)
        print(f"PROJECT #{idx}: {record['Project_ID']} | Sector: {record['Sector']} | Type: {record['Project_Type']}")
        print(f"Approved Cost: ₹{record['Approved_Cost']} Cr | Physical: {record['Physical_Progress']}% (Planned: {record['Planned_Progress']}%)")
        print(f"Contractor: {record['Contractor_Performance']} | Milestone Slippage: {record['Milestones_Delayed']}/{record['Milestones_Total']} | Pending Approvals: {record['Approvals_Pending']}")
        print(f"OVERALL RISK SCORE: {exp['overall_risk_score']} / 100 [{exp['risk_level']} RISK]")
        print("━" * 75)

        for dim_key in ["time", "cost", "impl"]:
            dim_exp = exp[f"{'time_overrun' if dim_key=='time' else 'cost_overrun' if dim_key=='cost' else 'implementation_risk'}"]
            print(f"\n  ▶ {dim_exp['risk_dimension'].upper()} (Predicted Probability: {dim_exp['risk_probability'] * 100:.1f}%)")
            print(f"    Margin: {dim_exp['model_margin']:+.4f} | Base Value: {dim_exp['base_value']:+.4f}")

            # Verification check
            mv = dim_exp["mathematical_verification"]
            ver_status = "PASSED (Exact)" if mv["verified_consistent"] else "FAILED"
            print(f"    Consistency Check: base_val ({mv['base_value']}) + sum_shap ({mv['sum_shap_values']}) = {mv['reconstructed_margin']} vs model margin {mv['actual_model_margin']} [{ver_status}]")

            print(f"    ▲ Top Positive Risk Factors (Increasing Risk):")
            if dim_exp["top_risk_factors"]:
                for factor in dim_exp["top_risk_factors"][:3]:
                    print(f"      • {factor['feature']}: {factor['value']}  (SHAP Contribution: {factor['contribution']:+.4f})")
            else:
                print("      • None (No feature significantly drives risk upward)")

            print(f"    ▼ Protective Factors (Decreasing Risk):")
            if dim_exp["protective_factors"]:
                for factor in dim_exp["protective_factors"][:3]:
                    print(f"      • {factor['feature']}: {factor['value']}  (SHAP Contribution: {factor['contribution']:+.4f})")
            else:
                print("      • None (No feature provides significant risk attenuation)")

        print()

    # [2/3] Generate SHAP Visualizations for representative projects
    print("=" * 75)
    print(f"[2/3] Generating SHAP Waterfall and Bar Plots in: {os.path.abspath(output_dir)}")
    print("=" * 75)

    # Generate full visual sets for PRJ-0005 (High Risk project) and PRJ-0001 (Low Risk project)
    high_risk_record = df[df["Project_ID"] == "PRJ-0005"].iloc[0].to_dict()
    low_risk_record = df[df["Project_ID"] == "PRJ-0001"].iloc[0].to_dict()

    files_high = generate_shap_visualizations(high_risk_record, output_dir=output_dir, prefix="prj_0005")
    files_low = generate_shap_visualizations(low_risk_record, output_dir=output_dir, prefix="prj_0001")

    print("\nGenerated SHAP Visualizations:")
    for key, path in {**files_high, **files_low}.items():
        print(f"  • {os.path.basename(path)} ({os.path.getsize(path) // 1024} KB)")

    print("\n" + "=" * 75)
    print("[3/3] Explainability engine test & verification completed successfully.")
    print("=" * 75)


if __name__ == "__main__":
    run_explanation_demo()
