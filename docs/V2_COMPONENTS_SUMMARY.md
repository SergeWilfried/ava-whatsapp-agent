# V2 Components & API Integration Summary

## ✅ What's Been Implemented

This document summarizes all V2 components and API integration features that are ready to use.

---

## 📦 Available V2 Components

### 1. Interactive Components V2 ✅

**Location:** `src/ai_companion/interfaces/whatsapp/interactive_components_v2.py`

**Components:**
- ✅ `create_size_selection_buttons()` - API presentations or legacy pricing
- ✅ `create_extras_list()` - API modifiers or legacy extras
- ✅ `create_modifiers_list()` - Advanced modifiers with validation
- ✅ `create_category_selection_list()` - API categories or mock data

**Helper Functions:**
- ✅ `extract_modifier_selections()` - Parse user selections
- ✅ `extract_presentation_id()` - Parse size selection

**Usage:**
```python
from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    create_size_selection_buttons,
    create_extras_list,
    create_modifiers_list,
    create_category_selection_list,
    extract_modifier_selections,
    extract_presentation_id,
)
```

### 2. Carousel Components V2 ✅

**Location:** `src/ai_companion/interfaces/whatsapp/carousel_components_v2.py`

**Components:**
- ✅ `create_product_carousel()` - API or legacy product format
- ✅ `create_api_menu_carousel()` - Direct from API menu structure
- ✅ `create_category_products_carousel()` - Category-specific carousels

**Usage:**
```python
from ai_companion.interfaces.whatsapp.carousel_components_v2 import (
    create_product_carousel,
    create_api_menu_carousel,
    create_category_products_carousel,
)
```

### 3. Cart Service V2 ✅

**Location:** `src/ai_companion/modules/cart/cart_service_v2.py`

**Features:**
- ✅ Async menu item lookup via MenuAdapter
- ✅ API presentation support (sizes)
- ✅ API modifier support (extras)
- ✅ Async order creation via API
- ✅ Automatic fallback to local on errors
- ✅ Backward-compatible sync versions

**Usage:**
```python
from ai_companion.modules.cart.cart_service_v2 import CartService, get_cart_service

cart_service = get_cart_service()

# Async version (recommended)
await cart_service.add_item_to_cart(
    cart=cart,
    menu_item_id="prod001",
    presentation_id="pres002",
    modifier_selections={"mod001": ["opt001"]},
)

# Sync version (backward compatible)
cart_service.add_item_to_cart_sync(...)
```

### 4. Order Messages ✅

**Location:** `src/ai_companion/modules/cart/order_messages.py`

**Functions:**
- ✅ `format_order_confirmation()` - Beautiful order confirmations
- ✅ `format_order_status_update()` - Status change notifications
- ✅ `format_order_summary()` - Brief summaries
- ✅ `format_order_error()` - Error messages

**Usage:**
```python
from ai_companion.modules.cart.order_messages import (
    format_order_confirmation,
    format_order_status_update,
)

# Format confirmation
message = format_order_confirmation(order)
await send_whatsapp_message(user_phone, message)
```

### 5. Menu Adapter ✅

**Location:** `src/ai_companion/services/menu_adapter.py`

**Features:**
- ✅ Unified interface for menu operations
- ✅ Automatic API/mock switching
- ✅ Product ID mapping (legacy ↔ API)
- ✅ Graceful fallback on errors

**Usage:**
```python
from ai_companion.services.menu_adapter import get_menu_adapter

adapter = get_menu_adapter()

# Works with both legacy and API IDs
product = await adapter.find_menu_item("prod001")  # API ID
product = await adapter.find_menu_item("pizzas_0")  # Legacy ID (mapped)
```

### 6. Order Service ✅

**Location:** `src/ai_companion/services/cartaai/order_service.py`

**Features:**
- ✅ Create orders via API
- ✅ Get order status
- ✅ Get customer order history
- ✅ Automatic payload building

**Usage:**
```python
from ai_companion.services.cartaai.order_service import get_order_service

order_service = get_order_service()

# Create order
response = await order_service.create_order(
    cart=cart,
    customer_name="John Doe",
    customer_phone="+51987654321",
    delivery_method=DeliveryMethod.DELIVERY,
    payment_method=PaymentMethod.CASH,
    delivery_address="123 Main St",
)

# Track order
order_status = await order_service.get_order(order_id)
```

### 7. Menu Service ✅

**Location:** `src/ai_companion/services/cartaai/menu_service.py`

**Features:**
- ✅ Get menu structure
- ✅ Get product details
- ✅ Search products
- ✅ Automatic caching

**Usage:**
```python
from ai_companion.services.cartaai.menu_service import get_menu_service

menu_service = get_menu_service()

# Get menu
menu = await menu_service.get_menu_structure()

# Get product details
product = await menu_service.get_product_by_id("prod001")

# Search
results = await menu_service.search_products_by_name("burger")
```

---

## 🔧 Configuration

### Feature Flags

**Location:** `src/ai_companion/core/config.py`

