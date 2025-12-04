"""Tests for updated interactive components with API support."""

import pytest

from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    create_size_selection_buttons,
    create_extras_list,
    create_modifiers_list,
    create_category_selection_list,
    extract_modifier_selections,
    extract_presentation_id,
)


class TestSizeSelectionButtons:
    """Test size selection with API presentations."""

    def test_with_api_presentations(self):
        """Test size selection using API presentations."""
        presentations = [
            {"_id": "pres001", "name": "Regular", "price": 15.99},
            {"_id": "pres002", "name": "Large", "price": 18.99},
        ]

        component = create_size_selection_buttons(
            "Classic Burger", presentations=presentations
        )

        assert component["type"] == "button"
        assert len(component["action"]["buttons"]) == 2
        assert component["action"]["buttons"][0]["reply"]["id"] == "size_pres001"
        assert "Regular" in component["action"]["buttons"][0]["reply"]["title"]
        assert "$15.99" in component["action"]["buttons"][0]["reply"]["title"]

    def test_with_legacy_pricing(self):
        """Test size selection using legacy base price."""
        component = create_size_selection_buttons("Classic Burger", base_price=15.99)

        assert component["type"] == "button"
        assert len(component["action"]["buttons"]) == 3
        assert component["action"]["buttons"][0]["reply"]["id"] == "size_small"
        assert component["action"]["buttons"][1]["reply"]["id"] == "size_medium"
        assert component["action"]["buttons"][2]["reply"]["id"] == "size_large"

    def test_without_pricing(self):
        """Test size selection without pricing data."""
        component = create_size_selection_buttons("Classic Burger")

        assert component["type"] == "button"
        assert len(component["action"]["buttons"]) == 1
        assert component["action"]["buttons"][0]["reply"]["id"] == "size_default"

    def test_limits_to_three_buttons(self):
        """Test that only first 3 presentations are used."""
        presentations = [
            {"_id": f"pres{i}", "name": f"Size {i}", "price": 10.0 + i}
            for i in range(5)
        ]

        component = create_size_selection_buttons(
            "Test Item", presentations=presentations
        )

        assert len(component["action"]["buttons"]) == 3


class TestExtrasListLegacy:
    """Test extras list with legacy hardcoded data."""

    def test_pizza_extras(self):
        """Test pizza extras list."""
        component = create_extras_list(category="pizza")

        assert component["type"] == "list"
        sections = component["action"]["sections"]
        assert len(sections) >= 2  # At least 2 sections for pizza

        # Check for "no extras" option
        all_rows = [row for section in sections for row in section["rows"]]
        no_extras_ids = [row["id"] for row in all_rows if row["id"] == "no_extras"]
        assert len(no_extras_ids) == 1

    def test_burger_extras(self):
        """Test burger extras list."""
        component = create_extras_list(category="burger")

        assert component["type"] == "list"
        sections = component["action"]["sections"]
        assert len(sections) >= 1


class TestExtrasListAPI:
    """Test extras list with API modifiers."""

    def test_with_api_modifiers(self):
        """Test extras list using API modifiers."""
        modifiers = [
            {
                "_id": "mod001",
                "name": "Toppings",
                "options": [
                    {"_id": "opt001", "name": "Extra Cheese", "price": 2.00},
                    {"_id": "opt002", "name": "Bacon", "price": 3.00},
                ],
            }
        ]

        component = create_extras_list(modifiers=modifiers)

        assert component["type"] == "list"
        sections = component["action"]["sections"]
        assert any(s["title"] == "Toppings" for s in sections)

        # Find toppings section
        toppings_section = next(s for s in sections if s["title"] == "Toppings")
        rows = toppings_section["rows"]

        # Check for modifier options
        option_ids = [row["id"] for row in rows]
        assert "extra_opt001" in option_ids
        assert "extra_opt002" in option_ids

    def test_with_free_options(self):
        """Test that free options display correctly."""
        modifiers = [
            {
                "_id": "mod001",
                "name": "Sauces",
                "options": [
                    {"_id": "opt001", "name": "Ketchup", "price": 0.00},
                    {"_id": "opt002", "name": "Mayo", "price": 0.00},
                ],
            }
        ]

        component = create_extras_list(modifiers=modifiers)

        sections = component["action"]["sections"]
        sauces_section = next(s for s in sections if s["title"] == "Sauces")

        # Check that free items show "Free" instead of "$0.00"
        for row in sauces_section["rows"]:
            assert row["description"] == "Free"


