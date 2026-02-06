"""
Unit tests for database abstraction layer.

Tests the SQLite/PostgreSQL compatibility layer and query conversion.
"""

import os

# Set SECRET_KEY for testing
os.environ.setdefault(
    "SECRET_KEY", "test-secret-key-for-db-abstraction-tests-min32chars"
)

from rivaflow.db.database import convert_query


class TestQueryConversion:
    """Test SQL query parameter conversion."""

    def test_convert_query_preserves_single_param(self):
        """Test single parameter marker is preserved."""
        sqlite_query = "SELECT * FROM users WHERE user_id = ?"
        converted = convert_query(sqlite_query)

        # Should preserve the query structure
        assert "users" in converted
        assert "user_id" in converted
        # Parameter marker should be preserved (? or $1 depending on DB)
        assert ("?" in converted) or ("$1" in converted)

    def test_convert_query_handles_multiple_params(self):
        """Test multiple parameter markers."""
        sqlite_query = "SELECT * FROM sessions WHERE user_id = ? AND session_date = ? AND class_type = ?"
        converted = convert_query(sqlite_query)

        assert "sessions" in converted
        assert "user_id" in converted
        assert "session_date" in converted
        assert "class_type" in converted

    def test_convert_query_handles_insert(self):
        """Test INSERT query conversion."""
        sqlite_query = "INSERT INTO users (email, hashed_password) VALUES (?, ?)"
        converted = convert_query(sqlite_query)

        assert "INSERT" in converted.upper()
        assert "users" in converted
        assert "email" in converted
        assert "hashed_password" in converted

    def test_convert_query_handles_update(self):
        """Test UPDATE query conversion."""
        sqlite_query = (
            "UPDATE sessions SET intensity = ?, notes = ? WHERE session_id = ?"
        )
        converted = convert_query(sqlite_query)

        assert "UPDATE" in converted.upper()
        assert "sessions" in converted
        assert "intensity" in converted
        assert "WHERE" in converted.upper()

    def test_convert_query_handles_delete(self):
        """Test DELETE query conversion."""
        sqlite_query = "DELETE FROM sessions WHERE session_id = ?"
        converted = convert_query(sqlite_query)

        assert "DELETE" in converted.upper()
        assert "sessions" in converted

    def test_convert_query_handles_join(self):
        """Test JOIN query conversion."""
        sqlite_query = """
        SELECT s.*, p.first_name
        FROM sessions s
        JOIN profile p ON s.user_id = p.user_id
        WHERE s.session_id = ?
        """
        converted = convert_query(sqlite_query)

        assert "JOIN" in converted.upper()
        assert "sessions" in converted
        assert "profile" in converted

    def test_convert_query_handles_subquery(self):
        """Test subquery conversion."""
        sqlite_query = """
        SELECT * FROM sessions
        WHERE user_id IN (
            SELECT user_id FROM users WHERE email = ?
        )
        """
        converted = convert_query(sqlite_query)

        assert "SELECT" in converted.upper()
        assert "sessions" in converted
        assert "users" in converted

    def test_convert_query_preserves_current_timestamp(self):
        """Test CURRENT_TIMESTAMP is preserved."""
        sqlite_query = (
            "INSERT INTO sessions (user_id, created_at) VALUES (?, CURRENT_TIMESTAMP)"
        )
        converted = convert_query(sqlite_query)

        assert "CURRENT_TIMESTAMP" in converted.upper()

    def test_convert_query_handles_count(self):
        """Test COUNT(*) queries."""
        sqlite_query = "SELECT COUNT(*) FROM sessions WHERE user_id = ?"
        converted = convert_query(sqlite_query)

        assert "COUNT" in converted.upper()
        assert "sessions" in converted

    def test_convert_query_handles_aggregate(self):
        """Test aggregate function queries."""
        sqlite_query = (
            "SELECT SUM(duration_mins), AVG(intensity) FROM sessions WHERE user_id = ?"
        )
        converted = convert_query(sqlite_query)

        assert "SUM" in converted.upper()
        assert "AVG" in converted.upper()
        assert "duration_mins" in converted
        assert "intensity" in converted


class TestDatabaseConnectionRetry:
    """Test database connection retry logic."""

    def test_connection_retry_on_failure(self):
        """Test connection retries on transient failures."""
        from rivaflow.db.database import get_connection

        # Should succeed (or raise if database truly unavailable)
        with get_connection() as conn:
            assert conn is not None


