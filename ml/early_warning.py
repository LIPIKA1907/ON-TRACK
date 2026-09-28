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

    # ---------------------------------------------------------
    # 1. Physical progress gap
    # ---------------------------------------------------------
    physical_progress = float(
        project_record.get("Physical_Progress", 0) or 0
    )
    planned_progress = float(
        project_record.get("Planned_Progress", 0) or 0
    )

    progress_gap = planned_progress - physical_progress

    if progress_gap >= 20:
        warnings.append(
            "Physical progress is significantly below planned progress."
        )
    elif progress_gap >= 10:
        warnings.append(
            "Physical progress is below planned progress."
        )

    # ---------------------------------------------------------
    # 2. Milestone delays
    # ---------------------------------------------------------
    milestones_total = float(
        project_record.get("Milestones_Total", 0) or 0
    )
    milestones_delayed = float(
        project_record.get("Milestones_Delayed", 0) or 0
    )

    if milestones_total > 0:
        delayed_ratio = milestones_delayed / milestones_total

        if delayed_ratio >= 0.50:
            warnings.append(
                "A significant proportion of project milestones are delayed."
            )
        elif delayed_ratio >= 0.25:
            warnings.append(
                "Multiple project milestones are delayed."
            )

    # ---------------------------------------------------------
    # 3. Procurement delay
    # ---------------------------------------------------------
    procurement_delay = float(
        project_record.get("Procurement_Delay_Days", 0) or 0
    )

    if procurement_delay >= 60:
        warnings.append(
            "Procurement delay is high."
        )
    elif procurement_delay >= 30:
        warnings.append(
            "Procurement activities are experiencing delays."
        )

    # ---------------------------------------------------------
    # 4. Pending approvals
    # ---------------------------------------------------------
    approvals_pending = float(
        project_record.get("Approvals_Pending", 0) or 0
    )

    if approvals_pending >= 5:
        warnings.append(
            "Several project approvals are pending."
        )
    elif approvals_pending >= 2:
        warnings.append(
            "Pending approvals may affect project implementation."
        )

    # ---------------------------------------------------------
    # 5. Land acquisition
    # ---------------------------------------------------------
    land_progress = float(
        project_record.get("Land_Acquisition_Progress", 100) or 0
    )

    if land_progress < 40:
        warnings.append(
            "Land acquisition progress is low."
        )
    elif land_progress < 70:
        warnings.append(
            "Land acquisition is incomplete."
        )

    # ---------------------------------------------------------
    # 6. Scope changes
    # ---------------------------------------------------------
    scope_changes = float(
        project_record.get("Scope_Changes", 0) or 0
    )

    if scope_changes >= 5:
        warnings.append(
            "Frequent scope changes may affect the project baseline."
        )
    elif scope_changes >= 3:
        warnings.append(
            "Multiple scope changes have been recorded."
        )

    # ---------------------------------------------------------
    # 7. Average milestone delay
    # ---------------------------------------------------------
    avg_delay = float(
        project_record.get("Average_Milestone_Delay_Days", 0) or 0
    )

    if avg_delay >= 60:
        warnings.append(
            "Average milestone delay is high."
        )

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