"""Repository for video data access."""

import json
import sqlite3
from datetime import datetime

from rivaflow.db.database import convert_query, execute_insert, get_connection


class VideoRepository:
    """Data access layer for training videos."""

    @staticmethod
    def create(
        url: str,
        title: str | None = None,
        timestamps: list[dict] | None = None,
        technique_id: int | None = None,
    ) -> int:
        """Create a new video and return its ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """
                INSERT INTO videos (url, title, timestamps, technique_id)
                VALUES (?, ?, ?, ?)
                """,
                (
                    url,
                    title,
                    json.dumps(timestamps) if timestamps else None,
                    technique_id,
                ),
            )

    @staticmethod
    def get_by_id(video_id: int) -> dict | None:
        """Get a video by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM videos WHERE id = ?"), (video_id,)
            )
            row = cursor.fetchone()
            if row:
                return VideoRepository._row_to_dict(row)
            return None

    @staticmethod
    def list_all() -> list[dict]:
        """Get all videos ordered by creation date."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM videos ORDER BY created_at DESC")
            )
            return [VideoRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_technique(technique_id: int) -> list[dict]:
        """Get all videos linked to a specific technique."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM videos WHERE technique_id = ? ORDER BY created_at DESC"
                ),
                (technique_id,),
            )
            return [VideoRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def search(query: str) -> list[dict]:
        """Search videos by title or URL (case-insensitive)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT * FROM videos
                WHERE title LIKE ? OR url LIKE ?
                ORDER BY created_at DESC
                """),
                (f"%{query}%", f"%{query}%"),
            )
            return [VideoRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def update(
        video_id: int,
        title: str | None = None,
        timestamps: list[dict] | None = None,
        technique_id: int | None = None,
    ) -> None:
        """Update video fields."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                UPDATE videos
                SET title = COALESCE(?, title),
                    timestamps = COALESCE(?, timestamps),
                    technique_id = COALESCE(?, technique_id)
                WHERE id = ?
                """),
                (
                    title,
                    json.dumps(timestamps) if timestamps else None,
                    technique_id,
                    video_id,
                ),
            )

    @staticmethod
    def delete(video_id: int) -> None:
        """Delete a video by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM videos WHERE id = ?"), (video_id,)
            )

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)
        # Parse JSON fields
        if data.get("timestamps"):
            data["timestamps"] = json.loads(data["timestamps"])
        # Parse dates - handle both PostgreSQL (datetime) and SQLite (string)
        if data.get("created_at") and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return data
