# OnTrack AI — Benchmarking & What-If Simulation Guide & Evaluation Report (Checkpoint 4)

> **SIH 2026 Problem Statement: SIH26103**  
> **Project:** OnTrack AI — AI-assisted infrastructure project monitoring and early-warning system.  
> **Modules:** `ml/benchmark.py` & `ml/what_if.py`

---

## 1. Executive Overview

Infrastructure projects rarely operate in total isolation. When assessing whether a ₹1,800 Crore railway corridor is truly in distress or if its procurement lag is standard for projects of similar scale, decision-makers require **comparative peer context**. Furthermore, once potential project bottlenecks are identified, Project Monitoring Units (PMUs) need an interactive way to explore **counterfactual interventions** (e.g., *"What happens to projected risk if we fast-track approvals or accelerate right-of-way handover?"*).

In Checkpoint 4, OnTrack AI introduces two core analytical capabilities without requiring new models or redundant infrastructure:
1. **Factual Project Benchmarking (`ml/benchmark.py`):** Automatically locates historical peers and compares key physical, financial, milestone, and risk metrics.
2. **What-If Scenario Simulation (`ml/what_if.py`):** Re-runs the actual trained XGBoost models under user-specified operational modifications to simulate projected risk changes.

---

## 2. Part 1: Project Benchmarking Engine

### A. What Benchmarking Does
Benchmarking provides objective context by answering:
> *"How does this project's current progress, expenditure rate, and delay profile compare to similar infrastructure projects in the same sector and scale bracket?"*

Rather than relying on subjective opinions, benchmarking produces **factual, side-by-side comparative metrics** against relevant historical projects in `data/projects.csv`.

### B. How Comparable Projects Are Selected
To prevent misleading comparisons (such as comparing a ₹25 Crore rural primary school to a ₹3,000 Crore high-voltage power transmission grid), OnTrack AI implements a **sensible hierarchical matching algorithm**:

1. **Tier 1 (Strict / High-Fidelity Match):**
   - **Same Infrastructure Sector** (e.g., `Transport`)
   - **Same Project Type** (e.g., `Railway`)
   - **Sanctioned Cost Scale:** Peer projects must fall within $[0.5 \times \text{Cost}, 2.0 \times \text{Cost}]$ of the target project.
   - **Sanctioned Schedule Duration:** Peer projects must fall within $[0.7 \times \text{Duration}, 1.3 \times \text{Duration}]$ of the target project.
   - *Requirement:* If this strict cohort yields $\ge 5$ peer projects, it is selected as the primary benchmark group.

2. **Tier 2 (Relaxed Scale Fallback):**
   - If fewer than 5 peers match Tier 1, the scale brackets are relaxed to include all projects sharing the **Same Sector and Project Type**.

3. **Tier 3 (Sector-Level Fallback):**
   - If still fewer than 5 peers are found, the system compares against all projects across the **Entire Sector**.

This tiered approach guarantees that every project receives a statistically meaningful cohort of peers without crashing on edge cases or rare mega-projects.

### C. Factual Information Returned
The benchmark engine returns purely objective numbers without automated value judgments:
- **Comparable Project Count:** Number of matched peer projects.
- **Physical Progress (%):** Project value vs. peer average and median (plus factual arithmetic difference).
- **Financial Progress (%):** Project disbursement percentage vs. peer average and median.
- **Procurement Delay (Days):** Project vendor delay vs. peer average and median.
- **Average Milestone Delay (Days):** Typical schedule delay across milestones vs. peer average.
- **Milestones Delayed:** Number of slipped milestones vs. peer average.
- **Pending Approvals:** Outstanding clearances vs. peer average.
- **Land Acquisition Progress (%):** Right-of-way handover vs. peer average.
- **Overall Risk Score (0–100):** Project composite risk vs. peer cohort average.
- **Peer Risk Distribution:** Exact counts and percentages of peers in Low, Medium, and High risk tiers.

### D. Benchmark Example (PRJ-0005 — Railway Project)

```json
{
  "project_id": "PRJ-0005",
  "sector": "Transport",
  "project_type": "Railway",
  "comparable_project_count": 64,
  "similarity_criteria": {
    "match_tier": "Strict (Sector, Type & Scale Bracket)",
    "cost_bracket_crores": [926.3, 3705.2],
    "duration_bracket_months": [42.0, 78.0]
  },
  "metrics": {
    "physical_progress": { "project": 46.1, "peer_average": 52.7, "difference": -6.6 },
    "procurement_delay_days": { "project": 79.0, "peer_average": 20.6, "difference": 58.4 },
    "approvals_pending": { "project": 5.0, "peer_average": 1.0, "difference": 4.0 },
    "average_milestone_delay_days": { "project": 60.8, "peer_average": 30.5, "difference": 30.3 },
    "overall_risk_score": { "project": 88.7, "peer_average": 38.4, "difference": 50.3 }
  },
  "peer_risk_distribution": {
    "low_risk_count": 35,
    "medium_risk_count": 11,
    "high_risk_count": 18
  }
}
```

