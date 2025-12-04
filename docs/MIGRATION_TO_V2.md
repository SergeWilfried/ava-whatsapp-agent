# Migration Guide: Legacy to V2 Components with API Integration

This guide shows how to migrate from legacy mock implementations to v2 components with CartaAI API integration.

---

## 🔄 Quick Migration Steps

### Step 1: Update Imports

**Before (Legacy):**
```python
# Old imports
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_size_selection_buttons,
    create_extras_list,
    create_category_selection_list,
)
from ai_companion.interfaces.whatsapp.carousel_components import (
    create_product_carousel,
)
from ai_companion.modules.cart.cart_service import CartService
```

**After (V2 with API):**
```python
# New imports
from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    create_size_selection_buttons,
    create_extras_list,
    create_modifiers_list,
    create_category_selection_list,
    extract_modifier_selections,
    extract_presentation_id,
)
from ai_companion.interfaces.whatsapp.carousel_components_v2 import (
    create_product_carousel,
    create_api_menu_carousel,
    create_category_products_carousel,
)
from ai_companion.modules.cart.cart_service_v2 import CartService
from ai_companion.modules.cart.order_messages import (
    format_order_confirmation,
    format_order_status_update,
)
```

### Step 2: Enable API Features

**Environment Configuration:**
```bash
# Enable CartaAI API
export USE_CARTAAI_API=true
export CARTAAI_MENU_ENABLED=true
export CARTAAI_ORDERS_ENABLED=true

# API Credentials
export CARTAAI_SUBDOMAIN=your-restaurant
export CARTAAI_LOCAL_ID=branch-001
export CARTAAI_API_KEY=your_api_key_here
export CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe/api/v1
```

**Or in code:**
```python
from ai_companion.core.config import get_config

config = get_config()
config.use_cartaai_api = True
config.menu_api_enabled = True
config.orders_api_enabled = True
```

---

## 📋 Component Migration Examples

### 1. Size Selection Buttons

**Before (Legacy with mock data):**
```python
# Only supports base_price with multipliers
component = create_size_selection_buttons(
    item_name="Classic Burger",
    base_price=15.99
)
# Creates: Small ($12.79), Medium ($15.99), Large ($20.79)
```

**After (V2 with API presentations):**
```python
# Fetch product with presentations
product = await menu_service.get_product_by_id("prod001")

# Use API presentations
component = create_size_selection_buttons(
    item_name=product["name"],
    presentations=product.get("presentations")
)
# Creates buttons from actual API data with real prices

# Or fallback to legacy if no presentations
component = create_size_selection_buttons(
    item_name="Classic Burger",
    base_price=15.99  # Falls back to multipliers
)
```

### 2. Extras/Modifiers List

**Before (Legacy with hardcoded extras):**
```python
# Hardcoded extras by category
component = create_extras_list(category="pizza")
# Returns hardcoded: Extra Cheese, Pepperoni, etc.
```

**After (V2 with API modifiers):**
```python
# Fetch product with modifiers
product = await menu_service.get_product_by_id("prod001")

# Use API modifiers
component = create_extras_list(
    modifiers=product.get("modifiers")
)
# Returns actual modifiers from API

# For advanced modifiers with validation
component = create_modifiers_list(
    item_name=product["name"],
    modifiers=product.get("modifiers")
)
# Includes (Required) and (Max N) indicators
```

### 3. Category Selection

**Before (Legacy with mock categories):**
```python
# Hardcoded 5 categories
component = create_category_selection_list()
# Returns: Pizzas, Burgers, Sides, Drinks, Desserts
```

**After (V2 with API categories):**
```python
# Fetch real categories
menu = await menu_service.get_menu_structure()
categories = menu["data"]["categories"]

# Use API categories
component = create_category_selection_list(
    categories=categories
)
# Returns actual categories with real item counts
```

### 4. Product Carousel

**Before (Legacy with manual product data):**
```python
# Manual product list
products = [
    {
        "name": "Burger",
        "price": 15.99,
        "image_url": "https://...",
        "product_url": "https://..."
    }
]

component = create_product_carousel(
    products=products,
    use_api_format=False
)
```

