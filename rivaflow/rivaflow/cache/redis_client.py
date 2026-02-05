"""Redis client with connection pooling and graceful fallback."""

import json
import logging
import os
from contextlib import contextmanager
from typing import Any

try:
    import redis
    from redis.exceptions import ConnectionError, RedisError, TimeoutError

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    RedisError = Exception
    ConnectionError = Exception
    TimeoutError = Exception

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client with connection pooling and graceful fallback.

    When Redis is unavailable (not installed, not running, or connection fails),
    the client automatically falls back to no-op mode where all operations
    succeed but no caching occurs.
    """

    def __init__(self, redis_url: str | None = None):
        """
        Initialize Redis client.

        Args:
            redis_url: Redis connection URL (default: from REDIS_URL env var)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client = None
        self._fallback_mode = False

        if not REDIS_AVAILABLE:
            logger.warning(
                "Redis library not available. Running in fallback mode (no caching)."
            )
            self._fallback_mode = True
        else:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize Redis connection pool."""
        try:
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
                max_connections=10,
            )
            # Test connection
            self._client.ping()
            logger.info(f"Redis client connected to {self.redis_url}")
        except (RedisError, ConnectionError, Exception) as e:
            logger.warning(
                f"Failed to connect to Redis: {e}. Running in fallback mode (no caching)."
            )
            self._client = None
            self._fallback_mode = True

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value (deserialized from JSON) or None if not found/unavailable
        """
        if self._fallback_mode or not self._client:
            return None

        try:
            value = self._client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except (RedisError, ConnectionError, TimeoutError, json.JSONDecodeError) as e:
            logger.warning(f"Redis GET error for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        if self._fallback_mode or not self._client:
            return False

        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                self._client.setex(key, ttl, serialized)
            else:
                self._client.set(key, serialized)
            return True
        except (
            RedisError,
            ConnectionError,
            TimeoutError,
            TypeError,
            json.JSONEncodeError,
        ) as e:
            logger.warning(f"Redis SET error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        if self._fallback_mode or not self._client:
            return False

        try:
            return bool(self._client.delete(key))
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis DELETE error for key '{key}': {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        if self._fallback_mode or not self._client:
            return 0

        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis DELETE_PATTERN error for pattern '{pattern}': {e}")
            return 0

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if self._fallback_mode or not self._client:
            return False

        try:
            return bool(self._client.exists(key))
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis EXISTS error for key '{key}': {e}")
            return False

    def flush_all(self) -> bool:
        """
        Flush all keys from Redis (use with caution).

        Returns:
            True if successful, False otherwise
        """
        if self._fallback_mode or not self._client:
            return False

        try:
            self._client.flushdb()
            logger.info("Redis cache flushed")
            return True
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis FLUSH error: {e}")
            return False

    @contextmanager
    def pipeline(self):
        """
        Context manager for Redis pipeline (batch operations).

        Yields:
            Redis pipeline or None if in fallback mode
        """
        if self._fallback_mode or not self._client:
            yield None
            return

        try:
            pipe = self._client.pipeline()
            yield pipe
            pipe.execute()
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis PIPELINE error: {e}")
            yield None

    def is_available(self) -> bool:
        """
        Check if Redis is available.

        Returns:
            True if Redis is connected and responsive, False otherwise
        """
        if self._fallback_mode or not self._client:
            return False

        try:
            self._client.ping()
            return True
        except (RedisError, ConnectionError, TimeoutError):
            return False


# Global Redis client instance
_redis_client: RedisClient | None = None


def get_redis_client() -> RedisClient:
    """
    Get the global Redis client instance.

    Returns:
        RedisClient instance (singleton)
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
