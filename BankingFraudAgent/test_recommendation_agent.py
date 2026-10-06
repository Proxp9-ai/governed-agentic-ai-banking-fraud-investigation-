
from agents.transaction_agent import analyze_transaction
from agents.behavior_agent import analyze_behavior
from agents.risk_policy_agent import assess_risk
from agents.recommendation_agent import generate_recommendation

transaction_result = analyze_transaction(
    amount=75000,
    channel="Internet Banking",
)

behavior_result = analyze_behavior(
    location="New Location",
    device="New Device",
    failed_logins=4,
)

risk_result = assess_risk(
    transaction_result,
    behavior_result,
)

recommendation = generate_recommendation(risk_result)

print(recommendation)

assert recommendation["risk_level"] == "HIGH"
assert recommendation["priority"] == "URGENT"
assert recommendation["human_review_required"] is True
assert len(recommendation["recommended_next_steps"]) == 3

print("Recommendation Agent test passed!")
