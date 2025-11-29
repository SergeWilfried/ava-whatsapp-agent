# E-commerce Integration - Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will help you quickly integrate the WhatsApp e-commerce functionality into your existing Python AI agent.

---

## Prerequisites

- ✅ Python AI WhatsApp agent running (existing project)
- ✅ Node.js commerce backend running (separate project with products/orders)
- ✅ MongoDB database (shared between both projects)
- ✅ Meta Business Manager account
- ✅ WhatsApp Business API access

---

## Step 1: Install Dependencies

```bash
cd ava-whatsapp-agent

# Install new dependencies (if not already installed)
pip install httpx pydantic
```

---

## Step 2: Set Environment Variables

Add to your `.env` file:

```bash
# Existing variables (keep these)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=your_database_name
ENCRYPTION_SECRET=your_encryption_secret_here

# New e-commerce variables
META_APP_SECRET=your_meta_app_secret_here
META_WEBHOOK_VERIFY_TOKEN=choose_a_strong_token_here
WHATSAPP_API_VERSION=v21.0
```

---

## Step 3: Create MongoDB Indexes

Run these commands in MongoDB:

```javascript
// Connect to your database
use your_database_name

// Products indexes
db.products.createIndex({ "rId": 1, "subDomain": 1 })
db.products.createIndex({ "subDomain": 1, "categoryId": 1, "isActive": 1 })
db.products.createIndex({ "subDomain": 1, "isAvailable": 1, "sortOrder": 1 })

// Categories indexes
db.categories.createIndex({ "rId": 1, "subDomain": 1 })
db.categories.createIndex({ "subDomain": 1, "isActive": 1, "sortOrder": 1 })

// Orders indexes
db.orders.createIndex({ "orderNumber": 1 }, { unique: true })
db.orders.createIndex({ "subDomain": 1, "status": 1, "createdAt": -1 })
db.orders.createIndex({ "conversationId": 1 })

// Carts indexes (for session-based carts)
db.carts.createIndex({ "sessionId": 1, "subDomain": 1 })
db.carts.createIndex({ "expiresAt": 1 }, { expireAfterSeconds: 0 })
```

---

## Step 4: Update FastAPI Application

Update your main webhook file:

`src/ai_companion/interfaces/whatsapp/webhook_endpoint_optimized.py`

Add these imports at the top:

```python
from ai_companion.interfaces.whatsapp.flow_endpoints import router as flow_router
from ai_companion.interfaces.whatsapp.meta_webhooks import router as meta_router
```

Add routers to your FastAPI app (after creating the app):

```python
# Existing webhook routes
# ... your existing code ...

# Add new e-commerce routers
app.include_router(flow_router, prefix="/api/v1")
app.include_router(meta_router, prefix="/api/v1")
```

---

## Step 5: Update LangGraph Workflow

Update your graph file:

`src/ai_companion/graph/graph.py`

Add these imports:

```python
from ai_companion.graph.nodes_ecommerce import (
    catalog_node,
    product_detail_node,
    cart_node,
    checkout_node,
    flow_handler_node
)
from ai_companion.graph.ecommerce_router import EcommerceRouter
```

Add nodes to your graph:

```python
# Add e-commerce nodes
graph.add_node("catalog", catalog_node)
graph.add_node("product_detail", product_detail_node)
graph.add_node("cart", cart_node)
graph.add_node("checkout", checkout_node)
graph.add_node("flow_handler", flow_handler_node)
```

Update your router function to check for e-commerce intents:

```python
def route_workflow(state: AICompanionState):
    """Route to appropriate workflow node"""

    # Check for e-commerce intent FIRST
    if EcommerceRouter.should_route_to_ecommerce(state):
        intent = EcommerceRouter.detect_intent(state)
        workflow = EcommerceRouter.get_ecommerce_workflow(intent)
        return workflow

    # Existing routing logic (conversation, image, audio)
    workflow = state.get("workflow", "conversation")

    if workflow == "image":
        return "image_node"
    elif workflow == "audio":
        return "audio_node"
    else:
        return "conversation_node"

# Add conditional edge
graph.add_conditional_edges("router", route_workflow)
```

---

## Step 6: Configure Meta Webhook

