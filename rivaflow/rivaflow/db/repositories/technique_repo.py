"""Repository for technique data access."""

import sqlite3
from datetime import date, datetime

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository


class TechniqueRepository(BaseRepository):
    """Data access layer for techniques."""

    @staticmethod
    def create(name: str, category: str | None = None) -> int:
        """Create a new technique and return its ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                return execute_insert(
                    cursor,
                    "INSERT INTO techniques (name, category) VALUES (?, ?)",
                    (name.lower().strip(), category),
                )
            except sqlite3.IntegrityError:
                # Technique already exists, return existing ID
                cursor.execute(
                    convert_query("SELECT id FROM techniques WHERE name = ?"),
                    (name.lower().strip(),),
                )
                row = cursor.fetchone()
                return row["id"]

    @staticmethod
    def get_by_id(technique_id: int) -> dict | None:
        """Get a technique by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM techniques WHERE id = ?"), (technique_id,)
            )
            row = cursor.fetchone()
            if row:
                return TechniqueRepository._row_to_dict(row)
            return None

    @staticmethod
    def get_by_name(name: str) -> dict | None:
        """Get a technique by name (case-insensitive)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM techniques WHERE name = ?"),
                (name.lower().strip(),),
            )
            row = cursor.fetchone()
            if row:
                return TechniqueRepository._row_to_dict(row)
            return None

    @staticmethod
    def get_or_create(name: str, category: str | None = None) -> dict | None:
        """Get existing technique or create new one. Returns technique dict."""
        existing = TechniqueRepository.get_by_name(name)
        if existing:
            return existing

        technique_id = TechniqueRepository.create(name, category)
        return TechniqueRepository.get_by_id(technique_id)

    @staticmethod
    def list_all() -> list[dict]:
        """Get all techniques ordered by name."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("SELECT * FROM techniques ORDER BY name"))
            return [TechniqueRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def update_last_trained(technique_id: int, trained_date: date) -> None:
        """Update the last trained date for a technique."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "UPDATE techniques SET last_trained_date = ? WHERE id = ?"
                ),
                (trained_date.isoformat(), technique_id),
            )

    @staticmethod
    def get_stale(days: int = 7) -> list[dict]:
        """Get techniques not trained in N days (or never trained)."""
        from datetime import date, timedelta

        # Calculate cutoff date in Python (works for both SQLite and PostgreSQL)
        cutoff_date = (date.today() - timedelta(days=days)).isoformat()

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT * FROM techniques
                WHERE last_trained_date IS NULL
                   OR last_trained_date < ?
                ORDER BY last_trained_date ASC
                """),
                (cutoff_date,),
            )
            return [TechniqueRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def search(query: str) -> list[dict]:
        """Search techniques by name (case-insensitive partial match)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM techniques WHERE name LIKE ? ORDER BY name"
                ),
                (f"%{query.lower()}%",),
            )
            return [TechniqueRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_unique_names() -> list[str]:
        """Get all technique names for autocomplete."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("SELECT name FROM techniques ORDER BY name"))
            rows = cursor.fetchall()
            return [row["name"] for row in rows]

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)
        # Parse dates - handle both PostgreSQL (date/datetime) and SQLite (string)
        if data.get("last_trained_date") and isinstance(data["last_trained_date"], str):
            data["last_trained_date"] = date.fromisoformat(data["last_trained_date"])
        if data.get("created_at") and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return data