class TestModifiersList:
    """Test advanced modifiers list."""

    def test_with_required_modifier(self):
        """Test modifier with minSelections > 0."""
        modifiers = [
            {
                "_id": "mod001",
                "name": "Choose Protein",
                "minSelections": 1,
                "maxSelections": 1,
                "options": [
                    {"_id": "opt001", "name": "Beef", "price": 0.00},
                    {"_id": "opt002", "name": "Chicken", "price": 0.00},
                ],
            }
        ]

        component = create_modifiers_list("Burger", modifiers)

        assert component is not None
        sections = component["action"]["sections"]

        # Check title indicates required
        protein_section = sections[0]
        assert "(Required)" in protein_section["title"]

    def test_with_multiple_selections(self):
        """Test modifier with maxSelections > 1."""
        modifiers = [
            {
                "_id": "mod001",
                "name": "Toppings",
                "minSelections": 0,
                "maxSelections": 3,
                "options": [
                    {"_id": "opt001", "name": "Cheese", "price": 1.00},
                    {"_id": "opt002", "name": "Bacon", "price": 2.00},
                ],
            }
        ]

        component = create_modifiers_list("Burger", modifiers)

        sections = component["action"]["sections"]
        toppings_section = sections[0]

        # Check title indicates max selections
        assert "(Max 3)" in toppings_section["title"]

    def test_respects_row_limit(self):
        """Test that total rows don't exceed WhatsApp limit."""
        modifiers = [
            {
                "_id": f"mod{i}",
                "name": f"Group {i}",
                "minSelections": 0,
                "maxSelections": 1,
                "options": [
                    {"_id": f"opt{i}_{j}", "name": f"Option {j}", "price": 1.00}
                    for j in range(5)
                ],
            }
            for i in range(3)  # 3 groups x 5 options = 15 total (exceeds limit)
        ]

        component = create_modifiers_list("Item", modifiers, max_total_rows=10)

        sections = component["action"]["sections"]
        total_rows = sum(len(s["rows"]) for s in sections)

        assert total_rows <= 10  # WhatsApp limit

    def test_with_no_modifiers(self):
        """Test with empty modifiers list."""
        component = create_modifiers_list("Item", [])

        assert component is None


class TestCategorySelection:
    """Test category selection list."""

    def test_with_api_categories(self):
        """Test category selection using API categories."""
        categories = [
            {"id": "cat001", "name": "Burgers", "products": [{}, {}]},
            {"id": "cat002", "name": "Pizza", "products": [{}, {}, {}]},
        ]

        component = create_category_selection_list(categories=categories)

        assert component["type"] == "list"
        sections = component["action"]["sections"]
        rows = sections[0]["rows"]

        assert len(rows) == 2
        assert rows[0]["id"] == "cat_cat001"
        assert "Burgers" in rows[0]["title"]
        assert "2 items" in rows[0]["description"]

    def test_with_mock_categories(self):
        """Test category selection using mock data."""
        component = create_category_selection_list()

        assert component["type"] == "list"
        sections = component["action"]["sections"]
        rows = sections[0]["rows"]

        assert len(rows) == 5  # Mock has 5 categories
        assert any("Pizza" in row["title"] for row in rows)

    def test_limits_to_ten_categories(self):
        """Test that only first 10 categories are shown."""
        categories = [
            {"id": f"cat{i:03d}", "name": f"Category {i}", "products": []}
            for i in range(15)
        ]

        component = create_category_selection_list(categories=categories)

        sections = component["action"]["sections"]
        rows = sections[0]["rows"]

        assert len(rows) <= 10


class TestHelperFunctions:
    """Test helper functions."""

    def test_extract_modifier_selections(self):
        """Test extracting modifier selections from reply IDs."""
        selected_ids = [
            "mod_mod001_opt001",
            "mod_mod001_opt002",
            "mod_mod002_opt005",
        ]

        selections = extract_modifier_selections(selected_ids)

        assert "mod001" in selections
        assert "opt001" in selections["mod001"]
        assert "opt002" in selections["mod001"]
        assert "mod002" in selections
        assert "opt005" in selections["mod002"]

    def test_extract_modifier_selections_with_underscores(self):
        """Test extraction with IDs containing underscores."""
        selected_ids = ["mod_mod_001_opt_extra_cheese"]

        selections = extract_modifier_selections(selected_ids)

        assert "mod" in selections
        assert "001_opt_extra_cheese" in selections["mod"]

    def test_extract_modifier_selections_ignores_non_mod(self):
        """Test that non-modifier IDs are ignored."""
        selected_ids = [
            "mod_mod001_opt001",
            "size_large",
            "cat_pizza",
        ]

        selections = extract_modifier_selections(selected_ids)

        assert len(selections) == 1
        assert "mod001" in selections

    def test_extract_presentation_id(self):
        """Test extracting presentation ID from reply."""
        assert extract_presentation_id("size_pres001") == "pres001"
        assert extract_presentation_id("size_pres_large") == "pres_large"
        assert extract_presentation_id("size_large") == "large"

    def test_extract_presentation_id_non_size(self):
        """Test that non-size IDs return None."""
        assert extract_presentation_id("mod_mod001_opt001") is None
        assert extract_presentation_id("cat_burgers") is None