1. Go to [Meta App Dashboard](https://developers.facebook.com/apps/)
2. Select your app → WhatsApp → Configuration
3. Edit Webhook:
   - **Callback URL:** `https://your-domain.com/api/v1/meta/webhook`
   - **Verify Token:** (same as `META_WEBHOOK_VERIFY_TOKEN` in `.env`)
4. Subscribe to webhook fields:
   - ✅ `messages` (already subscribed)
   - ✅ `product_item_update`
   - ✅ `commerce_order_update`

---

## Step 7: Extract Session Context

Update your WhatsApp webhook handler to extract business context:

`src/ai_companion/interfaces/whatsapp/whatsapp_response.py`

Add this to your message processing:

```python
async def process_whatsapp_message(webhook_data):
    # Existing code to extract message...

    # Extract business context
    phone_number_id = webhook_data["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
    from_number = webhook_data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]

    # Get business
    business_service = await get_optimized_business_service()
    business = await business_service.get_business_by_phone_number_id(phone_number_id)

    # Create session ID
    session_id = f"{business['subDomain']}:{from_number}"

    # Add to state
    initial_state = {
        "messages": [HumanMessage(content=message_text)],
        "sub_domain": business["subDomain"],
        "local_id": business.get("locations", [None])[0],  # First location
        "user_phone": from_number,
        # ... other existing state fields ...
    }

    # Invoke graph with state
    result = await graph.ainvoke(initial_state)
```

---

## Step 8: Test the Integration

### Test 1: Browse Catalog

Open WhatsApp and send:

```
You: Show me the menu
```

Expected response:
```
Bot: Here's our menu! Select a category:
     [Interactive List Button]
```

### Test 2: View Products

Tap the list and select a category. Expected response:

```
Bot: Here are the products:
     [Interactive List with products]
```

### Test 3: View Product Details

Select a product. Expected response:

```
Bot: Product details:
     [Product name, description, price]
     [Customize Order] [Back to Menu]
```

---

## Step 9: Deploy Flows (via Node.js Backend)

For products with customization options, deploy Flows:

```bash
# Deploy Flow for a product
curl -X POST http://localhost:3001/api/v1/whatsapp/flow/deploy/prod:pizza-margherita/my-restaurant \
  -u "username:password" \
  -H "Content-Type: application/json" \
  -d '{"forceUpdate": true}'
```

This stores the Flow ID in the business document:

```javascript
{
  "fbFlowMapping": {
    "prod:pizza-margherita": "flow_id_from_meta"
  }
}
```

---

## Step 10: Sync Catalog to Meta

Trigger manual catalog sync:

```bash
curl -X POST https://your-domain.com/api/v1/meta/catalog/sync/my-restaurant
```

Expected response:

```json
{
  "status": "completed",
  "total_products": 50,
  "synced": 50,
  "failed": 0,
  "errors": []
}
```

---

## Verification Checklist

- [ ] Products exist in MongoDB (created via Node.js backend)
- [ ] Categories exist in MongoDB
- [ ] Business has `fbBusinessId` set
- [ ] Business has `whatsappAccessToken` (encrypted)
- [ ] Meta webhook is configured and verified
- [ ] Catalog browse works in WhatsApp
- [ ] Product details show correctly
- [ ] Cart management works
- [ ] Flow customization works (for products with presentations/modifiers)

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│      WhatsApp Cloud API                 │
│  - Messages                             │
│  - Interactive Lists/Buttons            │
│  - WhatsApp Flows                       │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│   Python AI Agent (FastAPI)             │
│                                         │
│  Main Webhook: /whatsapp_response       │
│  Flow Endpoint: /flows/product/{id}     │
│  Meta Webhook: /meta/webhook            │
└───────────────┬─────────────────────────┘
                │
      ┌─────────┴──────────┐
      ↓                    ↓
┌─────────────┐    ┌───────────────┐
│  LangGraph  │    │  Product Svc  │
│  E-commerce │    │  - Get prods  │
│  Nodes      │    │  - Meta sync  │
│             │    │  - Pricing    │
│  - Catalog  │    └───────────────┘
│  - Cart     │            │
│  - Checkout │            ↓
└─────────────┘    ┌───────────────┐
                   │    MongoDB    │
                   │  - Products   │
                   │  - Orders     │
                   │  - Carts      │
                   │  - Business   │
                   └───────────────┘
```

---

## Common Issues & Solutions

### Issue: "No products available"

**Solution:**
1. Check MongoDB has products: `db.products.find({subDomain: "my-restaurant"}).count()`
2. Ensure products have `isActive: true` and `isAvailable: true`
3. Verify business subdomain matches

### Issue: Flow button doesn't open Flow

**Solution:**
1. Deploy Flow via Node.js backend
2. Check `fbFlowMapping` has Flow ID for the product
3. Verify WhatsApp access token has `whatsapp_business_messaging` permission

### Issue: Catalog sync fails

**Solution:**
1. Check `fbBusinessId` is set in business document
2. Verify WhatsApp access token is valid
3. Check token has `catalog_management` permission
4. Ensure product has required fields (name, price)

---

## Next Steps

1. **Test Complete Flow:**
   - Browse catalog → Select product → Customize → Add to cart → Checkout

2. **Configure Order Processing:**
   - Set up order status updates
   - Configure payment methods
   - Set up delivery/pickup workflows

3. **Enable Notifications:**
   - WhatsApp template messages for order status
   - Payment confirmations
   - Delivery updates

4. **Monitor & Optimize:**
   - Track conversion rates
   - Monitor catalog sync success
   - Review customer journeys

---

## Resources

- **Full Documentation:** [ECOMMERCE_INTEGRATION.md](./ECOMMERCE_INTEGRATION.md)
- **Node.js Flow API Docs:** See your commerce backend docs
- **Meta WhatsApp Docs:** https://developers.facebook.com/docs/whatsapp
- **Meta Catalog Docs:** https://developers.facebook.com/docs/marketing-api/catalog

---

**🎉 You're ready to start selling via WhatsApp!**

For questions or issues, refer to the [Troubleshooting section](./ECOMMERCE_INTEGRATION.md#troubleshooting) in the main documentation.
