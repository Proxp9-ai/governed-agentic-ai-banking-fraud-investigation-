import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

DB_DIR = Path(__file__).resolve().parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "investigations.db"

REVIEW_STATUSES = {
    "Pending Review", "Under Investigation", "Escalated", "Closed After Review"
}
APPROVAL_STATUSES = {"Pending Approval", "Approved", "Rejected", "Not Required"}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS investigations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                amount REAL NOT NULL,
                channel TEXT NOT NULL,
                location TEXT NOT NULL,
                device TEXT NOT NULL,
                failed_logins INTEGER NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                findings_json TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                human_review_required INTEGER NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'Pending Review',
                route TEXT NOT NULL DEFAULT 'UNKNOWN',
                route_priority TEXT NOT NULL DEFAULT 'UNKNOWN',
                route_reason TEXT NOT NULL DEFAULT '',
                review_notes TEXT NOT NULL DEFAULT '',
                approval_status TEXT NOT NULL DEFAULT 'Pending Approval',
                approved_by TEXT NOT NULL DEFAULT '',
                approved_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        existing = {row["name"] for row in connection.execute("PRAGMA table_info(investigations)")}
        migrations = {
            "route": "TEXT NOT NULL DEFAULT 'UNKNOWN'",
            "route_priority": "TEXT NOT NULL DEFAULT 'UNKNOWN'",
            "route_reason": "TEXT NOT NULL DEFAULT ''",
            "review_notes": "TEXT NOT NULL DEFAULT ''",
            "approval_status": "TEXT NOT NULL DEFAULT 'Pending Approval'",
            "approved_by": "TEXT NOT NULL DEFAULT ''",
            "approved_at": "TEXT NOT NULL DEFAULT ''",
        }
        for column, definition in migrations.items():
            if column not in existing:
                connection.execute(f"ALTER TABLE investigations ADD COLUMN {column} {definition}")


def initialize_audit_table():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS investigation_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investigation_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                actor TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (investigation_id) REFERENCES investigations(id)
            )
        """)


def save_investigation(
    transaction_id, amount, channel, location, device, failed_logins,
    risk_result, recommendation_result, human_review_required, routing_result=None,
):
    now = utc_now()
    findings_json = json.dumps(risk_result.get("findings", []), ensure_ascii=False)
    routing_result = routing_result or {}
    initial_approval = "Pending Approval" if human_review_required else "Not Required"
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO investigations (
                transaction_id, amount, channel, location, device, failed_logins,
                risk_score, risk_level, findings_json, recommendation,
                human_review_required, review_status, route, route_priority,
                route_reason, review_notes, approval_status, approved_by,
                approved_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_id, amount, channel, location, device, failed_logins,
            risk_result.get("total_risk_points", 0),
            risk_result.get("risk_level", "UNKNOWN"), findings_json,
            risk_result.get("recommendation", recommendation_result.get("case_summary", "")),
            int(human_review_required), "Pending Review",
            routing_result.get("route", "UNKNOWN"),
            routing_result.get("priority", "UNKNOWN"), routing_result.get("reason", ""),
            "", initial_approval, "", "", now, now,
        ))
        return cursor.lastrowid


def get_investigations(limit=100):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM investigations ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def case_requires_human_review(case):
    raw_flag = case.get("human_review_required", False)
    if isinstance(raw_flag, str):
        review_flag = raw_flag.strip().lower() in {"1", "true", "yes", "required"}
    else:
        review_flag = bool(raw_flag)
    risk_level = str(case.get("risk_level", "") or "").strip().upper()
    location = str(case.get("location", "") or "").strip().lower()
    device = str(case.get("device", "") or "").strip().lower()
    return review_flag or risk_level in {"HIGH", "MEDIUM"} or location == "unknown" or device == "unknown"


def record_audit_event(
    investigation_id, action, old_value="", new_value="", actor="Demo Investigator"
):
    timestamp = utc_now()
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO investigation_audit_log (
                investigation_id, action, old_value, new_value, actor, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (investigation_id, action, old_value, new_value, actor, timestamp))
        return cursor.lastrowid


def save_review_workflow(investigation_id, review_status, review_notes, actor, approval_status):
    """Save review notes, status, approval metadata, and audit events atomically."""
    if review_status not in REVIEW_STATUSES:
        raise ValueError("Invalid review status.")
    if approval_status not in APPROVAL_STATUSES:
        raise ValueError("Invalid approval status.")
    actor = str(actor or "").strip()
    review_notes = str(review_notes or "").strip()
    if not actor:
        raise ValueError("Enter an investigator name.")
    if not review_notes:
        raise ValueError("Document review notes before saving the review.")

    now = utc_now()
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM investigations WHERE id = ?", (investigation_id,)).fetchone()
        if row is None:
            return False
        case = dict(row)
        requires_review = case_requires_human_review(case)
        old_status = case.get("review_status", "Pending Review")
        old_notes = case.get("review_notes", "") or ""
        old_approval = case.get("approval_status", "Pending Approval") or "Pending Approval"

        if approval_status == "Approved" and review_status == "Pending Review":
            raise ValueError("Move the case to Under Investigation or Escalated before approval.")
        if review_status == "Closed After Review":
            if requires_review and approval_status != "Approved":
                raise ValueError("Closure blocked: this case requires human review and explicit approval.")
            if not requires_review and approval_status not in {"Approved", "Not Required"}:
                raise ValueError("Closure requires approval or a Not Required approval decision.")

        approved_by = actor if approval_status == "Approved" else ""
        approved_at = now if approval_status == "Approved" else ""
        connection.execute("""
            UPDATE investigations
            SET review_status = ?, review_notes = ?, approval_status = ?,
                approved_by = ?, approved_at = ?, updated_at = ?
            WHERE id = ?
        """, (review_status, review_notes, approval_status, approved_by, approved_at, now, investigation_id))

        def audit(action, old_value, new_value):
            connection.execute("""
                INSERT INTO investigation_audit_log
                (investigation_id, action, old_value, new_value, actor, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (investigation_id, action, old_value, new_value, actor, now))

        if old_notes != review_notes:
            audit("Review notes updated", old_notes or "(empty)", review_notes)
        if old_approval != approval_status:
            new_approval_value = approval_status
            if approval_status == "Approved":
                new_approval_value = f"Approved by {actor} at {now}"
            old_approval_value = old_approval
            if old_approval == "Approved":
                old_approval_value = f"Approved by {case.get('approved_by', '')} at {case.get('approved_at', '')}"
            audit("Approval decision changed", old_approval_value, new_approval_value)
        if old_status != review_status:
            action = "Case closed" if review_status == "Closed After Review" else "Review status changed"
            audit(action, old_status, review_status)
        return True


def update_review_status(investigation_id, review_status):
    """Compatibility wrapper; closure is blocked unless saved review requirements are met."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT review_notes, approval_status FROM investigations WHERE id = ?", (investigation_id,)
        ).fetchone()
    if row is None:
        return False
    return save_review_workflow(
        investigation_id, review_status, row["review_notes"] or "", "Demo Investigator",
        row["approval_status"] or "Pending Approval",
    )


def get_audit_events(investigation_id):
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT * FROM investigation_audit_log
            WHERE investigation_id = ? ORDER BY id DESC
        """, (investigation_id,)).fetchall()
        return [dict(row) for row in rows]
