#!/usr/bin/env python3
"""
Automatic database migration runner.
Runs pending migrations on app startup.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rivaflow.config import get_db_type
import psycopg2


def get_migration_files():
    """Get all PostgreSQL migration files in order."""
    migrations_dir = Path(__file__).parent / "migrations"

    # Get all _pg.sql files (PostgreSQL versions)
    pg_migrations = sorted(migrations_dir.glob("*_pg.sql"))

    return pg_migrations


def create_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist."""
    cursor = conn.cursor()
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
    cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
    applied = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return set(applied)


def apply_migration(conn, migration_file):
    """Apply a single migration file."""
    version = migration_file.stem  # Filename without extension

    print(f"Applying migration: {version}")

    # Read migration SQL
    with open(migration_file, 'r') as f:
        sql = f.read()

    cursor = conn.cursor()
    try:
        # Execute migration
        cursor.execute(sql)

        # Record migration
        cursor.execute(
            "INSERT INTO schema_migrations (version) VALUES (%s)",
            (version,)
        )

        conn.commit()
        print(f"✓ Applied: {version}")
        return True

    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to apply {version}: {e}")
        return False
    finally:
        cursor.close()


def run_migrations():
    """Run all pending migrations."""
    db_type = get_db_type()

    if db_type != "postgresql":
        print("Migrations only run on PostgreSQL (production).")
        print("For SQLite (local dev), migrations are not needed.")
        return

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    print("=" * 60)
    print("Running database migrations...")
    print("=" * 60)

    # Connect to database
    try:
        conn = psycopg2.connect(database_url)
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)

    # Create migrations tracking table
    create_migrations_table(conn)

    # Get applied and pending migrations
    applied = get_applied_migrations(conn)
    migration_files = get_migration_files()

    pending = [f for f in migration_files if f.stem not in applied]

    if not pending:
        print("✓ All migrations up to date!")
        conn.close()
        return

    print(f"Found {len(pending)} pending migration(s)")
    print()

    # Apply each pending migration
    success_count = 0
    for migration_file in pending:
        if apply_migration(conn, migration_file):
            success_count += 1
        else:
            print(f"\nERROR: Migration failed. Stopping.")
            conn.close()
            sys.exit(1)

    conn.close()

    print()
    print("=" * 60)
    print(f"✓ Successfully applied {success_count} migration(s)")
    print("=" * 60)


if __name__ == "__main__":
    run_migrations()
