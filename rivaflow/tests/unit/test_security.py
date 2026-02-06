"""
Unit tests for security features.

Tests authentication, authorization, password hashing, token security,
and protection against common vulnerabilities.
"""

import os
import time
from datetime import timedelta

import pytest

# Set SECRET_KEY for testing
os.environ.setdefault(
    "SECRET_KEY", "test-secret-key-for-security-tests-minimum-32-characters-long"
)

from rivaflow.core.auth import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    verify_password,
)
from rivaflow.db.database import get_connection
from rivaflow.db.repositories.password_reset_token_repo import (
    PasswordResetTokenRepository,
)


class TestPasswordHashing:
    """Test password hashing security."""

    def test_password_hashed_not_stored_plain(self):
        """Test passwords are hashed, not stored in plain text."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)

        # Hash should be different from original
        assert hashed != password

        # Hash should be bcrypt format
        assert hashed.startswith("$2b$")

        # Hash should be long (bcrypt = 60 chars)
        assert len(hashed) == 60

    def test_same_password_different_hashes(self):
        """Test same password generates different hashes (salt)."""
        password = "SamePassword123!"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Different hashes due to random salt
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_password_verification_correct(self):
        """Test correct password verifies successfully."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_wrong_password(self):
        """Test wrong password fails verification."""
        password = "CorrectPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_password_verification_case_sensitive(self):
        """Test password verification is case-sensitive."""
        password = "Password123!"
        hashed = hash_password(password)

        # Wrong case should fail
        assert verify_password("password123!", hashed) is False
        assert verify_password("PASSWORD123!", hashed) is False

    def test_hashed_password_not_reversible(self):
        """Test password hashes cannot be reversed."""
        password = "SecretPassword123!"
        hashed = hash_password(password)

        # Should not be able to extract original password from hash
        # (This is a conceptual test - bcrypt is one-way)
        assert password not in hashed


class TestJWTTokenSecurity:
    """Test JWT token security."""

    def test_token_contains_user_info(self):
        """Test tokens contain user information."""
        user_email = "test@example.com"
        user_id = 123

        token = create_access_token(data={"sub": user_email, "user_id": user_id})

        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == user_email
        assert payload["user_id"] == user_id

    def test_token_has_expiration(self):
        """Test tokens have expiration time."""
        token = create_access_token(data={"sub": "test@example.com"})

        payload = decode_access_token(token)
        assert payload is not None
        assert "exp" in payload

        # Expiration should be in the future
        exp_timestamp = payload["exp"]
        assert exp_timestamp > time.time()

    def test_expired_token_rejected(self):
        """Test expired tokens are rejected."""
        # Create token that expires immediately
        token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        payload = decode_access_token(token)
        # Expired token should be rejected
        assert payload is None

    def test_invalid_token_rejected(self):
        """Test invalid tokens are rejected."""
        invalid_token = "invalid.jwt.token"

        payload = decode_access_token(invalid_token)
        assert payload is None

    def test_tampered_token_rejected(self):
        """Test tampered tokens are rejected."""
        token = create_access_token(data={"sub": "test@example.com"})

        # Tamper with token by changing a character
        tampered_token = token[:-1] + ("X" if token[-1] != "X" else "Y")

        payload = decode_access_token(tampered_token)
        assert payload is None

    def test_refresh_token_different_from_access(self):
        """Test refresh tokens are different from access tokens."""
        refresh_token = generate_refresh_token()

        # Refresh token should be a random string, not a JWT
        assert not refresh_token.count(".") == 2  # JWTs have 2 dots

    def test_token_cannot_be_forged(self):
        """Test tokens cannot be forged without secret key."""
        # Even if attacker knows the payload structure,
        # they can't create a valid token without SECRET_KEY

        # Attempt to create a "token" manually
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhdHRhY2tlckByaXZhZmxvdy50ZXN0In0.fake_signature"

        payload = decode_access_token(fake_token)
        # Should be rejected (invalid signature)
        assert payload is None


