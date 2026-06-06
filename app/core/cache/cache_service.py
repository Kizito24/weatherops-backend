"""Redis caching service abstraction."""

import json
import logging
from typing import Any

from app.core.redis import RedisClient

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching operations with Redis."""

    def __init__(self):
        """Initialize cache service."""
        self.client = RedisClient()

    async def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache (will be JSON serialized).
            ttl: Time-to-live in seconds.
        """
        try:
            serialized = json.dumps(value)
            await self.client.set(key, serialized, ttl)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")

    async def delete(self, key: str) -> None:
        """
        Delete value from cache.

        Args:
            key: Cache key.
        """
        try:
            await self.client.delete(key)
            logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key.

        Returns:
            True if key exists, False otherwise.
        """
        try:
            return await self.client.exists(key)
        except Exception as e:
            logger.warning(f"Cache exists error for key {key}: {e}")
            return False

    @staticmethod
    def make_weather_key(latitude: float, longitude: float, weather_type: str) -> str:
        """
        Create a cache key for weather data.

        Args:
            latitude: Location latitude.
            longitude: Location longitude.
            weather_type: Type of weather data (current, forecast, etc.).

        Returns:
            Formatted cache key.
        """
        return f"weather:{latitude}:{longitude}:{weather_type}"
