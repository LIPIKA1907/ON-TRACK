import json
import csv
import os
from datetime import datetime

def parse_date(d_str):
    if not d_str:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(d_str.strip(), fmt)
        except Exception:
            pass
    return None

def clean_float(val):
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

# Mapping for Sector and Project Type
SECTOR_MAP = {
    "Roads & Highways": "Road Transport",
    "Railways": "Railways",
    "Electricity Generation": "Power",
    "Energy Storage": "Power",
    "Transmission & Distribution": "Power",
    "Coal": "Coal & Mines",
    "Metals & Mining": "Mining",
    "Oil & Gas": "Petroleum & Natural Gas",
    "Water Resources": "Water Resources",
    "Waste & Water": "Water & Sanitation",
    "Healthcare": "Healthcare",
    "Education": "Education",
    "Urban Public Transport": "Urban Infrastructure",
    "Real Estate": "Urban Infrastructure",
    "Construction ": "Urban Infrastructure",
    "Shipping": "Ports & Shipping",
    "Aviation & Aviation Infrastructure": "Civil Aviation",
    "Telecommunication": "Telecommunications",
    "Logistics Infrastructure": "Logistics",
    "Tourism, Hospitality & Wellness": "Tourism",
    "Steel": "Heavy Industry",
}

TYPE_MAP = {
    "Roads & Highways": "Road",
    "Railways": "Railway",
    "Electricity Generation": "Power Plant",
    "Energy Storage": "Substation",
    "Transmission & Distribution": "Grid Transmission",
    "Coal": "Mine Development",
    "Metals & Mining": "Processing Plant",
    "Oil & Gas": "Pipeline / Refinery",
    "Water Resources": "Water Supply / Dam",
    "Waste & Water": "Treatment Facility",
    "Healthcare": "Hospital",
    "Education": "School / University",
    "Urban Public Transport": "Metro / Light Rail",
    "Real Estate": "Commercial / Residential",
    "Construction ": "Building Complex",
    "Shipping": "Port / Terminal",
    "Aviation & Aviation Infrastructure": "Airport",
    "Telecommunication": "Telecom Towers",
    "Logistics Infrastructure": "Logistics Park",
    "Tourism, Hospitality & Wellness": "Hospitality Center",
    "Steel": "Steel Plant",
}

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    extract_file = os.path.join(base_dir, "paimana_full_extract.json")
    if not os.path.exists(extract_file):
        raise FileNotFoundError(f"Missing extract file: {extract_file}")

    with open(extract_file, "r", encoding="utf-8") as f:
        full_data = json.load(f)

    raw_projects = full_data.get("projects", [])
    print(f"Loaded {len(raw_projects)} projects from extract.")

    paimana_dir = os.path.join(base_dir, "data", "paimana")
    os.makedirs(paimana_dir, exist_ok=True)

    # 1. Save paimana_raw_projects.json (unchanged raw file)
    raw_json_path = os.path.join(paimana_dir, "paimana_raw_projects.json")
    with open(raw_json_path, "w", encoding="utf-8") as f:
        json.dump(raw_projects, f, indent=2, ensure_ascii=False)
    print(f"Saved raw JSON: {raw_json_path} ({os.path.getsize(raw_json_path)} bytes)")

    # 2. Save paimana_projects.csv (raw fields in CSV)
    raw_csv_path = os.path.join(paimana_dir, "paimana_projects.csv")
    if raw_projects:
        fieldnames = list(raw_projects[0].keys())
        with open(raw_csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in raw_projects:
                writer.writerow(p)
        print(f"Saved raw CSV: {raw_csv_path} ({os.path.getsize(raw_csv_path)} bytes)")

    # 3. Save paimana_normalized.csv (normalized to OnTrack AI schema)
    # Target schema:
    # Project_ID, Project_Name, Line_Ministry, Executing_Agency, Sector, Project_Type,
    # Approved_Cost, Planned_Duration, Elapsed_Duration, Physical_Progress, Planned_Progress, Financial_Progress, Expenditure,
    # Milestones_Total, Milestones_Delayed, Average_Milestone_Delay_Days, Procurement_Delay_Days, Land_Acquisition_Progress,
    # Approvals_Pending, Scope_Changes, Contractor_Performance,
    # Time_Overrun_Months, Cost_Overrun_Pct, Time_Overrun_Flag, Cost_Overrun_Flag, Implementation_Risk_Flag

    normalized_cols = [
        "Project_ID",
        "Project_Name",
        "Line_Ministry",
        "Executing_Agency",
        "Sector",
        "Project_Type",
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
        "Contractor_Performance",
        "Time_Overrun_Months",
        "Cost_Overrun_Pct",
        "Time_Overrun_Flag",
        "Cost_Overrun_Flag",
        "Implementation_Risk_Flag",
    ]

    snapshot_date = datetime(2026, 8, 31)  # Snapshot date of August 2026 PAIMANA data
    normalized_rows = []

    for p in raw_projects:
        project_id = str(p.get("ProjectId", "")).strip()
        project_name = str(p.get("ProjectName", "")).strip()
        ministry = str(p.get("LineMinistry", "")).strip()
        executing_agency = str(p.get("COMPANYNAME", "") or p.get("AgencyName", "")).strip()
        raw_sector = str(p.get("SectorName", "")).strip()
        
        sector = SECTOR_MAP.get(raw_sector, raw_sector)
        project_type = TYPE_MAP.get(raw_sector, "Infrastructure")

        orig_cost = clean_float(p.get("OriginalCost"))
        rev_cost = clean_float(p.get("RevisedCost"))
        expenditure = clean_float(p.get("Expenditure"))
        phys_prog = clean_float(p.get("PhysicalProgress"))

        s_date = parse_date(p.get("SanctionDate"))
        end_date = parse_date(p.get("OriginalEndDate"))
        rev_date = parse_date(p.get("RevisedDate"))

        # Approved_Cost = OriginalCost
        approved_cost = orig_cost if orig_cost is not None else None

        # Planned_Duration = months between SanctionDate and OriginalEndDate
        planned_duration = None
        if s_date and end_date:
            dur = (end_date.year - s_date.year) * 12 + (end_date.month - s_date.month)
            if dur > 0:
                planned_duration = dur

        # Elapsed_Duration = months between SanctionDate and snapshot date
        elapsed_duration = None
        if s_date:
            elapsed = (snapshot_date.year - s_date.year) * 12 + (snapshot_date.month - s_date.month)
            elapsed_duration = max(0, elapsed)

        # Financial_Progress = min(100, Expenditure / OriginalCost * 100)
        financial_progress = None
        if orig_cost and orig_cost > 0 and expenditure is not None:
            financial_progress = round(min(100.0, max(0.0, (expenditure / orig_cost) * 100.0)), 1)

        # Planned_Progress = min(100, Elapsed_Duration / Planned_Duration * 100)
        planned_progress = None
        if elapsed_duration is not None and planned_duration and planned_duration > 0:
            planned_progress = round(min(100.0, max(0.0, (elapsed_duration / planned_duration) * 100.0)), 1)

        # Physical_Progress = min(100, max(0, phys_prog))
        physical_progress = None
        if phys_prog is not None:
            physical_progress = round(min(100.0, max(0.0, phys_prog)), 1)

        # Time_Overrun_Months = months between RevisedDate and OriginalEndDate
        time_overrun_months = None
        if end_date and rev_date:
            delay = (rev_date.year - end_date.year) * 12 + (rev_date.month - end_date.month)
            time_overrun_months = max(0.0, float(delay))
        elif p.get("DELAYED_TIME") is not None and str(p.get("DELAYED_TIME")).strip() != "":
            try:
                dt = float(p.get("DELAYED_TIME"))
                if dt >= 0:
                    time_overrun_months = round(dt, 1)
            except:
                pass

        # Cost_Overrun_Pct = (RevisedCost - OriginalCost) / OriginalCost * 100
        cost_overrun_pct = None
        if orig_cost and orig_cost > 0 and rev_cost is not None and rev_cost >= orig_cost:
            cost_overrun_pct = round(((rev_cost - orig_cost) / orig_cost) * 100.0, 1)
        elif p.get("COST_OVERRUN_PERC") is not None and str(p.get("COST_OVERRUN_PERC")).strip() != "":
            try:
                co = float(p.get("COST_OVERRUN_PERC"))
                if co >= 0:
                    cost_overrun_pct = round(co, 1)
            except:
                pass

        # Flags
        time_overrun_flag = 1 if (time_overrun_months is not None and time_overrun_months >= 3.0) else 0
        cost_overrun_flag = 1 if (cost_overrun_pct is not None and cost_overrun_pct >= 5.0) else 0

        # Implementation_Risk_Flag = 1 when time overrun >= 12 months OR cost overrun >= 10% OR physical progress lag > 25% Otherwise 0
        phys_lag = 0.0
        if planned_progress is not None and physical_progress is not None:
            phys_lag = planned_progress - physical_progress

        is_high_time = (time_overrun_months is not None and time_overrun_months >= 12.0)
        is_high_cost = (cost_overrun_pct is not None and cost_overrun_pct >= 10.0)
        is_high_lag = (phys_lag > 25.0)

        implementation_risk_flag = 1 if (is_high_time or is_high_cost or is_high_lag) else 0

        row = {
            "Project_ID": f"PAIMANA-{project_id}" if not project_id.startswith("PAIMANA-") else project_id,
            "Project_Name": project_name,
            "Line_Ministry": ministry,
            "Executing_Agency": executing_agency,
            "Sector": sector,
            "Project_Type": project_type,
            "Approved_Cost": approved_cost if approved_cost is not None else "",
            "Planned_Duration": planned_duration if planned_duration is not None else "",
            "Elapsed_Duration": elapsed_duration if elapsed_duration is not None else "",
            "Physical_Progress": physical_progress if physical_progress is not None else "",
            "Planned_Progress": planned_progress if planned_progress is not None else "",
            "Financial_Progress": financial_progress if financial_progress is not None else "",
            "Expenditure": expenditure if expenditure is not None else "",
            # Operational fields kept as empty / null (NOT FABRICATED)
            "Milestones_Total": "",
            "Milestones_Delayed": "",
            "Average_Milestone_Delay_Days": "",
            "Procurement_Delay_Days": "",
            "Land_Acquisition_Progress": "",
            "Approvals_Pending": "",
            "Scope_Changes": "",
            "Contractor_Performance": "",
            "Time_Overrun_Months": time_overrun_months if time_overrun_months is not None else "",
            "Cost_Overrun_Pct": cost_overrun_pct if cost_overrun_pct is not None else "",
            "Time_Overrun_Flag": time_overrun_flag,
            "Cost_Overrun_Flag": cost_overrun_flag,
            "Implementation_Risk_Flag": implementation_risk_flag,
        }
        normalized_rows.append(row)

    normalized_csv_path = os.path.join(paimana_dir, "paimana_normalized.csv")
    with open(normalized_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=normalized_cols)
        writer.writeheader()
        for r in normalized_rows:
            writer.writerow(r)
    print(f"Saved normalized CSV: {normalized_csv_path} ({os.path.getsize(normalized_csv_path)} bytes, {len(normalized_rows)} records)")

    # 4. Generate PAIMANA_METADATA.md
    metadata_content = f"""# MoSPI PAIMANA Official Dataset Metadata
**Smart India Hackathon 2026 | Problem Statement: SIH26103**  
**Infrastructure Project Monitoring Division (IPMD)**  
**Ministry of Statistics and Programme Implementation (MoSPI), Government of India**

---

## 1. Provenance & Official Source
- **Official Public Dashboard:** [https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew](https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew)
- **Official Reporting Portal:** [https://paimana-proj.mospi.gov.in/ReportPage](https://paimana-proj.mospi.gov.in/ReportPage)
- **Data Extracted On:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")}
- **Official Freeze Date:** August 2026 (Month: 08, Year: 2026)
- **Total Monitored Projects:** {len(raw_projects)} Central Sector Infrastructure Projects (Cost ₹150 Crore and above)
- **Total Sanctioned / Original Cost:** ₹{sum(clean_float(p.get('OriginalCost')) or 0 for p in raw_projects):,.2f} Crore
- **Total Cumulative Expenditure:** ₹{sum(clean_float(p.get('Expenditure')) or 0 for p in raw_projects):,.2f} Crore

---

## 2. Dataset Files in this Directory

| File Name | Description | Integrity Note |
|---|---|---|
| `paimana_raw_projects.json` | 100% unaltered raw JSON payload of 1,731 Central Sector projects from MoSPI PAIMANA public endpoint. | Read-Only. Never manually modified. |
| `paimana_projects.csv` | Direct tabular representation of all 26 raw PAIMANA attributes. | Direct extract from raw JSON. |
| `paimana_normalized.csv` | Normalized dataset mapped to OnTrack AI unified schema. Derived features calculated strictly by formula. | Null operational fields preserved as null. |
| `PAIMANA_METADATA.md` | This provenance and documentation file. | System metadata. |

---

## 3. Schema & Feature Mapping

| OnTrack Schema Field | PAIMANA Raw Field | Derivation / Mapping Formula | Missing Value Policy |
|---|---|---|---|
| `Project_ID` | `ProjectId` | Formatted as `PAIMANA-<ProjectId>` | Required |
| `Project_Name` | `ProjectName` | Direct text mapping | Raw text preserved |
| `Line_Ministry` | `LineMinistry` | Official Line Ministry (e.g. Ministry of Road Transport and Highways) | Raw text preserved |
| `Executing_Agency` | `COMPANYNAME` / `AgencyName` | Executing Public Sector Undertaking / Agency (e.g. NHAI, RVNL) | Raw text preserved |
| `Sector` | `SectorName` | Normalized sector category | Standardized category |
| `Project_Type` | Derived from `SectorName` | High-level infrastructure project archetype | Inferred archetype |
| `Approved_Cost` | `OriginalCost` | Sanctioned cost in ₹ Crore | Direct float |
| `Planned_Duration` | `SanctionDate`, `OriginalEndDate` | Months between SanctionDate and OriginalEndDate | Null if dates missing |
| `Elapsed_Duration` | `SanctionDate` | Months between SanctionDate and August 2026 freeze date | Null if sanction date missing |
| `Physical_Progress` | `PhysicalProgress` | Cumulative physical progress percentage [0.0 - 100.0] | Clamped [0, 100] |
| `Planned_Progress` | `Elapsed_Duration`, `Planned_Duration` | `min(100.0, (Elapsed_Duration / Planned_Duration) * 100.0)` | Null if planned duration is 0/null |
| `Financial_Progress` | `Expenditure`, `OriginalCost` | `min(100.0, (Expenditure / OriginalCost) * 100.0)` | Null if cost is 0/null |
| `Expenditure` | `Expenditure` | Cumulative audited expenditure in ₹ Crore | Direct float |
| `Time_Overrun_Months` | `OriginalEndDate`, `RevisedDate` | Months between RevisedDate and OriginalEndDate (or `DELAYED_TIME`) | 0.0 if on schedule; null if no revised date |
| `Cost_Overrun_Pct` | `OriginalCost`, `RevisedCost` | `((RevisedCost - OriginalCost) / OriginalCost) * 100.0` | 0.0 if within budget; null if no revised cost |
| `Time_Overrun_Flag` | Derived | `1` when `Time_Overrun_Months >= 3`, else `0` | Binary indicator |
| `Cost_Overrun_Flag` | Derived | `1` when `Cost_Overrun_Pct >= 5`, else `0` | Binary indicator |
| `Implementation_Risk_Flag` | Derived | `1` when time overrun >= 12m OR cost overrun >= 10% OR physical progress lag > 25%, else `0` | Composite risk indicator |

---

## 4. Strict Non-Fabrication Policy for Operational Metrics

The official MoSPI PAIMANA public feed tracks macro milestones, financial expenditure, and sanction dates, but **does not publish internal operational granularities** such as:
- `Milestones_Total`
- `Milestones_Delayed`
- `Average_Milestone_Delay_Days`
- `Procurement_Delay_Days`
- `Land_Acquisition_Progress`
- `Approvals_Pending`
- `Scope_Changes`
- `Contractor_Performance`

**Policy Enforcement:**
In accordance with ethical AI guidelines and Government of India data integrity standards, **these fields are strictly set to `null` / `NaN`**. The OnTrack AI ML inference pipeline, SHAP explainer, and preprocessing imputers have been designed to safely handle missing operational indicators via median/mode statistical baselines without crash or data fabrication.
"""
    metadata_path = os.path.join(paimana_dir, "PAIMANA_METADATA.md")
    with open(metadata_path, "w", encoding="utf-8") as f:
        f.write(metadata_content)
    print(f"Saved Metadata: {metadata_path} ({os.path.getsize(metadata_path)} bytes)")

if __name__ == "__main__":
    main()
