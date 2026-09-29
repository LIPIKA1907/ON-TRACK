"""
OnTrack AI — Early Warning Engine
Smart India Hackathon 2026 | Problem Statement: SIH26103

Prototype-level early warning logic based on predicted risk
and project performance indicators.
"""

from typing import Dict, List, Any

try:
    from ml.predict import predict_project_risk
except ImportError:
    from predict import predict_project_risk


def generate_early_warning(
    project_record: Dict[str, Any],
    risk_result: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate an early-warning assessment for a project.

    Parameters:
        project_record: Project input features.
        risk_result: Optional existing output from predict_project_risk().

    Returns:
        Dictionary containing warning level, message and triggered warnings.
    """

    # ---------------------------------------------------------
    # Get risk prediction if it wasn't already supplied
    # ---------------------------------------------------------
    if risk_result is None:
        risk_result = predict_project_risk(project_record)

    risk_score = float(
        risk_result.get("overall_risk_score", 0) or 0
    )

    # ---------------------------------------------------------
    # Determine overall warning level
    # Consistent with predict.py:
    # LOW < 35
    # MEDIUM 35-64.9
    # HIGH >= 65
    # ---------------------------------------------------------
    if risk_score >= 65:
        warning_level = "HIGH"
        message = (
            "Project requires immediate attention based on current "
            "risk indicators."
        )
    elif risk_score >= 35:
        warning_level = "MEDIUM"
        message = (
            "Project requires closer monitoring based on current "
            "risk indicators."
        )
    else:
        warning_level = "LOW"
        message = (
            "No major early-warning condition detected from the "
            "current risk indicators."
        )

    warnings: List[str] = []

    # Helper to check if a field has a valid, non-null value
    def _get_valid_val(key: str) -> Any:
        v = project_record.get(key)
        if v is None or v == "":
            return None
        try:
            fv = float(v)
            if fv != fv:  # check for NaN
                return None
            return fv
        except (ValueError, TypeError):
            return None

    # ---------------------------------------------------------
    # 1. Physical progress gap
    # ---------------------------------------------------------
    physical_progress = _get_valid_val("Physical_Progress")
    planned_progress = _get_valid_val("Planned_Progress")

    if physical_progress is not None and planned_progress is not None:
        progress_gap = planned_progress - physical_progress
        if progress_gap >= 20:
            warnings.append("Physical progress is significantly below planned progress.")
        elif progress_gap >= 10:
            warnings.append("Physical progress is below planned progress.")

    # ---------------------------------------------------------
    # 2. Schedule & Cost Overruns (from official/derived data)
    # ---------------------------------------------------------
    time_overrun = _get_valid_val("Time_Overrun_Months")
    if time_overrun is not None:
        if time_overrun >= 12:
            warnings.append(f"Significant schedule delay of {int(time_overrun)} months beyond original completion date.")
        elif time_overrun >= 3:
            warnings.append(f"Schedule slippage of {int(time_overrun)} months detected.")

    cost_overrun = _get_valid_val("Cost_Overrun_Pct")
    if cost_overrun is not None:
        if cost_overrun >= 10:
            warnings.append(f"High cost escalation: {cost_overrun:.1f}% above approved sanction budget.")
        elif cost_overrun >= 5:
            warnings.append(f"Cost escalation: {cost_overrun:.1f}% above approved sanction budget.")

    # ---------------------------------------------------------
    # 3. Milestone delays (evaluated only when tracked)
    # ---------------------------------------------------------
    milestones_total = _get_valid_val("Milestones_Total")
    milestones_delayed = _get_valid_val("Milestones_Delayed")

    if milestones_total is not None and milestones_total > 0 and milestones_delayed is not None:
        delayed_ratio = milestones_delayed / milestones_total
        if delayed_ratio >= 0.50:
            warnings.append("A significant proportion of project milestones are delayed.")
        elif delayed_ratio >= 0.25:
            warnings.append("Multiple project milestones are delayed.")

    # ---------------------------------------------------------
    # 4. Procurement delay (evaluated only when tracked)
    # ---------------------------------------------------------
    procurement_delay = _get_valid_val("Procurement_Delay_Days")
    if procurement_delay is not None:
        if procurement_delay >= 60:
            warnings.append("Procurement delay is high.")
        elif procurement_delay >= 30:
            warnings.append("Procurement activities are experiencing delays.")

    # ---------------------------------------------------------
    # 5. Pending approvals (evaluated only when tracked)
    # ---------------------------------------------------------
    approvals_pending = _get_valid_val("Approvals_Pending")
    if approvals_pending is not None:
        if approvals_pending >= 5:
            warnings.append("Several project approvals are pending.")
        elif approvals_pending >= 2:
            warnings.append("Pending approvals may affect project implementation.")

    # ---------------------------------------------------------
    # 6. Land acquisition (evaluated only when tracked)
    # ---------------------------------------------------------
    land_progress = _get_valid_val("Land_Acquisition_Progress")
    if land_progress is not None:
        if land_progress < 40:
            warnings.append("Land acquisition progress is low.")
        elif land_progress < 70:
            warnings.append("Land acquisition is incomplete.")

    # ---------------------------------------------------------
    # 7. Scope changes (evaluated only when tracked)
    # ---------------------------------------------------------
    scope_changes = _get_valid_val("Scope_Changes")
    if scope_changes is not None:
        if scope_changes >= 5:
            warnings.append("Frequent scope changes may affect the project baseline.")
        elif scope_changes >= 3:
            warnings.append("Multiple scope changes have been recorded.")

    # ---------------------------------------------------------
    # 8. Average milestone delay (evaluated only when tracked)
    # ---------------------------------------------------------
    avg_delay = _get_valid_val("Average_Milestone_Delay_Days")
    if avg_delay is not None and avg_delay >= 60:
        warnings.append("Average milestone delay is high.")

    # ---------------------------------------------------------
    # Limit warnings for a clean dashboard
    # ---------------------------------------------------------
    warnings = warnings[:6]

    return {
        "warning_level": warning_level,
        "message": message,
        "risk_score": round(risk_score, 1),
        "warnings": warnings
    }


def main():
    """
    Test the early-warning engine with three sample projects.
    """

    test_projects = [
        {
            "Project_ID": "TEST-LOW",
            "Physical_Progress": 75,
            "Planned_Progress": 78,
            "Milestones_Total": 10,
            "Milestones_Delayed": 1,
            "Procurement_Delay_Days": 10,
            "Approvals_Pending": 0,
            "Land_Acquisition_Progress": 95,
            "Scope_Changes": 0
        },
        {
            "Project_ID": "TEST-MEDIUM",
            "Physical_Progress": 50,
            "Planned_Progress": 65,
            "Milestones_Total": 10,
            "Milestones_Delayed": 3,
            "Procurement_Delay_Days": 35,
            "Approvals_Pending": 3,
            "Land_Acquisition_Progress": 65,
            "Scope_Changes": 2
        },
        {
            "Project_ID": "TEST-HIGH",
            "Physical_Progress": 30,
            "Planned_Progress": 65,
            "Milestones_Total": 10,
            "Milestones_Delayed": 7,
            "Procurement_Delay_Days": 80,
            "Approvals_Pending": 6,
            "Land_Acquisition_Progress": 35,
            "Scope_Changes": 5
        }
    ]

    # Prototype test risk scores.
    # The actual application will obtain these from predict_project_risk().
    test_risk_scores = [20, 50, 80]

    print("=" * 70)
    print("OnTrack AI — Early Warning Engine Test")
    print("=" * 70)

    for project, score in zip(test_projects, test_risk_scores):

        risk_result = {
            "overall_risk_score": score,
            "risk_level": (
                "LOW" if score < 35
                else "MEDIUM" if score < 65
                else "HIGH"
            )
        }

        result = generate_early_warning(
            project,
            risk_result
        )

        print(f"\nProject: {project['Project_ID']}")
        print(f"Risk Score: {result['risk_score']}")
        print(f"Warning Level: {result['warning_level']}")
        print(f"Message: {result['message']}")

        if result["warnings"]:
            print("Warnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")
        else:
            print("Warnings: None")

    print("\n" + "=" * 70)
    print("Early-warning test completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()