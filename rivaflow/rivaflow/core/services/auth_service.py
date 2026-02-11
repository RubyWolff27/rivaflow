"""Service layer for authentication operations."""

import logging
from typing import Any

from rivaflow.core.auth import (
    create_access_token,
    generate_refresh_token,
    get_refresh_token_expiry,
    hash_password,
    verify_password,
)
from rivaflow.core.email_validation import validate_email_address
from rivaflow.core.exceptions import AuthenticationError, ValidationError
from rivaflow.db.repositories.profile_repo import ProfileRepository
from rivaflow.db.repositories.refresh_token_repo import RefreshTokenRepository
from rivaflow.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


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
        default_gym: str | None = None,
        current_grade: str | None = None,
    ) -> dict[str, Any]:
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
        # Validate email format and block disposable emails
        is_valid, normalized_email, error = validate_email_address(
            email,
            check_deliverability=False,  # Skip MX check for performance
            allow_disposable=True,  # Allow disposable emails for testing/beta
        )
        if not is_valid:
            error_code = error.get("code", "INVALID_EMAIL")
            if error_code == "DISPOSABLE_EMAIL":
                action = "Use your personal or work email address instead of temporary email services"
            else:
                action = "Please provide a valid email address (e.g., user@example.com)"

            raise ValidationError(
                message=error.get("message", "Invalid email format"),
                details={"code": error_code},
                action=action,
            )

        # Use normalized email (lowercase domain)
        email = normalized_email

        # Validate password strength
        if len(password) < 8:
            raise ValidationError(
                message="Password must be at least 8 characters long",
                action="Choose a password with at least 8 characters.",
            )
        if not any(c.isupper() for c in password):
            raise ValidationError(
                message="Password must contain at least one uppercase letter",
                action="Add an uppercase letter to your password.",
            )
        if not any(c.islower() for c in password):
            raise ValidationError(
                message="Password must contain at least one lowercase letter",
                action="Add a lowercase letter to your password.",
            )
        if not any(c.isdigit() for c in password):
            raise ValidationError(
                message="Password must contain at least one number",
                action="Add a number to your password.",
            )

        # Check if email already exists
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise ValidationError(
                message="Email already registered",
                action="If you already have an account, please login instead. If you forgot your password, use the 'Forgot Password' link.",
            )

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
        except (ConnectionError, OSError, ValueError) as e:
            raise ValueError(f"Failed to create user: {str(e)}")

        # Create profile + streaks in a single transaction
        try:
            import logging

            from rivaflow.db.database import convert_query, get_connection

            logger = logging.getLogger(__name__)

            with get_connection() as conn:
                cursor = conn.cursor()

                # Profile
                cursor.execute(
                    convert_query("""
                    INSERT INTO profile (user_id, first_name, last_name, email)
                    VALUES (?, ?, ?, ?)
                    """),
                    (user["id"], first_name, last_name, email),
                )

                # Streaks
                for streak_type in ("checkin", "training", "readiness"):
                    cursor.execute(
                        convert_query(
                            "INSERT INTO streaks (streak_type, current_streak, longest_streak, user_id) VALUES (?, ?, ?, ?)"
                        ),
                        (streak_type, 0, 0, user["id"]),
                    )
        except (ConnectionError, OSError, ValueError) as e:
            logger.error(f"Failed to create profile/streaks for user {user['id']}: {e}")
            try:
                from rivaflow.db.database import convert_query, get_connection

                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        convert_query("DELETE FROM users WHERE id = ?"),
                        (user["id"],),
                    )
            except (ConnectionError, OSError):
                pass  # Best effort cleanup
            raise ValueError("Registration failed - unable to initialize user data")

        # Update profile with gym/belt if provided during registration
        if default_gym or current_grade:
            try:
                self.profile_repo.update(
                    user_id=user["id"],
                    default_gym=default_gym,
                    current_grade=current_grade,
                )
            except (ConnectionError, OSError, ValueError) as e:
                logger.warning(f"Failed to set gym/belt for user {user['id']}: {e}")

        # Generate tokens (sub must be string for JWT)
        access_token = create_access_token(data={"sub": str(user["id"])})
        refresh_token = generate_refresh_token()
        expires_at = get_refresh_token_expiry()

        # Store refresh token
        self.refresh_token_repo.create(
            user_id=user["id"], token=refresh_token, expires_at=expires_at
        )

        # Send welcome email (fire and forget — don't block registration)
        try:
            from rivaflow.core.services.email_service import EmailService

            email_service = EmailService()
            email_service.send_welcome_email(
                email=email,
                first_name=first_name,
            )
        except (ConnectionError, OSError, RuntimeError) as e:
            logger.warning(f"Failed to send welcome email to {email}: {e}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": self._sanitize_user(user),
        }

    def login(self, email: str, password: str) -> dict[str, Any]:
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
            raise AuthenticationError(
                message="Invalid email or password",
                action="Double-check your email and password. If you forgot your password, click 'Forgot Password' to reset it.",
            )

        # Check if user is active
        if not user.get("is_active"):
            raise AuthenticationError(
                message="Account is inactive",
                action="Your account has been deactivated. Please contact support@rivaflow.com for assistance.",
            )

        # Verify password
        if not verify_password(password, user["hashed_password"]):
            raise AuthenticationError(
                message="Invalid email or password",
                action="Double-check your email and password. If you forgot your password, click 'Forgot Password' to reset it.",
            )

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

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
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
        access_token = create_access_token(data={"sub": str(user["id"])})

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
        """
        Validate email format (legacy method for backward compatibility).

        Prefer using rivaflow.core.email_validation.validate_email_address() directly.
        """
        from rivaflow.core.email_validation import is_valid_email_simple

        return is_valid_email_simple(email, allow_disposable=True)

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

        from rivaflow.core.services.email_service import EmailService
        from rivaflow.db.repositories.password_reset_token_repo import (
            PasswordResetTokenRepository,
        )

        logger = logging.getLogger(__name__)

        # Get user by email
        user = self.user_repo.get_by_email(email)

        # Only send email if user exists (but don't reveal this to caller)
        if user and user.get("is_active"):
            token_repo = PasswordResetTokenRepository()

            # Check rate limit (max 3 requests per hour)
            recent_requests = token_repo.count_recent_requests(user["id"], hours=1)
            if recent_requests >= 3:
                logger.warning(
                    f"Password reset rate limit exceeded for user {user['id']}"
                )
                # Still return True to not reveal rate limiting
                return True

            # Create reset token
            token = token_repo.create_token(user["id"], expiry_hours=1)

            # Send email
            email_service = EmailService()
            success = email_service.send_password_reset_email(
                to_email=email, reset_token=token, user_name=user.get("first_name")
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

        from rivaflow.core.services.email_service import EmailService
        from rivaflow.db.repositories.password_reset_token_repo import (
            PasswordResetTokenRepository,
        )

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
            from rivaflow.db.database import convert_query, get_connection

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    convert_query("""
                    UPDATE users
                    SET hashed_password = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """),
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
                to_email=user["email"], user_name=user.get("first_name")
            )

            logger.info(f"Password reset successful for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Password reset failed for user {user_id}: {e}")
            raise

    @staticmethod
    def _sanitize_user(user: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive fields from user dict."""
        sanitized = user.copy()
        sanitized.pop("hashed_password", None)
        # Convert datetime objects to ISO format strings for JSON serialization
        if "created_at" in sanitized and hasattr(sanitized["created_at"], "isoformat"):
            sanitized["created_at"] = sanitized["created_at"].isoformat()
        if "updated_at" in sanitized and hasattr(sanitized["updated_at"], "isoformat"):
            sanitized["updated_at"] = sanitized["updated_at"].isoformat()
        if (
            "tier_expires_at" in sanitized
            and sanitized["tier_expires_at"]
            and hasattr(sanitized["tier_expires_at"], "isoformat")
        ):
            sanitized["tier_expires_at"] = sanitized["tier_expires_at"].isoformat()
        if (
            "beta_joined_at" in sanitized
            and sanitized["beta_joined_at"]
            and hasattr(sanitized["beta_joined_at"], "isoformat")
        ):
            sanitized["beta_joined_at"] = sanitized["beta_joined_at"].isoformat()
        return sanitized
