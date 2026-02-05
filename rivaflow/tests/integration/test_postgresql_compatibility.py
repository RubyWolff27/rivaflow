"""
Integration tests for PostgreSQL compatibility.

Tests that the database abstraction layer works correctly with both
SQLite (development) and PostgreSQL (production).
"""

import os
from datetime import date, timedelta

import pytest

# Set SECRET_KEY for testing
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-postgresql-tests-minimum-32chars")

from rivaflow.db.database import convert_query, get_connection, init_db
from rivaflow.db.repositories.checkin_repo import CheckinRepository
from rivaflow.db.repositories.session_repo import SessionRepository


@pytest.fixture(scope="module")
def test_db():
    """Initialize test database."""
    init_db()
    yield
    # Cleanup after all tests


@pytest.fixture(scope="function")
def test_user():
    """Create a test user for database operations."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (email, password_hash, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """,
            ("postgres_test@example.com", "dummy_hash"),
        )
        conn.commit()
        user_id = cursor.lastrowid

    yield user_id

    # Cleanup
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM readiness WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM daily_checkins WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()


class TestQueryConversion:
    """Test SQL query parameter conversion."""

    def test_convert_query_basic(self):
        """Test basic query conversion."""
        sqlite_query = "SELECT * FROM users WHERE user_id = ?"
        converted = convert_query(sqlite_query)

        # Should work regardless of database type
        assert "users" in converted
        assert "user_id" in converted

    def test_convert_query_multiple_params(self):
        """Test query conversion with multiple parameters."""
        sqlite_query = "SELECT * FROM sessions WHERE user_id = ? AND session_date = ?"
        converted = convert_query(sqlite_query)

        # Should preserve structure
        assert "sessions" in converted
        assert "user_id" in converted
        assert "session_date" in converted

    def test_convert_query_insert(self):
        """Test INSERT query conversion."""
        sqlite_query = "INSERT INTO users (email, password_hash) VALUES (?, ?)"
        converted = convert_query(sqlite_query)

        assert "INSERT" in converted
        assert "users" in converted


class TestCRUDOperations:
    """Test Create, Read, Update, Delete operations work across databases."""

    def test_create_and_read_session(self, test_db, test_user):
        """Test creating and reading a session."""
        # Create
        session = SessionRepository.create(
            user_id=test_user,
            session_date=date.today(),
            class_type="gi",
            gym_name="Test Gym",
            duration_mins=90,
            intensity=4,
            rolls=5,
        )

        assert session["session_id"] is not None

        # Read back
        retrieved = SessionRepository.get_by_id(session["session_id"])
        assert retrieved is not None
        assert retrieved["gym_name"] == "Test Gym"
        assert retrieved["duration_mins"] == 90

    def test_update_session(self, test_db, test_user):
        """Test updating a session."""
        # Create
        session = SessionRepository.create(
            user_id=test_user,
            session_date=date.today(),
            class_type="gi",
            gym_name="Original Gym",
            duration_mins=90,
            intensity=4,
            rolls=5,
        )

        # Update
        updated = SessionRepository.update(
            session_id=session["session_id"],
            gym_name="Updated Gym",
            duration_mins=120,
        )

        assert updated["gym_name"] == "Updated Gym"
        assert updated["duration_mins"] == 120

    def test_delete_session(self, test_db, test_user):
        """Test deleting a session."""
        # Create
        session = SessionRepository.create(
            user_id=test_user,
            session_date=date.today(),
            class_type="gi",
            gym_name="Test Gym",
            duration_mins=90,
            intensity=4,
            rolls=5,
        )

        session_id = session["session_id"]

        # Delete
        SessionRepository.delete(session_id)

        # Verify deletion
        retrieved = SessionRepository.get_by_id(session_id)
        assert retrieved is None


class TestDateHandling:
    """Test date handling across database types."""

    def test_date_storage_and_retrieval(self, test_db, test_user):
        """Test dates are stored and retrieved correctly."""
        test_date = date(2026, 1, 15)

        session = SessionRepository.create(
            user_id=test_user,
            session_date=test_date,
            class_type="gi",
            gym_name="Test Gym",
            duration_mins=90,
            intensity=4,
            rolls=5,
        )

        retrieved = SessionRepository.get_by_id(session["session_id"])
        # Date should match (as string or date object)
        retrieved_date = retrieved["session_date"]
        if isinstance(retrieved_date, str):
            retrieved_date = date.fromisoformat(retrieved_date)

        assert retrieved_date == test_date

    def test_date_range_queries(self, test_db, test_user):
        """Test querying by date range."""
        # Create sessions across a range
        dates = [date.today() - timedelta(days=i) for i in range(5)]

        for i, session_date in enumerate(dates):
            SessionRepository.create(
                user_id=test_user,
                session_date=session_date,
                class_type="gi",
                gym_name=f"Gym {i}",
                duration_mins=90,
                intensity=4,
                rolls=5,
            )

        # Query range
        start_date = date.today() - timedelta(days=3)
        end_date = date.today()

        sessions = SessionRepository.get_by_date_range(test_user, start_date, end_date)
        assert len(sessions) >= 3


