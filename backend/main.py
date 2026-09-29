import csv
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ml.predict import predict_project_risk
from ml.explain import explain_all_risks
from ml.benchmark import benchmark_project
from ml.what_if import simulate_what_if
from ml.recommendations import generate_recommendations
from ml.early_warning import generate_early_warning
from ml.llm_service import chat as llm_chat, get_llm_status, generate_risk_summary
from backend.paimana_service import paimana_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ontrack.api")

app = FastAPI(
    title="OnTrack AI API",
    description="AI-powered infrastructure project monitoring and risk analysis (SIH26103 / MoSPI PAIMANA)",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ontrack-ai-kappa.vercel.app",
       " https://on-track-fawn.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProjectRequest(BaseModel):
    project: Dict[str, Any]

class WhatIfRequest(BaseModel):
    project: Dict[str, Any]
    modifications: Dict[str, Any]
    include_explanations: bool = False

class ChatRequest(BaseModel):
    message: str
    project: Optional[Dict[str, Any]] = None
    risk_data: Optional[Dict[str, Any]] = None
    explain_data: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = None
    model: Optional[str] = None

class RiskSummaryRequest(BaseModel):
    project: Dict[str, Any]
    risk_data: Dict[str, Any]
    explain_data: Optional[Dict[str, Any]] = None
    model: Optional[str] = None

def sanitize_for_json(obj: Any) -> Any:
    """Recursively replace NaN/Inf float values with None so json.dumps won't crash."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    return obj

NUMERIC_FIELDS = {
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
    "Time_Overrun_Months",
    "Cost_Overrun_Pct",
    "Time_Overrun_Flag",
    "Cost_Overrun_Flag",
    "Implementation_Risk_Flag",
}

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
    paimana_avail = paimana_service.is_available()
    llm = get_llm_status()
    return {
        "status": "ok",
        "service": "OnTrack AI API",
        "paimana_status": "CONNECTED" if paimana_avail else "REQUIRES DATA FILE",
        "paimana_available": paimana_avail,
        "llm_status": "CONNECTED" if llm["ollama_running"] else "OFFLINE",
        "llm_model": llm.get("active_model"),
    }

@app.get("/sources")
def get_data_sources():
    """Returns available project data sources and their status."""
    paimana_avail = paimana_service.is_available()
    paimana_count = len(paimana_service.load_projects()) if paimana_avail else 0

    return {
        "sources": [
            {
                "id": "sih",
                "name": "MoSPI PAIMANA Official Data",
                "is_synthetic": False,
                "is_available": paimana_avail,
                "project_count": paimana_count,
                "snapshot_date": "August 2026",
                "portal_url": "https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew",
                "badge": "MoSPI Official (August 2026)",
                "status": "CONNECTED" if paimana_avail else "REQUIRES DATA FILE",
            }
        ]
    }

@app.get("/projects")
def get_projects(source: str = Query("sih", description="Data source: 'sih' (MoSPI PAIMANA official)")):
    """
    Returns list of projects with source metadata.
    Defaults to source='sih' (MoSPI PAIMANA official data).
    """
    if not paimana_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="MoSPI PAIMANA official dataset is currently unavailable. Please place data in data/paimana/paimana_normalized.csv.",
        )
    try:
        projects = paimana_service.load_projects()
        return {
            "success": True,
            "source": "sih",
            "source_name": "MoSPI PAIMANA Official Infrastructure Projects",
            "is_synthetic": False,
            "project_count": len(projects),
            "snapshot_date": "August 2026",
            "portal_url": "https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew",
            "count": len(projects),
            "projects": projects,
        }
    except Exception as e:
        logger.error(f"Error loading PAIMANA projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load PAIMANA projects: {str(e)}")

@app.post("/predict")
def predict_risk(request: ProjectRequest):
    try:
        return sanitize_for_json({"success": True, "result": predict_project_risk(request.project)})
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/explain")
def explain_risk(request: ProjectRequest):
    try:
        return sanitize_for_json({"success": True, "result": explain_all_risks(request.project)})
    except Exception as e:
        logger.error(f"Explanation error: {e}")
        # Safe fallback if explainability throws unexpected error
        return sanitize_for_json({
            "success": True,
            "result": {
                "project_id": request.project.get("Project_ID", "UNKNOWN"),
                "overall_risk_score": 50.0,
                "risk_level": "MEDIUM",
                "time_overrun": {"fallback": True, "fallback_reason": str(e), "top_risk_factors": []},
                "cost_overrun": {"fallback": True, "fallback_reason": str(e), "top_risk_factors": []},
                "implementation_risk": {"fallback": True, "fallback_reason": str(e), "top_risk_factors": []},
                "cross_cutting_primary_drivers": [],
            }
        })

@app.post("/benchmark")
def benchmark(request: ProjectRequest):
    try:
        return sanitize_for_json({"success": True, "result": benchmark_project(request.project)})
    except Exception as e:
        logger.error(f"Benchmarking error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/what-if")
def what_if(request: WhatIfRequest):
    try:
        return sanitize_for_json({
            "success": True,
            "result": simulate_what_if(
                request.project,
                request.modifications,
                request.include_explanations,
            ),
        })
    except Exception as e:
        logger.error(f"What-If error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/recommendations")
def recommendations(request: ProjectRequest):
    try:
        return sanitize_for_json({"success": True, "result": generate_recommendations(request.project)})
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/early-warning")
def early_warning(request: ProjectRequest):
    try:
        return sanitize_for_json({"success": True, "result": generate_early_warning(request.project)})
    except Exception as e:
        logger.error(f"Early warning error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
def root():
    llm = get_llm_status()
    return {
        "message": "OnTrack AI API is running",
        "paimana_status": "CONNECTED" if paimana_service.is_available() else "REQUIRES DATA FILE",
        "llm_status": "CONNECTED" if llm["ollama_running"] else "OFFLINE",
        "llm_model": llm.get("active_model"),
        "docs": "/docs",
    }

@app.get("/llm-status")
def llm_status():
    """Check local LLM (Ollama) availability and loaded models."""
    status = get_llm_status()
    return {
        "success": True,
        **status,
    }

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    """Send a message to the local LLM with optional project context."""
    try:
        result = llm_chat(
            message=request.message,
            project=request.project,
            risk_data=request.risk_data,
            explain_data=request.explain_data,
            history=request.history,
            model=request.model,
        )
        return sanitize_for_json(result)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"success": False, "error": str(e), "response": None, "model": None}

@app.post("/risk-summary")
def risk_summary(request: RiskSummaryRequest):
    """Generate a natural-language risk summary using the local LLM."""
    try:
        result = generate_risk_summary(
            project=request.project,
            risk_data=request.risk_data,
            explain_data=request.explain_data,
            model=request.model,
        )
        return sanitize_for_json(result)
    except Exception as e:
        logger.error(f"Risk summary error: {e}")
        return {"success": False, "error": str(e), "response": None, "model": None}
