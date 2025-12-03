"""
Image URL utilities for WhatsApp carousel messages.

Provides helper functions to generate image URLs for menu items,
with support for custom hosted images and fallback to placeholder services.
"""

from typing import Optional, Dict

# High-quality free food images from Unsplash (no API key needed for these direct links)
# These are permanent, high-quality images that work great for carousels
DEFAULT_CATEGORY_IMAGES = {
    "pizzas": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800&h=600&fit=crop",
    "burgers": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&h=600&fit=crop",
    "sides": "https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=800&h=600&fit=crop",
    "drinks": "https://images.unsplash.com/photo-1437418747212-8d9709afab22?w=800&h=600&fit=crop",
    "desserts": "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=800&h=600&fit=crop",
    "default": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&h=600&fit=crop"  # Generic food
}

# Specific item images (high quality Unsplash photos)
ITEM_SPECIFIC_IMAGES = {
    # Pizzas
    "margherita pizza": "https://images.unsplash.com/photo-1604068549290-dea0e4a305ca?w=800&h=600&fit=crop",
    "pepperoni pizza": "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=800&h=600&fit=crop",
    "vegetarian pizza": "https://images.unsplash.com/photo-1511689660979-10d2b1aada49?w=800&h=600&fit=crop",
    "bbq chicken pizza": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&h=600&fit=crop",
    "hawaiian pizza": "https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=800&h=600&fit=crop",

    # Burgers
    "classic burger": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=800&h=600&fit=crop",
    "cheeseburger": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&h=600&fit=crop",
    "bacon burger": "https://images.unsplash.com/photo-1553979459-d2229ba7433b?w=800&h=600&fit=crop",
    "veggie burger": "https://images.unsplash.com/photo-1520072959219-c595dc870360?w=800&h=600&fit=crop",

    # Sides
    "french fries": "https://images.unsplash.com/photo-1576107232684-1279f390859f?w=800&h=600&fit=crop",
    "onion rings": "https://images.unsplash.com/photo-1639024471283-03518883512d?w=800&h=600&fit=crop",
    "mozzarella sticks": "https://images.unsplash.com/photo-1531749668029-2db88e4276c7?w=800&h=600&fit=crop",
    "caesar salad": "https://images.unsplash.com/photo-1546793665-c74683f339c1?w=800&h=600&fit=crop",

    # Drinks
    "coca-cola": "https://images.unsplash.com/photo-1554866585-cd94860890b7?w=800&h=600&fit=crop",
    "sprite": "https://images.unsplash.com/photo-1625772452859-1c03d5bf1137?w=800&h=600&fit=crop",
    "iced tea": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=800&h=600&fit=crop",
    "water": "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=800&h=600&fit=crop",

    # Desserts
    "chocolate brownie": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=800&h=600&fit=crop",
    "cheesecake": "https://images.unsplash.com/photo-1533134242820-f8d745a1c29e?w=800&h=600&fit=crop",
    "ice cream sundae": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=800&h=600&fit=crop",
}


def get_menu_item_image_url(
    item_name: str,
    category: str = "default",
    custom_url: Optional[str] = None
) -> str:
    """
    Get image URL for a menu item with intelligent fallback.

    Priority order:
    1. Custom URL (if provided)
    2. Item-specific image (matched by name)
    3. Category default image
    4. Generic food image

    Args:
        item_name: Name of the menu item (e.g., "Margherita Pizza")
        category: Category of the item (e.g., "pizzas", "burgers")
        custom_url: Optional custom image URL to use

    Returns:
        str: HTTPS URL to an image suitable for WhatsApp carousel

    Example:
        >>> get_menu_item_image_url("Margherita Pizza", "pizzas")
        "https://images.unsplash.com/photo-1604068549290..."

        >>> get_menu_item_image_url("Custom Item", "pizzas", "https://mycdn.com/item.jpg")
        "https://mycdn.com/item.jpg"
    """
    # 1. Use custom URL if provided
    if custom_url:
        return custom_url

    # 2. Try item-specific image
    item_key = item_name.lower().strip()
    if item_key in ITEM_SPECIFIC_IMAGES:
        return ITEM_SPECIFIC_IMAGES[item_key]

    # 3. Use category default
    category_key = category.lower().strip()
    if category_key in DEFAULT_CATEGORY_IMAGES:
        return DEFAULT_CATEGORY_IMAGES[category_key]

    # 4. Fall back to generic food image
    return DEFAULT_CATEGORY_IMAGES["default"]


