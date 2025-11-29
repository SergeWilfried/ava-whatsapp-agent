# E-commerce Integration - Implementation Checklist

Use this checklist to track your implementation progress.

---

## ✅ Phase 1: Core Setup (30 minutes)

### Environment Setup

- [ ] Install Python dependencies
  ```bash
  pip install httpx pydantic
  ```

- [ ] Add environment variables to `.env`
  ```bash
  META_APP_SECRET=your_meta_app_secret
  META_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
  WHATSAPP_API_VERSION=v21.0
  ```

- [ ] Verify existing environment variables
  - [ ] `MONGODB_URI`
  - [ ] `MONGODB_DB_NAME`
  - [ ] `ENCRYPTION_SECRET`

### Database Setup

- [ ] Connect to MongoDB
  ```bash
  mongo mongodb://localhost:27017/your_database_name
  ```

- [ ] Create products indexes
  ```javascript
  db.products.createIndex({"rId": 1, "subDomain": 1})
  db.products.createIndex({"subDomain": 1, "categoryId": 1, "isActive": 1})
  db.products.createIndex({"subDomain": 1, "isAvailable": 1, "sortOrder": 1})
  ```

- [ ] Create categories indexes
  ```javascript
  db.categories.createIndex({"rId": 1, "subDomain": 1})
  db.categories.createIndex({"subDomain": 1, "isActive": 1, "sortOrder": 1})
  ```

- [ ] Create orders indexes
  ```javascript
  db.orders.createIndex({"orderNumber": 1}, {unique: true})
  db.orders.createIndex({"subDomain": 1, "status": 1, "createdAt": -1})
  db.orders.createIndex({"conversationId": 1})
  db.orders.createIndex({"customer.phone": 1})
  ```

- [ ] Create carts indexes
  ```javascript
  db.carts.createIndex({"sessionId": 1, "subDomain": 1})
  db.carts.createIndex({"expiresAt": 1}, {expireAfterSeconds: 0})
  ```

### Verify Existing Data

- [ ] Products exist in database
  ```javascript
  db.products.find({subDomain: "YOUR_SUBDOMAIN"}).count()
  ```

- [ ] Categories exist in database
  ```javascript
  db.categories.find({subDomain: "YOUR_SUBDOMAIN"}).count()
  ```

- [ ] Business has required fields
  ```javascript
  db.businesses.findOne({subDomain: "YOUR_SUBDOMAIN"}, {
    fbBusinessId: 1,
    whatsappAccessToken: 1,
    whatsappPhoneNumberIds: 1
  })
  ```

---

## ✅ Phase 2: Code Integration (45 minutes)

### FastAPI Application Updates

- [ ] Open `src/ai_companion/interfaces/whatsapp/webhook_endpoint_optimized.py`

- [ ] Add imports at the top
  ```python
  from ai_companion.interfaces.whatsapp.flow_endpoints import router as flow_router
  from ai_companion.interfaces.whatsapp.meta_webhooks import router as meta_router
  ```

- [ ] Add routers to app (after app creation)
  ```python
  app.include_router(flow_router, prefix="/api/v1")
  app.include_router(meta_router, prefix="/api/v1")
  ```

- [ ] Save file

### LangGraph Workflow Updates

- [ ] Open `src/ai_companion/graph/graph.py`

- [ ] Add imports at the top
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

- [ ] Add e-commerce nodes to graph
  ```python
  graph.add_node("catalog", catalog_node)
  graph.add_node("product_detail", product_detail_node)
  graph.add_node("cart", cart_node)
  graph.add_node("checkout", checkout_node)
  graph.add_node("flow_handler", flow_handler_node)
  ```

- [ ] Update router function to check e-commerce intents
  ```python
  def route_workflow(state: AICompanionState):
      # Check for e-commerce intent FIRST
      if EcommerceRouter.should_route_to_ecommerce(state):
          intent = EcommerceRouter.detect_intent(state)
          workflow = EcommerceRouter.get_ecommerce_workflow(intent)
          return workflow

      # Existing routing logic
      workflow = state.get("workflow", "conversation")
      # ... rest of existing code
  ```

