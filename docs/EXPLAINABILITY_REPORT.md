# OnTrack AI — Explainable AI (XAI) Architecture & Evaluation Report (Checkpoint 3)

> **SIH 2026 Problem Statement: SIH26103**  
> **Project:** OnTrack AI — AI-assisted infrastructure project monitoring and early-warning system.  
> **Module:** Machine Learning Explainability (`ml/explain.py`)

---

## 1. Executive Summary & Purpose

A major impediment to adopting machine learning in public infrastructure oversight is the **"black-box" dilemma**. When a project monitoring unit (PMU) or government department receives an alert stating that a railway or bridge project has an 88% probability of delay, decision-makers cannot act effectively without knowing **why**:
- *Is the delay driven by regulatory clearances?*
- *Is it contractor inefficiency?*
- *Is it tendering and procurement bottlenecks?*
- *What positive strengths are currently preventing even worse slippage?*

In Checkpoint 3, OnTrack AI integrates **real SHAP (SHapley Additive exPlanations)** directly with the existing trained XGBoost models (`models/time_overrun_model.joblib`, `models/cost_overrun_model.joblib`, `models/implementation_risk_model.joblib`). 

This engine provides transparent, per-project local feature attribution, decomposing each prediction into:
1. **Model Prediction & Probability:** Exact risk estimates across Time, Cost, and Implementation dimensions.
2. **Top Positive Risk Factors:** Features driving the predicted risk upward ($\phi_i > 0$).
3. **Protective Factors:** Features acting as operational buffers pulling predicted risk downward ($\phi_i < 0$).
4. **Exact Feature Contributions:** Grounded in cooperative game theory with mathematical consistency.
5. **Human-Readable Interface:** Clean, structured JSON output ready for frontend dashboards and high-resolution visual plots.

---

## 2. What is SHAP and Why is it Used?

### A. Theoretical Foundation: Shapley Values
SHAP is grounded in **cooperative game theory**, originally developed by Nobel laureate Lloyd Shapley (1953) to determine the fair distribution of payouts among players collaborating in a game. In machine learning:
- The **"game"** is the model's prediction task for a specific project.
- The **"players"** are the project's feature values (e.g., `Procurement_Delay_Days = 79`, `Approvals_Pending = 5`).
- The **"payout"** is the difference between the model's prediction for this project and the expected average prediction across all projects ($\Delta f(x) = f(x) - E[f(X)]$).

SHAP uniquely satisfies four foundational axioms of fair attribution that heuristic importance metrics (such as Gini impurity or gain) violate:
1. **Efficiency (Local Accuracy):** The sum of feature contributions plus the expected base value strictly equals the model's output:
   $$f(x) = \phi_0 + \sum_{i=1}^{M} \phi_i(x)$$
2. **Symmetry:** Two features that contribute equally across all possible feature coalitions receive identical attributions.
3. **Dummy Player (Missingness):** A feature that does not influence the model's decision receives a contribution of zero.
4. **Additivity (Consistency):** If a model change increases a feature's marginal contribution, that feature's attribution cannot decrease.

### B. TreeSHAP for XGBoost
For tree-based gradient boosted ensembles (XGBoost), computing classic Shapley values requires exponential time $\mathcal{O}(2^M)$. OnTrack AI utilizes **TreeSHAP** (Lundberg et al., *Nature Machine Intelligence*, 2020), which evaluates exact feature attributions in polynomial time $\mathcal{O}(T \cdot L \cdot D^2)$ (where $T$ is the number of trees, $L$ is maximum leaves, and $D$ is maximum tree depth). This delivers sub-millisecond, exact local explanations suitable for real-time decision-support.

### C. Why SHAP Over Generic Feature Importance?
Standard global feature importances (e.g., XGBoost built-in `feature_importances_`) show what features were important across the entire training dataset on average. However, **infrastructure governance requires project-specific explanations**:
- For **Project A**, delay may be 90% driven by pending forest clearances.
- For **Project B**, clearances may be complete, but vendor procurement is 120 days late.
- Global metrics cannot differentiate these two cases; **SHAP computes exact local explanations for every individual project record.**

---

## 3. Architecture & Implementation (`ml/explain.py`)

### A. Pipeline Architecture

