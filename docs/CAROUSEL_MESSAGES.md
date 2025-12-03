# WhatsApp Interactive Media Carousel Messages

## Overview

Interactive media carousel messages enable businesses to send horizontally scrollable cards with images or videos, each with a call-to-action (CTA) button, within WhatsApp conversations. This format allows users to browse multiple offers or content in a single message.

**Available:** November 11 for delivery to WhatsApp users

## Features

- **2-10 cards per carousel**: Minimum 2 cards, maximum 10 cards
- **Rich media**: Each card supports either an image or video header
- **Call-to-action buttons**: Each card includes a clickable CTA button with custom text and URL
- **Consistent design**: All cards must use the same header type (all images or all videos)
- **Body text**: Required message body text (max 1024 characters)
- **Card descriptions**: Each card can have body text (max 160 characters, up to 2 line breaks)

## Requirements

### Card Requirements
- **card_index**: Unique integer 0-9 for each card
- **type**: Must be `"cta_url"`
- **header.type**: Either `"image"` or `"video"` (all cards must match)
- **header media link**: URL to the image or video file
- **body.text**: Card description (max 160 characters)
- **action.name**: Must be `"cta_url"`
- **action.parameters.display_text**: Button text (max 20 characters)
- **action.parameters.url**: Button destination URL

### Message Requirements
- **body.text**: Required main message body (max 1024 characters)
- **No header, footer, or buttons**: Outside of cards - only body text and cards array

## API Structure

### Complete Request Example

```json
{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "1234567890",
  "type": "interactive",
  "interactive": {
    "type": "carousel",
    "body": {
      "text": "Check out our latest offers!"
    },
    "action": {
      "cards": [
        {
          "card_index": 0,
          "type": "cta_url",
          "header": {
            "type": "image",
            "image": {
              "link": "https://example.com/image1.png"
            }
          },
          "body": {
            "text": "Exclusive deal #1"
          },
          "action": {
            "name": "cta_url",
            "parameters": {
              "display_text": "Shop now",
              "url": "https://shop.example.com/deal1"
            }
          }
        },
        {
          "card_index": 1,
          "type": "cta_url",
          "header": {
            "type": "image",
            "image": {
              "link": "https://example.com/image2.png"
            }
          },
          "body": {
            "text": "Exclusive deal #2"
          },
          "action": {
            "name": "cta_url",
            "parameters": {
              "display_text": "Shop now",
              "url": "https://shop.example.com/deal2"
            }
          }
        }
      ]
    }
  }
}
```

## Python Implementation

### Basic Usage

```python
from ai_companion.interfaces.whatsapp.carousel_components import (
    create_carousel_card,
    create_carousel_component
)
from ai_companion.interfaces.whatsapp.whatsapp_response import send_response

# Create individual cards
cards = [
    create_carousel_card(
        card_index=0,
        header_type="image",
        media_link="https://example.com/pizza1.jpg",
        body_text="Margherita Pizza\n$12.99",
        button_display_text="Order Now",
        button_url="https://order.example.com/pizza/1"
    ),
    create_carousel_card(
        card_index=1,
        header_type="image",
        media_link="https://example.com/pizza2.jpg",
        body_text="Pepperoni Pizza\n$14.99",
        button_display_text="Order Now",
        button_url="https://order.example.com/pizza/2"
    )
]

# Create carousel component
carousel = create_carousel_component(
    body_text="Check out our delicious pizzas! 🍕",
    cards=cards
)

# Send the carousel message
await send_response(
    from_number="1234567890",
    response_text="",  # Not used for carousels
    message_type="interactive_carousel",
    phone_number_id=phone_number_id,
    whatsapp_token=whatsapp_token,
    interactive_component=carousel
)
```

### Product Carousel

Quickly create product carousels from structured data:

