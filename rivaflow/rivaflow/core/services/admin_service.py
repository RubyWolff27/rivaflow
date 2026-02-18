"""Service layer for admin operations."""

import logging

from rivaflow.db.repositories.activity_comment_repo import (
    ActivityCommentRepository,
)
from rivaflow.db.repositories.glossary_repo import GlossaryRepository
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class AdminService:
    """Business logic for admin operations."""

    @staticmethod
    def get_dashboard_stats() -> dict:
        """Get platform statistics for admin dashboard."""
        from datetime import datetime, timedelta

        user_stats = UserRepository.get_dashboard_stats()

        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        active_users = SessionRepository.get_active_user_count(thirty_days_ago)
        total_sessions = SessionRepository.get_total_count()
        total_comments = SessionRepository.get_total_comment_count()

        return {
            "total_users": user_stats["total_users"],
            "active_users": active_users,
            "new_users_week": user_stats["new_users_week"],
            "total_sessions": total_sessions,
            "total_comments": total_comments,
        }

    @staticmethod
    def list_users(
        search: str | None = None,
        is_active: bool | None = None,
        is_admin: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """List users with optional filters.

        Returns:
            Dict with 'users', 'total', 'limit', 'offset'
        """
        return UserRepository.admin_list_users(
            search=search,
            is_active=is_active,
            is_admin=is_admin,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def get_user_details(user_id: int) -> dict | None:
        """Get detailed user info with stats.

        Returns:
            User dict with stats, or None if not found
        """
        user = UserRepository.get_by_id(user_id)
        if not user:
            return None

        stats = UserRepository.get_user_stats_for_admin(user_id)

        safe_user = {k: v for k, v in user.items() if k != "hashed_password"}
        return {
            **safe_user,
            "stats": stats,
        }

    @staticmethod
    def update_user(user_id: int, changes: dict) -> dict | None:
        """Update admin-editable user fields.

        Args:
            user_id: User's ID
            changes: Dict of field->value (is_active, is_admin,
                     subscription_tier, is_beta_user)

        Returns:
            Updated user dict, or None if not found
        """
        valid_fields = {
            "is_active",
            "is_admin",
            "subscription_tier",
            "is_beta_user",
        }

        updates = []
        params = []
        for field, value in changes.items():
            if field not in valid_fields:
                raise ValueError(f"Invalid field: {field}")
            updates.append(f"{field} = ?")
            params.append(value)

        if not updates:
            return UserRepository.get_by_id(user_id)

        UserRepository.admin_update_user(user_id, updates, params)

        return UserRepository.get_by_id(user_id)

    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Hard-delete a user.

        Returns:
            True if deleted
        """
        return UserRepository.delete_by_id(user_id)

    @staticmethod
    def list_comments(limit: int = 100, offset: int = 0) -> dict:
        """List all comments for moderation.

        Returns:
            Dict with 'comments', 'total', 'limit', 'offset'
        """
        return ActivityCommentRepository.admin_list_comments(limit, offset)

    @staticmethod
    def list_techniques(
        search: str | None = None,
        category: str | None = None,
        custom_only: bool = False,
    ) -> dict:
        """List techniques for admin management.

        Returns:
            Dict with 'techniques' and 'count'
        """
        techniques = GlossaryRepository.admin_list_techniques(
            search=search, category=category, custom_only=custom_only
        )
        return {
            "techniques": techniques,
            "count": len(techniques),
        }

    @staticmethod
    def delete_technique(technique_id: int) -> str | None:
        """Delete a technique by ID.

        Returns:
            The technique name if found and deleted, None if not found
        """
        return GlossaryRepository.admin_delete_technique(technique_id)

    @staticmethod
    def get_broadcast_users() -> list[dict]:
        """Get all active users for email broadcast.

        Returns:
            List of user dicts with id, email, first_name
        """
        return UserRepository.get_broadcast_users()
