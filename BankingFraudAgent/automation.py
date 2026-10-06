"""Optional, privacy-conscious webhook integration for n8n.

Configure N8N_WEBHOOK_URL in the environment to enable dispatch. By default,
no external network request is made. Do not send card numbers, account numbers,
credentials, or full customer records through this demo integration.
"""

import json
import os
import urllib.error
import urllib.request


def dispatch_case_event(case_event, timeout=5):
    """Send a minimal case event to n8n, or return disabled when unconfigured."""
    webhook_url = os.getenv("N8N_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return {"status": "disabled", "message": "N8N_WEBHOOK_URL is not configured."}

    if not webhook_url.startswith(("https://", "http://localhost", "http://127.0.0.1")):
        return {
            "status": "failed",
            "message": "Webhook URL must use HTTPS, except for localhost development.",
        }

    allowed_fields = {
        "case_id", "transaction_id", "risk_level", "risk_score", "route",
        "priority", "human_review_required", "location", "device",
        "review_status", "event_type",
    }
    payload = {key: value for key, value in dict(case_event).items() if key in allowed_fields}
    payload["source"] = "banking-fraud-investigation-prototype"

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    secret = os.getenv("N8N_WEBHOOK_SECRET", "").strip()
    if secret:
        headers["X-Webhook-Secret"] = secret

    request = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            if 200 <= status_code < 300:
                return {"status": "sent", "message": f"HTTP {status_code}"}
            return {"status": "failed", "message": f"Unexpected HTTP status {status_code}"}
    except urllib.error.HTTPError as error:
        return {"status": "failed", "message": f"HTTP {error.code}"}
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        # Avoid storing response bodies or potentially sensitive endpoint details.
        return {"status": "failed", "message": f"Connection error: {type(error).__name__}"}
