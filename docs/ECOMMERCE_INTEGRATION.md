# WhatsApp E-commerce Integration - Complete Guide

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Setup & Configuration](#setup--configuration)
- [API Reference](#api-reference)
- [Workflow Integration](#workflow-integration)
- [Meta Catalog Integration](#meta-catalog-integration)
- [WhatsApp Flows](#whatsapp-flows)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Overview

This integration transforms the Python AI WhatsApp agent into a full-featured e-commerce platform. It enables businesses to sell products directly through WhatsApp using:

- **Meta Commerce Catalog** - Product catalog sync to Meta
- **WhatsApp Flows** - Interactive product customization forms
- **Interactive Messages** - Catalog browsing with lists and buttons
- **Cart Management** - Session-based shopping cart
- **Order Processing** - Complete checkout and order management

### Key Features

✅ **Multi-tenant** - Supports multiple businesses with isolated catalogs
✅ **Category-based Catalogs** - Each category has its own Meta catalog
✅ **Product Customization** - Presentations (sizes) and modifiers (add-ons)
✅ **WhatsApp Flows** - Complex forms for product customization
✅ **Real-time Sync** - Automatic catalog sync on product changes
✅ **Webhook Support** - Meta catalog update notifications
✅ **Session Management** - Persistent shopping cart per user

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    WhatsApp Cloud API                        │
│  - Interactive Messages (Lists, Buttons)                    │
│  - WhatsApp Flows (Multi-screen forms)                      │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────────────┐
│         Python FastAPI Application (Webhook Handler)         │
│  - Main WhatsApp webhook: /whatsapp_response                │
│  - Flow endpoints: /flows/product/{id}/{subdomain}          │
│  - Meta webhooks: /meta/webhook                             │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                  E-commerce Router                           │
│  - Intent Detection (browse, cart, checkout)                │
│  - Interactive Response Parsing                             │
│  - Workflow Routing                                         │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┬─────────────────┐
        │                       │                 │
        ↓                       ↓                 ↓
┌───────────────┐   ┌──────────────────┐   ┌─────────────┐
│  LangGraph    │   │  Product Service │   │   MongoDB   │
│  E-commerce   │   │                  │   │             │
│  Nodes        │   │  - Catalog Mgmt  │   │  - Products │
│               │   │  - Meta Sync     │   │  - Orders   │
│  - Catalog    │   │  - Pricing       │   │  - Carts    │
│  - Product    │   └──────────────────┘   │  - Business │
│  - Cart       │                           └─────────────┘
│  - Checkout   │
│  - Flow       │
└───────────────┘
        │
        ↓
┌─────────────────────────────────────────────────────────────┐
│                Meta Commerce Manager API                     │
│  - Create/Update Catalogs                                   │
│  - Sync Products                                            │
│  - Webhook Notifications                                    │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**Customer Browsing Products:**
```
Customer: "Show me the menu"
    ↓
[WhatsApp Webhook] → Parse message
    ↓
[E-commerce Router] → Detect intent: "browse_catalog"
    ↓
[LangGraph: catalog_node]
    ├─ Fetch categories from MongoDB
    ├─ Build interactive list message
    └─ Return to WhatsApp API
    ↓
Customer sees category list in WhatsApp
    ↓
Customer selects "Pizza" category
    ↓
[WhatsApp Webhook] → Parse selection: "cat:pizza"
    ↓
[E-commerce Router] → Detect intent: "view_category"
    ↓
[LangGraph: catalog_node]
    ├─ Fetch products in category
    ├─ Build product list
    └─ Return to WhatsApp API
    ↓
Customer sees product list
```

**Product Customization with Flow:**
```
Customer selects "Build Your Pizza"
    ↓
[E-commerce Router] → Detect intent: "view_product"
    ↓
[LangGraph: product_detail_node]
    ├─ Fetch product details
    ├─ Check for presentations/modifiers
    ├─ Product HAS customization → Show "Customize" button
    └─ Return message with button
    ↓
Customer taps "Customize Order"
    ↓
[E-commerce Router] → Parse button: "customize:prod_123"
    ↓
[LangGraph: flow_handler_node]
    ├─ Generate Flow endpoint URL
    └─ Return Flow trigger message
    ↓
[WhatsApp sends Flow message]
    ↓
Customer opens Flow in WhatsApp
    ↓
[Flow Endpoint: /flows/product/{id}]
    ├─ ACTION: INIT → Return SIZE_SELECTION screen
    ├─ ACTION: data_exchange → Process size selection
    ├─ Return MODIFIERS_SELECTION screen
    ├─ ACTION: data_exchange → Process modifiers
    ├─ Return ORDER_SUMMARY screen
    └─ ACTION: data_exchange → Add to cart & close Flow
    ↓
Customer returns to WhatsApp chat
    ↓
"✅ Added to cart! View cart or continue shopping?"
```

---

## Components

### 1. MongoDB Schemas (`src/ai_companion/models/schemas.py`)

**Product Schema:**
```python
class Product(BaseModel):
    r_id: str              # Product ID (e.g., "prod:pizza-margherita")
    name: str              # Product name
    description: str       # Product description
    category_id: str       # Category ID (e.g., "cat:pizza")
    category: str          # Category name
    base_price: float      # Base price
    is_available: bool     # Availability
    image_url: str         # Product image
    presentations: List[str]  # Size/variant IDs
    modifiers: List[ProductModifier]  # Add-ons
    sub_domain: str        # Business subdomain
    local_id: str          # Location ID
```

**Order Schema:**
```python
class Order(BaseModel):
    order_number: str      # Generated order number
    customer: CustomerInfo # Customer details
    items: List[OrderItem] # Order items with modifiers
    subtotal: float        # Subtotal
    tax: float             # Tax amount
    delivery_fee: float    # Delivery fee
    total: float           # Total amount
    status: str            # pending|confirmed|preparing|delivered
    type: str              # delivery|pickup
    payment_method: str    # cash|card|digital_wallet
    source: str = "whatsapp"
    sub_domain: str        # Business subdomain
    conversation_id: str   # WhatsApp session ID
```

**Cart Schema:**
```python
class Cart(BaseModel):
    session_id: str        # WhatsApp phone number
    sub_domain: str        # Business subdomain
    items: List[OrderItem] # Cart items
    subtotal: float        # Cart subtotal
    expires_at: datetime   # Cart expiry (24 hours)
```

### 2. Product Service (`src/ai_companion/services/product_service.py`)

**Key Methods:**

```python
class ProductService:
    async def get_products_by_category(
        sub_domain: str,
        category_id: str = None,
        limit: int = 50
    ) -> List[Product]

    async def get_product_by_id(
        product_id: str,
        sub_domain: str
    ) -> Product

    async def get_presentations_for_product(
        product_id: str,
        sub_domain: str
    ) -> List[Presentation]

    async def get_modifiers_for_product(
        product_id: str,
        sub_domain: str
    ) -> List[Modifier]

    async def sync_product_to_meta_catalog(
        product: Product,
        business_data: Dict
    ) -> Dict[str, Any]
```

### 3. E-commerce Graph Nodes (`src/ai_companion/graph/nodes_ecommerce.py`)

**Catalog Node:**
- Shows categories or products based on selection
- Uses interactive list messages
- Handles navigation between categories and products

**Product Detail Node:**
- Shows product information
- Detects if product needs customization
- Shows "Customize" button for complex products
- Shows "Add to Cart" for simple products

**Cart Node:**
- Displays cart contents
- Shows subtotal and item count
- Provides checkout/continue shopping buttons

**Checkout Node:**
- Collects delivery/pickup preference
- Triggers checkout Flow for address/payment
- Creates order in MongoDB

**Flow Handler Node:**
- Generates Flow endpoint URLs
- Prepares Flow context (product ID, cart data)
- Returns Flow trigger message

### 4. E-commerce Router (`src/ai_companion/graph/ecommerce_router.py`)

**Intent Detection:**

```python
class EcommerceRouter:
    @staticmethod
    def detect_intent(state: AICompanionState) -> str:
        """
        Detects intent from message or interactive response.

        Returns:
        - browse_catalog: Show categories/products
        - view_product: Show product details
        - customize_product: Open customization Flow
        - add_to_cart: Add simple product to cart
        - view_cart: Show cart contents
        - checkout: Start checkout process
        """
```

**Interactive Response Parsing:**
- List selections: `[List selection: Pizza (ID: cat:pizza)]`
- Button presses: `[Button: Customize (ID: customize:prod_123)]`
- Extracts IDs and updates state context

### 5. WhatsApp Flow Endpoints (`src/ai_companion/interfaces/whatsapp/flow_endpoints.py`)

**Product Customization Flow:**

```python
@router.post("/flows/product/{product_id}/{sub_domain}")
async def product_flow_data_exchange(
    product_id: str,
    sub_domain: str,
    flow_request: FlowRequest
):
    """
    Handles Flow screens:
    1. SIZE_SELECTION - Choose presentation
    2. MODIFIERS_SELECTION - Select add-ons
    3. ORDER_SUMMARY - Review and confirm
    """
```

**Flow Screens:**

1. **INIT (SIZE_SELECTION):**
   - Shows available presentations (sizes)
   - Default selection
   - Product image and description

2. **data_exchange (SIZE_SELECTION → MODIFIERS_SELECTION):**
   - Receives selected size
   - Returns modifier groups with options
   - Supports single/multiple selection

3. **data_exchange (MODIFIERS_SELECTION → ORDER_SUMMARY):**
   - Receives selected modifiers
   - Calculates total price
   - Shows price breakdown

4. **data_exchange (ORDER_SUMMARY → SUCCESS):**
   - Adds item to cart
   - Returns success message
   - Closes Flow

### 6. Meta Webhooks (`src/ai_companion/interfaces/whatsapp/meta_webhooks.py`)

**Webhook Verification:**
```python
@router.get("/meta/webhook")
async def verify_webhook(
    hub_mode: str,
    hub_verify_token: str,
    hub_challenge: str
):
    """
    Verifies webhook with Meta.
    Returns challenge if token matches.
    """
```

**Webhook Handler:**
```python
@router.post("/meta/webhook")
async def handle_webhook(request: Request):
    """
    Handles webhook events:
    - product_item_update: Product changed in catalog
    - commerce_order_update: Order status changed
    - catalog_update: Catalog modified
    """
```

**Manual Catalog Sync:**
```python
@router.post("/meta/catalog/sync/{sub_domain}")
async def trigger_catalog_sync(sub_domain: str):
    """
    Manually sync all products to Meta catalog.
    Useful for initial setup or recovery.
    """
```

---

## Setup & Configuration

### 1. Environment Variables

```bash
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=your_database_name

# Business Cache
BUSINESS_CACHE_TTL=300              # 5 minutes
BUSINESS_CACHE_SIZE=1000
WARMUP_CACHE=true

# MongoDB Connection Pool
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10

# Encryption
ENCRYPTION_SECRET=your_encryption_secret_here

# Meta/WhatsApp
META_APP_SECRET=your_meta_app_secret
META_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token

# WhatsApp API
WHATSAPP_API_VERSION=v21.0
```

### 2. MongoDB Indexes

**Critical Indexes (must create these):**

```javascript
// Products collection
db.products.createIndex({ "rId": 1, "subDomain": 1 })
db.products.createIndex({ "subDomain": 1, "categoryId": 1, "isActive": 1 })
db.products.createIndex({ "subDomain": 1, "isAvailable": 1, "sortOrder": 1 })

// Categories collection
db.categories.createIndex({ "rId": 1, "subDomain": 1 })
db.categories.createIndex({ "subDomain": 1, "isActive": 1, "sortOrder": 1 })

// Orders collection
db.orders.createIndex({ "orderNumber": 1 }, { unique: true })
db.orders.createIndex({ "subDomain": 1, "status": 1, "createdAt": -1 })
db.orders.createIndex({ "conversationId": 1 })
db.orders.createIndex({ "customer.phone": 1 })

// Carts collection
db.carts.createIndex({ "sessionId": 1, "subDomain": 1 })
db.carts.createIndex({ "expiresAt": 1 }, { expireAfterSeconds: 0 })

// Businesses collection (already exists, add these)
db.businesses.createIndex({
    "whatsappPhoneNumberIds": 1,
    "whatsappEnabled": 1,
    "isActive": 1
})
db.businesses.createIndex({ "subDomain": 1 }, { unique: true })
```

### 3. Meta Setup

**Step 1: Create Meta App**
1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create new Business App
3. Add WhatsApp Product
4. Get App ID and App Secret

**Step 2: Create Business Manager**
1. Go to [Meta Business Suite](https://business.facebook.com/)
2. Create Business Manager
3. Get Business Manager ID

**Step 3: Set up Catalogs**
- Catalogs are created automatically per category
- First product in a category triggers catalog creation
- Stored in `businesses.fbCatalogMapping`

**Step 4: Configure Webhooks**
1. In Meta App Dashboard → WhatsApp → Configuration
2. Set Webhook URL: `https://your-domain.com/meta/webhook`
3. Set Verify Token: (same as `META_WEBHOOK_VERIFY_TOKEN`)
4. Subscribe to fields:
   - `messages` (already subscribed for chat)
   - `product_item_update`
   - `commerce_order_update`

### 4. FastAPI Integration

**Update your main application:**

```python
# src/ai_companion/interfaces/whatsapp/webhook_endpoint_optimized.py

from ai_companion.interfaces.whatsapp.flow_endpoints import router as flow_router
from ai_companion.interfaces.whatsapp.meta_webhooks import router as meta_router

# Include routers
app.include_router(flow_router)
app.include_router(meta_router)
```

### 5. LangGraph Integration

**Update graph to include e-commerce nodes:**

```python
# src/ai_companion/graph/graph.py

from ai_companion.graph.nodes_ecommerce import (
    catalog_node,
    product_detail_node,
    cart_node,
    checkout_node,
    flow_handler_node
)
from ai_companion.graph.ecommerce_router import EcommerceRouter

# Add nodes to graph
graph.add_node("catalog", catalog_node)
graph.add_node("product_detail", product_detail_node)
graph.add_node("cart", cart_node)
graph.add_node("checkout", checkout_node)
graph.add_node("flow_handler", flow_handler_node)

# Add conditional edge from router
def route_workflow(state):
    # Check for e-commerce intent first
    if EcommerceRouter.should_route_to_ecommerce(state):
        intent = EcommerceRouter.detect_intent(state)
        workflow = EcommerceRouter.get_ecommerce_workflow(intent)
        return workflow

    # Existing routing logic (conversation, image, audio)
    return state.get("workflow", "conversation")

graph.add_conditional_edges("router", route_workflow)
```

---

## API Reference

### Flow Endpoints

**POST /flows/product/{product_id}/{sub_domain}**

Product customization Flow data exchange.

**Request Body:**
```json
{
  "version": "3.0",
  "screen": "SIZE_SELECTION",
  "action": "INIT",
  "data": {},
  "flow_token": "..."
}
```

**Response (INIT):**
```json
{
  "version": "3.0",
  "screen": "SIZE_SELECTION",
  "data": {
    "product_name": "Build Your Pizza",
    "product_image": "https://...",
    "size_options": [
      {"id": "pres:small", "title": "Small (10\")", "description": "$12.00"},
      {"id": "pres:large", "title": "Large (16\")", "description": "$18.00"}
    ],
    "selected_size": "pres:small"
  }
}
```

**Response (ORDER_SUMMARY):**
```json
{
  "version": "3.0",
  "screen": "ORDER_SUMMARY",
  "data": {
    "product_name": "Build Your Pizza",
    "base_price": 12.00,
    "modifiers_total": 4.50,
    "total_price": 16.50,
    "modifier_summary": [
      {"name": "Extra Cheese", "quantity": 1, "price": 2.00},
      {"name": "Pepperoni", "quantity": 1, "price": 2.50}
    ]
  }
}
```

### Meta Webhook Endpoints

**GET /meta/webhook**

Webhook verification endpoint.

**Query Parameters:**
- `hub.mode`: "subscribe"
- `hub.verify_token`: Your verification token
- `hub.challenge`: Challenge string from Meta

**Returns:** Challenge integer

**POST /meta/webhook**

Webhook event handler.

**Headers:**
- `X-Hub-Signature-256`: HMAC signature

**Request Body:**
```json
{
  "object": "commerce_account",
  "entry": [{
    "id": "...",
    "time": 1234567890,
    "changes": [{
      "field": "product_item_update",
      "value": {
        "id": "...",
        "retailer_id": "prod:pizza-margherita",
        "action": "UPDATE"
      }
    }]
  }]
}
```

**POST /meta/catalog/sync/{sub_domain}**

Manually trigger catalog sync.

**Response:**
```json
{
  "status": "completed",
  "total_products": 50,
  "synced": 48,
  "failed": 2,
  "errors": [
    {"product_id": "prod:123", "error": "Missing image"}
  ]
}
```

---

## Workflow Integration

### Complete Customer Journey

**1. Browse Catalog**
```
User: "Show me your menu"
    ↓
[Router] → browse_catalog
    ↓
[catalog_node] → Show categories list
    ↓
User selects "Pizza"
    ↓
[catalog_node] → Show products in Pizza category
```

**2. View Product**
```
User selects "Margherita Pizza"
    ↓
[Router] → view_product
    ↓
[product_detail_node]
    ├─ No customization → Show "Add to Cart" button
    └─ Has customization → Show "Customize Order" button
```

**3. Customize Product (with Flow)**
```
User taps "Customize Order"
    ↓
[Router] → customize_product
    ↓
[flow_handler_node] → Generate Flow URL
    ↓
WhatsApp sends Flow message
    ↓
User opens Flow
    ↓
[Flow Endpoint] → SIZE_SELECTION screen
    ↓
User selects "Large"
    ↓
[Flow Endpoint] → MODIFIERS_SELECTION screen
    ↓
User selects toppings
    ↓
[Flow Endpoint] → ORDER_SUMMARY screen
    ↓
User confirms
    ↓
[Flow Endpoint] → Add to cart, close Flow
    ↓
WhatsApp chat shows: "✅ Added to cart!"
```

**4. View Cart**
```
User: "Show my cart"
    ↓
[Router] → view_cart
    ↓
[cart_node] → Show cart items with total
    ↓
Buttons: [Checkout] [Add More] [Clear Cart]
```

**5. Checkout**
```
User taps "Checkout"
    ↓
[Router] → checkout
    ↓
[checkout_node] → Ask delivery/pickup
    ↓
User selects "Delivery"
    ↓
[checkout_node] → Trigger checkout Flow (future)
    OR
[checkout_node] → Ask for address via conversation
    ↓
Collect payment method
    ↓
Create order in MongoDB
    ↓
Send confirmation: "Order #12345 confirmed! 🎉"
```

---

## Meta Catalog Integration

### How Category-Based Catalogs Work

**Concept:**
- Each product category gets its own Meta catalog
- Enables better organization and filtering
- Catalogs are created automatically on first product sync
- Mapping stored in `businesses.fbCatalogMapping`

**Example:**
```javascript
// Business document
{
  "subDomain": "my-restaurant",
  "fbBusinessId": "123456789",
  "fbCatalogMapping": {
    "cat:pizza": "catalog_111",      // Pizza catalog
    "cat:burgers": "catalog_222",    // Burgers catalog
    "cat:drinks": "catalog_333"      // Drinks catalog
  }
}
```

### Automatic Sync Flow

**Product Created/Updated:**
```python
# 1. Product saved to MongoDB (via Node.js backend)
product = {
    "rId": "prod:margherita",
    "categoryId": "cat:pizza",
    "name": "Margherita Pizza",
    "basePrice": 12.00
}

# 2. Python service detects new product (via webhook or polling)
# 3. Check if category catalog exists
catalog_id = business.fbCatalogMapping.get("cat:pizza")

# 4. If no catalog, create one
if not catalog_id:
    catalog_id = await create_category_catalog(
        business_id=business.fbBusinessId,
        category_name="Pizza"
    )
    # Store mapping
    business.fbCatalogMapping["cat:pizza"] = catalog_id

# 5. Sync product to catalog
await sync_product_to_catalog(
    catalog_id=catalog_id,
    product=product
)
```

### Manual Bulk Sync

**Sync all products for a business:**

```bash
curl -X POST https://your-domain.com/meta/catalog/sync/my-restaurant
```

**Response:**
```json
{
  "status": "completed",
  "total_products": 150,
  "synced": 145,
  "failed": 5,
  "errors": [
    {"product_id": "prod:old-item", "error": "Product not found"}
  ]
}
```

---

## WhatsApp Flows

### Flow JSON Structure

**Example: Product Customization Flow**

```json
{
  "version": "3.0",
  "screens": [
    {
      "id": "SIZE_SELECTION",
      "title": "Select Size",
      "data": {
        "product_name": {
          "type": "string",
          "__example__": "Margherita Pizza"
        },
        "size_options": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": {"type": "string"},
              "title": {"type": "string"},
              "description": {"type": "string"}
            }
          },
          "__example__": [
            {"id": "small", "title": "Small", "description": "$12.00"}
          ]
        }
      },
      "layout": {
        "type": "SingleColumnLayout",
        "children": [
          {
            "type": "Form",
            "name": "size_form",
            "children": [
              {
                "type": "Dropdown",
                "name": "selected_size",
                "label": "Choose Size",
                "data-source": "${data.size_options}",
                "required": true
              },
              {
                "type": "Footer",
                "label": "Continue",
                "on-click-action": {
                  "name": "data_exchange",
                  "payload": {
                    "selected_size": "${form.selected_size}"
                  }
                }
              }
            ]
          }
        ]
      }
    },
    {
      "id": "MODIFIERS_SELECTION",
      "title": "Customize Your Order",
      "layout": {
        "type": "SingleColumnLayout",
        "children": [
          // Modifier selection UI
        ]
      }
    },
    {
      "id": "ORDER_SUMMARY",
      "title": "Review Your Order",
      "layout": {
        "type": "SingleColumnLayout",
        "children": [
          // Order summary UI
        ]
      }
    }
  ]
}
```

### Flow Deployment

**Via Node.js Backend:**

The Node.js backend has Flow deployment built-in. When a product with presentations/modifiers is created:

```javascript
// Auto-deploys Flow to Meta
POST /api/v1/whatsapp/flow/deploy/:productId/:subDomain/:localId

// Stores Flow ID in business.fbFlowMapping
{
  "fbFlowMapping": {
    "prod:margherita": "flow_987654321"
  }
}
```

**Flow Triggering (from Python):**

```python
# In flow_handler_node
flow_url = f"https://your-domain.com/flows/product/{product_id}/{sub_domain}"

# Send Flow message via WhatsApp API
await send_flow_message(
    to=customer_phone,
    flow_id=flow_id,
    flow_token=session_token,
    flow_endpoint=flow_url
)
```

---

## Testing

### Test Catalog Browsing

**1. Start conversation:**
```
You: Show me the menu
Bot: Here's our menu! Select a category:
     [Interactive List]
```

**2. Select category:**
```
You: [Select "Pizza" from list]
Bot: Here are the products:
     [Interactive List with products]
```

**3. Select product:**
```
You: [Select "Margherita Pizza"]
Bot: Product details:
     Margherita Pizza
     Classic tomato and mozzarella
     💰 Price: $12.00
     [Customize Order] [Back to Menu]
```

### Test Product Customization

**1. Tap "Customize Order":**
```
WhatsApp opens Flow screen
```

**2. Flow Screen 1 - Select Size:**
```
Choose Size:
○ Small (10") - $12.00
● Medium (12") - $15.00
○ Large (16") - $18.00
[Continue]
```

**3. Flow Screen 2 - Select Toppings:**
```
Extra Toppings:
☐ Pepperoni (+$2.50)
☑ Extra Cheese (+$2.00)
☐ Mushrooms (+$1.50)
[Continue]
```

**4. Flow Screen 3 - Order Summary:**
```
Your Order:
Margherita Pizza (Medium)
+ Extra Cheese

Subtotal: $17.00
[Add to Cart]
```

**5. Added to cart:**
```
Flow closes
Bot: ✅ Added to cart!
     [View Cart] [Continue Shopping]
```

### Test Cart & Checkout

**1. View cart:**
```
You: Show my cart
Bot: 🛒 Your Cart

     1. Margherita Pizza (Medium) x1
        + Extra Cheese
        $17.00

     *Subtotal: $17.00*

     [Checkout] [Add More Items] [Clear Cart]
```

**2. Checkout:**
```
You: [Tap Checkout]
Bot: How would you like to receive your order?
     [🚚 Delivery] [🏪 Pickup] [Back to Cart]
```

**3. Select delivery:**
```
You: [Tap Delivery]
Bot: Please share your delivery address
You: [Share location OR type address]
Bot: Payment method?
     [Cash] [Card] [Yape]
You: [Select Cash]
Bot: Order confirmed! 🎉
     Order #ORD12345
     Estimated delivery: 30-45 min
```

---

## Deployment

### Production Checklist

**Environment:**
- [ ] Set `META_APP_SECRET` environment variable
- [ ] Set `META_WEBHOOK_VERIFY_TOKEN` environment variable
- [ ] Set `ENCRYPTION_SECRET` environment variable
- [ ] Configure MongoDB connection string
- [ ] Set up MongoDB indexes

**Meta Configuration:**
- [ ] Create Meta Business App
- [ ] Add WhatsApp Product
- [ ] Get App ID and Secret
- [ ] Configure webhook URL
- [ ] Subscribe to webhook fields
- [ ] Test webhook verification

**Database:**
- [ ] Products collection populated (via Node.js backend)
- [ ] Categories collection populated
- [ ] Presentations collection populated
- [ ] Modifiers collection populated
- [ ] Businesses collection has Meta credentials

**Testing:**
- [ ] Test catalog browsing
- [ ] Test product customization Flow
- [ ] Test cart management
- [ ] Test checkout process
- [ ] Test Meta webhook delivery
- [ ] Test catalog sync

**Monitoring:**
- [ ] Set up logging for Flow endpoints
- [ ] Monitor Meta webhook delivery
- [ ] Track catalog sync success rate
- [ ] Monitor order creation
- [ ] Set up error alerts

---

## Troubleshooting

### Issue: Catalog not showing

**Symptoms:** User says "show menu" but gets "No products available"

**Diagnosis:**
```python
# Check if products exist
products = await product_service.get_products_by_category(
    sub_domain="my-restaurant"
)
print(f"Found {len(products)} products")

# Check if products are active
active_products = [p for p in products if p.is_active and p.is_available]
print(f"Active products: {len(active_products)}")
```

**Solutions:**
1. Ensure products are created via Node.js backend
2. Check `isActive` and `isAvailable` flags
3. Verify `subDomain` matches business subdomain
4. Check MongoDB indexes are created

### Issue: Flow not opening

**Symptoms:** User taps "Customize Order" but Flow doesn't open

**Diagnosis:**
```python
# Check if Flow is deployed
business = await business_service.get_business_by_subdomain("my-restaurant")
flow_id = business.get("fbFlowMapping", {}).get("prod:margherita")
print(f"Flow ID: {flow_id}")
```

**Solutions:**
1. Deploy Flow via Node.js backend:
   ```bash
   POST /api/v1/whatsapp/flow/deploy/prod:margherita/my-restaurant
   ```
2. Verify Flow ID is stored in `fbFlowMapping`
3. Check Flow endpoint URL is correct
4. Verify WhatsApp access token is valid

### Issue: Meta catalog sync failing

**Symptoms:** Products not appearing in Meta Commerce Manager

**Diagnosis:**
```bash
# Trigger manual sync
curl -X POST https://your-domain.com/meta/catalog/sync/my-restaurant

# Check response for errors
```

**Solutions:**
1. Verify `fbBusinessId` is set in business document
2. Check WhatsApp access token is valid and not expired
3. Ensure token has `catalog_management` permission
4. Check product has required fields (name, price, image)
5. Verify catalog exists for product's category

### Issue: Webhook not receiving events

**Symptoms:** No logs when products are updated in Meta

**Diagnosis:**
```bash
# Test webhook manually
curl -X POST https://your-domain.com/meta/webhook \
  -H "Content-Type: application/json" \
  -d '{"object": "test", "entry": []}'
```

**Solutions:**
1. Verify webhook URL in Meta App settings
2. Check `META_WEBHOOK_VERIFY_TOKEN` matches Meta configuration
3. Test webhook verification endpoint (GET request)
4. Check firewall/load balancer allows Meta IPs
5. Verify webhook signature validation is working

### Issue: Cart items not persisting

**Symptoms:** Cart empties between messages

**Solutions:**
1. Ensure `sessionId` is consistent (phone number)
2. Check cart TTL hasn't expired (24 hours default)
3. Verify cart is saved to MongoDB, not just in-memory state
4. Check MongoDB TTL index on `expiresAt` field

---

## Next Steps

### Enhancements to Consider

1. **Order Status Updates**
   - Send WhatsApp template messages for order status changes
   - "Your order is being prepared..."
   - "Your order is out for delivery..."
   - "Your order has been delivered!"

2. **Payment Integration**
   - Integrate with Stripe/PayPal
   - WhatsApp Pay support (where available)
   - QR code generation for payment apps

3. **Inventory Management**
   - Track stock levels in MongoDB
   - Show "Out of stock" for unavailable items
   - Auto-hide out-of-stock products

4. **Recommendations**
   - "Customers also bought..."
   - Upsell suggestions
   - Personalized recommendations based on order history

5. **Loyalty Program**
   - Points for purchases
   - Rewards and discounts
   - Referral bonuses

6. **Analytics**
   - Track popular products
   - Conversion rates (view → cart → checkout)
   - Average order value
   - Customer lifetime value

---

## Support

For issues or questions:
- Check logs: `tail -f logs/whatsapp_webhook.log`
- Review this documentation
- Test with the provided test cases
- Check Meta documentation: https://developers.facebook.com/docs/whatsapp

---

**🎉 Your Python AI WhatsApp agent is now a full e-commerce platform!**
