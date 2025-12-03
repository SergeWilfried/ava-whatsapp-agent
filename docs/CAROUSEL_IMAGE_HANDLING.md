# Carousel Image Handling Guide

## Problem

Carousels require HTTPS URLs to images or videos. You need a strategy for providing these URLs.

## ✨ Solution: Built-in Image Utilities (Recommended)

**We've included automatic image handling for your menu!** All your menu items automatically get high-quality food images from Unsplash.

### Quick Start

```python
from ai_companion.core.schedules import RESTAURANT_MENU
from ai_companion.interfaces.whatsapp.image_utils import prepare_menu_items_for_carousel
from ai_companion.interfaces.whatsapp.carousel_components import create_restaurant_menu_carousel

# Automatically adds images to your pizzas
pizza_items = prepare_menu_items_for_carousel(
    RESTAURANT_MENU["pizzas"],
    "pizzas"
)

# Each item now has image_url and order_url!
carousel = create_restaurant_menu_carousel(
    pizza_items,
    body_text="Check out our delicious pizzas! 🍕"
)
```

**No configuration needed** - works immediately with your existing `RESTAURANT_MENU`!

---

## How It Works

### Intelligent Image Matching

The `image_utils.py` module provides automatic image URLs with three levels of fallback:

1. **Item-Specific Images** - Exact matches by name
   - "Margherita Pizza" → High-quality margherita pizza photo
   - "Cheeseburger" → Perfect cheeseburger photo

2. **Category Defaults** - If no exact match
   - Pizzas → Generic pizza photo
   - Burgers → Generic burger photo
   - Desserts → Generic dessert photo

3. **Generic Food** - Ultimate fallback
   - Any unmatched item → Beautiful food photo

### Included Mappings

Your menu items already have perfect image matches:

**Pizzas:**
- ✅ Margherita Pizza - Matched
- ✅ Pepperoni Pizza - Matched
- ✅ Vegetarian Pizza - Matched
- ✅ BBQ Chicken Pizza - Matched
- ✅ Hawaiian Pizza - Matched

**Burgers:**
- ✅ Classic Burger - Matched
- ✅ Cheeseburger - Matched
- ✅ Bacon Burger - Matched
- ✅ Veggie Burger - Matched

**Sides:**
- ✅ French Fries - Matched
- ✅ Onion Rings - Matched
- ✅ Mozzarella Sticks - Matched
- ✅ Caesar Salad - Matched

**Drinks:**
- ✅ Coca-Cola - Matched
- ✅ Sprite - Matched
- ✅ Iced Tea - Matched
- ✅ Water - Matched

**Desserts:**
- ✅ Chocolate Brownie - Matched
- ✅ Cheesecake - Matched
- ✅ Ice Cream Sundae - Matched

---

## Usage Examples

### Example 1: Single Category

```python
from ai_companion.core.schedules import RESTAURANT_MENU
from ai_companion.interfaces.whatsapp.image_utils import prepare_menu_items_for_carousel
from ai_companion.interfaces.whatsapp.carousel_components import create_restaurant_menu_carousel

# Show all burgers
burger_items = prepare_menu_items_for_carousel(
    RESTAURANT_MENU["burgers"],
    "burgers"
)

carousel = create_restaurant_menu_carousel(burger_items)
```

### Example 2: Mixed Items (Top 10)

```python
from ai_companion.core.schedules import RESTAURANT_MENU
from ai_companion.interfaces.whatsapp.image_utils import get_all_menu_items_with_images
from ai_companion.interfaces.whatsapp.carousel_components import create_restaurant_menu_carousel

# Get first 10 items across all categories
all_items = get_all_menu_items_with_images(
    RESTAURANT_MENU,
    max_items=10  # Carousel maximum
)

carousel = create_restaurant_menu_carousel(all_items)
```

### Example 3: Featured Items

```python
from ai_companion.core.schedules import RESTAURANT_MENU
from ai_companion.interfaces.whatsapp.image_utils import get_featured_items_with_images
from ai_companion.interfaces.whatsapp.carousel_components import create_restaurant_menu_carousel

# Hand-pick items to feature
featured = get_featured_items_with_images(
    RESTAURANT_MENU,
    featured_names=[
        "Margherita Pizza",
        "Classic Burger",
        "Chocolate Brownie"
    ]
)

carousel = create_restaurant_menu_carousel(
    featured,
    body_text="⭐ Staff Picks - Our Most Popular!"
)
```

### Example 4: In Your Agent Node

```python
# In your graph node
from ai_companion.core.schedules import RESTAURANT_MENU
from ai_companion.interfaces.whatsapp.carousel_components import create_restaurant_menu_carousel
from ai_companion.interfaces.whatsapp.image_utils import prepare_menu_items_for_carousel
from langchain_core.messages import AIMessage

async def show_menu_carousel_node(state):
    """Show menu as an interactive carousel."""

    category = state.get("selected_category", "pizzas")

    # Prepare items with images
    items = prepare_menu_items_for_carousel(
        RESTAURANT_MENU[category],
        category
    )

    # Create carousel
    carousel = create_restaurant_menu_carousel(
        items,
        body_text=f"Check out our {category}! 😋"
    )

    return {
        "messages": [AIMessage(content=f"Here are our {category}!")],
        "interactive_component": carousel,
        "message_type": "interactive_carousel"
    }
```

---

## Image Sources

