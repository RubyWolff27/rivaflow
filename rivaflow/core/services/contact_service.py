"""Service layer for contacts (training partners and instructors) operations."""
from typing import List, Optional

from rivaflow.db.repositories import ContactRepository


class ContactService:
    """Business logic for contacts."""

    def __init__(self):
        self.repo = ContactRepository()

    def create_contact(
        self,
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
        return self.repo.create(
            name=name,
            contact_type=contact_type,
            belt_rank=belt_rank,
            belt_stripes=belt_stripes,
            instructor_certification=instructor_certification,
            phone=phone,
            email=email,
            notes=notes,
        )

    def get_contact(self, contact_id: int) -> Optional[dict]:
        """Get a contact by ID."""
        return self.repo.get_by_id(contact_id)

    def get_contact_by_name(self, name: str) -> Optional[dict]:
        """Get a contact by exact name match."""
        return self.repo.get_by_name(name)

    def list_contacts(self, order_by: str = "name ASC") -> List[dict]:
        """Get all contacts."""
        return self.repo.list_all(order_by=order_by)

    def list_instructors(self) -> List[dict]:
        """Get all contacts who are instructors."""
        instructors = self.repo.list_by_type("instructor", order_by="name ASC")
        both = self.repo.list_by_type("both", order_by="name ASC")
        return instructors + both

    def list_training_partners(self) -> List[dict]:
        """Get all contacts who are training partners."""
        partners = self.repo.list_by_type("training-partner", order_by="name ASC")
        both = self.repo.list_by_type("both", order_by="name ASC")
        return partners + both

    def search_contacts(self, query: str) -> List[dict]:
        """Search contacts by name."""
        return self.repo.search(query)

    def update_contact(
        self,
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
        """Update a contact."""
        return self.repo.update(
            contact_id=contact_id,
            name=name,
            contact_type=contact_type,
            belt_rank=belt_rank,
            belt_stripes=belt_stripes,
            instructor_certification=instructor_certification,
            phone=phone,
            email=email,
            notes=notes,
        )

    def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact."""
        return self.repo.delete(contact_id)

    def format_belt_display(self, contact: dict) -> str:
        """Format belt rank and stripes for display."""
        if not contact.get("belt_rank"):
            return "Unranked"

        rank = contact["belt_rank"].title()
        stripes = contact.get("belt_stripes", 0)

        if stripes > 0:
            return f"{rank} Belt ({stripes} stripe{'s' if stripes > 1 else ''})"
        return f"{rank} Belt"
