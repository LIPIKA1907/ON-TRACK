import sys
import json

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

def run_tests():
    print("=" * 70)
    print("RUNNING COMPLETE ONTRACK AI VERIFICATION SUITE")
    print("=" * 70)

    # 1. Health check
    h = health_check()
    print("[1] Health Check:", h)
    assert h["status"] == "ok"
    assert h["paimana_status"] == "CONNECTED"

    # 2. Data sources
    s = get_data_sources()
    print(f"[2] Sources ({len(s['sources'])}):", [src["name"] for src in s["sources"]])

    # 3. GET /projects?source=synthetic
    synth_res = get_projects(source="synthetic")
    print(f"[3] Synthetic Projects: {synth_res['count']} projects | Source: {synth_res['source_name']}")
    assert synth_res["success"] is True
    assert synth_res["count"] > 0
    synth_sample = synth_res["projects"][0]

    # 4. GET /projects?source=sih
    sih_res = get_projects(source="sih")
    print(f"[4] SIH / PAIMANA Projects: {sih_res['count']} projects | Source: {sih_res['source_name']}")
    assert sih_res["success"] is True
    assert sih_res["count"] == 1731
    paimana_sample = sih_res["projects"][0]
    print(f"    Sample PAIMANA project: {paimana_sample['Project_ID']} — {paimana_sample['Project_Name']}")
    print(f"    Ministry: {paimana_sample['Line_Ministry']} | Agency: {paimana_sample['Executing_Agency']}")

    # 5. Predict on Synthetic & PAIMANA
    p_synth = predict_risk(ProjectRequest(project=synth_sample))
    print(f"[5a] Predict (Synthetic PRJ-0001): Overall Risk = {p_synth['result']['overall_risk_score']} ({p_synth['result']['risk_level']})")
    
    p_sih = predict_risk(ProjectRequest(project=paimana_sample))
    print(f"[5b] Predict (PAIMANA {paimana_sample['Project_ID']}): Overall Risk = {p_sih['result']['overall_risk_score']} ({p_sih['result']['risk_level']})")
    assert p_sih["success"] is True

    # 6. Explain on Synthetic & PAIMANA
    exp_synth = explain_risk(ProjectRequest(project=synth_sample))
    print(f"[6a] Explain (Synthetic): Top time drivers: {len(exp_synth['result']['time_overrun']['top_risk_factors'])}")

    exp_sih = explain_risk(ProjectRequest(project=paimana_sample))
    print(f"[6b] Explain (PAIMANA): Result obtained successfully (Fallback={exp_sih['result']['time_overrun'].get('fallback', False)})")
    assert exp_sih["success"] is True

    # 7. Benchmark on Synthetic & PAIMANA
    b_synth = benchmark(ProjectRequest(project=synth_sample))
    print(f"[7a] Benchmark (Synthetic): {b_synth['result']['comparable_project_count']} peers found.")

    b_sih = benchmark(ProjectRequest(project=paimana_sample))
    print(f"[7b] Benchmark (PAIMANA): {b_sih['result']['comparable_project_count']} peers found across PAIMANA database.")
    assert b_sih["success"] is True
    assert b_sih["result"]["comparable_project_count"] > 0

    # 8. What-If Simulation
    w_synth = what_if(WhatIfRequest(project=synth_sample, modifications={"Approvals_Pending": 0}))
    print(f"[8a] What-If (Synthetic): Risk delta = {w_synth['result']['deltas']['overall_risk_score_delta']}")

    w_sih = what_if(WhatIfRequest(project=paimana_sample, modifications={"Physical_Progress": 85.0}))
    print(f"[8b] What-If (PAIMANA in-memory simulation): Risk delta = {w_sih['result']['deltas']['overall_risk_score_delta']}")
    assert w_sih["success"] is True

    # 9. Early Warning
    ew_synth = early_warning(ProjectRequest(project=synth_sample))
    print(f"[9a] Early Warning (Synthetic): Level = {ew_synth['result']['warning_level']}, Signals = {len(ew_synth['result']['warnings'])}")

    ew_sih = early_warning(ProjectRequest(project=paimana_sample))
    print(f"[9b] Early Warning (PAIMANA): Level = {ew_sih['result']['warning_level']}, Signals = {len(ew_sih['result']['warnings'])}")
    print(f"     Signals: {ew_sih['result']['warnings']}")
    assert ew_sih["success"] is True

    # 10. Recommendations
    rec_synth = recommendations(ProjectRequest(project=synth_sample))
    print(f"[10a] Recommendations (Synthetic): {len(rec_synth['result'])} items")

    rec_sih = recommendations(ProjectRequest(project=paimana_sample))
    print(f"[10b] Recommendations (PAIMANA): {len(rec_sih['result'])} items")
    assert rec_sih["success"] is True

    print("\n" + "=" * 70)
    print("ALL VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
