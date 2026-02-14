"""Repository for user data access."""

from datetime import datetime

from rivaflow.db.database import convert_query, execute_insert, get_connection


class UserRepository:
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
                convert_query("SELECT * FROM users WHERE id = ?"), (user_id,)
            )
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"User {user_id} was inserted but cannot be retrieved")

            return UserRepository._row_to_dict(row)

    @staticmethod
    def get_by_email(email: str) -> dict | None:
        """
        Get a user by email address.

        Args:
            email: User's email address

        Returns:
            User dictionary or None if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM users WHERE email = ?"), (email,)
            )
            row = cursor.fetchone()
            if row:
                return UserRepository._row_to_dict(row)
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
                convert_query("SELECT * FROM users WHERE id = ?"), (user_id,)
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
                convert_query("SELECT * FROM users WHERE id = ?"), (user_id,)
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
                (1,),
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
                (1, like_pattern, like_pattern, like_pattern, limit),
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
    def _row_to_dict(row) -> dict:
        """Convert a database row to a dictionary."""
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

        # Remove hashed_password from returned dict for security
        # (services that need it can access directly from row)
        # Actually, keep it for now as auth service needs it for verification
        # We'll remove it in the API response layer

        return data
