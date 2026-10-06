
from agents.transaction_agent import analyze_transaction

result = analyze_transaction(
    amount=75000,
    channel="Internet Banking",
)

print(result)

assert result["risk_points"] == 2
assert "High transaction amount" in result["findings"]

print("Transaction agent test passed!")
