# WhatsApp Carousel Messages - Quick Start Guide

## 30-Second Setup

```python
from ai_companion.interfaces.whatsapp.carousel_components import create_product_carousel
from ai_companion.interfaces.whatsapp.whatsapp_response import send_response

# 1. Prepare your products
products = [
    {
        "name": "Product 1",
        "description": "Great product",
        "price": 19.99,
        "image_url": "https://example.com/img1.jpg",
        "product_url": "https://shop.example.com/1"
    },
    {
        "name": "Product 2",
        "description": "Amazing product",
        "price": 29.99,
        "image_url": "https://example.com/img2.jpg",
        "product_url": "https://shop.example.com/2"
    }
]

# 2. Create carousel
carousel = create_product_carousel(products)

# 3. Send it
await send_response(
    from_number="1234567890",
    response_text="",
    message_type="interactive_carousel",
    phone_number_id=your_phone_id,
    whatsapp_token=your_token,
    interactive_component=carousel
)
```

Done! 🎉

## Common Use Cases

### Restaurant Menu

```python
from ai_companion.interfaces.whatsapp.carousel_components import create_restaurant_menu_carousel

menu_items = [
    {
        "name": "Margherita Pizza",
        "description": "Classic cheese",
        "price": 12.99,
        "image_url": "https://example.com/pizza1.jpg",
        "order_url": "https://order.example.com/1"
    },
    # Add 1-9 more items
]

carousel = create_restaurant_menu_carousel(menu_items)
```

### Promotional Offers

```python
from ai_companion.interfaces.whatsapp.carousel_components import create_offer_carousel

offers = [
    {
        "title": "50% Off First Order",
        "description": "New customers only",
        "image_url": "https://example.com/offer1.jpg",
        "offer_url": "https://shop.example.com/offer1"
    },
    # Add 1-9 more offers
]

carousel = create_offer_carousel(offers)
```

### Custom Carousel

```python
from ai_companion.interfaces.whatsapp.carousel_components import (
    create_carousel_card,
    create_carousel_component
)

cards = [
    create_carousel_card(
        card_index=0,
        header_type="image",
        media_link="https://example.com/img1.jpg",
        body_text="First item description",
        button_display_text="View",
        button_url="https://example.com/1"
    ),
    create_carousel_card(
        card_index=1,
        header_type="image",
        media_link="https://example.com/img2.jpg",
        body_text="Second item description",
        button_display_text="View",
        button_url="https://example.com/2"
    )
]

carousel = create_carousel_component(
    body_text="Check these out!",
    cards=cards
)
```

## Key Rules

✅ **DO:**
- Use 2-10 cards
- Use same media type for all cards (all images OR all videos)
- Keep button text under 20 characters
- Use HTTPS URLs
- Test on actual devices

❌ **DON'T:**
- Mix image and video headers in same carousel
- Use just 1 card (minimum is 2)
- Exceed 10 cards
- Use very long text (card body max 160 chars)
- Forget to validate URLs work

## Integration with Agent

```python
# In your graph node or handler
def show_products_node(state):
    products = get_featured_products()

    carousel = create_product_carousel(
        products=products,
        body_text="Browse our featured products!",
        button_text="View"
    )

    return {
        "messages": [AIMessage(content="Here are our featured items:")],
        "interactive_component": carousel,
        "message_type": "interactive_carousel"
    }
```

## Troubleshooting

**Error: "Carousel requires at least 2 cards"**
- Add more products/items to your list

**Error: "All cards must have the same header type"**
- Make sure all items use images OR all use videos, not mixed

**Error: "card_index must be between 0 and 9"**
- Use valid indexes (0, 1, 2, etc.) for your cards

**Carousel not displaying?**
- Check URLs are HTTPS and accessible
- Verify images are valid and load properly
- Ensure WhatsApp API credentials are correct
- Feature is available from November 11+

## Character Limits

| Field | Limit |
|-------|-------|
| Message body | 1024 characters |
| Card body | 160 characters |
| Button text | 20 characters |

## Need More Help?

- Full documentation: [docs/CAROUSEL_MESSAGES.md](./CAROUSEL_MESSAGES.md)
- Complete examples: [examples/carousel_example.py](../examples/carousel_example.py)
- Test it: `python examples/carousel_test_simple.py`

## Available Functions

```python
# Basic building blocks
create_carousel_card()        # Create individual cards
create_carousel_component()   # Assemble cards into carousel

# Convenience functions
create_product_carousel()           # For products/items
create_offer_carousel()             # For promotions
create_restaurant_menu_carousel()   # For menus
```

## Full API Reference

For complete API documentation, parameters, and advanced usage, see:
- [CAROUSEL_MESSAGES.md](./CAROUSEL_MESSAGES.md)
