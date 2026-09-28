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

    # ---------------------------------------------------------
    # Helper function
    # ---------------------------------------------------------
    def add_recommendation(priority, issue, recommendation):
        recommendations.append({
            "priority": priority,
            "issue": issue,
            "recommendation": recommendation
        })

    # ---------------------------------------------------------
    # 1. Procurement delay
    # ---------------------------------------------------------
    procurement_delay = float(
        project_record.get("Procurement_Delay_Days", 0) or 0
    )

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
    # 3. Average milestone delay
    # ---------------------------------------------------------
    avg_milestone_delay = float(
        project_record.get("Average_Milestone_Delay_Days", 0) or 0
    )

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
    # 4. Physical progress vs planned progress
    # ---------------------------------------------------------
    physical_progress = float(
        project_record.get("Physical_Progress", 0) or 0
    )
    planned_progress = float(
        project_record.get("Planned_Progress", 0) or 0
    )

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
    # 5. Pending approvals
    # ---------------------------------------------------------
    approvals_pending = float(
        project_record.get("Approvals_Pending", 0) or 0
    )

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
    # 6. Land acquisition
    # ---------------------------------------------------------
    land_progress = float(
        project_record.get("Land_Acquisition_Progress", 100) or 0
    )

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
    # 7. Scope changes
    # ---------------------------------------------------------
    scope_changes = float(
        project_record.get("Scope_Changes", 0) or 0
    )

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
    # 8. Contractor performance
    # ---------------------------------------------------------
    contractor = str(
        project_record.get("Contractor_Performance", "")
    ).strip().lower()

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