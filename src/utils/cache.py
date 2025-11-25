"""Redis caching layer for Pipedrive MCP Server."""

import json
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta

import redis.asyncio as redis
from ..config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager for Pipedrive data."""

    def __init__(self):
        """Initialize Redis connection."""
        self.redis_url = (
            f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        )
        self._redis: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        try:
            self._redis = redis.from_url(
                self.redis_url, password=settings.redis_password, decode_responses=True
            )
            # Test connection
            await self._redis.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis")

    def _is_available(self) -> bool:
        """Check if Redis is available."""
        return self._redis is not None

    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create cache key."""
        return f"pipedrive:{prefix}:{identifier}"

    async def get(self, prefix: str, identifier: str) -> Optional[Any]:
        """
        Get cached data.

        Args:
            prefix: Cache prefix (e.g., 'deal', 'person', 'token')
            identifier: Unique identifier

        Returns:
            Cached data or None if not found/expired
        """
        if not self._is_available():
            return None

        try:
            key = self._make_key(prefix, identifier)
            data = await self._redis.get(key)
            if data:
                logger.debug(f"Cache hit: {key}")
                return json.loads(data)
            else:
                logger.debug(f"Cache miss: {key}")
                return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def set(
        self, prefix: str, identifier: str, data: Any, ttl: Optional[int] = None
    ) -> bool:
        """
        Set cached data.

        Args:
            prefix: Cache prefix
            identifier: Unique identifier
            data: Data to cache (must be JSON serializable)
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self._is_available():
            return False

        try:
            key = self._make_key(prefix, identifier)
            serialized_data = json.dumps(data, default=str)

            if ttl is None:
                # Use default TTL based on prefix
                ttl = self._get_default_ttl(prefix)

            await self._redis.setex(key, ttl, serialized_data)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    async def delete(self, prefix: str, identifier: str) -> bool:
        """
        Delete cached data.

        Args:
            prefix: Cache prefix
            identifier: Unique identifier

        Returns:
            True if successful, False otherwise
        """
        if not self._is_available():
            return False

        try:
            key = self._make_key(prefix, identifier)
            await self._redis.delete(key)
            logger.debug(f"Cache delete: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Pattern to match (e.g., 'deal:*')

        Returns:
            Number of keys deleted
        """
        if not self._is_available():
            return 0

        try:
            full_pattern = f"pipedrive:{pattern}"
            keys = await self._redis.keys(full_pattern)
            if keys:
                await self._redis.delete(*keys)
                logger.debug(
                    f"Cache invalidated: {len(keys)} keys matching {full_pattern}"
                )
                return len(keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache invalidate pattern error: {e}")
            return 0

    def _get_default_ttl(self, prefix: str) -> int:
        """Get default TTL based on prefix."""
        ttl_mapping = {
            "token": settings.cache_ttl_token,
            "metadata": settings.cache_ttl_metadata,
            "deal": settings.cache_ttl_deal,
            "search": settings.cache_ttl_search,
            "person": settings.cache_ttl_metadata,
            "organization": settings.cache_ttl_metadata,
            "activity": settings.cache_ttl_metadata,
            "pipeline": settings.cache_ttl_metadata,
            "product": settings.cache_ttl_metadata,
            "user": settings.cache_ttl_metadata,
        }
        return ttl_mapping.get(prefix, settings.cache_ttl_search)

    # Specific cache methods for common use cases
    async def get_token(self, token_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached token data."""
        return await self.get("token", token_hash)

    async def set_token(self, token_hash: str, token_data: Dict[str, Any]) -> bool:
        """Cache token data."""
        return await self.set("token", token_hash, token_data, settings.cache_ttl_token)

    async def get_deal(self, deal_id: int) -> Optional[Dict[str, Any]]:
        """Get cached deal data."""
        return await self.get("deal", str(deal_id))

    async def set_deal(self, deal_id: int, deal_data: Dict[str, Any]) -> bool:
        """Cache deal data."""
        return await self.set("deal", str(deal_id), deal_data, settings.cache_ttl_deal)

    async def get_search_results(
        self, query_hash: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results."""
        return await self.get("search", query_hash)

    async def set_search_results(
        self, query_hash: str, results: List[Dict[str, Any]]
    ) -> bool:
        """Cache search results."""
        return await self.set("search", query_hash, results, settings.cache_ttl_search)

    async def get_metadata(
        self, entity_type: str, identifier: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached metadata (pipelines, stages, users, etc.)."""
        return await self.get("metadata", f"{entity_type}:{identifier}")

    async def set_metadata(
        self, entity_type: str, identifier: str, data: Dict[str, Any]
    ) -> bool:
        """Cache metadata."""
        return await self.set(
            "metadata", f"{entity_type}:{identifier}", data, settings.cache_ttl_metadata
        )

    async def invalidate_deal_cache(self, deal_id: int) -> bool:
        """Invalidate all cache entries related to a deal."""
        # Invalidate specific deal
        await self.delete("deal", str(deal_id))
        # Invalidate search results (they might include this deal)
        await self.invalidate_pattern("search:*")
        return True

    async def invalidate_user_cache(self, user_id: int) -> bool:
        """Invalidate all cache entries related to a user."""
        await self.delete("user", str(user_id))
        await self.invalidate_pattern("search:*")
        return True


# Global cache manager instance
cache_manager = CacheManager()


async def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    if not cache_manager._is_available():
        await cache_manager.connect()
    return cache_manager