**Environment Variables:**
```bash
# Master switch
export USE_CARTAAI_API=true

# Feature toggles
export CARTAAI_MENU_ENABLED=true
export CARTAAI_ORDERS_ENABLED=true
export CARTAAI_DELIVERY_ENABLED=false  # Phase 4

# API credentials
export CARTAAI_SUBDOMAIN=your-restaurant
export CARTAAI_LOCAL_ID=branch-001
export CARTAAI_API_KEY=your_api_key_here

# Optional tuning
export CARTAAI_TIMEOUT=30
export CARTAAI_MAX_RETRIES=3
export CARTAAI_CACHE_TTL=900  # 15 minutes
```

**Checking Configuration:**
```python
from ai_companion.core.config import get_config

config = get_config()
print(f"API Enabled: {config.use_cartaai_api}")
print(f"Menu API: {config.menu_api_enabled}")
print(f"Orders API: {config.orders_api_enabled}")
```

---

## 📋 Integration Points to Update

### Where to Use V2 Components

#### 1. **Menu Browsing Flow**

**Files to Update:**
- `src/ai_companion/graph/menu_nodes.py`
- `src/ai_companion/interfaces/whatsapp/menu_handler.py`

**Changes Needed:**
```python
# OLD
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_category_selection_list
)
categories = create_category_selection_list()  # Mock data

# NEW
from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    create_category_selection_list
)
from ai_companion.services.cartaai.menu_service import get_menu_service

menu_service = get_menu_service()
menu = await menu_service.get_menu_structure()
categories = create_category_selection_list(
    categories=menu["data"]["categories"]
)
```

#### 2. **Product Selection**

**Files to Update:**
- `src/ai_companion/graph/product_nodes.py`
- LangGraph node handlers

**Changes Needed:**
```python
# OLD
from ai_companion.interfaces.whatsapp.carousel_components import (
    create_product_carousel
)
products = get_mock_products(category)
carousel = create_product_carousel(products)

# NEW
from ai_companion.interfaces.whatsapp.carousel_components_v2 import (
    create_api_menu_carousel
)
from ai_companion.services.cartaai.menu_service import get_menu_service

menu_service = get_menu_service()
menu = await menu_service.get_menu_structure()
carousel = create_api_menu_carousel(menu, category_id=category_id)
```

#### 3. **Size/Presentation Selection**

**Files to Update:**
- Customization flow handlers
- Interactive response handlers

**Changes Needed:**
```python
# OLD
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_size_selection_buttons
)
component = create_size_selection_buttons("Burger", base_price=15.99)

# NEW
from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    create_size_selection_buttons
)
from ai_companion.services.cartaai.menu_service import get_menu_service

menu_service = get_menu_service()
product = await menu_service.get_product_by_id(product_id)

component = create_size_selection_buttons(
    product["name"],
    presentations=product.get("presentations")
)
```

#### 4. **Modifier/Extras Selection**

**Files to Update:**
- Customization flow handlers

**Changes Needed:**
```python
# OLD
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_extras_list
)
component = create_extras_list(category="pizza")

# NEW
from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    create_modifiers_list
)
from ai_companion.services.cartaai.menu_service import get_menu_service

menu_service = get_menu_service()
product = await menu_service.get_product_by_id(product_id)

component = create_modifiers_list(
    product["name"],
    modifiers=product.get("modifiers")
)
```

#### 5. **User Response Handling**

**Files to Update:**
- Interactive button/list response handlers

**Changes Needed:**
```python
# OLD
selected_size = reply_id.replace("size_", "")
selected_extras = ["extra_cheese", "bacon"]

# NEW
from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    extract_presentation_id,
    extract_modifier_selections,
)

presentation_id = extract_presentation_id(reply_id)  # "pres002"
modifier_selections = extract_modifier_selections(selected_ids)
# Returns: {"mod001": ["opt001", "opt002"]}
```

#### 6. **Adding Items to Cart**

**Files to Update:**
- Cart operation handlers
- Add to cart nodes

**Changes Needed:**
```python
# OLD
from ai_companion.modules.cart.cart_service import CartService

cart_service = CartService()
success, msg, item = cart_service.add_item_to_cart(
    cart, "pizzas_0", 1, "large", ["extra_cheese"]
)

# NEW
from ai_companion.modules.cart.cart_service_v2 import get_cart_service

cart_service = get_cart_service()
success, msg, item = await cart_service.add_item_to_cart(
    cart=cart,
    menu_item_id="prod001",
    quantity=1,
    presentation_id="pres002",
    modifier_selections={"mod001": ["opt001"]},
)
```

#### 7. **Order Creation**

**Files to Update:**
- Checkout flow handlers
- Order confirmation nodes

