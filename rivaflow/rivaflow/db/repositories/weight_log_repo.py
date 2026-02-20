"""Repository for weight log data access."""

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository


class WeightLogRepository(BaseRepository):
    """Data access layer for weight logs."""

    @staticmethod
    def create(user_id: int, data: dict) -> int:
        """Create a new weight log entry. Returns the log ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            log_id = execute_insert(
                cursor,
                """
                INSERT INTO weight_logs
                (user_id, weight, logged_date, time_of_day, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    data["weight"],
                    data.get("logged_date"),
                    data.get("time_of_day"),
                    data.get("notes"),
                ),
            )
            return log_id

    @staticmethod
    def list_by_user(
        user_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        """List weight logs for a user, optionally filtered by date range."""
        with get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM weight_logs WHERE user_id = ?"
            params: list = [user_id]

            if start_date:
                query += " AND logged_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND logged_date <= ?"
                params.append(end_date)

            query += " ORDER BY logged_date DESC, created_at DESC"

            cursor.execute(convert_query(query), params)
            rows = cursor.fetchall()
            return [WeightLogRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def get_latest(user_id: int) -> dict | None:
        """Get the most recent weight log for a user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM weight_logs WHERE user_id = ? "
                    "ORDER BY logged_date DESC, created_at DESC LIMIT 1"
                ),
                (user_id,),
            )
            row = cursor.fetchone()
            return WeightLogRepository._row_to_dict(row) if row else None

    @staticmethod
    def get_averages(user_id: int, period: str = "weekly") -> list[dict]:
        """Get weight averages grouped by period (weekly or monthly)."""
        with get_connection() as conn:
            cursor = conn.cursor()

            if period == "monthly":
                group_expr = "strftime('%Y-%m', logged_date)"
            else:
                # weekly: group by ISO week
                group_expr = "strftime('%Y-W%W', logged_date)"

            query = f"""
                SELECT
                    {group_expr} AS period,
                    ROUND(AVG(weight), 2) AS avg_weight,
                    ROUND(MIN(weight), 2) AS min_weight,
                    ROUND(MAX(weight), 2) AS max_weight,
                    COUNT(*) AS entries
                FROM weight_logs
                WHERE user_id = ?
                GROUP BY {group_expr}
                ORDER BY period DESC
                LIMIT 52
            """
            cursor.execute(convert_query(query), (user_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a database row to a dictionary."""
        if not row:
            return {}
        data = dict(row)
        if "id" in data and data["id"] is not None:
            data["id"] = int(data["id"])
        if "user_id" in data and data["user_id"] is not None:
            data["user_id"] = int(data["user_id"])
        if "weight" in data and data["weight"] is not None:
            data["weight"] = float(data["weight"])
        return data
