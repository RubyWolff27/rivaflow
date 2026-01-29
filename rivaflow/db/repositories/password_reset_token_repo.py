"""Repository for password reset token management."""
import secrets
from datetime import datetime, timedelta
from typing import Optional

from rivaflow.db.database import get_connection


class PasswordResetTokenRepository:
    """Data access layer for password reset tokens."""

    @staticmethod
    def create_token(user_id: int, expiry_hours: int = 1) -> str:
        """
        Create a password reset token for a user.

        Args:
            user_id: User ID
            expiry_hours: Token expiry time in hours (default 1)

        Returns:
            Reset token string
        """
        # Generate secure random token
        token = secrets.token_urlsafe(32)

        # Calculate expiry timestamp
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, token, expires_at.isoformat()),
            )

        return token

    @staticmethod
    def get_by_token(token: str) -> Optional[dict]:
        """
        Get password reset token record by token string.

        Args:
            token: Reset token

        Returns:
            Token record dict or None if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, token, expires_at, used_at, created_at
                FROM password_reset_tokens
                WHERE token = %s
                """,
                (token,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return dict(row)

    @staticmethod
    def is_valid(token: str) -> bool:
        """
        Check if a token is valid (exists, not used, not expired).

        Args:
            token: Reset token

        Returns:
            True if valid, False otherwise
        """
        token_record = PasswordResetTokenRepository.get_by_token(token)

        if not token_record:
            return False

        # Check if already used
        if token_record.get("used_at"):
            return False

        # Check if expired
        expires_at = datetime.fromisoformat(token_record["expires_at"])
        if datetime.utcnow() > expires_at:
            return False

        return True

    @staticmethod
    def mark_as_used(token: str) -> bool:
        """
        Mark a token as used.

        Args:
            token: Reset token

        Returns:
            True if marked successfully, False if token not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE password_reset_tokens
                SET used_at = CURRENT_TIMESTAMP
                WHERE token = %s
                """,
                (token,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[int]:
        """
        Get user ID associated with a valid token.

        Args:
            token: Reset token

        Returns:
            User ID or None if token invalid
        """
        if not PasswordResetTokenRepository.is_valid(token):
            return None

        token_record = PasswordResetTokenRepository.get_by_token(token)
        return token_record["user_id"] if token_record else None

    @staticmethod
    def invalidate_all_user_tokens(user_id: int) -> int:
        """
        Invalidate all unused tokens for a user.

        Useful when user successfully resets password.

        Args:
            user_id: User ID

        Returns:
            Number of tokens invalidated
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE password_reset_tokens
                SET used_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND used_at IS NULL
                """,
                (user_id,),
            )
            return cursor.rowcount

    @staticmethod
    def cleanup_expired_tokens(days_old: int = 7) -> int:
        """
        Delete expired tokens older than specified days.

        Args:
            days_old: Delete tokens older than this many days (default 7)

        Returns:
            Number of tokens deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days_old)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM password_reset_tokens
                WHERE expires_at < %s
                """,
                (cutoff.isoformat(),),
            )
            return cursor.rowcount

    @staticmethod
    def count_recent_requests(user_id: int, hours: int = 1) -> int:
        """
        Count how many reset requests a user has made recently.

        Used for rate limiting.

        Args:
            user_id: User ID
            hours: Time window in hours (default 1)

        Returns:
            Number of reset requests in time window
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM password_reset_tokens
                WHERE user_id = %s AND created_at > %s
                """,
                (user_id, since.isoformat()),
            )
            row = cursor.fetchone()
            return dict(row)["count"] if row else 0
