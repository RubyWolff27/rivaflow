"""Database connection management and initialization."""
import sqlite3
from pathlib import Path
from typing import Optional, Union
from contextlib import contextmanager

from rivaflow.config import APP_DIR, DB_PATH, DATABASE_URL, DB_TYPE

# Import PostgreSQL adapter if available
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


def init_db() -> None:
    """Initialize the database with schema migrations."""
    if DB_TYPE == "sqlite":
        _init_sqlite_db()
    elif DB_TYPE == "postgresql":
        _init_postgresql_db()
    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")


def _init_sqlite_db() -> None:
    """Initialize SQLite database with migrations."""
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

        _apply_migrations(conn, applied_migrations, "sqlite")

    finally:
        conn.close()


def _init_postgresql_db() -> None:
    """Initialize PostgreSQL database with migrations."""
    if not PSYCOPG2_AVAILABLE:
        raise ImportError("psycopg2 is required for PostgreSQL support. Install with: pip install psycopg2-binary")

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required for PostgreSQL")

    conn = psycopg2.connect(DATABASE_URL)
    try:
        cursor = conn.cursor()

        # Create migrations tracking table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_name TEXT PRIMARY KEY,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # Get list of already applied migrations
        cursor.execute("SELECT migration_name FROM schema_migrations")
        applied_migrations = {row[0] for row in cursor.fetchall()}

        _apply_migrations(conn, applied_migrations, "postgresql")

        # Reset sequences for tables with SERIAL primary keys
        _reset_postgresql_sequences(conn)

    finally:
        conn.close()


