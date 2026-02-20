"""Integration tests for authentication routes."""


class TestRegister:
    """Registration endpoint tests."""

    def test_register_success(self, client, temp_db):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "first_name": "New",
                "last_name": "User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "first_name": "Dup",
                "last_name": "User",
            },
        )
        assert response.status_code in (400, 409, 422)

    def test_register_weak_password(self, client, temp_db):
        """Test registration with weak password fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "short",
                "first_name": "Weak",
                "last_name": "Pass",
            },
        )
        assert response.status_code in (400, 422)

    def test_register_missing_fields(self, client, temp_db):
        """Test registration with missing required fields fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "missing@example.com"},
        )
        assert response.status_code == 422


class TestLogin:
    """Login endpoint tests."""

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPass123!secure"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpass"},
        )
        assert response.status_code in (401, 400)

    def test_login_nonexistent_user(self, client, temp_db):
        """Test login with nonexistent email fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "TestPass123!secure"},
        )
        assert response.status_code in (401, 400)


class TestMe:
    """Current user endpoint tests."""

    def test_get_me_authenticated(self, authenticated_client, test_user):
        """Test getting current user info."""
        response = authenticated_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_get_me_unauthenticated(self, client):
        """Test that /me requires authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestLogout:
    """Logout endpoint tests."""

    def test_logout(self, authenticated_client, test_user):
        """Test logout clears session."""
        response = authenticated_client.post("/api/v1/auth/logout")
        assert response.status_code == 200

    def test_logout_requires_auth(self, client):
        """Test logout requires authentication."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401


class TestForgotPassword:
    """Password reset flow tests."""

    def test_forgot_password_existing_email(self, client, test_user):
        """Test forgot password with existing email (should always return 200)."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 200

    def test_forgot_password_nonexistent_email(self, client, temp_db):
        """Test forgot password with unknown email (should still return 200 to not leak info)."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nobody@example.com"},
        )
        assert response.status_code == 200
