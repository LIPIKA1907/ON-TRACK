import csv
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ml.predict import predict_project_risk
from ml.explain import explain_all_risks
from ml.benchmark import benchmark_project
from ml.what_if import simulate_what_if
from ml.recommendations import generate_recommendations
from ml.early_warning import generate_early_warning

app = FastAPI(title="OnTrack AI API", description="AI-powered infrastructure project monitoring and risk analysis", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173" "https://ontrack-ai-kappa.vercel.app",], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class ProjectRequest(BaseModel):
    project: Dict[str, Any]

class WhatIfRequest(BaseModel):
    project: Dict[str, Any]
    modifications: Dict[str, Any]
    include_explanations: bool = False

NUMERIC_FIELDS = {"Approved_Cost","Planned_Duration","Elapsed_Duration","Physical_Progress","Planned_Progress","Financial_Progress","Expenditure","Milestones_Total","Milestones_Delayed","Average_Milestone_Delay_Days","Procurement_Delay_Days","Land_Acquisition_Progress","Approvals_Pending","Scope_Changes","Time_Overrun_Months","Cost_Overrun_Pct","Time_Overrun_Flag","Cost_Overrun_Flag","Implementation_Risk_Flag"}

def load_projects_from_csv():
    csv_path = Path(__file__).resolve().parents[1] / "data" / "projects.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Project dataset not found: {csv_path}")
    projects = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            project = {}
            for key, value in row.items():
                if key in NUMERIC_FIELDS and value not in (None, ""):
                    try:
                        number = float(value)
                        project[key] = int(number) if number.is_integer() else number
                    except ValueError:
                        project[key] = value
                else:
                    project[key] = value
            projects.append(project)
    return projects

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "OnTrack AI API"}

@app.get("/projects")
def get_projects():
    try:
        projects = load_projects_from_csv()
        return {"success": True, "count": len(projects), "projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
def predict_risk(request: ProjectRequest):
    try: return {"success": True, "result": predict_project_risk(request.project)}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@app.post("/explain")
def explain_risk(request: ProjectRequest):
    try: return {"success": True, "result": explain_all_risks(request.project)}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@app.post("/benchmark")
def benchmark(request: ProjectRequest):
    try: return {"success": True, "result": benchmark_project(request.project)}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@app.post("/what-if")
def what_if(request: WhatIfRequest):
    try: return {"success": True, "result": simulate_what_if(request.project, request.modifications, request.include_explanations)}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@app.post("/recommendations")
def recommendations(request: ProjectRequest):
    try: return {"success": True, "result": generate_recommendations(request.project)}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@app.post("/early-warning")
def early_warning(request: ProjectRequest):
    try: return {"success": True, "result": generate_early_warning(request.project)}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
def root():
    return {"message": "OnTrack AI API is running", "docs": "/docs"}
