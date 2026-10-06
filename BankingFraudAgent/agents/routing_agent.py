
def route_investigation(risk_result: dict, location: str, device: str) -> dict:
    """Choose an investigation path using illustrative routing rules."""

    risk_level = risk_result.get("risk_level", "UNKNOWN")

    incomplete_evidence = (
        location == "Unknown"
        or device == "Unknown"
    )

    if incomplete_evidence:
        route = "EVIDENCE_VERIFICATION"
        priority = "HIGH"
        human_review_required = True
        reason = "Location or device evidence is incomplete."

    elif risk_level == "HIGH":
        route = "PRIORITY_INVESTIGATION"
        priority = "URGENT"
        human_review_required = True
        reason = "The risk assessment returned HIGH risk."

    elif risk_level == "MEDIUM":
        route = "STANDARD_INVESTIGATION"
        priority = "NORMAL"
        human_review_required = True
        reason = "The risk assessment returned MEDIUM risk."

    elif risk_level == "LOW":
        route = "STANDARD_REVIEW"
        priority = "ROUTINE"
        human_review_required = False
        reason = "No elevated risk was identified by the illustrative rules."

    else:
        route = "MANUAL_REVIEW"
        priority = "URGENT"
        human_review_required = True
        reason = "Risk level is unknown or invalid."

    return {
        "agent": "Investigation Routing Agent",
        "route": route,
        "priority": priority,
        "reason": reason,
        "human_review_required": human_review_required,
        "status": "completed",
    }
