"""Tests for MenuAdapter."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_companion.services.menu_adapter import MenuAdapter, get_menu_adapter, reset_menu_adapter
from ai_companion.core.config import CartaAIConfig


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = MagicMock(spec=CartaAIConfig)
    config.use_cartaai_api = False
    config.menu_api_enabled = False
    config.validate.return_value = True
    return config


@pytest.fixture
async def menu_adapter(mock_config):
    """Create menu adapter with mocked config."""
    with patch("ai_companion.services.menu_adapter.get_cartaai_config", return_value=mock_config):
        adapter = MenuAdapter()
        yield adapter
        await adapter.close()


@pytest.mark.asyncio
class TestMenuAdapter:
    """Test MenuAdapter functionality."""

    async def test_initialization(self, menu_adapter):
        """Test adapter initialization."""
        assert menu_adapter is not None
        assert menu_adapter._initialized is False

    async def test_find_menu_item_mock_mode(self, menu_adapter):
        """Test finding menu item in mock mode."""
        # Should use mock data
        item = await menu_adapter.find_menu_item("pizzas_0")

        assert item is not None
        assert item["id"] == "pizzas_0"
        assert "name" in item
        assert "price" in item

    async def test_find_menu_item_invalid_id(self, menu_adapter):
        """Test finding non-existent menu item."""
        item = await menu_adapter.find_menu_item("invalid_999")

        assert item is None

    async def test_search_products_mock_mode(self, menu_adapter):
        """Test searching products in mock mode."""
        results = await menu_adapter.search_products("pizza")

        assert len(results) > 0
        assert all("pizza" in r["name"].lower() or "pizza" in r["description"].lower() for r in results)

    async def test_search_products_with_category(self, menu_adapter):
        """Test searching products filtered by category."""
        results = await menu_adapter.search_products("burger", category="burgers")

        assert len(results) > 0
        assert all(r["category"] == "burgers" for r in results)

    async def test_get_menu_structure_mock(self, menu_adapter):
        """Test getting menu structure in mock mode."""
        menu = await menu_adapter.get_menu_structure()

        assert menu["type"] == "1"
        assert "data" in menu
        assert "categories" in menu["data"]
        assert len(menu["data"]["categories"]) > 0

    async def test_get_restaurant_info(self, menu_adapter):
        """Test getting restaurant information."""
        info = menu_adapter.get_restaurant_info()

        assert "tax_rate" in info
        assert "delivery_fee" in info
        assert "free_delivery_minimum" in info

    async def test_singleton_pattern(self):
        """Test global adapter singleton."""
        adapter1 = get_menu_adapter()
        adapter2 = get_menu_adapter()

        assert adapter1 is adapter2

        # Clean up
        reset_menu_adapter()

    async def test_convert_api_product_to_legacy(self, menu_adapter):
        """Test converting API product format to legacy format."""
        api_product = {
            "_id": "prod001",
            "name": "Test Burger",
            "price": 15.99,
            "description": "Delicious burger",
            "category": {"name": "Burgers"},
            "isAvailable": True,
            "presentations": [],
            "modifiers": [],
        }

        legacy = menu_adapter._convert_api_product_to_legacy(api_product, "burgers_0")

        assert legacy["id"] == "burgers_0"
        assert legacy["api_id"] == "prod001"
        assert legacy["name"] == "Test Burger"
        assert legacy["price"] == 15.99
        assert legacy["is_available"] is True
