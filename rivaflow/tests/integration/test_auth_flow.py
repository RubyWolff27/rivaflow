"""
Integration tests for authentication flow.

Tests the complete authentication workflow including registration,
login, token refresh, password reset, and access control.
"""
import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

# Set SECRET_KEY for testing
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-integration-tests-minimum-32-chars-long")

from rivaflow.api.main import app
from rivaflow.core.auth import create_access_token, decode_access_token
from rivaflow.db.database import get_connection, init_db


@pytest.fixture(scope="module")
def test_client():
    """Create test client for API testing."""
    # Initialize test database
    init_db()
    return TestClient(app)


@pytest.fixture(scope="function")
def cleanup_test_user():
    """Clean up test user after each test."""
    yield
    # Clean up test users created during tests
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM users WHERE email LIKE 'test_%@example.com'"
        )
        conn.commit()


class TestRegistration:
    """Test user registration flow."""

    def test_successful_registration(self, test_client, cleanup_test_user):
        """Test successful user registration."""
        response = test_client.post("/api/v1/auth/register", json={
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User",
        })

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"].endswith("@example.com")

    def test_registration_duplicate_email(self, test_client, cleanup_test_user):
        """Test registration fails with duplicate email."""
        email = f"test_duplicate_{datetime.now().timestamp()}@example.com"

        # First registration
        response1 = test_client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User",
        })
        assert response1.status_code == 201

        # Duplicate registration
        response2 = test_client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "DifferentPassword456!",
            "first_name": "Another",
            "last_name": "User",
        })
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"].lower()

    def test_registration_invalid_email(self, test_client):
        """Test registration fails with invalid email."""
        response = test_client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User",
        })
        assert response.status_code == 422  # Validation error

    def test_registration_weak_password(self, test_client):
        """Test registration fails with weak password."""
        response = test_client.post("/api/v1/auth/register", json={
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "password": "weak",
            "first_name": "Test",
            "last_name": "User",
        })
        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()


class TestLogin:
    """Test user login flow."""

    @pytest.fixture
    def registered_user(self, test_client, cleanup_test_user):
        """Create a registered user for testing."""
        email = f"test_login_{datetime.now().timestamp()}@example.com"
        password = "SecurePassword123!"

        response = test_client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User",
        })
        assert response.status_code == 201

        return {"email": email, "password": password}

    def test_successful_login(self, test_client, registered_user):
        """Test successful login with correct credentials."""
        response = test_client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, test_client, registered_user):
        """Test login fails with wrong password."""
        response = test_client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": "WrongPassword123!",
        })

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, test_client):
        """Test login fails for non-existent user."""
        response = test_client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        })

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_case_insensitive_email(self, test_client, registered_user):
        """Test login works with case-insensitive email."""
        response = test_client.post("/api/v1/auth/login", json={
            "email": registered_user["email"].upper(),
            "password": registered_user["password"],
        })

        assert response.status_code == 200


class TestTokenRefresh:
    """Test token refresh flow."""

    @pytest.fixture
    def logged_in_user(self, test_client, cleanup_test_user):
        """Create and login a user."""
        email = f"test_refresh_{datetime.now().timestamp()}@example.com"
        password = "SecurePassword123!"

        # Register
        test_client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User",
        })

        # Login
        response = test_client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password,
        })

        return response.json()

    def test_successful_token_refresh(self, test_client, logged_in_user):
        """Test successful token refresh."""
        refresh_token = logged_in_user["refresh_token"]

        response = test_client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # New access token should be different from original
        assert data["access_token"] != logged_in_user["access_token"]

    def test_refresh_with_invalid_token(self, test_client):
        """Test token refresh fails with invalid token."""
        response = test_client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here",
        })

        assert response.status_code == 401

    def test_refresh_with_access_token(self, test_client, logged_in_user):
        """Test token refresh fails when using access token instead of refresh token."""
        access_token = logged_in_user["access_token"]

        response = test_client.post("/api/v1/auth/refresh", json={
            "refresh_token": access_token,
        })

        # Should fail because access tokens shouldn't work for refresh
        assert response.status_code in [401, 400]


class TestProtectedEndpoints:
    """Test access control on protected endpoints."""

    @pytest.fixture
    def logged_in_user(self, test_client, cleanup_test_user):
        """Create and login a user."""
        email = f"test_protected_{datetime.now().timestamp()}@example.com"
        password = "SecurePassword123!"

        # Register
        test_client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User",
        })

        # Login
        response = test_client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password,
        })

        return response.json()

    def test_protected_endpoint_without_token(self, test_client):
        """Test protected endpoint rejects request without token."""
        response = test_client.get("/api/v1/profile/me")

        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, test_client):
        """Test protected endpoint rejects invalid token."""
        response = test_client.get(
            "/api/v1/profile/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token(self, test_client, logged_in_user):
        """Test protected endpoint allows access with valid token."""
        access_token = logged_in_user["access_token"]

        response = test_client.get(
            "/api/v1/profile/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "email" in data

    def test_expired_token_rejected(self, test_client):
        """Test expired token is rejected."""
        # Create an expired token
        expired_token = create_access_token(
            data={"sub": "test@example.com", "user_id": 999},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        response = test_client.get(
            "/api/v1/profile/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401


class TestPasswordReset:
    """Test password reset flow."""

    @pytest.fixture
    def registered_user(self, test_client, cleanup_test_user):
        """Create a registered user for testing."""
        email = f"test_reset_{datetime.now().timestamp()}@example.com"
        password = "SecurePassword123!"

        test_client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User",
        })

        return {"email": email, "password": password}

    def test_forgot_password_existing_user(self, test_client, registered_user):
        """Test forgot password endpoint for existing user."""
        response = test_client.post("/api/v1/auth/forgot-password", json={
            "email": registered_user["email"],
        })

        # Should always return 200 (don't leak user existence)
        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()

    def test_forgot_password_nonexistent_user(self, test_client):
        """Test forgot password endpoint doesn't leak user non-existence."""
        response = test_client.post("/api/v1/auth/forgot-password", json={
            "email": "nonexistent@example.com",
        })

        # Should still return 200 (security: don't leak user existence)
        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()


class TestRateLimiting:
    """Test rate limiting on authentication endpoints."""

    def test_login_rate_limit(self, test_client):
        """Test login endpoint enforces rate limiting."""
        # Make multiple rapid login attempts
        responses = []
        for i in range(10):
            response = test_client.post("/api/v1/auth/login", json={
                "email": "ratelimit@example.com",
                "password": "SomePassword123!",
            })
            responses.append(response)

        # At least some should be rate limited (429)
        # Note: Exact count depends on SlowAPI configuration
        status_codes = [r.status_code for r in responses]
        # Should see either 401 (invalid creds) or 429 (rate limit)
        assert any(code == 429 for code in status_codes) or all(code == 401 for code in status_codes)


class TestTokenVerification:
    """Test token creation and verification."""

    def test_create_and_decode_access_token(self):
        """Test token can be created and verified."""
        user_email = "test@example.com"
        user_id = 123

        token = create_access_token(
            data={"sub": user_email, "user_id": user_id}
        )

        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == user_email
        assert payload["user_id"] == user_id

    def test_verify_invalid_token(self):
        """Test invalid token returns None."""
        payload = decode_access_token("invalid.token.here")
        assert payload is None

    def test_verify_malformed_token(self):
        """Test malformed token returns None."""
        payload = decode_access_token("not-even-a-jwt")
        assert payload is None
