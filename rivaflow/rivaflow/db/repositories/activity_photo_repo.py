"""Repository for activity photos data access."""

from rivaflow.db.database import convert_query, execute_insert, get_connection


class ActivityPhotoRepository:
    """Data access layer for activity photos."""

    @staticmethod
    def create(
        user_id: int,
        activity_type: str,
        activity_id: int,
        activity_date: str,
        file_path: str,
        file_name: str,
        file_size: int | None = None,
        mime_type: str | None = None,
        caption: str | None = None,
        display_order: int = 1,
    ) -> int:
        """Create a new activity photo record. Returns photo ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """
                INSERT INTO activity_photos (
                    user_id, activity_type, activity_id, activity_date,
                    file_path, file_name, file_size, mime_type, caption, display_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    activity_type,
                    activity_id,
                    activity_date,
                    file_path,
                    file_name,
                    file_size,
                    mime_type,
                    caption,
                    display_order,
                ),
            )

    @staticmethod
    def get_by_activity(
        user_id: int, activity_type: str, activity_id: int
    ) -> list[dict]:
        """Get all photos for a specific activity."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT * FROM activity_photos
                WHERE user_id = ? AND activity_type = ? AND activity_id = ?
                ORDER BY display_order, created_at
                """),
                (user_id, activity_type, activity_id),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_by_date(user_id: int, activity_date: str) -> list[dict]:
        """Get all photos for a specific date."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT * FROM activity_photos
                WHERE user_id = ? AND activity_date = ?
                ORDER BY display_order, created_at
                """),
                (user_id, activity_date),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_by_id(user_id: int, photo_id: int) -> dict | None:
        """Get a photo by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM activity_photos WHERE id = ? AND user_id = ?"),
                (photo_id, user_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def delete(user_id: int, photo_id: int) -> bool:
        """Delete a photo by ID. Returns True if deleted."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM activity_photos WHERE id = ? AND user_id = ?"),
                (photo_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete_by_activity(
        user_id: int, activity_type: str, activity_id: int
    ) -> None:
        """Delete all photos for a specific activity."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                DELETE FROM activity_photos
                WHERE user_id = ? AND activity_type = ? AND activity_id = ?
                """),
                (user_id, activity_type, activity_id),
            )

    @staticmethod
    def update_caption(user_id: int, photo_id: int, caption: str) -> bool:
        """Update photo caption. Returns True if updated."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                UPDATE activity_photos SET caption = ?
                WHERE id = ? AND user_id = ?
                """),
                (caption, photo_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def count_by_activity(
        user_id: int, activity_type: str, activity_id: int
    ) -> int:
        """Count photos for a specific activity."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT COUNT(*) FROM activity_photos
                WHERE user_id = ? AND activity_type = ? AND activity_id = ?
                """),
                (user_id, activity_type, activity_id),
            )
            row = cursor.fetchone()
            # Handle both dict (PostgreSQL) and tuple (SQLite) results
            if hasattr(row, 'keys'):
                # PostgreSQL RealDictCursor - get first value
                return list(row.values())[0]
            else:
                # SQLite tuple
                return row[0]
