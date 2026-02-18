"""Repository for coach preferences data access."""

import json

from rivaflow.db.database import convert_query, get_connection

JSON_FIELDS = ("focus_areas", "injuries", "motivations")


class CoachPreferencesRepository:
    """Data access layer for coach preferences."""

    @staticmethod
    def get(user_id: int) -> dict | None:
        """Get coach preferences for a user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM coach_preferences WHERE user_id = ?"),
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return CoachPreferencesRepository._row_to_dict(row)

    @staticmethod
    def upsert(user_id: int, **fields) -> dict:
        """Create or update coach preferences. Returns the saved record."""
        # Serialize JSON fields
        for key in JSON_FIELDS:
            if key in fields and fields[key] is not None:
                if isinstance(fields[key], (list, dict)):
                    fields[key] = json.dumps(fields[key])

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT id FROM coach_preferences WHERE user_id = ?"),
                (user_id,),
            )
            existing = cursor.fetchone()

            if existing:
                # Build dynamic UPDATE
                set_parts = []
                values = []
                for key, value in fields.items():
                    if key in ("id", "user_id", "created_at"):
                        continue
                    set_parts.append(f"{key} = ?")
                    values.append(value)
                if set_parts:
                    set_parts.append("updated_at = CURRENT_TIMESTAMP")
                    values.append(user_id)
                    sql = (
                        "UPDATE coach_preferences SET "
                        + ", ".join(set_parts)
                        + " WHERE user_id = ?"
                    )
                    cursor.execute(convert_query(sql), values)
            else:
                # INSERT new row
                fields["user_id"] = user_id
                columns = list(fields.keys())
                placeholders = ", ".join(["?"] * len(columns))
                col_str = ", ".join(columns)
                sql = (
                    f"INSERT INTO coach_preferences ({col_str}) VALUES ({placeholders})"
                )
                cursor.execute(convert_query(sql), [fields[c] for c in columns])

        return CoachPreferencesRepository.get(user_id)  # type: ignore[return-value]

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a database row to a dict with JSON deserialization."""
        d = dict(row)

        # Deserialize JSON fields
        for key in JSON_FIELDS:
            if key in d and isinstance(d[key], str):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    d[key] = []
            elif key in d and d[key] is None:
                d[key] = []

        return d
