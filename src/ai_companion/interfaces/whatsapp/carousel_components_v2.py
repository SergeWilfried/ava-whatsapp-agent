"""Updated carousel components with API support.

This module provides carousel component creators that work with both
mock data and API product data.
"""

from typing import List, Dict, Optional, Literal
import logging

logger = logging.getLogger(__name__)


def create_carousel_card(
    card_index: int,
    header_type: Literal["image", "video"],
    media_link: str,
    body_text: str,
    button_display_text: str,
    button_url: str,
) -> Dict:
    """Create a single carousel card.

    Args:
        card_index: Unique index for the card (0-9)
        header_type: "image" or "video"
        media_link: URL to the image or video file
        body_text: Card body text (max 160 characters)
        button_display_text: CTA button text (max 20 characters)
        button_url: Button destination URL

    Returns:
        Card object for carousel
    """
    if not 0 <= card_index <= 9:
        raise ValueError(f"card_index must be between 0 and 9, got {card_index}")

    if header_type not in ["image", "video"]:
        raise ValueError(f"header_type must be 'image' or 'video', got {header_type}")

    header = {"type": header_type, header_type: {"link": media_link}}

    card = {
        "card_index": card_index,
        "type": "cta_url",
        "header": header,
        "body": {"text": body_text[:160]},
        "action": {
            "name": "cta_url",
            "parameters": {
                "display_text": button_display_text[:20],
                "url": button_url,
            },
        },
    }

    return card


def create_carousel_component(body_text: str, cards: List[Dict]) -> Dict:
    """Create an interactive carousel component.

    Args:
        body_text: Main message body text (max 1024 characters)
        cards: List of card dictionaries (min 2, max 10)

    Returns:
        Interactive carousel component for WhatsApp API

    Raises:
        ValueError: If cards list is invalid
    """
    if len(cards) < 2:
        raise ValueError(f"Carousel requires at least 2 cards, got {len(cards)}")
    if len(cards) > 10:
        raise ValueError(f"Carousel supports maximum 10 cards, got {len(cards)}")

    header_types = {card.get("header", {}).get("type") for card in cards}
    if len(header_types) > 1:
        raise ValueError(
            f"All cards must have the same header type. Found: {header_types}"
        )

    card_indexes = {card.get("card_index") for card in cards}
    if len(card_indexes) != len(cards):
        raise ValueError("Each card must have a unique card_index")

    return {
        "type": "carousel",
        "body": {"text": body_text[:1024]},
        "action": {"cards": cards},
    }


def create_product_carousel(
    products: List[Dict],
    body_text: str = "Check out our featured products!",
    button_text: str = "View Product",
    header_type: Literal["image", "video"] = "image",
    default_image_url: str = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800",
    use_api_format: bool = True,
) -> Dict:
    """Create a product carousel from products list.

    Supports both API product format and legacy format.

    Args:
        products: List of product dicts (API or legacy format)
        body_text: Main carousel message
        button_text: Text for CTA buttons
        header_type: "image" or "video"
        default_image_url: Fallback image if product has no image
        use_api_format: Whether products are in API format

    API Format:
        {
            "id" or "_id": "prod001",
            "name": "Classic Burger",
            "description": "Juicy beef patty",
            "price" or "basePrice": 15.99,
            "imageUrl": "https://...",
            "isAvailable": true
        }

    Legacy Format:
        {
            "name": "Classic Burger",
            "description": "...",
            "price": 15.99,
            "image_url": "https://...",
            "product_url": "https://..."
        }

    Returns:
        Interactive carousel component
    """
    if len(products) < 2:
        logger.warning(f"Product carousel requires at least 2 products, got {len(products)}")
        raise ValueError(f"Product carousel requires at least 2 products, got {len(products)}")

    if len(products) > 10:
        logger.warning(f"Trimming products from {len(products)} to 10 (WhatsApp limit)")
        products = products[:10]

    cards = []

    for idx, product in enumerate(products):
        # Extract fields based on format
        if use_api_format:
            product_id = product.get("_id") or product.get("id", f"prod_{idx}")
            product_name = product.get("name", "Unknown Product")
            product_desc = product.get("description", "")
            product_price = product.get("price") or product.get("basePrice", 0.0)
            product_image = product.get("imageUrl") or default_image_url
            is_available = product.get("isAvailable", True)

            # Build order URL (WhatsApp deep link)
            product_url = f"https://wa.me/?text=Order:{product_id}"

        else:
            # Legacy format
            product_id = product.get("id", f"prod_{idx}")
            product_name = product.get("name", "Unknown Product")
            product_desc = product.get("description", "")
            product_price = product.get("price", 0.0)
            product_image = product.get("image_url") or default_image_url
            is_available = True
            product_url = product.get("product_url", f"https://wa.me/?text=Order:{product_id}")

        # Skip unavailable products
        if not is_available:
            logger.debug(f"Skipping unavailable product: {product_name}")
            continue

        # Build card body text
        card_body = product_name

        if product_desc:
            # Truncate description to fit in 160 char limit
            desc_limit = 160 - len(product_name) - len(f"\n${product_price:.2f}") - 5
            if len(product_desc) > desc_limit:
                product_desc = product_desc[:desc_limit - 3] + "..."
            card_body += f"\n{product_desc}"

        if product_price > 0:
            card_body += f"\n${product_price:.2f}"

        # Create card
        try:
            card = create_carousel_card(
                card_index=idx,
                header_type=header_type,
                media_link=product_image,
                body_text=card_body,
                button_display_text=button_text,
                button_url=product_url,
            )
            cards.append(card)

        except Exception as e:
            logger.error(f"Error creating card for product {product_name}: {e}")
            continue

    # Validate we have at least 2 cards
    if len(cards) < 2:
        raise ValueError(
            f"Failed to create at least 2 valid cards (got {len(cards)}). "
            "Check product data and availability."
        )

    return create_carousel_component(body_text, cards)


