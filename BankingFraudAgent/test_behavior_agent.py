
from agents.behavior_agent import analyze_behavior

result = analyze_behavior(
    location="New Location",
    device="New Device",
    failed_logins=4,
)

print(result)

assert result["risk_points"] == 7
assert len(result["findings"]) == 3
assert result["status"] == "completed"

print("Behaviour agent test passed!")