**Changes Needed:**
```python
# OLD
from ai_companion.modules.cart.cart_service import CartService

cart_service = CartService()
order = cart_service.create_order_from_cart(
    cart, DeliveryMethod.DELIVERY, "John", "123 Main", "+51..."
)
cart_service.save_order(order)

message = f"Order {order.order_id} confirmed! Total: ${order.total:.2f}"

# NEW
from ai_companion.modules.cart.cart_service_v2 import get_cart_service
from ai_companion.modules.cart.order_messages import format_order_confirmation

cart_service = get_cart_service()
order = await cart_service.create_order_from_cart(
    cart=cart,
    delivery_method=DeliveryMethod.DELIVERY,
    customer_name="John Doe",
    delivery_address="123 Main St",
    delivery_phone="+51987654321",
    payment_method=PaymentMethod.CASH,
)

# Save local backup
cart_service.save_order(order)

# Send beautiful confirmation
message = format_order_confirmation(order)
await send_whatsapp_message(user_phone, message)
```

---

## 🎯 Recommended Migration Order

### Phase 1: Infrastructure (No User-Facing Changes)
1. ✅ Set up API credentials (env vars)
2. ✅ Configure feature flags (disabled)
3. ✅ Test API connectivity
4. ✅ Verify fallback mechanisms

### Phase 2: Menu Integration
1. Update menu browsing to use `menu_service`
2. Update category selection to use API categories
3. Update product carousels to use API products
4. Test with `CARTAAI_MENU_ENABLED=true`

### Phase 3: Product Customization
1. Update size selection to use presentations
2. Update extras selection to use modifiers
3. Update response handlers to extract API IDs
4. Test complete product selection flow

### Phase 4: Cart Operations
1. Update cart service to use v2
2. Update add-to-cart handlers
3. Test cart operations with API data

### Phase 5: Order Creation
1. Update order creation to use v2
2. Update confirmation messages
3. Enable `CARTAAI_ORDERS_ENABLED=true`
4. Test complete order flow

### Phase 6: Production Rollout
1. Deploy with API disabled
2. Enable menu API in production
3. Monitor for 24 hours
4. Enable orders API
5. Monitor order creation success rate

---

## 🧪 Testing Checklist

### Unit Tests
- ✅ 63 tests for API client (Phase 0)
- ✅ 23 tests for menu integration (Phase 1)
- ✅ 20 tests for interactive components (Phase 2)
- ✅ 31 tests for order service (Phase 3)

**Total:** 137 tests

### Integration Tests Needed
- [ ] End-to-end menu browsing
- [ ] Product selection with API
- [ ] Cart operations with API data
- [ ] Order creation via API
- [ ] Fallback to mock data
- [ ] Error recovery

### Manual Testing
- [ ] Browse menu in WhatsApp
- [ ] Select product with presentations
- [ ] Select modifiers
- [ ] Add to cart
- [ ] Create order
- [ ] Receive confirmation message
- [ ] Track order status

---

## 📊 Current Status

### Implemented (Ready to Use)
- ✅ CartaAI API Client
- ✅ Menu Service with caching
- ✅ Order Service
- ✅ Menu Adapter (API/mock switching)
- ✅ Product ID Mapper
- ✅ Interactive Components V2
- ✅ Carousel Components V2
- ✅ Cart Service V2
- ✅ Order Messages
- ✅ Feature Flags

### Pending Integration
- ⏳ Update menu browsing handlers
- ⏳ Update product selection handlers
- ⏳ Update customization handlers
- ⏳ Update cart operation handlers
- ⏳ Update order creation handlers
- ⏳ Update WhatsApp message handlers

### Not Yet Implemented
- ⏹️ Delivery Zones API (Phase 4)
- ⏹️ Driver tracking (Phase 5)
- ⏹️ Order status webhooks (Phase 6)

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Already in requirements.txt
pip install aiohttp python-dotenv
```

### 2. Configure Environment
```bash
# Create .env file
cat > .env << EOF
USE_CARTAAI_API=true
CARTAAI_MENU_ENABLED=true
CARTAAI_ORDERS_ENABLED=true
CARTAAI_SUBDOMAIN=your-restaurant
CARTAAI_LOCAL_ID=branch-001
CARTAAI_API_KEY=your_key_here
EOF
```

### 3. Test API Connection
```python
import asyncio
from ai_companion.services.cartaai.menu_service import get_menu_service

async def test():
    menu_service = get_menu_service()
    menu = await menu_service.get_menu_structure()
    print(f"Categories: {len(menu['data']['categories'])}")

asyncio.run(test())
```

### 4. Start Using V2 Components
```python
# Import v2 versions
from ai_companion.interfaces.whatsapp.interactive_components_v2 import *
from ai_companion.modules.cart.cart_service_v2 import get_cart_service

# Use as shown in examples above
```

---

## 📚 Documentation

- [Migration Guide](./MIGRATION_TO_V2.md) - Step-by-step migration
- [Phase 0 Docs](./PHASE_0_IMPLEMENTATION.md) - API Client
- [Phase 1 Docs](./PHASE_1_IMPLEMENTATION.md) - Menu Integration
- [Phase 2 Docs](./PHASE_2_IMPLEMENTATION.md) - Interactive Components
- [Phase 3 Docs](./PHASE_3_IMPLEMENTATION.md) - Order Creation
- [API Reference](./api/CHATBOT_INTEGRATION.md) - CartaAI API docs

---

**All V2 components are ready to use! Start migration today!** 🚀
