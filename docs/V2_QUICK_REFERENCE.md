# V2 Components Quick Reference Card

Quick copy-paste examples for common tasks with V2 components and API integration.

---

## 🚀 Setup

```bash
# .env configuration
USE_CARTAAI_API=true
CARTAAI_MENU_ENABLED=true
CARTAAI_ORDERS_ENABLED=true
CARTAAI_SUBDOMAIN=your-restaurant
CARTAAI_LOCAL_ID=branch-001
CARTAAI_API_KEY=your_key_here
```

---

## 📦 Common Imports

```python
# Services
from ai_companion.services.cartaai.menu_service import get_menu_service
from ai_companion.services.cartaai.order_service import get_order_service
from ai_companion.services.menu_adapter import get_menu_adapter
from ai_companion.modules.cart.cart_service_v2 import get_cart_service

# Interactive Components
from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    create_size_selection_buttons,
    create_extras_list,
    create_modifiers_list,
    create_category_selection_list,
    extract_modifier_selections,
    extract_presentation_id,
)

# Carousels
from ai_companion.interfaces.whatsapp.carousel_components_v2 import (
    create_product_carousel,
    create_api_menu_carousel,
)

# Messages
from ai_companion.modules.cart.order_messages import (
    format_order_confirmation,
    format_order_status_update,
)

# Models
from ai_companion.modules.cart.models import (
    DeliveryMethod,
    PaymentMethod,
    OrderStatus,
)
```

---

## 📋 Menu Operations

### Get Menu Structure
```python
menu_service = get_menu_service()
menu = await menu_service.get_menu_structure()
categories = menu["data"]["categories"]
```

### Get Product Details
```python
menu_service = get_menu_service()
product = await menu_service.get_product_by_id("prod001")
```

### Search Products
```python
menu_service = get_menu_service()
results = await menu_service.search_products_by_name("burger")
```

### Find Menu Item (with fallback)
```python
adapter = get_menu_adapter()
item = await adapter.find_menu_item("prod001")  # Works with API or legacy IDs
```

---

## 🎨 Interactive Components

### Category Selection
```python
menu = await menu_service.get_menu_structure()
component = create_category_selection_list(
    categories=menu["data"]["categories"]
)
```

### Product Carousel
```python
# From API menu
menu = await menu_service.get_menu_structure()
carousel = create_api_menu_carousel(
    api_menu_structure=menu,
    category_id="cat001"  # Optional filter
)

# From product list
products = menu["data"]["categories"][0]["products"]
carousel = create_product_carousel(
    products=products,
    use_api_format=True
)
```

### Size Selection
```python
product = await menu_service.get_product_by_id("prod001")
component = create_size_selection_buttons(
    item_name=product["name"],
    presentations=product.get("presentations")
)
```

### Modifiers/Extras
```python
product = await menu_service.get_product_by_id("prod001")

# Simple extras list
component = create_extras_list(
    modifiers=product.get("modifiers")
)

# Advanced with validation
component = create_modifiers_list(
    item_name=product["name"],
    modifiers=product.get("modifiers")
)
```

---

## 🎯 Response Handling

### Extract Presentation ID
```python
# User clicked: "size_pres002"
presentation_id = extract_presentation_id(reply_id)
# Returns: "pres002"
```

### Extract Modifier Selections
```python
# User selected: ["mod_mod001_opt001", "mod_mod001_opt002"]
selections = extract_modifier_selections(selected_ids)
# Returns: {"mod001": ["opt001", "opt002"]}
```

---

## 🛒 Cart Operations

### Initialize Cart Service
```python
cart_service = get_cart_service()
cart = cart_service.create_cart()
```

### Add Item to Cart
```python
success, message, item = await cart_service.add_item_to_cart(
    cart=cart,
    menu_item_id="prod001",
    quantity=2,
    presentation_id="pres002",  # Optional
    modifier_selections={"mod001": ["opt001", "opt002"]},  # Optional
    special_instructions="No onions",  # Optional
)
```

### Remove from Cart
```python
success, message = cart_service.remove_item_from_cart(cart, cart_item_id)
```

