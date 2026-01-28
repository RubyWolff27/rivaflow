"""Repository for refresh token data access."""
import sqlite3
from datetime import datetime
from typing import Optional

from rivaflow.db.database import get_connection


class RefreshTokenRepository:
    """Data access layer for refresh tokens."""

    @staticmethod
    def create(user_id: int, token: str, expires_at: str) -> dict:
        """
        Create a new refresh token.

        Args:
            user_id: User's ID
            token: The refresh token string
            expires_at: ISO 8601 expiration datetime

        Returns:
            Dictionary representation of the created token
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO refresh_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, token, expires_at),
            )
            token_id = cursor.lastrowid

            # Fetch and return the created token
            cursor.execute("SELECT * FROM refresh_tokens WHERE id = %s", (token_id,))
            row = cursor.fetchone()
            return RefreshTokenRepository._row_to_dict(row)

    @staticmethod
    def get_by_token(token: str) -> Optional[dict]:
        """
        Get a refresh token by its token string.

        Args:
            token: The refresh token string

        Returns:
            Token dictionary or None if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM refresh_tokens WHERE token = %s", (token,))
            row = cursor.fetchone()
            if row:
                return RefreshTokenRepository._row_to_dict(row)
            return None

    @staticmethod
    def get_by_user_id(user_id: int) -> list[dict]:
        """
        Get all refresh tokens for a user.

        Args:
            user_id: User's ID

        Returns:
            List of token dictionaries
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM refresh_tokens
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
            return [RefreshTokenRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def delete_by_token(token: str) -> bool:
        """
        Delete a refresh token.

        Args:
            token: The refresh token string

        Returns:
            True if token was deleted, False if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM refresh_tokens WHERE token = %s", (token,))
            return cursor.rowcount > 0

    @staticmethod
    def delete_by_user_id(user_id: int) -> int:
        """
        Delete all refresh tokens for a user (logout from all devices).

        Args:
            user_id: User's ID

        Returns:
            Number of tokens deleted
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM refresh_tokens WHERE user_id = %s", (user_id,))
            return cursor.rowcount

    @staticmethod
    def delete_expired() -> int:
        """
        Delete all expired refresh tokens.

        Returns:
            Number of tokens deleted
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "DELETE FROM refresh_tokens WHERE expires_at < %s", (now,)
            )
            return cursor.rowcount

    @staticmethod
    def is_valid(token: str) -> bool:
        """
        Check if a refresh token is valid (exists and not expired).

        Args:
            token: The refresh token string

        Returns:
            True if valid, False otherwise
        """
        token_data = RefreshTokenRepository.get_by_token(token)
        if not token_data:
            return False

        # Check if expired
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if expires_at < datetime.utcnow():
            # Clean up expired token
            RefreshTokenRepository.delete_by_token(token)
            return False

        return True

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)

        # Parse timestamps
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("expires_at"):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])

        return data
