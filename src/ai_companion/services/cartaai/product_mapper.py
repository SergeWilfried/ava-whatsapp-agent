"""Product ID mapper for transitioning from mock data to API."""

from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class ProductIDMapper:
    """Maps legacy product IDs to API product IDs.

    During migration, we need to maintain backward compatibility with the old
    ID format (e.g., "pizzas_0", "burgers_1") while transitioning to API IDs
    (e.g., "prod001", "prod002").

    This mapper provides bidirectional mapping and can be populated dynamically
    from the API menu structure.
    """

    def __init__(self):
        """Initialize empty mapping."""
        self._legacy_to_api: Dict[str, str] = {}
        self._api_to_legacy: Dict[str, str] = {}
        self._category_mapping: Dict[str, str] = {}  # category_key -> API category ID

    def add_mapping(self, legacy_id: str, api_id: str):
        """Add a single ID mapping.

        Args:
            legacy_id: Old format ID (e.g., "pizzas_0")
            api_id: API product ID (e.g., "prod001")
        """
        self._legacy_to_api[legacy_id] = api_id
        self._api_to_legacy[api_id] = legacy_id

        logger.debug(f"Added mapping: {legacy_id} -> {api_id}")

    def add_category_mapping(self, category_key: str, api_category_id: str):
        """Add category ID mapping.

        Args:
            category_key: Old category key (e.g., "pizzas", "burgers")
            api_category_id: API category ID (e.g., "cat001")
        """
        self._category_mapping[category_key] = api_category_id
        logger.debug(f"Added category mapping: {category_key} -> {api_category_id}")

    def get_api_id(self, legacy_id: str) -> Optional[str]:
        """Get API ID from legacy ID.

        Args:
            legacy_id: Old format ID (e.g., "pizzas_0")

        Returns:
            API product ID or None if not found
        """
        return self._legacy_to_api.get(legacy_id)

    def get_legacy_id(self, api_id: str) -> Optional[str]:
        """Get legacy ID from API ID.

        Args:
            api_id: API product ID

        Returns:
            Legacy ID or None if not found
        """
        return self._api_to_legacy.get(api_id)

    def get_api_category_id(self, category_key: str) -> Optional[str]:
        """Get API category ID from category key.

        Args:
            category_key: Old category key

        Returns:
            API category ID or None if not found
        """
        return self._category_mapping.get(category_key)

    def build_from_menu_structure(self, menu_data: Dict, legacy_menu: Dict):
        """Build mappings from API menu structure and legacy menu.

        This automatically generates mappings by comparing product names
        between the API menu and legacy mock menu.

        Args:
            menu_data: API menu structure response
            legacy_menu: Mock RESTAURANT_MENU data
        """
        if menu_data.get("type") != "1":
            logger.warning("Invalid menu data type, cannot build mappings")
            return

        categories = menu_data.get("data", {}).get("categories", [])

        for category in categories:
            api_category_id = category.get("id")
            category_name = category.get("name", "").lower()

            # Find matching legacy category
            legacy_category_key = self._find_legacy_category_key(
                category_name, legacy_menu
            )

            if legacy_category_key:
                self.add_category_mapping(legacy_category_key, api_category_id)

                # Map products within this category
                api_products = category.get("products", [])
                legacy_products = legacy_menu.get(legacy_category_key, {}).get(
                    "items", []
                )

                self._map_products_by_position(
                    legacy_category_key, api_products, legacy_products
                )

        logger.info(
            f"Built mappings: {len(self._legacy_to_api)} products, "
            f"{len(self._category_mapping)} categories"
        )

    def _find_legacy_category_key(
        self, api_category_name: str, legacy_menu: Dict
    ) -> Optional[str]:
        """Find legacy category key that matches API category name.

        Args:
            api_category_name: Category name from API (e.g., "Burgers")
            legacy_menu: Legacy menu structure

        Returns:
            Legacy category key (e.g., "burgers") or None
        """
        api_name_lower = api_category_name.lower()

        for category_key in legacy_menu.keys():
            if category_key in api_name_lower or api_name_lower in category_key:
                return category_key

        return None

    def _map_products_by_position(
        self,
        category_key: str,
        api_products: List[Dict],
        legacy_products: List[Dict],
    ):
        """Map products by position in category.

        Assumes products are in the same order in both API and legacy data.

        Args:
            category_key: Legacy category key
            api_products: List of API products
            legacy_products: List of legacy products
        """
        # Map by position first
        for index, api_product in enumerate(api_products):
            api_id = api_product.get("id")
            legacy_id = f"{category_key}_{index}"

            if api_id:
                self.add_mapping(legacy_id, api_id)

        # Try to match by name if positions don't align
        if len(api_products) != len(legacy_products):
            logger.warning(
                f"Category '{category_key}': API has {len(api_products)} products "
                f"but legacy has {len(legacy_products)}"
            )
            self._map_products_by_name(category_key, api_products, legacy_products)

    def _map_products_by_name(
        self,
        category_key: str,
        api_products: List[Dict],
        legacy_products: List[Dict],
    ):
        """Map products by matching names.

        Args:
            category_key: Legacy category key
            api_products: List of API products
            legacy_products: List of legacy products
        """
        for index, legacy_product in enumerate(legacy_products):
            legacy_name = legacy_product.get("name", "").lower()
            legacy_id = f"{category_key}_{index}"

            # Skip if already mapped by position
            if self.get_api_id(legacy_id):
                continue

            # Find matching API product by name
            for api_product in api_products:
                api_name = api_product.get("name", "").lower()

                if legacy_name == api_name or legacy_name in api_name:
                    api_id = api_product.get("id")
                    if api_id and not self.get_legacy_id(api_id):
                        self.add_mapping(legacy_id, api_id)
                        break

    def get_all_mappings(self) -> Dict[str, str]:
        """Get all product ID mappings.

        Returns:
            Dictionary of legacy_id -> api_id mappings
        """
        return self._legacy_to_api.copy()

    def get_all_category_mappings(self) -> Dict[str, str]:
        """Get all category ID mappings.

        Returns:
            Dictionary of category_key -> api_category_id mappings
        """
        return self._category_mapping.copy()

    def clear(self):
        """Clear all mappings."""
        self._legacy_to_api.clear()
        self._api_to_legacy.clear()
        self._category_mapping.clear()
        logger.info("Cleared all ID mappings")

    def __len__(self) -> int:
        """Get number of product mappings."""
        return len(self._legacy_to_api)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ProductIDMapper("
            f"products={len(self._legacy_to_api)}, "
            f"categories={len(self._category_mapping)})"
        )


# Global singleton instance
_global_mapper: Optional[ProductIDMapper] = None


def get_product_mapper() -> ProductIDMapper:
    """Get global product ID mapper instance.

    Returns:
        Global ProductIDMapper instance
    """
    global _global_mapper
    if _global_mapper is None:
        _global_mapper = ProductIDMapper()
    return _global_mapper


def reset_product_mapper():
    """Reset global product ID mapper."""
    global _global_mapper
    _global_mapper = None
