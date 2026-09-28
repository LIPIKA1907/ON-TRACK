"""
OnTrack AI — Synthetic Infrastructure Project Dataset Generator
Smart India Hackathon 2026 | Problem Statement: SIH26103

Generates representative, realistic synthetic project-monitoring records
for infrastructure projects across sectors. Uses Python standard library
for 100% dependency-free reproducibility.
"""

import os
import math
import random
import csv
import statistics
from collections import Counter


def clip(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min_val and max_val."""
    return max(min_val, min(value, max_val))


def generate_synthetic_data(n_samples: int = 1000, seed: int = 42) -> list:
    """
    Generate representative synthetic infrastructure project monitoring dataset.
    Calibrated against empirical infrastructure dynamics where ~35-40% of projects
    experience meaningful schedule slippages and ~30-35% experience cost overruns.
    
    Parameters:
        n_samples (int): Number of project records to generate. Default 1000.
        seed (int): Fixed random seed for strict reproducibility. Default 42.
        
    Returns:
        list of dict: List of project dictionaries.
    """
    random.seed(seed)

    sectors = [
        "Transport",
        "Energy",
        "Water",
        "Urban Development",
        "Health",
        "Education",
    ]
    sector_weights = [0.35, 0.20, 0.15, 0.14, 0.08, 0.08]

    sector_type_map = {
        "Transport": (["Road", "Railway", "Bridge"], [0.50, 0.30, 0.20]),
        "Energy": (["Power"], [1.0]),
        "Water": (["Water Supply"], [1.0]),
        "Urban Development": (["Urban Infrastructure"], [1.0]),
        "Health": (["Hospital"], [1.0]),
        "Education": (["School"], [1.0]),
    }

    records = []

    for i in range(n_samples):
        project_id = f"PRJ-{i+1:04d}"

        # 1. Sector and Project Type
        sector = random.choices(sectors, weights=sector_weights, k=1)[0]
        types, type_weights = sector_type_map[sector]
        project_type = random.choices(types, weights=type_weights, k=1)[0]

        # 2. Approved Cost (₹ Crores) & Planned Duration (Months)
        if project_type == "Railway":
            approved_cost = round(random.uniform(400.0, 4500.0), 2)
            planned_duration = random.randint(36, 72)
        elif project_type == "Bridge":
            approved_cost = round(random.uniform(150.0, 1800.0), 2)
            planned_duration = random.randint(24, 60)
        elif project_type == "Road":
            approved_cost = round(random.uniform(100.0, 2200.0), 2)
            planned_duration = random.randint(18, 48)
        elif project_type == "Power":
            approved_cost = round(random.uniform(300.0, 4000.0), 2)
            planned_duration = random.randint(30, 66)
        elif project_type == "Water Supply":
            approved_cost = round(random.uniform(50.0, 1100.0), 2)
            planned_duration = random.randint(18, 42)
        elif project_type == "Urban Infrastructure":
            approved_cost = round(random.uniform(80.0, 1500.0), 2)
            planned_duration = random.randint(18, 48)
        elif project_type == "Hospital":
            approved_cost = round(random.uniform(70.0, 850.0), 2)
            planned_duration = random.randint(18, 42)
        else:  # School
            approved_cost = round(random.uniform(20.0, 300.0), 2)
            planned_duration = random.randint(12, 30)

        # 3. Lifecycle Stage: Elapsed Duration (Months)
        lifecycle_ratio = random.uniform(0.20, 1.05)
        elapsed_duration = int(round(planned_duration * lifecycle_ratio))
        elapsed_duration = int(clip(elapsed_duration, 1, planned_duration + 12))

        # 4. Planned Progress (%)
        linear_expected = (elapsed_duration / planned_duration) * 100.0
        planned_progress = clip(round(linear_expected + random.gauss(0.0, 2.0), 1), 5.0, 100.0)

        # 5. Friction & Operational Bottlenecks
        # Approvals pending (0 to 5) - most projects have 0 to 1
        approvals_pending = random.choices([0, 1, 2, 3, 4, 5], weights=[0.50, 0.25, 0.13, 0.07, 0.03, 0.02], k=1)[0]

        # Scope changes (0 to 4) - most projects have 0 to 1
        scope_changes = random.choices([0, 1, 2, 3, 4], weights=[0.55, 0.25, 0.12, 0.05, 0.03], k=1)[0]

        # Contractor Performance
        contractor_perf = random.choices(["Good", "Average", "Poor"], weights=[0.55, 0.32, 0.13], k=1)[0]
        perf_score = 0.0 if contractor_perf == "Good" else (0.5 if contractor_perf == "Average" else 1.2)

        # Procurement Delay (Days)
        # ~60% of projects experience on-time or minimal procurement (0-10 days), ~40% face longer delays
        if random.random() < 0.40:
            procurement_delay = int(round(random.expovariate(1.0 / 40.0)))
            procurement_delay = int(clip(procurement_delay, 5, 150))
        else:
            procurement_delay = int(random.randint(0, 10))

        # Land Acquisition Progress (%)
        if sector in ["Health", "Education"]:
            land_acq = round(random.uniform(90.0, 100.0), 1)
        else:
            # Linear & urban infrastructure: majority achieve decent land acquisition, minority struggle
            if random.random() < 0.70:
                land_acq = round(random.uniform(75.0, 100.0), 1)
            else:
                land_acq = round(random.uniform(25.0, 74.0), 1)
        land_acq = clip(land_acq, 15.0, 100.0)

        # 6. Milestone Tracking
        milestones_total = random.randint(6, 25)
        # Delay probability conditioned on friction
        base_delay_prob = 0.06 + 0.15 * perf_score + 0.04 * approvals_pending + 0.0015 * procurement_delay
        delay_prob = clip(base_delay_prob + random.gauss(0.0, 0.04), 0.02, 0.80)
        milestones_delayed = sum(1 for _ in range(milestones_total) if random.random() < delay_prob)

        if milestones_delayed > 0:
            avg_delay = round(
                random.uniform(10.0, 35.0) * (1.0 + perf_score) +
                0.25 * procurement_delay +
                approvals_pending * 3.0 +
                random.gauss(0.0, 4.0),
                1
            )
            avg_delay = clip(avg_delay, 5.0, 200.0)
        else:
            avg_delay = 0.0

        # 7. Physical Progress (%) & Slippage
        # In a healthy project, slippage is near 0 or slight lead (-2% to +2%).
        # Under friction, slippage grows with delayed milestones and unresolved issues.
        milestone_ratio = milestones_delayed / milestones_total
        ground_friction = (
            milestone_ratio * 12.0 +
            (avg_delay / 30.0) * 1.6 +
            (100.0 - land_acq) * 0.08 +
            approvals_pending * 1.2 +
            perf_score * 3.0 +
            random.gauss(-1.5, 2.0)
        )
        slippage = max(-3.0, ground_friction)
        physical_progress = clip(round(planned_progress - slippage, 1), 2.0, 100.0)

        # 8. Financial Progress (%) & Expenditure (₹ Crores)
        # Financial progress closely aligns with physical progress (+/- a few percent for mobilization/retention)
        fin_progress = clip(round(physical_progress + random.gauss(0.5, 2.5), 1), 1.0, 100.0)
        expenditure = round(approved_cost * (fin_progress / 100.0) * random.uniform(0.98, 1.04), 2)
        expenditure = max(expenditure, 0.1)

        # -------------------------------------------------------------
        # TARGET VARIABLE SYNTHESIS (Realistic, Stochastic, Balanced)
        # -------------------------------------------------------------

        # A. Time Overrun (Months and Flag)
        # Latent risk index: when low, overrun is zero; when high, delay scales up.
        time_risk_index = (
            (planned_progress - physical_progress) * 0.35 +
            (avg_delay / 30.0) * 1.4 +
            (procurement_delay / 30.0) * 0.7 +
            approvals_pending * 0.9 +
            (100.0 - land_acq) * 0.05 +
            scope_changes * 1.1 +
            (perf_score - 0.4) * 2.8 +
            random.gauss(-4.0, 2.0)
        )

        if time_risk_index <= 0.0:
            time_overrun_months = 0.0
        else:
            time_overrun_months = clip(round(time_risk_index * 1.10, 1), 0.0, 36.0)

        # Time Overrun Flag:
        # Standard threshold: schedule delay >= 3.0 months triggers formal overrun flag
        # Sigmoid centered at 3.2 months with boundary blur
        if time_overrun_months == 0.0:
            time_overrun_flag = 0
        else:
            p_time = 1.0 / (1.0 + math.exp(-(time_overrun_months - 3.2) / 1.0))
            time_overrun_flag = 1 if random.random() < p_time else 0

        # B. Cost Overrun (Pct and Flag)
        # Driven by time overrun (escalation/IDC), scope revisions, procurement friction, contractor performance
        cost_risk_index = (
            time_overrun_months * 0.75 +
            scope_changes * 2.5 +
            (procurement_delay / 30.0) * 1.0 +
            approvals_pending * 0.6 +
            (100.0 - land_acq) * 0.04 +
            (perf_score - 0.3) * 3.0 +
            random.gauss(-4.2, 2.0)
        )

        if cost_risk_index <= 0.0:
            cost_overrun_pct = 0.0
        else:
            cost_overrun_pct = clip(round(cost_risk_index * 1.20, 1), 0.0, 50.0)

        # Cost Overrun Flag:
        # Standard threshold: budget escalation >= 5.0%
        if cost_overrun_pct == 0.0:
            cost_overrun_flag = 0
        else:
            p_cost = 1.0 / (1.0 + math.exp(-(cost_overrun_pct - 5.0) / 1.2))
            cost_overrun_flag = 1 if random.random() < p_cost else 0

        # C. Implementation Risk Flag
        # Composite operational risk representing high-stress projects
        composite_risk_score = (
            0.32 * (time_overrun_months / 8.0) +
            0.28 * (cost_overrun_pct / 10.0) +
            0.18 * (milestones_delayed / milestones_total) +
            0.12 * (approvals_pending / 3.0) +
            0.10 * perf_score +
            random.gauss(-0.35, 0.18)
        )
        p_impl = 1.0 / (1.0 + math.exp(-(composite_risk_score - 0.28) / 0.15))
        impl_risk_flag = 1 if random.random() < p_impl else 0

        records.append({
            "Project_ID": project_id,
            "Sector": sector,
            "Project_Type": project_type,
            "Approved_Cost": approved_cost,
            "Planned_Duration": planned_duration,
            "Elapsed_Duration": elapsed_duration,
            "Physical_Progress": physical_progress,
            "Planned_Progress": planned_progress,
            "Financial_Progress": fin_progress,
            "Expenditure": expenditure,
            "Milestones_Total": milestones_total,
            "Milestones_Delayed": milestones_delayed,
            "Average_Milestone_Delay_Days": avg_delay,
            "Procurement_Delay_Days": procurement_delay,
            "Land_Acquisition_Progress": land_acq,
            "Approvals_Pending": approvals_pending,
            "Scope_Changes": scope_changes,
            "Contractor_Performance": contractor_perf,
            "Time_Overrun_Months": time_overrun_months,
            "Cost_Overrun_Pct": cost_overrun_pct,
            "Time_Overrun_Flag": time_overrun_flag,
            "Cost_Overrun_Flag": cost_overrun_flag,
            "Implementation_Risk_Flag": impl_risk_flag,
        })

    return records


def introduce_missing_data(records: list, seed: int = 143) -> list:
    """
    Introduce realistic missing values in selected input fields.
    Targets and core identifiers strictly remain non-empty.
    """
    random.seed(seed)
    modified = []

    for r in records:
        rec = dict(r)

        # 1. Average_Milestone_Delay_Days: ~3.0% missing
        if random.random() < 0.030:
            rec["Average_Milestone_Delay_Days"] = ""

        # 2. Procurement_Delay_Days: ~2.5% missing
        if random.random() < 0.025:
            rec["Procurement_Delay_Days"] = ""

        # 3. Land_Acquisition_Progress: ~2.0% missing
        if random.random() < 0.020:
            rec["Land_Acquisition_Progress"] = ""

        # 4. Contractor_Performance: ~2.0% missing
        if random.random() < 0.020:
            rec["Contractor_Performance"] = ""

        modified.append(rec)

    return modified


def validate_records(records: list) -> list:
    """Validate data integrity and business logic constraints."""
    errors = []

    if len(records) != 1000:
        errors.append(f"Expected 1000 records, got {len(records)}.")

    target_fields = [
        "Time_Overrun_Months",
        "Cost_Overrun_Pct",
        "Time_Overrun_Flag",
        "Cost_Overrun_Flag",
        "Implementation_Risk_Flag",
    ]

    for idx, r in enumerate(records):
        # Target completeness
        for tf in target_fields:
            if r[tf] == "" or r[tf] is None:
                errors.append(f"Row {idx+1}: Target {tf} is missing.")

        # Positive costs and durations
        if float(r["Approved_Cost"]) <= 0:
            errors.append(f"Row {idx+1}: Approved_Cost is non-positive.")
        if int(r["Planned_Duration"]) <= 0:
            errors.append(f"Row {idx+1}: Planned_Duration is non-positive.")
        if int(r["Elapsed_Duration"]) <= 0:
            errors.append(f"Row {idx+1}: Elapsed_Duration is non-positive.")
        if float(r["Expenditure"]) <= 0:
            errors.append(f"Row {idx+1}: Expenditure is non-positive.")

        # Progress ranges
        for pf in ["Physical_Progress", "Planned_Progress", "Financial_Progress"]:
            v = float(r[pf])
            if v < 0 or v > 100:
                errors.append(f"Row {idx+1}: {pf}={v} is out of [0, 100].")

        # Milestone consistency
        m_tot = int(r["Milestones_Total"])
        m_del = int(r["Milestones_Delayed"])
        if m_del < 0 or m_del > m_tot:
            errors.append(f"Row {idx+1}: Invalid milestones ({m_del} delayed of {m_tot}).")

    return errors


def calculate_summary(records: list) -> dict:
    """Calculate summary statistics without external dependencies."""
    n = len(records)
    fields = list(records[0].keys())

    missing_counts = {}
    for f in fields:
        missing_counts[f] = sum(1 for r in records if r[f] == "" or r[f] is None)

    # Target distributions
    flag_dist = {}
    for flag in ["Time_Overrun_Flag", "Cost_Overrun_Flag", "Implementation_Risk_Flag"]:
        counts = Counter(int(r[flag]) for r in records)
        flag_dist[flag] = {
            0: counts[0],
            1: counts[1],
            "pct_0": round((counts[0] / n) * 100, 2),
            "pct_1": round((counts[1] / n) * 100, 2),
        }

    # Continuous targets
    time_overrun = [float(r["Time_Overrun_Months"]) for r in records]
    cost_overrun = [float(r["Cost_Overrun_Pct"]) for r in records]

    continuous_stats = {
        "Time_Overrun_Months": {
            "mean": round(statistics.mean(time_overrun), 2),
            "std": round(statistics.stdev(time_overrun), 2),
            "min": round(min(time_overrun), 2),
            "median": round(statistics.median(time_overrun), 2),
            "max": round(max(time_overrun), 2),
        },
        "Cost_Overrun_Pct": {
            "mean": round(statistics.mean(cost_overrun), 2),
            "std": round(statistics.stdev(cost_overrun), 2),
            "min": round(min(cost_overrun), 2),
            "median": round(statistics.median(cost_overrun), 2),
            "max": round(max(cost_overrun), 2),
        }
    }

    # Key numerical input feature stats
    numeric_features = [
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

    feature_stats = {}
    for f in numeric_features:
        vals = [float(r[f]) for r in records if r[f] != "" and r[f] is not None]
        if vals:
            feature_stats[f] = {
                "mean": round(statistics.mean(vals), 2),
                "std": round(statistics.stdev(vals), 2),
                "min": round(min(vals), 2),
                "median": round(statistics.median(vals), 2),
                "max": round(max(vals), 2),
            }

    return {
        "n_rows": n,
        "n_cols": len(fields),
        "fields": fields,
        "missing_counts": missing_counts,
        "flag_dist": flag_dist,
        "continuous_stats": continuous_stats,
        "feature_stats": feature_stats,
    }


def main():
    print("=" * 65)
    print("OnTrack AI — Synthetic Dataset Generator (Checkpoint 1)")
    print("Smart India Hackathon 2026 | Problem Statement: SIH26103")
    print("=" * 65)

    # 1. Generate base dataset
    print("\n[1/4] Generating 1,000 synthetic infrastructure records (seed=42)...")
    records_raw = generate_synthetic_data(n_samples=1000, seed=42)

    # 2. Add realistic missing values
    print("[2/4] Introducing realistic missing values into selected input fields...")
    records_final = introduce_missing_data(records_raw, seed=143)

    # 3. Validate
    print("[3/4] Validating records against physical & logical constraints...")
    errors = validate_records(records_final)
    if errors:
        print("Validation FAILED with errors:")
        for err in errors[:10]:
            print(f"  - {err}")
        raise ValueError(f"Encountered {len(errors)} validation errors.")
    print("  -> Validation PASSED successfully! All records conform to business logic.")

    # 4. Save to CSV
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "projects.csv")

    fieldnames = list(records_final[0].keys())
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records_final)

    print(f"[4/4] Saved dataset successfully to:\n      {os.path.abspath(csv_path)}")

    # 5. Output Summary
    summary = calculate_summary(records_final)
    print("\n" + "=" * 65)
    print("DATASET VALIDATION & STATISTICAL SUMMARY")
    print("=" * 65)
    print(f"Total Rows:    {summary['n_rows']}")
    print(f"Total Columns: {summary['n_cols']}")

    print("\n--- Missing Values per Column ---")
    for f in summary["fields"]:
        cnt = summary["missing_counts"][f]
        pct = (cnt / summary['n_rows']) * 100
        print(f"  {f:30s}: {cnt:3d} missing ({pct:.1f}%)")

    print("\n--- Target Distributions (Binary Flags) ---")
    for flag, d in summary["flag_dist"].items():
        print(f"  {flag:26s}: Class 0: {d[0]:3d} ({d['pct_0']:5.2f}%) | Class 1: {d[1]:3d} ({d['pct_1']:5.2f}%)")

    print("\n--- Continuous Target Metrics ---")
    for tgt, st in summary["continuous_stats"].items():
        print(f"  {tgt:22s}: Mean={st['mean']:5.2f}, Std={st['std']:5.2f}, Min={st['min']:5.2f}, Median={st['median']:5.2f}, Max={st['max']:5.2f}")

    print("\n--- Key Input Feature Summary ---")
    for feat, st in summary["feature_stats"].items():
        print(f"  {feat:30s}: Mean={st['mean']:7.2f}, Median={st['median']:7.2f}, Range=[{st['min']:6.2f}, {st['max']:6.2f}]")

    print("=" * 65)
    print("Checkpoint 1 dataset generation completed successfully.")


if __name__ == "__main__":
    main()
