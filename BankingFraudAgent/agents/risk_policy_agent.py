
def assess_risk(
    transaction_result: dict,
    behavior_result: dict,
) -> dict:
    transaction_points = transaction_result.get("risk_points", 0)
    behavior_points = behavior_result.get("risk_points", 0)

    total_points = transaction_points + behavior_points

    findings = (
        transaction_result.get("findings", [])
        + behavior_result.get("findings", [])
    )

    incomplete_evidence = any(
        "unknown" in finding.lower()
        for finding in findings
    )

    if total_points >= 6:
        risk_level = "HIGH"
        recommendation = "Escalate for human investigation."
        human_review_required = True

    elif total_points >= 3:
        risk_level = "MEDIUM"
        recommendation = "Request investigator review."
        human_review_required = True

    else:
        risk_level = "LOW"
        recommendation = (
            "No elevated risk identified by these illustrative rules."
        )
        human_review_required = False

    if incomplete_evidence:
        human_review_required = True
        recommendation = (
            "Human review required: verify incomplete information "
            "before making a decision."
        )

    return {
        "agent": "Risk and Policy Agent",
        "total_risk_points": total_points,
        "risk_level": risk_level,
        "findings": findings,
        "recommendation": recommendation,
        "human_review_required": human_review_required,
        "status": "completed",
    }
