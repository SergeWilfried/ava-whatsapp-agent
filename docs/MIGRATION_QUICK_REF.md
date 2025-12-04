# Migration Quick Reference

Quick reference guide for the CartaAI API migration.

## 📁 Related Documents

- **[COMPREHENSIVE_MIGRATION_PLAN.md](./COMPREHENSIVE_MIGRATION_PLAN.md)** - Complete migration plan (all phases, examples, testing)
- **[MIGRATION_PLAN.md](./MIGRATION_PLAN.md)** - Original menu API migration plan
- **[api/CHATBOT_INTEGRATION.md](./api/CHATBOT_INTEGRATION.md)** - CartaAI API documentation
- **[api/openapi-chatbot.yaml](./api/openapi-chatbot.yaml)** - OpenAPI specification

## 🎯 Key API Endpoints

| Endpoint | Priority | Purpose |
|----------|----------|---------|
| `GET /menu2/bot-structure` | **P0** | Menu structure |
| `POST /menu/getProductInMenu/{localId}/{subDomain}` | **P0** | Product details with modifiers |
| `POST /order` | **P0** | Create order |
| `GET /order/get-order/{orderId}` | **P0** | Track order |
| `GET /delivery/zones/{subDomain}/{localId}` | **P1** | Delivery zones & fees |

## 📊 Mock Data Locations

| Data | File | Line |
|------|------|------|
| `RESTAURANT_MENU` | [schedules.py](../src/ai_companion/core/schedules.py) | ~50-180 |
| `SIZE_MULTIPLIERS` | [cart_service.py](../src/ai_companion/modules/cart/cart_service.py) | ~15 |
| `EXTRAS_PRICING` | Same | ~20 |
| Image URLs | [image_utils.py](../src/ai_companion/interfaces/whatsapp/image_utils.py) | ~30-60 |

## 🔧 Files to Modify

### High Priority
1. `cart_service.py` - Menu lookups, pricing, order creation
2. `cart_nodes.py` - Ordering workflow
3. `interactive_components.py` - Size/extras UI

### New Files to Create
1. `services/cartaai/client.py` - HTTP client
2. `services/cartaai/menu_service.py` - Menu operations
3. `services/cartaai/order_service.py` - Order operations
4. `services/cartaai/delivery_service.py` - Delivery zones
5. `mappers/product_mapper.py` - Data transformation
6. `mappers/order_mapper.py` - Order transformation

## 🚀 Implementation Phases

| Phase | Duration | Focus |
|-------|----------|-------|
| 0 | 2-3 days | Setup & infrastructure |
| 1 | 3-4 days | Menu Structure API |
| 2 | 2-3 days | Product Details API |
| 3 | 3-4 days | Order Creation API |
| 4 | 2-3 days | Delivery Zones API |
| 5 | 2-3 days | Order Tracking API |
| 6 | 1-2 days | Image CDN |
| 7 | 2-3 days | Cleanup & optimization |
| **Total** | **17-25 days** | **3-5 weeks** |

## 🔑 Environment Variables

```bash
# API Configuration
CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe/api/v1
CARTAAI_SUBDOMAIN=restaurant-name
CARTAAI_LOCAL_ID=branch-001
CARTAAI_API_TOKEN=<jwt_token>

# Feature Flags
USE_CARTAAI_API=true
CARTAAI_MENU_ENABLED=true
CARTAAI_ORDERS_ENABLED=true
CARTAAI_DELIVERY_ENABLED=true

# Performance
CARTAAI_CACHE_TTL=900              # 15 minutes
CARTAAI_API_TIMEOUT=30             # 30 seconds
CARTAAI_MAX_RETRIES=3
```

## 🗺️ Data Mapping Cheat Sheet

### Menu Items
```python
# Old: "pizzas_0" → New: "prod001"
PRODUCT_MAP = {"pizzas_0": "prod001", ...}
```

### Pricing
```python
# Old: base_price * SIZE_MULTIPLIERS["large"]
# New: presentations[].price (absolute price)
```

### Order Types
```python
DeliveryMethod.DELIVERY → "delivery"
DeliveryMethod.PICKUP → "pickup"
DeliveryMethod.DINE_IN → "on_site"
```

### Payment Methods
```python
PaymentMethod.CASH → "cash"
PaymentMethod.CREDIT_CARD → "card"
PaymentMethod.MOBILE_PAYMENT → "yape" or "plin"
```

### Order Statuses
```
pending → confirmed → preparing → ready → dispatched → delivered
```

## 🧪 Quick Test Commands

```bash
# Test API connection
curl -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/menu2/bot-structure?subDomain=$SUBDOMAIN&localId=$LOCAL_ID"

# Test product details
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '["prod001"]' \
  "$BASE_URL/menu/getProductInMenu/$LOCAL_ID/$SUBDOMAIN"

# Test delivery zones
curl -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/delivery/zones/$SUBDOMAIN/$LOCAL_ID"
```

## 🚨 Rollback Commands

```bash
# Immediate rollback (disable all API)
export USE_CARTAAI_API=false

# Gradual rollback (disable specific features)
export CARTAAI_ORDERS_ENABLED=false  # Keep menu, disable orders
```

## 📋 Pre-Deployment Checklist

- [ ] API credentials configured
- [ ] Test environment validated
- [ ] Feature flags set up
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Rollback plan documented
- [ ] Monitoring configured

## 📞 Key Contacts

- **API Base URL:** https://ssgg.api.cartaai.pe/api/v1
- **Support Email:** support@cartaai.pe
- **Documentation:** [api/CHATBOT_INTEGRATION.md](./api/CHATBOT_INTEGRATION.md)

## 💡 Quick Code Examples

### Fetch Menu
```python
client = CartaAIClient(base_url, subdomain, local_id, token)
menu = await client.get_menu_structure()
```

### Get Product Details
```python
products = await client.get_product_details(["prod001", "prod002"])
```

### Create Order
```python
order_data = OrderMapper.cart_to_api_order(cart, customer, delivery_info)
response = await client.create_order(order_data)
order_id = response["data"]["_id"]
```

### Track Order
```python
order = await client.get_order(order_id)
status = order["data"]["status"]
```

---

**For detailed implementation guides, see [COMPREHENSIVE_MIGRATION_PLAN.md](./COMPREHENSIVE_MIGRATION_PLAN.md)**
