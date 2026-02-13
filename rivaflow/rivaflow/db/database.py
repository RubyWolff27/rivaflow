"""Database connection management and initialization.

Schema migrations use 'version' column (not 'migration_name').
"""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Union

from rivaflow.config import APP_DIR, DATABASE_URL, DB_PATH, get_db_type

logger = logging.getLogger(__name__)

# Backwards compatibility
DB_TYPE = get_db_type()


def get_placeholder():
    """Get the correct SQL parameter placeholder for the current database."""
    return "?" if get_db_type() == "sqlite" else "%s"


def convert_query(query: str) -> str:
    """
    Convert a query with ? placeholders to the correct format for current database.

    Skips ``?`` characters inside single-quoted SQL string literals so that
    values like ``'What?'`` are not mangled.

    Args:
        query: SQL query string with ? placeholders (SQLite style)

    Returns:
        Query string with correct placeholders for current database
    """
    if get_db_type() == "postgresql":
        import re

        # Replace ? with %s only when NOT inside single-quoted strings.
        # Strategy: split on single-quote boundaries, only substitute in
        # even-indexed segments (outside quotes).
        parts = re.split(r"('(?:[^'\\]|\\.)*')", query)
        for i in range(0, len(parts), 2):
            parts[i] = parts[i].replace("?", "%s")
        return "".join(parts)
    return query


def execute_insert(cursor, query: str, params: tuple) -> int:
    """
    Execute an INSERT query and return the inserted ID.

    Handles the difference between PostgreSQL (RETURNING id) and SQLite (lastrowid).

    Args:
        cursor: Database cursor
        query: INSERT query string with ? placeholders (without RETURNING clause)
        params: Query parameters tuple

    Returns:
        The ID of the inserted row
    """
    if get_db_type() == "postgresql":
        import re as _re

        import psycopg2.errors

        # PostgreSQL: Add RETURNING id and fetch the result
        query_with_returning = query.rstrip().rstrip(";") + " RETURNING id"
        converted = convert_query(query_with_returning)

        try:
            cursor.execute(converted, params)
        except psycopg2.errors.UniqueViolation as exc:
            # Serial sequence out of sync — reset and retry once
            err_msg = str(exc)
            logger.warning(f"UniqueViolation on INSERT, resetting sequence: {err_msg}")
            conn = cursor.connection
            conn.rollback()

            # Extract table name from INSERT INTO <table>
            tbl_match = _re.search(r"INSERT\s+INTO\s+(\w+)", query, _re.IGNORECASE)
            if tbl_match:
                tbl_name = tbl_match.group(1)
                try:
                    cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {tbl_name}")  # noqa: S608
                    max_id = cursor.fetchone()[0]

                    # Find sequence by name pattern (handles renamed tables)
                    cursor.execute(
                        "SELECT relname FROM pg_class " "WHERE relkind = 'S' AND relname LIKE %s",
                        (f"%{tbl_name}%",),
                    )
                    seqs = [r[0] for r in cursor.fetchall()]
                    logger.info(f"Found sequences for {tbl_name}: {seqs}, max_id={max_id}")

                    for seq in seqs:
                        cursor.execute("SELECT setval(%s, %s, true)", (seq, max_id))
                        logger.info(f"Reset sequence {seq} to {max_id}")
                    conn.commit()

                    if not seqs:
                        # No sequence found at all — insert with explicit id
                        logger.warning(f"No sequence found for {tbl_name}, using explicit id")
                        explicit_id = max_id + 1
                        # Add id column to the INSERT
                        explicit_query = _re.sub(
                            rf"INSERT\s+INTO\s+{tbl_name}\s*\(",
                            f"INSERT INTO {tbl_name} (id, ",
                            query,
                            count=1,
                            flags=_re.IGNORECASE,
                        )
                        explicit_query = _re.sub(
                            r"VALUES\s*\(",
                            f"VALUES ({explicit_id}, ",
                            explicit_query,
                            count=1,
                            flags=_re.IGNORECASE,
                        )
                        explicit_query = explicit_query.rstrip().rstrip(";") + " RETURNING id"
                        cursor.execute(convert_query(explicit_query), params)
                        conn.commit()
                        result = cursor.fetchone()
                        if hasattr(result, "keys"):
                            return result["id"]
                        return result[0]

                except Exception as inner:
                    logger.error(f"Failed to reset sequence for {tbl_name}: {inner}")
                    conn.rollback()

            # Retry the INSERT once (sequence should be fixed now)
            cursor.execute(converted, params)

        result = cursor.fetchone()

        if result is None:
            logger.error(f"INSERT query returned no rows. Query: {query[:100]}...")
            raise ValueError("INSERT did not return an ID")

        # Handle both dict-like and tuple-like results
        try:
            if hasattr(result, "keys"):
                return result["id"]
            else:
                return result[0]
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Failed to extract ID from result: {result}, error: {e}")
            raise ValueError(f"Could not extract ID from INSERT result: {result}")
    else:
        # SQLite: Use lastrowid
        cursor.execute(convert_query(query), params)
        inserted_id = cursor.lastrowid

        if not inserted_id or inserted_id == 0:
            logger.error(f"SQLite INSERT returned invalid lastrowid: {inserted_id}")
            raise ValueError(f"INSERT did not return a valid ID (got {inserted_id})")

        return inserted_id