- [ ] Add conditional edge from router
  ```python
  graph.add_conditional_edges("router", route_workflow)
  ```

- [ ] Save file

### WhatsApp Response Handler Updates

- [ ] Open `src/ai_companion/interfaces/whatsapp/whatsapp_response.py`

- [ ] Locate message processing function

- [ ] Add business context extraction
  ```python
  # After getting business from phone_number_id
  business = await business_service.get_business_by_phone_number_id(phone_number_id)

  # Add to initial state
  initial_state = {
      "messages": [HumanMessage(content=message_text)],
      "sub_domain": business["subDomain"],
      "local_id": business.get("locations", [None])[0],
      "user_phone": from_number,
      # ... other existing fields
  }
  ```

- [ ] Save file

---

## ✅ Phase 3: Meta Configuration (15 minutes)

### Meta App Setup

- [ ] Log in to [Meta for Developers](https://developers.facebook.com/)

- [ ] Select your WhatsApp Business app

- [ ] Navigate to WhatsApp → Configuration

- [ ] Edit Webhook settings:
  - **Callback URL:** `https://your-domain.com/api/v1/meta/webhook`
  - **Verify Token:** (copy from your `.env` file)

- [ ] Subscribe to webhook fields:
  - [ ] `messages` (should already be checked)
  - [ ] `product_item_update`
  - [ ] `commerce_order_update`

- [ ] Click "Verify and Save"

- [ ] Test webhook verification
  ```bash
  curl -X GET 'https://your-domain.com/api/v1/meta/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=12345'
  ```
  Should return: `12345`

### Meta Business Manager

- [ ] Go to [Meta Business Suite](https://business.facebook.com/)

- [ ] Select your Business Manager

- [ ] Copy Business Manager ID

- [ ] Verify it matches `fbBusinessId` in your MongoDB business document

---

## ✅ Phase 4: Testing (30 minutes)

### Test 1: Server Startup

- [ ] Start the Python server
  ```bash
  python -m uvicorn src.ai_companion.interfaces.whatsapp.webhook_endpoint_optimized:app --reload
  ```

- [ ] Check for errors in console

- [ ] Verify all routes are registered
  - Look for: `/api/v1/flows/...`
  - Look for: `/api/v1/meta/...`

### Test 2: Browse Catalog

- [ ] Open WhatsApp and send to your business number:
  ```
  Show me the menu
  ```

- [ ] Expected response:
  - Message: "Here's our menu! Select a category:"
  - Interactive list button

- [ ] If not working:
  - [ ] Check logs for errors
  - [ ] Verify products exist in database
  - [ ] Check `isActive` and `isAvailable` fields

### Test 3: Select Category

- [ ] Tap the interactive list

- [ ] Select a category (e.g., "Pizza")

- [ ] Expected response:
  - Message: "Here are the products:"
  - Interactive list with products

- [ ] If not working:
  - [ ] Check `categoryId` matches in products
  - [ ] Verify products are active

### Test 4: View Product

- [ ] Select a product from the list

- [ ] Expected response:
  - Product name, description, price
  - Buttons: "Customize Order" OR "Add to Cart"

- [ ] If not working:
  - [ ] Check product has required fields
  - [ ] Verify presentations/modifiers exist

### Test 5: Product Customization (if available)

- [ ] Tap "Customize Order" button

- [ ] Expected behavior:
  - Flow opens in WhatsApp
  - Shows size selection screen

- [ ] If Flow doesn't open:
  - [ ] Deploy Flow via Node.js backend
    ```bash
    POST /api/v1/whatsapp/flow/deploy/PRODUCT_ID/SUBDOMAIN
    ```
  - [ ] Check `fbFlowMapping` has Flow ID
  - [ ] Verify access token has Flow permissions

### Test 6: Cart Management

- [ ] Send message:
  ```
  Show my cart
  ```

- [ ] Expected response:
  - Cart contents (if items added)
  - OR "Your cart is empty"

- [ ] If not working:
  - [ ] Check cart is saved to MongoDB
  - [ ] Verify session ID format

### Test 7: Checkout

- [ ] Tap "Checkout" button (if cart has items)

- [ ] Expected response:
  - "How would you like to receive your order?"
  - Buttons: Delivery, Pickup

- [ ] Select delivery method

- [ ] Follow checkout flow

### Test 8: Meta Webhook

- [ ] Trigger webhook verification:
  ```bash
  curl -X GET 'https://your-domain.com/api/v1/meta/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=12345'
  ```

- [ ] Expected: Returns `12345`

- [ ] Check server logs for webhook activity

### Test 9: Catalog Sync

- [ ] Trigger manual sync:
  ```bash
  curl -X POST https://your-domain.com/api/v1/meta/catalog/sync/YOUR_SUBDOMAIN
  ```

- [ ] Expected response:
  ```json
  {
    "status": "completed",
    "total_products": 50,
    "synced": 50,
    "failed": 0
  }
  ```

- [ ] Verify in Meta Commerce Manager:
  - [ ] Log in to Commerce Manager
  - [ ] Check catalogs exist for each category
  - [ ] Verify products are visible

---

## ✅ Phase 5: Production Deployment (Optional)

### Pre-Deployment

- [ ] Review all environment variables
- [ ] Test on staging environment
- [ ] Verify all MongoDB indexes are created
- [ ] Check Meta webhook is configured
- [ ] Test complete customer journey

### Deployment

- [ ] Deploy Python application to production
- [ ] Update Meta webhook URL to production domain
- [ ] Test webhook verification in production
- [ ] Monitor logs for errors
- [ ] Test catalog browsing in production

### Post-Deployment

- [ ] Monitor first 10 customer interactions
- [ ] Check catalog sync success rate
- [ ] Verify orders are created correctly
- [ ] Monitor Meta webhook delivery
- [ ] Set up error alerts

---

## ✅ Phase 6: Documentation & Training (Optional)

### Documentation

- [ ] Read full documentation: [ECOMMERCE_INTEGRATION.md](./ECOMMERCE_INTEGRATION.md)
- [ ] Bookmark troubleshooting guide
- [ ] Save API reference for future use

### Team Training

- [ ] Share documentation with team
- [ ] Demonstrate catalog browsing
- [ ] Show product customization flow
- [ ] Explain cart and checkout process
- [ ] Review Meta webhook events

---

## 🎯 Success Criteria

Your integration is complete when:

✅ Customers can browse catalog via WhatsApp
✅ Product details display correctly
✅ Product customization Flow works
✅ Cart management works (add, view, clear)
✅ Checkout process completes
✅ Orders are created in MongoDB
✅ Meta catalog sync works
✅ Meta webhooks are received

---

## 📊 Progress Tracking

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1: Core Setup | 17 tasks | ⏸️ Not Started |
| Phase 2: Code Integration | 13 tasks | ⏸️ Not Started |
| Phase 3: Meta Configuration | 11 tasks | ⏸️ Not Started |
| Phase 4: Testing | 9 tests | ⏸️ Not Started |
| Phase 5: Production Deployment | 10 tasks | ⏸️ Not Started |
| Phase 6: Documentation | 5 tasks | ⏸️ Not Started |

**Total Progress: 0/65 tasks**

---

## 🆘 Need Help?

### Common Issues

**Catalog not showing:**
- Check: Products exist with `isActive: true`
- Check: Business `subDomain` matches
- Check: MongoDB indexes created

**Flow not opening:**
- Check: Flow deployed via Node.js backend
- Check: `fbFlowMapping` has Flow ID
- Check: Access token valid

**Catalog sync fails:**
- Check: `fbBusinessId` is set
- Check: Access token has `catalog_management` permission
- Check: Products have required fields

### Resources

- **Full Documentation:** [ECOMMERCE_INTEGRATION.md](./ECOMMERCE_INTEGRATION.md)
- **Quick Start:** [QUICKSTART.md](./QUICKSTART.md)
- **Summary:** [INTEGRATION_SUMMARY.md](./INTEGRATION_SUMMARY.md)

---

**🎉 Good luck with your implementation!**

Mark each checkbox as you complete the tasks. When all are checked, your e-commerce integration is complete!
