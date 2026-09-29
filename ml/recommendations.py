"""
OnTrack AI — Rule-Based Recommendation Engine
Smart India Hackathon 2026 | Problem Statement: SIH26103

Generates simple, explainable project-management recommendations
based on actual project indicators and predicted risk.
"""

from typing import Dict, List, Any


def generate_recommendations(
    project_record: Dict[str, Any],
    risk_result: Dict[str, Any] = None
) -> List[Dict[str, str]]:
    """
    Generate prioritized recommendations for a project.

    Parameters:
        project_record: Dictionary containing project input features.
        risk_result: Optional output from predict_project_risk().

    Returns:
        List of recommendation dictionaries.
    """

    recommendations = []

    # Helper function
    def add_recommendation(priority, issue, recommendation):
        recommendations.append({
            "priority": priority,
            "issue": issue,
            "recommendation": recommendation
        })

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
    # 1. Schedule & Cost Overruns (from official/derived data)
    # ---------------------------------------------------------
    time_overrun = _get_valid_val("Time_Overrun_Months")
    if time_overrun is not None:
        if time_overrun >= 12:
            add_recommendation(
                "High",
                f"Severe schedule delay ({int(time_overrun)} months overrun)",
                "Convene an empowered inter-ministerial review meeting to establish an expedited completion plan and identify critical path hindrances."
            )
        elif time_overrun >= 3:
            add_recommendation(
                "Medium",
                f"Project delayed by {int(time_overrun)} months",
                "Conduct joint progress review with executing agency to address schedule slippage against original sanction date."
            )

    cost_overrun = _get_valid_val("Cost_Overrun_Pct")
    if cost_overrun is not None:
        if cost_overrun >= 10:
            add_recommendation(
                "High",
                f"High cost overrun ({cost_overrun:.1f}% escalation)",
                "Submit Revised Cost Estimate (RCE) for administrative approval and conduct expenditure audit on high-variance work packages."
            )
        elif cost_overrun >= 5:
            add_recommendation(
                "Medium",
                f"Cost overrun detected ({cost_overrun:.1f}% escalation)",
                "Institute stricter monthly financial burn audits with the project authority to curb further budget escalation."
            )

    # ---------------------------------------------------------
    # 2. Procurement delay (evaluated only when tracked)
    # ---------------------------------------------------------
    procurement_delay = _get_valid_val("Procurement_Delay_Days")
    if procurement_delay is not None:
        if procurement_delay >= 60:
            add_recommendation(
                "High",
                "High procurement delay",
                "Review procurement timelines and identify delayed procurement activities."
            )
        elif procurement_delay >= 30:
            add_recommendation(
                "Medium",
                "Moderate procurement delay",
                "Monitor procurement activities and address pending procurement bottlenecks."
            )

    # ---------------------------------------------------------
    # 3. Milestone delays (evaluated only when tracked)
    # ---------------------------------------------------------
    milestones_total = _get_valid_val("Milestones_Total")
    milestones_delayed = _get_valid_val("Milestones_Delayed")

    if milestones_total is not None and milestones_total > 0 and milestones_delayed is not None:
        delayed_ratio = milestones_delayed / milestones_total
        if delayed_ratio >= 0.50:
            add_recommendation(
                "High",
                "Many project milestones are delayed",
                "Review delayed milestones and establish a recovery schedule for critical activities."
            )
        elif delayed_ratio >= 0.25:
            add_recommendation(
                "Medium",
                "Multiple milestones are delayed",
                "Monitor delayed milestones closely and identify activities affecting the project schedule."
            )

    # ---------------------------------------------------------
    # 4. Average milestone delay (evaluated only when tracked)
    # ---------------------------------------------------------
    avg_milestone_delay = _get_valid_val("Average_Milestone_Delay_Days")
    if avg_milestone_delay is not None:
        if avg_milestone_delay >= 60:
            add_recommendation(
                "High",
                "High average milestone delay",
                "Review the causes of prolonged milestone delays and establish corrective actions."
            )
        elif avg_milestone_delay >= 30:
            add_recommendation(
                "Medium",
                "Moderate milestone delay",
                "Track delayed activities and establish milestone-level recovery targets."
            )

    # ---------------------------------------------------------
    # 5. Physical progress vs planned progress
    # ---------------------------------------------------------
    physical_progress = _get_valid_val("Physical_Progress")
    planned_progress = _get_valid_val("Planned_Progress")

    if physical_progress is not None and planned_progress is not None:
        progress_gap = planned_progress - physical_progress
        if progress_gap >= 20:
            add_recommendation(
                "High",
                "Physical progress is significantly below planned progress",
                "Review the causes of schedule slippage and prioritize recovery of critical activities."
            )
        elif progress_gap >= 10:
            add_recommendation(
                "Medium",
                "Physical progress is below planned progress",
                "Monitor project progress against the baseline and address activities contributing to the gap."
            )

    # ---------------------------------------------------------
    # 6. Pending approvals (evaluated only when tracked)
    # ---------------------------------------------------------
    approvals_pending = _get_valid_val("Approvals_Pending")
    if approvals_pending is not None:
        if approvals_pending >= 5:
            add_recommendation(
                "High",
                "Several approvals are pending",
                "Prioritize pending approvals and track responsible stakeholders and expected resolution dates."
            )
        elif approvals_pending >= 2:
            add_recommendation(
                "Medium",
                "Pending approvals may affect implementation",
                "Monitor pending approvals and identify those that could affect project timelines."
            )

    # ---------------------------------------------------------
    # 7. Land acquisition (evaluated only when tracked)
    # ---------------------------------------------------------
    land_progress = _get_valid_val("Land_Acquisition_Progress")
    if land_progress is not None:
        if land_progress < 40:
            add_recommendation(
                "High",
                "Land acquisition progress is low",
                "Review unresolved land acquisition dependencies and prioritize cases affecting project activities."
            )
        elif land_progress < 70:
            add_recommendation(
                "Medium",
                "Land acquisition is incomplete",
                "Monitor pending land acquisition activities and their impact on project execution."
            )

    # ---------------------------------------------------------
    # 8. Scope changes (evaluated only when tracked)
    # ---------------------------------------------------------
    scope_changes = _get_valid_val("Scope_Changes")
    if scope_changes is not None:
        if scope_changes >= 5:
            add_recommendation(
                "High",
                "Frequent scope changes",
                "Review scope changes and assess their potential impact on project cost and schedule."
            )
        elif scope_changes >= 3:
            add_recommendation(
                "Medium",
                "Multiple scope changes",
                "Monitor scope changes and evaluate their effect on the approved project baseline."
            )

    # ---------------------------------------------------------
    # 9. Contractor performance (evaluated only when tracked)
    # ---------------------------------------------------------
    contractor_raw = project_record.get("Contractor_Performance")
    if contractor_raw:
        contractor = str(contractor_raw).strip().lower()
        if contractor in {
            "poor",
            "low",
            "weak",
            "below average",
            "unsatisfactory"
        }:
            add_recommendation(
                "High",
                "Low contractor performance",
                "Review contractor performance and establish corrective actions for delayed or incomplete activities."
            )
        elif contractor in {
            "average",
            "moderate"
        }:
            add_recommendation(
                "Medium",
                "Moderate contractor performance",
                "Monitor contractor delivery against planned milestones and contractual commitments."
            )

    # ---------------------------------------------------------
    # 9. Overall risk
    # ---------------------------------------------------------
    if risk_result:
        risk_score = float(
            risk_result.get("overall_risk_score", 0) or 0
        )

        if risk_score >= 65:
            add_recommendation(
                "High",
                "Overall project risk is high",
                "Review the major risk drivers and prioritize corrective actions for critical project dependencies."
            )
        elif risk_score >= 35:
            add_recommendation(
                "Medium",
                "Overall project risk is moderate",
                "Continue close monitoring of the project's major risk indicators."
            )

    # ---------------------------------------------------------
    # Sort recommendations by priority
    # ---------------------------------------------------------
    priority_order = {
        "High": 1,
        "Medium": 2,
        "Low": 3
    }

    recommendations.sort(
        key=lambda x: priority_order.get(x["priority"], 99)
    )

    # Keep prototype output concise
    return recommendations[:6]


def main():
    """
    Simple demonstration using a sample project record.
    """

    sample_project = {
        "Procurement_Delay_Days": 75,
        "Milestones_Total": 10,
        "Milestones_Delayed": 6,
        "Average_Milestone_Delay_Days": 45,
        "Physical_Progress": 35,
        "Planned_Progress": 60,
        "Approvals_Pending": 5,
        "Land_Acquisition_Progress": 45,
        "Scope_Changes": 4,
        "Contractor_Performance": "Poor"
    }

    sample_risk = {
        "overall_risk_score": 78.5,
        "risk_level": "HIGH"
    }

    results = generate_recommendations(
        sample_project,
        sample_risk
    )

    print("=" * 70)
    print("OnTrack AI — Recommendation Engine Test")
    print("=" * 70)

    for item in results:
        print(f"\n[{item['priority']}] {item['issue']}")
        print(f"Recommendation: {item['recommendation']}")

    print("\n" + "=" * 70)
    print("Recommendation test completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()