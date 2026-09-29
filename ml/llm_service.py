"""
OnTrack AI — Local LLM Service (Ollama)
Smart India Hackathon 2026 | Problem Statement: SIH26103

Provides local, offline LLM inference via Ollama for:
- Natural-language project risk summaries
- Context-aware recommendations
- Interactive project Q&A

Uses the Ollama REST API at http://localhost:11434
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ontrack.llm")

OLLAMA_BASE_URL = "http://localhost:11434"

# Preferred models in order of preference (smallest first for faster inference)
PREFERRED_MODELS = [
    "llama3.2:1b",
    "llama3.2:3b",
    "llama3.2",
    "llama3.1:8b",
    "llama3.1",
    "llama3:8b",
    "llama3",
    "mistral",
    "phi3",
    "gemma2:2b",
    "gemma2",
    "qwen2.5:1.5b",
    "qwen2.5:3b",
    "qwen2.5",
    "tinyllama",
]


SYSTEM_PROMPT = """You are OnTrack AI, an expert AI assistant for infrastructure project monitoring and risk analysis for the Government of India.
You are part of the Smart India Hackathon 2026 project (Problem Statement SIH26103), working with MoSPI PAIMANA official project data.

Your role:
- Answer user questions about project performance, delays, cost overruns, and risks.
- Act as a conversational assistant.

