"""Simple in-memory cache with TTL for API responses."""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MenuCache:
    """Simple in-memory cache for menu data with TTL (Time To Live).

    Features:
    - Thread-safe with asyncio locks
    - TTL-based expiration
    - Cache invalidation
    - Cache statistics

    Example:
        cache = MenuCache(ttl_minutes=15)
        await cache.set("menu:restaurant", menu_data)
        cached_menu = await cache.get("menu:restaurant")
    """

    def __init__(self, ttl_minutes: int = 15, max_size: int = 1000):
        """Initialize cache.

        Args:
            ttl_minutes: Time to live in minutes (default: 15)
            max_size: Maximum number of cached items (default: 1000)
        """
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
            "expirations": 0,
        }

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired.

        Args:
            key: Cache key

        Returns:
            True if expired or not found, False otherwise
        """
        if key not in self._timestamps:
            return True

        age = datetime.now() - self._timestamps[key]
        return age > self.ttl

    def _evict_if_needed(self):
        """Evict oldest entries if cache is full."""
        if len(self._cache) >= self.max_size:
            # Find oldest entry
            oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])

            # Remove oldest entry
            self._cache.pop(oldest_key, None)
            self._timestamps.pop(oldest_key, None)
            self.stats["evictions"] += 1

            logger.info(f"Cache evicted oldest entry: {oldest_key}")

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/not found
        """
        async with self._lock:
            if key in self._cache and not self._is_expired(key):
                self.stats["hits"] += 1
                logger.debug(f"Cache HIT: {key}")
                return self._cache[key]

            # Entry expired or not found
            if key in self._cache:
                # Remove expired entry
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
                self.stats["expirations"] += 1
                logger.debug(f"Cache EXPIRED: {key}")

            self.stats["misses"] += 1
            logger.debug(f"Cache MISS: {key}")
            return None

    async def set(self, key: str, value: Any):
        """Set cache value with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
        """
        async with self._lock:
            # Evict if cache is full
            self._evict_if_needed()

            # Set value and timestamp
            self._cache[key] = value
            self._timestamps[key] = datetime.now()
            self.stats["sets"] += 1

            logger.debug(f"Cache SET: {key}")

    async def invalidate(self, key: str):
        """Remove specific key from cache.

        Args:
            key: Cache key to invalidate
        """
        async with self._lock:
            removed = key in self._cache
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)

            if removed:
                logger.info(f"Cache INVALIDATE: {key}")

    async def invalidate_pattern(self, pattern: str):
        """Remove all keys matching pattern.

        Args:
            pattern: Key pattern (simple wildcard with * supported)
                Example: "menu:*" invalidates "menu:restaurant1", "menu:restaurant2"
        """
        async with self._lock:
            # Convert wildcard pattern to simple matching
            if "*" in pattern:
                prefix = pattern.split("*")[0]
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
            else:
                keys_to_remove = [pattern] if pattern in self._cache else []

            # Remove matching keys
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)

            if keys_to_remove:
                logger.info(f"Cache INVALIDATE pattern '{pattern}': {len(keys_to_remove)} keys")

    async def clear(self):
        """Clear entire cache."""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._timestamps.clear()

            logger.info(f"Cache CLEARED: {count} entries removed")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics including hit rate
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_minutes": self.ttl.total_seconds() / 60,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "evictions": self.stats["evictions"],
            "expirations": self.stats["expirations"],
            "hit_rate": hit_rate,
        }

    def reset_stats(self):
        """Reset cache statistics."""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
            "expirations": 0,
        }

    async def cleanup_expired(self):
        """Remove all expired entries from cache."""
        async with self._lock:
            expired_keys = [k for k in self._cache.keys() if self._is_expired(k)]

            for key in expired_keys:
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
                self.stats["expirations"] += 1

            if expired_keys:
                logger.info(f"Cache cleanup: {len(expired_keys)} expired entries removed")

    def __repr__(self) -> str:
        """String representation of cache."""
        stats = self.get_stats()
        return (
            f"MenuCache(size={stats['size']}/{stats['max_size']}, "
            f"ttl={stats['ttl_minutes']}min, "
            f"hit_rate={stats['hit_rate']:.1f}%)"
        )
