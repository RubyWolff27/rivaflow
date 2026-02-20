"""Audit logging service for admin actions."""

import json
import logging
from typing import Any

from rivaflow.db.repositories.audit_log_repo import AuditLogRepository

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
            # Convert details dict to JSON string if provided
            details_json = json.dumps(details) if details else None

            log_id = AuditLogRepository.create(
                actor_id=actor_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details_json=details_json,
                ip_address=ip_address,
            )

            logger.info(
                f"Audit log created: actor={actor_id}, action={action}, "
                f"target={target_type}:{target_id}"
            )

            return log_id

        except (ConnectionError, OSError) as e:
            logger.error("Failed to create audit log: %s", e)
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
            return AuditLogRepository.get_logs(
                limit=limit,
                offset=offset,
                actor_id=actor_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
            )

        except (ConnectionError, OSError) as e:
            logger.error("Failed to retrieve audit logs: %s", e)
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
            return AuditLogRepository.get_total_count(
                actor_id=actor_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
            )

        except (ConnectionError, OSError) as e:
            logger.error("Failed to count audit logs: %s", e)
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
            return AuditLogRepository.get_user_activity_summary(user_id, days)

        except (ConnectionError, OSError) as e:
            logger.error("Failed to get user activity summary: %s", e)
            return {
                "user_id": user_id,
                "days": days,
                "total_actions": 0,
                "action_counts": {},
                "most_recent_action": None,
            }
