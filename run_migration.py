#!/usr/bin/env python3
"""
Run a specific migration on the production database.
Usage: python run_migration.py <migration_file>
"""
import sys
import os
import psycopg2

def run_migration(migration_file: str):
    """Run a migration file on the production database."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Read migration file
    if not os.path.exists(migration_file):
        print(f"ERROR: Migration file not found: {migration_file}")
        sys.exit(1)

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    print(f"Running migration: {migration_file}")
    print("=" * 60)

    # Connect to database and run migration
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Execute migration
        cursor.execute(migration_sql)
        conn.commit()

        print("✓ Migration completed successfully!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_migration.py <migration_file>")
        print("Example: python run_migration.py rivaflow/db/migrations/041_create_notifications_pg.sql")
        sys.exit(1)

    run_migration(sys.argv[1])
