"""Database connection management and initialization.

PostgreSQL-only. Schema migrations use 'version' column (not 'migration_name').
"""

import logging
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from rivaflow.core.settings import settings

logger = logging.getLogger(__name__)

# Backwards compatibility
DB_TYPE = settings.DB_TYPE
APP_DIR = settings.APP_DIR
DATABASE_URL = settings.DATABASE_URL
DB_PATH = settings.DB_PATH


def get_placeholder():
    """Get the correct SQL parameter placeholder (%s for PostgreSQL)."""
    return "%s"


def convert_query(query: str) -> str:
    """
    Convert a query with ? placeholders to PostgreSQL %s format.

    Skips ``?`` characters inside single-quoted SQL string literals so that
    values like ``'What?'`` are not mangled.

    Args:
        query: SQL query string with ? placeholders

    Returns:
        Query string with %s placeholders for PostgreSQL
    """
    # Replace ? with %s only when NOT inside single-quoted strings.
    # Strategy: split on single-quote boundaries, only substitute in
    # even-indexed segments (outside quotes).
    parts = re.split(r"('(?:[^'\\]|\\.)*')", query)
    for i in range(0, len(parts), 2):
        parts[i] = parts[i].replace("?", "%s")
    return "".join(parts)


def execute_insert(cursor, query: str, params: tuple) -> int:
    """
    Execute an INSERT query and return the inserted ID via RETURNING id.

    Args:
        cursor: Database cursor
        query: INSERT query string with ? placeholders (without RETURNING clause)
        params: Query parameters tuple

    Returns:
        The ID of the inserted row
    """
    import re as _re

    import psycopg2.errors

    # Add RETURNING id and convert placeholders
    query_with_returning = query.rstrip().rstrip(";") + " RETURNING id"
    converted = convert_query(query_with_returning)

    try:
        cursor.execute(converted, params)
    except psycopg2.errors.UniqueViolation:
        # Serial sequence out of sync — reset it and retry once
        conn = cursor.connection
        conn.rollback()

        tbl_match = _re.search(r"INSERT\s+INTO\s+(\w+)", query, _re.IGNORECASE)
        if not tbl_match:
            raise

        tbl_name = tbl_match.group(1)
        logger.warning(
            "UniqueViolation on INSERT into %s, resetting sequence",
            tbl_name,
        )

        # Reset the sequence to max(id) so the next insert succeeds
        cursor.execute(
            "SELECT setval(pg_get_serial_sequence(%s, 'id'), "
            "COALESCE(MAX(id), 1)) FROM " + tbl_name,
            (tbl_name,),
        )
        cursor.execute(converted, params)

    result = cursor.fetchone()

    if result is None:
        logger.error("INSERT query returned no rows. Query: %s...", query[:100])
        raise ValueError("INSERT did not return an ID")

    # Handle both dict-like and tuple-like results
    try:
        if hasattr(result, "keys"):
            return result["id"]
        else:
            return result[0]
    except (KeyError, IndexError, TypeError) as e:
        logger.error("Failed to extract ID from result: %s, error: %s", result, e)
        raise ValueError(f"Could not extract ID from INSERT result: {result}")


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

        # Create thread-safe connection pool
        # minconn=2: Keep 2 warm connections ready
        # maxconn=20: Allows more concurrent requests while staying
        #   within Render managed PG limits (~97 connections)
        _connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=20,
            dsn=DATABASE_URL,
            connect_timeout=10,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
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
    """Initialize the PostgreSQL database with schema and seed data."""
    _init_postgresql_db()

    # Seed glossary data if not already present
    try:
        from rivaflow.db.seed_glossary import seed_glossary

        seed_glossary()
    except Exception as e:
        logger.warning("Could not seed glossary (table may not exist yet): %s", e)


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
        logger.info(
            "PostgreSQL database initialized. Migrations will be handled by migrate.py"
        )

        # Reset sequences for tables with SERIAL primary keys
        try:
            _reset_postgresql_sequences(conn)
        except Exception as e:
            # Sequences might not exist yet if this is first run
            logger.debug("Skipping sequence reset (tables may not exist yet): %s", e)

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
                sql.SQL("SELECT pg_get_serial_sequence({lit}, 'id')").format(
                    lit=sql.Literal(table)
                )
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
                        logger.info(
                            f"Found sequence {seq_name} for {table} via column default"
                        )

            if seq_name:
                cursor.execute(
                    sql.SQL("SELECT COALESCE(MAX(id), 0) FROM {tbl}").format(tbl=tbl)
                )
                max_id = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT setval(%s, %s, false)",
                    (seq_name, max_id + 1),
                )
                logger.info("Reset %s to %s for %s", seq_name, max_id + 1, table)

            conn.commit()
        except Exception as e:
            # Rollback this table's transaction and continue with next table
            conn.rollback()
            logger.warning("Skipped sequence reset for table %s: %s", table, e)


