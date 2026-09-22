# OnTrack AI

> **AI-Assisted Infrastructure Project Monitoring & Early-Warning System**  
> **Smart India Hackathon 2026 — Problem Statement: SIH26103**

---

## 📌 Executive Summary
**OnTrack AI** is a decision-support platform designed to help project monitoring units, administrators, and infrastructure planners identify, explain, and mitigate risks across major capital projects before costly delays occur.

The system evaluates:
1. **Time Overrun Risk** — Likelihood and expected extent of schedule delays.
2. **Cost Overrun Risk** — Probability of budget escalation and fiscal slippage.
3. **Implementation Risk** — Operational vulnerabilities stemming from regulatory clearances, contractor execution, and ground bottlenecks.

---

## ⚠️ Synthetic Data Limitation & Transparency Notice
> **Important Prototype Disclosure:**  
> This prototype does **NOT** use confidential or proprietary government infrastructure monitoring data. All model training and demonstrations utilize a **representative synthetic dataset** engineered to capture real-world infrastructure dynamics (e.g., land acquisition hurdles, environmental clearances, cash flow disbursement ratios, physical vs. financial milestone divergence).
>
> - The model does not claim to have been trained on actual government records.
> - Prediction accuracies and validation metrics are grounded strictly in the synthetic benchmark dataset without fabrication.
> - Predictions are generated dynamically via trained machine learning models, not hardcoded mocks.

---

## 🔄 Core Product Workflow

```
PROJECT DATA
     ↓
PREDICT RISK (Time, Cost, and Implementation Risk Scoring)
     ↓
EXPLAIN (SHAP-driven Feature Attribution & Root Cause Analysis)
     ↓
BENCHMARK (Comparison Against Similar Historical Infrastructure Projects)
     ↓
SIMULATE (Counterfactual What-If Scenario Modeling)
     ↓
RECOMMEND (Targeted, Prioritized Interventions)
     ↓
EARLY WARNING (Proactive Alert Tiers: Low, Medium, Critical)
```

---

## 🛠️ Technology Stack

| Layer | Technologies | Role / Scope |
| :--- | :--- | :--- |
| **Frontend** | React, Vite | Clean, responsive government decision-support dashboard |
| **Backend** | Python, FastAPI | High-performance REST API services and analytical endpoints |
| **Machine Learning** | Scikit-learn, XGBoost, SHAP | Tabular risk classification, regression, and interpretability |
| **Data Processing** | Pandas, NumPy | Data transformation, feature engineering, and simulation logic |
| **Data Storage** | Flat Files (CSV / JSON) | Lightweight, portable prototype storage (no external DB engine) |

---

## 📂 Project Structure

```
OnTrack-AI/
├── frontend/             # User interface (React + Vite)
├── backend/              # REST API services (FastAPI)
├── ml/                   # Machine learning pipelines, feature engineering, & inference
├── data/                 # Representative synthetic datasets (CSV/JSON)
├── models/               # Serialized trained models & SHAP explainers
├── docs/                 # Architectural specifications, data dictionaries, & notes
├── README.md             # Project documentation & overview
├── PROJECT_CONTEXT.md    # In-depth architectural rules, scope, & constraints
└── .gitignore            # Version control exclusion rules
```

---

## 🎨 UI Guidelines (Government Decision-Support)
- **Palette:** Crisp white/neutral background with an institutional deep blue primary color.
- **Status Indicators:** Strictly tri-color indicator convention (Green = Low Risk, Amber = Medium Risk, Red = High Risk / Critical).
- **Style:** Clean, minimal, tabular, and chart-focused. No gradients, glassmorphism, or non-essential animations.

---

## 🚫 Out-of-Scope (Strict Anti-Scope)
To avoid unnecessary complexity in the hackathon prototype, the following are deliberately omitted:
- User authentication & role management
- LLMs, chatbots, or generative AI wrappers
- IoT or hardware sensor integrations
- External notification gateways (SMS, WhatsApp)
- Cloud microservice orchestrators (Kubernetes)
- External database engines (PostgreSQL, MongoDB)
