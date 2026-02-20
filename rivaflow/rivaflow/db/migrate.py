#!/usr/bin/env python3
"""
Automatic database migration runner.
Runs pending migrations on app startup.
"""

import hashlib
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2

from rivaflow.core.settings import settings

logger = logging.getLogger(__name__)

# Advisory lock key for PostgreSQL (stable hash of "rivaflow_migrations")
_PG_LOCK_KEY = int(hashlib.md5(b"rivaflow_migrations").hexdigest()[:15], 16) % (2**31)


def _ensure_critical_columns(conn):
    """Ensure critical columns exist, bypassing migration tracking.

    This handles cases where a migration was recorded as applied
    but the schema change never actually took effect.
    """
    checks = [
        ("profile", "timezone", "TEXT DEFAULT 'UTC'"),
        ("users", "failed_login_attempts", "INTEGER DEFAULT 0"),
        ("users", "locked_until", "TIMESTAMP"),
    ]
    # Whitelist of allowed table/column names to prevent SQL injection
    allowed_tables = {"profile", "sessions", "users"}
    allowed_columns = {
        "timezone",
        "session_score",
        "score_breakdown",
        "score_version",
        "failed_login_attempts",
        "locked_until",
    }

    cursor = conn.cursor()
    for table, column, col_def in checks:
        if table not in allowed_tables or column not in allowed_columns:
            logger.error(
                f"Skipping unknown table/column: {table}.{column} "
                f"— add to whitelist if intentional"
            )
            continue
        try:
            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = %s AND column_name = %s",
                (table, column),
            )
            if cursor.fetchone() is None:
                logger.warning("Column %s.%s missing — adding it now", table, column)
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
                conn.commit()
                logger.info("Added missing column %s.%s", table, column)
            else:
                logger.info("Column %s.%s exists — OK", table, column)
        except psycopg2.Error as e:
            logger.error("Failed to ensure %s.%s: %s", table, column, e)
            conn.rollback()

    # Ensure needs_review is BOOLEAN (migrations 089/090 failed due to
    # semicolon splitting and ::boolean cast issues)
    try:
        cursor.execute(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = 'sessions' AND column_name = 'needs_review'"
        )
        row = cursor.fetchone()
        if row and row[0] != "boolean":
            logger.warning("sessions.needs_review is %s, converting to BOOLEAN", row[0])
            # Must drop default before type change, then re-add
            cursor.execute(
                "ALTER TABLE sessions ALTER COLUMN needs_review DROP DEFAULT"
            )
            cursor.execute(
                "ALTER TABLE sessions ALTER COLUMN needs_review "
                "TYPE BOOLEAN USING CASE WHEN needs_review = 0 "
                "THEN FALSE WHEN needs_review IS NULL THEN NULL "
                "ELSE TRUE END"
            )
            cursor.execute(
                "ALTER TABLE sessions ALTER COLUMN needs_review " "SET DEFAULT FALSE"
            )
            conn.commit()
            logger.info("Converted sessions.needs_review to BOOLEAN")
        else:
            logger.info("sessions.needs_review is BOOLEAN — OK")
    except psycopg2.Error as e:
        logger.error("Failed to fix needs_review type: %s", e)
        conn.rollback()

    cursor.close()


def create_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist."""
    cursor = conn.cursor()

    # Check if table exists and has correct schema
    try:
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'schema_migrations' AND column_name = 'version'
        """)
        has_version_column = cursor.fetchone() is not None

        if not has_version_column:
            # Table exists but has wrong schema - drop and recreate
            logger.warning(
                "schema_migrations table exists with incorrect schema. Recreating..."
            )
            cursor.execute("DROP TABLE IF EXISTS schema_migrations")
            conn.commit()
    except psycopg2.Error as e:
        logger.warning("Error checking schema_migrations table: %s", e)
        conn.rollback()

    # Create table with correct schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()


def get_applied_migrations(conn):
    """Get list of already applied migrations."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        applied = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return set(applied)
    except psycopg2.Error as e:
        logger.error("Error getting applied migrations: %s", e)
        cursor.close()
        return set()  # Return empty set if table doesn't exist or has issues


def apply_migration(conn, migration_file):
    """Apply a single migration file."""
    version = migration_file.stem  # Filename without extension

    logger.info("Applying migration: %s", version)

    # Read migration SQL
    with open(migration_file) as f:
        sql = f.read()

    cursor = conn.cursor()
    try:
        # Execute migration
        cursor.execute(sql)

        # Record migration
        cursor.execute(
            "INSERT INTO schema_migrations (version) VALUES (%s)", (version,)
        )

        conn.commit()
        logger.info("✓ Applied: %s", version)
        return True

    except psycopg2.Error as e:
        conn.rollback()
        logger.error("✗ Failed to apply %s: %s", version, e, exc_info=True)
        return False
    finally:
        cursor.close()


def run_migrations():
    """Run all pending migrations."""
    db_type = settings.DB_TYPE

    if db_type != "postgresql":
        logger.info("Migrations only run on PostgreSQL (production).")
        logger.info("For SQLite (local dev), migrations are handled by database.py")
        return

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("ERROR: DATABASE_URL not set")
        raise RuntimeError("DATABASE_URL environment variable is not set")

    logger.info("=" * 60)
    logger.info("Running database migrations...")
    logger.info("=" * 60)

    # Connect to database
    try:
        conn = psycopg2.connect(database_url)
    except psycopg2.Error as e:
        logger.error("ERROR: Could not connect to database: %s", e, exc_info=True)
        raise RuntimeError(f"Could not connect to database: {e}") from e

    # Acquire advisory lock to prevent concurrent migrations
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT pg_try_advisory_lock(%s)", (_PG_LOCK_KEY,))
        acquired = cursor.fetchone()[0]
        cursor.close()

        if not acquired:
            logger.info("Another process is running migrations, skipping.")
            conn.close()
            return

        logger.info("Acquired migration advisory lock")
    except psycopg2.Error as e:
        logger.warning("Could not acquire advisory lock, proceeding anyway: %s", e)

    try:
        # Create migrations tracking table
        create_migrations_table(conn)

        # Ensure critical columns exist (bypass migration tracking)
        _ensure_critical_columns(conn)

        # Get applied migrations
        applied = get_applied_migrations(conn)
        logger.info("Already applied: %s migrations", len(applied))

        # Use database.py's _apply_migrations which handles SQLite-to-PG conversion
        from rivaflow.db.database import _apply_migrations

        _apply_migrations(conn, applied, "postgresql")
        logger.info("=" * 60)
        logger.info("✓ All migrations applied successfully")
        logger.info("=" * 60)
    except (psycopg2.Error, RuntimeError) as e:
        logger.error("Migration failed: %s", e, exc_info=True)
        raise RuntimeError(f"Database migration failed: {e}") from e
    finally:
        # Release advisory lock
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT pg_advisory_unlock(%s)", (_PG_LOCK_KEY,))
            cursor.close()
            logger.info("Released migration advisory lock")
        except psycopg2.Error:
            pass
        conn.close()

    # Reset connection pool after migrations to ensure clean state
    from rivaflow.db.database import close_connection_pool

    close_connection_pool()
    logger.info("Connection pool reset after migrations")


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    run_migrations()
