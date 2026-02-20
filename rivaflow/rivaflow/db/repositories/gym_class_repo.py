"""Repository for gym class timetable data access."""

from typing import Any

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class GymClassRepository(BaseRepository):
    """Data access layer for gym_classes table."""

    @staticmethod
    def create(
        gym_id: int,
        day_of_week: int,
        start_time: str,
        end_time: str,
        class_name: str,
        class_type: str | None = None,
        level: str | None = None,
    ) -> int:
        """Create a new gym class entry and return its ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                convert_query("""
                    INSERT INTO gym_classes
                    (gym_id, day_of_week, start_time, end_time,
                     class_name, class_type, level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """),
                (
                    gym_id,
                    day_of_week,
                    start_time,
                    end_time,
                    class_name,
                    class_type,
                    level,
                ),
            )

    @staticmethod
    def get_by_gym(gym_id: int) -> list[dict[str, Any]]:
        """Get all active classes for a gym, ordered by day and time."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT * FROM gym_classes
                    WHERE gym_id = ? AND is_active = ?
                    ORDER BY day_of_week, start_time
                """),
                (gym_id, True),
            )
            return [GymClassRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_gym_and_day(gym_id: int, day_of_week: int) -> list[dict[str, Any]]:
        """Get active classes for a gym on a specific day."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT * FROM gym_classes
                    WHERE gym_id = ? AND day_of_week = ? AND is_active = ?
                    ORDER BY start_time
                """),
                (gym_id, day_of_week, True),
            )
            return [GymClassRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def update(class_id: int, **kwargs) -> dict[str, Any] | None:
        """Update a gym class entry."""
        allowed = {
            "day_of_week",
            "start_time",
            "end_time",
            "class_name",
            "class_type",
            "level",
            "is_active",
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return GymClassRepository._get_by_id(class_id)

        with get_connection() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join(f"{f} = ?" for f in fields)
            values = list(fields.values())
            values.append(class_id)
            cursor.execute(
                convert_query(
                    f"UPDATE gym_classes SET {set_clause},"
                    " updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                ),
                values,
            )
            if cursor.rowcount == 0:
                return None
            return GymClassRepository._get_by_id(class_id)

    @staticmethod
    def delete(class_id: int) -> bool:
        """Delete a gym class entry."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM gym_classes WHERE id = ?"),
                (class_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def bulk_replace(gym_id: int, classes: list[dict]) -> list[int]:
        """Replace all classes for a gym with a new set.

        Deletes existing classes and inserts new ones atomically.
        Returns list of new class IDs.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM gym_classes WHERE gym_id = ?"),
                (gym_id,),
            )
            ids = []
            for cls in classes:
                new_id = execute_insert(
                    cursor,
                    convert_query("""
                        INSERT INTO gym_classes
                        (gym_id, day_of_week, start_time, end_time,
                         class_name, class_type, level)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """),
                    (
                        gym_id,
                        cls["day_of_week"],
                        cls["start_time"],
                        cls["end_time"],
                        cls["class_name"],
                        cls.get("class_type"),
                        cls.get("level"),
                    ),
                )
                ids.append(new_id)
            return ids

    @staticmethod
    def _get_by_id(class_id: int) -> dict[str, Any] | None:
        """Get a single class by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM gym_classes WHERE id = ?"),
                (class_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return GymClassRepository._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        """Convert a database row to a dictionary."""
        d = dict(row)
        d["day_name"] = DAY_NAMES[d["day_of_week"]]
        return d