### Unsplash (Current)

Images are sourced from [Unsplash](https://unsplash.com/) - high-quality, free-to-use photos.

**Advantages:**
- ✅ No API key required
- ✅ Permanent, stable URLs
- ✅ High quality professional photos
- ✅ Free for commercial use
- ✅ Fast CDN delivery
- ✅ Works immediately

**License:** Free to use under [Unsplash License](https://unsplash.com/license)

---

## Custom Images (Optional)

### Option A: Add to Menu Data

Edit `src/ai_companion/core/schedules.py`:

```python
RESTAURANT_MENU = {
    "pizzas": [
        {
            "name": "Margherita Pizza",
            "price": 12.99,
            "description": "Classic cheese pizza",
            "image_url": "https://yourcdn.com/pizzas/margherita.jpg"  # Add this
        },
        # ... more items
    ]
}
```

The image utilities will use your custom URLs automatically!

### Option B: Set Custom CDN Base URL

```python
from ai_companion.interfaces.whatsapp.image_utils import set_custom_image_base_url

# If your images are at: https://cdn.yourshop.com/images/pizzas/margherita-pizza.jpg
set_custom_image_base_url("https://cdn.yourshop.com/images")

# Now all items will try your CDN first, with automatic fallback to Unsplash
```

### Option C: Manual URLs

```python
from ai_companion.interfaces.whatsapp.carousel_components import create_product_carousel

# Manually specify everything
products = [
    {
        "name": "Custom Pizza",
        "description": "Your special pizza",
        "price": 19.99,
        "image_url": "https://your-cdn.com/custom-pizza.jpg",
        "product_url": "https://yourshop.com/order/custom"
    }
]

carousel = create_product_carousel(products)
```

---

## API Reference

### `prepare_menu_items_for_carousel()`

Enrich menu items with image URLs and order URLs.

```python
items = prepare_menu_items_for_carousel(
    menu_items=RESTAURANT_MENU["pizzas"],
    category="pizzas",
    base_order_url="https://yourshop.com/order"  # Optional
)
```

**Returns:** List of items with `image_url` and `order_url` added.

### `get_all_menu_items_with_images()`

Get items from all categories with images.

```python
items = get_all_menu_items_with_images(
    menu_dict=RESTAURANT_MENU,
    max_items=10
)
```

**Returns:** Up to 10 items from mixed categories.

### `get_featured_items_with_images()`

Get specific items by name with images.

```python
items = get_featured_items_with_images(
    menu_dict=RESTAURANT_MENU,
    featured_names=["Margherita Pizza", "Classic Burger"]
)
```

**Returns:** Only the requested items with images.

### `get_menu_item_image_url()`

Get image URL for a single item.

```python
url = get_menu_item_image_url(
    item_name="Margherita Pizza",
    category="pizzas",
    custom_url=None  # Optional override
)
```

**Returns:** HTTPS URL to an image.

---

## Testing

Run the example to see image URLs:

```bash
python examples/carousel_with_real_menu.py
```

You'll see:
- Pizza carousel with 5 items
- Mixed menu carousel with 10 items
- Featured items carousel
- Category-specific carousels
- Integration examples

---

## Image Specifications

### Recommended

- **Resolution:** 1200x630 pixels (WhatsApp recommended)
- **Aspect Ratio:** 16:9 or 1.91:1
- **Format:** JPEG or PNG
- **File Size:** Under 5MB
- **Protocol:** HTTPS only

### Current Implementation

Unsplash images are delivered as:
- `?w=800&h=600&fit=crop` - 800x600 optimized
- High quality, fast loading
- Consistent aspect ratio across all items

---

## FAQ

**Q: Do I need an API key?**
A: No! The Unsplash URLs work without authentication.

**Q: Will these images always work?**
A: Yes, these are permanent Unsplash URLs with stable CDN delivery.

**Q: Can I use my own images?**
A: Yes! See "Custom Images" section above.

**Q: What if I add a new menu item?**
A: It will automatically use the category default image. You can add a specific mapping in `image_utils.py` if desired.

**Q: Are these images free to use commercially?**
A: Yes, Unsplash images are free for commercial use.

**Q: Can I change the image URLs later?**
A: Yes, edit `ITEM_SPECIFIC_IMAGES` in `image_utils.py` or add `image_url` to your menu data.

---

## Best Practices

1. **Use provided images** - They're ready to go!
2. **Test first** - Run `examples/carousel_with_real_menu.py`
3. **Add custom images gradually** - Start with defaults, customize later
4. **Keep aspect ratios consistent** - All images should be similar dimensions
5. **Optimize file sizes** - Under 1MB is ideal

---

## Summary

✅ **Zero configuration** - Works immediately with your menu
✅ **High-quality images** - Professional food photography
✅ **Automatic matching** - Item-specific images for all your products
✅ **Intelligent fallbacks** - Category and generic defaults
✅ **Free to use** - No API keys or fees
✅ **Production ready** - Stable, fast CDN delivery

Start using carousels right now - no image setup required!

---

## See Also

- [CAROUSEL_MESSAGES.md](./CAROUSEL_MESSAGES.md) - Complete carousel documentation
- [CAROUSEL_QUICK_START.md](./CAROUSEL_QUICK_START.md) - Quick reference
- [examples/carousel_with_real_menu.py](../examples/carousel_with_real_menu.py) - Working examples
