
from database import (
    initialize_database,
    initialize_audit_table,
    save_investigation,
    record_audit_event,
    get_audit_events,
)

initialize_database()
initialize_audit_table()

risk_result = {
    "total_risk_points": 9,
    "risk_level": "HIGH",
    "findings": ["High transaction amount"],
}

recommendation_result = {
    "case_summary": "High-risk test investigation",
}

case_id = save_investigation(
    transaction_id="AUDIT-TEST-001",
    amount=75000,
    channel="Internet Banking",
    location="New Location",
    device="New Device",
    failed_logins=4,
    risk_result=risk_result,
    recommendation_result=recommendation_result,
    human_review_required=True,
)

record_audit_event(
    investigation_id=case_id,
    action="Review status changed",
    old_value="Pending Review",
    new_value="Under Investigation",
    actor="Test Investigator",
)

events = get_audit_events(case_id)

assert len(events) == 1
assert events[0]["action"] == "Review status changed"
assert events[0]["old_value"] == "Pending Review"
assert events[0]["new_value"] == "Under Investigation"
assert events[0]["actor"] == "Test Investigator"

print("Audit event:", events[0]["action"])
print("Old status:", events[0]["old_value"])
print("New status:", events[0]["new_value"])
print("Audit trail test passed!")
