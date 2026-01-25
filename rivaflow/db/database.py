"""Database connection management and initialization."""
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from rivaflow.config import APP_DIR, DB_PATH


def init_db() -> None:
    """Initialize the database with schema migrations."""
    # Ensure app directory exists
    APP_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        # Create migrations tracking table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

        # Get list of already applied migrations
        cursor = conn.cursor()
        cursor.execute("SELECT migration_name FROM schema_migrations")
        applied_migrations = {row[0] for row in cursor.fetchall()}

        # Define migrations in order
        migrations = [
            "001_initial_schema.sql",
            "002_add_profile.sql",
            "003_profile_dob_and_gradings.sql",
            "004_add_professor_fields.sql",
            "005_add_name_and_location.sql",
            "006_rename_suburb_to_state.sql",
            "007_create_movements_glossary.sql",
            "008_create_contacts.sql",
            "009_create_session_rolls.sql",
            "010_add_instructor_to_sessions.sql",
            "011_add_whoop_stats.sql",
            "012_create_session_techniques.sql",
            "013_add_weight_to_readiness.sql",
            "014_add_video_urls_to_glossary.sql",
            "015_create_movement_videos.sql",
            "016_add_weekly_goals.sql",
        ]

        migrations_dir = Path(__file__).parent / "migrations"

        # Run only new migrations
        for migration in migrations:
            if migration in applied_migrations:
                print(f"[DB] Skipping already applied migration: {migration}")
                continue

            migration_path = migrations_dir / migration
            if migration_path.exists():
                print(f"[DB] Applying migration: {migration}")
                with open(migration_path) as f:
                    conn.executescript(f.read())

                # Record this migration as applied
                conn.execute(
                    "INSERT INTO schema_migrations (migration_name) VALUES (?)",
                    (migration,)
                )
                conn.commit()
                print(f"[DB] Successfully applied migration: {migration}")
            else:
                print(f"[DB] Warning: Migration file not found: {migration}")

    finally:
        conn.close()


@contextmanager
def get_connection():
    """Context manager for database connections."""
    # Auto-initialize if database doesn't exist
    if not DB_PATH.exists():
        init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_cursor(conn: sqlite3.Connection) -> sqlite3.Cursor:
    """Get a cursor from a connection."""
    return conn.cursor()
