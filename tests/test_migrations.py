"""Tests for migration correctness and schema integrity."""

import pytest

from rivaflow.db.database import get_connection, convert_query, DB_TYPE


class TestMigrationCorrectness:
    """Verify all migrations applied correctly."""

    def test_schema_migrations_table_has_entries(self, temp_db):
        """Migrations tracking table should have entries after init."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT COUNT(*) AS cnt FROM schema_migrations")
            )
            row = cursor.fetchone()
            # sqlite3.Row and RealDictRow both support int index
            count = row[0]
            assert count > 0, "No migrations recorded"

    def test_core_tables_exist(self, temp_db):
        """All core tables should exist after migrations."""
        expected_tables = [
            "sessions",
            "users",
            "readiness",
            "profile",
            "techniques",
            "videos",
            "movements_glossary",
            "session_rolls",
            "session_techniques",
            "friends",
            "gradings",
            "daily_checkins",
            "streaks",
            "milestones",
            "activity_photos",
            "refresh_tokens",
            "schema_migrations",
        ]
        with get_connection() as conn:
            cursor = conn.cursor()
            for table in expected_tables:
                if DB_TYPE == "sqlite":
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table,),
                    )
                else:
                    cursor.execute(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema='public' AND table_name=%s",
                        (table,),
                    )
                row = cursor.fetchone()
                assert row is not None, f"Table '{table}' does not exist"

    def test_sessions_has_required_columns(self, temp_db):
        """Sessions table should have all expected columns."""
        expected_columns = [
            "id",
            "user_id",
            "session_date",
            "class_type",
            "gym_name",
            "duration_mins",
            "intensity",
            "rolls",
            "needs_review",
            "session_score",
            "source",
        ]
        with get_connection() as conn:
            cursor = conn.cursor()
            if DB_TYPE == "sqlite":
                cursor.execute("PRAGMA table_info(sessions)")
                columns = {
                    row[1] if isinstance(row, tuple) else row["name"]
                    for row in cursor.fetchall()
                }
            else:
                cursor.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='sessions'"
                )
                columns = {
                    row[0] if isinstance(row, tuple) else row["column_name"]
                    for row in cursor.fetchall()
                }
            for col in expected_columns:
                assert col in columns, f"Column 'sessions.{col}' missing"

    @pytest.mark.skipif(
        DB_TYPE == "sqlite",
        reason="SQLite FK enforcement disabled (stale references in schema)",
    )
    def test_fk_constraint_sessions_user(self, temp_db):
        """Inserting a session with non-existent user_id should fail."""
        with get_connection() as conn:
            cursor = conn.cursor()
            with pytest.raises(Exception):
                cursor.execute(
                    convert_query(
                        "INSERT INTO sessions (user_id, session_date, class_type, "
                        "gym_name, duration_mins, intensity, rolls) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)"
                    ),
                    (99999, "2026-01-01", "gi", "Test Gym", 60, 4, 3),
                )
                conn.commit()

    def test_check_constraint_intensity(self, temp_db, test_user):
        """Inserting a session with invalid intensity should fail."""
        with get_connection() as conn:
            cursor = conn.cursor()
            with pytest.raises(Exception):
                cursor.execute(
                    convert_query(
                        "INSERT INTO sessions (user_id, session_date, class_type, "
                        "gym_name, duration_mins, intensity, rolls) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)"
                    ),
                    (test_user["id"], "2026-01-01", "gi", "Test Gym", 60, 0, 3),
                )
                conn.commit()

    def test_users_has_lockout_columns(self, temp_db):
        """Users table should have login lockout columns from migration 093."""
        with get_connection() as conn:
            cursor = conn.cursor()
            if DB_TYPE == "sqlite":
                cursor.execute("PRAGMA table_info(users)")
                columns = {
                    row[1] if isinstance(row, tuple) else row["name"]
                    for row in cursor.fetchall()
                }
            else:
                cursor.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='users'"
                )
                columns = {
                    row[0] if isinstance(row, tuple) else row["column_name"]
                    for row in cursor.fetchall()
                }
            assert "failed_login_attempts" in columns
            assert "locked_until" in columns
