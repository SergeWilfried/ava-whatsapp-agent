"""Tests for ProductIDMapper."""

import pytest

from ai_companion.services.cartaai.product_mapper import ProductIDMapper, get_product_mapper, reset_product_mapper


class TestProductIDMapper:
    """Test ProductIDMapper functionality."""

    def test_initialization(self):
        """Test mapper initialization."""
        mapper = ProductIDMapper()

        assert len(mapper) == 0
        assert len(mapper._category_mapping) == 0

    def test_add_mapping(self):
        """Test adding product ID mapping."""
        mapper = ProductIDMapper()

        mapper.add_mapping("pizzas_0", "prod001")

        assert mapper.get_api_id("pizzas_0") == "prod001"
        assert mapper.get_legacy_id("prod001") == "pizzas_0"
        assert len(mapper) == 1

    def test_add_category_mapping(self):
        """Test adding category ID mapping."""
        mapper = ProductIDMapper()

        mapper.add_category_mapping("pizzas", "cat001")

        assert mapper.get_api_category_id("pizzas") == "cat001"

    def test_get_nonexistent_mapping(self):
        """Test getting nonexistent mapping."""
        mapper = ProductIDMapper()

        assert mapper.get_api_id("invalid_id") is None
        assert mapper.get_legacy_id("invalid_id") is None

    def test_build_from_menu_structure(self):
        """Test building mappings from menu structures."""
        mapper = ProductIDMapper()

        # API menu
        api_menu = {
            "type": "1",
            "data": {
                "categories": [
                    {
                        "id": "cat001",
                        "name": "Burgers",
                        "products": [
                            {"id": "prod001", "name": "Classic Burger"},
                            {"id": "prod002", "name": "Cheese Burger"},
                        ],
                    }
                ]
            },
        }

        # Legacy menu
        legacy_menu = {
            "burgers": {
                "items": [
                    {"name": "Classic Burger", "price": 15.99},
                    {"name": "Cheese Burger", "price": 17.99"},
                ]
            }
        }

        mapper.build_from_menu_structure(api_menu, legacy_menu)

        # Check category mapping
        assert mapper.get_api_category_id("burgers") == "cat001"

        # Check product mappings
        assert mapper.get_api_id("burgers_0") == "prod001"
        assert mapper.get_api_id("burgers_1") == "prod002"

    def test_get_all_mappings(self):
        """Test getting all mappings."""
        mapper = ProductIDMapper()

        mapper.add_mapping("pizzas_0", "prod001")
        mapper.add_mapping("pizzas_1", "prod002")

        all_mappings = mapper.get_all_mappings()

        assert len(all_mappings) == 2
        assert all_mappings["pizzas_0"] == "prod001"
        assert all_mappings["pizzas_1"] == "prod002"

    def test_get_all_category_mappings(self):
        """Test getting all category mappings."""
        mapper = ProductIDMapper()

        mapper.add_category_mapping("pizzas", "cat001")
        mapper.add_category_mapping("burgers", "cat002")

        all_category_mappings = mapper.get_all_category_mappings()

        assert len(all_category_mappings) == 2
        assert all_category_mappings["pizzas"] == "cat001"

    def test_clear(self):
        """Test clearing all mappings."""
        mapper = ProductIDMapper()

        mapper.add_mapping("pizzas_0", "prod001")
        mapper.add_category_mapping("pizzas", "cat001")

        assert len(mapper) == 1

        mapper.clear()

        assert len(mapper) == 0
        assert len(mapper._category_mapping) == 0

    def test_repr(self):
        """Test string representation."""
        mapper = ProductIDMapper()

        mapper.add_mapping("pizzas_0", "prod001")
        mapper.add_category_mapping("pizzas", "cat001")

        repr_str = repr(mapper)

        assert "ProductIDMapper" in repr_str
        assert "products=1" in repr_str
        assert "categories=1" in repr_str

    def test_singleton_pattern(self):
        """Test global mapper singleton."""
        mapper1 = get_product_mapper()
        mapper2 = get_product_mapper()

        assert mapper1 is mapper2

        # Clean up
        reset_product_mapper()
