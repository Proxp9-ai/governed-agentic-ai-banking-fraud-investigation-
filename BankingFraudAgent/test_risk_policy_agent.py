
from agents.transaction_agent import analyze_transaction
from agents.behavior_agent import analyze_behavior
from agents.risk_policy_agent import assess_risk

transaction_result = analyze_transaction(
    amount=75000,
    channel="Internet Banking",
)

behavior_result = analyze_behavior(
    location="New Location",
    device="New Device",
    failed_logins=4,
)

result = assess_risk(
    transaction_result,
    behavior_result,
)

print(result)

assert result["total_risk_points"] == 9
assert result["risk_level"] == "HIGH"
assert result["human_review_required"] is True

print("Risk and Policy Agent test passed!")
