"""Repository for game plan node data access."""

from rivaflow.db.database import convert_query, execute_insert, get_connection


class GamePlanNodeRepository:
    """Data access layer for game plan nodes."""

    @staticmethod
    def create(
        plan_id: int,
        name: str,
        node_type: str = "technique",
        parent_id: int | None = None,
        glossary_id: int | None = None,
        confidence: int = 1,
        priority: str = "normal",
        sort_order: int = 0,
        notes: str | None = None,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """INSERT INTO game_plan_nodes
                (plan_id, parent_id, name, node_type,
                 glossary_id, confidence, priority,
                 sort_order, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    plan_id,
                    parent_id,
                    name,
                    node_type,
                    glossary_id,
                    confidence,
                    priority,
                    sort_order,
                    notes,
                ),
            )

    @staticmethod
    def bulk_create(nodes: list[dict]) -> list[int]:
        ids = []
        with get_connection() as conn:
            cursor = conn.cursor()
            for node in nodes:
                node_id = execute_insert(
                    cursor,
                    """INSERT INTO game_plan_nodes
                    (plan_id, parent_id, name, node_type,
                     glossary_id, confidence, priority,
                     sort_order, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        node["plan_id"],
                        node.get("parent_id"),
                        node["name"],
                        node.get("node_type", "technique"),
                        node.get("glossary_id"),
                        node.get("confidence", 1),
                        node.get("priority", "normal"),
                        node.get("sort_order", 0),
                        node.get("notes"),
                    ),
                )
                ids.append(node_id)
        return ids

    @staticmethod
    def get_by_id(node_id: int, plan_id: int) -> dict | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM game_plan_nodes" " WHERE id = ? AND plan_id = ?"
                ),
                (node_id, plan_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_by_plan(plan_id: int) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM game_plan_nodes"
                    " WHERE plan_id = ?"
                    " ORDER BY sort_order, name"
                ),
                (plan_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_focus_nodes(plan_id: int) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM game_plan_nodes"
                    " WHERE plan_id = ? AND is_focus = 1"
                    " ORDER BY sort_order"
                ),
                (plan_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def update(node_id: int, plan_id: int, **kwargs) -> dict | None:
        valid_fields = {
            "name",
            "node_type",
            "glossary_id",
            "confidence",
            "priority",
            "is_focus",
            "attempts",
            "successes",
            "last_used_date",
            "sort_order",
            "notes",
            "parent_id",
        }
        updates = []
        params = []
        for field, value in kwargs.items():
            if field in valid_fields:
                updates.append(f"{field} = ?")
                params.append(value)
        if not updates:
            return GamePlanNodeRepository.get_by_id(node_id, plan_id)
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([node_id, plan_id])
        with get_connection() as conn:
            cursor = conn.cursor()
            query = (
                "UPDATE game_plan_nodes"
                f" SET {', '.join(updates)}"
                " WHERE id = ? AND plan_id = ?"
            )
            cursor.execute(convert_query(query), params)
            if cursor.rowcount == 0:
                return None
            return GamePlanNodeRepository.get_by_id(node_id, plan_id)

    @staticmethod
    def increment_usage(node_id: int, plan_id: int, success: bool = False) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            if success:
                cursor.execute(
                    convert_query(
                        "UPDATE game_plan_nodes"
                        " SET attempts = attempts + 1,"
                        " successes = successes + 1,"
                        " last_used_date = date('now'),"
                        " updated_at = CURRENT_TIMESTAMP"
                        " WHERE id = ? AND plan_id = ?"
                    ),
                    (node_id, plan_id),
                )
            else:
                cursor.execute(
                    convert_query(
                        "UPDATE game_plan_nodes"
                        " SET attempts = attempts + 1,"
                        " last_used_date = date('now'),"
                        " updated_at = CURRENT_TIMESTAMP"
                        " WHERE id = ? AND plan_id = ?"
                    ),
                    (node_id, plan_id),
                )

    @staticmethod
    def delete(node_id: int, plan_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "DELETE FROM game_plan_nodes" " WHERE id = ? AND plan_id = ?"
                ),
                (node_id, plan_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def set_focus_nodes(plan_id: int, node_ids: list[int]) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Clear all focus
            cursor.execute(
                convert_query(
                    "UPDATE game_plan_nodes"
                    " SET is_focus = 0,"
                    " updated_at = CURRENT_TIMESTAMP"
                    " WHERE plan_id = ?"
                ),
                (plan_id,),
            )
            # Set new focus (max 5)
            for nid in node_ids[:5]:
                cursor.execute(
                    convert_query(
                        "UPDATE game_plan_nodes"
                        " SET is_focus = 1,"
                        " updated_at = CURRENT_TIMESTAMP"
                        " WHERE id = ? AND plan_id = ?"
                    ),
                    (nid, plan_id),
                )
