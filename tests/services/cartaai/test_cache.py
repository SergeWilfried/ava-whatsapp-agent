"""Unit tests for MenuCache."""

import pytest
import asyncio
from datetime import timedelta

from ai_companion.services.cartaai.cache import MenuCache


@pytest.mark.asyncio
class TestMenuCache:
    """Test MenuCache functionality."""

    async def test_cache_initialization(self):
        """Test cache initialization with default parameters."""
        cache = MenuCache()

        assert cache.ttl == timedelta(minutes=15)
        assert cache.max_size == 1000
        assert len(cache._cache) == 0

    async def test_cache_initialization_custom(self):
        """Test cache initialization with custom parameters."""
        cache = MenuCache(ttl_minutes=30, max_size=500)

        assert cache.ttl == timedelta(minutes=30)
        assert cache.max_size == 500

    async def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = MenuCache()

        # Set value
        await cache.set("key1", {"data": "value1"})

        # Get value
        result = await cache.get("key1")

        assert result == {"data": "value1"}
        assert cache.stats["sets"] == 1
        assert cache.stats["hits"] == 1
        assert cache.stats["misses"] == 0

    async def test_cache_miss(self):
        """Test cache miss for non-existent key."""
        cache = MenuCache()

        result = await cache.get("nonexistent")

        assert result is None
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 1

    async def test_cache_expiration(self):
        """Test cache expiration after TTL."""
        cache = MenuCache(ttl_minutes=0)  # Expire immediately

        await cache.set("key1", "value1")

        # Wait a bit to ensure expiration
        await asyncio.sleep(0.01)

        result = await cache.get("key1")

        assert result is None
        assert cache.stats["expirations"] == 1

    async def test_invalidate(self):
        """Test cache invalidation."""
        cache = MenuCache()

        await cache.set("key1", "value1")
        await cache.invalidate("key1")

        result = await cache.get("key1")

        assert result is None

    async def test_invalidate_pattern(self):
        """Test pattern-based cache invalidation."""
        cache = MenuCache()

        await cache.set("menu:rest1:item1", "value1")
        await cache.set("menu:rest1:item2", "value2")
        await cache.set("menu:rest2:item1", "value3")

        # Invalidate all menu:rest1:* keys
        await cache.invalidate_pattern("menu:rest1:*")

        result1 = await cache.get("menu:rest1:item1")
        result2 = await cache.get("menu:rest1:item2")
        result3 = await cache.get("menu:rest2:item1")

        assert result1 is None
        assert result2 is None
        assert result3 == "value3"

    async def test_clear(self):
        """Test clearing entire cache."""
        cache = MenuCache()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        assert len(cache._cache) == 3

        await cache.clear()

        assert len(cache._cache) == 0

    async def test_cache_eviction(self):
        """Test cache eviction when max size reached."""
        cache = MenuCache(max_size=3)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        assert len(cache._cache) == 3

        # Add one more to trigger eviction
        await cache.set("key4", "value4")

        assert len(cache._cache) == 3
        assert cache.stats["evictions"] == 1

        # Oldest key (key1) should be evicted
        result = await cache.get("key1")
        assert result is None

    async def test_get_stats(self):
        """Test cache statistics."""
        cache = MenuCache()

        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss

        stats = cache.get_stats()

        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["hit_rate"] == 50.0  # 1 hit out of 2 requests

    async def test_reset_stats(self):
        """Test resetting cache statistics."""
        cache = MenuCache()

        await cache.set("key1", "value1")
        await cache.get("key1")

        assert cache.stats["sets"] == 1
        assert cache.stats["hits"] == 1

        cache.reset_stats()

        assert cache.stats["sets"] == 0
        assert cache.stats["hits"] == 0

    async def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = MenuCache(ttl_minutes=0)  # Expire immediately

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        await asyncio.sleep(0.01)

        await cache.cleanup_expired()

        assert len(cache._cache) == 0
        assert cache.stats["expirations"] == 2

    async def test_concurrent_access(self):
        """Test concurrent cache access."""
        cache = MenuCache()

        async def set_value(key: str, value: str):
            await cache.set(key, value)

        async def get_value(key: str):
            return await cache.get(key)

        # Run concurrent operations
        await asyncio.gather(
            set_value("key1", "value1"),
            set_value("key2", "value2"),
            set_value("key3", "value3"),
        )

        results = await asyncio.gather(
            get_value("key1"),
            get_value("key2"),
            get_value("key3"),
        )

        assert results == ["value1", "value2", "value3"]

    async def test_repr(self):
        """Test string representation."""
        cache = MenuCache(ttl_minutes=10, max_size=100)

        repr_str = repr(cache)

        assert "MenuCache" in repr_str
        assert "ttl=10" in repr_str
        assert "max_size=100" in repr_str