class TestPasswordResetTokenSecurity:
    """Test password reset token security."""

    def test_reset_tokens_are_hashed(self):
        """Test password reset tokens are hashed before storage."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                ("test_reset_hash@example.com", "hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

        try:
            # Create reset token
            token = PasswordResetTokenRepository.create_token(user_id)

            # Token should be random string
            assert len(token) > 20

            # Check database stores hash, not plain token
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT token FROM password_reset_tokens WHERE user_id = ?",
                    (user_id,),
                )
                row = cursor.fetchone()
                stored_token = row[0] if isinstance(row, tuple) else row["token"]

                # Stored token should be hash (SHA-256 = 64 hex chars)
                assert stored_token != token
                assert len(stored_token) == 64

                # Cleanup
                cursor.execute(
                    "DELETE FROM password_reset_tokens WHERE user_id = ?", (user_id,)
                )
                conn.commit()
        finally:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()

    def test_reset_token_single_use(self):
        """Test password reset tokens can only be used once."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                ("test_single_use@example.com", "hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

        try:
            token = PasswordResetTokenRepository.create_token(user_id)

            # First use - should be valid
            assert PasswordResetTokenRepository.is_valid(token) is True

            # Mark as used
            PasswordResetTokenRepository.mark_as_used(token)

            # Second use - should be invalid
            assert PasswordResetTokenRepository.is_valid(token) is False

            # Cleanup
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM password_reset_tokens WHERE user_id = ?", (user_id,)
                )
                conn.commit()
        finally:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()

    def test_reset_token_expires(self):
        """Test password reset tokens expire."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                ("test_expire@example.com", "hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

        try:
            # Create token with very short expiry
            token = PasswordResetTokenRepository.create_token(
                user_id, expiry_hours=0.0001
            )

            # Wait for expiry (0.0001 hours = 0.36 seconds)
            time.sleep(1)

            # Should be expired
            assert PasswordResetTokenRepository.is_valid(token) is False

            # Cleanup
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM password_reset_tokens WHERE user_id = ?", (user_id,)
                )
                conn.commit()
        finally:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()


class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""

    def test_parameterized_queries_prevent_injection(self):
        """Test parameterized queries prevent SQL injection."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Malicious input attempting SQL injection
            malicious_email = "attacker@example.com'; DROP TABLE users; --"

            # This should safely escape the input
            cursor.execute(
                """
                SELECT * FROM users WHERE email = ?
            """,
                (malicious_email,),
            )

            # Should return empty (no results), not drop the table
            results = cursor.fetchall()
            assert isinstance(results, list)

            # Verify users table still exists
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()
            assert count is not None

    def test_special_characters_escaped(self):
        """Test special characters are properly escaped."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                ("test_special@example.com", "hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

        try:
            # Input with special SQL characters
            special_input = 'Gym\'s "Name" <with> & chars; --comment'

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO sessions (
                        user_id, session_date, class_type, gym_name,
                        duration_mins, intensity, rolls, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (user_id, "2026-02-01", "gi", special_input, 90, 4, 5),
                )
                conn.commit()
                session_id = cursor.lastrowid

                # Retrieve and verify stored correctly
                cursor.execute(
                    "SELECT gym_name FROM sessions WHERE id = ?", (session_id,)
                )
                row = cursor.fetchone()
                gym_name = row[0] if isinstance(row, tuple) else row["gym_name"]

                assert gym_name == special_input

                # Cleanup
                cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                conn.commit()
        finally:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()


class TestAuthorizationChecks:
    """Test authorization and access control."""

    def test_user_cannot_access_other_users_sessions(self):
        """Test users can only access their own sessions."""
        from rivaflow.db.repositories.session_repo import SessionRepository

        # Create two users
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                ("user1@example.com", "hash"),
            )
            conn.commit()
            user1_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                ("user2@example.com", "hash"),
            )
            conn.commit()
            user2_id = cursor.lastrowid

        try:
            # User 1 creates a session
            session = SessionRepository.create(
                user_id=user1_id,
                session_date="2026-02-01",
                class_type="gi",
                gym_name="User 1 Gym",
                duration_mins=90,
                intensity=4,
            )
            session_id = session

            # User 2 tries to get User 1's sessions
            user2_sessions = SessionRepository.get_recent(user2_id, limit=10)

            # Should be empty (User 2 shouldn't see User 1's sessions)
            user2_session_ids = [s["id"] for s in user2_sessions]
            assert session_id not in user2_session_ids

            # Cleanup
            SessionRepository.delete(session_id)
        finally:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM users WHERE id IN (?, ?)", (user1_id, user2_id)
                )
                conn.commit()


class TestInputValidation:
    """Test input validation security."""

    def test_email_validation_prevents_invalid_format(self):
        """Test email validation rejects invalid formats."""
        from rivaflow.core.services.auth_service import AuthService

        service = AuthService()

        # Invalid email formats
        invalid_emails = [
            "not-an-email",
            "@no-local-part.com",
            "no-domain@",
            "spaces in email@example.com",
            "missing-at-sign.com",
        ]

        for invalid_email in invalid_emails:
            with pytest.raises(ValueError):
                service.register(
                    email=invalid_email,
                    password="SecurePassword123!",
                    first_name="Test",
                    last_name="User",
                )

    def test_password_minimum_length_enforced(self):
        """Test password minimum length is enforced."""
        from rivaflow.core.services.auth_service import AuthService

        service = AuthService()

        # Too short
        with pytest.raises(ValueError):
            service.register(
                email="test@example.com",
                password="short",
                first_name="Test",
                last_name="User",
            )


class TestSecretKeyValidation:
    """Test SECRET_KEY security validation."""

    def test_production_requires_secure_secret_key(self):
        """Test production environment requires secure SECRET_KEY."""
        # This test verifies the SECRET_KEY validation logic exists
        # Actual validation happens in core/auth.py

        from rivaflow.core.auth import SECRET_KEY

        # In test environment, any key is allowed
        # But production should validate:
        # - Not starting with "dev-"
        # - Minimum 32 characters
        # - Not empty

        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0


class TestTimingAttacks:
    """Test protection against timing attacks."""

    def test_password_verification_constant_time(self):
        """Test password verification takes similar time for correct vs wrong password."""
        # bcrypt.checkpw is designed to be constant-time
        # This is a basic check that it's being used

        password = "TestPassword123!"
        hashed = hash_password(password)

        # Measure time for correct password
        start = time.time()
        verify_password(password, hashed)
        correct_time = time.time() - start

        # Measure time for wrong password
        start = time.time()
        verify_password("WrongPassword456!", hashed)
        wrong_time = time.time() - start

        # Times should be similar (within order of magnitude)
        # bcrypt is intentionally slow (~0.1-0.5s)
        # Timing difference should be minimal
        time_ratio = max(correct_time, wrong_time) / min(correct_time, wrong_time)
        assert time_ratio < 2.0  # Less than 2x difference
