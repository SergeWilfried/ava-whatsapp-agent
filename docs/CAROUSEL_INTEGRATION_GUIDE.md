# Carousel Integration Guide

## Current Status

❌ Carousels are **not yet integrated** into your conversation flow.

✅ All components are ready to use - just need to add them to your handlers.

## Integration Points

### 1. Replace List Menu with Carousel (Recommended)

**Location:** `src/ai_companion/interfaces/whatsapp/whatsapp_response.py:160-171`

**Current code:**
```python
elif node_name == "view_menu":
    # User selected "View Menu" - show the actual menu
    interactive_comp = create_menu_list_from_restaurant_menu(RESTAURANT_MENU)
    success = await send_response(
        from_number,
        "Here's our menu! 😋",
        "interactive_list",  # ← Currently a list
        phone_number_id=phone_number_id,
        whatsapp_token=whatsapp_token,
        interactive_component=interactive_comp
    )
    return Response(content="Menu sent", status_code=200)
```

**Replace with:**
```python
elif node_name == "view_menu":
    # User selected "View Menu" - show as carousel with images
    from ai_companion.interfaces.whatsapp.image_utils import get_all_menu_items_with_images
    from ai_companion.interfaces.whatsapp.carousel_components import create_restaurant_menu_carousel

    # Get up to 10 items with automatic images
    menu_items = get_all_menu_items_with_images(RESTAURANT_MENU, max_items=10)

    # Create carousel instead of list
    interactive_comp = create_restaurant_menu_carousel(
        menu_items,
        body_text="Check out our delicious menu! 😋",
        button_text="Order"
    )

    success = await send_response(
        from_number,
        "Here's our menu!",
        "interactive_carousel",  # ← Changed to carousel
        phone_number_id=phone_number_id,
        whatsapp_token=whatsapp_token,
        interactive_component=interactive_comp
    )
    return Response(content="Carousel menu sent", status_code=200)
```

### 2. Add Category-Specific Carousels

Show different carousels for different categories:

**Add this new node handler:**

```python
elif node_name == "view_category_carousel":
    # Show carousel for specific category
    from ai_companion.interfaces.whatsapp.image_utils import prepare_menu_items_for_carousel
    from ai_companion.interfaces.whatsapp.carousel_components import create_restaurant_menu_carousel

    # Get category from state
    category = current_state_dict.get("selected_category", "pizzas")

    if category in RESTAURANT_MENU:
        # Prepare items with images
        menu_items = prepare_menu_items_for_carousel(
            RESTAURANT_MENU[category],
            category
        )

        # Create carousel
        interactive_comp = create_restaurant_menu_carousel(
            menu_items,
            body_text=f"Browse our {category}! 🍕",
            button_text="Order"
        )

        success = await send_response(
            from_number,
            f"Here are our {category}!",
            "interactive_carousel",
            phone_number_id=phone_number_id,
            whatsapp_token=whatsapp_token,
            interactive_component=interactive_comp
        )

        return Response(content="Category carousel sent", status_code=200)
```

### 3. Featured Items Carousel (Promotional)

Show hand-picked items for promotions:

**Add this handler:**

```python
elif node_name == "show_featured":
    # Show featured/popular items
    from ai_companion.interfaces.whatsapp.image_utils import get_featured_items_with_images
    from ai_companion.interfaces.whatsapp.carousel_components import create_restaurant_menu_carousel

    # Define featured items
    featured_names = [
        "Margherita Pizza",
        "BBQ Chicken Pizza",
        "Classic Burger",
        "Bacon Burger",
        "Chocolate Brownie"
    ]

    # Get items with images
    featured_items = get_featured_items_with_images(
        RESTAURANT_MENU,
        featured_names
    )

    # Create carousel
    interactive_comp = create_restaurant_menu_carousel(
        featured_items,
        body_text="⭐ Our Most Popular Items!",
        button_text="Order Now"
    )

    success = await send_response(
        from_number,
        "Check out our staff picks!",
        "interactive_carousel",
        phone_number_id=phone_number_id,
        whatsapp_token=whatsapp_token,
        interactive_component=interactive_comp
    )

    return Response(content="Featured carousel sent", status_code=200)
```

### 4. Daily Specials Carousel

Show special offers:

**Add this handler:**

