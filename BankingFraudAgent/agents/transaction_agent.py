
def analyze_transaction(amount: float, channel: str) -> dict:
    """
    Analyze transaction attributes using illustrative rules.
    This is not a trained or validated fraud detection model.
    """
    findings = []
    risk_points = 0

    if amount >= 50000:
        risk_points += 2
        findings.append("High transaction amount")

    if channel not in [
        "UPI",
        "Mobile Banking",
        "Internet Banking",
        "ATM",
        "Card",
    ]:
        findings.append("Unrecognised transaction channel")

    return {
        "agent": "Transaction Analysis Agent",
        "amount": amount,
        "channel": channel,
        "risk_points": risk_points,
        "findings": findings,
        "status": "completed",
    }
