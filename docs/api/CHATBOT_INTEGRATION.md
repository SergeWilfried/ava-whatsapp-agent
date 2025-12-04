# Chatbot Integration Guide

Complete API documentation for building a conversational ordering chatbot with CartaAI.

## 📋 Table of Contents

- [Overview](#overview)
- [OpenAPI Specifications](#openapi-specifications)
- [Essential Routes for Chatbot](#essential-routes-for-chatbot)
- [Integration Flow](#integration-flow)
- [Authentication](#authentication)
- [Common Use Cases](#common-use-cases)
- [Response Format](#response-format)
- [Error Handling](#error-handling)

## Overview

This guide provides the essential API endpoints and workflows for building a conversational commerce chatbot that enables customers to browse menus, customize orders, and complete purchases through natural conversation.

**Key Capabilities:**
- Browse menu categories and products
- View detailed product information with customization options
- Build orders with modifiers and special instructions
- Check delivery availability and fees
- Create and track orders
- Real-time order status updates

## OpenAPI Specifications

We've created separate OpenAPI specifications for different aspects of the API:

### 📄 Available Specifications

| File | Description | Primary Use Case |
|------|-------------|------------------|
| **[openapi-chatbot.yaml](./openapi-chatbot.yaml)** | 🎯 **Unified Chatbot API** | **START HERE** - Complete chatbot integration with essential endpoints |
| [openapi-products.yaml](./openapi-products.yaml) | Products & Catalog | Product management, presentations, modifiers |
| [openapi-categories.yaml](./openapi-categories.yaml) | Menu Categories | Category browsing and organization |
| [openapi-orders.yaml](./openapi-orders.yaml) | Order Management | Order creation, tracking, and status |
| [openapi-menu.yaml](./openapi-menu.yaml) | Menu Operations | Menu integration, parsing, Excel import |
| [openapi-delivery.yaml](./openapi-delivery.yaml) | Delivery Management | Delivery zones, drivers, real-time tracking |

### 🎯 Recommended Spec for Chatbot Integration

**Use `openapi-chatbot.yaml`** - This unified specification contains only the essential endpoints needed for a conversational ordering experience, with detailed examples and chatbot-specific documentation.

## Essential Routes for Chatbot

### Tier 1: Critical Endpoints (Must Have)

#### 1. Menu Discovery
```
GET /menu2/bot-structure?subDomain={business}&localId={branch}
```
**Purpose:** Load complete menu structure optimized for bot navigation
**Use When:** Initial menu display, category browsing

#### 2. Product Details
```
POST /menu/getProductInMenu/{localId}/{subDomain}
Body: ["productId1", "productId2"]
```
**Purpose:** Get detailed product info with all modifiers and options
**Use When:** User selects a product to customize

#### 3. Order Creation
```
POST /order?subDomain={business}&localId={branch}
Body: { customer, items, type, paymentMethod }
```
**Purpose:** Create new order from conversation
**Use When:** User confirms order

#### 4. Order Tracking
```
GET /order/get-order/{orderId}
```
**Purpose:** Track order status and get details
**Use When:** After order creation, status updates

### Tier 2: Important Endpoints (Recommended)

#### 5. Delivery Zones
```
GET /delivery/zones/{subDomain}/{localId}
```
**Purpose:** Check delivery availability, fees, and minimums
**Use When:** Before order creation for delivery orders

#### 6. Category List
```
GET /categories/get-all/{subDomain}/{localId}
```
**Purpose:** Get all menu categories
**Use When:** Alternative menu navigation

#### 7. Order History
```
GET /order/filled-orders/{subDomain}/{localId}?phone={customerPhone}
```
**Purpose:** Retrieve customer's past orders
**Use When:** "Show my orders" or reorder functionality

### Tier 3: Enhanced Features (Optional)

- Available drivers check
- Order statistics
- Real-time location tracking
- Menu parser (for menu updates)

## Integration Flow

### Typical Conversational Order Flow

```
1. GREETING & MENU DISPLAY
   ├─> Call GET /menu2/bot-structure
   └─> Display categories to user

2. CATEGORY SELECTION
   └─> Show products from selected category

3. PRODUCT SELECTION
   ├─> Call POST /menu/getProductInMenu with [productId]
   ├─> Display product with presentations
   └─> Show available modifiers and options

4. CUSTOMIZATION (if applicable)
   ├─> User selects size/presentation
   ├─> User selects modifiers (e.g., "extra cheese")
   └─> User adds special instructions

5. ADD TO CART
   └─> Store item in conversation context/cart

6. CHECKOUT INITIATION
   ├─> Collect customer info (name, phone)
   ├─> Ask for order type (delivery/pickup)
   └─> If delivery:
       ├─> Collect address
       └─> Call GET /delivery/zones to validate & show fee

7. PAYMENT METHOD
   └─> Ask for payment method (cash, card, yape, etc.)

8. ORDER CONFIRMATION
   ├─> Show order summary with total
   ├─> Get final confirmation
   └─> Call POST /order

9. ORDER TRACKING
   ├─> Save orderId from response
   ├─> Call GET /order/get-order/{orderId} periodically
   └─> Update user on status changes:
       - confirmed → "Restaurant confirmed your order"
       - preparing → "Your food is being prepared"
       - ready → "Your order is ready"
       - dispatched → "Driver is on the way"
       - delivered → "Order delivered! Enjoy!"
```

### Example Conversation Flow

```
Bot:  ¡Hola! 👋 Welcome to Restaurant. What would you like to order today?
      [Shows categories from /menu2/bot-structure]

User: Burgers

Bot:  Great choice! Here are our burgers:
      1. Classic Burger - S/.15.99
      2. Cheese Burger - S/.17.99
      3. Bacon Burger - S/.19.99

User: Classic Burger

Bot:  [Calls /menu/getProductInMenu]
      Classic Burger - S/.15.99

      Choose your size:
      • Regular (S/.15.99)
      • Large (S/.18.99)

User: Large

Bot:  Would you like to add extras?
      • Extra Cheese (+S/.2.00)
      • Bacon (+S/.3.00)
      • No extras

User: Extra cheese

Bot:  Perfect! I've added:
      1x Large Classic Burger with Extra Cheese - S/.20.99

      Would you like to add more items or proceed to checkout?

User: Checkout

Bot:  Great! Can I have your name and phone number?

User: Juan Pérez, +51987654321

Bot:  Would you like delivery or pickup?

User: Delivery

Bot:  What's your delivery address?

User: Av. Larco 1234, Miraflores

Bot:  [Calls /delivery/zones to validate]
      Perfect! Delivery to Miraflores:
      • Delivery fee: S/.5.00
      • Estimated time: 30 minutes

      Order Summary:
      • 1x Large Classic Burger with Extra Cheese - S/.20.99
      • Delivery fee - S/.5.00
      • Total: S/.25.99

      Payment method?

User: Cash

Bot:  [Calls POST /order]
      ✅ Order confirmed!
      Order #ORD-2024-001234

      Status: Pending confirmation
      Estimated delivery: 30 minutes

      I'll keep you updated on your order status!

[5 minutes later]

Bot:  🔔 Your order has been confirmed by the restaurant!
      Your food is being prepared...

[20 minutes later]

Bot:  🚗 Your order is on the way!
      Driver: Miguel
      Track your delivery: [link]
```

## Authentication

### JWT Bearer Token

Most endpoints require authentication via JWT Bearer token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Required Parameters

All requests require location identification:

- **`subDomain`**: Business identifier (e.g., "restaurant-name")
- **`localId`**: Branch/location identifier (e.g., "branch-001")

## Common Use Cases

### Use Case 1: Display Menu Structure

```javascript
// Request
GET /menu2/bot-structure?subDomain=myrestaurant&localId=branch01

// Response
{
  "type": "1",
  "message": "Menu structure retrieved",
  "data": {
    "categories": [
      {
        "id": "cat001",
        "name": "Burgers",
        "position": 1,
        "products": [
          {
            "id": "prod001",
            "name": "Classic Burger",
            "basePrice": 15.99,
            "isAvailable": true
          }
        ]
      }
    ]
  }
}
```

### Use Case 2: Get Product Details with Modifiers

```javascript
// Request
POST /menu/getProductInMenu/branch01/myrestaurant
Content-Type: application/json

["prod001"]

// Response
{
  "success": true,
  "message": "Products retrieved",
  "data": [
    {
      "_id": "prod001",
      "name": "Classic Burger",
      "price": 15.99,
      "presentations": [
        { "_id": "pres001", "name": "Regular", "price": 15.99 },
        { "_id": "pres002", "name": "Large", "price": 18.99 }
      ],
      "modifiers": [
        {
          "_id": "mod001",
          "name": "Extras",
          "minSelections": 0,
          "maxSelections": 5,
          "options": [
            { "_id": "opt001", "name": "Extra Cheese", "price": 2.00 },
            { "_id": "opt002", "name": "Bacon", "price": 3.00 }
          ]
        }
      ]
    }
  ]
}
```

### Use Case 3: Create Order

```javascript
// Request
POST /order?subDomain=myrestaurant&localId=branch01
Content-Type: application/json

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
    },
    "deliveryInstructions": "Ring doorbell twice"
  }
}

// Response
{
  "type": "1",
  "message": "Order created successfully",
  "data": {
    "_id": "order123",
    "orderNumber": "ORD-2024-001234",
    "status": "pending",
    "total": 25.99,
    "estimatedDeliveryTime": "2024-01-15T14:30:00Z"
  }
}
```

### Use Case 4: Track Order Status

```javascript
// Request
GET /order/get-order/order123

// Response
{
  "type": "1",
  "message": "Order retrieved",
  "data": {
    "_id": "order123",
    "orderNumber": "ORD-2024-001234",
    "status": "preparing",
    "customer": {
      "name": "Juan Pérez",
      "phone": "+51987654321"
    },
    "total": 25.99,
    "estimatedDeliveryTime": "2024-01-15T14:30:00Z"
  }
}
```

### Use Case 5: Check Delivery Zones

```javascript
// Request
GET /delivery/zones/myrestaurant/branch01

// Response
{
  "type": "1",
  "message": "Delivery zones retrieved",
  "data": [
    {
      "_id": "zone001",
      "zoneName": "Miraflores",
      "deliveryCost": 5.00,
      "minimumOrder": 20.00,
      "estimatedTime": 30,
      "allowsFreeDelivery": true,
      "minimumForFreeDelivery": 50.00
    }
  ]
}
```

## Response Format

### Success Response

All successful responses follow this structure:

```json
{
  "type": "1",
  "message": "Success message",
  "data": {
    // Response data
  }
}
```

- **`type`**: `"1"` for success, `"3"` for error
- **`message`**: Human-readable message
- **`data`**: Response payload (object or array)

### Error Response

```json
{
  "type": "3",
  "message": "Error description",
  "data": null
}
```

### Common HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | Success | Successful GET/PATCH/DELETE |
| 201 | Created | Successful POST (resource created) |
| 400 | Bad Request | Invalid parameters or validation error |
| 401 | Unauthorized | Missing or invalid authentication token |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Internal server error |

## Error Handling

### Common Errors & Solutions

#### 1. Product Not Available
```json
{
  "type": "3",
  "message": "Product is not available"
}
```
**Solution:** Check `isAvailable` field before allowing selection

#### 2. Delivery Zone Not Found
```json
{
  "type": "3",
  "message": "Address not in delivery zone"
}
```
**Solution:** Check delivery zones before order creation

#### 3. Minimum Order Not Met
```json
{
  "type": "3",
  "message": "Minimum order amount is S/.20.00"
}
```
**Solution:** Validate order total against zone's `minimumOrder`

#### 4. Invalid Modifiers
```json
{
  "type": "3",
  "message": "Required modifier not selected"
}
```
**Solution:** Validate required modifiers (minSelections) before submission

### Best Practices

1. **Always validate availability** before adding items to cart
2. **Check delivery zones** before collecting address
3. **Validate modifier requirements** (min/max selections)
4. **Handle network errors gracefully** with retry logic
5. **Store orderId** for tracking and customer service
6. **Poll order status** periodically for updates
7. **Use source: "whatsapp"** to identify chatbot orders
8. **Validate phone numbers** in international format

## Order Status Flow

Understanding order statuses is crucial for providing real-time updates:

```
pending
  ↓ (Restaurant confirms order)
confirmed
  ↓ (Kitchen starts preparation)
preparing
  ↓ (Food is ready)
ready
  ↓ (Driver picks up order)
dispatched
  ↓ (Customer receives order)
delivered
```

Alternative flows:
- `cancelled` - Customer cancels order
- `rejected` - Restaurant rejects order (out of stock, closed, etc.)

### User-Friendly Status Messages

| Status | Message to User |
|--------|----------------|
| pending | "Your order has been received and is awaiting confirmation" |
| confirmed | "Restaurant confirmed your order! Food preparation will begin shortly" |
| preparing | "Your food is being prepared with care 👨‍🍳" |
| ready | "Your order is ready!" (for pickup) / "Waiting for driver assignment" (for delivery) |
| dispatched | "Your order is on the way! 🚗 Driver: [name]" |
| delivered | "Order delivered! Enjoy your meal! 🎉" |
| cancelled | "Order has been cancelled" |
| rejected | "Sorry, the restaurant couldn't fulfill this order. Please try again" |

## Payment Methods

Supported payment methods:

| Code | Name | Description |
|------|------|-------------|
| `cash` | Cash | Pay with cash on delivery/pickup |
| `card` | Card | Credit/debit card |
| `yape` | Yape | Popular Peruvian mobile payment |
| `plin` | Plin | Mobile payment app |
| `mercado_pago` | Mercado Pago | Latin American payment platform |
| `bank_transfer` | Bank Transfer | Direct bank transfer |

## Order Types

| Code | Name | Use Case |
|------|------|----------|
| `delivery` | Delivery | Immediate delivery |
| `pickup` | Pickup | Customer picks up |
| `on_site` | Dine-in | Eat at restaurant |
| `scheduled_delivery` | Scheduled Delivery | Delivery at specific time |
| `scheduled_pickup` | Scheduled Pickup | Pickup at specific time |

## Testing Checklist

Before deploying your chatbot integration:

- [ ] Can browse menu categories
- [ ] Can view product details with modifiers
- [ ] Can build cart with multiple items
- [ ] Can customize products with modifiers
- [ ] Can validate delivery address
- [ ] Can calculate delivery fee correctly
- [ ] Can create order successfully
- [ ] Can track order status
- [ ] Can handle out-of-stock items
- [ ] Can handle delivery zone validation
- [ ] Error messages are user-friendly
- [ ] Authentication token is properly handled
- [ ] Orders are marked with source: "whatsapp"

## Support & Resources

- **Production API:** `https://ssgg.api.cartaai.pe/api/v1`
- **OpenAPI Specs:** `/docs/openapi-*.yaml`
- **Support Email:** support@cartaai.pe

## Quick Start Example (Pseudocode)

```python
# Initialize chatbot session
def start_conversation():
    menu = fetch_menu_structure(subdomain, local_id)
    return display_categories(menu.categories)

# Handle category selection
def on_category_selected(category_id):
    products = get_products_in_category(category_id)
    return display_products(products)

# Handle product selection
def on_product_selected(product_id):
    product = get_product_details([product_id])
    if product.presentations:
        return ask_for_presentation(product)
    elif product.modifiers:
        return ask_for_modifiers(product)
    else:
        return add_to_cart(product)

# Create order
def checkout(cart, customer, delivery_info):
    # Build order request
    order_data = {
        "customer": customer,
        "items": build_items_from_cart(cart),
        "type": "delivery",
        "paymentMethod": "cash",
        "source": "whatsapp",
        "deliveryInfo": delivery_info
    }

    # Create order
    order = create_order(order_data)

    # Start tracking
    start_order_tracking(order.id)

    return order

# Track order (polling)
def track_order(order_id):
    order = get_order_status(order_id)
    notify_customer_of_status(order.status)

    if order.status not in ["delivered", "cancelled"]:
        schedule_next_check(order_id, delay=60) # Check every minute
```

---

**Ready to integrate?** Start with the [openapi-chatbot.yaml](./openapi-chatbot.yaml) specification!
