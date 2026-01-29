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
            import traceback
            print(f"[AUTH] User creation failed: {type(e).__name__}: {str(e)}")
            print(f"[AUTH] Traceback: {traceback.format_exc()}")
            raise ValueError(f"Failed to create user: {type(e).__name__}: {str(e)}")

        # Create default profile for user
        try:
            from rivaflow.db.database import get_connection

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
            # If profile creation fails, we should probably rollback user creation
            # For now, log the error
            print(f"Warning: Failed to create profile for user {user['id']}: {e}")

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
            print(f"Warning: Failed to create streaks for user {user['id']}: {e}")

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
