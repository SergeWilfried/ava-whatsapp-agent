"""Menu adapter for integrating CartaAI API with existing CartService.

This adapter provides a compatibility layer between the API and existing code,
allowing gradual migration with feature flags.
"""

import logging
from typing import Dict, Optional, Tuple, List
import asyncio

from ai_companion.core.config import get_cartaai_config
from ai_companion.core.schedules import RESTAURANT_MENU, RESTAURANT_INFO
from ai_companion.services.cartaai import CartaAIClient, MenuService, MenuCache
from ai_companion.services.cartaai.product_mapper import get_product_mapper

logger = logging.getLogger(__name__)


class MenuAdapter:
    """Adapter for menu data access with API/mock fallback.

    This class provides a unified interface for accessing menu data,
    automatically switching between API and mock data based on feature flags.
    """

    def __init__(self):
        """Initialize menu adapter."""
        self.config = get_cartaai_config()
        self._client: Optional[CartaAIClient] = None
        self._menu_service: Optional[MenuService] = None
        self._cache: Optional[MenuCache] = None
        self._mapper = get_product_mapper()
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure API client and services are initialized."""
        if self._initialized:
            return

        # Debug logging to trace configuration
        logger.info("=" * 60)
        logger.info("MenuAdapter initialization check:")
        logger.info(f"  use_cartaai_api: {self.config.use_cartaai_api}")
        logger.info(f"  menu_api_enabled: {self.config.menu_api_enabled}")
        logger.info(f"  api_base_url: {self.config.api_base_url}")
        logger.info(f"  subdomain: {self.config.subdomain}")
        logger.info(f"  local_id: {self.config.local_id}")
        logger.info(f"  api_key: {'SET' if self.config.api_key else 'NOT SET'}")
        logger.info(f"  enable_api_logging: {self.config.enable_api_logging}")
        logger.info(f"  enable_cache: {self.config.enable_cache}")
        logger.info("=" * 60)

        if self.config.use_cartaai_api and self.config.menu_api_enabled:
            try:
                # Validate configuration
                if not self.config.validate():
                    logger.error("Invalid CartaAI configuration, falling back to mock data")
                    return

                # Create client
                self._client = CartaAIClient(
                    base_url=self.config.api_base_url,
                    subdomain=self.config.subdomain,
                    local_id=self.config.local_id,
                    api_key=self.config.api_key,
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries,
                    retry_delay=self.config.retry_delay,
                    max_concurrent_requests=self.config.max_concurrent_requests,
                    enable_logging=self.config.enable_api_logging,
                )

                # Ensure session is created
                await self._client._ensure_session()

                # Create cache
                if self.config.enable_cache:
                    self._cache = MenuCache(ttl_minutes=self.config.cache_ttl // 60)

                # Create menu service
                self._menu_service = MenuService(
                    self._client,
                    self._cache,
                    enable_cache=self.config.enable_cache,
                )

                # Build ID mappings - DISABLED: No longer using legacy IDs
                # await self._build_id_mappings()

                self._initialized = True
                logger.info("MenuAdapter initialized with API integration")

            except Exception as e:
                logger.error(f"Failed to initialize API client: {e}", exc_info=True)
                # Will fallback to mock data

    async def _build_id_mappings(self):
        """Build product ID mappings from API menu and mock menu."""
        try:
            # Fetch API menu
            menu_response = await self._menu_service.get_menu_structure()

            # Build mappings
            self._mapper.build_from_menu_structure(menu_response, RESTAURANT_MENU)

            logger.info(f"Built ID mappings: {len(self._mapper)} products")

        except Exception as e:
            logger.error(f"Failed to build ID mappings: {e}")

    async def find_menu_item(self, menu_item_id: str) -> Optional[Dict]:
        """Find menu item by ID (supports both legacy and API IDs).

        Args:
            menu_item_id: Legacy ID (e.g., "pizzas_0") or API ID (e.g., "prod001")

        Returns:
            Menu item dict or None if not found
        """
        await self._ensure_initialized()

        # Use API if enabled
        if (
            self.config.use_cartaai_api
            and self.config.menu_api_enabled
            and self._menu_service
        ):
            logger.info(f"🔵 Using API to find menu item: {menu_item_id}")
            try:
                return await self._find_menu_item_api(menu_item_id)
            except Exception as e:
                logger.error(f"API error finding menu item: {e}, falling back to mock")

        # Fallback to mock data
        logger.info(f"🟡 Using MOCK data to find menu item: {menu_item_id}")
        logger.info(f"  Reason: use_cartaai_api={self.config.use_cartaai_api}, menu_api_enabled={self.config.menu_api_enabled}, menu_service={'SET' if self._menu_service else 'NOT SET'}")
        return self._find_menu_item_mock(menu_item_id)

    async def _find_menu_item_api(self, menu_item_id: str) -> Optional[Dict]:
        """Find menu item using API.

        Args:
            menu_item_id: Menu item ID

        Returns:
            Menu item dict or None
        """
        # Use the product ID directly (API format)
        # Legacy ID mapping has been disabled - all IDs are now API IDs
        api_id = menu_item_id

        # Fetch from API
        product = await self._menu_service.get_product_by_id(api_id)

        if not product:
            return None

        # Convert API product to legacy format
        return self._convert_api_product_to_legacy(product, menu_item_id)

    def _convert_api_product_to_legacy(
        self, api_product: Dict, legacy_id: str
    ) -> Dict:
        """Convert API product format to legacy format.

        Args:
            api_product: Product from API
            legacy_id: Legacy ID to use

        Returns:
            Menu item in legacy format
        """
        return {
            "id": legacy_id,
            "api_id": api_product.get("_id"),
            "name": api_product.get("name", "Unknown Item"),
            "price": api_product.get("price") or api_product.get("basePrice", 0.0),
            "description": api_product.get("description", ""),
            "category": api_product.get("category", {}).get("name", "Other"),
            "is_available": api_product.get("isAvailable", True),
            "presentations": api_product.get("presentations", []),
            "modifiers": api_product.get("modifiers", []),
        }

    def _find_menu_item_mock(self, menu_item_id: str) -> Optional[Dict]:
        """Find menu item using mock data.

        Args:
            menu_item_id: Menu item ID in format "category_index"

        Returns:
            Menu item dict or None
        """
        try:
            parts = menu_item_id.split("_")
            if len(parts) >= 2:
                category = parts[0]
                index = int(parts[1])

                if category in RESTAURANT_MENU and index < len(
                    RESTAURANT_MENU[category]
                ):
                    item = RESTAURANT_MENU[category][index]
                    return {
                        "id": menu_item_id,
                        "name": item["name"],
                        "price": item["price"],
                        "description": item["description"],
                        "category": category,
                        "is_available": True,
                        "presentations": [],
                        "modifiers": [],
                    }
        except (ValueError, IndexError, KeyError) as e:
            logger.error(f"Error finding menu item {menu_item_id}: {e}")

        return None

    async def search_products(
        self, query: str, category: Optional[str] = None
    ) -> List[Dict]:
        """Search products by name.

        Args:
            query: Search query
            category: Optional category filter

        Returns:
            List of matching products
        """
        await self._ensure_initialized()

        # Use API if enabled
        if (
            self.config.use_cartaai_api
            and self.config.menu_api_enabled
            and self._menu_service
        ):
            try:
                # Get API category ID if category provided
                api_category_id = None
                if category:
                    api_category_id = self._mapper.get_api_category_id(category)

                results = await self._menu_service.search_products_by_name(
                    query, api_category_id
                )

                # Convert to legacy format
                return [
                    self._convert_api_product_to_legacy(p, f"search_{p.get('id')}")
                    for p in results
                ]

            except Exception as e:
                logger.error(f"API error searching products: {e}")

        # Fallback to mock search
        return self._search_products_mock(query, category)

    def _search_products_mock(
        self, query: str, category: Optional[str] = None
    ) -> List[Dict]:
        """Search products in mock data.

        Args:
            query: Search query
            category: Optional category filter

        Returns:
            List of matching products
        """
        results = []
        query_lower = query.lower()

        categories_to_search = (
            [category] if category and category in RESTAURANT_MENU else RESTAURANT_MENU.keys()
        )

        for cat_key in categories_to_search:
            items = RESTAURANT_MENU.get(cat_key, [])
            for index, item in enumerate(items):
                name = item.get("name", "").lower()
                description = item.get("description", "").lower()

                if query_lower in name or query_lower in description:
                    results.append(
                        {
                            "id": f"{cat_key}_{index}",
                            "name": item["name"],
                            "price": item["price"],
                            "description": item["description"],
                            "category": cat_key,
                            "is_available": True,
                        }
                    )

        return results

    async def get_menu_structure(self) -> Dict:
        """Get complete menu structure.

        Returns:
            Menu structure (API format or converted from mock)
        """
        await self._ensure_initialized()

        # Use API if enabled
        if (
            self.config.use_cartaai_api
            and self.config.menu_api_enabled
            and self._menu_service
        ):
            logger.info("🔵 Using API to get menu structure")
            try:
                return await self._menu_service.get_menu_structure()
            except Exception as e:
                logger.error(f"API error getting menu structure: {e}")

        # Fallback to mock data
        logger.info("🟡 Using MOCK data to get menu structure")
        logger.info(f"  Reason: use_cartaai_api={self.config.use_cartaai_api}, menu_api_enabled={self.config.menu_api_enabled}, menu_service={'SET' if self._menu_service else 'NOT SET'}")
        return self._get_mock_menu_structure()

    def _get_mock_menu_structure(self) -> Dict:
        """Get menu structure from mock data in API-like format.

        Returns:
            Menu structure dict
        """
        categories = []

        for cat_key, items in RESTAURANT_MENU.items():
            products = [
                {
                    "id": f"{cat_key}_{index}",
                    "name": item["name"],
                    "basePrice": item["price"],
                    "description": item["description"],
                    "isAvailable": True,
                }
                for index, item in enumerate(items)
            ]

            categories.append(
                {
                    "id": cat_key,
                    "name": cat_key.capitalize(),
                    "products": products,
                }
            )

        return {"type": "1", "data": {"categories": categories}}

    async def invalidate_cache(self):
        """Invalidate menu cache."""
        if self._menu_service:
            await self._menu_service.invalidate_menu_cache()

    async def preload_menu(self):
        """Preload menu into cache."""
        await self._ensure_initialized()

        if self._menu_service:
            await self._menu_service.preload_menu()

    async def close(self):
        """Close API client connection."""
        if self._client:
            await self._client.close()

    def get_restaurant_info(self) -> Dict:
        """Get restaurant information.

        For now, returns mock data. Future: fetch from API.

        Returns:
            Restaurant info dict
        """
        return RESTAURANT_INFO

    def __repr__(self) -> str:
        """String representation."""
        mode = "API" if (self.config.use_cartaai_api and self.config.menu_api_enabled) else "Mock"
        return f"MenuAdapter(mode={mode}, initialized={self._initialized})"


# Global singleton instance
_global_adapter: Optional[MenuAdapter] = None


def get_menu_adapter() -> MenuAdapter:
    """Get global menu adapter instance.

    Returns:
        Global MenuAdapter instance
    """
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = MenuAdapter()
    return _global_adapter


async def initialize_menu_adapter():
    """Initialize global menu adapter (call on startup)."""
    adapter = get_menu_adapter()
    await adapter._ensure_initialized()
    logger.info(f"Menu adapter initialized: {adapter}")


def reset_menu_adapter():
    """Reset global menu adapter (useful for testing)."""
    global _global_adapter
    if _global_adapter:
        # Schedule cleanup in event loop if it exists
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_global_adapter.close())
        except RuntimeError:
            pass
    _global_adapter = None
