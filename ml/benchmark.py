"""
OnTrack AI — Project Benchmarking Engine
Smart India Hackathon 2026 | Problem Statement: SIH26103

Provides comparative, factual benchmarking for a selected infrastructure project
against historical peers in projects.csv based on sector, project type, and scale.

Features:
- Sensible multi-tier peer filtering (Sector, Project Type, Cost scale, Duration scale)
- Graceful fallback to maintain statistically meaningful peer cohorts (N >= 5)
- Multi-metric comparative breakdown (Physical progress, spend, delays, clearances, risk)
- Strictly factual reporting (avoids subjective 'better' / 'worse' labels)
- Explicit disclosure of synthetic data basis
"""

import os
import sys
import shutil
import subprocess
from typing import Dict, Any, Optional, Tuple, Union

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Auto-delegate to Windows 'py' launcher if invoked from an environment without ML libraries
try:
    import pandas as pd
    import numpy as np
except ModuleNotFoundError as e:
    if "msys64" in sys.executable.lower() and shutil.which("py"):
        sys.exit(subprocess.call(["py"] + sys.argv))
    else:
        raise e

# Import prediction functions from ml/predict.py
try:
    from ml.predict import predict_project_risk, load_model_artifacts, NUMERICAL_FEATURES, ALL_INPUT_FEATURES
except ImportError:
    # If running directly inside ml directory
    from predict import predict_project_risk, load_model_artifacts, NUMERICAL_FEATURES, ALL_INPUT_FEATURES

# In-memory cache for projects dataset and precomputed risk scores
_BENCHMARK_CACHE = {
    "df": None,
    "scores_computed": False,
}

SYNTHETIC_DATASET_DISCLOSURE = (
    "Benchmark metrics are derived strictly from the available synthetic dataset "
    "(data/projects.csv, N=1,000 projects) created for prototype demonstration. "
    "Values represent factual statistical peer distributions and must be recalibrated "
    "against verified government project databases before real-world deployment."
)


