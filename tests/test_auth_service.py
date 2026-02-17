"""Tests for authentication service."""

from datetime import timedelta

import pytest

from rivaflow.core.auth import decode_access_token, verify_password
from rivaflow.core.exceptions import AuthenticationError, ValidationError
from rivaflow.core.services.auth_service import AuthService
from rivaflow.db.repositories.refresh_token_repo import RefreshTokenRepository
from rivaflow.db.repositories.user_repo import UserRepository


class TestAuthServiceRegister:
    """Tests for user registration."""

    def test_register_success(self, temp_db):
        """Test successful user registration."""
        auth_service = AuthService()

        result = auth_service.register(
            email="newuser@example.com",
            password="SecurePass123",
            first_name="New",
            last_name="User",
        )

        assert result is not None
        assert "access_token" in result
        assert "refresh_token" in result
        assert "user" in result
        assert result["user"]["email"] == "newuser@example.com"
        assert result["user"]["first_name"] == "New"
        assert result["user"]["last_name"] == "User"
        assert "hashed_password" not in result["user"]  # Should be sanitized

    def test_register_creates_profile(self, temp_db):
        """Test that registration creates a user profile."""
        auth_service = AuthService()

        result = auth_service.register(
            email="newuser@example.com",
            password="SecurePass123",
            first_name="New",
            last_name="User",
        )

        # Check that profile was created
        from rivaflow.db.repositories.profile_repo import ProfileRepository

        profile_repo = ProfileRepository()
        profile = profile_repo.get(result["user"]["id"])

        assert profile is not None
        assert profile["first_name"] == "New"
        assert profile["last_name"] == "User"

    def test_register_creates_streaks(self, temp_db):
        """Test that registration initializes streak records."""
        auth_service = AuthService()

        result = auth_service.register(
            email="newuser@example.com",
            password="SecurePass123",
            first_name="New",
            last_name="User",
        )

        # Check that streaks were created
        from rivaflow.db.database import convert_query, get_connection

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM streaks WHERE user_id = ?"),
                (result["user"]["id"],),
            )
            streaks = cursor.fetchall()

        assert len(streaks) == 3  # checkin, training, readiness
        streak_types = {
            row["streak_type"] if isinstance(row, dict) else row[1] for row in streaks
        }
        assert "checkin" in streak_types
        assert "training" in streak_types
        assert "readiness" in streak_types

    def test_register_invalid_email(self, temp_db):
        """Test registration with invalid email format."""
        auth_service = AuthService()

        with pytest.raises(ValidationError, match="Email must contain an @ sign"):
            auth_service.register(
                email="not-an-email",
                password="SecurePass123",
                first_name="New",
                last_name="User",
            )

    def test_register_short_password(self, temp_db):
        """Test registration with password too short."""
        auth_service = AuthService()

        with pytest.raises(ValidationError, match="at least 8 characters"):
            auth_service.register(
                email="newuser@example.com",
                password="short",
                first_name="New",
                last_name="User",
            )

    def test_register_no_uppercase(self, temp_db):
        """Test registration with password missing uppercase letter."""
        auth_service = AuthService()

        with pytest.raises(ValidationError, match="uppercase letter"):
            auth_service.register(
                email="newuser@example.com",
                password="nouppercase1",
                first_name="New",
                last_name="User",
            )

    def test_register_no_digit(self, temp_db):
        """Test registration with password missing a digit."""
        auth_service = AuthService()

        with pytest.raises(ValidationError, match="one number"):
            auth_service.register(
                email="newuser@example.com",
                password="NoDigitHere",
                first_name="New",
                last_name="User",
            )

    def test_register_duplicate_email(self, temp_db, test_user):
        """Test registration with already existing email."""
        auth_service = AuthService()

        with pytest.raises(
            ValidationError, match="Unable to create account with this email"
        ):
            auth_service.register(
                email="test@example.com",  # Already exists from test_user fixture
                password="SecurePass123",
                first_name="Duplicate",
                last_name="User",
            )

    def test_register_stores_refresh_token(self, temp_db):
        """Test that registration stores refresh token in database."""
        auth_service = AuthService()

        result = auth_service.register(
            email="newuser@example.com",
            password="SecurePass123",
            first_name="New",
            last_name="User",
        )

        # Check that refresh token was stored
        refresh_token_repo = RefreshTokenRepository()
        token_data = refresh_token_repo.get_by_token(result["refresh_token"])

        assert token_data is not None
        assert token_data["user_id"] == result["user"]["id"]


class TestAuthServiceLogin:
    """Tests for user login."""

    def test_login_success(self, temp_db, test_user):
        """Test successful login with valid credentials."""
        auth_service = AuthService()

        result = auth_service.login(email="test@example.com", password="testpass123")

        assert result is not None
        assert "access_token" in result
        assert "refresh_token" in result
        assert "user" in result
        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["id"] == test_user["id"]

    def test_login_wrong_password(self, temp_db, test_user):
        """Test login with incorrect password."""
        auth_service = AuthService()

        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            auth_service.login(email="test@example.com", password="wrongpassword")

    def test_login_nonexistent_user(self, temp_db):
        """Test login with non-existent email."""
        auth_service = AuthService()

        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            auth_service.login(email="nonexistent@example.com", password="anypassword")

    def test_login_generates_valid_jwt(self, temp_db, test_user):
        """Test that login generates a valid JWT token."""
        auth_service = AuthService()

        result = auth_service.login(email="test@example.com", password="testpass123")

        # Decode and verify token
        payload = decode_access_token(result["access_token"])
        assert payload["sub"] == str(test_user["id"])

    def test_login_stores_refresh_token(self, temp_db, test_user):
        """Test that login stores refresh token in database."""
        auth_service = AuthService()

        result = auth_service.login(email="test@example.com", password="testpass123")

        # Check that refresh token was stored
        refresh_token_repo = RefreshTokenRepository()
        token_data = refresh_token_repo.get_by_token(result["refresh_token"])

        assert token_data is not None
        assert token_data["user_id"] == test_user["id"]

    def test_login_inactive_user(self, temp_db):
        """Test that inactive users cannot login."""
        # Create inactive user
        user_repo = UserRepository()
        from rivaflow.core.auth import hash_password

        user = user_repo.create(
            email="inactive@example.com",
            hashed_password=hash_password("testpass123"),
            first_name="Inactive",
            last_name="User",
        )

        # Mark as inactive
        from rivaflow.db.database import convert_query, get_connection

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("UPDATE users SET is_active = ? WHERE id = ?"),
                (False, user["id"]),
            )

        auth_service = AuthService()

        with pytest.raises(AuthenticationError, match="Account is inactive"):
            auth_service.login(email="inactive@example.com", password="testpass123")