def _reset_postgresql_sequences(conn) -> None:
    """Reset PostgreSQL sequences for tables with SERIAL primary keys."""
    cursor = conn.cursor()

    # Get all tables with SERIAL columns
    tables_with_serials = [
        'users', 'profile', 'sessions', 'readiness', 'techniques', 'videos',
        'gradings', 'movements', 'contacts', 'movement_videos', 'session_rolls',
        'session_techniques', 'weekly_goal_progress', 'daily_checkins',
        'milestones', 'streaks', 'activity_photos', 'user_relationships',
        'activity_likes', 'activity_comments', 'refresh_tokens'
    ]

    for table in tables_with_serials:
        try:
            # Reset sequence to max(id) + 1
            cursor.execute(f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {table}), 0) + 1,
                    false
                )
            """)
            print(f"[DB] Reset sequence for table: {table}")
        except Exception as e:
            # Table might not exist or not have a sequence, skip
            print(f"[DB] Skipping sequence reset for {table}: {e}")

    conn.commit()


def _convert_sqlite_to_postgresql(sql: str) -> str:
    """Convert SQLite SQL syntax to PostgreSQL syntax."""
    import re

    # Replace AUTOINCREMENT with SERIAL (handle various whitespace)
    sql = re.sub(
        r'\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b',
        'SERIAL PRIMARY KEY',
        sql,
        flags=re.IGNORECASE
    )

    # Replace INSERT OR IGNORE with INSERT ... ON CONFLICT DO NOTHING
    sql = re.sub(
        r'\bINSERT\s+OR\s+IGNORE\s+INTO\b',
        'INSERT INTO',
        sql,
        flags=re.IGNORECASE
    )
    # Add ON CONFLICT DO NOTHING at the end of INSERT statements that were INSERT OR IGNORE
    # This is a bit tricky - we need to add it before the semicolon or end of statement
    # For now, we'll handle simple cases: INSERT INTO table (...) VALUES (...)
    sql = re.sub(
        r'(\bINSERT\s+INTO\s+\w+\s*\([^)]+\)\s*VALUES\s*\([^)]+\))(?=\s*;|\s*$)',
        r'\1 ON CONFLICT DO NOTHING',
        sql,
        flags=re.IGNORECASE
    )

    # Replace datetime('now') with CURRENT_TIMESTAMP
    sql = re.sub(
        r"datetime\s*\(\s*['\"]now['\"]\s*\)",
        'CURRENT_TIMESTAMP',
        sql,
        flags=re.IGNORECASE
    )

    # Replace TEXT columns with datetime defaults to TIMESTAMP
    sql = re.sub(
        r"TEXT\s+NOT\s+NULL\s+DEFAULT\s+\(\s*datetime\s*\(\s*['\"]now['\"]\s*\)\s*\)",
        'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP',
        sql,
        flags=re.IGNORECASE
    )

    # Replace standalone datetime('now') in DEFAULT clauses
    sql = re.sub(
        r"DEFAULT\s+\(\s*datetime\s*\(\s*['\"]now['\"]\s*\)\s*\)",
        'DEFAULT CURRENT_TIMESTAMP',
        sql,
        flags=re.IGNORECASE
    )

    # Replace BOOLEAN DEFAULT 1/0 with TRUE/FALSE (handles NOT NULL case too)
    sql = re.sub(
        r'\bBOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+1\b',
        'BOOLEAN NOT NULL DEFAULT TRUE',
        sql,
        flags=re.IGNORECASE
    )
    sql = re.sub(
        r'\bBOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+0\b',
        'BOOLEAN NOT NULL DEFAULT FALSE',
        sql,
        flags=re.IGNORECASE
    )
    sql = re.sub(
        r'\bBOOLEAN\s+DEFAULT\s+1\b',
        'BOOLEAN DEFAULT TRUE',
        sql,
        flags=re.IGNORECASE
    )
    sql = re.sub(
        r'\bBOOLEAN\s+DEFAULT\s+0\b',
        'BOOLEAN DEFAULT FALSE',
        sql,
        flags=re.IGNORECASE
    )

    # Replace integer literals used as boolean values in SELECT/INSERT
    # Pattern: "1 as column_name" where column_name suggests boolean (is_*, has_*, etc)
    sql = re.sub(
        r'\b1\s+as\s+(is_\w+|has_\w+|show_\w+|enable_\w+)\b',
        r'TRUE as \1',
        sql,
        flags=re.IGNORECASE
    )
    sql = re.sub(
        r'\b0\s+as\s+(is_\w+|has_\w+|show_\w+|enable_\w+)\b',
        r'FALSE as \1',
        sql,
        flags=re.IGNORECASE
    )

    return sql


def _apply_migrations(conn: Union[sqlite3.Connection, 'psycopg2.extensions.connection'],
                      applied_migrations: set,
                      db_type: str) -> None:
    """Apply pending migrations to the database."""
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
        "017_engagement_features.sql",
        "018_add_users_table.sql",
        "019_add_user_id_to_tables.sql",
        "020_fix_daily_checkins_unique_constraint.sql",
        "021_add_class_time_to_sessions.sql",
        "022_add_height_and_target_weight_to_profile.sql",
        "023_add_missing_current_professor_column.sql",
        "024_add_activity_photos.sql",
        "025_add_instructor_id_to_profile.sql",
        "026_social_features.sql",
    ]

    migrations_dir = Path(__file__).parent / "migrations"
    cursor = conn.cursor()

    # Run only new migrations
    for migration in migrations:
        if migration in applied_migrations:
            print(f"[DB] Skipping already applied migration: {migration}")
            continue

        migration_path = migrations_dir / migration
        if migration_path.exists():
            print(f"[DB] Applying migration: {migration}")
            with open(migration_path) as f:
                sql = f.read()

                # Convert SQLite syntax to PostgreSQL if needed
                if db_type == "postgresql":
                    original_sql = sql
                    sql = _convert_sqlite_to_postgresql(sql)
                    if 'AUTOINCREMENT' in original_sql.upper():
                        print(f"[DB] Converted SQLite syntax to PostgreSQL for {migration}")

                    # Split on semicolons and execute separately
                    statements = [s.strip() for s in sql.split(';') if s.strip()]
                    for statement in statements:
                        if not statement:
                            continue

                        # Remove comment lines, but keep the SQL
                        lines = statement.split('\n')
                        sql_lines = [line for line in lines if line.strip() and not line.strip().startswith('--')]
                        clean_statement = '\n'.join(sql_lines).strip()

                        # Skip if no SQL remains after removing comments
                        if not clean_statement:
                            continue

                        try:
                            cursor.execute(clean_statement)
                        except Exception as e:
                            print(f"[DB] Error executing statement: {clean_statement[:100]}...")
                            raise
                else:
                    # SQLite supports executescript
                    conn.executescript(sql)

            # Record this migration as applied
            cursor.execute(
                "INSERT INTO schema_migrations (migration_name) VALUES (%s)" if db_type == "postgresql" else "INSERT INTO schema_migrations (migration_name) VALUES (?)",
                (migration,)
            )
            conn.commit()
            print(f"[DB] Successfully applied migration: {migration}")
        else:
            print(f"[DB] Warning: Migration file not found: {migration}")


@contextmanager
def get_connection():
    """Context manager for database connections."""
    if DB_TYPE == "sqlite":
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

    elif DB_TYPE == "postgresql":
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required for PostgreSQL support")

        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")

        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")


def get_cursor(conn: Union[sqlite3.Connection, 'psycopg2.extensions.connection']):
    """Get a cursor from a connection."""
    return conn.cursor()


def get_last_insert_id(cursor, table_name: str = None) -> int:
    """
    Get the last inserted ID in a database-agnostic way.

    For PostgreSQL, use RETURNING id in your INSERT and call cursor.fetchone()[0].
    For SQLite, use cursor.lastrowid.

    This is a fallback helper - prefer using RETURNING id for PostgreSQL.

    Args:
        cursor: Database cursor
        table_name: Table name (for PostgreSQL sequence lookup, optional)

    Returns:
        Last inserted ID
    """
    if DB_TYPE == "sqlite":
        return cursor.lastrowid
    elif DB_TYPE == "postgresql":
        # For PostgreSQL, we should use RETURNING id in the INSERT statement
        # This is a fallback that queries the sequence
        if table_name:
            cursor.execute(f"SELECT currval(pg_get_serial_sequence('{table_name}', 'id'))")
            return cursor.fetchone()[0]
        else:
            raise ValueError("table_name is required for PostgreSQL")
    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")


if __name__ == "__main__":
    print("Running database migrations...")
    init_db()
    print("Database migrations complete!")
