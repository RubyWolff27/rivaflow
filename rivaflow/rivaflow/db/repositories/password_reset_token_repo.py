"""Repository for password reset token management."""

import hashlib
import secrets
from datetime import datetime, timedelta

from rivaflow.core.time_utils import utcnow
from rivaflow.db.database import convert_query, get_connection


class PasswordResetTokenRepository:
    """Data access layer for password reset tokens."""

    @staticmethod
    def _hash_token(token: str) -> str:
        """
        Hash a reset token using SHA-256.

        We use SHA-256 instead of bcrypt because:
        1. Reset tokens are already cryptographically random (32 bytes)
        2. SHA-256 is faster and sufficient for this use case
        3. We don't need the computational slowness of bcrypt here

        Args:
            token: Plain token string

        Returns:
            Hexadecimal hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def create_token(user_id: int, expiry_hours: int = 1) -> str:
        """
        Create a password reset token for a user.

        The token is hashed before storage for security. If the database
        is compromised, the hashed tokens cannot be used to reset passwords.

        Args:
            user_id: User ID
            expiry_hours: Token expiry time in hours (default 1)

        Returns:
            Reset token string (unhashed, to send to user)
        """
        # Generate secure random token (32 bytes = 256 bits)
        token = secrets.token_urlsafe(32)

        # Hash the token before storing
        token_hash = PasswordResetTokenRepository._hash_token(token)

        # Calculate expiry timestamp
        expires_at = utcnow() + timedelta(hours=expiry_hours)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (?, ?, ?)
                """),
                (user_id, token_hash, expires_at.isoformat()),
            )

        # Return the plain token (to send to user via email)
        # The hashed version is stored in the database
        return token

    @staticmethod
    def get_by_token(token: str) -> dict | None:
        """
        Get password reset token record by token string.

        Args:
            token: Reset token (unhashed)

        Returns:
            Token record dict or None if not found
        """
        # Hash the token before querying
        token_hash = PasswordResetTokenRepository._hash_token(token)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT id, user_id, token, expires_at, used_at, created_at
                FROM password_reset_tokens
                WHERE token = ?
                """),
                (token_hash,),
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
        # Handle both PostgreSQL (datetime object) and SQLite (string)
        expires_at = token_record["expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)

        if utcnow() > expires_at:
            return False

        return True

    @staticmethod
    def mark_as_used(token: str) -> bool:
        """
        Mark a token as used.

        Args:
            token: Reset token (unhashed)

        Returns:
            True if marked successfully, False if token not found
        """
        # Hash the token before querying
        token_hash = PasswordResetTokenRepository._hash_token(token)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                UPDATE password_reset_tokens
                SET used_at = CURRENT_TIMESTAMP
                WHERE token = ?
                """),
                (token_hash,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_user_id_from_token(token: str) -> int | None:
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
                convert_query("""
                UPDATE password_reset_tokens
                SET used_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND used_at IS NULL
                """),
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
        cutoff = utcnow() - timedelta(days=days_old)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                DELETE FROM password_reset_tokens
                WHERE expires_at < ?
                """),
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
        since = utcnow() - timedelta(hours=hours)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT COUNT(*) as count
                FROM password_reset_tokens
                WHERE user_id = ? AND created_at > ?
                """),
                (user_id, since.isoformat()),
            )
            row = cursor.fetchone()
            if not row:
                return 0
            return row["count"]
