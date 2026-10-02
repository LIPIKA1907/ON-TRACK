"""
OnTrack AI — LLM Service (Groq)
Smart India Hackathon 2026 | Problem Statement: SIH26103

Provides LLM inference via the Groq API for:
- Natural-language project risk summaries
- Context-aware recommendations
- Interactive project Q&A

Uses the OpenAI-compatible Groq API at https://api.groq.com/openai/v1
"""

import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI, APIError, APIConnectionError, AuthenticationError

load_dotenv()

logger = logging.getLogger("ontrack.llm")

XAI_API_KEY = os.getenv("XAI_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "qwen/qwen3.8-27b"

# Build the OpenAI client once (pointed at Groq)
_client: Optional[OpenAI] = None


def _get_client() -> Optional[OpenAI]:
    """Lazily initialise and return the OpenAI client for Groq."""
    global _client
    if _client is not None:
        return _client
    if not XAI_API_KEY:
        logger.warning("XAI_API_KEY is not set — LLM features will be unavailable.")
        return None
    _client = OpenAI(api_key=XAI_API_KEY, base_url=GROQ_BASE_URL)
    return _client


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


def is_llm_available() -> bool:
    """Check if the Groq LLM service is configured (API key present)."""
    return bool(XAI_API_KEY)


def get_available_models() -> List[str]:
    """Get list of models available via the Groq API."""
    if XAI_API_KEY:
        return [GROQ_MODEL]
    return []


def get_active_model() -> Optional[str]:
    """Return the active Groq model name."""
    if not XAI_API_KEY:
        return None
    return GROQ_MODEL


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
    Send a chat message to the Groq LLM with optional project context.

    Returns:
        Dict with 'response', 'model', 'success', and optional 'error' keys.
    """
    client = _get_client()
    if client is None:
        return {
            "success": False,
            "error": "Groq LLM is not configured. Please set XAI_API_KEY in the .env file.",
            "response": None,
            "model": None,
        }

    # Resolve model
    if not model:
        model = GROQ_MODEL

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

    # Call Groq via OpenAI-compatible SDK
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            temperature=0.2,
            top_p=0.9,
            max_tokens=256,
        )
        content = response.choices[0].message.content or ""
        return {
            "success": True,
            "response": content,
            "model": model,
        }
    except AuthenticationError:
        logger.warning("Groq API authentication failed — check XAI_API_KEY.")
        return {
            "success": False,
            "error": "Groq API authentication failed. Please verify your XAI_API_KEY.",
            "response": None,
            "model": model,
        }
    except APIConnectionError as e:
        logger.warning(f"Groq API connection error: {e}")
        return {
            "success": False,
            "error": "Failed to connect to the Groq API. Check your internet connection.",
            "response": None,
            "model": model,
        }
    except APIError as e:
        logger.warning(f"Groq API error: {e}")
        return {
            "success": False,
            "error": f"Groq API error: {e.message}",
            "response": None,
            "model": model,
        }
    except Exception as e:
        logger.warning(f"Groq request error: {e}")
        return {
            "success": False,
            "error": f"Failed to get response from Groq: {e}",
            "response": None,
            "model": model,
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
    running = is_llm_available()
    models = get_available_models() if running else []
    active = get_active_model() if running else None

    return {
        "llm_available": running,
        "available_models": models,
        "active_model": active,
        "llm_provider": "Groq",
        "llm_base_url": GROQ_BASE_URL,
    }