class TestRowToDictConversion:
    """Test row-to-dict conversion handles both SQLite and PostgreSQL."""

    def test_dict_conversion_preserves_all_fields(self):
        """Test all fields are preserved in dict conversion."""
        from datetime import date

        from rivaflow.db.database import get_connection

        # Create a test session
        with get_connection() as conn:
            cursor = conn.cursor()

            # First create a test user
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                ("test_dict@example.com", "dummy_hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

            # Create a session
            cursor.execute(
                """
                INSERT INTO sessions (
                    user_id, session_date, class_type, gym_name,
                    duration_mins, intensity, rolls, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (user_id, date.today().isoformat(), "gi", "Test Gym", 90, 4, 5),
            )
            conn.commit()
            session_id = cursor.lastrowid

            # Retrieve and convert to dict
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()

            # Convert to dict
            row_dict = dict(row)

            # Verify fields present
            assert "session_id" in row_dict
            assert "user_id" in row_dict
            assert "class_type" in row_dict
            assert "gym_name" in row_dict
            assert "duration_mins" in row_dict

            # Cleanup
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()


class TestParameterBinding:
    """Test parameter binding works correctly."""

    def test_parameter_binding_prevents_injection(self):
        """Test parameterized queries prevent SQL injection."""
        from rivaflow.db.database import get_connection

        # Attempt SQL injection via parameter
        malicious_input = "'; DROP TABLE sessions; --"

        with get_connection() as conn:
            cursor = conn.cursor()

            # This should safely escape the input
            cursor.execute(
                "SELECT * FROM sessions WHERE gym_name = ?", (malicious_input,)
            )

            # Should return empty results, not execute injection
            results = cursor.fetchall()
            assert isinstance(results, list)

            # Verify sessions table still exists
            cursor.execute("SELECT COUNT(*) FROM sessions")
            count = cursor.fetchone()
            assert count is not None


class TestTransactionIsolation:
    """Test transaction isolation and rollback."""

    def test_transaction_rollback_on_exception(self):
        """Test transactions rollback on exception."""
        from rivaflow.db.database import get_connection

        user_id = None

        # Create test user
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                ("test_rollback@example.com", "dummy_hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                # Insert a session
                cursor.execute(
                    """
                    INSERT INTO sessions (
                        user_id, session_date, class_type, gym_name,
                        duration_mins, intensity, rolls, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (user_id, "2026-02-01", "gi", "Test Gym", 90, 4, 5),
                )

                # Force an error (invalid SQL)
                cursor.execute("INVALID SQL SYNTAX HERE")

                conn.commit()
        except Exception:
            pass  # Expected

        # Verify rollback - session should not exist
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM sessions WHERE user_id = ? AND gym_name = ?",
                (user_id, "Test Gym"),
            )
            count = cursor.fetchone()[0]
            assert count == 0

            # Cleanup
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()

    def test_explicit_rollback(self):
        """Test explicit transaction rollback."""
        from rivaflow.db.database import get_connection

        user_id = None

        # Create test user
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                ("test_explicit_rollback@example.com", "dummy_hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

        # Start transaction and rollback
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
                (user_id, "2026-02-01", "gi", "Rollback Gym", 90, 4, 5),
            )

            # Explicit rollback
            conn.rollback()

        # Verify rollback
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM sessions WHERE user_id = ? AND gym_name = ?",
                (user_id, "Rollback Gym"),
            )
            count = cursor.fetchone()[0]
            assert count == 0

            # Cleanup
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()


class TestDatabaseTypes:
    """Test database handles different data types correctly."""

    def test_integer_storage_and_retrieval(self):
        """Test integer values are stored and retrieved correctly."""
        from rivaflow.db.database import get_connection

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                ("test_int@example.com", "hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

            # Verify integer type
            assert isinstance(user_id, int)
            assert user_id > 0

            # Cleanup
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()

    def test_string_storage_and_retrieval(self):
        """Test string values are stored and retrieved correctly."""
        from rivaflow.db.database import get_connection

        test_string = "Test Gym Name with Special Ch@rs!"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                ("test_string@example.com", "hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO sessions (
                    user_id, session_date, class_type, gym_name,
                    duration_mins, intensity, rolls, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (user_id, "2026-02-01", "gi", test_string, 90, 4, 5),
            )
            conn.commit()
            session_id = cursor.lastrowid

            # Retrieve
            cursor.execute(
                "SELECT gym_name FROM sessions WHERE session_id = ?", (session_id,)
            )
            row = cursor.fetchone()
            retrieved_string = row[0] if isinstance(row, tuple) else row["gym_name"]

            assert retrieved_string == test_string

            # Cleanup
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()

    def test_null_value_handling(self):
        """Test NULL values are handled correctly."""
        from rivaflow.db.database import get_connection

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                ("test_null@example.com", "hash"),
            )
            conn.commit()
            user_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO sessions (
                    user_id, session_date, class_type, gym_name,
                    duration_mins, intensity, rolls, notes, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (user_id, "2026-02-01", "gi", "Test Gym", 90, 4, 5, None),
            )
            conn.commit()
            session_id = cursor.lastrowid

            # Retrieve
            cursor.execute(
                "SELECT notes FROM sessions WHERE session_id = ?", (session_id,)
            )
            row = cursor.fetchone()
            notes = row[0] if isinstance(row, tuple) else row["notes"]

            assert notes is None

            # Cleanup
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
