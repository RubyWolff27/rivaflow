"""Audit logging service for admin actions."""

import json
import logging
from typing import Any

from rivaflow.db.database import convert_query, execute_insert, get_connection

logger = logging.getLogger(__name__)


class AuditService:
    """Service for logging and retrieving admin actions."""

    @staticmethod
    def log(
        actor_id: int,
        action: str,
        target_type: str | None = None,
        target_id: int | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> int:
        """
        Log an admin action to the audit log.

        Args:
            actor_id: ID of the user performing the action
            action: Action being performed (e.g., "user.update", "gym.delete")
            target_type: Type of entity being acted upon (e.g., "user", "gym")
            target_id: ID of the target entity
            details: Additional details about the action (will be stored as JSON)
            ip_address: IP address of the actor

        Returns:
            ID of the created audit log entry

        Raises:
            Exception: If logging fails
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                # Convert details dict to JSON string if provided
                details_json = json.dumps(details) if details else None

                query = """
                    INSERT INTO audit_logs (
                        actor_user_id, action, target_type, target_id,
                        details, ip_address
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """

                log_id = execute_insert(
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

                logger.info(
                    f"Audit log created: actor={actor_id}, action={action}, "
                    f"target={target_type}:{target_id}"
                )

                return log_id

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't raise - we don't want audit logging failures to break operations
            # But log the error for monitoring
            return 0

    @staticmethod
    def get_logs(
        limit: int = 100,
        offset: int = 0,
        actor_id: int | None = None,
        action: str | None = None,
        target_type: str | None = None,
        target_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve audit logs with optional filters.

        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip (for pagination)
            actor_id: Filter by actor user ID
            action: Filter by action type
            target_type: Filter by target type
            target_id: Filter by target ID

        Returns:
            List of audit log entries with actor details
        """
        try:
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
                params = []

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
                            # Keep as string if not valid JSON
                            pass

                    logs.append(log_dict)

                return logs

        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {e}")
            return []

    @staticmethod
    def get_total_count(
        actor_id: int | None = None,
        action: str | None = None,
        target_type: str | None = None,
        target_id: int | None = None,
    ) -> int:
        """
        Get total count of audit logs matching filters.

        Args:
            actor_id: Filter by actor user ID
            action: Filter by action type
            target_type: Filter by target type
            target_id: Filter by target ID

        Returns:
            Total count of matching audit logs
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT COUNT(*) FROM audit_logs WHERE 1=1"
                params = []

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

        except Exception as e:
            logger.error(f"Failed to count audit logs: {e}")
            return 0

    @staticmethod
    def get_user_activity_summary(user_id: int, days: int = 30) -> dict[str, Any]:
        """
        Get a summary of a user's activity from audit logs.

        Args:
            user_id: User ID to get activity for
            days: Number of days to look back

        Returns:
            Dictionary with activity summary
        """
        try:
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

                # Get total actions
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

        except Exception as e:
            logger.error(f"Failed to get user activity summary: {e}")
            return {
                "user_id": user_id,
                "days": days,
                "total_actions": 0,
                "action_counts": {},
                "most_recent_action": None,
            }
