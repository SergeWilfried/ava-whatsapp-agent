"""Menu service with caching for CartaAI API."""

from typing import Dict, List, Optional, Any
import logging

from .client import CartaAIClient
from .cache import MenuCache

logger = logging.getLogger(__name__)


class MenuService:
    """High-level service for menu operations with caching.

    Features:
    - Automatic caching of menu data
    - Product lookup and search
    - Category management
    - Cache invalidation

    Example:
        menu_service = MenuService(client, cache)
        menu = await menu_service.get_menu_structure()
        product = await menu_service.get_product_by_id("prod001")
    """

    def __init__(
        self,
        client: CartaAIClient,
        cache: Optional[MenuCache] = None,
        enable_cache: bool = True,
    ):
        """Initialize menu service.

        Args:
            client: CartaAI API client
            cache: Menu cache instance (creates default if None)
            enable_cache: Enable/disable caching
        """
        self.client = client
        self.enable_cache = enable_cache

        if cache is None and enable_cache:
            self.cache = MenuCache(ttl_minutes=15)
        else:
            self.cache = cache

    def _get_cache_key(self, key_type: str, identifier: str = "") -> str:
        """Generate cache key.

        Args:
            key_type: Type of data (menu, product, category)
            identifier: Optional identifier (product ID, category ID)

        Returns:
            Cache key string
        """
        subdomain = self.client.subdomain
        local_id = self.client.local_id or "default"

        if identifier:
            return f"{key_type}:{subdomain}:{local_id}:{identifier}"
        return f"{key_type}:{subdomain}:{local_id}"

    async def get_menu_structure(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get complete menu structure with caching.

        Args:
            force_refresh: Force refresh from API, bypass cache

        Returns:
            Menu structure response
            {
                "type": "1",
                "data": {
                    "categories": [...]
                }
            }
        """
        cache_key = self._get_cache_key("menu", "structure")

        # Check cache
        if self.enable_cache and not force_refresh:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.info("Menu structure retrieved from cache")
                return cached

        # Fetch from API
        logger.info("Fetching menu structure from API")
        menu_data = await self.client.get_menu_structure()

        # Cache result
        if self.enable_cache and menu_data.get("type") == "1":
            await self.cache.set(cache_key, menu_data)

        return menu_data

    async def get_all_categories(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get all categories with caching.

        Args:
            force_refresh: Force refresh from API

        Returns:
            Categories response
        """
        cache_key = self._get_cache_key("categories", "all")

        # Check cache
        if self.enable_cache and not force_refresh:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.info("Categories retrieved from cache")
                return cached

        # Fetch from API
        logger.info("Fetching categories from API")
        categories = await self.client.get_all_categories()

        # Cache result
        if self.enable_cache and categories.get("type") == "1":
            await self.cache.set(cache_key, categories)

        return categories

    async def get_product_details(
        self,
        product_ids: List[str],
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get detailed product information with caching.

        This method caches individual products and fetches only
        uncached products from the API.

        Args:
            product_ids: List of product IDs
            force_refresh: Force refresh from API

        Returns:
            List of product details
        """
        if not product_ids:
            return []

        cached_products = []
        uncached_ids = []

        # Check cache for each product
        if self.enable_cache and not force_refresh:
            for product_id in product_ids:
                cache_key = self._get_cache_key("product", product_id)
                cached = await self.cache.get(cache_key)

                if cached:
                    cached_products.append(cached)
                else:
                    uncached_ids.append(product_id)
        else:
            uncached_ids = product_ids

        # Fetch uncached products from API
        if uncached_ids:
            logger.info(f"Fetching {len(uncached_ids)} products from API")
            response = await self.client.get_product_details(uncached_ids)

            if response.get("success"):
                fresh_products = response.get("data", [])

                # Cache each product
                if self.enable_cache:
                    for product in fresh_products:
                        product_id = product.get("_id")
                        if product_id:
                            cache_key = self._get_cache_key("product", product_id)
                            await self.cache.set(cache_key, product)

                cached_products.extend(fresh_products)

        return cached_products

    async def get_product_by_id(
        self,
        product_id: str,
        force_refresh: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Get single product by ID.

        Args:
            product_id: Product ID
            force_refresh: Force refresh from API

        Returns:
            Product details or None if not found
        """
        products = await self.get_product_details([product_id], force_refresh)
        return products[0] if products else None

    async def search_products_by_name(
        self,
        query: str,
        category_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search products by name.

        Args:
            query: Search query
            category_id: Optional category filter

        Returns:
            List of matching products
        """
        # Get menu structure
        menu = await self.get_menu_structure()

        if menu.get("type") != "1":
            return []

        categories = menu["data"].get("categories", [])
        results = []

        # Filter by category if specified
        if category_id:
            categories = [c for c in categories if c.get("id") == category_id]

        # Search products
        query_lower = query.lower()
        for category in categories:
            for product in category.get("products", []):
                name = product.get("name", "").lower()
                description = product.get("description", "").lower()

                if query_lower in name or query_lower in description:
                    results.append(product)

        logger.info(f"Search '{query}' found {len(results)} products")
        return results

    async def get_category_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get category by ID.

        Args:
            category_id: Category ID

        Returns:
            Category data or None if not found
        """
        menu = await self.get_menu_structure()

        if menu.get("type") != "1":
            return None

        categories = menu["data"].get("categories", [])

        for category in categories:
            if category.get("id") == category_id:
                return category

        return None

    async def get_products_by_category(
        self,
        category_id: str,
    ) -> List[Dict[str, Any]]:
        """Get all products in a category.

        Args:
            category_id: Category ID

        Returns:
            List of products in category
        """
        category = await self.get_category_by_id(category_id)

        if category:
            return category.get("products", [])

        return []

    async def is_product_available(self, product_id: str) -> bool:
        """Check if product is available.

        Args:
            product_id: Product ID

        Returns:
            True if available, False otherwise
        """
        product = await self.get_product_by_id(product_id)

        if product:
            return product.get("isAvailable", True)

        return False

    async def get_product_price(self, product_id: str) -> Optional[float]:
        """Get product base price.

        Args:
            product_id: Product ID

        Returns:
            Base price or None if not found
        """
        product = await self.get_product_by_id(product_id)

        if product:
            return product.get("price") or product.get("basePrice")

        return None

    async def invalidate_menu_cache(self):
        """Invalidate all menu-related cache."""
        if self.enable_cache:
            await self.cache.invalidate_pattern(f"menu:{self.client.subdomain}:*")
            await self.cache.invalidate_pattern(f"categories:{self.client.subdomain}:*")
            await self.cache.invalidate_pattern(f"product:{self.client.subdomain}:*")
            logger.info("Menu cache invalidated")

    async def invalidate_product_cache(self, product_id: str):
        """Invalidate specific product cache.

        Args:
            product_id: Product ID to invalidate
        """
        if self.enable_cache:
            cache_key = self._get_cache_key("product", product_id)
            await self.cache.invalidate(cache_key)
            logger.info(f"Product cache invalidated: {product_id}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics dictionary
        """
        if self.enable_cache:
            return self.cache.get_stats()
        return {"cache_disabled": True}

    async def preload_menu(self):
        """Preload menu data into cache.

        Useful for warming up cache on application startup.
        """
        logger.info("Preloading menu data into cache...")

        # Load menu structure
        menu = await self.get_menu_structure(force_refresh=True)

        # Load all product IDs from menu
        if menu.get("type") == "1":
            categories = menu["data"].get("categories", [])
            all_product_ids = []

            for category in categories:
                for product in category.get("products", []):
                    product_id = product.get("id")
                    if product_id:
                        all_product_ids.append(product_id)

            # Load product details in batches
            batch_size = 10
            for i in range(0, len(all_product_ids), batch_size):
                batch = all_product_ids[i : i + batch_size]
                await self.get_product_details(batch, force_refresh=True)

            logger.info(f"Preloaded {len(all_product_ids)} products")

    def __repr__(self) -> str:
        """String representation."""
        cache_status = "enabled" if self.enable_cache else "disabled"
        return (
            f"MenuService("
            f"subdomain={self.client.subdomain}, "
            f"cache={cache_status})"
        )