CRITICAL RULES:
1. Greetings or small talk (like "hi", "hello", "how are you"): give a short, friendly reply (1-2 lines) and offer 2-3 example questions about the project. Do NOT output any project data, SHAP analysis, or risk scores.
2. Answer ONLY what the user asked. Do not dump SHAP factors, risk scores, or recommendations unless explicitly requested.
3. Use the provided project data only when the question is about it, and NEVER invent numbers. If data is missing to answer a question, explicitly state that it is missing.
4. Keep answers short, direct, and in plain language.
"""


def _ollama_request(endpoint: str, payload: dict, timeout: int = 60) -> Optional[dict]:
    """Make a request to the Ollama REST API."""
    url = f"{OLLAMA_BASE_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        logger.warning(f"Ollama request failed: {e}")
        return None
    except Exception as e:
        logger.warning(f"Ollama request error: {e}")
        return None


def _ollama_get(endpoint: str, timeout: int = 10) -> Optional[dict]:
    """Make a GET request to the Ollama REST API."""
    url = f"{OLLAMA_BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method="GET")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        logger.warning(f"Ollama GET failed: {e}")
        return None
    except Exception as e:
        logger.warning(f"Ollama GET error: {e}")
        return None


def is_ollama_running() -> bool:
    """Check if Ollama server is running."""
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=5)
        return resp.getcode() == 200
    except Exception:
        return False


def get_available_models() -> List[str]:
    """Get list of models available in Ollama."""
    resp = _ollama_get("/api/tags")
    if resp and "models" in resp:
        return [m["name"] for m in resp["models"]]
    return []


def get_active_model() -> Optional[str]:
    """Find the best available model from the preferred list."""
    available = get_available_models()
    if not available:
        return None

    # Check preferred models first
    for preferred in PREFERRED_MODELS:
        for avail in available:
            if avail == preferred or avail.startswith(preferred.split(":")[0]):
                return avail

    # Fallback to first available model
    return available[0] if available else None


def format_project_context(project: Dict[str, Any], risk_data: Optional[Dict] = None, explain_data: Optional[Dict] = None) -> str:
    """Format project data into a concise context string for the LLM."""
    lines = []
    lines.append("=== PROJECT DATA ===")

    pid = project.get("Project_ID", "Unknown")
    lines.append(f"Project ID: {pid}")

    sector = project.get("Sector", "Unknown")
    ptype = project.get("Project_Type", "Unknown")
    lines.append(f"Sector: {sector} | Type: {ptype}")

    cost = project.get("Approved_Cost")
    if cost is not None:
        lines.append(f"Approved Cost: ₹{cost} Crore")

    planned_dur = project.get("Planned_Duration")
    elapsed_dur = project.get("Elapsed_Duration")
    if planned_dur is not None:
        lines.append(f"Planned Duration: {planned_dur} months | Elapsed: {elapsed_dur or 'N/A'} months")

    phys = project.get("Physical_Progress")
    planned = project.get("Planned_Progress")
    if phys is not None:
        lines.append(f"Physical Progress: {phys}% | Planned: {planned or 'N/A'}%")

    fin = project.get("Financial_Progress")
    exp = project.get("Expenditure")
    if fin is not None:
        lines.append(f"Financial Progress: {fin}% | Expenditure: ₹{exp or 'N/A'} Crore")

    time_overrun = project.get("Time_Overrun_Months")
    cost_overrun = project.get("Cost_Overrun_Pct")
    if time_overrun is not None:
        lines.append(f"Time Overrun: {time_overrun} months")
    if cost_overrun is not None:
        lines.append(f"Cost Overrun: {cost_overrun}%")

    if risk_data:
        lines.append("\n=== RISK ASSESSMENT ===")
        lines.append(f"Overall Risk Score: {risk_data.get('overall_risk_score', 'N/A')}/100")
        lines.append(f"Risk Level: {risk_data.get('risk_level', 'N/A')}")

        for dim_key in ["time_overrun", "cost_overrun", "implementation_risk"]:
            dim = risk_data.get(dim_key, {})
            prob = dim.get("risk_probability", "N/A")
            if isinstance(prob, (int, float)):
                prob = f"{prob * 100:.1f}%"
            lines.append(f"  {dim.get('risk_dimension', dim_key)}: {prob}")

    if explain_data:
        lines.append("\n=== SHAP EXPLANATION (Top Risk Drivers) ===")
        for dim_key in ["time_overrun", "cost_overrun", "implementation_risk"]:
            dim = explain_data.get(dim_key, {})
            factors = dim.get("top_risk_factors", [])
            if factors:
                lines.append(f"  {dim.get('risk_dimension', dim_key)}:")
                for f in factors[:3]:
                    lines.append(f"    • {f.get('feature', '?')}: {f.get('value', '?')} (SHAP: {f.get('contribution', 0):+.4f})")

    return "\n".join(lines)


def chat(
    message: str,
    project: Optional[Dict[str, Any]] = None,
    risk_data: Optional[Dict] = None,
    explain_data: Optional[Dict] = None,
    history: Optional[List[Dict[str, str]]] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a chat message to the local Ollama LLM with optional project context.

    Returns:
        Dict with 'response', 'model', 'success', and optional 'error' keys.
    """
    if not is_ollama_running():
        return {
            "success": False,
            "error": "Ollama is not running. Please start Ollama first (run 'ollama serve' in a terminal).",
            "response": None,
            "model": None,
        }

    # Resolve model
    if not model:
        model = get_active_model()
    if not model:
        return {
            "success": False,
            "error": "No LLM models found. Please pull a model first (e.g., 'ollama pull llama3.2:1b').",
            "response": None,
            "model": None,
        }

    # Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add project context if available
    if project:
        context = format_project_context(project, risk_data, explain_data)
        messages.append({
            "role": "system",
            "content": f"The user is currently viewing the following project:\n\n{context}",
        })

    # Add conversation history
    if history:
        for h in history[-6:]:  # Keep last 6 messages for context window
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

    # Add current message
    messages.append({"role": "user", "content": message})

    # Call Ollama
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "num_predict": 256,
        },
    }

    resp = _ollama_request("/api/chat", payload, timeout=120)

    if resp is None:
        return {
            "success": False,
            "error": "Failed to get response from Ollama. Is the model loaded?",
            "response": None,
            "model": model,
        }

    return {
        "success": True,
        "response": resp.get("message", {}).get("content", ""),
        "model": model,
        "total_duration_ms": resp.get("total_duration", 0) // 1_000_000,
    }


def generate_risk_summary(
    project: Dict[str, Any],
    risk_data: Dict[str, Any],
    explain_data: Optional[Dict] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a natural-language risk summary for a project.
    """
    prompt = (
        "Based on the project data and risk assessment provided, write a concise executive risk summary (3-5 sentences). "
        "Highlight the most critical risk drivers, their impact, and one key recommended action. "
        "Be specific and reference actual numbers from the data."
    )

    return chat(
        message=prompt,
        project=project,
        risk_data=risk_data,
        explain_data=explain_data,
        model=model,
    )


def get_llm_status() -> Dict[str, Any]:
    """Get the current status of the LLM service."""
    running = is_ollama_running()
    models = get_available_models() if running else []
    active = get_active_model() if running else None

    return {
        "ollama_running": running,
        "available_models": models,
        "active_model": active,
        "ollama_url": OLLAMA_BASE_URL,
    }
