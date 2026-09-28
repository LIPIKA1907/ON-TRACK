# OnTrack AI — Machine Learning Training & Model Report (Checkpoint 2)

> **SIH 2026 Problem Statement: SIH26103**  
> **Project:** OnTrack AI — AI-assisted infrastructure project monitoring and early-warning system.

---

## 1. Executive Summary & Purpose
The goal of Checkpoint 2 is to construct, train, evaluate, and save reproducible machine learning models that estimate risk for major infrastructure projects. Instead of relying on single subjective project status ratings, OnTrack AI decomposes project vulnerability into three core dimensions:

1. **Time Overrun Risk:** Will the project experience a significant schedule delay ($\ge 3$ months)?
2. **Cost Overrun Risk:** Will the project breach its sanctioned budget by $\ge 5\%$?
3. **Implementation Risk:** Is the project facing compound operational bottlenecks (clearances, contractor friction, land hurdles) that could derail execution?

---

## 2. Input Features & Target Variables

### A. Input Features Used (17 Features)
To make reliable predictions without target leakage, the models use only operational and project-monitoring variables recorded up to the monitoring snapshot:

| Category | Features | Description |
|:---|:---|:---|
| **Project Basics** | `Sector`, `Project_Type`, `Approved_Cost`, `Planned_Duration`, `Elapsed_Duration` | Fundamental scale, type, and timeline of the infrastructure asset. |
| **Progress & Spend** | `Physical_Progress`, `Planned_Progress`, `Financial_Progress`, `Expenditure` | Ground work completed vs. scheduled work, disbursement rate, and budget utilized. |
| **Milestone Health** | `Milestones_Total`, `Milestones_Delayed`, `Average_Milestone_Delay_Days` | Granular delivery milestones and typical delay durations. |
| **Ground Friction** | `Procurement_Delay_Days`, `Land_Acquisition_Progress`, `Approvals_Pending`, `Scope_Changes`, `Contractor_Performance` | Key friction points: tendering delays, right-of-way handover, regulatory clearances, design changes, and vendor quality. |

### B. Excluded Columns (Strict No-Leakage Policy)
The following columns were **strictly excluded** from input features:
- `Project_ID` (Non-predictive identifier)
- `Time_Overrun_Months` (Direct target leakage)
- `Cost_Overrun_Pct` (Direct target leakage)
- `Time_Overrun_Flag`, `Cost_Overrun_Flag`, `Implementation_Risk_Flag` (Target outputs)

---

## 3. Data Preprocessing & Training Methodology

### A. Preprocessing Pipeline (`preprocessor.joblib`)
- **Numerical Features (14):** Missing values imputed using the feature **median** (robust to outliers).
- **Categorical Features (3):** Missing values imputed using the **most frequent** value, followed by Scikit-learn **One-Hot Encoding** (`handle_unknown='ignore'`).
- The entire preprocessor is fit strictly on training data (800 rows) and serialized to `models/preprocessor.joblib` to guarantee identical preprocessing during inference.

### B. Train / Test Split
- **Dataset Size:** 1,000 synthetic projects.
- **Split Ratio:** 80% Training (800 projects) / 20% Testing (200 projects).
- **Random Seed:** Fixed seed (`random_state=42`) with stratification on `Time_Overrun_Flag` to ensure reproducible, identical distributions across runs.

---

## 4. Models & Evaluation Results

Two model architectures were evaluated on the held-out 200 test projects:
- **Primary Model:** **XGBoost** (`XGBClassifier`) with tuned tree depth, learning rate, and subsampling.
- **Baseline Model:** **Random Forest** (`RandomForestClassifier`, 100 estimators, max depth 6).

### Performance Metrics on Test Set (N = 200)

| Risk Model | Algorithm | Accuracy | Precision | Recall | F1 Score | ROC-AUC |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **Time Overrun Risk** | **XGBoost (Primary)** | **83.50%** | **83.70%** | **81.05%** | **82.35%** | **0.9111** |
| | Random Forest (Baseline) | 83.00% | 81.44% | 83.16% | 82.29% | 0.9139 |
| **Cost Overrun Risk** | **XGBoost (Primary)** | **86.50%** | **87.30%** | **74.32%** | **80.29%** | **0.9229** |
| | Random Forest (Baseline) | 84.00% | 88.89% | 64.86% | 75.00% | 0.9313 |
| **Implementation Risk** | **XGBoost (Primary)** | **77.00%** | **57.50%** | **44.23%** | **50.00%** | **0.7885** |
| | Random Forest (Baseline) | 80.00% | 66.67% | 46.15% | 54.55% | 0.8034 |

### Metric Insights:
- **Balanced Tradeoffs:** Precision and Recall are balanced; the models achieve strong discrimination ($\text{ROC-AUC} > 0.91$ for schedule and cost risks).
- **Realistic Performance:** The metrics reflect genuine learning on noisy tabular data rather than artificially inflated 99% accuracy figures.
- **Implementation Risk Complexity:** Predicting multifaceted operational friction is naturally more challenging, showing ~77–80% accuracy and ~0.79 ROC-AUC.