```python
elif node_name == "show_specials":
    # Show daily specials as carousel
    from ai_companion.interfaces.whatsapp.carousel_components import create_offer_carousel

    # Create offers from special deals
    offers = []
    for combo in SPECIAL_OFFERS["combo_deals"]:
        offers.append({
            "title": combo["name"],
            "description": f"{', '.join(combo['items'])} - Save ${combo['savings']}!",
            "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800&h=600&fit=crop",
            "offer_url": f"https://yourshop.com/order/special/{combo['name'].lower().replace(' ', '-')}"
        })

    # Create carousel
    interactive_comp = create_offer_carousel(
        offers[:10],  # Max 10 cards
        body_text="🎉 Limited Time Offers - Don't Miss Out!",
        button_text="Order Now"
    )

    success = await send_response(
        from_number,
        "Check out today's specials!",
        "interactive_carousel",
        phone_number_id=phone_number_id,
        whatsapp_token=whatsapp_token,
        interactive_component=interactive_comp
    )

    return Response(content="Specials carousel sent", status_code=200)
```

## Step-by-Step Integration

### Step 1: Update Import Section

At the top of `whatsapp_response.py`, add:

```python
from ai_companion.interfaces.whatsapp.carousel_components import (
    create_restaurant_menu_carousel,
    create_offer_carousel
)
from ai_companion.interfaces.whatsapp.image_utils import (
    prepare_menu_items_for_carousel,
    get_all_menu_items_with_images,
    get_featured_items_with_images
)
```

### Step 2: Replace or Add Handlers

Choose one or more integration points above and add them to your `whatsapp_response.py` in the `elif` chain around line 160.

### Step 3: Update Cart Routing (Optional)

If you want carousels to work with cart interactions, update `cart_handler.py` to recognize carousel button clicks.

Currently, carousel buttons open URLs (external), so they don't trigger cart actions directly. If you want carousel → cart integration:

**Option A:** Keep current button lists for cart actions
**Option B:** Use carousels for browsing, buttons for cart actions
**Option C:** Make carousel buttons deep-link back to WhatsApp with cart commands

### Step 4: Test

```python
# Send a test message: "show menu"
# or trigger the "view_menu" node
# Should now show carousel instead of list
```

## Comparison: List vs Carousel

### Current: Interactive List
```
📋 Browse our menu!
├─ 🍕 Pizzas
│  ├─ Margherita $12.99
│  └─ Pepperoni $14.99
└─ 🍔 Burgers
   └─ Classic $9.99

[Button: View Menu]
(Tap to open list)
```

**Pros:**
- Simple interaction
- Can show many items
- Works with cart selection

**Cons:**
- No images
- Less engaging
- Hidden until clicked

### With Carousel
```
😋 Check out our menu!

[← → Swipe through cards]

🖼️ [Beautiful Pizza Photo]
Margherita Pizza
Fresh mozzarella, basil
$12.99
[Order Now →]

🖼️ [Beautiful Burger Photo]
Classic Burger
Beef patty, lettuce, tomato
$9.99
[Order Now →]
```

**Pros:**
- ✅ Beautiful images
- ✅ Highly engaging
- ✅ Shows multiple items at once
- ✅ Modern, app-like experience

**Cons:**
- Max 10 items
- External URLs (unless you handle deep links)
- Requires image hosting

## Recommendation

### Quick Win: Hybrid Approach

Use **both** - carousels for browsing, lists for cart actions:

1. **Show Menu** → Carousel (browsing, visual appeal)
2. **Add to Cart** → List or Buttons (cart interaction)
3. **View Cart** → Buttons (cart actions)
4. **Featured Items** → Carousel (promotional)
5. **Daily Specials** → Carousel (offers)

This gives you the best of both worlds!

## Testing Plan

1. **Replace `view_menu` with carousel** (Step 1 above)
2. **Test:** Send "show menu" message
3. **Verify:** See carousel with images
4. **Check:** Button URLs work correctly
5. **Iterate:** Add more carousel types as needed

## Need Help?

- See examples: `examples/carousel_with_real_menu.py`
- Check docs: `docs/CAROUSEL_MESSAGES.md`
- Test first: `examples/carousel_test_simple.py`

## Summary

✅ **Ready:** All carousel functions work
✅ **Images:** Automatic image URLs for all menu items
❌ **Not integrated:** Need to add handlers (5 minutes)
🎯 **Quick win:** Replace line 162 in `whatsapp_response.py`

Start with just replacing the menu list → carousel. It's a one-line change that makes a big visual impact!
