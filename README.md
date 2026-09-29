# OnTrack AI — Infrastructure Project Intelligence System

> **AI-Assisted Infrastructure Project Monitoring & Early-Warning System**  
> **Smart India Hackathon 2026 | Problem Statement: SIH26103**  
> **Supporting Ministry of Statistics and Programme Implementation (MoSPI) PAIMANA**

---

## 📌 Executive Summary
**OnTrack AI** is an AI-driven decision-support platform designed for project monitoring units, administrators, and infrastructure planners. It enables proactive risk mitigation across major Central Sector Infrastructure projects before costly time overruns and budget escalations materialize.

The application natively supports **two operational data modes** toggleable directly from the dashboard:
1. **🇮🇳 SIH / MoSPI PAIMANA Official Data:** 1,731 Central Sector Infrastructure Projects (sanctioned at ₹150 Crore+) from the official PAIMANA monitoring portal ([paimana-proj.mospi.gov.in](https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew)).
2. **⚙️ Synthetic Demonstration Data:** 1,000 baseline projects created for prototype testing and methodology validation.

---

## 🚀 Quick Start (Windows)

### Option 1: Automated Batch Scripts (Recommended)

1. **One-Time Setup:**
   Double-click `setup_ontrack.bat` (or run in terminal):
   ```cmd
   setup_ontrack.bat
   ```
   *Creates the Python virtual environment (`.venv`), installs all backend/ML dependencies, and installs React/Vite dependencies.*

2. **Launch Application:**
   Double-click `start_ontrack.bat` (or run in terminal):
   ```cmd
   start_ontrack.bat
   ```
   *Automatically starts the FastAPI backend (port 8000) and React frontend (port 5173), and opens the dashboard in your default browser.*

---

### Option 2: Manual Terminal Startup

**Terminal 1 — Backend (FastAPI):**
```cmd
cd OnTrack-AI
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend URL:* `http://127.0.0.1:8000`  
*Interactive Swagger API Docs:* `http://127.0.0.1:8000/docs`

**Terminal 2 — Frontend (React + Vite):**
```cmd
cd OnTrack-AI\frontend
npm install
npm run dev
```
*Frontend URL:* `http://localhost:5173`

---

## 🌐 System URLs & Endpoints

| Service | Local URL | Description |
|---|---|---|
| **Frontend Dashboard** | `http://localhost:5173` | Interactive Executive Dashboard with Source Switcher |
| **Backend API Root** | `http://127.0.0.1:8000/` | API Status & PAIMANA connectivity status |
| **API Health Check** | `http://127.0.0.1:8000/health` | Service health status |
| **Data Sources** | `http://127.0.0.1:8000/sources` | Metadata for SIH / PAIMANA and Synthetic sources |
| **Projects (PAIMANA)** | `http://127.0.0.1:8000/projects?source=sih` | 1,731 official MoSPI projects |
| **Projects (Synthetic)** | `http://127.0.0.1:8000/projects?source=synthetic` | 1,000 prototype demonstration projects |
| **Risk Prediction** | `POST /predict` | Composite risk scoring (Time, Cost, Implementation) |
| **SHAP Explanations** | `POST /explain` | TreeSHAP feature attributions with safe fallback |
| **Benchmarking** | `POST /benchmark` | Factual peer comparison across sector, scale, & duration |
| **What-If Simulation** | `POST /what-if` | In-memory counterfactual scenario analysis |
| **Early Warning** | `POST /early-warning` | Proactive alert triggers based on verified metrics |
| **Recommendations** | `POST /recommendations` | Prioritized interventions derived from project indicators |

---

## 🏛️ Official PAIMANA Data Integration

- **Source Portal:** Ministry of Statistics and Programme Implementation (MoSPI), Government of India
- **Live Portal:** `https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew`
- **Report Page:** `https://paimana-proj.mospi.gov.in/ReportPage`
- **Freeze Date:** August 2026 (Month: 08, Year: 2026)
- **Monitored Scope:** 1,731 Central Sector Infrastructure Projects (₹150 Cr and above)
- **Directory:** `data/paimana/`
  - `paimana_raw_projects.json` — Unmodified raw extract from MoSPI PAIMANA API.
  - `paimana_projects.csv` — Full tabular representation of raw attributes.
  - `paimana_normalized.csv` — Unified schema mapped to OnTrack AI specifications.
  - `PAIMANA_METADATA.md` — Complete data dictionary, provenance, and citation.

### Data Governance & Strict Non-Fabrication Guarantee
In accordance with ethical AI guidelines, **no government data is ever invented or fabricated**:
- Ground truth fields (`Approved_Cost`, `Expenditure`, `Physical_Progress`, sanction/revised dates) are extracted directly from official feeds.
- Derived metrics (`Time_Overrun_Months`, `Cost_Overrun_Pct`, `Planned_Progress`, `Financial_Progress`) use explicit, documented mathematical formulas.
- Micro operational metrics not published in the official feed (`Milestones_Total`, `Approvals_Pending`, `Procurement_Delay_Days`, `Contractor_Performance`) are **strictly preserved as null/NaN**.
- The ML inference and explainability engines safely handle missing operational indicators via baseline median/mode imputation without crashing.

---

## 📁 Repository Structure

```
PAIMANA/
├── setup_ontrack.bat            # Automated Windows environment installer
├── start_ontrack.bat            # Automated Windows launcher (backend + frontend)
└── OnTrack-AI/
    ├── backend/                 # FastAPI REST services
    │   ├── main.py              # Application entrypoint & routing
    │   └── paimana_service.py   # PAIMANA loader, metadata, & validation service
    ├── frontend/                # React + Vite application
    │   └── src/
    │       ├── App.jsx          # Dashboard, source toggle, views, & UI
    │       └── App.css          # Government institutional styling
    ├── data/
    │   ├── projects.csv         # Baseline synthetic dataset (N=1,000)
    │   └── paimana/             # Official MoSPI PAIMANA dataset
    │       ├── paimana_raw_projects.json
    │       ├── paimana_projects.csv
    │       ├── paimana_normalized.csv
    │       └── PAIMANA_METADATA.md
    ├── ml/                      # Machine Learning & Analytics Engines
    │   ├── predict.py           # Multi-model risk prediction
    │   ├── explain.py           # SHAP explainability engine with fallback
    │   ├── benchmark.py         # Multi-tier peer benchmarking (PAIMANA + Synthetic)
    │   ├── what_if.py           # In-memory counterfactual simulation
    │   ├── early_warning.py     # Safe alert triggering engine
    │   └── recommendations.py   # Rule-based decision-support interventions
    ├── models/                  # Serialized XGBoost models & preprocessors
    └── requirements.txt         # Python dependencies
```
