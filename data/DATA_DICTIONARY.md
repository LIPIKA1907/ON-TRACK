# OnTrack AI — Dataset Dictionary & Schema Documentation

## ⚠️ Synthetic Data Disclosure & Limitation Notice
> **Important Prototype Notice:**  
> **This dataset is representative synthetic data created for demonstrating the OnTrack AI prototype. It is not real government project data and must not be interpreted as evidence of real-world model performance.**
>
> All project records, milestone metrics, financial figures, and risk indicators have been generated synthetically using mathematical and statistical formulations to reflect realistic infrastructure project behavior. No confidential, proprietary, or actual ministry project monitoring data was used.

---

## 📊 Dataset Overview
- **File Name:** `projects.csv`
- **Location:** `data/projects.csv`
- **Total Records:** 1,000 projects
- **Total Columns:** 23 (18 input features + 5 target variables)
- **Generator Script:** `ml/generate_dataset.py`
- **Reproducibility Seed:** `42` (with independent seed `143` for realistic missing data injection)

---

## 📋 Data Dictionary

| # | Column Name | Role | Data Type | Units / Format | Allowed / Observed Range | Description & Domain Meaning | Missing Values |
|---|---|---|---|---|---|---|---|
| 1 | `Project_ID` | Identifier | String (Text) | `PRJ-XXXX` | PRJ-0001 to PRJ-1000 | Unique alphanumeric project identifier. | None (0.0%) |
| 2 | `Sector` | Input Feature | Categorical | Nominal | Transport, Energy, Water, Urban Development, Health, Education | Broad infrastructure sector under which the project is sanctioned. | None (0.0%) |
| 3 | `Project_Type` | Input Feature | Categorical | Nominal | Road, Railway, Bridge, Power, Water Supply, Hospital, School, Urban Infrastructure | Specific sub-category or asset type being developed. | None (0.0%) |
| 4 | `Approved_Cost` | Input Feature | Float (Numeric) | ₹ Crores | 20.33 to 4,483.09 | Original baseline sanctioned project cost as approved by competent authority. | None (0.0%) |
| 5 | `Planned_Duration` | Input Feature | Integer (Numeric) | Months | 12 to 72 | Sanctioned schedule duration from foundation/award to planned completion. | None (0.0%) |
| 6 | `Elapsed_Duration` | Input Feature | Integer (Numeric) | Months | 3 to 71 | Time elapsed since project commencement date up to the monitoring snapshot. | None (0.0%) |
| 7 | `Physical_Progress` | Input Feature | Float (Numeric) | Percentage (%) | 2.0% to 100.0% | Actual verified cumulative physical work completed on ground. | None (0.0%) |
| 8 | `Planned_Progress` | Input Feature | Float (Numeric) | Percentage (%) | 17.1% to 100.0% | Target cumulative work that was scheduled to be completed by the elapsed date. | None (0.0%) |
| 9 | `Financial_Progress` | Input Feature | Float (Numeric) | Percentage (%) | 4.5% to 100.0% | Cumulative percentage of funds released/disbursed against approved budget. | None (0.0%) |
| 10 | `Expenditure` | Input Feature | Float (Numeric) | ₹ Crores | 8.93 to 3,998.58 | Total actual cumulative financial expenditure incurred to date. | None (0.0%) |
| 11 | `Milestones_Total` | Input Feature | Integer (Numeric) | Count | 6 to 25 | Total key contractual milestone deliverables scheduled for the project. | None (0.0%) |
| 12 | `Milestones_Delayed` | Input Feature | Integer (Numeric) | Count | 0 to 14 | Number of key milestones that breached their scheduled delivery dates. | None (0.0%) |
| 13 | `Average_Milestone_Delay_Days` | Input Feature | Float (Numeric) | Days | 0.0 to 92.0 | Average days of delay across delayed milestones (0.0 if no milestones delayed). | 36 (3.6%) |
| 14 | `Procurement_Delay_Days` | Input Feature | Integer (Numeric) | Days | 0 to 150 | Slippage in tendering, equipment delivery, or vendor procurement. | 29 (2.9%) |
| 15 | `Land_Acquisition_Progress` | Input Feature | Float (Numeric) | Percentage (%) | 25.1% to 100.0% | Extent of right-of-way (RoW) or site land handed over to contractor. | 22 (2.2%) |
| 16 | `Approvals_Pending` | Input Feature | Integer (Numeric) | Count | 0 to 5 | Outstanding clearances (environmental, forest, utility, municipal). | None (0.0%) |
| 17 | `Scope_Changes` | Input Feature | Integer (Numeric) | Count | 0 to 4 | Approved major engineering change orders or variations in scope. | None (0.0%) |
| 18 | `Contractor_Performance` | Input Feature | Categorical | Ordinal | Good, Average, Poor | Qualitative rating of main engineering and EPC contractor execution. | 21 (2.1%) |
| 19 | `Time_Overrun_Months` | Target Variable | Float (Numeric) | Months | 0.0 to 22.3 | Continuous target: Total schedule delay in months beyond planned completion. | None (0.0%) |
| 20 | `Cost_Overrun_Pct` | Target Variable | Float (Numeric) | Percentage (%) | 0.0% to 36.0% | Continuous target: Percentage cost overrun relative to baseline approved cost. | None (0.0%) |
| 21 | `Time_Overrun_Flag` | Target Variable | Binary Flag | 0 or 1 | 0 (On Schedule) / 1 (Delayed) | Binary target: Schedule delay indicator (1 = delay >= 3 months). | None (0.0%) |
| 22 | `Cost_Overrun_Flag` | Target Variable | Binary Flag | 0 or 1 | 0 (Within Budget) / 1 (Cost Overrun) | Binary target: Budget escalation indicator (1 = cost overrun >= 5.0%). | None (0.0%) |
| 23 | `Implementation_Risk_Flag` | Target Variable | Binary Flag | 0 or 1 | 0 (Normal) / 1 (High Risk) | Binary target: Composite multi-dimensional operational distress indicator. | None (0.0%) |

---

## 🎯 Target Variable Distributions (N = 1,000)

### 1. Classification Targets (Binary Flags)
- **Time_Overrun_Flag:**
  - `Class 0 (On Schedule)`: 524 projects (52.40%)
  - `Class 1 (Delayed)`: 476 projects (47.60%)
- **Cost_Overrun_Flag:**
  - `Class 0 (Within Budget)`: 637 projects (63.70%)
  - `Class 1 (Cost Overrun)`: 363 projects (36.30%)
- **Implementation_Risk_Flag:**
  - `Class 0 (Normal Risk)`: 727 projects (72.70%)
  - `Class 1 (High Operational Risk)`: 273 projects (27.30%)

### 2. Regression Targets (Continuous Metrics)
- **Time_Overrun_Months:**
  - Mean: 3.96 months
  - Std Dev: 4.30 months
  - Median: 2.80 months
  - Range: [0.00, 22.30] months
- **Cost_Overrun_Pct:**
  - Mean: 4.62%
  - Std Dev: 6.04%
  - Median: 1.90%
  - Range: [0.00%, 36.00%]

---

## 🔍 Missing Data Distribution
Realistic, low-percentage missing values (~2% to 3.6%) have been injected into four operational fields where field monitoring data in public works is frequently incomplete or pending audit:
- `Average_Milestone_Delay_Days`: 36 missing records (3.6%)
- `Procurement_Delay_Days`: 29 missing records (2.9%)
- `Land_Acquisition_Progress`: 22 missing records (2.2%)
- `Contractor_Performance`: 21 missing records (2.1%)

All other input columns and all five target variables are 100% complete.
