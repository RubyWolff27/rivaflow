"""Repository for game plan edge data access."""

from rivaflow.db.database import convert_query, execute_insert, get_connection


class GamePlanEdgeRepository:
    """Data access layer for game plan edges."""

    @staticmethod
    def create(
        plan_id: int,
        from_node_id: int,
        to_node_id: int,
        edge_type: str = "transition",
        label: str | None = None,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """INSERT INTO game_plan_edges
                (plan_id, from_node_id, to_node_id,
                 edge_type, label)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    plan_id,
                    from_node_id,
                    to_node_id,
                    edge_type,
                    label,
                ),
            )

    @staticmethod
    def bulk_create(edges: list[dict]) -> list[int]:
        ids = []
        with get_connection() as conn:
            cursor = conn.cursor()
            for edge in edges:
                edge_id = execute_insert(
                    cursor,
                    """INSERT INTO game_plan_edges
                    (plan_id, from_node_id, to_node_id,
                     edge_type, label)
                    VALUES (?, ?, ?, ?, ?)""",
                    (
                        edge["plan_id"],
                        edge["from_node_id"],
                        edge["to_node_id"],
                        edge.get("edge_type", "transition"),
                        edge.get("label"),
                    ),
                )
                ids.append(edge_id)
        return ids

    @staticmethod
    def list_by_plan(plan_id: int) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM game_plan_edges" " WHERE plan_id = ? ORDER BY id"
                ),
                (plan_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def delete(edge_id: int, plan_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "DELETE FROM game_plan_edges" " WHERE id = ? AND plan_id = ?"
                ),
                (edge_id, plan_id),
            )
            return cursor.rowcount > 0
