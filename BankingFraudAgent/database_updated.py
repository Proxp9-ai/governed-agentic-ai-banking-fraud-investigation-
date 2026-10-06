import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

DB_DIR = Path(__file__).resolve().parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "investigations.db"


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
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        existing = {
            row["name"] for row in
            connection.execute("PRAGMA table_info(investigations)")
        }
        for column, definition in {
            "route": "TEXT NOT NULL DEFAULT 'UNKNOWN'",
            "route_priority": "TEXT NOT NULL DEFAULT 'UNKNOWN'",
            "route_reason": "TEXT NOT NULL DEFAULT ''",
        }.items():
            if column not in existing:
                connection.execute(
                    f"ALTER TABLE investigations ADD COLUMN {column} {definition}"
                )


def save_investigation(
    transaction_id, amount, channel, location, device, failed_logins,
    risk_result, recommendation_result, human_review_required,
    routing_result=None,
):
    now = datetime.now(timezone.utc).isoformat()
    findings_json = json.dumps(risk_result.get("findings", []), ensure_ascii=False)
    routing_result = routing_result or {}
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO investigations (
                transaction_id, amount, channel, location, device,
                failed_logins, risk_score, risk_level, findings_json,
                recommendation, human_review_required, review_status,
                route, route_priority, route_reason, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_id, amount, channel, location, device, failed_logins,
            risk_result.get("total_risk_points", 0),
            risk_result.get("risk_level", "UNKNOWN"),
            findings_json,
            risk_result.get("recommendation", recommendation_result.get("case_summary", "")),
            int(human_review_required), "Pending Review",
            routing_result.get("route", "UNKNOWN"),
            routing_result.get("priority", "UNKNOWN"),
            routing_result.get("reason", ""),
            now, now,
        ))
        return cursor.lastrowid


def get_investigations(limit=100):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM investigations ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def update_review_status(investigation_id, review_status):
    allowed_statuses = {
        "Pending Review", "Under Investigation", "Escalated", "Closed After Review"
    }
    if review_status not in allowed_statuses:
        raise ValueError("Invalid review status.")
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE investigations SET review_status = ?, updated_at = ?
            WHERE id = ?
        """, (review_status, now, investigation_id))
        return cursor.rowcount == 1


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


def record_audit_event(
    investigation_id, action, old_value="", new_value="", actor="Demo Investigator"
):
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO investigation_audit_log (
                investigation_id, action, old_value, new_value, actor, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (investigation_id, action, old_value, new_value, actor, timestamp))
        return cursor.lastrowid


def get_audit_events(investigation_id):
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT * FROM investigation_audit_log
            WHERE investigation_id = ? ORDER BY id DESC
        """, (investigation_id,)).fetchall()
        return [dict(row) for row in rows]
