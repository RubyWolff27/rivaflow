"""Service layer for technique management."""
from typing import Optional
from datetime import date

from rivaflow.db.repositories import TechniqueRepository


class TechniqueService:
    """Business logic for technique tracking."""

    def __init__(self):
        self.repo = TechniqueRepository()

    def add_technique(self, name: str, category: Optional[str] = None) -> int:
        """
        Add a new technique or get existing one.
        Returns technique ID.
        """
        return self.repo.create(name=name, category=category)

    def get_technique(self, technique_id: int) -> Optional[dict]:
        """Get a technique by ID."""
        return self.repo.get_by_id(technique_id)

    def get_technique_by_name(self, name: str) -> Optional[dict]:
        """Get a technique by name."""
        return self.repo.get_by_name(name)

    def list_all_techniques(self) -> list[dict]:
        """Get all techniques."""
        return self.repo.list_all()

    def get_stale_techniques(self, days: int = 7) -> list[dict]:
        """Get techniques not trained in N days."""
        return self.repo.get_stale(days)

    def search_techniques(self, query: str) -> list[dict]:
        """Search techniques by name."""
        return self.repo.search(query)

    def format_technique_summary(self, technique: dict) -> str:
        """Format a technique as a human-readable summary."""
        lines = [f"Technique: {technique['name']}"]

        if technique.get("category"):
            lines.append(f"  Category: {technique['category']}")

        if technique.get("last_trained_date"):
            lines.append(f"  Last trained: {technique['last_trained_date']}")
            days_ago = (date.today() - technique["last_trained_date"]).days
            lines.append(f"  Days since: {days_ago}")
        else:
            lines.append("  Last trained: Never")

        return "\n".join(lines)

    def calculate_days_since_trained(self, technique: dict) -> Optional[int]:
        """Calculate days since technique was last trained."""
        if not technique.get("last_trained_date"):
            return None

        return (date.today() - technique["last_trained_date"]).days
