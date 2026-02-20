"""Repository for AI insight data access."""

import json

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository


class AIInsightRepository(BaseRepository):
    """Data access layer for AI-generated insights."""

    @staticmethod
    def create(
        user_id: int,
        insight_type: str,
        title: str,
        content: str,
        category: str = "observation",
        session_id: int | None = None,
        data: dict | None = None,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """INSERT INTO ai_insights
                (user_id, session_id, insight_type,
                 title, content, category, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    session_id,
                    insight_type,
                    title,
                    content,
                    category,
                    json.dumps(data) if data else None,
                ),
            )

    @staticmethod
    def get_by_id(insight_id: int, user_id: int) -> dict | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM ai_insights" " WHERE id = ? AND user_id = ?"
                ),
                (insight_id, user_id),
            )
            row = cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            if result.get("data"):
                try:
                    result["data"] = json.loads(result["data"])
                except (json.JSONDecodeError, TypeError):
                    result["data"] = None
            return result

    @staticmethod
    def list_by_user(
        user_id: int,
        limit: int = 20,
        insight_type: str | None = None,
    ) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            if insight_type:
                cursor.execute(
                    convert_query(
                        "SELECT * FROM ai_insights"
                        " WHERE user_id = ?"
                        " AND insight_type = ?"
                        " ORDER BY created_at DESC"
                        " LIMIT ?"
                    ),
                    (user_id, insight_type, limit),
                )
            else:
                cursor.execute(
                    convert_query(
                        "SELECT * FROM ai_insights"
                        " WHERE user_id = ?"
                        " ORDER BY created_at DESC"
                        " LIMIT ?"
                    ),
                    (user_id, limit),
                )
            results = []
            for row in cursor.fetchall():
                r = dict(row)
                if r.get("data"):
                    try:
                        r["data"] = json.loads(r["data"])
                    except (json.JSONDecodeError, TypeError):
                        r["data"] = None
                results.append(r)
            return results

    @staticmethod
    def get_latest(user_id: int) -> dict | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM ai_insights"
                    " WHERE user_id = ?"
                    " ORDER BY created_at DESC LIMIT 1"
                ),
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            if result.get("data"):
                try:
                    result["data"] = json.loads(result["data"])
                except (json.JSONDecodeError, TypeError):
                    result["data"] = None
            return result

    @staticmethod
    def update_data(insight_id: int, user_id: int, data: dict) -> bool:
        """Update the data JSON field of an insight."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "UPDATE ai_insights SET data = ?" " WHERE id = ? AND user_id = ?"
                ),
                (json.dumps(data), insight_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def mark_as_read(insight_id: int, user_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "UPDATE ai_insights SET is_read = 1" " WHERE id = ? AND user_id = ?"
                ),
                (insight_id, user_id),
            )
            return cursor.rowcount > 0