```
Project Record (Dictionary or DataFrame)
       │
       ▼
ColumnTransformer Preprocessor (models/preprocessor.joblib)
       │  (Median imputation for 14 numerical features,
       │   one-hot encoding for 3 categorical features -> 31 transformed columns)
       ▼
XGBoost Classifiers (models/time_overrun_model.joblib, etc.)
       │
       ├─────────────────────────────────┬─────────────────────────────────┐
       ▼                                 ▼                                 ▼
Time Overrun Risk                Cost Overrun Risk               Implementation Risk
TreeExplainer (SHAP)             TreeExplainer (SHAP)            TreeExplainer (SHAP)
       │                                 │                                 │
       └─────────────────────────────────┼─────────────────────────────────┘
                                         ▼
                 Feature Aggregation & Human Name Mapping
                 (Combines one-hot dummies into 17 primary operational fields)
                                         │
                                         ▼
                 Risk Factors Separation & Ranking:
                 • Top Positive Risk Factors (phi > 0, sorted descending)
                 • Protective Factors (phi < 0, sorted ascending)
                                         │
                                         ▼
                 Mathematical Consistency Verification
                 (base_value + sum(phi) == model_margin)
                                         │
                                         ▼
                 Output: Frontend-Ready JSON & SHAP Visualizations
```

### B. Feature Name Mapping
To ensure non-technical PMU officers and dashboard users understand outputs immediately, raw column names are converted to professional labels:

| Raw Feature Column | Human-Readable Name | Domain Description |
|:---|:---|:---|
| `Procurement_Delay_Days` | **Procurement Delay** | Slippage in tendering, vendor contracting, or equipment delivery. |
| `Physical_Progress` | **Physical Progress** | Verified cumulative work completed on ground (%). |
| `Planned_Progress` | **Planned Progress** | Target cumulative work scheduled to be completed (%). |
| `Financial_Progress` | **Financial Progress** | Cumulative funds disbursed against sanctioned budget (%). |
| `Expenditure` | **Cumulative Spend (₹ Cr)** | Total financial expenditure incurred to date. |
| `Approved_Cost` | **Approved Cost (₹ Cr)** | Baseline sanctioned project cost. |
| `Planned_Duration` | **Planned Duration (Months)** | Baseline sanctioned schedule duration. |
| `Elapsed_Duration` | **Elapsed Duration (Months)** | Timeline elapsed from commencement to current audit. |
| `Milestones_Total` | **Total Milestones** | Sanctioned contractual milestone deliverables. |
| `Milestones_Delayed` | **Milestones Delayed** | Number of key milestones that breached their scheduled delivery dates. |
| `Average_Milestone_Delay_Days` | **Average Milestone Delay** | Typical delay duration (in days) across delayed milestones. |
| `Land_Acquisition_Progress` | **Land Acquisition Progress** | Extent of right-of-way (RoW) or site land handed over (%). |
| `Approvals_Pending` | **Pending Approvals** | Outstanding statutory/environmental/utility clearances. |
| `Scope_Changes` | **Scope Changes** | Approved major engineering change orders or variations. |
| `Contractor_Performance` | **Contractor Performance** | Contractor execution quality rating (`Good`, `Average`, `Poor`). |
| `Sector` | **Infrastructure Sector** | Sanctioned sector (`Transport`, `Energy`, `Water`, etc.). |
| `Project_Type` | **Project Type** | Specific asset subcategory (`Railway`, `Road`, `Bridge`, etc.). |

### C. Distinguishing Positive Risk Drivers vs. Protective Factors
SHAP local attributions explicitly split each prediction into two intuitive camps:
- **Positive Risk Factors ($\phi_i > 0$):** These conditions pushed the model's log-odds margin upward, directly increasing the predicted risk probability. For instance, having 5 pending approvals or 79 days of procurement delay.
- **Protective Factors ($\phi_i < 0$):** These conditions acted as stabilizers that pulled the model's log-odds margin downward, reducing the predicted risk probability. For instance, having a `Good` contractor rating or completed land acquisition (89%).

### D. JSON Schema for Frontend Consumption
The explainability engine outputs clean, standardized dictionaries ready for direct API consumption by the upcoming React frontend:

