"""Base repository with shared database utilities.

New repositories can inherit from BaseRepository to avoid duplicating
boilerplate for connection management, query conversion, and row→dict
mapping.  Existing repos are NOT modified — this is additive only.
"""

from __future__ import annotations

from typing import Any


class BaseRepository:
    """Base class for repositories with shared database utilities."""

    @staticmethod
    def _row_to_dict(row) -> dict | None:
        """Convert a database row to a dictionary.

        Returns None when *row* is None so callers can do a simple
        ``return self._row_to_dict(cursor.fetchone())``.
        """
        if row is None:
            return None
        return dict(row)

    @staticmethod
    def _rows_to_dicts(rows) -> list[dict]:
        """Convert a list of database rows to a list of dictionaries.

        Returns an empty list when *rows* is None or empty.
        """
        if not rows:
            return []
        return [dict(row) for row in rows]

    @staticmethod
    def _fetchone(query: str, params: tuple[Any, ...] = ()) -> dict | None:
        """Execute a query and return one result as a dict (or None).

        Handles connection acquisition, query conversion (``?`` -> ``$N``
        for PostgreSQL), and row-to-dict mapping in a single call.
        """
        from rivaflow.db.database import convert_query, get_connection

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query(query), params)
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def _fetchall(query: str, params: tuple[Any, ...] = ()) -> list[dict]:
        """Execute a query and return all results as a list of dicts.

        Handles connection acquisition, query conversion, and row-to-dict
        mapping in a single call.
        """
        from rivaflow.db.database import convert_query, get_connection

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query(query), params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def _execute(query: str, params: tuple[Any, ...] = ()):
        """Execute a write query (INSERT/UPDATE/DELETE) and commit.

        Returns the cursor so callers can inspect ``rowcount`` or
        ``lastrowid`` when needed.
        """
        from rivaflow.db.database import convert_query, get_connection

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query(query), params)
            conn.commit()
            return cursor
