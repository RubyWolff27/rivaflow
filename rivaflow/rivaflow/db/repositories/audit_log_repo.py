"""Repository for audit log data access."""

import json
import logging
from typing import Any

from rivaflow.db.database import convert_query, execute_insert, get_connection

logger = logging.getLogger(__name__)


class AuditLogRepository:
    """Data access layer for audit logs."""

    @staticmethod
    def create(
        actor_id: int,
        action: str,
        target_type: str | None = None,
        target_id: int | None = None,
        details_json: str | None = None,
        ip_address: str | None = None,
    ) -> int:
        """Insert an audit log entry. Returns the log ID."""
        with get_connection() as conn:
            cursor = conn.cursor()

            query = """
                INSERT INTO audit_logs (
                    actor_user_id, action, target_type, target_id,
                    details, ip_address
                ) VALUES (?, ?, ?, ?, ?, ?)
            """

            return execute_insert(
                cursor,
                query,
                (
                    actor_id,
                    action,
                    target_type,
                    target_id,
                    details_json,
                    ip_address,
                ),
            )

    @staticmethod
    def get_logs(
        limit: int = 100,
        offset: int = 0,
        actor_id: int | None = None,
        action: str | None = None,
        target_type: str | None = None,
        target_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve audit logs with optional filters and actor details."""
        with get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    al.id,
                    al.actor_user_id,
                    al.action,
                    al.target_type,
                    al.target_id,
                    al.details,
                    al.ip_address,
                    al.created_at,
                    u.email as actor_email,
                    u.first_name as actor_first_name,
                    u.last_name as actor_last_name
                FROM audit_logs al
                LEFT JOIN users u ON al.actor_user_id = u.id
                WHERE 1=1
            """
            params: list = []

            if actor_id is not None:
                query += " AND al.actor_user_id = ?"
                params.append(actor_id)

            if action is not None:
                query += " AND al.action = ?"
                params.append(action)

            if target_type is not None:
                query += " AND al.target_type = ?"
                params.append(target_type)

            if target_id is not None:
                query += " AND al.target_id = ?"
                params.append(target_id)

            query += " ORDER BY al.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(convert_query(query), params)
            rows = cursor.fetchall()

            logs = []
            for row in rows:
                log_dict = dict(row)

                # Parse JSON details if present
                if log_dict.get("details"):
                    try:
                        log_dict["details"] = json.loads(log_dict["details"])
                    except json.JSONDecodeError:
                        pass

                logs.append(log_dict)

            return logs

    @staticmethod
    def get_total_count(
        actor_id: int | None = None,
        action: str | None = None,
        target_type: str | None = None,
        target_id: int | None = None,
    ) -> int:
        """Get total count of audit logs matching filters."""
        with get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT COUNT(*) FROM audit_logs WHERE 1=1"
            params: list = []

            if actor_id is not None:
                query += " AND actor_user_id = ?"
                params.append(actor_id)

            if action is not None:
                query += " AND action = ?"
                params.append(action)

            if target_type is not None:
                query += " AND target_type = ?"
                params.append(target_type)

            if target_id is not None:
                query += " AND target_id = ?"
                params.append(target_id)

            cursor.execute(convert_query(query), params)
            row = cursor.fetchone()
            return row[0] if row else 0

    @staticmethod
    def get_user_activity_summary(user_id: int, days: int = 30) -> dict[str, Any]:
        """Get action counts and most recent action for a user."""
        with get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    action,
                    COUNT(*) as count
                FROM audit_logs
                WHERE actor_user_id = ?
                    AND created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY action
                ORDER BY count DESC
            """

            cursor.execute(convert_query(query), (user_id, days))
            rows = cursor.fetchall()

            action_counts = {row["action"]: row["count"] for row in rows}
            total_actions = sum(action_counts.values())

            # Get most recent action
            cursor.execute(
                convert_query("""
                    SELECT action, created_at
                    FROM audit_logs
                    WHERE actor_user_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                (user_id,),
            )
            recent_row = cursor.fetchone()
            most_recent_action = dict(recent_row) if recent_row else None

            return {
                "user_id": user_id,
                "days": days,
                "total_actions": total_actions,
                "action_counts": action_counts,
                "most_recent_action": most_recent_action,
            }
