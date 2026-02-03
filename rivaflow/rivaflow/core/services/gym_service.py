"""Service layer for gym management with caching."""
from typing import List, Dict, Any, Optional

from rivaflow.db.repositories.gym_repo import GymRepository
from rivaflow.cache import get_redis_client, CacheKeys


class GymService:
    """Business logic for gym operations with Redis caching."""

    def __init__(self):
        self.repo = GymRepository()
        self.cache = get_redis_client()

    def create(
        self,
        name: str,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: str = "Australia",
        address: Optional[str] = None,
        website: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        head_coach: Optional[str] = None,
        head_coach_belt: Optional[str] = None,
        google_maps_url: Optional[str] = None,
        verified: bool = False,
        added_by_user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new gym."""
        gym = self.repo.create(
            name=name,
            city=city,
            state=state,
            country=country,
            address=address,
            website=website,
            email=email,
            phone=phone,
            head_coach=head_coach,
            head_coach_belt=head_coach_belt,
            google_maps_url=google_maps_url,
            verified=verified,
            added_by_user_id=added_by_user_id,
        )

        # Invalidate gym directory cache
        self._invalidate_gym_cache()

        return gym

    def get_by_id(self, gym_id: int) -> Optional[Dict[str, Any]]:
        """Get a gym by ID."""
        # Try cache
        cache_key = CacheKeys.gym_by_id(gym_id)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        gym = self.repo.get_by_id(gym_id)

        # Cache for 1 hour
        if gym:
            self.cache.set(cache_key, gym, ttl=CacheKeys.TTL_1_HOUR)

        return gym

    def list_all(self, verified_only: bool = False) -> List[Dict[str, Any]]:
        """List all gyms."""
        # Try cache
        cache_key = CacheKeys.GYM_DIRECTORY_VERIFIED if verified_only else CacheKeys.GYM_DIRECTORY_ALL
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        gyms = self.repo.list_all(verified_only=verified_only)

        # Cache for 1 hour
        self.cache.set(cache_key, gyms, ttl=CacheKeys.TTL_1_HOUR)

        return gyms

    def search(self, query: str, verified_only: bool = False) -> List[Dict[str, Any]]:
        """Search gyms by name or location."""
        # Try cache
        cache_key = CacheKeys.gym_search(query, verified_only=verified_only)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        gyms = self.repo.search(query, verified_only=verified_only)

        # Cache for 1 hour
        self.cache.set(cache_key, gyms, ttl=CacheKeys.TTL_1_HOUR)

        return gyms

    def update(self, gym_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a gym."""
        gym = self.repo.update(gym_id, **kwargs)

        # Invalidate gym cache
        if gym:
            self._invalidate_gym_cache(gym_id)

        return gym

    def delete(self, gym_id: int) -> bool:
        """Delete a gym."""
        deleted = self.repo.delete(gym_id)

        # Invalidate gym cache
        if deleted:
            self._invalidate_gym_cache(gym_id)

        return deleted

    def get_pending_gyms(self) -> List[Dict[str, Any]]:
        """Get all unverified (user-added) gyms."""
        # Don't cache pending gyms (changes frequently)
        return self.repo.get_pending_gyms()

    def merge_gyms(self, source_gym_id: int, target_gym_id: int) -> bool:
        """Merge two gyms."""
        merged = self.repo.merge_gyms(source_gym_id, target_gym_id)

        # Invalidate gym cache for both gyms
        if merged:
            self._invalidate_gym_cache(source_gym_id)
            self._invalidate_gym_cache(target_gym_id)

        return merged

    def _invalidate_gym_cache(self, gym_id: Optional[int] = None) -> None:
        """
        Invalidate gym-related cache.

        Args:
            gym_id: If provided, invalidate specific gym cache. Otherwise, invalidate all.
        """
        if gym_id:
            # Invalidate specific gym cache
            self.cache.delete_pattern(CacheKeys.pattern_gym(gym_id))

        # Always invalidate directory and search caches
        self.cache.delete_pattern(CacheKeys.PATTERN_ALL_GYMS)