**After (V2 with API products):**
```python
# Fetch products from API
menu = await menu_service.get_menu_structure()
category = menu["data"]["categories"][0]
products = category["products"]

# Use API format
component = create_product_carousel(
    products=products,
    use_api_format=True
)

# Or use convenience function
component = create_api_menu_carousel(
    api_menu_structure=menu,
    category_id="cat001"
)
```

---

## 🛒 Cart Service Migration

### Adding Items to Cart

**Before (Legacy):**
```python
cart_service = CartService()

success, message, item = cart_service.add_item_to_cart(
    cart=cart,
    menu_item_id="pizzas_0",  # Legacy ID format
    quantity=2,
    size="large",  # Simple size string
    extras=["extra_cheese", "bacon"]  # Simple extras
)
```

**After (V2 with API):**
```python
cart_service = CartService()  # Now uses v2 internally

# Async version (recommended)
success, message, item = await cart_service.add_item_to_cart(
    cart=cart,
    menu_item_id="prod001",  # API ID format
    quantity=2,
    presentation_id="pres002",  # API presentation ID
    modifier_selections={  # API modifiers
        "mod001": ["opt001", "opt002"]
    }
)

# Sync version (backward compatible)
success, message, item = cart_service.add_item_to_cart_sync(...)
```

### Creating Orders

**Before (Legacy - local only):**
```python
# Synchronous, local file storage
order = cart_service.create_order_from_cart(
    cart=cart,
    delivery_method=DeliveryMethod.DELIVERY,
    customer_name="John Doe",
    delivery_address="123 Main St",
    delivery_phone="+51987654321",
    payment_method=PaymentMethod.CASH,
)

# Save locally
cart_service.save_order(order)

# Manual confirmation message
message = f"Order {order.order_id} confirmed!"
```

**After (V2 with API):**
```python
# Async with API integration
order = await cart_service.create_order_from_cart(
    cart=cart,
    delivery_method=DeliveryMethod.DELIVERY,
    customer_name="John Doe",
    delivery_address="123 Main St",
    delivery_phone="+51987654321",
    payment_method=PaymentMethod.CASH,
    delivery_instructions="Ring doorbell",  # NEW
    special_instructions="Extra napkins",
    scheduled_time=None,  # NEW: optional scheduling
)

# Order created in API automatically (if enabled)
if order.api_order_id:
    print(f"API Order: {order.api_order_number}")
else:
    print(f"Local Order: {order.order_id}")

# Save locally as backup
cart_service.save_order(order)

# Beautiful formatted confirmation
from ai_companion.modules.cart.order_messages import format_order_confirmation
message = format_order_confirmation(order)
# Returns formatted WhatsApp message with order details
```

---

## 🔄 Response Handling Migration

### Handling User Selections

**Before (Legacy - simple string parsing):**
```python
# User clicks button with ID "size_large"
selected_size = reply_id.replace("size_", "")  # "large"

# User selects extras
selected_extras = ["extra_cheese", "bacon"]
```

**After (V2 - API format extraction):**
```python
from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    extract_presentation_id,
    extract_modifier_selections,
)

# User clicks button with ID "size_pres002"
presentation_id = extract_presentation_id(reply_id)  # "pres002"

# User selects modifiers: ["mod_mod001_opt001", "mod_mod001_opt002"]
modifier_selections = extract_modifier_selections(selected_ids)
# Returns: {"mod001": ["opt001", "opt002"]}
```

---

## 📊 Complete Flow Comparison

### Legacy Flow (Mock Data)

```python
# 1. Show hardcoded categories
categories_component = create_category_selection_list()

# 2. User selects "Pizzas"
category = "pizzas"

# 3. Show hardcoded products
products = get_mock_products(category)
carousel = create_product_carousel(products, use_api_format=False)

# 4. User selects product
product = get_mock_product("pizzas_0")

# 5. Show hardcoded sizes
sizes = create_size_selection_buttons("Pizza", base_price=15.99)

# 6. Show hardcoded extras
extras = create_extras_list(category="pizza")

# 7. Add to cart with legacy format
cart_service.add_item_to_cart(
    cart, "pizzas_0", 1, "large", ["extra_cheese"]
)

# 8. Create local order
order = cart_service.create_order_from_cart(...)
cart_service.save_order(order)
```