```python
from ai_companion.interfaces.whatsapp.carousel_components import create_product_carousel

products = [
    {
        "name": "Margherita Pizza",
        "description": "Fresh mozzarella and basil",
        "price": 12.99,
        "image_url": "https://example.com/pizza1.jpg",
        "product_url": "https://order.example.com/pizza/1"
    },
    {
        "name": "Pepperoni Pizza",
        "description": "Loaded with pepperoni",
        "price": 14.99,
        "image_url": "https://example.com/pizza2.jpg",
        "product_url": "https://order.example.com/pizza/2"
    }
]

carousel = create_product_carousel(
    products=products,
    body_text="Browse our pizza menu! 🍕",
    button_text="Order Now"
)

await send_response(
    from_number="1234567890",
    message_type="interactive_carousel",
    phone_number_id=phone_number_id,
    whatsapp_token=whatsapp_token,
    interactive_component=carousel
)
```

### Offer Carousel

Create promotional offer carousels:

```python
from ai_companion.interfaces.whatsapp.carousel_components import create_offer_carousel

offers = [
    {
        "title": "50% Off First Order",
        "description": "New customers only",
        "image_url": "https://example.com/offer1.jpg",
        "offer_url": "https://shop.example.com/offers/first"
    },
    {
        "title": "Free Delivery",
        "description": "Orders over $25",
        "image_url": "https://example.com/offer2.jpg",
        "offer_url": "https://shop.example.com/offers/delivery"
    }
]

carousel = create_offer_carousel(
    offers=offers,
    body_text="🎉 Special offers just for you!",
    button_text="Claim Offer"
)
```

### Restaurant Menu Carousel

Specialized function for restaurant menus:

```python
from ai_companion.interfaces.whatsapp.carousel_components import create_restaurant_menu_carousel

menu_items = [
    {
        "name": "Margherita Pizza",
        "description": "Classic cheese pizza",
        "price": 12.99,
        "image_url": "https://example.com/pizza1.jpg",
        "order_url": "https://order.example.com/item/1"
    },
    {
        "name": "Pepperoni Pizza",
        "description": "Loaded with pepperoni",
        "price": 14.99,
        "image_url": "https://example.com/pizza2.jpg",
        "order_url": "https://order.example.com/item/2"
    }
]

carousel = create_restaurant_menu_carousel(
    menu_items=menu_items,
    body_text="Browse our delicious menu! 😋",
    button_text="Order Now"
)
```

### Video Carousel

Create carousels with video headers:

```python
cards = [
    create_carousel_card(
        card_index=0,
        header_type="video",
        media_link="https://example.com/video1.mp4",
        body_text="See how we make our pizza!",
        button_display_text="Watch More",
        button_url="https://example.com/videos"
    ),
    create_carousel_card(
        card_index=1,
        header_type="video",
        media_link="https://example.com/video2.mp4",
        body_text="Fast delivery guaranteed",
        button_display_text="Order Now",
        button_url="https://order.example.com"
    )
]

carousel = create_carousel_component(
    body_text="Experience our restaurant! 🎥",
    cards=cards
)
```

## API Functions Reference

### `create_carousel_card()`

Create a single carousel card.

**Parameters:**
- `card_index` (int): Unique index 0-9 for the card
- `header_type` (Literal["image", "video"]): Type of media header
- `media_link` (str): URL to the media file
- `body_text` (str): Card description (max 160 chars)
- `button_display_text` (str): CTA button text (max 20 chars)
- `button_url` (str): Button destination URL

**Returns:** dict - Card object

**Raises:** ValueError if parameters are invalid

### `create_carousel_component()`

Create an interactive carousel component from cards.

**Parameters:**
- `body_text` (str): Main message body (max 1024 chars)
- `cards` (List[Dict]): List of card objects (2-10 cards)

**Returns:** dict - Interactive carousel component

**Raises:** ValueError if cards are invalid (wrong count, mismatched types, etc.)

### `create_product_carousel()`

Create a product carousel from structured product data.

