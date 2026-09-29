# MoSPI PAIMANA Official Dataset Metadata
**Smart India Hackathon 2026 | Problem Statement: SIH26103**  
**Infrastructure Project Monitoring Division (IPMD)**  
**Ministry of Statistics and Programme Implementation (MoSPI), Government of India**

---

## 1. Provenance & Official Source
- **Official Public Dashboard:** [https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew](https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew)
- **Official Reporting Portal:** [https://paimana-proj.mospi.gov.in/ReportPage](https://paimana-proj.mospi.gov.in/ReportPage)
- **Data Extracted On:** 2026-09-29 17:48:59 IST
- **Official Freeze Date:** August 2026 (Month: 08, Year: 2026)
- **Total Monitored Projects:** 1731 Central Sector Infrastructure Projects (Cost ₹150 Crore and above)
- **Total Sanctioned / Original Cost:** ₹3,071,944.00 Crore
- **Total Cumulative Expenditure:** ₹1,632,560.78 Crore

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
