"""Service layer for technique management."""

from datetime import date

from rivaflow.cache import CacheKeys, get_redis_client
from rivaflow.db.repositories import TechniqueRepository


class TechniqueService:
    """Business logic for technique tracking."""

    def __init__(self):
        self.repo = TechniqueRepository()
        self.cache = get_redis_client()

    def add_technique(self, user_id: int, name: str, category: str | None = None) -> int:
        """
        Add a new technique or get existing one.
        Returns technique ID.
        """
        technique_id = self.repo.create(name=name, category=category)

        # Invalidate technique cache
        self._invalidate_technique_cache()

        return technique_id

    def get_technique(self, user_id: int, technique_id: int) -> dict | None:
        """Get a technique by ID."""
        # Try cache
        cache_key = CacheKeys.technique_by_id(technique_id)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        technique = self.repo.get_by_id(technique_id)

        # Cache for 24 hours
        if technique:
            self.cache.set(cache_key, technique, ttl=CacheKeys.TTL_24_HOURS)

        return technique

    def get_technique_by_name(self, user_id: int, name: str) -> dict | None:
        """Get a technique by name."""
        # Try cache
        cache_key = CacheKeys.technique_by_name(name)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        technique = self.repo.get_by_name(name)

        # Cache for 24 hours
        if technique:
            self.cache.set(cache_key, technique, ttl=CacheKeys.TTL_24_HOURS)

        return technique

    def list_all_techniques(self, user_id: int) -> list[dict]:
        """Get all techniques."""
        # Try cache
        cache_key = CacheKeys.TECHNIQUES_ALL
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        techniques = self.repo.list_all()

        # Cache for 24 hours
        self.cache.set(cache_key, techniques, ttl=CacheKeys.TTL_24_HOURS)

        return techniques

    def get_stale_techniques(self, user_id: int, days: int = 7) -> list[dict]:
        """Get techniques not trained in N days."""
        return self.repo.get_stale(days)

    def search_techniques(self, user_id: int, query: str) -> list[dict]:
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

    def calculate_days_since_trained(self, technique: dict) -> int | None:
        """Calculate days since technique was last trained."""
        if not technique.get("last_trained_date"):
            return None

        return (date.today() - technique["last_trained_date"]).days

    def _invalidate_technique_cache(self) -> None:
        """Invalidate all technique-related cache."""
        self.cache.delete_pattern(CacheKeys.PATTERN_ALL_TECHNIQUES)