**Parameters:**
- `products` (List[Dict]): Product data (name, description, price, image_url, product_url)
- `body_text` (str): Main message (default: "Check out our featured products!")
- `button_text` (str): CTA button text (default: "View Product")
- `header_type` (Literal["image", "video"]): Media type (default: "image")

**Returns:** dict - Interactive carousel component

### `create_offer_carousel()`

Create a promotional offers carousel.

**Parameters:**
- `offers` (List[Dict]): Offer data (title, description, image_url, offer_url)
- `body_text` (str): Main message (default: "Limited time offers just for you!")
- `button_text` (str): CTA button text (default: "Claim Offer")

**Returns:** dict - Interactive carousel component

### `create_restaurant_menu_carousel()`

Create a restaurant menu carousel.

**Parameters:**
- `menu_items` (List[Dict]): Menu item data (name, description, price, image_url, order_url)
- `body_text` (str): Main message (default: "Browse our delicious menu!")
- `button_text` (str): CTA button text (default: "Order Now")

**Returns:** dict - Interactive carousel component

## Best Practices

### 1. Image/Video Quality
- Use high-quality images (recommended: 1200x630 pixels)
- Optimize file sizes for fast loading
- Ensure all images have consistent aspect ratios
- Use HTTPS URLs for all media

### 2. Text Content
- Keep card body text concise (under 160 characters)
- Use emojis strategically to attract attention
- Make button text action-oriented ("Order Now", "Shop", "Learn More")
- Ensure button text is under 20 characters

### 3. URL Structure
- Use trackable URLs to measure engagement
- Include UTM parameters for analytics
- Ensure URLs lead to mobile-optimized pages
- Use deep links when possible for app users

### 4. User Experience
- Present similar items (all products, all offers, etc.)
- Order cards by relevance or popularity
- Limit to 3-5 cards for better engagement (max 10 allowed)
- Test on actual devices before deploying

### 5. Business Use Cases
- **E-commerce**: Product showcases, sales, new arrivals
- **Restaurants**: Menu items, daily specials, meal deals
- **Real Estate**: Property listings, virtual tours
- **Travel**: Destination packages, hotel options
- **Events**: Event highlights, ticket options

## Error Handling

The carousel functions include validation and will raise `ValueError` for:
- Invalid card_index (not 0-9)
- Wrong header_type (not "image" or "video")
- Too few cards (< 2)
- Too many cards (> 10)
- Mismatched header types across cards
- Duplicate card indexes

Example error handling:

```python
try:
    carousel = create_carousel_component(body_text="Test", cards=cards)
except ValueError as e:
    print(f"Carousel validation error: {e}")
    # Handle error appropriately
```

## Testing

Run the example file to see all carousel types:

```bash
python examples/carousel_example.py
```

To send actual test messages:
1. Set environment variables:
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_TOKEN`
   - `TEST_WHATSAPP_NUMBER`
2. Uncomment the send example in `carousel_example.py`
3. Run the script

## Limitations

1. **Availability**: Feature available November 11+
2. **Card Count**: 2-10 cards per carousel
3. **Media Type**: All cards must use same type (all images OR all videos)
4. **Text Limits**:
   - Message body: 1024 characters
   - Card body: 160 characters (2 line breaks max)
   - Button text: 20 characters
5. **No Custom Headers/Footers**: Only body text and cards allowed
6. **External URLs Only**: Button URLs must point to external web pages

## API Version

This feature uses WhatsApp Business API v19.0 or later.

## Related Documentation

- [Interactive Components](interactive_components.py) - Buttons and lists
- [Location Components](location_components.py) - Location messages
- [WhatsApp Response Handler](whatsapp_response.py) - Message sending

## Support

For issues or questions:
1. Check the [examples](../examples/carousel_example.py)
2. Review WhatsApp Business API documentation
3. Test with the example script first
4. Verify all media URLs are accessible

## License

Part of the AVA WhatsApp Agent project.
