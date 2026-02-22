"""Repository for monthly training goals data access."""

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository


class TrainingGoalRepository(BaseRepository):
    """Data access layer for monthly training goals."""

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert database row to dictionary."""
        if not row:
            return {}
        data = dict(row)
        if "id" in data and data["id"] is not None:
            data["id"] = int(data["id"])
        if "user_id" in data and data["user_id"] is not None:
            data["user_id"] = int(data["user_id"])
        if "target_value" in data and data["target_value"] is not None:
            data["target_value"] = int(data["target_value"])
        if "movement_id" in data and data["movement_id"] is not None:
            data["movement_id"] = int(data["movement_id"])
        # Normalize is_active to bool
        if "is_active" in data:
            data["is_active"] = bool(data["is_active"])
        return data

    def create(
        self,
        user_id: int,
        goal_type: str,
        metric: str,
        target_value: int,
        month: str,
        movement_id: int | None = None,
        class_type_filter: str | None = None,
    ) -> int:
        """Create a new training goal. Returns the goal ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """
                INSERT INTO training_goals
                (user_id, goal_type, metric, target_value, month,
                 movement_id, class_type_filter)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    goal_type,
                    metric,
                    target_value,
                    month,
                    movement_id,
                    class_type_filter,
                ),
            )

    def get_by_id(self, goal_id: int, user_id: int) -> dict | None:
        """Get a training goal by ID, scoped to user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT tg.*, mg.name as movement_name
                FROM training_goals tg
                LEFT JOIN movements_glossary mg ON tg.movement_id = mg.id
                WHERE tg.id = ? AND tg.user_id = ?
                """),
                (goal_id, user_id),
            )
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None

    def list_by_month(self, user_id: int, month: str) -> list[dict]:
        """List all goals for a user in a given month."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT tg.*, mg.name as movement_name
                FROM training_goals tg
                LEFT JOIN movements_glossary mg ON tg.movement_id = mg.id
                WHERE tg.user_id = ? AND tg.month = ?
                ORDER BY tg.created_at ASC
                """),
                (user_id, month),
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def update(
        self,
        goal_id: int,
        user_id: int,
        target_value: int | None = None,
        is_active: bool | None = None,
    ) -> dict | None:
        """Update a training goal. Returns updated goal or None."""
        updates = []
        params = []

        if target_value is not None:
            updates.append("target_value = ?")
            params.append(target_value)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)

        if not updates:
            return self.get_by_id(goal_id, user_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([goal_id, user_id])

        with get_connection() as conn:
            cursor = conn.cursor()
            query = f"UPDATE training_goals SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
            cursor.execute(convert_query(query), params)

            if cursor.rowcount == 0:
                return None

        return self.get_by_id(goal_id, user_id)

    def delete(self, goal_id: int, user_id: int) -> bool:
        """Delete a training goal. Returns True if deleted."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "DELETE FROM training_goals WHERE id = ? AND user_id = ?"
                ),
                (goal_id, user_id),
            )
            return cursor.rowcount > 0
