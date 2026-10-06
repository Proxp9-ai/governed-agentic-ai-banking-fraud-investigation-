
from database import (
    initialize_database,
    save_investigation,
    get_investigations,
    update_review_status,
)

initialize_database()

risk_result = {
    "total_risk_points": 9,
    "risk_level": "HIGH",
    "findings": [
        "High transaction amount",
        "Transaction from a new device",
    ],
}

recommendation_result = {
    "case_summary": "High-risk case requiring investigation.",
}

case_id = save_investigation(
    transaction_id="TEST-TXN-001",
    amount=75000,
    channel="Internet Banking",
    location="New Location",
    device="New Device",
    failed_logins=4,
    risk_result=risk_result,
    recommendation_result=recommendation_result,
    human_review_required=True,
)

cases = get_investigations()

assert any(case["id"] == case_id for case in cases)

case = next(
    case for case in cases if case["id"] == case_id
)

assert case["risk_level"] == "HIGH"
assert case["human_review_required"] == 1
assert update_review_status(case_id, "Under Investigation")

updated_cases = get_investigations()
updated_case = next(
    case for case in updated_cases if case["id"] == case_id
)

assert updated_case["review_status"] == "Under Investigation"

print("Saved case ID:", case_id)
print("Risk level:", case["risk_level"])
print("Updated review status:", updated_case["review_status"])
print("Database test passed!")