def create_category_products_carousel(
    category_name: str,
    products: List[Dict],
    button_text: str = "Order Now",
    use_api_format: bool = True,
) -> Dict:
    """Create a carousel for products in a specific category.

    Args:
        category_name: Name of the category
        products: List of products in API or legacy format
        button_text: Text for CTA buttons
        use_api_format: Whether products are in API format

    Returns:
        Interactive carousel component
    """
    emoji = _get_category_emoji(category_name)
    body_text = f"{emoji} {category_name}\n\nSwipe to browse our {category_name.lower()} selection:"

    return create_product_carousel(
        products=products,
        body_text=body_text,
        button_text=button_text,
        use_api_format=use_api_format,
    )


def create_api_menu_carousel(
    api_menu_structure: Dict,
    category_id: Optional[str] = None,
    max_products: int = 10,
) -> Dict:
    """Create carousel from API menu structure.

    Args:
        api_menu_structure: Menu structure from API (bot-structure response)
        category_id: Optional category ID to filter
        max_products: Maximum products to show

    Returns:
        Interactive carousel component

    Example:
        menu = await menu_service.get_menu_structure()
        carousel = create_api_menu_carousel(menu, category_id="cat001")
    """
    if api_menu_structure.get("type") != "1":
        raise ValueError("Invalid API menu structure")

    categories = api_menu_structure.get("data", {}).get("categories", [])

    # Filter by category if specified
    if category_id:
        categories = [c for c in categories if c.get("id") == category_id]
        if not categories:
            raise ValueError(f"Category {category_id} not found")

    # Collect products from categories
    all_products = []
    for category in categories:
        for product in category.get("products", []):
            # Add category info to product for context
            product_with_cat = product.copy()
            product_with_cat["category_name"] = category.get("name", "Menu")
            all_products.append(product_with_cat)

    if not all_products:
        raise ValueError("No products found in menu structure")

    # Limit to max_products
    all_products = all_products[:max_products]

    # Determine body text
    if category_id and categories:
        category_name = categories[0].get("name", "Menu")
        body_text = f"Browse our {category_name} selection:"
    else:
        body_text = "Browse our menu:"

    return create_product_carousel(
        products=all_products,
        body_text=body_text,
        button_text="Order",
        use_api_format=True,
    )


def create_offer_carousel(
    offers: List[Dict],
    body_text: str = "Limited time offers just for you!",
    button_text: str = "Claim Offer",
) -> Dict:
    """Create a promotional offers carousel.

    Args:
        offers: List of offer dicts
        body_text: Main carousel message
        button_text: Text for CTA buttons

    Returns:
        Interactive carousel component
    """
    if len(offers) < 2:
        raise ValueError(f"Offer carousel requires at least 2 offers, got {len(offers)}")

    if len(offers) > 10:
        offers = offers[:10]

    cards = []
    for idx, offer in enumerate(offers):
        card_body = offer.get("title", "Special Offer")
        if offer.get("description"):
            card_body += f"\n{offer['description']}"

        card = create_carousel_card(
            card_index=idx,
            header_type="image",
            media_link=offer["image_url"],
            body_text=card_body,
            button_display_text=button_text,
            button_url=offer["offer_url"],
        )
        cards.append(card)

    return create_carousel_component(body_text, cards)


def _get_category_emoji(category_name: str) -> str:
    """Get emoji for category name.

    Args:
        category_name: Category name

    Returns:
        Emoji string
    """
    name_lower = category_name.lower()

    emoji_map = {
        "pizza": "🍕",
        "burger": "🍔",
        "side": "🍟",
        "drink": "🥤",
        "dessert": "🍰",
        "salad": "🥗",
        "pasta": "🍝",
        "soup": "🍜",
        "sandwich": "🥪",
        "chicken": "🍗",
        "seafood": "🦐",
        "breakfast": "🍳",
        "coffee": "☕",
        "ice cream": "🍦",
    }

    for key, emoji in emoji_map.items():
        if key in name_lower:
            return emoji

    return "🍽️"


# Backward compatibility alias
create_menu_carousel = create_product_carousel
