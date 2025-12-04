# Chatbot API Integration - Quick Reference

## 🎯 Start Here

**Primary Specification:** [openapi-chatbot.yaml](./openapi-chatbot.yaml)

This unified OpenAPI spec contains all essential endpoints for building a conversational ordering chatbot.

## 📚 Available API Specifications

| Specification | Description | Use For |
|--------------|-------------|---------|
| **[openapi-chatbot.yaml](./openapi-chatbot.yaml)** | **🎯 Unified Chatbot API** | **Complete chatbot integration** |
| [openapi-products.yaml](./openapi-products.yaml) | Products & Catalog Management | Product CRUD, presentations, modifiers |
| [openapi-categories.yaml](./openapi-categories.yaml) | Category Management | Menu organization, category operations |
| [openapi-orders.yaml](./openapi-orders.yaml) | Order Management | Full order lifecycle management |
| [openapi-menu.yaml](./openapi-menu.yaml) | Menu Operations | Menu integration, parsing, imports |
| [openapi-delivery.yaml](./openapi-delivery.yaml) | Delivery Management | Zones, drivers, real-time tracking |

## 🔑 Essential Endpoints

### 1. Get Menu Structure (Start Here)
```http
GET /menu2/bot-structure?subDomain={business}&localId={branch}
```
Returns complete menu with categories and products optimized for bot navigation.

### 2. Get Product Details
```http
POST /menu/getProductInMenu/{localId}/{subDomain}
Body: ["productId1", "productId2"]
```
Returns detailed product information with presentations and modifiers.

### 3. Create Order
```http
POST /order?subDomain={business}&localId={branch}
Content-Type: application/json
```
Creates a new order with customer info, items, and delivery details.

### 4. Track Order
```http
GET /order/get-order/{orderId}
```
Gets current order status and details for tracking.

### 5. Check Delivery Zones
```http
GET /delivery/zones/{subDomain}/{localId}
```
Validates delivery availability and gets fees for customer address.

## 🔐 Authentication

All endpoints require JWT Bearer token:

```http
Authorization: Bearer {your_token}
```

Required parameters for all requests:
- **`subDomain`**: Business identifier (e.g., "myrestaurant")
- **`localId`**: Branch identifier (e.g., "branch-01")

## 📦 Order Creation Example

```json
POST /order?subDomain=restaurant&localId=branch01

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
  "source": "whatsapp"
}
```

## 📊 Order Status Flow

```
pending → confirmed → preparing → ready → dispatched → delivered
```

Alternative endings: `cancelled`, `rejected`

## 💡 Response Format

### Success (type: "1")
```json
{
  "type": "1",
  "message": "Success message",
  "data": { /* response data */ }
}
```

### Error (type: "3")
```json
{
  "type": "3",
  "message": "Error description",
  "data": null
}
```

## 🚀 Quick Integration Steps

1. **Get authentication token** for your business
2. **Load menu structure** using `/menu2/bot-structure`
3. **Display categories** to user
4. **Get product details** when user selects item
5. **Collect customizations** (size, modifiers)
6. **Build cart** in conversation context
7. **Collect customer info** (name, phone, address)
8. **Validate delivery zone** using `/delivery/zones`
9. **Create order** using `/order`
10. **Track order status** using `/order/get-order/{orderId}`

## 📖 Full Documentation

See [CHATBOT_INTEGRATION.md](./CHATBOT_INTEGRATION.md) for:
- Detailed endpoint descriptions
- Complete conversation flow examples
- Error handling guide
- Best practices
- Testing checklist
- Example code

## 🌐 API Base URL

```
Production: https://ssgg.api.cartaai.pe/api/v1
```

## 💳 Payment Methods

- `cash` - Cash on delivery/pickup
- `card` - Credit/debit card
- `yape` - Yape (Peru)
- `plin` - Plin (Peru)
- `mercado_pago` - Mercado Pago
- `bank_transfer` - Bank transfer

## 🚗 Order Types

- `delivery` - Immediate delivery
- `pickup` - Customer pickup
- `on_site` - Dine-in
- `scheduled_delivery` - Scheduled delivery
- `scheduled_pickup` - Scheduled pickup

## 📞 Support

- Email: support@cartaai.pe
- Documentation: `/docs/`

---

**Ready to build?** Open [openapi-chatbot.yaml](./openapi-chatbot.yaml) in your API client (Postman, Swagger, etc.) and start integrating!
