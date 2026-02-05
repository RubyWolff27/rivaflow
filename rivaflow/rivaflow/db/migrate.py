#!/usr/bin/env python3
"""
Automatic database migration runner.
Runs pending migrations on app startup.
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2

from rivaflow.config import get_db_type

logger = logging.getLogger(__name__)


def get_migration_files():
    """Get all PostgreSQL migration files in order."""
    migrations_dir = Path(__file__).parent / "migrations"

    # Get all _pg.sql files (PostgreSQL versions)
    pg_migrations = sorted(migrations_dir.glob("*_pg.sql"))

    return pg_migrations


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
    except Exception as e:
        logger.warning(f"Error checking schema_migrations table: {e}")
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
    except Exception as e:
        logger.error(f"Error getting applied migrations: {e}")
        cursor.close()
        return set()  # Return empty set if table doesn't exist or has issues


def apply_migration(conn, migration_file):
    """Apply a single migration file."""
    version = migration_file.stem  # Filename without extension

    logger.info(f"Applying migration: {version}")

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
        logger.info(f"✓ Applied: {version}")
        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Failed to apply {version}: {e}", exc_info=True)
        return False
    finally:
        cursor.close()


def run_migrations():
    """Run all pending migrations."""
    db_type = get_db_type()

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
    except Exception as e:
        logger.error(f"ERROR: Could not connect to database: {e}", exc_info=True)
        raise RuntimeError(f"Could not connect to database: {e}") from e

    # Create migrations tracking table
    create_migrations_table(conn)

    # Get applied migrations
    applied = get_applied_migrations(conn)
    logger.info(f"Already applied: {len(applied)} migrations")

    # Use database.py's _apply_migrations which handles SQLite-to-PostgreSQL conversion
    try:
        from rivaflow.db.database import _apply_migrations

        _apply_migrations(conn, applied, "postgresql")
        logger.info("=" * 60)
        logger.info("✓ All migrations applied successfully")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        conn.close()
        raise RuntimeError(f"Database migration failed: {e}") from e
    finally:
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