---

## 5. Overall Risk Score & Decision Levels

### A. Probability Outputs
Each primary XGBoost model predicts the exact probability ($0.0$ to $1.0$) of risk occurrence:
- $P_{\text{time}}$: Probability of schedule delay.
- $P_{\text{cost}}$: Probability of budget overrun.
- $P_{\text{impl}}$: Probability of high operational implementation risk.

### B. Composite Formula (0–100 Scale)
A weighted linear combination converts the individual probabilities into an intuitive, institutional 0–100 executive risk index:

$$\text{Overall Risk Score} = \Big(0.40 \times P_{\text{time}} + 0.35 \times P_{\text{cost}} + 0.25 \times P_{\text{impl}}\Big) \times 100$$

**Rationale for Weights:**
- **Time Overrun (40%):** Schedule delay is the most immediate leading indicator of all subsequent distress.
- **Cost Overrun (35%):** Fiscal escalation creates statutory and funding liabilities.
- **Implementation Risk (25%):** Operational friction captures institutional and clearance bottlenecks.

### C. Risk Level Tiers
- **🟢 LOW RISK (`0.0 – 34.9`):** Project progressing as planned; minor or negligible issues; normal monitoring.
- **🟡 MEDIUM RISK (`35.0 – 64.9`):** Watchlist status; early warning signs detected in procurement, clearances, or milestone slippages.
- **🔴 HIGH RISK (`65.0 – 100.0`):** Critical distress; significant likelihood of severe delays and cost escalation requiring PMU intervention.

---

## 6. Example Inferences from Verified Test Projects

| Project ID | Sector & Type | Key Conditions | Time Risk | Cost Risk | Impl Risk | Overall Score | Risk Level |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **PRJ-0001** | Water / Water Supply | Contractor Good, 4/23 milestones delayed, on-track spend | 7.9% | 6.2% | 5.7% | **6.8 / 100** | 🟢 **LOW** |
| **PRJ-0010** | Education / School | Contractor Average, 0/18 milestones delayed, minimal approvals pending | 3.4% | 7.6% | 7.6% | **5.9 / 100** | 🟢 **LOW** |
| **PRJ-0005** | Transport / Railway | Contractor Good, but 9/20 milestones delayed, 5 pending approvals, 79d procurement delay | 97.0% | 81.4% | 85.7% | **88.7 / 100** | 🔴 **HIGH** |
| **PRJ-0849** | Transport / Road | Contractor Poor, 4/16 milestones delayed, 11% physical progress gap | 94.7% | 97.0% | 83.5% | **92.7 / 100** | 🔴 **HIGH** |

---

## 7. Model Artifacts Saved in `models/`

| File Name | Size | Purpose |
|:---|:---:|:---|
| `preprocessor.joblib` | ~4.5 KB | Serialized ColumnTransformer (imputation + one-hot encoding). |
| `time_overrun_model.joblib` | ~156 KB | Serialized primary XGBoost model for Time Overrun Risk. |
| `cost_overrun_model.joblib` | ~158 KB | Serialized primary XGBoost model for Cost Overrun Risk. |
| `implementation_risk_model.joblib` | ~158 KB | Serialized primary XGBoost model for Implementation Risk. |
| `model_metadata.json` | ~3.3 KB | Stored evaluation metrics, feature lists, weights, and thresholds. |

---

## 8. Synthetic Data Limitation Notice
> **Transparency Disclosure:**  
> These models were trained and validated on a **representative synthetic dataset** (`data/projects.csv`) generated for the Smart India Hackathon 2026 prototype. While the dataset captures realistic engineering patterns (delays in land acquisition, procurement lags, progress divergence), **these models have not been trained on confidential government infrastructure data**. 
> 
> Real-world deployment will require calibration against actual state and central infrastructure project databases. Accuracies and ROC-AUC scores reported here reflect performance on synthetic benchmarks and must not be cited as empirical real-world validation.

---

## 9. Checkpoint 3 Update: SHAP Explainability Engine
In Checkpoint 3, these trained XGBoost models are fully interpreted using **TreeSHAP** via `ml/explain.py`. 
- **Explainability Module:** [`ml/explain.py`](file:///d:/OnTrack-AI/ml/explain.py)
- **Detailed Report & Visualizations:** [`docs/EXPLAINABILITY_REPORT.md`](file:///d:/OnTrack-AI/docs/EXPLAINABILITY_REPORT.md)
- **Example Visualizations:** Saved in `docs/shap_examples/` (Waterfall and Local Bar plots).
- **Core Principles:** Mathematical verification ($\text{base\_value} + \sum \phi_i = \text{margin}$), clear separation of positive risk factors vs. protective buffers, and explicit disclaimers regarding statistical attribution vs. causation.

