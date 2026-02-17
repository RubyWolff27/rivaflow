"""Service layer for admin operations."""

import logging
from datetime import datetime, timedelta

from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class AdminService:
    """Business logic for admin operations."""

    @staticmethod
    def get_dashboard_stats() -> dict:
        """Get platform statistics for admin dashboard."""
        with get_connection() as conn:
            cursor = conn.cursor()

            def get_count(result):
                if not result:
                    return 0
                if isinstance(result, dict):
                    return list(result.values())[0] or 0
                try:
                    return result[0]
                except (KeyError, IndexError, TypeError):
                    return 0

            cursor.execute(convert_query("SELECT COUNT(*) FROM users"))
            total_users = get_count(cursor.fetchone())

            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            cursor.execute(
                convert_query(
                    "SELECT COUNT(DISTINCT user_id) FROM sessions"
                    " WHERE session_date >= ?"
                ),
                (thirty_days_ago,),
            )
            active_users = get_count(cursor.fetchone())

            cursor.execute(convert_query("SELECT COUNT(*) FROM sessions"))
            total_sessions = get_count(cursor.fetchone())

            cursor.execute(convert_query("SELECT COUNT(*) FROM activity_comments"))
            total_comments = get_count(cursor.fetchone())

            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            cursor.execute(
                convert_query("SELECT COUNT(*) FROM users" " WHERE created_at >= ?"),
                (week_ago,),
            )
            new_users_week = get_count(cursor.fetchone())

        return {
            "total_users": total_users,
            "active_users": active_users,
            "new_users_week": new_users_week,
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
        with get_connection() as conn:
            cursor = conn.cursor()

            query = (
                "SELECT id, email, first_name, last_name,"
                " is_active, is_admin, subscription_tier,"
                " is_beta_user, created_at"
                " FROM users WHERE 1=1"
            )
            params: list = []

            if search:
                query += (
                    " AND (email LIKE ? OR first_name LIKE ?" " OR last_name LIKE ?)"
                )
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])

            if is_active is not None:
                query += " AND is_active = ?"
                params.append(is_active)

            if is_admin is not None:
                query += " AND is_admin = ?"
                params.append(is_admin)

            # Count query (before LIMIT/OFFSET)
            count_query = query.replace(
                "SELECT id, email, first_name, last_name,"
                " is_active, is_admin, subscription_tier,"
                " is_beta_user, created_at"
                " FROM users",
                "SELECT COUNT(*) FROM users",
            )
            cursor.execute(convert_query(count_query), params)
            row = cursor.fetchone()
            total_count = (
                list(row.values())[0]
                if isinstance(row, dict)
                else (row[0] if row else 0)
            )

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            cursor.execute(convert_query(query), params)
            users = [dict(row) for row in cursor.fetchall()]

        return {
            "users": users,
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }

    @staticmethod
    def get_user_details(user_id: int) -> dict | None:
        """Get detailed user info with stats.

        Returns:
            User dict with stats, or None if not found
        """
        user = UserRepository.get_by_id(user_id)
        if not user:
            return None

        with get_connection() as conn:
            cursor = conn.cursor()

            def extract_count(result):
                if not result:
                    return 0
                return (
                    list(result.values())[0] if isinstance(result, dict) else result[0]
                )

            cursor.execute(
                convert_query("SELECT COUNT(*) FROM sessions" " WHERE user_id = ?"),
                (user_id,),
            )
            session_count = extract_count(cursor.fetchone())

            cursor.execute(
                convert_query(
                    "SELECT COUNT(*) FROM activity_comments" " WHERE user_id = ?"
                ),
                (user_id,),
            )
            comment_count = extract_count(cursor.fetchone())

            cursor.execute(
                convert_query(
                    "SELECT COUNT(*) FROM user_relationships"
                    " WHERE following_user_id = ?"
                ),
                (user_id,),
            )
            followers_count = extract_count(cursor.fetchone())

            cursor.execute(
                convert_query(
                    "SELECT COUNT(*) FROM user_relationships"
                    " WHERE follower_user_id = ?"
                ),
                (user_id,),
            )
            following_count = extract_count(cursor.fetchone())

        safe_user = {k: v for k, v in user.items() if k != "hashed_password"}
        return {
            **safe_user,
            "stats": {
                "sessions": session_count,
                "comments": comment_count,
                "followers": followers_count,
                "following": following_count,
            },
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

        with get_connection() as conn:
            cursor = conn.cursor()
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            params.append(user_id)
            cursor.execute(convert_query(query), params)
            conn.commit()

        return UserRepository.get_by_id(user_id)

    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Hard-delete a user.

        Returns:
            True if deleted
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM users WHERE id = ?"),
                (user_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def list_comments(limit: int = 100, offset: int = 0) -> dict:
        """List all comments for moderation.

        Returns:
            Dict with 'comments', 'total', 'limit', 'offset'
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                convert_query(
                    "SELECT"
                    " c.id, c.user_id, c.activity_type,"
                    " c.activity_id, c.comment_text, c.created_at,"
                    " u.email, u.first_name, u.last_name"
                    " FROM activity_comments c"
                    " LEFT JOIN users u ON c.user_id = u.id"
                    " ORDER BY c.created_at DESC"
                    " LIMIT ? OFFSET ?"
                ),
                (limit, offset),
            )
            comments = [dict(row) for row in cursor.fetchall()]

            cursor.execute(convert_query("SELECT COUNT(*) FROM activity_comments"))
            row = cursor.fetchone()
            total = (
                list(row.values())[0]
                if isinstance(row, dict)
                else (row[0] if row else 0)
            )

        return {
            "comments": comments,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

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
        with get_connection() as conn:
            cursor = conn.cursor()

            query = (
                "SELECT id, name, category, subcategory, custom,"
                " user_id, gi_applicable, nogi_applicable"
                " FROM movements_glossary WHERE 1=1"
            )
            params: list = []

            if search:
                query += " AND name LIKE ?"
                params.append(f"%{search}%")

            if category:
                query += " AND category = ?"
                params.append(category)

            if custom_only:
                query += " AND custom = 1"

            query += " ORDER BY name"

            cursor.execute(convert_query(query), params)
            techniques = [dict(row) for row in cursor.fetchall()]

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
        technique_name = None
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT name FROM movements_glossary WHERE id = ?"),
                (technique_id,),
            )
            row = cursor.fetchone()
            if row:
                technique_name = row["name"] if hasattr(row, "__getitem__") else row[0]

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM movements_glossary WHERE id = ?"),
                (technique_id,),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None

        return technique_name

    @staticmethod
    def get_broadcast_users() -> list[dict]:
        """Get all active users for email broadcast.

        Returns:
            List of user dicts with id, email, first_name
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT id, email, first_name FROM users" " WHERE is_active = ?"
                ),
                (True,),
            )
            return [dict(r) for r in cursor.fetchall()]