```json
{
  "risk_dimension": "Time Overrun Risk",
  "risk_key": "time",
  "risk_probability": 0.9702,
  "model_margin": 3.4822,
  "base_value": -0.0833,
  "top_risk_factors": [
    {
      "feature": "Average Milestone Delay",
      "feature_key": "Average_Milestone_Delay_Days",
      "value": 60.8,
      "contribution": 1.4779
    },
    {
      "feature": "Pending Approvals",
      "feature_key": "Approvals_Pending",
      "value": 5,
      "contribution": 1.1554
    },
    {
      "feature": "Milestones Delayed",
      "feature_key": "Milestones_Delayed",
      "value": 9,
      "contribution": 0.7707
    }
  ],
  "protective_factors": [
    {
      "feature": "Contractor Performance",
      "feature_key": "Contractor_Performance",
      "value": "Good",
      "contribution": -0.3045
    },
    {
      "feature": "Scope Changes",
      "feature_key": "Scope_Changes",
      "value": 0,
      "contribution": -0.2025
    }
  ],
  "mathematical_verification": {
    "base_value": -0.08329,
    "sum_shap_values": 3.565514,
    "reconstructed_margin": 3.482224,
    "actual_model_margin": 3.482223,
    "margin_difference": 0.000001,
    "verified_consistent": true
  }
}
```

---

## 4. Mathematical Verification of Model Fidelity

To guarantee that explanations are **dynamically computed from the actual model** (and not mocked, hardcoded, or disconnected from the decision boundary), OnTrack AI performs automated consistency checks:

1. **Exact Local Summation:**
   $$\text{base\_value} + \sum_{i=1}^{M} \phi_i = \text{model\_margin}$$
2. **Sigmoidal Inversion:**
   $$P(\text{Risk} = 1) = \frac{1}{1 + e^{-\text{model\_margin}}}$$

Across all tested projects, the discrepancy between the reconstructed margin and the model's actual margin is bounded by $|\Delta| < 10^{-6}$ (floating point precision). This mathematically validates that:
- Every SHAP contribution corresponds directly to the internal tree nodes evaluated by XGBoost.
- The explanations are 100% faithful to the underlying model's decisions.

---

## 5. Detailed Case Studies on 3 Representative Projects

To evaluate the explainability engine, we evaluated three distinct real records from `data/projects.csv`:

### Case Study 1: `PRJ-0005` — Critical Distress (Railway Project)
- **Sector & Type:** Transport / Railway
- **Scale:** Approved Cost ₹1,852.62 Cr | Planned Duration: 60 months | Elapsed: 37 months
- **Ground Reality:** Physical progress is 46.1% vs 59.3% planned. 9 out of 20 milestones are delayed with an average slippage of 60.8 days. 5 regulatory clearances remain pending. Procurement is 79 days late.
- **Overall Risk Score:** **88.7 / 100 [HIGH RISK]**

#### Multi-Dimensional SHAP Breakdown:
| Risk Dimension | Predicted Probability | Model Margin | Top Risk-Increasing Drivers ($\phi > 0$) | Protective Factors ($\phi < 0$) |
|:---|:---:|:---:|:---|:---|
| **Time Overrun Risk** | **97.0%** | +3.4822 | • **Average Milestone Delay (60.8d):** $+1.4779$<br>• **Pending Approvals (5):** $+1.1554$<br>• **Milestones Delayed (9):** $+0.7707$ | • Contractor Performance (Good): $-0.3045$<br>• Scope Changes (0): $-0.2025$<br>• Total Milestones (20): $-0.1266$ |
| **Cost Overrun Risk** | **81.4%** | +1.4736 | • **Average Milestone Delay (60.8d):** $+1.1142$<br>• **Pending Approvals (5):** $+0.9811$<br>• **Procurement Delay (79d):** $+0.7591$ | • Scope Changes (0): $-0.9125$<br>• Contractor Performance (Good): $-0.5200$<br>• Elapsed Duration (37m): $-0.1184$ |
| **Implementation Risk** | **85.7%** | +1.7931 | • **Pending Approvals (5):** $+1.4630$<br>• **Average Milestone Delay (60.8d):** $+1.1887$<br>• **Milestones Delayed (9):** $+0.7109$ | • Scope Changes (0): $-0.3795$<br>• Contractor Performance (Good): $-0.2847$<br>• Total Milestones (20): $-0.1502$ |

**Diagnostic Takeaway:** PRJ-0005's acute delay and cost risks are **not caused by contractor incompetence** (contractor rating is `Good`, providing a protective effect of $-0.30$ to $-0.52$). Instead, the model pinpoints **severe bureaucratic bottlenecks**: 5 pending approvals and an unresolved 79-day procurement lag. A PMU can immediately prioritize inter-ministerial clearance coordination rather than issuing vendor default notices.

