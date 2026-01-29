"""Service layer for authentication operations."""
import re
from typing import Optional

from rivaflow.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    generate_refresh_token,
    get_refresh_token_expiry,
    decode_access_token,
)
from rivaflow.db.repositories.user_repo import UserRepository
from rivaflow.db.repositories.refresh_token_repo import RefreshTokenRepository
from rivaflow.db.repositories.profile_repo import ProfileRepository


class AuthService:
    """Business logic for authentication."""

    def __init__(self):
        self.user_repo = UserRepository()
        self.refresh_token_repo = RefreshTokenRepository()
        self.profile_repo = ProfileRepository()

    def register(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> dict:
        """
        Register a new user with email and password.

        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            first_name: User's first name
            last_name: User's last name

        Returns:
            Dictionary with access_token, refresh_token, and user info

        Raises:
            ValueError: If validation fails or email already exists
        """
        # Validate email format
        if not self._is_valid_email(email):
            raise ValueError("Invalid email format")

        # Validate password strength
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check if email already exists
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("Email already registered")

        # Hash password
        hashed_pwd = hash_password(password)

        # Create user
        try:
            user = self.user_repo.create(
                email=email,
                hashed_password=hashed_pwd,
                first_name=first_name,
                last_name=last_name,
            )
        except Exception as e:
            raise ValueError(f"Failed to create user: {str(e)}")

        # Create default profile for user
        try:
            from rivaflow.db.database import get_connection
            import logging
            logger = logging.getLogger(__name__)

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO profile (user_id, first_name, last_name, email)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (user["id"], first_name, last_name, email),
                )
        except Exception as e:
            # Profile creation failed - delete the user and fail registration
            logger.error(f"Failed to create profile for user {user['id']}: {e}")
            try:
                # Attempt to delete the user to maintain consistency
                from rivaflow.db.database import get_connection
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM users WHERE id = %s", (user["id"],))
            except:
                pass  # Best effort cleanup
            raise ValueError("Registration failed - unable to create user profile")

        # Initialize streak records for the new user
        try:
            from rivaflow.db.database import get_connection

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO streaks (streak_type, current_streak, longest_streak, user_id) VALUES (%s, %s, %s, %s)",
                    ("checkin", 0, 0, user["id"]),
                )
                cursor.execute(
                    "INSERT INTO streaks (streak_type, current_streak, longest_streak, user_id) VALUES (%s, %s, %s, %s)",
                    ("training", 0, 0, user["id"]),
                )
                cursor.execute(
                    "INSERT INTO streaks (streak_type, current_streak, longest_streak, user_id) VALUES (%s, %s, %s, %s)",
                    ("readiness", 0, 0, user["id"]),
                )
        except Exception as e:
            # Streaks creation failed - delete user and profile, fail registration
            logger.error(f"Failed to create streaks for user {user['id']}: {e}")
            try:
                # Cleanup: delete user (CASCADE will delete profile)
                from rivaflow.db.database import get_connection
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM users WHERE id = %s", (user["id"],))
            except:
                pass  # Best effort cleanup
            raise ValueError("Registration failed - unable to initialize user data")

        # Generate tokens (sub must be string for JWT)
        access_token = create_access_token(data={"sub": str(user["id"])})
        refresh_token = generate_refresh_token()
        expires_at = get_refresh_token_expiry()

        # Store refresh token
        self.refresh_token_repo.create(
            user_id=user["id"], token=refresh_token, expires_at=expires_at
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": self._sanitize_user(user),
        }

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email address
            password: Plain text password

        Returns:
            Dictionary with access_token, refresh_token, and user info

        Raises:
            ValueError: If credentials are invalid
        """
        # Get user by email
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")

        # Check if user is active
        if not user.get("is_active"):
            raise ValueError("Account is inactive")

        # Verify password
        if not verify_password(password, user["hashed_password"]):
            raise ValueError("Invalid email or password")

        # Generate tokens (sub must be string for JWT)
        access_token = create_access_token(data={"sub": str(user["id"])})
        refresh_token = generate_refresh_token()
        expires_at = get_refresh_token_expiry()

        # Store refresh token
        self.refresh_token_repo.create(
            user_id=user["id"], token=refresh_token, expires_at=expires_at
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": self._sanitize_user(user),
        }

    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Generate a new access token using a refresh token.

        Args:
            refresh_token: The refresh token string

        Returns:
            Dictionary with new access_token

        Raises:
            ValueError: If refresh token is invalid or expired
        """
        # Validate refresh token
        if not self.refresh_token_repo.is_valid(refresh_token):
            raise ValueError("Invalid or expired refresh token")

        # Get token data
        token_data = self.refresh_token_repo.get_by_token(refresh_token)
        if not token_data:
            raise ValueError("Invalid refresh token")

        # Get user
        user = self.user_repo.get_by_id(token_data["user_id"])
        if not user or not user.get("is_active"):
            raise ValueError("User not found or inactive")

        # Generate new access token
        access_token = create_access_token(data={"sub": user["id"]})

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    def logout(self, refresh_token: str) -> bool:
        """
        Logout a user by invalidating their refresh token.

        Args:
            refresh_token: The refresh token to invalidate

        Returns:
            True if successful
        """
        return self.refresh_token_repo.delete_by_token(refresh_token)

    def logout_all_devices(self, user_id: int) -> int:
        """
        Logout a user from all devices by invalidating all their refresh tokens.

        Args:
            user_id: User's ID

        Returns:
            Number of tokens invalidated
        """
        return self.refresh_token_repo.delete_by_user_id(user_id)

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format using regex."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def request_password_reset(self, email: str) -> bool:
        """
        Request a password reset for a user.

        Sends an email with a password reset link if the user exists.
        Always returns True to prevent user enumeration.

        Args:
            email: User's email address

        Returns:
            True (always, for security)
        """
        import logging
        from rivaflow.db.repositories.password_reset_token_repo import PasswordResetTokenRepository
        from rivaflow.core.services.email_service import EmailService

        logger = logging.getLogger(__name__)

        # Get user by email
        user = self.user_repo.get_by_email(email)

        # Only send email if user exists (but don't reveal this to caller)
        if user and user.get("is_active"):
            token_repo = PasswordResetTokenRepository()

            # Check rate limit (max 3 requests per hour)
            recent_requests = token_repo.count_recent_requests(user["id"], hours=1)
            if recent_requests >= 3:
                logger.warning(f"Password reset rate limit exceeded for user {user['id']}")
                # Still return True to not reveal rate limiting
                return True

            # Create reset token
            token = token_repo.create_token(user["id"], expiry_hours=1)

            # Send email
            email_service = EmailService()
            success = email_service.send_password_reset_email(
                to_email=email,
                reset_token=token,
                user_name=user.get("first_name")
            )

            if success:
                logger.info(f"Password reset email sent to {email}")
            else:
                logger.error(f"Failed to send password reset email to {email}")

        else:
            logger.info(f"Password reset requested for non-existent email: {email}")

        # Always return True (don't reveal if user exists)
        return True

    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset a user's password using a reset token.

        Args:
            token: Password reset token
            new_password: New password (plain text, will be hashed)

        Returns:
            True if successful, False if token invalid

        Raises:
            ValueError: If password validation fails
        """
        import logging
        from rivaflow.db.repositories.password_reset_token_repo import PasswordResetTokenRepository
        from rivaflow.core.services.email_service import EmailService

        logger = logging.getLogger(__name__)

        # Validate password strength
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        token_repo = PasswordResetTokenRepository()

        # Get user ID from token
        user_id = token_repo.get_user_id_from_token(token)
        if not user_id:
            return False

        # Get user
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False

        # Hash new password
        hashed_pwd = hash_password(new_password)

        # Update user's password
        try:
            from rivaflow.db.database import get_connection

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE users
                    SET hashed_password = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (hashed_pwd, user_id),
                )

            # Mark token as used
            token_repo.mark_as_used(token)

            # Invalidate all other unused reset tokens for this user
            token_repo.invalidate_all_user_tokens(user_id)

            # Invalidate all refresh tokens (logout from all devices for security)
            self.refresh_token_repo.delete_by_user_id(user_id)

            # Send confirmation email
            email_service = EmailService()
            email_service.send_password_changed_confirmation(
                to_email=user["email"],
                user_name=user.get("first_name")
            )

            logger.info(f"Password reset successful for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Password reset failed for user {user_id}: {e}")
            raise

    @staticmethod
    def _sanitize_user(user: dict) -> dict:
        """Remove sensitive fields from user dict."""
        sanitized = user.copy()
        sanitized.pop("hashed_password", None)
        # Convert datetime objects to ISO format strings for JSON serialization
        if "created_at" in sanitized and hasattr(sanitized["created_at"], "isoformat"):
            sanitized["created_at"] = sanitized["created_at"].isoformat()
        if "updated_at" in sanitized and hasattr(sanitized["updated_at"], "isoformat"):
            sanitized["updated_at"] = sanitized["updated_at"].isoformat()
        return sanitized