### Get Cart Summary
```python
summary = cart_service.get_cart_summary(cart)
# Returns formatted text for WhatsApp
```

---

## 📦 Order Creation

### Create Order
```python
order = await cart_service.create_order_from_cart(
    cart=cart,
    delivery_method=DeliveryMethod.DELIVERY,
    customer_name="John Doe",
    customer_phone="+51987654321",
    delivery_address="123 Main St, Lima",
    payment_method=PaymentMethod.CASH,
    special_instructions="Ring doorbell",  # Optional
    delivery_instructions="Blue door",  # Optional
    scheduled_time=None,  # Optional datetime
)

# Check if created via API
if order.api_order_id:
    print(f"API Order: {order.api_order_number}")
else:
    print(f"Local Order: {order.order_id}")
```

### Confirm Order
```python
confirmed_order = cart_service.confirm_order(order)
# Sets status and estimated ready time
```

### Save Order
```python
file_path = cart_service.save_order(order)
# Saves to data/carts/orders/{order_id}.json
```

---

## 💬 Order Messages

### Order Confirmation
```python
message = format_order_confirmation(order)
await send_whatsapp_message(user_phone, message)
```

### Status Update
```python
message = format_order_status_update(
    order=order,
    new_status=OrderStatus.PREPARING,
    message="Your order is being prepared!"  # Optional
)
await send_whatsapp_message(user_phone, message)
```

### Order Summary
```python
summary = format_order_summary(order)
# Brief summary for display
```

### Error Message
```python
error_msg = format_order_error(
    error_message="Payment failed",
    order_id=order.order_id  # Optional
)
await send_whatsapp_message(user_phone, error_msg)
```

---

## 📊 Order Tracking

### Get Order Status
```python
order_service = get_order_service()
response = await order_service.get_order(order.api_order_id)

if response["type"] == "1":
    order_data = response["data"]
    print(f"Status: {order_data['status']}")
```

### Get Customer Orders
```python
order_service = get_order_service()

# All orders
orders = await order_service.get_customer_orders("+51987654321")

# Filter by status
pending = await order_service.get_customer_orders(
    "+51987654321",
    status="pending"
)
```

---

## 🔄 Complete Flow Example

```python
import asyncio
from ai_companion.services.cartaai.menu_service import get_menu_service
from ai_companion.modules.cart.cart_service_v2 import get_cart_service
from ai_companion.interfaces.whatsapp.interactive_components_v2 import *
from ai_companion.interfaces.whatsapp.carousel_components_v2 import *
from ai_companion.modules.cart.order_messages import format_order_confirmation
from ai_companion.modules.cart.models import DeliveryMethod, PaymentMethod


async def complete_order_flow():
    # 1. Get services
    menu_service = get_menu_service()
    cart_service = get_cart_service()

    # 2. Show categories
    menu = await menu_service.get_menu_structure()
    categories_component = create_category_selection_list(
        categories=menu["data"]["categories"]
    )
    # Send to user...

    # 3. User selects category -> show products
    carousel = create_api_menu_carousel(menu, category_id="cat001")
    # Send to user...

    # 4. User selects product -> get details
    product = await menu_service.get_product_by_id("prod001")

    # 5. Show size selection
    sizes = create_size_selection_buttons(
        product["name"],
        presentations=product.get("presentations")
    )
    # Send to user...

    # 6. Show modifiers
    modifiers = create_modifiers_list(
        product["name"],
        modifiers=product.get("modifiers")
    )
    # Send to user...

    # 7. User makes selections -> extract
    presentation_id = extract_presentation_id("size_pres002")
    modifier_selections = extract_modifier_selections([
        "mod_mod001_opt001",
        "mod_mod001_opt002"
    ])

    # 8. Add to cart
    cart = cart_service.create_cart()
    success, message, item = await cart_service.add_item_to_cart(
        cart=cart,
        menu_item_id=product["_id"],
        quantity=2,
        presentation_id=presentation_id,
        modifier_selections=modifier_selections,
    )

    # 9. Show cart summary
    summary = cart_service.get_cart_summary(cart)
    # Send to user...

    # 10. Create order
    order = await cart_service.create_order_from_cart(
        cart=cart,
        delivery_method=DeliveryMethod.DELIVERY,
        customer_name="John Doe",
        customer_phone="+51987654321",
        delivery_address="123 Main St, Lima",
        payment_method=PaymentMethod.CASH,
    )

    # 11. Save and confirm
    cart_service.save_order(order)
    confirmation = format_order_confirmation(order)
    # Send to user...

    print(f"Order created: {order.api_order_number or order.order_id}")
    print(f"Total: ${order.total:.2f}")


# Run
asyncio.run(complete_order_flow())
```