---

### Case Study 2: `PRJ-0004` — High Cost Escalation (Urban Infrastructure Project)
- **Sector & Type:** Urban Development / Urban Infrastructure
- **Scale:** Approved Cost ₹836.44 Cr | Planned Duration: 48 months | Elapsed: 14 months
- **Ground Reality:** Physical progress is only 19.7% vs 29.3% planned. 6 out of 15 milestones delayed. Land acquisition progress is critically low at 34.9%. 2 major scope variations approved. 0 approvals pending.
- **Overall Risk Score:** **74.4 / 100 [HIGH RISK]**

#### Multi-Dimensional SHAP Breakdown:
| Risk Dimension | Predicted Probability | Model Margin | Top Risk-Increasing Drivers ($\phi > 0$) | Protective Factors ($\phi < 0$) |
|:---|:---:|:---:|:---|:---|
| **Time Overrun Risk** | **87.2%** | +1.9224 | • **Land Acquisition Progress (34.9%):** $+1.7628$<br>• **Scope Changes (2):** $+0.6941$<br>• **Milestones Delayed (6):** $+0.5914$ | • Average Milestone Delay (22.8d): $-0.7785$<br>• Pending Approvals (0): $-0.5276$<br>• Contractor Performance (Good): $-0.2451$ |
| **Cost Overrun Risk** | **96.0%** | +3.1687 | • **Scope Changes (2):** $+2.0198$<br>• **Land Acquisition Progress (34.9%):** $+1.2861$<br>• **Milestones Delayed (6):** $+0.6398$ | • Average Milestone Delay (22.8d): $-0.6390$<br>• Contractor Performance (Good): $-0.3798$<br>• Pending Approvals (0): $-0.3193$ |
| **Implementation Risk** | **23.9%** | -1.1602 | • **Land Acquisition Progress (34.9%):** $+0.5823$<br>• **Milestones Delayed (6):** $+0.4221$<br>• **Scope Changes (2):** $+0.3726$ | • Average Milestone Delay (22.8d): $-0.7655$<br>• Pending Approvals (0): $-0.5351$<br>• Contractor Performance (Good): $-0.3164$ |

**Diagnostic Takeaway:** For PRJ-0004, the primary fiscal threat is **Scope Changes ($\phi = +2.0198$)** coupled with **Land Acquisition stalls ($\phi = +1.2861$)**. Because clearances are completely resolved (`Pending Approvals = 0`, protective factor of $-0.53$), Implementation Risk remains low (23.9%), but budget overrun is nearly certain (96.0%). Interventions must target site handover and design freezing.

---

### Case Study 3: `PRJ-0001` — Stable Benchmark (Water Supply Project)
- **Sector & Type:** Water / Water Supply
- **Scale:** Approved Cost ₹338.78 Cr | Planned Duration: 36 months | Elapsed: 12 months
- **Ground Reality:** Physical progress is 29.9% vs 33.3% planned. 4 out of 23 milestones delayed by only 25.3 days on average. Land acquisition is 89.0% complete. Contractor rating is `Good`.
- **Overall Risk Score:** **6.8 / 100 [LOW RISK]**

#### Multi-Dimensional SHAP Breakdown:
| Risk Dimension | Predicted Probability | Model Margin | Top Risk-Increasing Drivers ($\phi > 0$) | Protective Factors ($\phi < 0$) |
|:---|:---:|:---:|:---|:---|
| **Time Overrun Risk** | **7.9%** | -2.4551 | • Physical Progress (29.9%): $+0.2646$<br>• Milestones Delayed (4): $+0.1989$<br>• Financial Progress (28.1%): $+0.0812$ | • **Average Milestone Delay (25.3d):** $-0.8160$<br>• **Land Acquisition Progress (89%):** $-0.7180$<br>• **Total Milestones (23):** $-0.4361$ |
| **Cost Overrun Risk** | **6.2%** | -2.7113 | • Milestones Delayed (4): $+0.2225$<br>• Physical Progress (29.9%): $+0.1989$<br>• Financial Progress (28.1%): $+0.1758$ | • **Average Milestone Delay (25.3d):** $-1.0810$<br>• **Contractor Performance (Good):** $-0.6393$<br>• **Land Acquisition Progress (89%):** $-0.4914$ |
| **Implementation Risk** | **5.7%** | -2.8141 | • Approved Cost (₹338.78 Cr): $+0.2578$<br>• Milestones Delayed (4): $+0.2296$<br>• Land Acquisition Progress (89%): $+0.0685$ | • **Average Milestone Delay (25.3d):** $-0.4113$<br>• **Contractor Performance (Good):** $-0.4015$<br>• **Total Milestones (23):** $-0.3787$ |

