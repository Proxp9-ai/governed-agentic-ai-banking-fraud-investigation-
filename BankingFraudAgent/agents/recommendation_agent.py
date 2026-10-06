
def generate_recommendation(risk_result: dict) -> dict:
    """
    Prepare an investigator-facing case summary.
    Recommendations are advisory and require human review.
    """
    risk_level = risk_result.get("risk_level", "UNKNOWN")
    findings = risk_result.get("findings", [])
    human_review_required = risk_result.get(
        "human_review_required", True
    )

    if risk_level == "HIGH":
        priority = "URGENT"
        next_steps = [
            "Review the transaction and supporting evidence.",
            "Verify relevant customer and device context.",
            "Escalate to the authorised fraud investigation team.",
        ]

    elif risk_level == "MEDIUM":
        priority = "NORMAL"
        next_steps = [
            "Review the identified risk indicators.",
            "Check for missing or inconsistent evidence.",
            "Record the investigator's assessment.",
        ]

    elif risk_level == "LOW":
        priority = "ROUTINE"
        next_steps = [
            "Review the available evidence if required by policy.",
            "Record the investigation outcome where applicable.",
        ]

    else:
        priority = "REVIEW REQUIRED"
        next_steps = [
            "Verify the risk assessment and available evidence.",
            "Refer the case to an authorised human investigator.",
        ]
        human_review_required = True

    return {
        "agent": "Recommendation Agent",
        "risk_level": risk_level,
        "priority": priority,
        "case_summary": (
            f"Risk assessment returned {risk_level} risk "
            f"with {len(findings)} recorded findings."
        ),
        "evidence_findings": findings,
        "recommended_next_steps": next_steps,
        "human_review_required": human_review_required,
        "status": "completed",
    }