### V2 Flow (API Integration)

```python
# 1. Fetch real categories from API
menu = await menu_service.get_menu_structure()
categories = menu["data"]["categories"]
categories_component = create_category_selection_list(categories=categories)

# 2. User selects category "cat001"
category_id = extract_category_id(reply_id)  # "cat001"

# 3. Show real products from API
carousel = create_api_menu_carousel(menu, category_id=category_id)

# 4. User selects product - fetch details
product = await menu_service.get_product_by_id("prod001")

# 5. Show API presentations (sizes)
sizes = create_size_selection_buttons(
    product["name"],
    presentations=product.get("presentations")
)

# 6. Show API modifiers
modifiers = create_modifiers_list(
    product["name"],
    modifiers=product.get("modifiers")
)

# 7. Extract selections and add to cart
presentation_id = extract_presentation_id(size_reply)
modifier_selections = extract_modifier_selections(modifier_replies)

await cart_service.add_item_to_cart(
    cart=cart,
    menu_item_id=product["_id"],
    quantity=1,
    presentation_id=presentation_id,
    modifier_selections=modifier_selections,
)

# 8. Create order via API
order = await cart_service.create_order_from_cart(
    cart=cart,
    delivery_method=DeliveryMethod.DELIVERY,
    customer_name="John Doe",
    customer_phone="+51987654321",
    delivery_address="123 Main St",
    payment_method=PaymentMethod.CASH,
)

# 9. Save locally and send confirmation
cart_service.save_order(order)
confirmation = format_order_confirmation(order)
await send_whatsapp_message(user_phone, confirmation)

# 10. Track order status via API
if order.api_order_id:
    order_status = await order_service.get_order(order.api_order_id)
```

---

## 🎯 Feature Flags for Gradual Migration

### Phase 1: Test with API Disabled
```python
# .env
USE_CARTAAI_API=false
CARTAAI_MENU_ENABLED=false
CARTAAI_ORDERS_ENABLED=false
```

**Result:** V2 components fall back to legacy behavior

### Phase 2: Enable Menu API Only
```python
# .env
USE_CARTAAI_API=true
CARTAAI_MENU_ENABLED=true
CARTAAI_ORDERS_ENABLED=false  # Still local orders
```

**Result:** Real menu data, local order storage

### Phase 3: Full API Integration
```python
# .env
USE_CARTAAI_API=true
CARTAAI_MENU_ENABLED=true
CARTAAI_ORDERS_ENABLED=true
```

**Result:** Complete API integration with fallback

---

## 🔧 Common Migration Patterns

### Pattern 1: Menu Item Lookup

**Before:**
```python
def get_menu_item(item_id: str):
    # Hardcoded lookup
    return MOCK_MENU.get(item_id)
```

**After:**
```python
async def get_menu_item(item_id: str):
    # API lookup with fallback
    menu_adapter = get_menu_adapter()
    return await menu_adapter.find_menu_item(item_id)
```

### Pattern 2: Price Calculation

**Before:**
```python
def calculate_price(base_price: float, size: str, extras: List[str]):
    # Hardcoded multipliers
    size_price = base_price * SIZE_MULTIPLIERS.get(size, 1.0)
    extras_price = sum(EXTRAS_PRICING.get(e, 0) for e in extras)
    return size_price + extras_price
```

**After:**
```python
async def calculate_price(
    product: Dict,
    presentation_id: str,
    modifier_selections: Dict
):
    # Use API pricing
    base_price = product["price"]

    # Get presentation price
    if product.get("presentations"):
        for pres in product["presentations"]:
            if pres["_id"] == presentation_id:
                base_price = pres["price"]
                break

    # Add modifier prices
    extras_price = 0
    if product.get("modifiers"):
        for modifier in product["modifiers"]:
            mod_id = modifier["_id"]
            if mod_id in modifier_selections:
                for option in modifier["options"]:
                    if option["_id"] in modifier_selections[mod_id]:
                        extras_price += option["price"]

    return base_price + extras_price
```

