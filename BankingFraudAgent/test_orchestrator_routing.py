
from agents.orchestrator import investigate_transaction


# Test a high-risk transaction.
result = investigate_transaction(
    amount=75000,
    channel="Internet Banking",
    location="New Location",
    device="New Device",
    failed_logins=4,
)

assert result["risk_assessment"]["risk_level"] == "HIGH"
assert result["routing"]["route"] == "PRIORITY_INVESTIGATION"
assert result["human_review_required"] is True

print("Risk level:", result["risk_assessment"]["risk_level"])
print("Route:", result["routing"]["route"])
print("Human review required:", result["human_review_required"])
print("Orchestrator routing test passed!")


# Test incomplete evidence.
unknown_result = investigate_transaction(
    amount=5000,
    channel="UPI",
    location="Unknown",
    device="Recognised Device",
    failed_logins=0,
)

assert unknown_result["routing"]["route"] == "EVIDENCE_VERIFICATION"
assert unknown_result["human_review_required"] is True

print("Unknown evidence routing test passed!")
