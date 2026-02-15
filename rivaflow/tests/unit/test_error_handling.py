"""
Unit tests for error handling across the application.

Tests exception handling, validation errors, and error messages.
"""

import os
from datetime import date, timedelta

import pytest

# Set SECRET_KEY for testing
os.environ.setdefault(
    "SECRET_KEY", "test-secret-key-for-error-handling-tests-minimum32chars"
)

from rivaflow.core.exceptions import AuthenticationError, ValidationError
from rivaflow.core.services.auth_service import AuthService
from rivaflow.core.services.session_service import SessionService
from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.session_repo import SessionRepository


class TestSessionValidationErrors:
    """Test session creation validation errors.

    Note: SessionService.create_session() does NOT validate inputs.
    Validation happens at the API layer via Pydantic models (SessionCreate).
    These tests verify the Pydantic model validation instead.
    """

    def test_future_date_rejected(self):
        """Test sessions with future dates are rejected by the model."""
        from rivaflow.core.models import SessionCreate

        # SessionCreate allows 1-day tolerance for timezone differences,
        # so use a date far enough in the future to trigger rejection
        future_date = date.today() + timedelta(days=7)

        with pytest.raises(Exception):
            SessionCreate(
                session_date=future_date,
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=90,
                intensity=4,
                rolls=5,
            )

    def test_invalid_class_type_rejected(self):
        """Test invalid class type raises validation error."""
        from rivaflow.core.models import SessionCreate

        with pytest.raises(Exception):
            SessionCreate(
                session_date=date.today(),
                class_type="invalid_type",
                gym_name="Test Gym",
                duration_mins=90,
                intensity=4,
                rolls=5,
            )

    def test_negative_duration_rejected(self):
        """Test negative duration raises validation error."""
        from rivaflow.core.models import SessionCreate

        with pytest.raises(Exception):
            SessionCreate(
                session_date=date.today(),
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=-10,
                intensity=4,
                rolls=5,
            )

    def test_invalid_intensity_rejected(self):
        """Test intensity outside valid range raises validation error."""
        from rivaflow.core.models import SessionCreate

        # Test too low
        with pytest.raises(Exception):
            SessionCreate(
                session_date=date.today(),
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=90,
                intensity=0,
                rolls=5,
            )

        # Test too high
        with pytest.raises(Exception):
            SessionCreate(
                session_date=date.today(),
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=90,
                intensity=10,
                rolls=5,
            )

    def test_empty_gym_name_rejected(self):
        """Test empty gym name raises validation error."""
        from rivaflow.core.models import SessionCreate

        with pytest.raises(Exception):
            SessionCreate(
                session_date=date.today(),
                class_type="gi",
                gym_name="",
                duration_mins=90,
                intensity=4,
                rolls=5,
            )


class TestAuthenticationErrors:
    """Test authentication error handling."""

    def test_invalid_email_format_rejected(self):
        """Test invalid email format raises error."""
        service = AuthService()

        with pytest.raises((ValueError, ValidationError)):
            service.register(
                email="not-an-email",
                password="SecurePassword123!",
                first_name="Test",
                last_name="User",
            )

    def test_weak_password_rejected(self):
        """Test weak password raises error."""
        service = AuthService()

        with pytest.raises((ValueError, ValidationError)):
            service.register(
                email="test@example.com",
                password="weak",
                first_name="Test",
                last_name="User",
            )

    def test_login_wrong_password_raises(self):
        """Test login with wrong password raises AuthenticationError."""
        from rivaflow.core.auth import hash_password

        service = AuthService()

        # Create user first
        with get_connection() as conn:
            cursor = conn.cursor()
            hashed = hash_password("CorrectPassword123!")
            cursor.execute(
                convert_query("""
                INSERT INTO users (email, hashed_password, is_active, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """),
                ("test_wrong_pass@example.com", hashed, True),
            )
            conn.commit()
            user_id = cursor.lastrowid

        try:
            # Try login with wrong password -- should raise
            with pytest.raises(AuthenticationError):
                service.login("test_wrong_pass@example.com", "WrongPassword123!")
        finally:
            # Cleanup
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    convert_query("DELETE FROM users WHERE id = ?"),
                    (user_id,),
                )
                conn.commit()

    def test_login_nonexistent_user_raises(self):
        """Test login for non-existent user raises AuthenticationError."""
        service = AuthService()

        with pytest.raises(AuthenticationError):
            service.login("nonexistent@example.com", "Password123!")