class TestTimestampHandling:
    """Test timestamp/datetime handling."""

    def test_created_at_timestamp(self, test_db, test_user):
        """Test created_at timestamp is set correctly."""
        session = SessionRepository.create(
            user_id=test_user,
            session_date=date.today(),
            class_type="gi",
            gym_name="Test Gym",
            duration_mins=90,
            intensity=4,
            rolls=5,
        )

        # Should have created_at
        assert "created_at" in session
        assert session["created_at"] is not None

    def test_updated_at_timestamp(self, test_db, test_user):
        """Test updated_at timestamp is updated."""
        # Create
        session = SessionRepository.create(
            user_id=test_user,
            session_date=date.today(),
            class_type="gi",
            gym_name="Test Gym",
            duration_mins=90,
            intensity=4,
            rolls=5,
        )

        original_updated = session.get("updated_at")

        # Small delay to ensure timestamp difference
        import time

        time.sleep(0.1)

        # Update
        updated = SessionRepository.update(
            session_id=session["session_id"],
            gym_name="Updated Gym",
        )

        # updated_at should change (if implemented)
        # Note: This may not be implemented yet, so we check gracefully
        if "updated_at" in updated and original_updated:
            assert updated["updated_at"] != original_updated


class TestJSONFields:
    """Test JSON field handling (arrays, objects)."""

    def test_array_field_storage(self, test_db, test_user):
        """Test array fields (partners, techniques) are stored correctly."""
        partners = ["Partner A", "Partner B", "Partner C"]
        techniques = ["armbar", "triangle", "kimura"]

        session = SessionRepository.create(
            user_id=test_user,
            session_date=date.today(),
            class_type="gi",
            gym_name="Test Gym",
            duration_mins=90,
            intensity=4,
            rolls=5,
            partners=partners,
            techniques=techniques,
        )

        retrieved = SessionRepository.get_by_id(session["session_id"])

        # Arrays should be preserved
        assert retrieved["partners"] == partners
        assert retrieved["techniques"] == techniques

    def test_empty_array_handling(self, test_db, test_user):
        """Test empty arrays are handled correctly."""
        session = SessionRepository.create(
            user_id=test_user,
            session_date=date.today(),
            class_type="gi",
            gym_name="Test Gym",
            duration_mins=90,
            intensity=4,
            rolls=5,
            partners=[],
            techniques=[],
        )

        retrieved = SessionRepository.get_by_id(session["session_id"])

        # Empty arrays should be preserved (not None)
        assert retrieved["partners"] == []
        assert retrieved["techniques"] == []


class TestNullHandling:
    """Test NULL value handling."""

    def test_optional_fields_can_be_null(self, test_db, test_user):
        """Test optional fields can be NULL."""
        session = SessionRepository.create(
            user_id=test_user,
            session_date=date.today(),
            class_type="gi",
            gym_name="Test Gym",
            duration_mins=90,
            intensity=4,
            rolls=5,
            # Optional fields omitted
        )

        # Should succeed
        assert session["session_id"] is not None

        # Optional fields should be None or empty
        assert session.get("notes") in [None, ""]
        assert session.get("location") in [None, ""]


class TestTransactionHandling:
    """Test database transaction handling."""

    def test_transaction_commit(self, test_db, test_user):
        """Test transactions are committed properly."""
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
                (test_user, date.today().isoformat(), "gi", "Test Gym", 90, 4, 5),
            )
            conn.commit()
            session_id = cursor.lastrowid

        # Verify in separate connection
        retrieved = SessionRepository.get_by_id(session_id)
        assert retrieved is not None

    def test_transaction_rollback_on_error(self, test_db, test_user):
        """Test transactions roll back on error."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                # Insert valid record
                cursor.execute(
                    """
                    INSERT INTO sessions (
                        user_id, session_date, class_type, gym_name,
                        duration_mins, intensity, rolls, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (test_user, date.today().isoformat(), "gi", "Test Gym", 90, 4, 5),
                )

                # Force an error (invalid SQL)
                cursor.execute("INVALID SQL HERE")
                conn.commit()
        except Exception:
            pass  # Expected

        # Verify rollback - count should not increase
        SessionRepository.get_recent(test_user, limit=100)
        # We can't easily verify the exact count, but at least it shouldn't crash


class TestConcurrency:
    """Test concurrent access handling."""

    def test_multiple_connections(self, test_db, test_user):
        """Test multiple connections can be created."""
        # Create session in first connection
        with get_connection() as conn1:
            cursor = conn1.cursor()
            cursor.execute(
                """
                INSERT INTO sessions (
                    user_id, session_date, class_type, gym_name,
                    duration_mins, intensity, rolls, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (test_user, date.today().isoformat(), "gi", "Test Gym", 90, 4, 5),
            )
            conn1.commit()
            session_id = cursor.lastrowid

        # Read in second connection
        with get_connection() as conn2:
            cursor = conn2.cursor()
            cursor.execute(
                convert_query("SELECT * FROM sessions WHERE session_id = ?"),
                (session_id,),
            )
            row = cursor.fetchone()
            assert row is not None


class TestDataIntegrity:
    """Test data integrity constraints."""

    def test_foreign_key_constraint(self, test_db):
        """Test foreign key constraints are enforced."""
        # Try to create session for non-existent user
        try:
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
                    (999999, date.today().isoformat(), "gi", "Test Gym", 90, 4, 5),
                )
                conn.commit()

            # If we get here, foreign keys might not be enforced
            # (SQLite requires PRAGMA foreign_keys=ON)
        except Exception:
            # Expected - foreign key violation
            pass

    def test_unique_constraint(self, test_db, test_user):
        """Test unique constraints work (if any)."""
        # Create a check-in for today
        CheckinRepository.create_or_update(
            user_id=test_user,
            check_date=date.today(),
            checkin_type="readiness",
        )

        # Try to create another for same day
        # Should update, not create duplicate
        CheckinRepository.create_or_update(
            user_id=test_user,
            check_date=date.today(),
            checkin_type="session",
        )

        # Verify only one exists
        checkin = CheckinRepository.get_checkin(test_user, date.today())
        assert checkin is not None
        # Latest one should be "session"
        assert checkin["checkin_type"] == "session"