### Pattern 3: Order Confirmation

**Before:**
```python
def send_order_confirmation(order):
    # Manual message building
    message = f"Order {order.order_id} confirmed!\n"
    message += f"Total: ${order.total:.2f}\n"
    message += "Thank you!"

    send_message(message)
```

**After:**
```python
async def send_order_confirmation(order):
    from ai_companion.modules.cart.order_messages import format_order_confirmation

    # Beautiful formatted message
    message = format_order_confirmation(order)
    await send_whatsapp_message(user_phone, message)

    # Track via API if available
    if order.api_order_id:
        order_service = get_order_service()
        await order_service.get_order(order.api_order_id)
```

---

## ✅ Migration Checklist

### Code Updates
- [ ] Update imports to use v2 components
- [ ] Replace `cart_service` with async version
- [ ] Update menu item lookups to use `menu_adapter`
- [ ] Replace hardcoded categories with API calls
- [ ] Update product carousels to use API format
- [ ] Replace size selection with presentations
- [ ] Replace extras with modifiers
- [ ] Update order creation to async
- [ ] Add order confirmation messages
- [ ] Implement modifier selection extraction

### Configuration
- [ ] Set environment variables for API
- [ ] Configure API credentials
- [ ] Set feature flags appropriately
- [ ] Test with API disabled (fallback)
- [ ] Test with menu API only
- [ ] Test with full API integration

### Testing
- [ ] Test menu browsing with API
- [ ] Test product selection with presentations
- [ ] Test modifier selection
- [ ] Test cart operations
- [ ] Test order creation
- [ ] Test order confirmation messages
- [ ] Test API error handling
- [ ] Test fallback to mock data

### Deployment
- [ ] Deploy with API disabled first
- [ ] Enable menu API in staging
- [ ] Enable orders API in staging
- [ ] Monitor error rates
- [ ] Enable in production gradually
- [ ] Monitor API performance

---

## 🐛 Troubleshooting

### Issue: Components showing mock data

**Cause:** API not enabled or credentials not set

**Solution:**
```bash
# Check configuration
python -c "from ai_companion.core.config import get_config; c=get_config(); print(f'API: {c.use_cartaai_api}, Menu: {c.menu_api_enabled}')"

# Enable API
export USE_CARTAAI_API=true
export CARTAAI_MENU_ENABLED=true
```

### Issue: Orders not creating in API

**Cause:** Orders API not enabled

**Solution:**
```bash
export CARTAAI_ORDERS_ENABLED=true
```

### Issue: Product IDs not found

**Cause:** Using legacy ID format with API

**Solution:**
```python
# Use ProductIDMapper to convert
from ai_companion.services.cartaai.product_mapper import get_product_mapper

mapper = get_product_mapper()
api_id = mapper.get_api_id("pizzas_0")  # Returns "prod001"
```

### Issue: Async errors in sync code

**Cause:** Using async methods in sync context

**Solution:**
```python
# Use sync wrapper
order = cart_service.create_order_from_cart_sync(...)

# Or use asyncio
import asyncio
order = asyncio.run(cart_service.create_order_from_cart(...))
```

---

## 📚 Additional Resources

- [Phase 0 Implementation](./PHASE_0_IMPLEMENTATION.md) - API Client
- [Phase 1 Implementation](./PHASE_1_IMPLEMENTATION.md) - Menu Integration
- [Phase 2 Implementation](./PHASE_2_IMPLEMENTATION.md) - Interactive Components
- [Phase 3 Implementation](./PHASE_3_IMPLEMENTATION.md) - Order Creation
- [Comprehensive Migration Plan](./COMPREHENSIVE_MIGRATION_PLAN.md) - Full roadmap
- [CartaAI API Documentation](./api/CHATBOT_INTEGRATION.md) - API reference

---

**Ready to migrate?** Start with Phase 1 (API disabled) and gradually enable features!
