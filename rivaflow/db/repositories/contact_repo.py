"""Repository for contacts (training partners and instructors) data access."""
import sqlite3
from typing import List, Optional

from rivaflow.db.database import get_connection


class ContactRepository:
    """Data access layer for contacts."""

    @staticmethod
    def create(
        name: str,
        contact_type: str = "training-partner",
        belt_rank: Optional[str] = None,
        belt_stripes: int = 0,
        instructor_certification: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """Create a new contact."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO contacts
                (name, contact_type, belt_rank, belt_stripes, instructor_certification, phone, email, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, contact_type, belt_rank, belt_stripes, instructor_certification, phone, email, notes),
            )
            contact_id = cursor.lastrowid

            # Return the created contact
            cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
            row = cursor.fetchone()
            return ContactRepository._row_to_dict(row)

    @staticmethod
    def get_by_id(contact_id: int) -> Optional[dict]:
        """Get a contact by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
            row = cursor.fetchone()
            return ContactRepository._row_to_dict(row) if row else None

    @staticmethod
    def get_by_name(name: str) -> Optional[dict]:
        """Get a contact by exact name match."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contacts WHERE name = ?", (name,))
            row = cursor.fetchone()
            return ContactRepository._row_to_dict(row) if row else None

    @staticmethod
    def list_all(order_by: str = "name ASC") -> List[dict]:
        """Get all contacts, ordered by name alphabetically by default."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM contacts ORDER BY {order_by}")
            rows = cursor.fetchall()
            return [ContactRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def list_by_type(contact_type: str, order_by: str = "name ASC") -> List[dict]:
        """Get contacts filtered by type."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM contacts WHERE contact_type = ? ORDER BY {order_by}",
                (contact_type,),
            )
            rows = cursor.fetchall()
            return [ContactRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def search(query: str) -> List[dict]:
        """Search contacts by name (case-insensitive partial match)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM contacts WHERE name LIKE ? ORDER BY name ASC",
                (f"%{query}%",),
            )
            rows = cursor.fetchall()
            return [ContactRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def update(
        contact_id: int,
        name: Optional[str] = None,
        contact_type: Optional[str] = None,
        belt_rank: Optional[str] = None,
        belt_stripes: Optional[int] = None,
        instructor_certification: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[dict]:
        """Update a contact by ID. Returns updated contact or None if not found."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if contact_type is not None:
                updates.append("contact_type = ?")
                params.append(contact_type)
            if belt_rank is not None:
                updates.append("belt_rank = ?")
                params.append(belt_rank)
            if belt_stripes is not None:
                updates.append("belt_stripes = ?")
                params.append(belt_stripes)
            if instructor_certification is not None:
                updates.append("instructor_certification = ?")
                params.append(instructor_certification)
            if phone is not None:
                updates.append("phone = ?")
                params.append(phone)
            if email is not None:
                updates.append("email = ?")
                params.append(email)
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)

            if not updates:
                # No updates provided, just return current record
                return ContactRepository.get_by_id(contact_id)

            # Add updated_at timestamp
            updates.append("updated_at = datetime('now')")
            params.append(contact_id)

            query = f"UPDATE contacts SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

            if cursor.rowcount == 0:
                return None

            return ContactRepository.get_by_id(contact_id)

    @staticmethod
    def delete(contact_id: int) -> bool:
        """Delete a contact by ID. Returns True if deleted, False if not found."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        if not row:
            return {}

        data = dict(row)

        # Convert integer to actual int (SQLite returns all as int already)
        if "id" in data and data["id"] is not None:
            data["id"] = int(data["id"])
        if "belt_stripes" in data and data["belt_stripes"] is not None:
            data["belt_stripes"] = int(data["belt_stripes"])

        return data