**Diagnostic Takeaway:** PRJ-0001 represents a healthy project. Although 4 minor milestones slipped, the typical delay is short (25.3 days), right-of-way is securely handed over (89%), and vendor execution is strong (`Good`). The model recognizes these protective buffers, which collectively push the prediction margin deep into negative territory ($-2.45$ to $-2.81$), yielding minimal risk ($<8\%$).

---

## 6. Generated Visualizations Gallery

The engine automatically generates publication-grade SHAP plots saved under `docs/shap_examples/`.

### Visual Types Generated:
1. **SHAP Waterfall Plots:** Illustrates the step-by-step composition of the prediction, starting at the baseline expected margin $E[f(X)]$ and adding or subtracting each feature's contribution until reaching the final model output $f(x)$.
2. **SHAP Local Bar Plots:** Ranks features by absolute magnitude of impact for that specific project, clearly distinguishing positive drivers (red) from protective mitigations (blue).

### Generated Files in `docs/shap_examples/`:
- `time_risk_waterfall.png` & `time_risk_bar.png`
- `cost_risk_waterfall.png` & `cost_risk_bar.png`
- `implementation_risk_waterfall.png` & `implementation_risk_bar.png`
- Project-specific sets: `prj_0005_*` (Critical High Risk) and `prj_0001_*` (Low Risk benchmark).

---

## 7. Critical Disclosures, Methodological Boundaries & Limitations

### ⚠️ A. Feature Attribution vs. Causation (Crucial Governance Principle)
> **Statutory Notice for Decision-Makers:**  
> **SHAP computes statistical feature attribution within the model's learned decision surface; it does NOT prove causal relationships.**
>
> 1. **Attribution $\ne$ Intervention:** If SHAP indicates that `Pending_Approvals = 5` contributed $+1.46$ to Implementation Risk, this reflects the model's association between high pending approvals and project failure. It does **not** causally prove that administratively stamping approved status on pending files without resolving underlying disputes will automatically make the project succeed.
> 2. **Confounding Variables:** Unobserved factors (such as contractor financial insolvency or local political protests) may drive both delayed milestones and pending approvals simultaneously.
> 3. **Actionable Governance Rule:** SHAP values must be utilized as **decision-support indicators for prioritized human audit**, never as automated administrative warrants for contractual sanctions.

### ⚠️ B. Synthetic Data Basis Disclosure
> **Prototype Data Notice:**  
> All models evaluated by this explainability system were trained on a **representative synthetic dataset** (`data/projects.csv`, $N = 1,000$ projects). 
> 
> While the dataset was generated using domain formulations reflective of Indian infrastructure realities (MORTH, NHAI, Indian Railways project characteristics), **the models have not been trained on confidential government infrastructure databases**.
> 
> Numerical contribution values, base values, and threshold percentages must be recalibrated prior to operational deployment on state or central ministry dashboards.

### C. Correlated Features in TreeSHAP
In infrastructure projects, operational variables often correlate (e.g., as `Elapsed_Duration` advances, `Expenditure` and `Physical_Progress` generally increase). TreeSHAP traverses conditional expectation trees assuming standard tree split paths. In the presence of strong collinearity, credit may be divided among correlated features. OnTrack AI mitigates this by grouping dummy-encoded categorical variables and presenting both aggregated feature summaries and granular breakdowns.

---

## 8. Summary of Checkpoint 3 Deliverables

1. **Explainability Engine:** [`ml/explain.py`](file:///d:/OnTrack-AI/ml/explain.py) supporting `explain_project_risk()`, `explain_all_risks()`, and `generate_shap_visualizations()`.
2. **Models Preserved:** Retained existing XGBoost models without unnecessary retraining or architectural bloat.
3. **Frontend Integration Ready:** Standardized JSON outputs conforming to requirements with human-readable names and positive/negative separation.
4. **Visual Demonstrations:** High-resolution Waterfall and Bar plots generated and verified in `docs/shap_examples/`.
5. **Exact Verification:** Zero mock data; all explanations verified consistent with model output margins to $< 10^{-6}$.
