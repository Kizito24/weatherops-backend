"""
Redis connection and caching utilities.
Provides async Redis client for caching and session storage.
"""

from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import get_settings


class RedisClient:
    """Async Redis client wrapper."""

    _client: Redis | None = None

    @classmethod
    async def connect(cls) -> Redis:
        """
        Establish Redis connection.

        Returns:
            Redis client instance.
        """
        if cls._client is None:
            settings = get_settings()
            cls._client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf8",
                decode_responses=True,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                socket_keepalive=settings.REDIS_SOCKET_KEEPALIVE,
            )
        return cls._client

    @classmethod
    async def disconnect(cls) -> None:
        """Close Redis connection."""
        if cls._client is not None:
            await cls._client.close()
            cls._client = None

    @classmethod
    async def get(cls, key: str) -> Any:
        """Get value from Redis."""
        client = await cls.connect()
        return await client.get(key)

    @classmethod
    async def set(cls, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in Redis."""
        client = await cls.connect()
        await client.set(key, value, ex=ttl)

    @classmethod
    async def delete(cls, key: str) -> None:
        """Delete key from Redis."""
        client = await cls.connect()
        await client.delete(key)

    @classmethod
    async def exists(cls, key: str) -> bool:
        """Check if key exists in Redis."""
        client = await cls.connect()
        result = await client.exists(key)
        return bool(result)


async def get_redis_client() -> Redis:
    """Get Redis client for dependency injection."""
    return await RedisClient.connect()
