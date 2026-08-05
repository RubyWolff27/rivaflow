"""Repository for the belt-curriculum tracker (slots, evidence, sign-offs, meta).

Deliberately has NO write path for slot status — status is derived on read by
``rivaflow.core.services.curriculum_service``. The tables carry no status column
for a route to set.
"""

from typing import Any

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository

# Columns a caller is allowed to edit on an existing slot. Everything else
# (user_id, block, requirement_key, slot_index) is structural and fixed at seed.
EDITABLE_SLOT_FIELDS = (
    "seq_entry",
    "seq_position",
    "seq_finish",
    "game_tag",
    "movement_ids",
    "is_draft",
    "tension_note",
    "blocker_note",
)


class CurriculumRepository(BaseRepository):
    """Data access layer for the curriculum module."""

    # ---------------------------------------------------------------- slots

    @staticmethod
    def create_slot(user_id: int, data: dict) -> int:
        """Insert a slot and return its id."""
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """
                INSERT INTO curriculum_slot
                (user_id, belt, block, requirement_key, requirement_label,
                 slot_index, of_choice, seq_entry, seq_position, seq_finish,
                 game_tag, movement_ids, is_draft, tension_note, blocker_note,
                 declared_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    data.get("belt", "purple"),
                    data["block"],
                    data["requirement_key"],
                    data.get("requirement_label"),
                    data["slot_index"],
                    data.get("of_choice", True),
                    data.get("seq_entry"),
                    data.get("seq_position"),
                    data.get("seq_finish"),
                    data.get("game_tag"),
                    data.get("movement_ids"),
                    data.get("is_draft", False),
                    data.get("tension_note"),
                    data.get("blocker_note"),
                    data.get("declared_at"),
                ),
            )

    @staticmethod
    def get_slot(slot_id: int, user_id: int) -> dict | None:
        """Fetch one slot, scoped to its owner."""
        return CurriculumRepository._fetchone(
            "SELECT * FROM curriculum_slot WHERE id = ? AND user_id = ?",
            (slot_id, user_id),
        )

    @staticmethod
    def list_slots(user_id: int, belt: str = "purple") -> list[dict]:
        """All slots for a user's belt, in syllabus order."""
        return CurriculumRepository._fetchall(
            """
            SELECT * FROM curriculum_slot
            WHERE user_id = ? AND belt = ?
            ORDER BY block, requirement_key, slot_index
            """,
            (user_id, belt),
        )

    @staticmethod
    def update_slot(slot_id: int, user_id: int, fields: dict) -> bool:
        """Update the editable fields of a slot. Returns True when a row changed."""
        updates = {k: v for k, v in fields.items() if k in EDITABLE_SLOT_FIELDS}
        if not updates:
            return False

        set_clause = ", ".join(f"{col} = ?" for col in updates)
        params: list[Any] = list(updates.values())
        params.extend([slot_id, user_id])
        cursor = CurriculumRepository._execute(
            f"UPDATE curriculum_slot SET {set_clause} WHERE id = ? AND user_id = ?",
            tuple(params),
        )
        return cursor.rowcount > 0

    @staticmethod
    def mark_declared(slot_id: int, user_id: int, declared_at: str) -> None:
        """Stamp declared_at the first time a slot gets a sequence."""
        CurriculumRepository._execute(
            """
            UPDATE curriculum_slot SET declared_at = ?
            WHERE id = ? AND user_id = ? AND declared_at IS NULL
            """,
            (declared_at, slot_id, user_id),
        )

    # ------------------------------------------------------------- evidence

    @staticmethod
    def create_evidence(user_id: int, slot_id: int, data: dict) -> int:
        """Insert one evidence row and return its id."""
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """
                INSERT INTO curriculum_slot_evidence
                (slot_id, user_id, session_id, kind, partner_ref,
                 partner_rank_band, partner_size, note, logged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    slot_id,
                    user_id,
                    data.get("session_id"),
                    data["kind"],
                    data.get("partner_ref"),
                    data.get("partner_rank_band"),
                    data.get("partner_size"),
                    data.get("note"),
                    data["logged_at"],
                ),
            )

    @staticmethod
    def list_evidence(user_id: int, belt: str = "purple") -> list[dict]:
        """Every evidence row for a user's belt, oldest first."""
        return CurriculumRepository._fetchall(
            """
            SELECT e.* FROM curriculum_slot_evidence e
            JOIN curriculum_slot s ON s.id = e.slot_id
            WHERE e.user_id = ? AND s.belt = ?
            ORDER BY e.logged_at, e.id
            """,
            (user_id, belt),
        )

    # ------------------------------------------------------------- signoffs

    @staticmethod
    def create_signoff(user_id: int, slot_id: int, data: dict) -> int:
        """Insert one sign-off row and return its id.

        There is no update or delete counterpart — sign-offs are immutable
        attributed records of what a coach actually said.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """
                INSERT INTO curriculum_slot_signoff
                (slot_id, user_id, verdict, coach_name, coach_rank, note)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    slot_id,
                    user_id,
                    data["verdict"],
                    data["coach_name"],
                    data.get("coach_rank"),
                    data.get("note"),
                ),
            )

    @staticmethod
    def list_signoffs(user_id: int, belt: str = "purple") -> list[dict]:
        """Every sign-off for a user's belt, oldest first."""
        return CurriculumRepository._fetchall(
            """
            SELECT g.* FROM curriculum_slot_signoff g
            JOIN curriculum_slot s ON s.id = g.slot_id
            WHERE g.user_id = ? AND s.belt = ?
            ORDER BY g.created_at, g.id
            """,
            (user_id, belt),
        )

    # ----------------------------------------------------------------- meta

    @staticmethod
    def get_meta(user_id: int, belt: str = "purple") -> dict | None:
        """Hard-gate row for a user's belt, if one exists."""
        return CurriculumRepository._fetchone(
            "SELECT * FROM curriculum_meta WHERE user_id = ? AND belt = ?",
            (user_id, belt),
        )

    @staticmethod
    def upsert_meta(user_id: int, belt: str, fields: dict) -> None:
        """Create or update the hard-gate row for a user's belt."""
        existing = CurriculumRepository.get_meta(user_id, belt)
        allowed = (
            "competition_date",
            "competition_note",
            "classes_logged",
            "stripes",
            "notes",
        )
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return

        if existing:
            set_clause = ", ".join(f"{col} = ?" for col in updates)
            params: list[Any] = list(updates.values())
            params.extend([user_id, belt])
            CurriculumRepository._execute(
                f"UPDATE curriculum_meta SET {set_clause} "
                f"WHERE user_id = ? AND belt = ?",
                tuple(params),
            )
            return

        cols = ", ".join(updates)
        placeholders = ", ".join("?" for _ in updates)
        CurriculumRepository._execute(
            f"INSERT INTO curriculum_meta (user_id, belt, {cols}) "
            f"VALUES (?, ?, {placeholders})",
            (user_id, belt, *updates.values()),
        )

    @staticmethod
    def count_slots(user_id: int, belt: str = "purple") -> int:
        """How many slots the user already has seeded for this belt."""
        row = CurriculumRepository._fetchone(
            "SELECT COUNT(*) AS n FROM curriculum_slot WHERE user_id = ? AND belt = ?",
            (user_id, belt),
        )
        return int(row["n"]) if row else 0

    @staticmethod
    def bulk_create_slots(user_id: int, rows: list[dict]) -> int:
        """Insert many slots in one connection. Returns the number inserted."""
        if not rows:
            return 0
        with get_connection() as conn:
            cursor = conn.cursor()
            for data in rows:
                cursor.execute(
                    convert_query("""
                        INSERT INTO curriculum_slot
                        (user_id, belt, block, requirement_key, requirement_label,
                         slot_index, of_choice, seq_entry, seq_position, seq_finish,
                         game_tag, movement_ids, is_draft, tension_note,
                         blocker_note, declared_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """),
                    (
                        user_id,
                        data.get("belt", "purple"),
                        data["block"],
                        data["requirement_key"],
                        data.get("requirement_label"),
                        data["slot_index"],
                        data.get("of_choice", True),
                        data.get("seq_entry"),
                        data.get("seq_position"),
                        data.get("seq_finish"),
                        data.get("game_tag"),
                        data.get("movement_ids"),
                        data.get("is_draft", False),
                        data.get("tension_note"),
                        data.get("blocker_note"),
                        data.get("declared_at"),
                    ),
                )
            conn.commit()
            return len(rows)