---

## 🎛️ Feature Flags

### Check Configuration
```python
from ai_companion.core.config import get_config

config = get_config()
print(f"API Enabled: {config.use_cartaai_api}")
print(f"Menu API: {config.menu_api_enabled}")
print(f"Orders API: {config.orders_api_enabled}")
```

### Runtime Toggle
```python
config = get_config()
config.use_cartaai_api = True
config.menu_api_enabled = True
config.orders_api_enabled = True
```

---

## ⚠️ Error Handling

### Try-Catch Pattern
```python
try:
    menu = await menu_service.get_menu_structure()
except Exception as e:
    logger.error(f"Failed to fetch menu: {e}")
    # Fall back to mock data
    menu = get_mock_menu()
```

### With Fallback
```python
from ai_companion.services.menu_adapter import get_menu_adapter

adapter = get_menu_adapter()
# Automatically falls back to mock on API errors
product = await adapter.find_menu_item("prod001")
```

---

## 🧪 Testing

### Test API Connection
```python
import asyncio
from ai_companion.services.cartaai.menu_service import get_menu_service

async def test():
    menu_service = get_menu_service()
    try:
        menu = await menu_service.get_menu_structure()
        print(f"✅ API Connected! Categories: {len(menu['data']['categories'])}")
    except Exception as e:
        print(f"❌ API Error: {e}")

asyncio.run(test())
```

### Run Unit Tests
```bash
# All tests
pytest tests/services/cartaai/ -v

# Specific phase
pytest tests/services/cartaai/test_order_service.py -v

# With coverage
pytest tests/services/cartaai/ --cov=ai_companion.services.cartaai
```

---

## 📝 Common Patterns

### Pattern: Fetch and Display Product
```python
# Fetch
product = await menu_service.get_product_by_id(product_id)

# Create components
sizes = create_size_selection_buttons(
    product["name"],
    presentations=product.get("presentations")
)
modifiers = create_modifiers_list(
    product["name"],
    modifiers=product.get("modifiers")
)

# Send to user
await send_interactive_component(sizes)
await send_interactive_component(modifiers)
```

### Pattern: Handle User Response
```python
# Extract data
presentation_id = extract_presentation_id(size_reply_id)
modifier_selections = extract_modifier_selections(modifier_reply_ids)

# Add to cart
success, msg, item = await cart_service.add_item_to_cart(
    cart=cart,
    menu_item_id=product_id,
    quantity=quantity,
    presentation_id=presentation_id,
    modifier_selections=modifier_selections,
)

# Confirm
if success:
    await send_message(f"✅ {msg}")
```

### Pattern: Complete Order Flow
```python
# Create order
order = await cart_service.create_order_from_cart(...)

# Confirm
confirmed = cart_service.confirm_order(order)

# Save
cart_service.save_order(confirmed)

# Send confirmation
message = format_order_confirmation(confirmed)
await send_whatsapp_message(user_phone, message)
```

---

## 🔗 Related Documentation

- [Full Migration Guide](./MIGRATION_TO_V2.md)
- [V2 Components Summary](./V2_COMPONENTS_SUMMARY.md)
- [Phase 3 Implementation](./PHASE_3_IMPLEMENTATION.md)
- [API Reference](./api/CHATBOT_INTEGRATION.md)

---

**Keep this reference handy while migrating!** 📌
