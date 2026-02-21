"""Repository for user data access."""

from datetime import datetime

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository

# Columns returned by default (excludes hashed_password for security)
_USER_COLS = (
    "id, email, first_name, last_name, is_active, created_at, updated_at, "
    "primary_gym_id, is_admin, last_seen_feed, avatar_url, "
    "subscription_tier, is_beta_user, "
    "username, display_name, profile_photo_url, "
    "location_city, location_state, location_country, "
    "belt_rank, belt_stripes, searchable, "
    "profile_visibility, activity_visibility, bio, preferred_style, "
    "tier_expires_at, beta_joined_at"
)

# All columns including auth-sensitive fields (for auth queries only)
_USER_COLS_WITH_PASSWORD = (
    "hashed_password, failed_login_attempts, locked_until, " + _USER_COLS
)


class UserRepository(BaseRepository):
    """Data access layer for user accounts."""

    @staticmethod
    def create(
        email: str,
        hashed_password: str,
        first_name: str | None = None,
        last_name: str | None = None,
        is_active: bool = True,
        subscription_tier: str = "free",  # Default to free tier
        is_beta_user: bool = False,  # Beta period ended, new users start as free
    ) -> dict:
        """
        Create a new user.

        Args:
            email: User's email address (must be unique)
            hashed_password: Pre-hashed password
            first_name: User's first name
            last_name: User's last name
            is_active: Whether the user account is active
            subscription_tier: Subscription tier (default: free)
            is_beta_user: Whether user has beta access (default: False)

        Returns:
            Dictionary representation of the created user

        Raises:
            sqlite3.IntegrityError: If email already exists
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            user_id = execute_insert(
                cursor,
                """
                INSERT INTO users (email, hashed_password, first_name, last_name, is_active, subscription_tier, is_beta_user)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    email,
                    hashed_password,
                    first_name,
                    last_name,
                    is_active,
                    subscription_tier,
                    is_beta_user,
                ),
            )

            if not user_id or user_id == 0:
                raise ValueError(f"Invalid user_id returned: {user_id}")

            # Fetch and return the created user
            cursor.execute(
                convert_query(f"SELECT {_USER_COLS} FROM users WHERE id = ?"),
                (user_id,),
            )
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"User {user_id} was inserted but cannot be retrieved")

            return UserRepository._row_to_dict(row)

    @staticmethod
    def get_by_email(email: str, include_password: bool = False) -> dict | None:
        """
        Get a user by email address.

        Args:
            email: User's email address
            include_password: If True, include hashed_password in result (for auth only)

        Returns:
            User dictionary or None if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cols = _USER_COLS_WITH_PASSWORD if include_password else _USER_COLS
            cursor.execute(
                convert_query(f"SELECT {cols} FROM users WHERE email = ?"),
                (email,),
            )
            row = cursor.fetchone()
            if row:
                return UserRepository._row_to_dict(
                    row, include_password=include_password
                )
            return None

    @staticmethod
    def get_by_id(user_id: int) -> dict | None:
        """
        Get a user by ID.

        Args:
            user_id: User's ID

        Returns:
            User dictionary or None if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(f"SELECT {_USER_COLS} FROM users WHERE id = ?"),
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return UserRepository._row_to_dict(row)
            return None

    @staticmethod
    def update(
        user_id: int,
        email: str | None = None,
        hashed_password: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        is_active: bool | None = None,
    ) -> dict | None:
        """
        Update a user's information.

        Args:
            user_id: User's ID
            email: New email address
            hashed_password: New hashed password
            first_name: New first name
            last_name: New last name
            is_active: New active status

        Returns:
            Updated user dictionary or None if user not found
        """
        # Valid fields that can be updated (whitelist for SQL safety)
        valid_update_fields = {
            "email",
            "hashed_password",
            "first_name",
            "last_name",
            "is_active",
        }

        with get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query from hardcoded fields only
            updates = []
            params = []

            field_values = {
                "email": email,
                "hashed_password": hashed_password,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": is_active,
            }

            for field, value in field_values.items():
                if field not in valid_update_fields:
                    raise ValueError(f"Invalid field: {field}")
                if value is not None:
                    updates.append(f"{field} = ?")
                    params.append(value)

            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(convert_query(query), params)

            # Return updated user
            cursor.execute(
                convert_query(f"SELECT {_USER_COLS} FROM users WHERE id = ?"),
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return UserRepository._row_to_dict(row)
            return None

    @staticmethod
    def list_all() -> list[dict]:
        """
        Get all active users.

        Returns:
            List of all active users (without hashed passwords)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT id, email, first_name, last_name, is_active, created_at, updated_at FROM users WHERE is_active = ?"
                ),
                (True,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def search(query: str, limit: int = 20) -> list[dict]:
        """
        Search users by name or email (case-insensitive).

        Args:
            query: Search string to match against first_name, last_name, or email
            limit: Maximum number of results

        Returns:
            List of matching user dicts (without hashed_password)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            like_pattern = f"%{query}%"
            cursor.execute(
                convert_query("""
                    SELECT id, email, first_name, last_name, is_active, created_at, updated_at
                    FROM users
                    WHERE is_active = ?
                      AND (first_name LIKE ? OR last_name LIKE ? OR email LIKE ?)
                    ORDER BY first_name, last_name
                    LIMIT ?
                    """),
                (True, like_pattern, like_pattern, like_pattern, limit),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def delete(user_id: int) -> bool:
        """
        Delete a user (soft delete by setting is_active to False).

        Args:
            user_id: User's ID

        Returns:
            True if user was deleted, False if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("UPDATE users SET is_active = FALSE WHERE id = ?"),
                (user_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_avatar(user_id: int, avatar_url: str | None) -> bool:
        """
        Update a user's avatar URL.

        Args:
            user_id: User's ID
            avatar_url: New avatar URL (or None to clear)

        Returns:
            True if updated successfully, False if user not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "UPDATE users SET avatar_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                ),
                (avatar_url, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_activity_visibility_bulk(user_ids: list[int]) -> dict[int, str]:
        """Get activity_visibility for multiple users.

        Args:
            user_ids: List of user IDs

        Returns:
            Dict mapping user_id to activity_visibility value
        """
        if not user_ids:
            return {}

        with get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(user_ids))
            cursor.execute(
                convert_query(
                    f"SELECT id, activity_visibility FROM users"
                    f" WHERE id IN ({placeholders})"
                ),
                user_ids,
            )
            return {
                row["id"]: row["activity_visibility"] or "friends"
                for row in cursor.fetchall()
            }

    @staticmethod
    def update_activity_visibility(user_id: int, visibility: str) -> bool:
        """Update a user's activity_visibility setting.

        Args:
            user_id: User's ID
            visibility: 'friends' or 'private'

        Returns:
            True if updated successfully
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "UPDATE users SET activity_visibility = ?,"
                    " updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                ),
                (visibility, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_primary_gym(user_id: int, gym_id: int | None) -> bool:
        """Set the user's primary gym ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "UPDATE users SET primary_gym_id = ?,"
                    " updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                ),
                (gym_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_password(user_id: int, hashed_password: str) -> bool:
        """Update a user's password hash.

        Args:
            user_id: User's ID
            hashed_password: New hashed password

        Returns:
            True if updated successfully, False if user not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "UPDATE users SET hashed_password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                ),
                (hashed_password, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def record_failed_login(
        user_id: int, new_attempts: int, locked_until: str | None = None
    ) -> bool:
        """Record a failed login attempt and optionally lock the account.

        Args:
            user_id: User's ID
            new_attempts: Updated count of failed attempts
            locked_until: ISO timestamp when lock expires (None if not locked)

        Returns:
            True if updated successfully
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE id = ?"
                ),
                (new_attempts, locked_until, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def reset_login_attempts(user_id: int) -> bool:
        """Reset failed login counters on successful login.

        Args:
            user_id: User's ID

        Returns:
            True if updated successfully
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?"
                ),
                (user_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_last_login(user_id: int) -> None:
        """Stamp last_login with current UTC time on successful login.

        Args:
            user_id: User's ID
        """
        from rivaflow.core.time_utils import utcnow

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("UPDATE users SET last_login = ? WHERE id = ?"),
                (utcnow(), user_id),
            )

    @staticmethod
    def delete_by_id(user_id: int) -> bool:
        """Hard-delete a user by ID.

        Args:
            user_id: User's ID

        Returns:
            True if deleted, False if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM users WHERE id = ?"),
                (user_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_dashboard_stats() -> dict:
        """Get platform-level user counts for admin dashboard."""
        from datetime import timedelta

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

            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            cursor.execute(
                convert_query("SELECT COUNT(*) FROM users WHERE created_at >= ?"),
                (week_ago,),
            )
            new_users_week = get_count(cursor.fetchone())

        return {
            "total_users": total_users,
            "new_users_week": new_users_week,
        }

    @staticmethod
    def admin_list_users(
        search: str | None = None,
        is_active: bool | None = None,
        is_admin: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """List users with optional filters for admin.

        Returns dict with 'users', 'total', 'limit', 'offset'.
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            query = (
                "SELECT id, email, first_name, last_name,"
                " is_active, is_admin, subscription_tier,"
                " is_beta_user, created_at, last_login"
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
                " is_beta_user, created_at, last_login"
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
    def admin_update_user(user_id: int, updates: list, params: list) -> None:
        """Execute an admin field update on a user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            params.append(user_id)
            cursor.execute(convert_query(query), params)

    @staticmethod
    def get_user_stats_for_admin(user_id: int) -> dict:
        """Get session/comment/follower/following counts for admin user detail."""
        with get_connection() as conn:
            cursor = conn.cursor()

            def extract_count(result):
                if not result:
                    return 0
                return (
                    list(result.values())[0] if isinstance(result, dict) else result[0]
                )

            cursor.execute(
                convert_query("SELECT COUNT(*) FROM sessions WHERE user_id = ?"),
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

        return {
            "sessions": session_count,
            "comments": comment_count,
            "followers": followers_count,
            "following": following_count,
        }

    @staticmethod
    def get_broadcast_users() -> list[dict]:
        """Get all active users for email broadcast (id, email, first_name)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT id, email, first_name FROM users" " WHERE is_active = ?"
                ),
                (True,),
            )
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def get_users_by_ids(user_ids: list[int]) -> list[dict]:
        """Get basic user profiles for a list of user IDs."""
        if not user_ids:
            return []
        with get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(user_ids))
            query = convert_query(f"""
                SELECT id, first_name, last_name, email
                FROM users
                WHERE id IN ({placeholders})
            """)
            cursor.execute(query, user_ids)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_candidate_users(
        user_id: int,
        exclude_ids: list[int] | set[int] | None = None,
    ) -> list[dict]:
        """Get all users excluding a given set of IDs (for friend suggestions)."""
        all_excludes = list(exclude_ids or [])
        if user_id not in all_excludes:
            all_excludes.append(user_id)
        exclude_ids = all_excludes if all_excludes else [0]
        placeholders = ", ".join("?" * len(exclude_ids))

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(f"""
                    SELECT
                        id, username, display_name, belt_rank, belt_stripes,
                        location_city, location_state, primary_gym_id
                    FROM users
                    WHERE id NOT IN ({placeholders})
                    LIMIT 500
                """),
                exclude_ids,
            )
            rows = cursor.fetchall()

            candidates = []
            for row in rows:
                candidates.append(dict(row))
            return candidates

    @staticmethod
    def _row_to_dict(row, include_password: bool = False) -> dict:
        """Convert a database row to a dictionary.

        Args:
            row: Database row
            include_password: If True, keep hashed_password in result.
                Only set this for auth operations that need password verification.
        """
        data = dict(row)

        # Parse timestamps - handle both PostgreSQL (datetime) and SQLite (string)
        if data.get("created_at") and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at") and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("tier_expires_at") and isinstance(data["tier_expires_at"], str):
            data["tier_expires_at"] = datetime.fromisoformat(data["tier_expires_at"])
        if data.get("beta_joined_at") and isinstance(data["beta_joined_at"], str):
            data["beta_joined_at"] = datetime.fromisoformat(data["beta_joined_at"])

        # Strip hashed_password by default for security
        if not include_password:
            data.pop("hashed_password", None)

        return data