*Takeaway:* PRJ-0005 has a procurement delay of 79 days compared to the peer average of 20.6 days (+58.4 days) and 5 pending approvals compared to 1.0 peer average (+4.0), clearly exposing where this project deviates from historical norms.

---

## 3. Part 2: What-If Counterfactual Simulation Engine

### A. What What-If Simulation Does
What-if simulation enables decision-makers to evaluate prospective interventions before committing resources. For example:
- *"What if we expedite equipment delivery and cut procurement delay from 79 days to 15 days?"*
- *"What if the district collector accelerates land handover from 35% to 85% and freezes design changes?"*
- *"What if we replace an underperforming contractor with a Grade-A contractor?"*

### B. Why the Simulation Reruns the Machine Learning Model
A critical requirement of OnTrack AI is **modeling integrity**:
- ❌ **Forbidden:** Hardcoded static rules such as *"Every 10 days of delay reduction = -5% risk"*. Infrastructure projects are non-linear; resolving one issue does not eliminate risk if other severe bottlenecks remain unaddressed.
- ✔ **OnTrack AI Approach:** The system creates a copy of the project record, updates the user-specified variables, and **passes the modified record through the actual trained XGBoost models** (`models/time_overrun_model.joblib`, `models/cost_overrun_model.joblib`, `models/implementation_risk_model.joblib`).

Because tree ensembles capture non-linear feature splits and multidimensional interactions, the scenario prediction accurately reflects how the model's decision boundaries respond to the new feature combination.

### C. Validation & Safety Boundaries
The simulation engine validates all user inputs against realistic engineering limits before running inference:
- **Progress Metrics:** Must be percentages between `0.0%` and `100.0%`.
- **Delays (Procurement / Milestones):** Must be non-negative numbers ($\ge 0$).
- **Counts (Approvals / Scope Changes / Milestones):** Must be non-negative integers ($\ge 0$).
- **Contractor Rating:** Must strictly be one of `["Good", "Average", "Poor"]`.

Invalid inputs (e.g. `Physical_Progress = 125%` or `Procurement_Delay_Days = -20`) are immediately rejected with clear error guidance.

---

## 4. Evaluated What-If Case Studies

### Scenario 1: Significant Procurement Delay Reduction on `PRJ-0005`
- **Target Project:** `PRJ-0005` (Transport / Railway | Baseline Risk Score: **88.7 [HIGH]**)
- **Simulated Intervention:** `Procurement_Delay_Days` reduced from **79.0 days $\to$ 15.0 days** ($\Delta = -64$ days).
- **Model Inferences:**

| Risk Dimension | Baseline Probability | Scenario Probability | Model Shift ($\Delta$) |
|:---|:---:|:---:|:---:|
| **Time Overrun Risk** | 97.0% | 94.0% | $-3.0\%$ |
| **Cost Overrun Risk** | 81.4% | 59.3% | **$-22.1\%$** |
| **Implementation Risk** | 85.7% | 87.8% | $+2.1\%$ |
| **Overall Risk Score** | **88.7 [HIGH]** | **80.3 [HIGH]** | **$-8.4$ points** |

**Analytical Insight:**  
Notice that although Cost Overrun Risk dropped significantly by 22.1%, **Time Overrun Risk and Implementation Risk remained very high (~94% and ~88%)**, keeping the project in the HIGH risk category.  
*Why?* Because `PRJ-0005` still has **5 pending approvals** and an **average milestone delay of 60.8 days**. The real XGBoost model recognizes that solving procurement alone cannot prevent schedule slippage when regulatory clearances are still blocked. A simplistic hardcoded formula would have falsely claimed the project was saved; the real ML model provides an authentic, nuanced evaluation.

---

### Scenario 2: Multi-Factor Land Handover & Scope Freeze on `PRJ-0004`
- **Target Project:** `PRJ-0004` (Urban Development / Urban Infrastructure | Baseline Risk Score: **74.4 [HIGH]**)
- **Baseline Distress:** Stalled land acquisition (34.9%) and 2 approved scope changes.
- **Simulated Intervention:**
  1. `Land_Acquisition_Progress`: **34.9% $\to$ 85.0%** ($\Delta = +50.1\%$)
  2. `Scope_Changes`: **2 $\to$ 0** ($\Delta = -2$, design freeze)