def _apply_migrations(
    conn: "psycopg2.extensions.connection",
    applied_migrations: set,
) -> None:
    """Apply pending migrations to the PostgreSQL database."""
    # Discover migrations from filesystem (sorted by filename prefix)
    migrations_dir = Path(__file__).parent / "migrations"
    migrations = sorted(
        f.name for f in migrations_dir.glob("*.sql") if not f.name.endswith("_pg.sql")
    )

    cursor = conn.cursor()

    # Run only new migrations
    for migration in migrations:
        if migration in applied_migrations:
            logger.info("Skipping already applied migration: %s", migration)
            continue

        migration_path = migrations_dir / migration
        # Prefer _pg.sql version for PostgreSQL
        pg_path = migrations_dir / migration.replace(".sql", "_pg.sql")
        if pg_path.exists():
            migration_path = pg_path
        if migration_path.exists():
            logger.info("Applying migration: %s", migration)
            with open(migration_path) as f:
                sql = f.read()

                # Split on semicolons and execute separately
                statements = [s.strip() for s in sql.split(";") if s.strip()]
                stmt_failures = 0
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
                        # Use SAVEPOINT so a single failed statement
                        # (e.g. CREATE EXTENSION for missing pgvector)
                        # doesn't abort the whole migration transaction.
                        cursor.execute("SAVEPOINT migration_stmt")
                        cursor.execute(clean_statement)
                        cursor.execute("RELEASE SAVEPOINT migration_stmt")
                    except Exception as e:
                        stmt_failures += 1
                        logger.warning(
                            f"Statement failed (rolling back): "
                            f"{clean_statement[:100]}... - {e}"
                        )
                        cursor.execute("ROLLBACK TO SAVEPOINT migration_stmt")
                        cursor.execute("RELEASE SAVEPOINT migration_stmt")
                if stmt_failures:
                    if stmt_failures >= len(statements):
                        raise RuntimeError(
                            f"Migration {migration}: ALL {stmt_failures} "
                            f"statement(s) failed — aborting deployment"
                        )
                    logger.warning(
                        f"Migration {migration}: {stmt_failures} of "
                        f"{len(statements)} statement(s) failed (non-fatal)"
                    )

            # Record this migration as applied
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (migration,),
            )
            conn.commit()
            logger.info("Successfully applied migration: %s", migration)
        else:
            logger.warning("Migration file not found: %s", migration)


@contextmanager
def get_connection():
    """Context manager for PostgreSQL connections with connection pooling."""
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


def get_cursor(conn: "psycopg2.extensions.connection"):
    """Get a cursor from a connection."""
    return conn.cursor()


def get_last_insert_id(cursor, table_name: str = None) -> int:
    """
    Get the last inserted ID by querying the PostgreSQL sequence.

    Prefer using RETURNING id in your INSERT statement instead.

    Args:
        cursor: Database cursor
        table_name: Table name (required for PostgreSQL sequence lookup)

    Returns:
        Last inserted ID
    """
    if table_name:
        cursor.execute(
            "SELECT currval(pg_get_serial_sequence(%s, 'id'))",
            (table_name,),
        )
        return cursor.fetchone()[0]
    else:
        raise ValueError("table_name is required for PostgreSQL")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger.info("Running database migrations...")
    init_db()
    logger.info("Database migrations complete!")
