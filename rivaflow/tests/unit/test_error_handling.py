"""
Unit tests for error handling across the application.

Tests exception handling, validation errors, and error messages.
"""
import pytest
import os
from datetime import date, timedelta

# Set SECRET_KEY for testing
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-error-handling-tests-minimum32chars")

from rivaflow.core.services.session_service import SessionService
from rivaflow.core.services.auth_service import AuthService
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.database import get_connection


class TestSessionValidationErrors:
    """Test session creation validation errors."""

    def test_future_date_rejected(self):
        """Test sessions cannot be created for future dates."""
        service = SessionService()
        future_date = date.today() + timedelta(days=1)

        with pytest.raises(ValueError) as exc_info:
            service.create_session(
                user_id=1,
                session_date=future_date,
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=90,
                intensity=4,
            )

        assert "future" in str(exc_info.value).lower()

    def test_invalid_class_type_rejected(self):
        """Test invalid class type raises error."""
        service = SessionService()

        with pytest.raises(ValueError) as exc_info:
            service.create_session(
                user_id=1,
                session_date=date.today(),
                class_type="invalid_type",
                gym_name="Test Gym",
                duration_mins=90,
                intensity=4,
            )

        assert "class_type" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_negative_duration_rejected(self):
        """Test negative duration raises error."""
        service = SessionService()

        with pytest.raises(ValueError) as exc_info:
            service.create_session(
                user_id=1,
                session_date=date.today(),
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=-10,
                intensity=4,
            )

        assert "duration" in str(exc_info.value).lower() or "positive" in str(exc_info.value).lower()

    def test_invalid_intensity_rejected(self):
        """Test intensity outside 1-5 range raises error."""
        service = SessionService()

        # Test too low
        with pytest.raises(ValueError):
            service.create_session(
                user_id=1,
                session_date=date.today(),
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=90,
                intensity=0,
            )

        # Test too high
        with pytest.raises(ValueError):
            service.create_session(
                user_id=1,
                session_date=date.today(),
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=90,
                intensity=10,
            )

    def test_empty_gym_name_rejected(self):
        """Test empty gym name raises error."""
        service = SessionService()

        with pytest.raises(ValueError) as exc_info:
            service.create_session(
                user_id=1,
                session_date=date.today(),
                class_type="gi",
                gym_name="",
                duration_mins=90,
                intensity=4,
            )

        assert "gym" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()


class TestAuthenticationErrors:
    """Test authentication error handling."""

    def test_invalid_email_format_rejected(self):
        """Test invalid email format raises error."""
        service = AuthService()

        with pytest.raises(ValueError) as exc_info:
            service.register(
                email="not-an-email",
                password="SecurePassword123!",
                first_name="Test",
                last_name="User",
            )

        assert "email" in str(exc_info.value).lower()

    def test_weak_password_rejected(self):
        """Test weak password raises error."""
        service = AuthService()

        with pytest.raises(ValueError) as exc_info:
            service.register(
                email="test@example.com",
                password="weak",
                first_name="Test",
                last_name="User",
            )

        assert "password" in str(exc_info.value).lower()

    def test_login_wrong_password_returns_none(self):
        """Test login with wrong password returns None."""
        service = AuthService()

        # Create user first
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (email, password_hash, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, ("test_wrong_pass@rivaflow.test", "dummy_hash"))
            conn.commit()
            user_id = cursor.lastrowid

        try:
            # Try login with wrong password
            result = service.login("test_wrong_pass@rivaflow.test", "WrongPassword123!")
            assert result is None
        finally:
            # Cleanup
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                conn.commit()

    def test_login_nonexistent_user_returns_none(self):
        """Test login for non-existent user returns None."""
        service = AuthService()

        result = service.login("nonexistent@rivaflow.test", "Password123!")
        assert result is None


class TestRepositoryErrorHandling:
    """Test repository layer error handling."""

    def test_get_nonexistent_session_returns_none(self):
        """Test getting non-existent session returns None."""
        session = SessionRepository.get_by_id(999999)
        assert session is None

    def test_update_nonexistent_session_returns_none(self):
        """Test updating non-existent session returns None."""
        updated = SessionRepository.update(
            session_id=999999,
            intensity=5,
        )
        assert updated is None

    def test_delete_nonexistent_session_no_error(self):
        """Test deleting non-existent session doesn't raise error."""
        # Should complete without error (even if nothing deleted)
        SessionRepository.delete(999999)


