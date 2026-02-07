"""Repository for game plan data access."""

from rivaflow.db.database import convert_query, execute_insert, get_connection


class GamePlanRepository:
    """Data access layer for game plans."""

    @staticmethod
    def create(
        user_id: int,
        belt_level: str,
        archetype: str,
        style: str = "balanced",
        title: str | None = None,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """INSERT INTO game_plans
                (user_id, belt_level, archetype, style, title)
                VALUES (?, ?, ?, ?, ?)""",
                (user_id, belt_level, archetype, style, title),
            )

    @staticmethod
    def get_by_id(plan_id: int, user_id: int) -> dict | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM game_plans" " WHERE id = ? AND user_id = ?"
                ),
                (plan_id, user_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_active(user_id: int) -> dict | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM game_plans"
                    " WHERE user_id = ? AND is_active = ?"
                    " ORDER BY updated_at DESC LIMIT 1"
                ),
                (user_id, True),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_by_user(user_id: int) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM game_plans"
                    " WHERE user_id = ?"
                    " ORDER BY updated_at DESC"
                ),
                (user_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def update(plan_id: int, user_id: int, **kwargs) -> dict | None:
        valid_fields = {
            "belt_level",
            "archetype",
            "style",
            "title",
            "is_active",
        }
        updates = []
        params = []
        for field, value in kwargs.items():
            if field in valid_fields:
                updates.append(f"{field} = ?")
                params.append(value)
        if not updates:
            return GamePlanRepository.get_by_id(plan_id, user_id)
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([plan_id, user_id])
        with get_connection() as conn:
            cursor = conn.cursor()
            query = (
                f"UPDATE game_plans SET {', '.join(updates)}"
                " WHERE id = ? AND user_id = ?"
            )
            cursor.execute(convert_query(query), params)
            if cursor.rowcount == 0:
                return None
            return GamePlanRepository.get_by_id(plan_id, user_id)

    @staticmethod
    def delete(plan_id: int, user_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM game_plans" " WHERE id = ? AND user_id = ?"),
                (plan_id, user_id),
            )
            return cursor.rowcount > 0
