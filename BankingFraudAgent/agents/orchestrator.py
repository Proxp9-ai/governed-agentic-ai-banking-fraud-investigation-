
from agents.transaction_agent import analyze_transaction
from agents.behavior_agent import analyze_behavior
from agents.risk_policy_agent import assess_risk
from agents.recommendation_agent import generate_recommendation
from agents.routing_agent import route_investigation


def investigate_transaction(
    amount: float,
    channel: str,
    location: str,
    device: str,
    failed_logins: int,
) -> dict:
    """Run the investigation agents and select a routing path."""

    # Step 1: Analyze transaction details.
    transaction_result = analyze_transaction(
        amount=amount,
        channel=channel,
    )

    # Step 2: Analyze behavioural indicators.
    behavior_result = analyze_behavior(
        location=location,
        device=device,
        failed_logins=failed_logins,
    )

    # Step 3: Assess the combined risk.
    risk_result = assess_risk(
        transaction_result,
        behavior_result,
    )

    # Step 4: Generate investigation recommendations.
    recommendation_result = generate_recommendation(
        risk_result
    )

    # Step 5: Select the investigation route.
    routing_result = route_investigation(
        risk_result=risk_result,
        location=location,
        device=device,
    )

    # Enforce human review when routing or recommendation
    # identifies a need for it.
    human_review_required = (
        routing_result["human_review_required"]
        or recommendation_result["human_review_required"]
    )

    return {
        "transaction_analysis": transaction_result,
        "behavior_analysis": behavior_result,
        "risk_assessment": risk_result,
        "recommendation": recommendation_result,
        "routing": routing_result,
        "human_review_required": human_review_required,
        "workflow_status": "completed",
    }