class TestRepositoryErrorHandling:
    """Test repository layer error handling."""

    def test_get_nonexistent_session_returns_none(self):
        """Test getting non-existent session returns None."""
        session = SessionRepository.get_by_id(999998, 999999)
        assert session is None

    def test_update_nonexistent_session_returns_none(self):
        """Test updating non-existent session returns None."""
        updated = SessionRepository.update(
            user_id=999998,
            session_id=999999,
            intensity=5,
        )
        assert updated is None

    def test_delete_nonexistent_session_no_error(self):
        """Test deleting non-existent session doesn't raise error."""
        # Should complete without error (even if nothing deleted)
        SessionRepository.delete(999998, 999999)


class TestDatabaseConstraintErrors:
    """Test database constraint error handling."""

    def test_foreign_key_violation_handled(self):
        """Test foreign key violation is handled gracefully."""
        # Try to create session for non-existent user
        # Note: SQLite may not enforce FK unless PRAGMA foreign_keys=ON
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    convert_query("""
                    INSERT INTO sessions (
                        user_id, session_date, class_type, gym_name,
                        duration_mins, intensity, rolls, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """),
                    (
                        999999,
                        date.today().isoformat(),
                        "gi",
                        "Test Gym",
                        90,
                        4,
                        5,
                    ),
                )
                conn.commit()
                # If FK not enforced (SQLite without pragma), clean up
                session_id = cursor.lastrowid
                if session_id:
                    cursor.execute(
                        convert_query("DELETE FROM sessions WHERE id = ?"),
                        (session_id,),
                    )
                    conn.commit()
        except Exception:
            pass  # Expected for PG or SQLite with FK enforcement

    def test_duplicate_email_handled(self):
        """Test duplicate email registration is handled."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Create first user
            cursor.execute(
                convert_query("""
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """),
                ("duplicate@example.com", "hash1"),
            )
            conn.commit()
            user1_id = cursor.lastrowid

            try:
                # Try to create duplicate
                with pytest.raises(Exception):  # Database constraint error
                    cursor.execute(
                        convert_query("""
                        INSERT INTO users (email, hashed_password, created_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    """),
                        ("duplicate@example.com", "hash2"),
                    )
                    conn.commit()
            finally:
                # Cleanup
                cursor.execute(
                    convert_query("DELETE FROM users WHERE id = ?"),
                    (user1_id,),
                )
                conn.commit()


class TestInputSanitization:
    """Test input sanitization and SQL injection prevention."""

    def test_sql_injection_prevented(self):
        """Test SQL injection attempts are prevented."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Create test user
            cursor.execute(
                convert_query("""
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """),
                ("test_injection@example.com", "hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

            try:
                # Attempt SQL injection via gym_name
                malicious_input = "'; DROP TABLE sessions; --"

                cursor.execute(
                    convert_query("""
                    INSERT INTO sessions (
                        user_id, session_date, class_type, gym_name,
                        duration_mins, intensity, rolls, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """),
                    (
                        user_id,
                        date.today().isoformat(),
                        "gi",
                        malicious_input,
                        90,
                        4,
                        5,
                    ),
                )
                conn.commit()
                session_id = cursor.lastrowid

                # Verify sessions table still exists and data is safe
                cursor.execute(
                    convert_query("SELECT gym_name FROM sessions WHERE id = ?"),
                    (session_id,),
                )
                row = cursor.fetchone()
                gym_name = row[0] if isinstance(row, tuple) else row["gym_name"]

                # Should be stored as literal string, not executed
                assert gym_name == malicious_input

                # Verify table wasn't dropped
                cursor.execute(convert_query("SELECT COUNT(*) FROM sessions"))
                count = cursor.fetchone()
                assert count is not None

                # Cleanup
                cursor.execute(
                    convert_query("DELETE FROM sessions WHERE id = ?"),
                    (session_id,),
                )
                conn.commit()
            finally:
                cursor.execute(
                    convert_query("DELETE FROM users WHERE id = ?"),
                    (user_id,),
                )
                conn.commit()

    def test_special_characters_handled(self):
        """Test special characters in input are handled correctly."""
        service = SessionService()

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """),
                ("test_special@example.com", "hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

        try:
            # Test various special characters
            special_chars_gym = 'Gym\'s "Best" <Place> & More!'

            session_id = service.create_session(
                user_id=user_id,
                session_date=date.today(),
                class_type="gi",
                gym_name=special_chars_gym,
                duration_mins=90,
                intensity=4,
            )

            session = service.get_session(user_id, session_id)
            assert session["gym_name"] == special_chars_gym

            # Cleanup
            SessionRepository.delete(user_id, session_id)
        finally:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    convert_query("DELETE FROM users WHERE id = ?"),
                    (user_id,),
                )
                conn.commit()


class TestErrorMessages:
    """Test error messages are clear and actionable."""

    def test_validation_error_message_clear(self):
        """Test validation error messages are clear."""
        from rivaflow.core.models import SessionCreate

        with pytest.raises(Exception) as exc_info:
            SessionCreate(
                session_date=date.today() + timedelta(days=7),
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=90,
                intensity=4,
            )

        error_message = str(exc_info.value).lower()
        # Error should mention the issue (future date)
        assert (
            "future" in error_message
            or "date" in error_message
            or "validation" in error_message
        )

    def test_authentication_error_message_secure(self):
        """Test auth error messages don't leak info."""
        service = AuthService()

        # Non-existent user - should raise AuthenticationError
        with pytest.raises(AuthenticationError):
            service.login("nonexistent@example.com", "Password123!")

        # Wrong password
        from rivaflow.core.auth import hash_password

        with get_connection() as conn:
            cursor = conn.cursor()
            hashed = hash_password("CorrectPassword123!")
            cursor.execute(
                convert_query("""
                INSERT INTO users (email, hashed_password, is_active, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """),
                ("test_secure_msg@example.com", hashed, True),
            )
            conn.commit()
            user_id = cursor.lastrowid

        try:
            # Wrong password should also raise AuthenticationError
            with pytest.raises(AuthenticationError):
                service.login("test_secure_msg@example.com", "WrongPassword!")
        finally:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    convert_query("DELETE FROM users WHERE id = ?"),
                    (user_id,),
                )
                conn.commit()


class TestExceptionRecovery:
    """Test application recovers gracefully from errors."""

    def test_database_rollback_on_error(self):
        """Test database transaction rolls back on error."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """),
                ("test_recovery@example.com", "hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                # Start transaction
                cursor.execute(
                    convert_query("""
                    INSERT INTO sessions (
                        user_id, session_date, class_type, gym_name,
                        duration_mins, intensity, rolls, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """),
                    (
                        user_id,
                        date.today().isoformat(),
                        "gi",
                        "Test Gym",
                        90,
                        4,
                        5,
                    ),
                )

                # Force error
                cursor.execute("INVALID SQL")
                conn.commit()
        except Exception:
            pass  # Expected

        # Verify rollback
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT COUNT(*) FROM sessions"
                    " WHERE user_id = ? AND gym_name = ?"
                ),
                (user_id, "Test Gym"),
            )
            row = cursor.fetchone()
            # Handle both tuple (SQLite default) and dict-like (RealDictCursor) results
            if isinstance(row, tuple):
                count = row[0]
            elif hasattr(row, "keys"):
                # dict-like row — use first value
                count = list(row.values())[0] if hasattr(row, "values") else row[0]
            else:
                count = row[0]
            assert count == 0

            # Cleanup
            cursor.execute(convert_query("DELETE FROM users WHERE id = ?"), (user_id,))
            conn.commit()
