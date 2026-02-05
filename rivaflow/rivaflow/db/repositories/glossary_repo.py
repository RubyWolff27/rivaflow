"""Repository for movements glossary data access."""
import json
import sqlite3
from datetime import datetime

from rivaflow.db.database import convert_query, execute_insert, get_connection


class GlossaryRepository:
    """Data access layer for movements glossary."""

    @staticmethod
    def list_all(
        category: str | None = None,
        search: str | None = None,
        gi_only: bool = False,
        nogi_only: bool = False,
    ) -> list[dict]:
        """Get all movements, with optional filtering."""
        with get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM movements_glossary WHERE 1=1"
            params = []

            if category:
                query += " AND category = ?"
                params.append(category)

            if search:
                query += " AND (name LIKE ? OR description LIKE ? OR aliases LIKE ?)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])

            if gi_only:
                query += " AND gi_applicable = 1"

            if nogi_only:
                query += " AND nogi_applicable = 1"

            query += " ORDER BY category, name"

            cursor.execute(convert_query(query), params)
            rows = cursor.fetchall()
            return [GlossaryRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def get_by_id(movement_id: int, include_custom_videos: bool = False) -> dict | None:
        """Get a movement by ID, optionally including custom video links."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("SELECT * FROM movements_glossary WHERE id = ?"), (movement_id,))
            row = cursor.fetchone()

            if not row:
                return None

            movement = GlossaryRepository._row_to_dict(row)

            if include_custom_videos:
                # Fetch custom videos for this movement
                cursor.execute(
                    convert_query("""
                    SELECT id, title, url, video_type, created_at
                    FROM movement_videos
                    WHERE movement_id = ?
                    ORDER BY created_at DESC
                    """),
                    (movement_id,)
                )
                videos = cursor.fetchall()
                movement["custom_videos"] = [dict(v) for v in videos]

            return movement

    @staticmethod
    def get_by_name(name: str) -> dict | None:
        """Get a movement by exact name."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("SELECT * FROM movements_glossary WHERE name = ?"), (name,))
            row = cursor.fetchone()
            return GlossaryRepository._row_to_dict(row) if row else None

    @staticmethod
    def get_categories() -> list[str]:
        """Get list of all categories."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("SELECT DISTINCT category FROM movements_glossary ORDER BY category"))
            rows = cursor.fetchall()
            # Handle both dict (PostgreSQL RealDictCursor) and tuple (SQLite) results
            if rows and hasattr(rows[0], 'keys'):
                return [row['category'] for row in rows]
            else:
                return [row[0] for row in rows]

    @staticmethod
    def create_custom(
        name: str,
        category: str,
        subcategory: str | None = None,
        points: int = 0,
        description: str | None = None,
        aliases: list[str] | None = None,
        gi_applicable: bool = True,
        nogi_applicable: bool = True,
    ) -> dict:
        """Create a custom user-added movement."""
        with get_connection() as conn:
            cursor = conn.cursor()

            aliases_json = json.dumps(aliases or [])

            movement_id = execute_insert(
                cursor,
                """
                INSERT INTO movements_glossary (
                    name, category, subcategory, points, description,
                    aliases, gi_applicable, nogi_applicable, custom
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    name, category, subcategory, points, description,
                    aliases_json, 1 if gi_applicable else 0, 1 if nogi_applicable else 0
                )
            )
            cursor.execute(convert_query("SELECT * FROM movements_glossary WHERE id = ?"), (movement_id,))
            row = cursor.fetchone()
            return GlossaryRepository._row_to_dict(row)

    @staticmethod
    def delete_custom(movement_id: int) -> bool:
        """Delete a custom movement. Can only delete custom movements."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("DELETE FROM movements_glossary WHERE id = ? AND custom = 1"), (movement_id,))
            return cursor.rowcount > 0

    @staticmethod
    def add_custom_video(
        movement_id: int,
        url: str,
        title: str | None = None,
        video_type: str = "general",
    ) -> dict:
        """Add a custom video link for a movement."""
        with get_connection() as conn:
            cursor = conn.cursor()
            video_id = execute_insert(
                cursor,
                """
                INSERT INTO movement_videos (movement_id, title, url, video_type)
                VALUES (?, ?, ?, ?)
                """,
                (movement_id, title, url, video_type)
            )
            cursor.execute(convert_query("SELECT * FROM movement_videos WHERE id = ?"), (video_id,))
            row = cursor.fetchone()
            return dict(row)

    @staticmethod
    def delete_custom_video(video_id: int) -> bool:
        """Delete a custom video link."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("DELETE FROM movement_videos WHERE id = ?"), (video_id,))
            return cursor.rowcount > 0

    @staticmethod
    def get_custom_videos(movement_id: int) -> list[dict]:
        """Get all custom videos for a movement."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT id, title, url, video_type, created_at
                FROM movement_videos
                WHERE movement_id = ?
                ORDER BY created_at DESC
                """),
                (movement_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)

        # Parse JSON aliases
        if data.get("aliases"):
            try:
                data["aliases"] = json.loads(data["aliases"])
            except (json.JSONDecodeError, TypeError):
                data["aliases"] = []
        else:
            data["aliases"] = []

        # Parse datetime - handle both PostgreSQL (datetime) and SQLite (string)
        if data.get("created_at") and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        # Convert integer booleans to actual booleans
        for field in ["gi_applicable", "nogi_applicable", "custom",
                      "ibjjf_legal_white", "ibjjf_legal_blue", "ibjjf_legal_purple",
                      "ibjjf_legal_brown", "ibjjf_legal_black"]:
            if field in data:
                data[field] = bool(data[field])

        return data
