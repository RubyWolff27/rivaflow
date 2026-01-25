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
        # Run migrations in order
        migrations = [
            "001_initial_schema.sql",
            "002_add_profile.sql",
        ]

        migrations_dir = Path(__file__).parent / "migrations"
        for migration in migrations:
            migration_path = migrations_dir / migration
            if migration_path.exists():
                with open(migration_path) as f:
                    conn.executescript(f.read())

        conn.commit()
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