class TestAuthServiceRefreshToken:
    """Tests for token refresh functionality."""

    def test_refresh_access_token_success(self, temp_db, test_user):
        """Test successful access token refresh."""
        auth_service = AuthService()

        # First login to get refresh token
        login_result = auth_service.login(
            email="test@example.com", password="testpass123"
        )

        # Refresh access token
        refresh_result = auth_service.refresh_access_token(
            refresh_token=login_result["refresh_token"]
        )

        assert "access_token" in refresh_result
        assert refresh_result["token_type"] == "bearer"

        # Verify new token is valid
        payload = decode_access_token(refresh_result["access_token"])
        assert payload["sub"] == str(test_user["id"])

    def test_refresh_with_invalid_token(self, temp_db):
        """Test refresh with invalid token."""
        auth_service = AuthService()

        with pytest.raises(ValueError, match="Invalid"):
            auth_service.refresh_access_token(refresh_token="invalid-token-12345")


class TestAuthServiceLogout:
    """Tests for logout functionality."""

    def test_logout_success(self, temp_db, test_user):
        """Test successful logout."""
        auth_service = AuthService()

        # Login first
        login_result = auth_service.login(
            email="test@example.com", password="testpass123"
        )

        # Logout
        result = auth_service.logout(login_result["refresh_token"])
        assert result is True

        # Verify token is no longer valid
        refresh_token_repo = RefreshTokenRepository()
        token_data = refresh_token_repo.get_by_token(login_result["refresh_token"])
        assert token_data is None

    def test_logout_all_devices(self, temp_db, test_user):
        """Test logout from all devices."""
        auth_service = AuthService()

        # Create multiple sessions
        login1 = auth_service.login(email="test@example.com", password="testpass123")
        login2 = auth_service.login(email="test@example.com", password="testpass123")

        # Logout from all devices
        count = auth_service.logout_all_devices(test_user["id"])
        assert count >= 2

        # Verify all tokens are invalidated
        refresh_token_repo = RefreshTokenRepository()
        assert refresh_token_repo.get_by_token(login1["refresh_token"]) is None
        assert refresh_token_repo.get_by_token(login2["refresh_token"]) is None


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_password_hashing(self, temp_db):
        """Test that passwords are properly hashed."""
        from rivaflow.core.auth import hash_password

        password = "mySecurePassword123"
        hashed = hash_password(password)

        # Hash should be different from original
        assert hashed != password

        # Hash should start with bcrypt identifier
        assert hashed.startswith("$2b$")

    def test_password_verification(self, temp_db):
        """Test password verification."""
        from rivaflow.core.auth import hash_password

        password = "mySecurePassword123"
        hashed = hash_password(password)

        # Correct password should verify
        assert verify_password(password, hashed) is True

        # Wrong password should not verify
        assert verify_password("wrongPassword", hashed) is False

    def test_long_password_truncation(self, temp_db):
        """Test that bcrypt 72-byte limit is handled correctly."""
        from rivaflow.core.auth import hash_password

        # Create password longer than 72 bytes
        long_password = "a" * 100
        hashed = hash_password(long_password)

        # Should still verify correctly
        assert verify_password(long_password, hashed) is True


class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    def test_create_access_token(self, temp_db):
        """Test JWT token creation."""
        from rivaflow.core.auth import create_access_token

        token = create_access_token(data={"sub": "123"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self, temp_db):
        """Test JWT token decoding."""
        from rivaflow.core.auth import create_access_token, decode_access_token

        user_id = "123"
        token = create_access_token(data={"sub": user_id})

        payload = decode_access_token(token)
        assert payload["sub"] == user_id
        assert "exp" in payload  # Expiration should be set

    def test_expired_token_rejection(self, temp_db):
        """Test that expired tokens are rejected."""
        from rivaflow.core.auth import create_access_token, decode_access_token

        # Create token that expires immediately
        token = create_access_token(
            data={"sub": "123"}, expires_delta=timedelta(seconds=-1)  # Already expired
        )

        result = decode_access_token(token)
        assert result is None

    def test_invalid_token_rejection(self, temp_db):
        """Test that invalid tokens are rejected."""
        from rivaflow.core.auth import decode_access_token

        result = decode_access_token("invalid.token.string")
        assert result is None


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_emails(self, temp_db):
        """Test that valid emails are accepted."""
        auth_service = AuthService()

        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user123@test-domain.com",
        ]

        for email in valid_emails:
            assert auth_service._is_valid_email(email) is True

    def test_invalid_emails(self, temp_db):
        """Test that invalid emails are rejected."""
        auth_service = AuthService()

        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user @example.com",
            "user@.com",
        ]

        for email in invalid_emails:
            assert auth_service._is_valid_email(email) is False
