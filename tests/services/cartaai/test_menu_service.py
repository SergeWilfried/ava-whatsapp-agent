"""Unit tests for MenuService."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import aioresponses

from ai_companion.services.cartaai import CartaAIClient, MenuCache, MenuService


@pytest.fixture
def mock_client():
    """Create mock CartaAI client."""
    client = MagicMock(spec=CartaAIClient)
    client.subdomain = "test-restaurant"
    client.local_id = "branch-01"
    return client


@pytest.fixture
def cache():
    """Create menu cache."""
    return MenuCache(ttl_minutes=15)


@pytest.fixture
def menu_service(mock_client, cache):
    """Create menu service with mocked client."""
    return MenuService(client=mock_client, cache=cache)


@pytest.mark.asyncio
class TestMenuService:
    """Test MenuService functionality."""

    async def test_initialization(self, mock_client):
        """Test menu service initialization."""
        service = MenuService(client=mock_client)

        assert service.client == mock_client
        assert service.enable_cache is True
        assert service.cache is not None

    async def test_initialization_without_cache(self, mock_client):
        """Test menu service initialization without cache."""
        service = MenuService(client=mock_client, enable_cache=False)

        assert service.enable_cache is False

    async def test_get_cache_key(self, menu_service):
        """Test cache key generation."""
        key = menu_service._get_cache_key("menu", "structure")

        assert key == "menu:test-restaurant:branch-01:structure"

    async def test_get_menu_structure_from_api(self, menu_service, mock_client):
        """Test fetching menu structure from API."""
        mock_response = {
            "type": "1",
            "data": {
                "categories": [
                    {"id": "cat1", "name": "Burgers", "products": []}
                ]
            }
        }

        mock_client.get_menu_structure = AsyncMock(return_value=mock_response)

        result = await menu_service.get_menu_structure()

        assert result["type"] == "1"
        assert len(result["data"]["categories"]) == 1
        mock_client.get_menu_structure.assert_called_once()

    async def test_get_menu_structure_from_cache(self, menu_service, mock_client):
        """Test fetching menu structure from cache."""
        mock_response = {
            "type": "1",
            "data": {"categories": []}
        }

        mock_client.get_menu_structure = AsyncMock(return_value=mock_response)

        # First call - populates cache
        await menu_service.get_menu_structure()

        # Second call - should use cache
        result = await menu_service.get_menu_structure()

        assert result["type"] == "1"
        # Client should only be called once (first call)
        assert mock_client.get_menu_structure.call_count == 1

        # Check cache stats
        stats = menu_service.get_cache_stats()
        assert stats["hits"] == 1

    async def test_get_menu_structure_force_refresh(self, menu_service, mock_client):
        """Test force refresh bypasses cache."""
        mock_response = {
            "type": "1",
            "data": {"categories": []}
        }

        mock_client.get_menu_structure = AsyncMock(return_value=mock_response)

        # First call
        await menu_service.get_menu_structure()

        # Second call with force_refresh
        result = await menu_service.get_menu_structure(force_refresh=True)

        assert result["type"] == "1"
        # Client should be called twice
        assert mock_client.get_menu_structure.call_count == 2

    async def test_get_product_details_partial_cache(self, menu_service, mock_client):
        """Test fetching products with some in cache."""
        product1 = {"_id": "prod1", "name": "Burger"}
        product2 = {"_id": "prod2", "name": "Pizza"}

        # Pre-cache product1
        cache_key = menu_service._get_cache_key("product", "prod1")
        await menu_service.cache.set(cache_key, product1)

        # Mock API response for prod2
        mock_client.get_product_details = AsyncMock(
            return_value={"success": True, "data": [product2]}
        )

        # Request both products
        results = await menu_service.get_product_details(["prod1", "prod2"])

        assert len(results) == 2
        # API should only be called for prod2
        mock_client.get_product_details.assert_called_once_with(["prod2"])

    async def test_get_product_by_id(self, menu_service, mock_client):
        """Test fetching single product by ID."""
        product = {"_id": "prod1", "name": "Burger"}

        mock_client.get_product_details = AsyncMock(
            return_value={"success": True, "data": [product]}
        )

        result = await menu_service.get_product_by_id("prod1")

        assert result["_id"] == "prod1"
        assert result["name"] == "Burger"

    async def test_get_product_by_id_not_found(self, menu_service, mock_client):
        """Test fetching non-existent product."""
        mock_client.get_product_details = AsyncMock(
            return_value={"success": True, "data": []}
        )

        result = await menu_service.get_product_by_id("invalid_id")

        assert result is None

    async def test_search_products_by_name(self, menu_service, mock_client):
        """Test searching products by name."""
        mock_menu = {
            "type": "1",
            "data": {
                "categories": [
                    {
                        "id": "cat1",
                        "name": "Burgers",
                        "products": [
                            {"id": "prod1", "name": "Classic Burger"},
                            {"id": "prod2", "name": "Cheese Burger"},
                            {"id": "prod3", "name": "Veggie Pizza"},
                        ]
                    }
                ]
            }
        }

        mock_client.get_menu_structure = AsyncMock(return_value=mock_menu)

        results = await menu_service.search_products_by_name("burger")

        assert len(results) == 2
        assert results[0]["name"] == "Classic Burger"
        assert results[1]["name"] == "Cheese Burger"

    async def test_search_products_by_category(self, menu_service, mock_client):
        """Test searching products filtered by category."""
        mock_menu = {
            "type": "1",
            "data": {
                "categories": [
                    {
                        "id": "cat1",
                        "name": "Burgers",
                        "products": [
                            {"id": "prod1", "name": "Classic Burger"},
                        ]
                    },
                    {
                        "id": "cat2",
                        "name": "Pizza",
                        "products": [
                            {"id": "prod2", "name": "Classic Pizza"},
                        ]
                    }
                ]
            }
        }

        mock_client.get_menu_structure = AsyncMock(return_value=mock_menu)

        results = await menu_service.search_products_by_name("classic", category_id="cat1")

        assert len(results) == 1
        assert results[0]["name"] == "Classic Burger"

    async def test_get_category_by_id(self, menu_service, mock_client):
        """Test fetching category by ID."""
        mock_menu = {
            "type": "1",
            "data": {
                "categories": [
                    {"id": "cat1", "name": "Burgers", "products": []},
                    {"id": "cat2", "name": "Pizza", "products": []},
                ]
            }
        }

        mock_client.get_menu_structure = AsyncMock(return_value=mock_menu)

        category = await menu_service.get_category_by_id("cat1")

        assert category["id"] == "cat1"
        assert category["name"] == "Burgers"

    async def test_get_category_by_id_not_found(self, menu_service, mock_client):
        """Test fetching non-existent category."""
        mock_menu = {
            "type": "1",
            "data": {"categories": []}
        }

        mock_client.get_menu_structure = AsyncMock(return_value=mock_menu)

        category = await menu_service.get_category_by_id("invalid_id")

        assert category is None

    async def test_get_products_by_category(self, menu_service, mock_client):
        """Test fetching all products in category."""
        mock_menu = {
            "type": "1",
            "data": {
                "categories": [
                    {
                        "id": "cat1",
                        "name": "Burgers",
                        "products": [
                            {"id": "prod1", "name": "Classic Burger"},
                            {"id": "prod2", "name": "Cheese Burger"},
                        ]
                    }
                ]
            }
        }

        mock_client.get_menu_structure = AsyncMock(return_value=mock_menu)

        products = await menu_service.get_products_by_category("cat1")

        assert len(products) == 2
        assert products[0]["name"] == "Classic Burger"

    async def test_is_product_available(self, menu_service, mock_client):
        """Test checking product availability."""
        product = {"_id": "prod1", "isAvailable": True}

        mock_client.get_product_details = AsyncMock(
            return_value={"success": True, "data": [product]}
        )

        is_available = await menu_service.is_product_available("prod1")

        assert is_available is True

    async def test_is_product_unavailable(self, menu_service, mock_client):
        """Test checking unavailable product."""
        product = {"_id": "prod1", "isAvailable": False}

        mock_client.get_product_details = AsyncMock(
            return_value={"success": True, "data": [product]}
        )

        is_available = await menu_service.is_product_available("prod1")

        assert is_available is False

    async def test_get_product_price(self, menu_service, mock_client):
        """Test fetching product price."""
        product = {"_id": "prod1", "price": 15.99}

        mock_client.get_product_details = AsyncMock(
            return_value={"success": True, "data": [product]}
        )

        price = await menu_service.get_product_price("prod1")

        assert price == 15.99

    async def test_invalidate_menu_cache(self, menu_service):
        """Test invalidating menu cache."""
        # Populate cache
        await menu_service.cache.set("menu:test-restaurant:branch-01:structure", {})
        await menu_service.cache.set("product:test-restaurant:branch-01:prod1", {})

        await menu_service.invalidate_menu_cache()

        # Cache should be empty
        stats = menu_service.get_cache_stats()
        assert stats["size"] == 0

    async def test_invalidate_product_cache(self, menu_service):
        """Test invalidating specific product cache."""
        cache_key = menu_service._get_cache_key("product", "prod1")
        await menu_service.cache.set(cache_key, {"_id": "prod1"})

        await menu_service.invalidate_product_cache("prod1")

        result = await menu_service.cache.get(cache_key)
        assert result is None

    async def test_get_cache_stats(self, menu_service):
        """Test getting cache statistics."""
        stats = menu_service.get_cache_stats()

        assert "size" in stats
        assert "hit_rate" in stats
        assert "hits" in stats

    async def test_preload_menu(self, menu_service, mock_client):
        """Test preloading menu data."""
        mock_menu = {
            "type": "1",
            "data": {
                "categories": [
                    {
                        "id": "cat1",
                        "name": "Burgers",
                        "products": [
                            {"id": "prod1", "name": "Classic Burger"},
                            {"id": "prod2", "name": "Cheese Burger"},
                        ]
                    }
                ]
            }
        }

        mock_client.get_menu_structure = AsyncMock(return_value=mock_menu)
        mock_client.get_product_details = AsyncMock(
            return_value={"success": True, "data": []}
        )

        await menu_service.preload_menu()

        # Menu structure should be cached
        cache_key = menu_service._get_cache_key("menu", "structure")
        cached_menu = await menu_service.cache.get(cache_key)
        assert cached_menu is not None

    async def test_repr(self, menu_service):
        """Test string representation."""
        repr_str = repr(menu_service)

        assert "MenuService" in repr_str
        assert "test-restaurant" in repr_str
        assert "cache=enabled" in repr_str
