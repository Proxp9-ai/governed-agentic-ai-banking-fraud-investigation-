
from agents.orchestrator import investigate_transaction

result = investigate_transaction(
    amount=75000,
    channel="Internet Banking",
    location="New Location",
    device="New Device",
    failed_logins=4,
)

print(result)

assert result["workflow_status"] == "completed"
assert result["risk_assessment"]["risk_level"] == "HIGH"
assert result["recommendation"]["human_review_required"] is True

print("Orchestrator test passed!")