# Import PostgreSQL adapter if available
try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

# Global connection pool for PostgreSQL (initialized on first use)
_connection_pool: Optional["psycopg2.pool.ThreadedConnectionPool"] = None


def _get_connection_pool() -> "psycopg2.pool.ThreadedConnectionPool":
    """Get or create the PostgreSQL connection pool."""
    global _connection_pool

    if _connection_pool is None:
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required for PostgreSQL support")

        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")

        # Create thread-safe connection pool with min=2, max=20 connections
        # minconn=2: Keep 2 warm connections ready
        # maxconn=20: Stay within Render starter tier limits
        _connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2, maxconn=20, dsn=DATABASE_URL
        )

    return _connection_pool


def close_connection_pool() -> None:
    """Close all connections in the PostgreSQL connection pool.

    Call this on application shutdown to gracefully close database connections.
    """
    global _connection_pool

    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None


def init_db() -> None:
    """Initialize the database with schema migrations and seed data."""
    if DB_TYPE == "sqlite":
        _init_sqlite_db()
    elif DB_TYPE == "postgresql":
        _init_postgresql_db()
    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")

    # Seed glossary data if not already present
    try:
        from rivaflow.db.seed_glossary import seed_glossary

        seed_glossary()
    except Exception as e:
        logger.warning(f"Could not seed glossary (table may not exist yet): {e}")


def _init_sqlite_db() -> None:
    """Initialize SQLite database with migrations."""
    import os

    # Ensure app directory exists
    APP_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        # Create migrations tracking table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

        # Get list of already applied migrations
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM schema_migrations")
        applied_migrations = {row[0] for row in cursor.fetchall()}

        _apply_migrations(conn, applied_migrations, "sqlite")

    finally:
        conn.close()

    # Set secure file permissions (user read/write only) - 0o600
    # This ensures other users on the system cannot access the database
    if DB_PATH.exists():
        os.chmod(DB_PATH, 0o600)
        logger.info(f"Set secure file permissions (0o600) on {DB_PATH}")


def _init_postgresql_db() -> None:
    """Initialize PostgreSQL database.

    Note: PostgreSQL migrations are handled by migrate.py, not by this function.
    This function only creates the migrations tracking table and resets sequences.
    """
    if not PSYCOPG2_AVAILABLE:
        raise ImportError(
            "psycopg2 is required for PostgreSQL support. Install with: pip install psycopg2-binary"
        )

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required for PostgreSQL")

    conn = psycopg2.connect(DATABASE_URL)
    try:
        cursor = conn.cursor()

        # Create migrations tracking table if it doesn't exist
        # migrate.py will populate this table with applied migrations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # PostgreSQL migrations are handled by migrate.py
        # Skip _apply_migrations() to avoid conflicts with migrate.py
        logger.info("PostgreSQL database initialized. Migrations will be handled by migrate.py")

        # Reset sequences for tables with SERIAL primary keys
        try:
            _reset_postgresql_sequences(conn)
        except Exception as e:
            # Sequences might not exist yet if this is first run
            logger.debug(f"Skipping sequence reset (tables may not exist yet): {e}")

    finally:
        conn.close()


