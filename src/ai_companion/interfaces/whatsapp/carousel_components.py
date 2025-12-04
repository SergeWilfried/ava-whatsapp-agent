"""
Interactive media carousel message components for WhatsApp Business API.

This module provides helper functions to create horizontally scrollable carousel cards
with images or videos, each with a call-to-action button. Available for delivery to
WhatsApp users on November 11.

Requirements:
- Minimum 2 cards, maximum 10 cards
- Each card has a unique card_index (0-9)
- All cards must have the same header type (image or video)
- Message body is required (max 1024 characters)
- Each card must have a CTA button with display text (max 20 chars) and URL
"""

from typing import List, Dict, Optional, Literal


def create_carousel_card(
    card_index: int,
    header_type: Literal["image", "video"],
    media_link: str,
    body_text: str,
    button_display_text: str,
    button_url: str
) -> Dict:
    """
    Create a single carousel card.

    Args:
        card_index: Unique index for the card (0-9)
        header_type: "image" or "video"
        media_link: URL to the image or video file
        body_text: Card body text (max 160 characters, up to 2 line breaks)
        button_display_text: CTA button text (max 20 characters)
        button_url: Button destination URL

    Returns:
        dict: Card object for carousel

    Example:
        >>> card = create_carousel_card(
        ...     card_index=0,
        ...     header_type="image",
        ...     media_link="https://example.com/image1.png",
        ...     body_text="Exclusive deal #1",
        ...     button_display_text="Shop now",
        ...     button_url="https://shop.example.com/deal1"
        ... )
    """
    # Validate card_index
    if not 0 <= card_index <= 9:
        raise ValueError(f"card_index must be between 0 and 9, got {card_index}")

    # Validate header_type
    if header_type not in ["image", "video"]:
        raise ValueError(f"header_type must be 'image' or 'video', got {header_type}")

    # Build header based on type
    header = {
        "type": header_type,
        header_type: {
            "link": media_link
        }
    }

    # Build card structure
    card = {
        "card_index": card_index,
        "type": "cta_url",
        "header": header,
        "body": {
            "text": body_text[:160]  # Max 160 chars
        },
        "action": {
            "name": "cta_url",
            "parameters": {
                "display_text": button_display_text[:20],  # Max 20 chars
                "url": button_url
            }
        }
    }

    return card


def create_carousel_component(
    body_text: str,
    cards: List[Dict]
) -> Dict:
    """
    Create an interactive carousel component.

    Args:
        body_text: Main message body text (required, max 1024 characters)
        cards: List of card dictionaries (min 2, max 10 cards)
                Each card should be created using create_carousel_card()

    Returns:
        dict: Interactive carousel component for WhatsApp API

    Raises:
        ValueError: If cards list is invalid (wrong count, inconsistent types, etc.)

    Example:
        >>> cards = [
        ...     create_carousel_card(0, "image", "https://example.com/img1.png",
        ...                         "Deal 1", "Shop now", "https://shop.com/1"),
        ...     create_carousel_card(1, "image", "https://example.com/img2.png",
        ...                         "Deal 2", "Shop now", "https://shop.com/2")
        ... ]
        >>> carousel = create_carousel_component("Check out our latest offers!", cards)
    """
    # Validate cards count
    if len(cards) < 2:
        raise ValueError(f"Carousel requires at least 2 cards, got {len(cards)}")
    if len(cards) > 10:
        raise ValueError(f"Carousel supports maximum 10 cards, got {len(cards)}")

    # Validate all cards have the same header type
    header_types = {card.get("header", {}).get("type") for card in cards}
    if len(header_types) > 1:
        raise ValueError(
            f"All cards must have the same header type (image or video). "
            f"Found multiple types: {header_types}"
        )

    # Validate card indexes are unique and sequential
    card_indexes = {card.get("card_index") for card in cards}
    if len(card_indexes) != len(cards):
        raise ValueError("Each card must have a unique card_index")

    return {
        "type": "carousel",
        "body": {
            "text": body_text[:1024]  # Max 1024 chars
        },
        "action": {
            "cards": cards
        }
    }