def prepare_menu_items_for_carousel(
    menu_items: list[Dict],
    category: str,
    base_order_url: str = "https://yourshop.com/order"
) -> list[Dict]:
    """
    Prepare menu items with image URLs and order URLs for carousel.

    Takes raw menu items from RESTAURANT_MENU and enriches them with:
    - Image URLs (using intelligent fallback)
    - Order URLs (generated from item names)

    Args:
        menu_items: List of menu item dicts with name, price, description
        category: Category name (e.g., "pizzas", "burgers")
        base_order_url: Base URL for order links

    Returns:
        list[Dict]: Menu items ready for carousel with image_url and order_url

    Example:
        >>> from ai_companion.core.schedules import RESTAURANT_MENU
        >>> items = prepare_menu_items_for_carousel(
        ...     RESTAURANT_MENU["pizzas"],
        ...     "pizzas"
        ... )
        >>> items[0]["image_url"]
        "https://images.unsplash.com/photo-1604068549290..."
    """
    prepared_items = []

    for item in menu_items:
        # Generate order URL from item name
        item_slug = item["name"].lower().replace(" ", "-")
        order_url = f"{base_order_url}/{category}/{item_slug}"

        # Get image URL with fallback
        image_url = get_menu_item_image_url(
            item_name=item["name"],
            category=category,
            custom_url=item.get("image_url")  # Use if already in menu data
        )

        prepared_items.append({
            "name": item["name"],
            "description": item.get("description", ""),
            "price": item["price"],
            "image_url": image_url,
            "order_url": order_url,
            "category": category
        })

    return prepared_items


def get_all_menu_items_with_images(
    menu_dict: Dict,
    max_items: int = 10,
    base_order_url: str = "https://yourshop.com/order"
) -> list[Dict]:
    """
    Get all menu items from RESTAURANT_MENU with images and URLs.

    Useful for creating a carousel with mixed items from multiple categories.

    Args:
        menu_dict: RESTAURANT_MENU dictionary
        max_items: Maximum number of items to return (carousel limit is 10)
        base_order_url: Base URL for order links

    Returns:
        list[Dict]: Up to max_items menu items with images

    Example:
        >>> from ai_companion.core.schedules import RESTAURANT_MENU
        >>> items = get_all_menu_items_with_images(RESTAURANT_MENU, max_items=5)
        >>> len(items)
        5
    """
    all_items = []

    for category, items in menu_dict.items():
        prepared = prepare_menu_items_for_carousel(items, category, base_order_url)
        all_items.extend(prepared)

    # Return up to max_items
    return all_items[:max_items]


def get_featured_items_with_images(
    menu_dict: Dict,
    featured_names: list[str],
    base_order_url: str = "https://yourshop.com/order"
) -> list[Dict]:
    """
    Get specific featured menu items by name with images.

    Useful for creating promotional carousels with hand-picked items.

    Args:
        menu_dict: RESTAURANT_MENU dictionary
        featured_names: List of item names to feature
        base_order_url: Base URL for order links

    Returns:
        list[Dict]: Featured items with images

    Example:
        >>> from ai_companion.core.schedules import RESTAURANT_MENU
        >>> featured = get_featured_items_with_images(
        ...     RESTAURANT_MENU,
        ...     ["Margherita Pizza", "Classic Burger", "Chocolate Brownie"]
        ... )
        >>> len(featured)
        3
    """
    featured_items = []
    featured_set = set(name.lower() for name in featured_names)

    for category, items in menu_dict.items():
        for item in items:
            if item["name"].lower() in featured_set:
                prepared = prepare_menu_items_for_carousel([item], category, base_order_url)
                featured_items.extend(prepared)

    return featured_items


# Configuration: Update these if you have your own CDN
def set_custom_image_base_url(base_url: str):
    """
    Set a custom base URL for your hosted images.

    If you have images at https://cdn.yourshop.com/images/pizzas/margherita.jpg,
    call this with "https://cdn.yourshop.com/images"

    Args:
        base_url: Base URL for your image CDN
    """
    global CUSTOM_IMAGE_BASE_URL
    CUSTOM_IMAGE_BASE_URL = base_url


def get_custom_image_url(category: str, item_name: str) -> Optional[str]:
    """
    Generate URL for custom hosted images.

    Only returns a URL if CUSTOM_IMAGE_BASE_URL is set.

    Args:
        category: Item category
        item_name: Item name

    Returns:
        Optional[str]: URL if custom base is set, None otherwise
    """
    if hasattr(get_custom_image_url, 'CUSTOM_IMAGE_BASE_URL'):
        item_slug = item_name.lower().replace(" ", "-")
        return f"{CUSTOM_IMAGE_BASE_URL}/{category}/{item_slug}.jpg"
    return None


# Initialize
CUSTOM_IMAGE_BASE_URL = None
