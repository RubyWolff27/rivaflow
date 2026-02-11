"""Repository for groups data access."""

from rivaflow.db.database import convert_query, execute_insert, get_connection


class GroupsRepository:
    """Data access layer for groups and group members."""

    @staticmethod
    def create(user_id: int, data: dict) -> int:
        """Create a new group and add creator as admin member.

        Args:
            user_id: ID of the user creating the group.
            data: Dict with name, description, group_type, privacy, gym_id,
                  avatar_url.

        Returns:
            The ID of the newly created group.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            group_id = execute_insert(
                cursor,
                """
                INSERT INTO groups
                (name, description, group_type, privacy, gym_id, created_by,
                 avatar_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data.get("name"),
                    data.get("description"),
                    data.get("group_type", "training_crew"),
                    data.get("privacy", "invite_only"),
                    data.get("gym_id"),
                    user_id,
                    data.get("avatar_url"),
                ),
            )

            # Add creator as admin member
            execute_insert(
                cursor,
                """
                INSERT INTO group_members (group_id, user_id, role)
                VALUES (?, ?, ?)
                """,
                (group_id, user_id, "admin"),
            )

            return group_id

    @staticmethod
    def get_by_id(group_id: int) -> dict | None:
        """Get a group by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM groups WHERE id = ?"),
                (group_id,),
            )
            row = cursor.fetchone()
            return GroupsRepository._row_to_dict(row) if row else None

    @staticmethod
    def list_by_user(user_id: int) -> list[dict]:
        """List all groups a user belongs to."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT g.*, gm.role as member_role
                    FROM groups g
                    JOIN group_members gm ON g.id = gm.group_id
                    WHERE gm.user_id = ?
                    ORDER BY g.created_at DESC
                    """),
                (user_id,),
            )
            rows = cursor.fetchall()
            return [GroupsRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def add_member(group_id: int, user_id: int, role: str = "member") -> bool:
        """Add a member to a group.

        Returns True if added, False if already exists.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                execute_insert(
                    cursor,
                    """
                    INSERT INTO group_members (group_id, user_id, role)
                    VALUES (?, ?, ?)
                    """,
                    (group_id, user_id, role),
                )
                return True
            except Exception:
                return False

    @staticmethod
    def remove_member(group_id: int, user_id: int) -> bool:
        """Remove a member from a group. Returns True if removed."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "DELETE FROM group_members" " WHERE group_id = ? AND user_id = ?"
                ),
                (group_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_members(group_id: int) -> list[dict]:
        """Get all members of a group with user details."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT gm.id, gm.group_id, gm.user_id, gm.role,
                           gm.joined_at, u.first_name, u.last_name, u.email
                    FROM group_members gm
                    JOIN users u ON gm.user_id = u.id
                    WHERE gm.group_id = ?
                    ORDER BY gm.role DESC, gm.joined_at ASC
                    """),
                (group_id,),
            )
            rows = cursor.fetchall()
            return [GroupsRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def get_member_role(group_id: int, user_id: int) -> str | None:
        """Get the role of a user in a group.

        Returns None if not a member.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT role FROM group_members"
                    " WHERE group_id = ? AND user_id = ?"
                ),
                (group_id, user_id),
            )
            row = cursor.fetchone()
            if row:
                return dict(row).get("role")
            return None

    @staticmethod
    def update(group_id: int, user_id: int, data: dict) -> bool:
        """Update a group. Only admins can update.

        Returns True if updated.
        """
        role = GroupsRepository.get_member_role(group_id, user_id)
        if role != "admin":
            return False

        with get_connection() as conn:
            cursor = conn.cursor()

            updates = []
            params: list = []

            for field in [
                "name",
                "description",
                "group_type",
                "privacy",
                "gym_id",
                "avatar_url",
            ]:
                if field in data and data[field] is not None:
                    updates.append(f"{field} = ?")
                    params.append(data[field])

            if not updates:
                return True

            params.append(group_id)
            query = f"UPDATE groups SET {', '.join(updates)}" " WHERE id = ?"
            cursor.execute(convert_query(query), params)
            return cursor.rowcount > 0

    @staticmethod
    def delete(group_id: int, user_id: int) -> bool:
        """Delete a group. Only the creator or admins can delete."""
        role = GroupsRepository.get_member_role(group_id, user_id)
        if role != "admin":
            return False

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM groups WHERE id = ?"),
                (group_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_member_count(group_id: int) -> int:
        """Get the number of members in a group."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT COUNT(*) as cnt FROM group_members" " WHERE group_id = ?"
                ),
                (group_id,),
            )
            row = cursor.fetchone()
            return dict(row).get("cnt", 0) if row else 0

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a database row to a dictionary."""
        if not row:
            return {}

        data = dict(row)

        if "id" in data and data["id"] is not None:
            data["id"] = int(data["id"])
        if "group_id" in data and data["group_id"] is not None:
            data["group_id"] = int(data["group_id"])
        if "user_id" in data and data["user_id"] is not None:
            data["user_id"] = int(data["user_id"])
        if "created_by" in data and data["created_by"] is not None:
            data["created_by"] = int(data["created_by"])
        if "gym_id" in data and data["gym_id"] is not None:
            data["gym_id"] = int(data["gym_id"])

        return data