def create_product_carousel(
    products: List[Dict],
    body_text: str = "Check out our featured products!",
    button_text: str = "View Product",
    header_type: Literal["image", "video"] = "image"
) -> Dict:
    """
    Create a product carousel from a list of product data.

    Convenience function for creating product-focused carousels.

    Args:
        products: List of product dicts with keys:
                 - name: Product name
                 - description: Product description (optional)
                 - image_url: Product image/video URL
                 - product_url: Link to product page
                 - price: Product price (optional, will be added to description)
        body_text: Main carousel message (max 1024 chars)
        button_text: Text for all CTA buttons (max 20 chars)
        header_type: "image" or "video" (default: "image")

    Returns:
        dict: Interactive carousel component

    Example:
        >>> products = [
        ...     {
        ...         "name": "Margherita Pizza",
        ...         "description": "Classic cheese pizza",
        ...         "price": 12.99,
        ...         "image_url": "https://example.com/pizza1.jpg",
        ...         "product_url": "https://shop.example.com/pizza/margherita"
        ...     },
        ...     {
        ...         "name": "Pepperoni Pizza",
        ...         "description": "Loaded with pepperoni",
        ...         "price": 14.99,
        ...         "image_url": "https://example.com/pizza2.jpg",
        ...         "product_url": "https://shop.example.com/pizza/pepperoni"
        ...     }
        ... ]
        >>> carousel = create_product_carousel(products)
    """
    if len(products) < 2:
        raise ValueError(f"Product carousel requires at least 2 products, got {len(products)}")
    if len(products) > 10:
        products = products[:10]  # Trim to max 10

    cards = []
    for idx, product in enumerate(products):
        # Build body text for card
        card_body = product.get("name", "Product")
        if product.get("description"):
            card_body += f"\n{product['description']}"
        if product.get("basePrice") is not None:
            card_body += f"\n${product['basePrice']:.2f}"

        # Create card
        # Support both product_url and order_url keys
        url = product.get("product_url") or product.get("order_url", "https://example.com")

        card = create_carousel_card(
            card_index=idx,
            header_type=header_type,
            media_link=product["image_url"],
            body_text=card_body,
            button_display_text=button_text,
            button_url=url
        )
        cards.append(card)

    return create_carousel_component(body_text, cards)


def create_offer_carousel(
    offers: List[Dict],
    body_text: str = "Limited time offers just for you!",
    button_text: str = "Claim Offer"
) -> Dict:
    """
    Create a promotional offers carousel.

    Args:
        offers: List of offer dicts with keys:
               - title: Offer title
               - description: Offer description (optional)
               - image_url: Offer banner image URL
               - offer_url: Link to claim/view offer
        body_text: Main carousel message (max 1024 chars)
        button_text: Text for all CTA buttons (max 20 chars)

    Returns:
        dict: Interactive carousel component

    Example:
        >>> offers = [
        ...     {
        ...         "title": "50% Off First Order",
        ...         "description": "New customers only",
        ...         "image_url": "https://example.com/offer1.jpg",
        ...         "offer_url": "https://shop.example.com/offers/first-order"
        ...     },
        ...     {
        ...         "title": "Free Delivery",
        ...         "description": "Orders over $25",
        ...         "image_url": "https://example.com/offer2.jpg",
        ...         "offer_url": "https://shop.example.com/offers/free-delivery"
        ...     }
        ... ]
        >>> carousel = create_offer_carousel(offers)
    """
    if len(offers) < 2:
        raise ValueError(f"Offer carousel requires at least 2 offers, got {len(offers)}")
    if len(offers) > 10:
        offers = offers[:10]  # Trim to max 10

    cards = []
    for idx, offer in enumerate(offers):
        # Build body text for card
        card_body = offer.get("title", "Special Offer")
        if offer.get("description"):
            card_body += f"\n{offer['description']}"

        # Create card
        card = create_carousel_card(
            card_index=idx,
            header_type="image",
            media_link=offer["image_url"],
            body_text=card_body,
            button_display_text=button_text,
            button_url=offer["offer_url"]
        )
        cards.append(card)

    return create_carousel_component(body_text, cards)


def create_restaurant_menu_carousel(
    menu_items: List[Dict],
    body_text: str = "Browse our delicious menu!",
    button_text: str = "Order Now"
) -> Dict:
    """
    Create a restaurant menu carousel.

    Specialized function for restaurant menu items with images.

    Args:
        menu_items: List of menu item dicts with keys:
                   - name: Item name
                   - description: Item description (optional)
                   - price: Item price
                   - image_url: Item image URL
                   - order_url: Link to order page for this item
        body_text: Main carousel message (max 1024 chars)
        button_text: Text for all CTA buttons (max 20 chars)

    Returns:
        dict: Interactive carousel component

    Example:
        >>> menu_items = [
        ...     {
        ...         "name": "Margherita Pizza",
        ...         "description": "Fresh mozzarella and basil",
        ...         "price": 12.99,
        ...         "image_url": "https://example.com/pizza1.jpg",
        ...         "order_url": "https://order.example.com/item/1"
        ...     },
        ...     {
        ...         "name": "BBQ Chicken Pizza",
        ...         "description": "Grilled chicken with BBQ sauce",
        ...         "price": 15.99,
        ...         "image_url": "https://example.com/pizza2.jpg",
        ...         "order_url": "https://order.example.com/item/2"
        ...     }
        ... ]
        >>> carousel = create_restaurant_menu_carousel(menu_items)
    """
    return create_product_carousel(
        products=menu_items,
        body_text=body_text,
        button_text=button_text,
        header_type="image"
    )
