"""Cache key patterns and TTL constants for consistent caching."""


class CacheKeys:
    """
    Cache key patterns and TTL constants.

    All cache keys follow a consistent naming pattern:
    <entity>:<identifier>[:<sub-identifier>]
    """

    # TTL Constants (in seconds)
    TTL_24_HOURS = 86400  # 24 hours
    TTL_1_HOUR = 3600  # 1 hour
    TTL_15_MINUTES = 900  # 15 minutes
    TTL_5_MINUTES = 300  # 5 minutes

    # Movements Glossary Cache Keys
    MOVEMENTS_GLOSSARY_ALL = "movements:glossary:all"
    MOVEMENTS_GLOSSARY_CATEGORIES = "movements:glossary:categories"

    @staticmethod
    def movements_glossary_filtered(
        category: str = None, gi_only: bool = False, nogi_only: bool = False
    ) -> str:
        """
        Generate cache key for filtered movements list.

        Args:
            category: Optional category filter
            gi_only: Filter for gi-applicable movements only
            nogi_only: Filter for nogi-applicable movements only

        Returns:
            Cache key string
        """
        filters = []
        if category:
            filters.append(f"cat:{category}")
        if gi_only:
            filters.append("gi")
        if nogi_only:
            filters.append("nogi")

        filter_str = ":".join(filters) if filters else "all"
        return f"movements:glossary:filtered:{filter_str}"

    @staticmethod
    def movement_by_id(movement_id: int) -> str:
        """Generate cache key for movement by ID."""
        return f"movements:id:{movement_id}"

    @staticmethod
    def movement_by_name(name: str) -> str:
        """Generate cache key for movement by name."""
        # Normalize name to lowercase for consistent caching
        normalized_name = name.lower().strip()
        return f"movements:name:{normalized_name}"

    # Gym Directory Cache Keys
    GYM_DIRECTORY_ALL = "gyms:directory:all"
    GYM_DIRECTORY_VERIFIED = "gyms:directory:verified"

    @staticmethod
    def gym_by_id(gym_id: int) -> str:
        """Generate cache key for gym by ID."""
        return f"gyms:id:{gym_id}"

    @staticmethod
    def gym_search(query: str, verified_only: bool = False) -> str:
        """
        Generate cache key for gym search.

        Args:
            query: Search query
            verified_only: Filter for verified gyms only

        Returns:
            Cache key string
        """
        # Normalize query to lowercase for consistent caching
        normalized_query = query.lower().strip()
        verified_suffix = ":verified" if verified_only else ""
        return f"gyms:search:{normalized_query}{verified_suffix}"

    # User Profile Cache Keys
    @staticmethod
    def user_profile(user_id: int) -> str:
        """Generate cache key for user profile."""
        return f"users:profile:{user_id}"

    @staticmethod
    def user_basic(user_id: int) -> str:
        """Generate cache key for basic user info."""
        return f"users:basic:{user_id}"

    @staticmethod
    def user_stats(user_id: int) -> str:
        """Generate cache key for user stats."""
        return f"users:stats:{user_id}"

    # Technique Cache Keys
    TECHNIQUES_ALL = "techniques:all"

    @staticmethod
    def technique_by_id(technique_id: int) -> str:
        """Generate cache key for technique by ID."""
        return f"techniques:id:{technique_id}"

    @staticmethod
    def technique_by_name(name: str) -> str:
        """Generate cache key for technique by name."""
        # Normalize name to lowercase for consistent caching
        normalized_name = name.lower().strip()
        return f"techniques:name:{normalized_name}"

    # Cache Invalidation Patterns
    PATTERN_ALL_MOVEMENTS = "movements:*"
    PATTERN_ALL_GYMS = "gyms:*"
    PATTERN_ALL_TECHNIQUES = "techniques:*"

    @staticmethod
    def pattern_user(user_id: int) -> str:
        """Generate pattern to invalidate all user-related cache."""
        return f"users:*:{user_id}*"

    @staticmethod
    def pattern_gym(gym_id: int) -> str:
        """Generate pattern to invalidate gym-specific cache."""
        return f"gyms:*:{gym_id}*"

    @staticmethod
    def pattern_movement(movement_id: int) -> str:
        """Generate pattern to invalidate movement-specific cache."""
        return f"movements:*:{movement_id}*"
