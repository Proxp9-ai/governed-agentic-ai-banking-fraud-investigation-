
from agents.transaction_agent import analyze_transaction
from agents.behavior_agent import analyze_behavior
from agents.risk_policy_agent import assess_risk

transaction = analyze_transaction(
    amount=5000,
    channel="UPI",
)

behavior = analyze_behavior(
    location="Unknown",
    device="Unknown",
    failed_logins=0,
)

result = assess_risk(transaction, behavior)

print("Risk level:", result["risk_level"])
print("Human review required:", result["human_review_required"])
print("Recommendation:", result["recommendation"])

assert result["risk_level"] == "LOW"
assert result["human_review_required"] is True
assert "unknown" in result["recommendation"].lower() or (
    "incomplete" in result["recommendation"].lower()
)

print("Unknown evidence safety test passed!")
