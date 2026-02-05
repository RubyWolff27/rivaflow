"""Reset failed migrations in production database.

Run this ONCE on Render to clear the migration state for migrations that
failed partway through but got marked as "applied".

Usage on Render:
    python reset_failed_migrations.py
"""

import os
import sys

# Add project to path
sys.path.insert(0, "/opt/render/project/src")

from rivaflow.db.database import get_connection, get_db_type


def reset_migrations():
    """Remove failed migrations from schema_migrations table."""

    # Migrations that need to be reset (they failed but got marked as applied)
    failed_migrations = [
        "030_fix_goal_progress_unique_constraint.sql",
        "031_fix_readiness_unique_constraint.sql",
        "032_fix_friends_unique_constraint.sql",
        "034_fix_movements_glossary_custom.sql",
    ]

    print("=" * 60)
    print("RESETTING FAILED MIGRATIONS")
    print("=" * 60)
    print(f"Database type: {get_db_type()}")
    print()

    with get_connection() as conn:
        cursor = conn.cursor()

        for migration in failed_migrations:
            # Check if migration is marked as applied
            cursor.execute(
                "SELECT migration_name FROM schema_migrations WHERE migration_name = %s",
                (migration,),
            )
            result = cursor.fetchone()

            if result:
                print(f"✓ Found {migration} - removing from applied list")
                cursor.execute(
                    "DELETE FROM schema_migrations WHERE migration_name = %s",
                    (migration,),
                )
                conn.commit()
            else:
                print(f"  {migration} - not in applied list (OK)")

        print()
        print("=" * 60)
        print("MIGRATION RESET COMPLETE")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Restart the web service on Render")
        print("2. Migrations will run again on startup")
        print("3. Check logs to confirm they complete successfully")
        print()


if __name__ == "__main__":
    try:
        reset_migrations()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