def load_benchmark_dataset(data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Loads and caches the projects dataset with precomputed risk scores for fast benchmarking.
    """
    global _BENCHMARK_CACHE
    if _BENCHMARK_CACHE["df"] is not None:
        return _BENCHMARK_CACHE["df"]

    if data_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(script_dir, "..", "data", "projects.csv")

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Projects dataset not found at: {os.path.abspath(data_path)}")

    df = pd.read_csv(data_path)

    # Precompute risk scores for all projects to allow fast peer average calculations
    try:
        artifacts = load_model_artifacts()
        preprocessor = artifacts["preprocessor"]
        time_model = artifacts["time_model"]
        cost_model = artifacts["cost_model"]
        impl_model = artifacts["impl_model"]

        X = df[ALL_INPUT_FEATURES].copy()
        for col in NUMERICAL_FEATURES:
            X[col] = pd.to_numeric(X[col], errors="coerce")

        X_proc = preprocessor.transform(X)
        p_time = time_model.predict_proba(X_proc)[:, 1]
        p_cost = cost_model.predict_proba(X_proc)[:, 1]
        p_impl = impl_model.predict_proba(X_proc)[:, 1]

        # Overall risk score formula: (0.40 * time + 0.35 * cost + 0.25 * impl) * 100
        overall_scores = (0.40 * p_time + 0.35 * p_cost + 0.25 * p_impl) * 100.0
        df["_precomputed_overall_risk"] = np.round(np.clip(overall_scores, 0.0, 100.0), 1)
        df["_precomputed_time_risk"] = np.round(p_time, 4)
        df["_precomputed_cost_risk"] = np.round(p_cost, 4)
        df["_precomputed_impl_risk"] = np.round(p_impl, 4)
    except Exception:
        # Fallback if model loading fails
        df["_precomputed_overall_risk"] = np.nan

    _BENCHMARK_CACHE["df"] = df
    _BENCHMARK_CACHE["scores_computed"] = True
    return df


def _filter_comparable_peers(
    project_record: Dict[str, Any],
    df: pd.DataFrame,
    min_peers: int = 5,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Finds comparable peer projects in df using sensible, hierarchical criteria:
    Tier 1 (Narrow/High-Fidelity): Same Sector + Same Project_Type + Cost in [0.5x, 2.0x] + Duration in [0.7x, 1.3x]
    Tier 2 (Relaxed Scale): Same Sector + Same Project_Type
    Tier 3 (Sector Level): Same Sector
    """
    project_id = project_record.get("Project_ID", None)
    sector = project_record.get("Sector", None)
    project_type = project_record.get("Project_Type", None)
    approved_cost = float(project_record.get("Approved_Cost", 0.0) or 0.0)
    planned_duration = float(project_record.get("Planned_Duration", 0.0) or 0.0)

    # Exclude the project itself if present
    base_pool = df if project_id is None else df[df["Project_ID"] != project_id]

    # Tier 1: Sector + Type + Scale Range
    if sector and project_type and approved_cost > 0 and planned_duration > 0:
        cost_min, cost_max = approved_cost * 0.50, approved_cost * 2.00
        dur_min, dur_max = planned_duration * 0.70, planned_duration * 1.30

        tier1_mask = (
            (base_pool["Sector"] == sector) &
            (base_pool["Project_Type"] == project_type) &
            (base_pool["Approved_Cost"] >= cost_min) &
            (base_pool["Approved_Cost"] <= cost_max) &
            (base_pool["Planned_Duration"] >= dur_min) &
            (base_pool["Planned_Duration"] <= dur_max)
        )
        tier1_peers = base_pool[tier1_mask]
        if len(tier1_peers) >= min_peers:
            criteria = {
                "match_tier": "Strict (Sector, Type & Scale Bracket)",
                "sector": sector,
                "project_type": project_type,
                "cost_bracket_crores": [round(cost_min, 1), round(cost_max, 1)],
                "duration_bracket_months": [round(dur_min, 1), round(dur_max, 1)],
            }
            return tier1_peers, criteria

    # Tier 2: Sector + Project Type
    if sector and project_type:
        tier2_mask = (base_pool["Sector"] == sector) & (base_pool["Project_Type"] == project_type)
        tier2_peers = base_pool[tier2_mask]
        if len(tier2_peers) >= min_peers:
            criteria = {
                "match_tier": "Sector & Project Type Match",
                "sector": sector,
                "project_type": project_type,
                "cost_bracket_crores": "Unrestricted",
                "duration_bracket_months": "Unrestricted",
            }
            return tier2_peers, criteria

    # Tier 3: Sector Level Fallback
    if sector:
        tier3_mask = (base_pool["Sector"] == sector)
        tier3_peers = base_pool[tier3_mask]
        if len(tier3_peers) > 0:
            criteria = {
                "match_tier": "Sector Level Fallback",
                "sector": sector,
                "project_type": "All Types in Sector",
                "cost_bracket_crores": "Unrestricted",
                "duration_bracket_months": "Unrestricted",
            }
            return tier3_peers, criteria

    # Universal Fallback: All projects
    criteria = {
        "match_tier": "Universal Dataset Fallback",
        "sector": "All Sectors",
        "project_type": "All Types",
        "cost_bracket_crores": "Unrestricted",
        "duration_bracket_months": "Unrestricted",
    }
    return base_pool, criteria


def benchmark_project(
    project_record: Union[Dict[str, Any], pd.Series, pd.DataFrame],
    data_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compares a selected project against similar projects in projects.csv.

    Accepts:
        project_record: dict, Series, or single-row DataFrame.
        data_path: optional custom path to projects.csv.

    Returns:
        Structured dictionary with peer averages and factual comparisons:
        {
            "project_id": "...",
            "comparable_project_count": int,
            "similarity_criteria": { ... },
            "metrics": {
                "physical_progress": { "project": ..., "peer_average": ..., "difference": ... },
                ...
            },
            "peer_risk_distribution": { "low": ..., "medium": ..., "high": ... },
            "dataset_notice": "..."
        }
    """
    if isinstance(project_record, pd.DataFrame):
        record_dict = project_record.iloc[0].to_dict()
    elif isinstance(project_record, pd.Series):
        record_dict = project_record.to_dict()
    elif isinstance(project_record, dict):
        record_dict = dict(project_record)
    else:
        raise ValueError(f"Unsupported record format: {type(project_record)}. Expected dict, Series, or DataFrame.")

    df = load_benchmark_dataset(data_path)
    peers, criteria = _filter_comparable_peers(record_dict, df)

    # Compute selected project risk score if not in input
    project_risk_score = record_dict.get("Overall_Risk_Score", None)
    if project_risk_score is None:
        try:
            pred = predict_project_risk(record_dict)
            project_risk_score = pred["overall_risk_score"]
        except Exception:
            project_risk_score = None

    # Helper for factual metric comparison
    def _compute_metric_stat(key: str, project_val: Any, decimals: int = 1) -> Dict[str, Any]:
        p_val = float(project_val) if project_val is not None and not pd.isna(project_val) else None
        if key in peers.columns:
            peer_series = pd.to_numeric(peers[key], errors="coerce").dropna()
            peer_avg = round(float(peer_series.mean()), decimals) if len(peer_series) > 0 else None
            peer_med = round(float(peer_series.median()), decimals) if len(peer_series) > 0 else None
        else:
            peer_avg = None
            peer_med = None

        diff = round(p_val - peer_avg, decimals) if (p_val is not None and peer_avg is not None) else None

        return {
            "project": round(p_val, decimals) if p_val is not None else None,
            "peer_average": peer_avg,
            "peer_median": peer_med,
            "difference": diff,
        }

    # Extract comparison metrics
    metrics = {
        "physical_progress": _compute_metric_stat(
            "Physical_Progress", record_dict.get("Physical_Progress")
        ),
        "financial_progress": _compute_metric_stat(
            "Financial_Progress", record_dict.get("Financial_Progress")
        ),
        "procurement_delay_days": _compute_metric_stat(
            "Procurement_Delay_Days", record_dict.get("Procurement_Delay_Days")
        ),
        "average_milestone_delay_days": _compute_metric_stat(
            "Average_Milestone_Delay_Days", record_dict.get("Average_Milestone_Delay_Days")
        ),
        "milestones_delayed": _compute_metric_stat(
            "Milestones_Delayed", record_dict.get("Milestones_Delayed")
        ),
        "approvals_pending": _compute_metric_stat(
            "Approvals_Pending", record_dict.get("Approvals_Pending")
        ),
        "land_acquisition_progress": _compute_metric_stat(
            "Land_Acquisition_Progress", record_dict.get("Land_Acquisition_Progress")
        ),
    }

    # Include overall risk score comparison if available
    peer_scores = peers["_precomputed_overall_risk"].dropna()
    if len(peer_scores) > 0 and project_risk_score is not None:
        peer_avg_risk = round(float(peer_scores.mean()), 1)
        peer_med_risk = round(float(peer_scores.median()), 1)
        risk_diff = round(float(project_risk_score) - peer_avg_risk, 1)

        metrics["overall_risk_score"] = {
            "project": round(float(project_risk_score), 1),
            "peer_average": peer_avg_risk,
            "peer_median": peer_med_risk,
            "difference": risk_diff,
        }

        # Peer risk distribution
        low_count = int((peer_scores < 35.0).sum())
        med_count = int(((peer_scores >= 35.0) & (peer_scores < 65.0)).sum())
        high_count = int((peer_scores >= 65.0).sum())
        peer_risk_dist = {
            "low_risk_count": low_count,
            "medium_risk_count": med_count,
            "high_risk_count": high_count,
            "low_risk_pct": round((low_count / len(peer_scores)) * 100, 1),
            "medium_risk_pct": round((med_count / len(peer_scores)) * 100, 1),
            "high_risk_pct": round((high_count / len(peer_scores)) * 100, 1),
        }
    else:
        peer_risk_dist = None

    return {
        "project_id": record_dict.get("Project_ID", "UNKNOWN"),
        "sector": record_dict.get("Sector", "UNKNOWN"),
        "project_type": record_dict.get("Project_Type", "UNKNOWN"),
        "comparable_project_count": int(len(peers)),
        "similarity_criteria": criteria,
        "metrics": metrics,
        "peer_risk_distribution": peer_risk_dist,
        "dataset_notice": SYNTHETIC_DATASET_DISCLOSURE,
    }


# -------------------------------------------------------------
# CLI TESTING & VERIFICATION
# -------------------------------------------------------------

def run_benchmark_demo():
    print("=" * 75)
    print("OnTrack AI — Project Benchmarking Engine (Checkpoint 4)")
    print("Smart India Hackathon 2026 | Problem Statement: SIH26103")
    print("=" * 75)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "projects.csv")

    df = load_benchmark_dataset(data_path)

    # Test 3 distinct projects
    test_ids = ["PRJ-0001", "PRJ-0005", "PRJ-0004"]
    sample_df = df[df["Project_ID"].isin(test_ids)]

    print(f"\nEvaluating benchmarks for {len(sample_df)} representative projects:\n")

    for _, row in sample_df.iterrows():
        record = row.to_dict()
        bench = benchmark_project(record, data_path=data_path)

        print("━" * 75)
        print(f"BENCHMARK: {bench['project_id']} | {bench['sector']} / {bench['project_type']}")
        print(f"Matching Criteria: {bench['similarity_criteria']['match_tier']}")
        print(f"Comparable Peer Projects Found: {bench['comparable_project_count']}")
        print("━" * 75)

        m = bench["metrics"]
        print(f"{'Metric':<30} | {'Project':<10} | {'Peer Avg':<10} | {'Difference':<10}")
        print("-" * 68)

        metric_names = [
            ("Physical Progress (%)", "physical_progress"),
            ("Financial Progress (%)", "financial_progress"),
            ("Procurement Delay (Days)", "procurement_delay_days"),
            ("Average Milestone Delay (Days)", "average_milestone_delay_days"),
            ("Milestones Delayed", "milestones_delayed"),
            ("Pending Approvals", "approvals_pending"),
            ("Land Acquisition Progress (%)", "land_acquisition_progress"),
        ]

        if "overall_risk_score" in m:
            metric_names.append(("Overall Risk Score (0-100)", "overall_risk_score"))

        for display_name, key in metric_names:
            stat = m.get(key, {})
            p_val = f"{stat.get('project', 'N/A')}"
            peer_val = f"{stat.get('peer_average', 'N/A')}"
            diff_val = f"{stat.get('difference', 'N/A'):+}" if stat.get('difference') is not None else "N/A"
            print(f"{display_name:<30} | {p_val:<10} | {peer_val:<10} | {diff_val:<10}")

        if bench["peer_risk_distribution"]:
            dist = bench["peer_risk_distribution"]
            print(f"\nPeer Risk Breakdown: {dist['low_risk_count']} Low ({dist['low_risk_pct']}%) | "
                  f"{dist['medium_risk_count']} Med ({dist['medium_risk_pct']}%) | "
                  f"{dist['high_risk_count']} High ({dist['high_risk_pct']}%)")
        print()

    print("=" * 75)
    print("Benchmarking verification completed successfully.")
    print("=" * 75)


if __name__ == "__main__":
    run_benchmark_demo()
