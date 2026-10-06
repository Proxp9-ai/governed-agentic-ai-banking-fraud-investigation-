
from agents.routing_agent import route_investigation

# Test 1: High-risk transaction
high_risk = route_investigation(
    risk_result={"risk_level": "HIGH"},
    location="New Location",
    device="New Device",
)

assert high_risk["route"] == "PRIORITY_INVESTIGATION"
assert high_risk["human_review_required"] is True


# Test 2: Incomplete evidence
unknown_evidence = route_investigation(
    risk_result={"risk_level": "LOW"},
    location="Unknown",
    device="Recognised Device",
)

assert unknown_evidence["route"] == "EVIDENCE_VERIFICATION"
assert unknown_evidence["human_review_required"] is True


# Test 3: Medium-risk transaction
medium_risk = route_investigation(
    risk_result={"risk_level": "MEDIUM"},
    location="Usual Location",
    device="Recognised Device",
)

assert medium_risk["route"] == "STANDARD_INVESTIGATION"
assert medium_risk["human_review_required"] is True


# Test 4: Low-risk transaction
low_risk = route_investigation(
    risk_result={"risk_level": "LOW"},
    location="Usual Location",
    device="Recognised Device",
)

assert low_risk["route"] == "STANDARD_REVIEW"
assert low_risk["human_review_required"] is False


# Test 5: Invalid risk level
invalid_risk = route_investigation(
    risk_result={"risk_level": "INVALID"},
    location="Usual Location",
    device="Recognised Device",
)

assert invalid_risk["route"] == "MANUAL_REVIEW"
assert invalid_risk["human_review_required"] is True


print("Test 1: HIGH risk routing passed.")
print("Test 2: Incomplete evidence routing passed.")
print("Test 3: MEDIUM risk routing passed.")
print("Test 4: LOW risk routing passed.")
print("Test 5: Invalid risk routing passed.")
print("\nAll routing agent tests passed!")
