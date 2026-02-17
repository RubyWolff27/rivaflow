"""Service layer for movements glossary operations."""

from rivaflow.cache import CacheKeys, get_redis_client
from rivaflow.db.repositories import GlossaryRepository


class GlossaryService:
    """Business logic for movements glossary."""

    def __init__(self):
        self.repo = GlossaryRepository()
        self.cache = get_redis_client()

    def list_movements(
        self,
        user_id: int,
        category: str | None = None,
        search: str | None = None,
        gi_only: bool = False,
        nogi_only: bool = False,
    ) -> list[dict]:
        """Get all movements with optional filtering."""
        # Skip cache for search queries (too many permutations)
        if search:
            return self.repo.list_all(
                category=category,
                search=search,
                gi_only=gi_only,
                nogi_only=nogi_only,
            )

        # Generate cache key based on filters
        cache_key = CacheKeys.movements_glossary_filtered(
            category=category,
            gi_only=gi_only,
            nogi_only=nogi_only,
        )

        # Try to get from cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        movements = self.repo.list_all(
            category=category,
            search=search,
            gi_only=gi_only,
            nogi_only=nogi_only,
        )

        # Cache for 24 hours
        self.cache.set(cache_key, movements, ttl=CacheKeys.TTL_24_HOURS)

        return movements

    def get_movement(
        self, user_id: int, movement_id: int, include_custom_videos: bool = False
    ) -> dict | None:
        """Get a specific movement by ID, optionally with custom video links."""
        # Skip cache if custom videos requested (user-specific)
        if include_custom_videos:
            return self.repo.get_by_id(movement_id, include_custom_videos=True)

        # Try cache
        cache_key = CacheKeys.movement_by_id(movement_id)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        movement = self.repo.get_by_id(movement_id, include_custom_videos=False)

        # Cache for 24 hours
        if movement:
            self.cache.set(cache_key, movement, ttl=CacheKeys.TTL_24_HOURS)

        return movement

    def get_movement_by_name(self, user_id: int, name: str) -> dict | None:
        """Get a movement by exact name."""
        # Try cache
        cache_key = CacheKeys.movement_by_name(name)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        movement = self.repo.get_by_name(name)

        # Cache for 24 hours
        if movement:
            self.cache.set(cache_key, movement, ttl=CacheKeys.TTL_24_HOURS)

        return movement

    def get_categories(self, user_id: int) -> list[str]:
        """Get list of all movement categories."""
        # Try cache
        cache_key = CacheKeys.MOVEMENTS_GLOSSARY_CATEGORIES
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        categories = self.repo.get_categories()

        # Cache for 24 hours
        self.cache.set(cache_key, categories, ttl=CacheKeys.TTL_24_HOURS)

        return categories

    def create_custom_movement(
        self,
        user_id: int,
        name: str,
        category: str,
        subcategory: str | None = None,
        points: int = 0,
        description: str | None = None,
        aliases: list[str] | None = None,
        gi_applicable: bool = True,
        nogi_applicable: bool = True,
    ) -> dict:
        """Create a custom user-added movement."""
        # Custom movements are global (not user-specific)
        movement = self.repo.create_custom(
            name=name,
            category=category,
            subcategory=subcategory,
            points=points,
            description=description,
            aliases=aliases,
            gi_applicable=gi_applicable,
            nogi_applicable=nogi_applicable,
        )

        # Invalidate movement cache
        self._invalidate_movement_cache()

        return movement

    def delete_custom_movement(self, user_id: int, movement_id: int) -> bool:
        """Delete a custom movement. Can only delete custom movements."""
        # Custom movements are global
        deleted = self.repo.delete_custom(movement_id)

        # Invalidate movement cache
        if deleted:
            self._invalidate_movement_cache()

        return deleted

    def add_custom_video(
        self,
        user_id: int,
        movement_id: int,
        url: str,
        title: str | None = None,
        video_type: str = "general",
    ) -> dict:
        """Add a custom video link to a movement."""
        # Custom videos are global
        return self.repo.add_custom_video(
            movement_id=movement_id,
            url=url,
            title=title,
            video_type=video_type,
        )

    def delete_custom_video(self, user_id: int, video_id: int) -> bool:
        """Delete a custom video link.

        Only admin users can delete videos since videos are global resources
        without per-user ownership.
        """
        from rivaflow.db.repositories.user_repo import UserRepository

        user = UserRepository().get_by_id(user_id)
        if not user or not user.get("is_admin"):
            raise PermissionError("Only admins can delete videos")
        return self.repo.delete_custom_video(video_id)

    def list_trained_movements(
        self,
        user_id: int,
        category: str | None = None,
        search: str | None = None,
        trained_only: bool = False,
    ) -> list[dict]:
        """Get movements with per-user training data."""
        return self.repo.list_with_training_data(
            user_id=user_id,
            category=category,
            search=search,
            trained_only=trained_only,
        )

    def get_stale_movements(self, user_id: int, days: int = 7) -> list[dict]:
        """Get movements the user has trained but not within N days."""
        return self.repo.get_stale(user_id=user_id, days=days)

    def get_trained_names(self, user_id: int) -> list[str]:
        """Get distinct trained movement names for autocomplete."""
        return self.repo.get_trained_names(user_id=user_id)

    def list_all_videos(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """List all movement videos with linked movement names."""
        return self.repo.list_all_videos(limit=limit, offset=offset)

    def get_video(self, user_id: int, video_id: int) -> dict | None:
        """Get a single movement video by ID."""
        return self.repo.get_video_by_id(video_id)

    def add_video(
        self,
        user_id: int,
        movement_id: int,
        url: str,
        title: str | None = None,
        video_type: str = "general",
    ) -> dict:
        """Add a video link to a movement."""
        return self.repo.add_custom_video(
            movement_id=movement_id,
            url=url,
            title=title,
            video_type=video_type,
        )

    def delete_video(self, user_id: int, video_id: int) -> bool:
        """Delete a movement video.

        Only admin users can delete videos since videos are global resources.
        """
        from rivaflow.db.repositories.user_repo import UserRepository

        user = UserRepository().get_by_id(user_id)
        if not user or not user.get("is_admin"):
            raise PermissionError("Only admins can delete videos")
        return self.repo.delete_custom_video(video_id)

    def _invalidate_movement_cache(self) -> None:
        """Invalidate all movement-related cache."""
        self.cache.delete_pattern(CacheKeys.PATTERN_ALL_MOVEMENTS)
