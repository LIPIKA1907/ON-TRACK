# OnTrack AI — Project Context & Architectural Guidelines

## 1. Project Overview & Purpose
**OnTrack AI** is an AI-assisted infrastructure project monitoring and early-warning decision-support system. It is designed to assist government agencies, project monitoring units (PMUs), and infrastructure managers in detecting potential project slippages before they escalate into severe fiscal and scheduling delays.

The platform ingests project progress, contractual, and financial metrics, runs machine learning models to assess multi-dimensional risks, provides transparent interpretability (explaining *why* a risk exists), benchmarks projects against historical peers, evaluates "what-if" counterfactual scenarios, and provides actionable recommendations with early warnings.

---

## 2. SIH Problem Statement
- **Hackathon:** Smart India Hackathon 2026
- **Problem Statement ID:** SIH26103
- **Focus Area:** AI-driven Infrastructure Project Monitoring & Early Warning

---

## 3. Core Product Workflow
The application follows a strictly defined, end-to-end analytical workflow:

```
PROJECT DATA
     ↓
PREDICT RISK (Time Overrun, Cost Overrun, Implementation Risk)
     ↓
EXPLAIN (SHAP / Feature Attribution: why is this project at risk?)
     ↓
BENCHMARK (Compare performance against similar sectoral/regional projects)
     ↓
SIMULATE (What-if scenario analysis: e.g., budget reallocation, contractor changes)
     ↓
RECOMMEND (Pragmatic, prioritized interventions based on risk drivers)
     ↓
EARLY WARNING (Configurable risk thresholds, triggers, and alerts)
```

---

## 4. Prototype Data Limitation & Ethical Principles
**Critical Disclosure:**
- We do **NOT** have access to confidential or real government infrastructure project-monitoring datasets.
- The prototype uses a **representative synthetic dataset** designed to emulate real-world infrastructure parameters (e.g., project sector, tender value, planned vs. actual physical progress, disbursement rates, land acquisition status, environmental clearance flags, contractor performance).
- **Core Modeling Conduct:**
  - **Never** claim the model was trained on actual government data.
  - **Never** fabricate model accuracy metrics (e.g., claiming 99.9% accuracy).
  - **Never** hardcode fake predictions or simulate outputs via random mock functions without real model inference. All predictions must come from genuine models trained on the synthetic dataset.
  - All UI screens and reports must visibly disclose the synthetic data basis of this prototype.

---

## 5. Technology Stack

### Frontend
- **Framework:** React + Vite
- **Styling:** Vanilla CSS (or tailored utility-based styling conforming strictly to the UI rules below)
- **Visualizations:** Lightweight React charting library (e.g., Recharts or Chart.js) when needed

### Backend
- **Framework:** Python + FastAPI
- **Data Exchange:** REST APIs (JSON / standard payloads)
- **Data Layer:** Flat files (CSV / JSON) for datasets and project records. No external database engine at this stage.

### Machine Learning
- **Environment:** Python
- **Data Manipulation:** Pandas, NumPy
- **Modeling:** Scikit-learn, XGBoost
- **Interpretability:** SHAP (SHapley Additive exPlanations) for local and global feature attribution

---

## 6. Machine Learning Approach
1. **Risk Dimensions:**
   - **Time Overrun Risk:** Classification / Regression (predicting probability of delay or delay in days/months).
   - **Cost Overrun Risk:** Regression / Classification (predicting % budget escalation or high/medium/low cost overrun probability).
   - **Implementation Risk:** Composite operational risk score reflecting regulatory, vendor, and ground-level execution bottlenecks.
2. **Explainability:**
   - Use SHAP values computed during inference to determine the top positive and negative contributing factors for every individual project prediction.
3. **What-If Simulation:**
   - Allow users to modify key adjustable variables (e.g., budget allocation pacing, clearance timelines, contractor staffing) and re-run model inference on the fly to observe projected risk reduction.
4. **Benchmarking:**
   - Nearest-neighbor / similarity clustering to match a project against comparable historical projects (by sector, budget scale, terrain/state).

---

## 7. UI / UX Design Rules
The UI must strictly project an authentic, institutional, government decision-support aesthetic:
- **Tone:** Clean, professional, minimal, and authoritative.
- **Theme:** Light theme only.
- **Background:** White and crisp neutral backgrounds (`#FFFFFF`, `#F8FAFC`, `#F1F5F9`).
- **Primary Color:** Institutional deep blue / navy (`#1E3A8A`, `#2563EB`).
- **Status Colors Only:** 
  - Green (Low Risk / On Track)
  - Amber (Medium Risk / Watchlist)
  - Red (High Risk / Critical Early Warning)
- **Prohibited UI Elements:**
  - ❌ No gradients
  - ❌ No glassmorphism / blurred card overlays
  - ❌ No neon or glowing effects
  - ❌ No excessive animations or parallax transitions
  - ❌ No visual clutter or unnecessary card decorations

---

## 8. Planned Features (In Scope)
- Synthetic infrastructure dataset generator / loader.
- Risk prediction pipeline (Time, Cost, Implementation).
- SHAP-based risk factor breakdown and feature importance visualization.
- Sectoral and regional project benchmarking view.
- Interactive what-if scenario simulator.
- Actionable decision-support recommendations tailored to risk drivers.
- Early warning alerts dashboard with filtered risk tiers.

---

## 9. Anti-Scope: Explicitly Excluded Features
To prevent overengineering and keep the hackathon delivery focused and rigorous, the following are **strictly out of scope**:
- ❌ No user authentication, login systems, or JWT flows (single-user decision prototype)
- ❌ No AI chatbots or conversational assistants
- ❌ No Large Language Models (LLMs) or generative prompt chains
- ❌ No IoT sensors, camera feeds, or hardware integrations
- ❌ No SMS / WhatsApp / email delivery gateways
- ❌ No Kubernetes, Docker Swarm, or complex microservices architecture
- ❌ No payment gateways or financial billing systems
- ❌ No SQL / NoSQL database servers (PostgreSQL, MongoDB, etc.) at this stage
- ❌ No redundant infrastructure or complex cloud orchestration
