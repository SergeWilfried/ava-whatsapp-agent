# Comprehensive Migration Plan: Mock Data → CartaAI API Integration

## Executive Summary

This document provides a complete, detailed migration strategy from mock restaurant data to the CartaAI API for the WhatsApp ordering chatbot. This plan integrates the full API specification including menu management, order creation, delivery zones, and order tracking.

**Key Differences from Original Plan:**
- ✨ Includes **Order Creation API** (`POST /order`)
- ✨ Includes **Order Tracking API** (`GET /order/get-order/{orderId}`)
- ✨ Includes **Delivery Zones API** (`GET /delivery/zones/{subDomain}/{localId}`)
- ✨ Complete data mapping for all endpoints
- ✨ Phase-by-phase implementation with detailed code examples
- ✨ Comprehensive testing and rollback strategies

**Estimated Timeline:** 3-5 weeks
**Risk Level:** Medium (existing service layer provides good abstraction)

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Target API Integration Overview](#2-target-api-integration-overview)
3. [Migration Architecture](#3-migration-architecture)
4. [Phase-by-Phase Implementation](#4-phase-by-phase-implementation)
5. [Data Mapping Reference](#5-data-mapping-reference)
6. [Technical Implementation Examples](#6-technical-implementation-examples)
7. [Testing Strategy](#7-testing-strategy)
8. [Rollback & Risk Mitigation](#8-rollback--risk-mitigation)
9. [Performance & Optimization](#9-performance--optimization)
10. [Deployment Checklist](#10-deployment-checklist)

---

## 1. Current State Analysis

### 1.1 Mock Data Inventory

| Data Source | File Location | Purpose | Size |
|-------------|--------------|---------|------|
| `RESTAURANT_MENU` | [src/ai_companion/core/schedules.py](../src/ai_companion/core/schedules.py) | 5 categories, 20 menu items | ~200 lines |
| `RESTAURANT_INFO` | Same | Business info, delivery fees, tax | ~30 lines |
| `BUSINESS_HOURS` | Same | Operating hours (7 days) | ~10 lines |
| `SPECIAL_OFFERS` | Same | Combo deals, daily specials | ~20 lines |
| `SIZE_MULTIPLIERS` | [src/ai_companion/modules/cart/cart_service.py](../src/ai_companion/modules/cart/cart_service.py) | Pricing multipliers for sizes | 4 items |
| `EXTRAS_PRICING` | Same | Extra toppings pricing | 10 items |
| `ITEM_SPECIFIC_IMAGES` | [src/ai_companion/interfaces/whatsapp/image_utils.py](../src/ai_companion/interfaces/whatsapp/image_utils.py) | Unsplash image URLs | 16 mappings |

### 1.2 Files Using Mock Data

**High Priority (Core Functionality):**
1. [cart_service.py](../src/ai_companion/modules/cart/cart_service.py) - Menu lookups, pricing
2. [cart_nodes.py](../src/ai_companion/graph/cart_nodes.py) - Ordering workflow
3. [interactive_components.py](../src/ai_companion/interfaces/whatsapp/interactive_components.py) - Size/extras UI

**Medium Priority (Supporting Features):**
4. [carousel_components.py](../src/ai_companion/interfaces/whatsapp/carousel_components.py) - Menu display
5. [context_generation.py](../src/ai_companion/modules/schedules/context_generation.py) - AI context
6. [image_utils.py](../src/ai_companion/interfaces/whatsapp/image_utils.py) - Images

**Low Priority (Reference Data):**
7. [nodes.py](../src/ai_companion/graph/nodes.py) - System context injection

### 1.3 Current Architecture Flow

```
User (WhatsApp) → Webhook → CartInteractionHandler
    ↓
LangGraph Nodes (cart_nodes.py)
    ↓
CartService
    ├─→ find_menu_item() → RESTAURANT_MENU[category][index]
    ├─→ add_item_to_cart() → SIZE_MULTIPLIERS, EXTRAS_PRICING
    ├─→ create_order_from_cart() → RESTAURANT_INFO (fees, tax)
    └─→ save_order() → JSON files (data/carts/orders/*.json)
    ↓
WhatsApp Response (interactive components + carousel)
```

### 1.4 Current Limitations

| Limitation | Impact | API Solution |
|------------|--------|--------------|
| Single restaurant | Cannot scale | Multi-tenant via `subDomain`/`localId` |
| Static menu | Manual code updates | Real-time API updates |
| Hardcoded pricing | Inflexible | Dynamic pricing from API |
| No size variations | Limited customization | `presentations[]` array |
| Local file orders | No centralization | API order management |
| No delivery zones | Fixed delivery fee | Zone-based pricing & validation |
| No order tracking | Manual status updates | Real-time order status API |

---

## 2. Target API Integration Overview

### 2.1 CartaAI API Endpoints

**Base URL:** `https://ssgg.api.cartaai.pe/api/v1`

**Authentication:** JWT Bearer Token in `Authorization` header

#### Tier 1: Critical Endpoints (Must Implement)

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/menu2/bot-structure` | GET | Menu structure for bot | **P0** |
| `/menu/getProductInMenu/{localId}/{subDomain}` | POST | Product details with modifiers | **P0** |
| `/order` | POST | Create order | **P0** |
| `/order/get-order/{orderId}` | GET | Track order status | **P0** |

#### Tier 2: Important Endpoints (Recommended)

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/delivery/zones/{subDomain}/{localId}` | GET | Delivery zone validation & fees | **P1** |
| `/categories/get-all/{subDomain}/{localId}` | GET | Category list | **P1** |
| `/order/filled-orders/{subDomain}/{localId}` | GET | Customer order history | **P1** |

#### Tier 3: Optional Endpoints (Future Enhancement)

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/delivery/drivers/available/{subDomain}/{localId}` | GET | Check driver availability | **P2** |
| `/products/get-all/{subDomain}/{localId}` | GET | All products (alternative to bot-structure) | **P2** |

### 2.2 API Data Models

#### Menu Structure Response
```json
{
  "type": "1",
  "message": "Menu structure retrieved",
  "data": {
    "categories": [
      {
        "id": "cat001",
        "name": "Burgers",
        "position": 1,
        "imageUrl": "https://cdn.example.com/cat.jpg",
        "products": [
          {
            "id": "prod001",
            "name": "Classic Burger",
            "basePrice": 15.99,
            "description": "Juicy beef patty...",
            "imageUrl": "https://cdn.example.com/burger.jpg",
            "isAvailable": true,
            "preparationTime": 15
          }
        ]
      }
    ]
  }
}
```

#### Product Details Response
```json
{
  "success": true,
  "message": "Products retrieved",
  "data": [
    {
      "_id": "prod001",
      "name": "Classic Burger",
      "price": 15.99,
      "category": {
        "_id": "cat001",
        "name": "Burgers"
      },
      "presentations": [
        {"_id": "pres001", "name": "Regular", "price": 15.99},
        {"_id": "pres002", "name": "Large", "price": 18.99}
      ],
      "modifiers": [
        {
          "_id": "mod001",
          "name": "Extras",
          "minSelections": 0,
          "maxSelections": 5,
          "options": [
            {"_id": "opt001", "name": "Extra Cheese", "price": 2.00},
            {"_id": "opt002", "name": "Bacon", "price": 3.00}
          ]
        }
      ]
    }
  ]
}
```

#### Order Creation Request
```json
{
  "customer": {
    "name": "Juan Pérez",
    "phone": "+51987654321",
    "address": {
      "street": "Av. Larco 1234",
      "city": "Lima",
      "district": "Miraflores"
    }
  },
  "items": [
    {
      "productId": "prod001",
      "presentationId": "pres002",
      "name": "Classic Burger",
      "quantity": 1,
      "unitPrice": 18.99,
      "modifiers": [
        {
          "modifierId": "mod001",
          "name": "Extras",
          "options": [
            {
              "optionId": "opt001",
              "name": "Extra Cheese",
              "price": 2.00,
              "quantity": 1
            }
          ]
        }
      ]
    }
  ],
  "type": "delivery",
  "paymentMethod": "cash",
  "source": "whatsapp",
  "deliveryInfo": {
    "address": {
      "street": "Av. Larco 1234",
      "city": "Lima",
      "district": "Miraflores"
    }
  }
}
```

#### Order Status Response
```json
{
  "type": "1",
  "message": "Order retrieved",
  "data": {
    "_id": "order123",
    "orderNumber": "ORD-2024-001234",
    "status": "preparing",
    "total": 25.99,
    "estimatedDeliveryTime": "2024-01-15T14:30:00Z"
  }
}
```

---

## 3. Migration Architecture

### 3.1 New Service Layer Structure

```
src/ai_companion/
├── services/
│   ├── cartaai/                    # NEW: CartaAI integration
│   │   ├── __init__.py
│   │   ├── client.py               # HTTP client with auth
│   │   ├── models.py               # Pydantic models
│   │   ├── menu_service.py         # Menu operations
│   │   ├── order_service.py        # Order operations (NEW)
│   │   ├── delivery_service.py     # Delivery zones (NEW)
│   │   └── cache.py                # Caching layer
│   │
│   ├── config_service.py           # Multi-tenant config (NEW)
│   └── business_service.py         # Existing (fetch credentials)
│
├── mappers/                        # NEW: Data transformation
│   ├── __init__.py
│   ├── product_mapper.py           # API ↔ Internal format
│   └── order_mapper.py             # Order transformation
│
└── modules/
    └── cart/
        └── cart_service.py         # MODIFIED: Use new services
```

### 3.2 Configuration Management

**New Environment Variables:**
```bash
# API Configuration
CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe/api/v1
CARTAAI_SUBDOMAIN=restaurant-name
CARTAAI_LOCAL_ID=branch-001
CARTAAI_API_TOKEN=<jwt_token>

# Feature Flags
USE_CARTAAI_API=true               # Master switch
CARTAAI_MENU_ENABLED=true          # Menu API
CARTAAI_ORDERS_ENABLED=true        # Order creation/tracking
CARTAAI_DELIVERY_ENABLED=true      # Delivery zones

# Performance
CARTAAI_CACHE_TTL=900              # 15 minutes
CARTAAI_API_TIMEOUT=30             # 30 seconds
CARTAAI_MAX_RETRIES=3              # Retry on failure
```

### 3.3 Data Flow (Post-Migration)

```
User (WhatsApp) → Webhook → CartInteractionHandler
    ↓
LangGraph Nodes
    ↓
CartService (refactored)
    ├─→ MenuService
    │   ├─→ MenuCache (check)
    │   └─→ CartaAIClient.get_menu_structure()
    │
    ├─→ OrderService (NEW)
    │   ├─→ CartaAIClient.create_order()
    │   └─→ CartaAIClient.get_order()
    │
    └─→ DeliveryService (NEW)
        └─→ CartaAIClient.get_delivery_zones()
    ↓
WhatsApp Response
```

---

## 4. Phase-by-Phase Implementation

### Phase 0: Setup & Infrastructure (2-3 days)

**Goal:** Create foundational services and configuration

#### Tasks:

1. **Create API Client**
   ```python
   # File: src/ai_companion/services/cartaai/client.py
   class CartaAIClient:
       def __init__(self, base_url, subdomain, local_id, auth_token):
           # Async HTTP client with aiohttp
           # JWT Bearer auth
           # Retry logic with exponential backoff
           # Request/response logging
   ```

2. **Create Configuration Service**
   ```python
   # File: src/ai_companion/services/config_service.py
   class ConfigService:
       def get_business_config(business_id) -> CartaAIConfig:
           # Fetch from BusinessService
           # Return subdomain, local_id, token
   ```

3. **Create Base Mappers**
   ```python
   # File: src/ai_companion/mappers/product_mapper.py
   class ProductMapper:
       @staticmethod
       def api_to_internal(api_product: Dict) -> Dict:
           # Convert API format to internal format
   ```

4. **Add Feature Flags**
   - Add to config.py
   - Create toggle functions
   - Add fallback logic

5. **Setup Test Infrastructure**
   - Mock API responses
   - Test credentials
   - Integration test environment

**Deliverables:**
- ✅ CartaAIClient with authentication
- ✅ ConfigService for multi-tenant setup
- ✅ Feature flag system
- ✅ Base mapper classes
- ✅ Unit tests for client

**Testing:**
- Test API connection
- Test authentication
- Test error handling
- Test retry logic

---

### Phase 1: Menu Structure API (3-4 days)

**Goal:** Replace `RESTAURANT_MENU` with API calls

#### Tasks:

1. **Create MenuService**
   ```python
   # File: src/ai_companion/services/cartaai/menu_service.py
   class MenuService:
       async def get_menu_structure(subdomain, local_id):
           # GET /menu2/bot-structure
           # Cache for 15 minutes
           return menu_data

       async def get_categories():
           # GET /categories/get-all/{subdomain}/{localId}
           return categories
   ```

2. **Create Menu Cache**
   ```python
   # File: src/ai_companion/services/cartaai/cache.py
   class MenuCache:
       def __init__(self, ttl_minutes=15):
           # In-memory cache with TTL
           # Thread-safe with asyncio locks
   ```

3. **Update CartService**
   ```python
   # Modify find_menu_item() method
   # Before:
   def find_menu_item(self, menu_item_id):
       parts = menu_item_id.split("_")
       return RESTAURANT_MENU[parts[0]][int(parts[1])]

   # After:
   async def find_menu_item(self, product_id):
       if USE_CARTAAI_API:
           return await self.menu_service.get_product(product_id)
       else:
           # Fallback to mock data
           return self._find_mock_menu_item(product_id)
   ```

4. **Create Product ID Mapping**
   ```python
   # Map old format to API IDs
   PRODUCT_ID_MAP = {
       "pizzas_0": "prod001",
       "pizzas_1": "prod002",
       "burgers_0": "prod010",
       # ...
   }
   ```

5. **Update Interactive Components**
   - Modify category selection list
   - Update carousel builders
   - Handle API product format

**Data Mapping:**

| Mock Field | API Field | Notes |
|------------|-----------|-------|
| `category` (str) | `categories[].name` | Direct |
| `items[].name` | `products[].name` | Direct |
| `items[].price` | `products[].basePrice` | Direct |
| `"category_index"` | `products[]._id` | Need mapping table |

**Deliverables:**
- ✅ MenuService with caching
- ✅ Updated CartService.find_menu_item()
- ✅ Product ID mapping
- ✅ Unit + integration tests

**Testing:**
- Fetch menu from API
- Compare with mock structure
- Test cache behavior
- Test category navigation

---

### Phase 2: Product Details API (2-3 days)

**Goal:** Replace hardcoded modifiers with API data

#### Tasks:

1. **Extend MenuService**
   ```python
   async def get_product_details(self, product_ids: List[str]):
       # POST /menu/getProductInMenu/{localId}/{subDomain}
       # Body: ["prod001", "prod002"]
       return product_details
   ```

2. **Create Mapper for Presentations**
   ```python
   class ProductMapper:
       @staticmethod
       def map_presentations(api_presentations):
           # Convert to pricing dict
           return {"pres001": 15.99, "pres002": 18.99}
   ```

3. **Create Mapper for Modifiers**
   ```python
   @staticmethod
   def map_modifiers(api_modifiers):
       # Extract options with prices
       # Validate min/max selections
       return modifiers_list
   ```

4. **Update CartService Pricing**
   ```python
   # Replace SIZE_MULTIPLIERS with API presentations
   # Replace EXTRAS_PRICING with API modifiers

   async def calculate_item_price(self, product_id, presentation_id, modifier_selections):
       product = await self.menu_service.get_product_details([product_id])

       # Use presentation price directly
       base_price = product["presentations"][presentation_id]

       # Add modifier prices
       extras_total = sum(
           mod["price"] for mod in get_selected_modifiers(modifier_selections)
       )

       return base_price + extras_total
   ```

5. **Update Interactive Components**
   ```python
   def create_size_selection_buttons(product_details):
       # Use API presentations instead of SIZE_MULTIPLIERS
       buttons = []
       for pres in product_details["presentations"]:
           buttons.append({
               "id": pres["_id"],
               "title": f"{pres['name']} - S/.{pres['price']}"
           })
       return buttons
   ```

**Data Mapping:**

| Mock Field | API Field | Notes |
|------------|-----------|-------|
| `SIZE_MULTIPLIERS["large"]` | `presentations[].price` | Absolute price, not multiplier |
| `EXTRAS_PRICING["extra_cheese"]` | `modifiers[].options[].price` | Direct price |
| N/A | `modifiers[].minSelections` | NEW validation |
| N/A | `modifiers[].maxSelections` | NEW validation |

**Deliverables:**
- ✅ Product details fetching
- ✅ Presentation/modifier mapping
- ✅ Updated pricing logic
- ✅ Updated UI components

**Testing:**
- Fetch product with modifiers
- Validate pricing calculations
- Test required modifiers
- Test max selections enforcement

---

### Phase 3: Order Creation API (3-4 days)

**Goal:** Replace JSON file persistence with API order creation

#### Tasks:

1. **Create OrderService**
   ```python
   # File: src/ai_companion/services/cartaai/order_service.py
   class OrderService:
       async def create_order(self, order_data: Dict):
           # POST /order?subDomain={}&localId={}
           # Body: CreateOrderRequest
           return order_response

       async def get_order(self, order_id: str):
           # GET /order/get-order/{orderId}
           return order_details
   ```

2. **Create OrderMapper**
   ```python
   # File: src/ai_companion/mappers/order_mapper.py
   class OrderMapper:
       @staticmethod
       def cart_to_api_order(cart, customer_info, delivery_info):
           # Convert ShoppingCart → API CreateOrderRequest
           return {
               "customer": {...},
               "items": [...],
               "type": "delivery",
               "paymentMethod": "cash",
               "source": "whatsapp"
           }
   ```

3. **Update CartService.create_order_from_cart()**
   ```python
   async def create_order_from_cart(self, cart, customer_info, delivery_info):
       if USE_CARTAAI_API:
           # Build API request
           order_request = OrderMapper.cart_to_api_order(
               cart, customer_info, delivery_info
           )

           # Create order via API
           response = await self.order_service.create_order(order_request)

           # Store order ID in state
           order_id = response["data"]["_id"]
           order_number = response["data"]["orderNumber"]

           return Order(
               api_order_id=order_id,
               api_order_number=order_number,
               ...
           )
       else:
           # Fallback to JSON file
           return self._create_order_locally(cart, customer_info, delivery_info)
   ```

4. **Map Cart Items to API Format**
   ```python
   def map_cart_item_to_api(cart_item, product_details):
       return {
           "productId": cart_item.menu_item_id,
           "presentationId": cart_item.customization.size,
           "name": cart_item.item_name,
           "quantity": cart_item.quantity,
           "unitPrice": cart_item.unit_price,
           "modifiers": [
               {
                   "modifierId": mod_id,
                   "name": mod_name,
                   "options": [
                       {
                           "optionId": opt_id,
                           "name": opt_name,
                           "price": opt_price,
                           "quantity": 1
                       }
                   ]
               }
           ],
           "notes": cart_item.customization.special_instructions
       }
   ```

5. **Handle Order Response**
   - Store `_id` (order ID for tracking)
   - Store `orderNumber` (display to user)
   - Update order status
   - Send confirmation to user

**Data Mapping:**

| Internal Model | API Field | Notes |
|----------------|-----------|-------|
| `Order.customer_name` | `customer.name` | Direct |
| `Order.customer_phone` | `customer.phone` | Validate format |
| `Order.delivery_address` | `customer.address.street` | Parse address |
| `DeliveryMethod.DELIVERY` | `type: "delivery"` | Enum mapping |
| `PaymentMethod.CASH` | `paymentMethod: "cash"` | Enum mapping |
| N/A | `source: "whatsapp"` | Always set |

**Deliverables:**
- ✅ OrderService implementation
- ✅ OrderMapper for data transformation
- ✅ Updated CartService order creation
- ✅ Order ID storage in state

**Testing:**
- Create order with delivery
- Create order with pickup
- Test with various modifiers
- Verify order in API

---

### Phase 4: Delivery Zones API (2-3 days)

**Goal:** Replace hardcoded delivery fee with zone validation

#### Tasks:

1. **Create DeliveryService**
   ```python
   # File: src/ai_companion/services/cartaai/delivery_service.py
   class DeliveryService:
       async def get_delivery_zones(self):
           # GET /delivery/zones/{subDomain}/{localId}
           # Cache for 1 hour
           return zones

       async def validate_address(self, address):
           # Check if address in any zone
           zones = await self.get_delivery_zones()
           return matching_zone

       async def calculate_delivery_fee(self, zone_id):
           zone = await self.get_zone(zone_id)
           return zone["deliveryCost"]
   ```

2. **Update Location Handling**
   ```python
   # In cart_nodes.py
   async def handle_delivery_method_node(state):
       if delivery_method == "delivery":
           # Request location
           state.awaiting_location = True

           # When location received:
           zone = await delivery_service.validate_address(address)

           if zone:
               state.delivery_zone = zone
               state.delivery_fee = zone["deliveryCost"]
           else:
               return "Address outside delivery area"
   ```

3. **Update CartService.apply_discounts()**
   ```python
   async def apply_discounts(self, cart, delivery_zone):
       # Use zone-specific fees
       delivery_fee = delivery_zone["deliveryCost"]
       minimum_for_free = delivery_zone["minimumForFreeDelivery"]

       if cart.subtotal >= minimum_for_free:
           delivery_fee = 0

       return delivery_fee
   ```

4. **Show Zone Information**
   ```python
   # In interactive components
   def show_delivery_info(zone):
       return f"""
       Delivery to {zone['zoneName']}:
       • Delivery fee: S/.{zone['deliveryCost']}
       • Minimum order: S/.{zone['minimumOrder']}
       • Estimated time: {zone['estimatedTime']} minutes
       """
   ```

**Data Mapping:**

| Mock Field | API Field | Notes |
|------------|-----------|-------|
| `RESTAURANT_INFO["delivery_fee"]` | `deliveryZone.deliveryCost` | Per-zone |
| `RESTAURANT_INFO["free_delivery_minimum"]` | `deliveryZone.minimumForFreeDelivery` | Per-zone |
| N/A | `deliveryZone.minimumOrder` | NEW validation |
| N/A | `deliveryZone.estimatedTime` | Show to user |

**Deliverables:**
- ✅ DeliveryService with zone caching
- ✅ Address validation logic
- ✅ Updated delivery fee calculation
- ✅ Zone-specific UI messages

**Testing:**
- Fetch delivery zones
- Validate known addresses
- Test addresses outside zones
- Test free delivery calculation

---

### Phase 5: Order Tracking API (2-3 days)

**Goal:** Enable real-time order status updates

#### Tasks:

1. **Extend OrderService**
   ```python
   async def poll_order_status(self, order_id, interval=60):
       while True:
           order = await self.get_order(order_id)
           status = order["data"]["status"]

           # Emit status change event
           yield status

           # Stop if terminal status
           if status in ["delivered", "cancelled", "rejected"]:
               break

           await asyncio.sleep(interval)
   ```

2. **Create Status Mapper**
   ```python
   STATUS_MESSAGES = {
       "pending": "⏳ Your order has been received and is awaiting confirmation",
       "confirmed": "✅ Restaurant confirmed your order!",
       "preparing": "👨‍🍳 Your food is being prepared with care",
       "ready": "🍽️ Your order is ready!",
       "dispatched": "🚗 Your order is on the way!",
       "delivered": "🎉 Order delivered! Enjoy your meal!",
       "cancelled": "❌ Order has been cancelled",
       "rejected": "😔 Sorry, the restaurant couldn't fulfill this order"
   }
   ```

3. **Update Cart Nodes**
   ```python
   async def track_order_node(state):
       order_id = state.active_order_id

       # Poll status
       async for status in order_service.poll_order_status(order_id):
           # Send WhatsApp update
           message = STATUS_MESSAGES[status]
           await send_whatsapp_message(state.phone_number_id, message)

           # Update state
           state.order_status = status
   ```

4. **Add Order Status Command**
   ```python
   # User can type "status" or "track" to check order
   if user_message.lower() in ["status", "track", "where is my order"]:
       if state.active_order_id:
           order = await order_service.get_order(state.active_order_id)
           status = order["data"]["status"]
           return STATUS_MESSAGES[status]
   ```

**Status Flow:**
```
pending → confirmed → preparing → ready → dispatched → delivered
          ↓           ↓          ↓
      cancelled   rejected   cancelled
```

**Deliverables:**
- ✅ Order polling logic
- ✅ Status change notifications
- ✅ User-friendly status messages
- ✅ Order status command

**Testing:**
- Mock different order statuses
- Test status transitions
- Test polling interval
- Test terminal statuses

---

### Phase 6: Image CDN Integration (1-2 days)

**Goal:** Replace Unsplash URLs with API images

#### Tasks:

1. **Update ImageService**
   ```python
   # In image_utils.py
   async def get_item_image_url(product_id, product_details=None):
       if USE_CARTAAI_API:
           if not product_details:
               product_details = await menu_service.get_product_details([product_id])

           return product_details.get("imageUrl") or DEFAULT_IMAGE
       else:
           return ITEM_SPECIFIC_IMAGES.get(product_id, DEFAULT_IMAGE)
   ```

2. **Update Carousel Components**
   ```python
   async def create_menu_carousel(category, products):
       cards = []
       for product in products:
           image_url = product.get("imageUrl") or get_default_category_image(category)
           cards.append({
               "header": {"type": "image", "image": {"link": image_url}},
               "body": {"text": product["description"]},
               "footer": {"text": f"S/.{product['basePrice']}"}
           })
       return cards
   ```

**Deliverables:**
- ✅ API image integration
- ✅ Fallback to default images
- ✅ Updated carousel components

**Testing:**
- Test with products that have images
- Test with products missing images
- Verify image URLs are accessible

---

### Phase 7: Cleanup & Optimization (2-3 days)

**Goal:** Remove mock data, optimize, finalize

#### Tasks:

1. **Remove Mock Data**
   - Delete `RESTAURANT_MENU` from schedules.py
   - Remove `SIZE_MULTIPLIERS`, `EXTRAS_PRICING`
   - Clean up unused image mappings

2. **Performance Optimization**
   - Implement Redis cache (optional)
   - Preload menu on startup
   - Optimize API call patterns
   - Add request batching

3. **Monitoring & Logging**
   - Add API call metrics
   - Log response times
   - Set up error alerts
   - Create dashboard

4. **Documentation**
   - Update README
   - Document API configuration
   - Create troubleshooting guide
   - Update architecture diagrams

5. **Final Testing**
   - End-to-end order flow
   - Load testing
   - Error scenarios
   - Multi-location testing

**Deliverables:**
- ✅ Clean codebase
- ✅ Performance benchmarks
- ✅ Complete documentation
- ✅ Deployment guide

---

## 5. Data Mapping Reference

### 5.1 Menu Item Mapping

```python
# Mock Format
RESTAURANT_MENU = {
    "burgers": {
        "category_name": "Burgers",
        "items": [
            {
                "name": "Classic Burger",
                "price": 15.99,
                "description": "Juicy beef patty"
            }
        ]
    }
}

# API Format
{
  "categories": [
    {
      "id": "cat001",
      "name": "Burgers",
      "products": [
        {
          "id": "prod001",
          "name": "Classic Burger",
          "basePrice": 15.99,
          "description": "Juicy beef patty"
        }
      ]
    }
  ]
}

# Mapping Table
CATEGORY_MAP = {"burgers": "cat001"}
PRODUCT_MAP = {"burgers_0": "prod001"}
```

### 5.2 Order Enums Mapping

```python
# Delivery Method
DELIVERY_METHOD_MAP = {
    DeliveryMethod.DELIVERY: "delivery",
    DeliveryMethod.PICKUP: "pickup",
    DeliveryMethod.DINE_IN: "on_site"
}

# Payment Method
PAYMENT_METHOD_MAP = {
    PaymentMethod.CASH: "cash",
    PaymentMethod.CREDIT_CARD: "card",
    PaymentMethod.DEBIT_CARD: "card",
    PaymentMethod.MOBILE_PAYMENT: "yape"  # or "plin"
}

# Order Status
STATUS_MAP = {
    "pending": OrderStatus.PENDING,
    "confirmed": OrderStatus.CONFIRMED,
    "preparing": OrderStatus.PREPARING,
    "ready": OrderStatus.READY,
    "dispatched": OrderStatus.IN_TRANSIT,
    "delivered": OrderStatus.DELIVERED,
    "cancelled": OrderStatus.CANCELLED,
    "rejected": OrderStatus.REJECTED
}
```

---

## 6. Technical Implementation Examples

### 6.1 CartaAIClient Complete Implementation

See detailed implementation in original document (Phase 0).

### 6.2 MenuService with Caching

```python
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MenuService:
    def __init__(self, client: CartaAIClient, cache: MenuCache):
        self.client = client
        self.cache = cache

    async def get_menu_structure(self) -> Dict:
        """Get bot menu structure with caching."""
        cache_key = f"menu:{self.client.subdomain}:{self.client.local_id}"

        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Fetch from API
        response = await self.client.get_menu_structure()
        menu_data = response.get("data", {})

        # Cache for 15 minutes
        await self.cache.set(cache_key, menu_data)

        return menu_data

    async def get_product_details(self, product_ids: List[str]) -> List[Dict]:
        """Get detailed product information."""
        # Check cache for each product
        cached_products = []
        uncached_ids = []

        for product_id in product_ids:
            cache_key = f"product:{product_id}"
            cached = await self.cache.get(cache_key)
            if cached:
                cached_products.append(cached)
            else:
                uncached_ids.append(product_id)

        # Fetch uncached from API
        if uncached_ids:
            response = await self.client.get_product_details(uncached_ids)
            fresh_products = response.get("data", [])

            # Cache each product
            for product in fresh_products:
                cache_key = f"product:{product['_id']}"
                await self.cache.set(cache_key, product)

            cached_products.extend(fresh_products)

        return cached_products

    async def find_product_by_old_id(self, old_id: str) -> Optional[Dict]:
        """Find product using old ID format (e.g., 'burgers_0')."""
        # Use mapping table
        new_id = PRODUCT_MAP.get(old_id)
        if not new_id:
            logger.warning(f"No mapping for old ID: {old_id}")
            return None

        products = await self.get_product_details([new_id])
        return products[0] if products else None
```

### 6.3 OrderMapper Implementation

```python
from typing import Dict, List
from ai_companion.modules.cart.models import ShoppingCart, Order, DeliveryMethod, PaymentMethod

class OrderMapper:
    @staticmethod
    def cart_to_api_order(
        cart: ShoppingCart,
        customer_name: str,
        customer_phone: str,
        delivery_address: str,
        delivery_method: DeliveryMethod,
        payment_method: PaymentMethod,
        special_notes: str = ""
    ) -> Dict:
        """Convert internal cart to API order request."""

        # Parse address (simplified - may need enhancement)
        address_parts = delivery_address.split(",")
        street = address_parts[0].strip() if address_parts else delivery_address
        district = address_parts[1].strip() if len(address_parts) > 1 else ""
        city = address_parts[2].strip() if len(address_parts) > 2 else "Lima"

        # Map items
        items = [
            OrderMapper._map_cart_item(item)
            for item in cart.items
        ]

        # Build order request
        order_request = {
            "customer": {
                "name": customer_name,
                "phone": customer_phone,
                "address": {
                    "street": street,
                    "city": city,
                    "district": district
                }
            },
            "items": items,
            "type": DELIVERY_METHOD_MAP[delivery_method],
            "paymentMethod": PAYMENT_METHOD_MAP[payment_method],
            "source": "whatsapp"
        }

        # Add delivery info if delivery order
        if delivery_method == DeliveryMethod.DELIVERY:
            order_request["deliveryInfo"] = {
                "address": {
                    "street": street,
                    "city": city,
                    "district": district
                }
            }

        # Add notes if present
        if special_notes:
            order_request["notes"] = special_notes

        return order_request

    @staticmethod
    def _map_cart_item(cart_item) -> Dict:
        """Map single cart item to API format."""
        item = {
            "productId": cart_item.menu_item_id,
            "name": cart_item.item_name,
            "quantity": cart_item.quantity,
            "unitPrice": cart_item.unit_price
        }

        # Add presentation (size) if present
        if cart_item.customization and cart_item.customization.size:
            item["presentationId"] = cart_item.customization.size

        # Add modifiers (extras)
        if cart_item.customization and cart_item.customization.extras:
            item["modifiers"] = OrderMapper._build_modifiers(
                cart_item.customization.extras
            )

        # Add special instructions
        if cart_item.customization and cart_item.customization.special_instructions:
            item["notes"] = cart_item.customization.special_instructions

        return item

    @staticmethod
    def _build_modifiers(extras: List[str]) -> List[Dict]:
        """Build modifiers array from extras list."""
        # Simplified - actual implementation needs to match extras to modifier options
        # This requires fetching product details to get modifier structure
        modifiers = []

        # Group extras by modifier (assume single "Extras" modifier for now)
        if extras:
            modifiers.append({
                "modifierId": "mod_extras",  # Would come from product details
                "name": "Extras",
                "options": [
                    {
                        "optionId": extra,  # Would map to actual option ID
                        "name": extra.replace("_", " ").title(),
                        "price": 0.0,  # Would come from product details
                        "quantity": 1
                    }
                    for extra in extras
                ]
            })

        return modifiers
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

```python
# tests/services/test_carta_ai_client.py
import pytest
from aioresponses import aioresponses
from ai_companion.services.cartaai.client import CartaAIClient

@pytest.mark.asyncio
async def test_get_menu_structure_success():
    mock_response = {
        "type": "1",
        "message": "Menu retrieved",
        "data": {"categories": []}
    }

    with aioresponses() as m:
        m.get(
            "https://api.test.com/menu2/bot-structure",
            payload=mock_response
        )

        async with CartaAIClient(
            base_url="https://api.test.com",
            subdomain="test",
            local_id="loc01",
            auth_token="token"
        ) as client:
            result = await client.get_menu_structure()
            assert result["type"] == "1"

@pytest.mark.asyncio
async def test_create_order_success():
    # Test order creation
    pass

@pytest.mark.asyncio
async def test_api_retry_on_500():
    # Test retry logic
    pass
```

### 7.2 Integration Tests

```python
# tests/integration/test_order_flow.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_order_flow():
    """Test end-to-end order creation."""
    # 1. Fetch menu
    menu_service = MenuService(...)
    menu = await menu_service.get_menu_structure()

    # 2. Get product details
    product = await menu_service.get_product_details(["prod001"])

    # 3. Create cart
    cart_service = CartService(...)
    cart = cart_service.create_cart()

    # 4. Add item to cart
    success, _, _ = await cart_service.add_item_to_cart(
        cart, "prod001", 1, "pres001", {}
    )
    assert success

    # 5. Create order
    order_service = OrderService(...)
    order = await cart_service.create_order_from_cart(
        cart, "John Doe", "+51987654321", "Av. Test 123"
    )

    # 6. Verify order created
    assert order.api_order_id

    # 7. Track order
    order_details = await order_service.get_order(order.api_order_id)
    assert order_details["data"]["status"] in ["pending", "confirmed"]
```

### 7.3 Manual Testing Checklist

**Pre-Migration (Mock Data):**
- [ ] Browse menu
- [ ] Select product
- [ ] Customize with size and extras
- [ ] Add to cart
- [ ] View cart
- [ ] Checkout with delivery
- [ ] Verify order saved

**Post-Migration (API):**
- [ ] Same flow with API data
- [ ] Verify prices match
- [ ] Test delivery zone validation
- [ ] Create order in API
- [ ] Track order status
- [ ] Test with multiple products
- [ ] Test error scenarios

---

## 8. Rollback & Risk Mitigation

### 8.1 Feature Flag Rollback

**Immediate rollback (no deployment):**
```bash
# Disable all API features
export USE_CARTAAI_API=false
export CARTAAI_MENU_ENABLED=false
export CARTAAI_ORDERS_ENABLED=false
```

**Gradual rollback (one feature at a time):**
```bash
# Keep menu API, disable orders
export CARTAAI_MENU_ENABLED=true
export CARTAAI_ORDERS_ENABLED=false
```

### 8.2 Rollback Procedure

1. **Detect Issue** - Monitor errors, response times
2. **Assess Impact** - How many users affected?
3. **Execute Rollback** - Set feature flags
4. **Verify** - Test with mock data
5. **Investigate** - Check logs, identify root cause
6. **Fix** - Deploy fix
7. **Re-enable** - Gradually turn on features

### 8.3 Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API downtime | Medium | High | Cache + fallback |
| Rate limiting | Low | Medium | Exponential backoff |
| Data mismatch | Low | High | Strong typing + validation |
| Performance | Medium | Medium | Aggressive caching |
| Auth failure | Low | High | Token refresh + monitoring |

---

## 9. Performance & Optimization

### 9.1 Expected Performance

| Metric | Mock (Current) | API (No Cache) | API (Cached) | Target |
|--------|---------------|----------------|--------------|--------|
| Menu load | <1ms | 300ms | 10ms | <100ms |
| Product details | <1ms | 200ms | 10ms | <100ms |
| Create order | 20ms | 500ms | 500ms | <1s |
| Track order | 50ms | 200ms | N/A | <300ms |

### 9.2 Optimization Strategies

1. **Preload menu on startup**
2. **Cache aggressively (15min TTL)**
3. **Batch API requests**
4. **Use Redis for distributed caching**
5. **Implement request queuing for rate limits**

---

## 10. Deployment Checklist

### 10.1 Pre-Deployment

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Feature flags configured
- [ ] API credentials validated
- [ ] Test environment verified
- [ ] Rollback plan documented
- [ ] Monitoring configured

### 10.2 Deployment Steps

1. [ ] Deploy new code with feature flags OFF
2. [ ] Enable menu API for 10% of users
3. [ ] Monitor for 24 hours
4. [ ] Gradually increase to 50%
5. [ ] Enable for 100% after 48 hours
6. [ ] Enable order API (repeat gradual rollout)
7. [ ] Enable delivery API
8. [ ] Remove mock data after 1 week

### 10.3 Post-Deployment

- [ ] Monitor error rates
- [ ] Check API response times
- [ ] Verify cache hit rates
- [ ] Collect user feedback
- [ ] Update documentation
- [ ] Schedule retrospective

---

## Summary

This comprehensive migration plan provides:

✅ **7 detailed implementation phases**
✅ **Complete API integration** (menu, orders, delivery, tracking)
✅ **Detailed code examples** for all major components
✅ **Data mapping reference** for all endpoints
✅ **Comprehensive testing strategy**
✅ **Rollback procedures** for risk mitigation
✅ **Performance optimization** guidelines
✅ **Deployment checklist** for safe rollout

**Estimated Timeline:** 17-25 days (3-5 weeks)

**Next Steps:**
1. Review and approve plan
2. Set up test environment
3. Begin Phase 0 implementation
4. Proceed sequentially through phases

---

**Document Version:** 2.0 (Comprehensive)
**Last Updated:** 2025-12-04
**Status:** Ready for Implementation
