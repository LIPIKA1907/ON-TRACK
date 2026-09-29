"""
Comprehensive verification of official SIH26103 MoSPI PAIMANA dataset integration.
Verifies all 6 conditions:
1. Actual PAIMANA records are loaded
2. Project names and IDs come from PAIMANA
3. No synthetic records are used in PAIMANA mode
4. Backend returns PAIMANA data
5. Predictions, explanations, benchmarking, what-if, early warnings, recommendations work
6. Existing OnTrack functionality remains working
"""

import sys
import json
import pandas as pd
from pathlib import Path

from backend.paimana_service import paimana_service
from backend.main import (
    health_check,
    get_data_sources,
    get_projects,
    predict_risk,
    explain_risk,
    benchmark,
    what_if,
    recommendations,
    early_warning,
    ProjectRequest,
    WhatIfRequest,
)

def verify():
    print("=" * 80)
    print("VERIFYING OFFICIAL SIH26103 / MoSPI PAIMANA DATA INTEGRATION")
    print("=" * 80)

    # CHECK 1: File integrity
    raw_path = Path("data/paimana/paimana_raw_projects.json")
    norm_path = Path("data/paimana/paimana_normalized.csv")
    csv_path = Path("data/paimana/paimana_projects.csv")

    assert raw_path.exists(), f"Missing {raw_path}"
    assert norm_path.exists(), f"Missing {norm_path}"
    assert csv_path.exists(), f"Missing {csv_path}"

    with raw_path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)
    print(f"[CHECK 1] Raw PAIMANA JSON: {len(raw_data)} projects directly from MoSPI feed.")
    assert len(raw_data) == 1731, f"Expected 1731, got {len(raw_data)}"

    # CHECK 2: Normalized dataset
    norm_df = pd.read_csv(norm_path)
    print(f"[CHECK 2] Normalized PAIMANA CSV: {len(norm_df)} rows, {len(norm_df.columns)} columns.")
    assert len(norm_df) == 1731

    # CHECK 3: Project names & IDs are real MoSPI records
    sample_ids = norm_df["Project_ID"].head(5).tolist()
    sample_names = norm_df["Project_Name"].head(5).tolist()
    sample_ministries = norm_df["Line_Ministry"].head(5).tolist()
    print(f"[CHECK 3] Sample Real PAIMANA Records:")
    for pid, name, min_name in zip(sample_ids, sample_names, sample_ministries):
        print(f"   - {pid}: '{name}' ({min_name})")
        assert pid.startswith("PAIMANA-"), f"Invalid ID prefix: {pid}"
        assert len(name) > 3, f"Invalid project name: {name}"

    # CHECK 4: Zero synthetic records mixed into PAIMANA
    synthetic_in_paimana = norm_df[norm_df["Project_ID"].str.startswith("PRJ-", na=False)]
    print(f"[CHECK 4] Synthetic records found in PAIMANA dataset: {len(synthetic_in_paimana)}")
    assert len(synthetic_in_paimana) == 0, "ERROR: Synthetic records found in PAIMANA dataset!"

    # CHECK 5: Non-fabricated unrecorded operational metrics
    null_milestones = norm_df["Milestones_Total"].isna().sum()
    null_approvals = norm_df["Approvals_Pending"].isna().sum()
    null_contractor = norm_df["Contractor_Performance"].isna().sum()
    print(f"[CHECK 5] Unrecorded operational fields correctly preserved as null (no fabrication):")
    print(f"   - Milestones_Total nulls: {null_milestones} / 1731 ({null_milestones/1731*100:.1f}%)")
    print(f"   - Approvals_Pending nulls: {null_approvals} / 1731 ({null_approvals/1731*100:.1f}%)")
    print(f"   - Contractor_Performance nulls: {null_contractor} / 1731 ({null_contractor/1731*100:.1f}%)")
    assert null_milestones == 1731
    assert null_approvals == 1731

    # CHECK 6: Backend endpoint GET /projects returns PAIMANA by default
    default_res = get_projects()
    print(f"[CHECK 6] Backend default GET /projects:")
    print(f"   - Source: {default_res['source']} ({default_res['source_name']})")
    print(f"   - Is synthetic: {default_res['is_synthetic']}")
    print(f"   - Project count: {default_res['count']}")
    assert default_res["source"] == "sih"
    assert default_res["is_synthetic"] is False
    assert default_res["count"] == 1731

    # CHECK 7: Health & Sources endpoints
    h = health_check()
    print(f"[CHECK 7] Health check: status={h['status']}, paimana_status={h['paimana_status']}")
    assert h["status"] == "ok"
    assert h["paimana_status"] == "CONNECTED"

    # CHECK 8: Risk prediction on sample PAIMANA project
    paimana_proj = default_res["projects"][0]
    p_req = ProjectRequest(project=paimana_proj)
    p_res = predict_risk(p_req)
    print(f"[CHECK 8] Prediction for {paimana_proj['Project_ID']} ('{paimana_proj['Project_Name']}'):")
    print(f"   - Risk Level: {p_res['result']['risk_level']}")
    print(f"   - Overall Score: {p_res['result']['overall_risk_score']}")
    print(f"   - Probabilities: Time={p_res['result']['time_risk_probability']}, Cost={p_res['result']['cost_risk_probability']}")
    assert p_res["success"] is True

    # CHECK 9: Explainability on PAIMANA project
    exp_res = explain_risk(p_req)
    print(f"[CHECK 9] Explainability for {paimana_proj['Project_ID']}:")
    print(f"   - Top Time Drivers: {[f['feature'] for f in exp_res['result']['time_overrun']['top_risk_factors']]}")
    assert exp_res["success"] is True

    # CHECK 10: Benchmark on PAIMANA project against PAIMANA database
    b_res = benchmark(p_req)
    print(f"[CHECK 10] Peer Benchmark for {paimana_proj['Project_ID']}:")
    print(f"   - Peer Count: {b_res['result']['comparable_project_count']} peers from PAIMANA")
    print(f"   - Source: {b_res['result']['source']}")
    print(f"   - Notice: {b_res['result']['dataset_notice'][:65]}...")
    assert b_res["success"] is True
    assert b_res["result"]["source"] == "sih"

    # CHECK 11: Early Warning on PAIMANA project
    ew_res = early_warning(p_req)
    print(f"[CHECK 11] Early Warnings for {paimana_proj['Project_ID']}:")
    print(f"   - Warning Level: {ew_res['result']['warning_level']}")
    print(f"   - Warning Signals: {ew_res['result']['warnings']}")
    assert ew_res["success"] is True

    # CHECK 12: Recommendations on PAIMANA project
    rec_res = recommendations(p_req)
    print(f"[CHECK 12] Action Recommendations for {paimana_proj['Project_ID']}:")
    print(f"   - Recommendations: {len(rec_res['result'])} items")
    assert rec_res["success"] is True

    # CHECK 13: Scenario Analysis / What-If on PAIMANA project
    wi_req = WhatIfRequest(project=paimana_proj, modifications={"Physical_Progress": 90.0})
    wi_res = what_if(wi_req)
    print(f"[CHECK 13] Scenario Simulation (Physical_Progress -> 90%):")
    print(f"   - Baseline Score: {wi_res['result']['original_prediction']['overall_risk_score']}")
    print(f"   - Simulated Score: {wi_res['result']['scenario_prediction']['overall_risk_score']}")
    print(f"   - Delta: {wi_res['result']['deltas']['overall_risk_score_delta']}")
    assert wi_res["success"] is True

    # CHECK 14: Existing Synthetic Mode Still Operates via ?source=synthetic
    synth_res = get_projects(source="synthetic")
    print(f"[CHECK 14] Synthetic Mode on Demand:")
    print(f"   - Count: {synth_res['count']}, First ID: {synth_res['projects'][0]['Project_ID']}")
    assert synth_res["source"] == "synthetic"
    assert synth_res["projects"][0]["Project_ID"] == "PRJ-0001"

    print("\n" + "=" * 80)
    print("ALL 14 INTEGRATION VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 80)

if __name__ == "__main__":
    verify()