def _reset_postgresql_sequences(conn) -> None:
    """Reset PostgreSQL sequences for tables with SERIAL primary keys."""
    # Get all tables with SERIAL columns
    tables_with_serials = [
        "users",
        "profile",
        "sessions",
        "readiness",
        "techniques",
        "videos",
        "gradings",
        "movements",
        "friends",
        "movement_videos",
        "session_rolls",
        "session_techniques",
        "weekly_goal_progress",
        "daily_checkins",
        "milestones",
        "streaks",
        "activity_photos",
        "user_relationships",
        "activity_likes",
        "activity_comments",
        "refresh_tokens",
        "gyms",
        "audit_logs",
        "game_plans",
        "game_plan_nodes",
        "game_plan_edges",
        "session_events",
        "ai_insights",
    ]

    for table in tables_with_serials:
        # Each table gets its own try-catch with rollback to prevent transaction abortion
        cursor = conn.cursor()
        try:
            # Check if table exists first
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                )
            """,
                (table,),
            )

            if not cursor.fetchone()[0]:
                continue

            # Reset sequence to max(id) + 1
            # Use parameterized identifier quoting via psycopg2.sql
            from psycopg2 import sql

            tbl = sql.Identifier(table)
            cursor.execute(
                sql.SQL("SELECT pg_get_serial_sequence({lit}, 'id')").format(lit=sql.Literal(table))
            )
            row = cursor.fetchone()
            seq_name = row[0] if row else None

            # Fallback: extract sequence name from column default expression
            # Handles renamed tables where pg_get_serial_sequence returns NULL
            if not seq_name:
                cursor.execute(
                    "SELECT column_default FROM information_schema.columns "
                    "WHERE table_name = %s AND column_name = 'id'",
                    (table,),
                )
                default_row = cursor.fetchone()
                if default_row and default_row[0]:
                    import re as _re

                    m = _re.search(r"nextval\('([^']+)'", default_row[0])
                    if m:
                        seq_name = m.group(1)
                        logger.info(f"Found sequence {seq_name} for {table} via column default")

            if seq_name:
                cursor.execute(sql.SQL("SELECT COALESCE(MAX(id), 0) FROM {tbl}").format(tbl=tbl))
                max_id = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT setval(%s, %s, false)",
                    (seq_name, max_id + 1),
                )
                logger.info(f"Reset {seq_name} to {max_id + 1} for {table}")

            conn.commit()
        except Exception as e:
            # Rollback this table's transaction and continue with next table
            conn.rollback()
            logger.warning(f"Skipped sequence reset for table {table}: {e}")


def _convert_sqlite_to_postgresql(sql: str) -> str:
    """Convert SQLite SQL syntax to PostgreSQL syntax."""
    import re

    # Replace AUTOINCREMENT with SERIAL (handle various whitespace)
    sql = re.sub(
        r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b",
        "SERIAL PRIMARY KEY",
        sql,
        flags=re.IGNORECASE,
    )

    # Replace INSERT OR IGNORE with INSERT ... ON CONFLICT DO NOTHING
    sql = re.sub(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b", "INSERT INTO", sql, flags=re.IGNORECASE)
    # Add ON CONFLICT DO NOTHING at the end of INSERT statements that were INSERT OR IGNORE
    # This is a bit tricky - we need to add it before the semicolon or end of statement
    # For now, we'll handle simple cases: INSERT INTO table (...) VALUES (...)
    sql = re.sub(
        r"(\bINSERT\s+INTO\s+\w+\s*\([^)]+\)\s*VALUES\s*\([^)]+\))(?=\s*;|\s*$)",
        r"\1 ON CONFLICT DO NOTHING",
        sql,
        flags=re.IGNORECASE,
    )

    # Replace TEXT columns with datetime defaults to TIMESTAMP
    # IMPORTANT: This must run BEFORE the standalone datetime('now') replacement
    # so the compound pattern can match
    sql = re.sub(
        r"TEXT\s+NOT\s+NULL\s+DEFAULT\s+\(\s*datetime\s*\(\s*['\"]now['\"]\s*\)\s*\)",
        "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        sql,
        flags=re.IGNORECASE,
    )

    # Replace standalone datetime('now') in DEFAULT clauses
    sql = re.sub(
        r"DEFAULT\s+\(\s*datetime\s*\(\s*['\"]now['\"]\s*\)\s*\)",
        "DEFAULT CURRENT_TIMESTAMP",
        sql,
        flags=re.IGNORECASE,
    )

    # Replace remaining datetime('now') with CURRENT_TIMESTAMP
    sql = re.sub(
        r"datetime\s*\(\s*['\"]now['\"]\s*\)",
        "CURRENT_TIMESTAMP",
        sql,
        flags=re.IGNORECASE,
    )

    # Replace date('now') with CURRENT_DATE (SQLite date function)
    sql = re.sub(
        r"date\s*\(\s*['\"]now['\"]\s*\)",
        "CURRENT_DATE",
        sql,
        flags=re.IGNORECASE,
    )

    # Replace BOOLEAN DEFAULT 1/0 with TRUE/FALSE (handles NOT NULL case too)
    sql = re.sub(
        r"\bBOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+1\b",
        "BOOLEAN NOT NULL DEFAULT TRUE",
        sql,
        flags=re.IGNORECASE,
    )
    sql = re.sub(
        r"\bBOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+0\b",
        "BOOLEAN NOT NULL DEFAULT FALSE",
        sql,
        flags=re.IGNORECASE,
    )
    sql = re.sub(r"\bBOOLEAN\s+DEFAULT\s+1\b", "BOOLEAN DEFAULT TRUE", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bBOOLEAN\s+DEFAULT\s+0\b", "BOOLEAN DEFAULT FALSE", sql, flags=re.IGNORECASE)

    # Replace integer literals used as boolean values in SELECT/INSERT
    # Pattern: "1 as column_name" where column_name suggests boolean (is_*, has_*, etc)
    sql = re.sub(
        r"\b1\s+as\s+(is_\w+|has_\w+|show_\w+|enable_\w+)\b",
        r"TRUE as \1",
        sql,
        flags=re.IGNORECASE,
    )
    sql = re.sub(
        r"\b0\s+as\s+(is_\w+|has_\w+|show_\w+|enable_\w+)\b",
        r"FALSE as \1",
        sql,
        flags=re.IGNORECASE,
    )

    # Add CASCADE to DROP TABLE statements (PostgreSQL needs it for FK deps)
    sql = re.sub(
        r"\bDROP\s+TABLE\s+IF\s+EXISTS\s+(\w+)\s*;",
        r"DROP TABLE IF EXISTS \1 CASCADE;",
        sql,
        flags=re.IGNORECASE,
    )

    return sql


def _apply_migrations(
    conn: Union[sqlite3.Connection, "psycopg2.extensions.connection"],
    applied_migrations: set,
    db_type: str,
) -> None:
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
        "027_fix_streaks_unique_constraint.sql",
        "028_password_reset_tokens.sql",
        "029_rename_contacts_to_friends.sql",
        "030_fix_goal_progress_unique_constraint.sql",
        "031_fix_readiness_unique_constraint.sql",
        "032_fix_friends_unique_constraint.sql",
        "034_fix_movements_glossary_custom.sql",
        "035_create_gyms_table.sql",
        "036_add_admin_role.sql",
        "037_add_gym_contact_fields.sql",
        "038_set_production_admin.sql",
        "039_create_audit_logs.sql",
        "040_add_performance_indexes.sql",
        "041_create_notifications.sql",
        "042_add_avatar_url.sql",
        "043_add_default_location.sql",
        "044_grapple_foundation.sql",
        "045_add_gym_maps_and_belt.sql",
        "047_add_primary_training_type.sql",
        "048_add_setup_wizard_fields.sql",
        "049_app_feedback_system.sql",
        "050_tier_system_enhancements.sql",
        "051_migrate_beta_users.sql",
        "052_add_activity_specific_goals.sql",
        "053_add_gradings_instructor_photo.sql",
        "054_fix_streaks_unique_constraint_final.sql",
        "058_set_owner_admin.sql",
        "059_create_waitlist.sql",
        "060_fight_dynamics.sql",
        "061_events_and_weight_logs.sql",
        "062_groups.sql",
        "063_social_connections.sql",
        "064_game_plans.sql",
        "065_enhanced_grapple.sql",
        "066_add_check_constraints.sql",
        "067_create_grapple_tables.sql",
        "071_deduplicate_glossary.sql",
        "072_fix_rate_limits_unique_index.sql",
        "073_create_training_goals.sql",
        "074_add_profile_timezone.sql",
        "075_whoop_integration.sql",
        "076_whoop_recovery.sql",
        "077_whoop_auto_sessions.sql",
        "078_coach_preferences.sql",
        "079_coach_belt_ruleset.sql",
        "080_training_start_date.sql",
        "081_whoop_auto_fill_readiness.sql",
        "082_gi_nogi_preference.sql",
        "083_target_weight_date.sql",
        "084_email_drip_log.sql",
        "085_multi_daily_checkins.sql",
        "086_ensure_profile_timezone.sql",
    ]

    migrations_dir = Path(__file__).parent / "migrations"
    cursor = conn.cursor()

    # Run only new migrations
    for migration in migrations:
        if migration in applied_migrations:
            logger.info(f"Skipping already applied migration: {migration}")
            continue

        migration_path = migrations_dir / migration
        # Prefer _pg.sql version for PostgreSQL
        if db_type == "postgresql":
            pg_path = migrations_dir / migration.replace(".sql", "_pg.sql")
            if pg_path.exists():
                migration_path = pg_path
        if migration_path.exists():
            logger.info(f"Applying migration: {migration}")
            with open(migration_path) as f:
                sql = f.read()

                # Convert SQLite syntax to PostgreSQL if needed
                if db_type == "postgresql":
                    original_sql = sql
                    sql = _convert_sqlite_to_postgresql(sql)
                    if "AUTOINCREMENT" in original_sql.upper():
                        logger.debug(f"Converted SQLite syntax to PostgreSQL for {migration}")

                    # Split on semicolons and execute separately
                    statements = [s.strip() for s in sql.split(";") if s.strip()]
                    for statement in statements:
                        if not statement:
                            continue

                        # Remove comment lines, but keep the SQL
                        lines = statement.split("\n")
                        sql_lines = [
                            line
                            for line in lines
                            if line.strip() and not line.strip().startswith("--")
                        ]
                        clean_statement = "\n".join(sql_lines).strip()

                        # Skip if no SQL remains after removing comments
                        if not clean_statement:
                            continue

                        try:
                            cursor.execute(clean_statement)
                        except Exception as e:
                            logger.error(
                                f"Error executing statement: {clean_statement[:100]}... - {e}"
                            )
                            raise
                else:
                    # SQLite supports executescript
                    try:
                        conn.executescript(sql)
                    except Exception as e:
                        logger.error(f"Failed to apply migration {migration}: {e}")
                        logger.error(f"SQL content (first 1000 chars): {sql[:1000]}")
                        raise

            # Record this migration as applied
            cursor.execute(
                (
                    "INSERT INTO schema_migrations (version) VALUES (%s)"
                    if db_type == "postgresql"
                    else "INSERT INTO schema_migrations (version) VALUES (?)"
                ),
                (migration,),
            )
            conn.commit()
            logger.info(f"Successfully applied migration: {migration}")
        else:
            logger.warning(f"Migration file not found: {migration}")


@contextmanager
def get_connection():
    """Context manager for database connections with connection pooling for PostgreSQL."""
    if DB_TYPE == "sqlite":
        import os

        # Auto-initialize if database doesn't exist
        if not DB_PATH.exists():
            init_db()
        else:
            # Ensure permissions are secure on existing database
            try:
                os.chmod(DB_PATH, 0o600)
            except (OSError, FileNotFoundError):
                # Silently ignore permission errors
                pass

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
        # Get connection from pool
        pool = _get_connection_pool()
        conn = pool.getconn()

        # Set RealDictCursor for this connection
        conn.cursor_factory = psycopg2.extras.RealDictCursor

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            # Return connection to pool instead of closing
            pool.putconn(conn)

    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")


def get_cursor(conn: Union[sqlite3.Connection, "psycopg2.extensions.connection"]):
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
            cursor.execute(
                "SELECT currval(pg_get_serial_sequence(%s, 'id'))",
                (table_name,),
            )
            return cursor.fetchone()[0]
        else:
            raise ValueError("table_name is required for PostgreSQL")
    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger.info("Running database migrations...")
    init_db()
    logger.info("Database migrations complete!")