class TestDatabaseConstraintErrors:
    """Test database constraint error handling."""

    def test_foreign_key_violation_handled(self):
        """Test foreign key violation is handled gracefully."""
        # Try to create session for non-existent user
        with pytest.raises(Exception):  # Database error expected
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (
                        user_id, session_date, class_type, gym_name,
                        duration_mins, intensity, rolls, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (999999, date.today().isoformat(), "gi", "Test Gym", 90, 4, 5))
                conn.commit()

    def test_duplicate_email_handled(self):
        """Test duplicate email registration is handled."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Create first user
            cursor.execute("""
                INSERT INTO users (email, password_hash, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, ("duplicate@rivaflow.test", "hash1"))
            conn.commit()
            user1_id = cursor.lastrowid

            try:
                # Try to create duplicate
                with pytest.raises(Exception):  # Database constraint error
                    cursor.execute("""
                        INSERT INTO users (email, password_hash, created_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    """, ("duplicate@rivaflow.test", "hash2"))
                    conn.commit()
            finally:
                # Cleanup
                cursor.execute("DELETE FROM users WHERE user_id = ?", (user1_id,))
                conn.commit()


class TestInputSanitization:
    """Test input sanitization and SQL injection prevention."""

    def test_sql_injection_prevented(self):
        """Test SQL injection attempts are prevented."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Create test user
            cursor.execute("""
                INSERT INTO users (email, password_hash, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, ("test_injection@rivaflow.test", "hash"))
            conn.commit()
            user_id = cursor.lastrowid

            try:
                # Attempt SQL injection via gym_name
                malicious_input = "'; DROP TABLE sessions; --"

                cursor.execute("""
                    INSERT INTO sessions (
                        user_id, session_date, class_type, gym_name,
                        duration_mins, intensity, rolls, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, date.today().isoformat(), "gi", malicious_input, 90, 4, 5))
                conn.commit()
                session_id = cursor.lastrowid

                # Verify sessions table still exists and data is safe
                cursor.execute("SELECT gym_name FROM sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                gym_name = row[0] if isinstance(row, tuple) else row["gym_name"]

                # Should be stored as literal string, not executed
                assert gym_name == malicious_input

                # Verify table wasn't dropped
                cursor.execute("SELECT COUNT(*) FROM sessions")
                count = cursor.fetchone()
                assert count is not None

                # Cleanup
                cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
            finally:
                cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                conn.commit()

    def test_special_characters_handled(self):
        """Test special characters in input are handled correctly."""
        service = SessionService()

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (email, password_hash, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, ("test_special@rivaflow.test", "hash"))
            conn.commit()
            user_id = cursor.lastrowid

        try:
            # Test various special characters
            special_chars_gym = "Gym's \"Best\" <Place> & More!"

            session = service.create_session(
                user_id=user_id,
                session_date=date.today(),
                class_type="gi",
                gym_name=special_chars_gym,
                duration_mins=90,
                intensity=4,
            )

            assert session["gym_name"] == special_chars_gym

            # Cleanup
            SessionRepository.delete(session["session_id"])
        finally:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                conn.commit()


class TestErrorMessages:
    """Test error messages are clear and actionable."""

    def test_validation_error_message_clear(self):
        """Test validation error messages are clear."""
        service = SessionService()

        with pytest.raises(ValueError) as exc_info:
            service.create_session(
                user_id=1,
                session_date=date.today() + timedelta(days=1),
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=90,
                intensity=4,
            )

        error_message = str(exc_info.value).lower()
        # Error should mention the issue
        assert "future" in error_message or "date" in error_message

    def test_authentication_error_message_secure(self):
        """Test auth error messages don't leak info."""
        service = AuthService()

        # Non-existent user
        result1 = service.login("nonexistent@rivaflow.test", "Password123!")

        # Wrong password
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (email, password_hash, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, ("test_secure_msg@rivaflow.test", "hash"))
            conn.commit()
            user_id = cursor.lastrowid

        try:
            result2 = service.login("test_secure_msg@rivaflow.test", "WrongPassword!")

            # Both should return None (don't leak which failed)
            assert result1 is None
            assert result2 is None
        finally:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                conn.commit()


class TestExceptionRecovery:
    """Test application recovers gracefully from errors."""

    def test_database_rollback_on_error(self):
        """Test database transaction rolls back on error."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (email, password_hash, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, ("test_recovery@rivaflow.test", "hash"))
            conn.commit()
            user_id = cursor.lastrowid

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                # Start transaction
                cursor.execute("""
                    INSERT INTO sessions (
                        user_id, session_date, class_type, gym_name,
                        duration_mins, intensity, rolls, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, date.today().isoformat(), "gi", "Test Gym", 90, 4, 5))

                # Force error
                cursor.execute("INVALID SQL")
                conn.commit()
        except Exception:
            pass  # Expected

        # Verify rollback
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM sessions WHERE user_id = ? AND gym_name = ?",
                (user_id, "Test Gym")
            )
            count = cursor.fetchone()[0]
            assert count == 0

            # Cleanup
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
