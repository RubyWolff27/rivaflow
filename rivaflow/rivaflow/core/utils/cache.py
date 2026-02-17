"""Simple in-memory cache with TTL support."""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)

# Sentinel object to distinguish "not in cache" from cached None/falsy values
_MISSING = object()

# Maximum cache entries to prevent unbounded memory growth
MAX_CACHE_SIZE = 10_000


class CacheEntry:
    """Cache entry with expiration time."""

    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() > self.expires_at


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, max_size: int = MAX_CACHE_SIZE):
        self._cache: dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
        self._max_size = max_size

    def get(self, key: str, default: Any = _MISSING) -> Any:
        """
        Get value from cache if it exists and hasn't expired.

        Args:
            key: Cache key
            default: Value to return if not found (defaults to _MISSING sentinel)

        Returns:
            Cached value or default if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return default

        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            return default

        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default: 5 minutes)
        """
        # Evict expired entries if at capacity
        if len(self._cache) >= self._max_size:
            self.cleanup_expired()

        # If still at capacity after cleanup, evict oldest entries
        if len(self._cache) >= self._max_size:
            entries = sorted(self._cache.items(), key=lambda x: x[1].expires_at)
            to_remove = len(self._cache) - self._max_size + 1
            for k, _ in entries[:to_remove]:
                del self._cache[k]

        self._cache[key] = CacheEntry(value, ttl_seconds)

    def delete(self, key: str):
        """
        Delete key from cache.

        Args:
            key: Cache key to delete
        """
        if key in self._cache:
            del self._cache[key]

    def delete_pattern(self, pattern: str):
        """Delete all keys matching a prefix pattern."""
        keys_to_delete = [k for k in self._cache if k.startswith(pattern)]
        for k in keys_to_delete:
            del self._cache[k]

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")

    def cleanup_expired(self):
        """Remove all expired entries from cache."""
        before_count = len(self._cache)
        self._cache = {k: v for k, v in self._cache.items() if not v.is_expired()}
        after_count = len(self._cache)
        removed = before_count - after_count
        if removed > 0:
            logger.info(f"Cleaned up {removed} expired cache entries")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "entries": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
        }


# Global cache instance
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get the global cache instance."""
    return _cache


def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results with TTL.

    Args:
        ttl_seconds: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key

    Usage:
        @cached(ttl_seconds=300, key_prefix="dashboard")
        def get_dashboard_data(user_id: int):
            return expensive_query()
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            cache_key_parts = [key_prefix] if key_prefix else []
            cache_key_parts.append(func.__name__)

            # Add args to key
            for arg in args:
                cache_key_parts.append(str(arg))

            # Add sorted kwargs to key
            for k, v in sorted(kwargs.items()):
                cache_key_parts.append(f"{k}={v}")

            cache_key = ":".join(cache_key_parts)

            # Try to get from cache (use sentinel to handle falsy values)
            cached_value = _cache.get(cache_key)
            if cached_value is not _MISSING:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value

            # Cache miss - call function
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)

            # Store in cache
            _cache.set(cache_key, result, ttl_seconds)

            return result

        return wrapper

    return decorator