- **Model Inferences:**

| Risk Dimension | Baseline Probability | Scenario Probability | Model Shift ($\Delta$) |
|:---|:---:|:---:|:---:|
| **Time Overrun Risk** | 87.2% | 9.7% | **$-77.5\%$** |
| **Cost Overrun Risk** | 96.0% | 12.3% | **$-83.7\%$** |
| **Implementation Risk** | 23.9% | 12.7% | $-11.2\%$ |
| **Overall Risk Score** | **74.4 [HIGH]** | **11.4 [LOW]** | **$-63.0$ points** |

**Analytical Insight:**  
As identified in Checkpoint 3's SHAP analysis, Land Acquisition and Scope Changes were the primary drivers pushing `PRJ-0004`'s cost risk to 96%. When both friction points are resolved simultaneously, the project successfully transitions from **HIGH Risk (74.4) to LOW Risk (11.4)**.

---

### Scenario 3: Comprehensive Multi-Variable Recovery Package on `PRJ-0005`
- **Target Project:** `PRJ-0005` (Transport / Railway | Baseline Risk Score: **88.7 [HIGH]**)
- **Simulated Intervention (Coordinated PMU Intervention):**
  1. `Procurement_Delay_Days`: **79.0 $\to$ 10.0 days**
  2. `Approvals_Pending`: **5 $\to$ 1** (Clear 4 outstanding statutory hurdles)
  3. `Average_Milestone_Delay_Days`: **60.8 $\to$ 20.0 days** (Fast-track milestone recovery)
- **Model Inferences:**

| Risk Dimension | Baseline Probability | Scenario Probability | Model Shift ($\Delta$) |
|:---|:---:|:---:|:---|
| **Time Overrun Risk** | 97.0% | 20.4% | **$-76.6\%$** |
| **Cost Overrun Risk** | 81.4% | 3.2% | **$-78.2\%$** |
| **Implementation Risk** | 85.7% | 13.3% | **$-72.4\%$** |
| **Overall Risk Score** | **88.7 [HIGH]** | **12.6 [LOW]** | **$-76.1$ points** |

**Analytical Insight:**  
Only a holistic intervention addressing tendering, regulatory clearances, and milestone scheduling concurrently achieves a decisive de-escalation for deeply distressed mega-projects like `PRJ-0005`.

---

## 5. Critical Methodological Disclosures & Limitations

### ⚠️ A. Simulation $\ne$ Real-World Causation
> **Governance Notice for Project Authorities:**  
> **What-if simulation results represent statistical model projections, NOT guaranteed real-world causal outcomes.**
>
> 1. **Model Sensitivity:** When you adjust `Procurement_Delay_Days` from 79 to 15, the model reports how projects with a 15-day delay historically scored across the training data.
> 2. **Execution Reality:** In the physical world, issuing an administrative directive to accelerate procurement does not automatically guarantee vendor manufacturing will speed up without unforeseen bottlenecks.
> 3. **Intended Role:** What-if simulation serves as a **decision-support heuristic to prioritize interventions**, not an automated guarantee of project turnaround.

### ⚠️ B. Synthetic Dataset Basis
> **Prototype Data Disclosure:**  
> All benchmarking comparisons and simulation inferences are computed using the **synthetic dataset** (`data/projects.csv`, $N = 1,000$ projects).  
> 
> While generated using mathematical formulations reflective of Indian infrastructure patterns, **this dataset does not contain actual confidential ministry records**. Before operational deployment, peer distributions and simulation baselines must be retrained on validated central/state government project databases.

---

## 6. Architecture & Reusability for Future FastAPI Backend

Both modules are designed with zero duplication of machine learning logic:

| Module | Core Function | Calling Interface | Primary Consumer |
|:---|:---|:---|:---|
| [`ml/predict.py`](file:///d:/OnTrack-AI/ml/predict.py) | `predict_project_risk(record)` | Pure dict / DataFrame | Fast inference, What-If engine |
| [`ml/explain.py`](file:///d:/OnTrack-AI/ml/explain.py) | `explain_all_risks(record)` | Pure dict / DataFrame | SHAP attribution, XAI views |
| [`ml/benchmark.py`](file:///d:/OnTrack-AI/ml/benchmark.py) | `benchmark_project(record)` | Pure dict / DataFrame | Peer comparison dashboard |
| [`ml/what_if.py`](file:///d:/OnTrack-AI/ml/what_if.py) | `simulate_what_if(record, mods)` | Pure dict / DataFrame | Interactive scenario simulator |

When FastAPI is developed in upcoming checkpoints, each route handler can import these functions directly with clean, lightweight JSON request and response payloads.
