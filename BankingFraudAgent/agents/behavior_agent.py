
def analyze_behavior(
    location: str,
    device: str,
    failed_logins: int,
) -> dict:
    """
    Examine behavioural indicators using illustrative rules.
    This is not a validated fraud detection model.
    """
    findings = []
    risk_points = 0

    if location == "New Location":
        risk_points += 2
        findings.append("Transaction from a new location")

    if device == "New Device":
        risk_points += 2
        findings.append("Transaction from a new device")

    if failed_logins >= 3:
        risk_points += 3
        findings.append("Three or more recent failed logins")

    if location == "Unknown":
        findings.append("Transaction location is unknown")

    if device == "Unknown":
        findings.append("Device identity is unknown")

    return {
        "agent": "Behaviour Analysis Agent",
        "risk_points": risk_points,
        "findings": findings,
        "status": "completed",
    }
