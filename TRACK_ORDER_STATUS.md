# Track Order Button - Integration Status

## Current Status: ⚠️ **Partially Implemented**

### What Exists

#### 1. **UI Button** ✅
**Location:** [interactive_components.py:321](src/ai_companion/interfaces/whatsapp/interactive_components.py:321)

```python
{"id": "track_order", "title": "📦 Suivre Commande"}
```

The button appears in:
- Quick action buttons (after order placement)
- Order status messages (line 644)

#### 2. **Button Handler** ⚠️ **Not Fully Implemented**
**Location:** [cart_handler.py:260-261](src/ai_companion/interfaces/whatsapp/cart_handler.py:260-261)

```python
if interaction_id == "track_order":
    return "conversation", {}  # Let AI handle tracking inquiries
```

**Current Behavior:** Routes to general conversation (AI handles it)
**Issue:** No dedicated tracking node, no API integration

#### 3. **API Methods** ✅ **Available**
**Location:** [order_service.py](src/ai_companion/services/cartaai/order_service.py)

Two methods ready for use:

**Method 1: Get Specific Order**
```python
async def get_order(self, order_id: str) -> Dict[str, Any]
```
- Returns order details by ID
- Includes status, items, total, etc.

**Method 2: Get Customer Orders**
```python
async def get_customer_orders(
    self,
    phone: str,
    status: Optional[str] = None
) -> List[Dict]
```
- Returns all orders for a phone number
- Can filter by status
- Useful for order history

---

## What's Missing

### ❌ **1. Dedicated Track Order Node**

Need to create: `track_order_node()` in `cart_nodes.py`

**Should:**
- Fetch order from API using stored `active_order_id`
- Display current status with emoji
- Show estimated time if available
- Provide tracking updates

### ❌ **2. Order Status Display Component**

Need to enhance the order status message to show real-time data:
- Current order status (from API)
- Estimated delivery/pickup time
- Order progress indicator
- Driver information (if available)

### ❌ **3. Order ID Persistence**

Currently:
- `active_order_id` is stored in state after order creation
- But may be lost if user closes WhatsApp

Should:
- Store order ID associated with phone number
- Allow users to check recent orders
- Handle multiple active orders

---

## Proposed Implementation

### Step 1: Create Track Order Node

Add to [cart_nodes.py](src/ai_companion/graph/cart_nodes.py):

```python
async def track_order_node(state: AICompanionState) -> Dict:
    """Track order status via API.

    Fetches real-time order status and displays to user.
    """
    from ai_companion.services.cartaai.order_service import get_order_service

    # Get order ID from state
    order_id = state.get("active_order_id")
    user_phone = state.get("user_phone")

    if not order_id and not user_phone:
        message = await generate_dynamic_message(
            "no_active_order",
            {}
        )
        return {
            "messages": AIMessage(content=message),
            "order_stage": OrderStage.BROWSING.value
        }

    order_service = get_order_service()

    try:
        if order_id:
            # Fetch specific order
            response = await order_service.get_order(order_id)
            order_data = response.get("data", {})
        else:
            # Fetch latest order for customer
            orders = await order_service.get_customer_orders(user_phone)
            if not orders:
                message = await generate_dynamic_message("no_orders_found", {})
                return {
                    "messages": AIMessage(content=message),
                    "order_stage": OrderStage.BROWSING.value
                }
            order_data = orders[0]  # Most recent order

        # Format order status message
        status_message = format_order_tracking_message(order_data)

        # Create tracking component with refresh button
        interactive_comp = create_order_tracking_component(order_data)

        return {
            "messages": AIMessage(content=status_message),
            "interactive_component": interactive_comp,
            "order_stage": OrderStage.TRACKING.value
        }

    except Exception as e:
        logger.error(f"Error tracking order: {e}")
        message = await generate_dynamic_message(
            "tracking_error",
            {"error": str(e)}
        )
        return {
            "messages": AIMessage(content=message),
            "order_stage": OrderStage.BROWSING.value
        }
```

### Step 2: Add Message Templates

Add to [message_generator.py](src/ai_companion/graph/utils/message_generator.py):

```python
MESSAGE_TEMPLATES = {
    # ... existing templates ...

    "no_active_order": """You are a friendly restaurant assistant.
The customer wants to track an order but has no active orders.
Generate a brief, helpful message.
Language: {language}
""",

    "no_orders_found": """You are a friendly restaurant assistant.
The customer has no order history.
Generate a friendly message encouraging them to place an order.
Language: {language}
""",

    "tracking_error": """You are a friendly restaurant assistant.
There was an error fetching the order status.
Generate a polite apology and suggest trying again.
Language: {language}
Error: {error}
""",
}
```

### Step 3: Create Tracking Display Function

```python
def format_order_tracking_message(order_data: Dict) -> str:
    """Format order tracking message with current status.

    Args:
        order_data: Order data from API

    Returns:
        Formatted tracking message
    """
    order_number = order_data.get("orderNumber", "N/A")
    status = order_data.get("status", "unknown")

    # Status emojis
    status_emoji = {
        "pending": "⏳",
        "confirmed": "✅",
        "preparing": "👨‍🍳",
        "ready": "✅",
        "on_route": "🚚",
        "delivered": "📦",
        "completed": "✅",
        "cancelled": "❌"
    }

    emoji = status_emoji.get(status.lower(), "📋")

    lines = [f"{emoji} *Order Tracking*\n"]
    lines.append(f"📋 Order: *{order_number}*")
    lines.append(f"Status: *{status.title()}*\n")

    # Add status-specific details
    if status == "preparing":
        lines.append("👨‍🍳 Your order is being prepared!")
        if order_data.get("estimatedTime"):
            lines.append(f"⏰ Ready in: ~{order_data['estimatedTime']} min")

    elif status == "ready":
        lines.append("✅ Your order is ready!")
        if order_data.get("type") == "pickup":
            lines.append("🏪 Available for pickup")
        else:
            lines.append("🚚 Driver will arrive shortly")

    elif status == "on_route":
        lines.append("🚚 Your order is on the way!")
        if order_data.get("driver"):
            driver = order_data["driver"]
            lines.append(f"Driver: {driver.get('name')}")

    elif status == "delivered":
        lines.append("📦 Your order has been delivered!")
        lines.append("Enjoy your meal! 🍽️")

    elif status == "cancelled":
        lines.append("❌ This order has been cancelled.")
        if order_data.get("cancellationReason"):
            lines.append(f"Reason: {order_data['cancellationReason']}")

    # Add order total
    if order_data.get("total"):
        lines.append(f"\n💰 Total: ${order_data['total']:.2f}")

    return "\n".join(lines)
```

### Step 4: Create Tracking Component

```python
def create_order_tracking_component(order_data: Dict) -> Dict:
    """Create interactive component for order tracking.

    Args:
        order_data: Order data from API

    Returns:
        Interactive button component
    """
    status = order_data.get("status", "unknown").lower()

    buttons = []

    # Refresh button (always available)
    buttons.append({
        "id": "refresh_tracking",
        "title": "🔄 Actualizar"
    })

    # Status-specific buttons
    if status in ["pending", "confirmed", "preparing"]:
        buttons.append({
            "id": "cancel_order",
            "title": "❌ Annuler"
        })

    if status in ["delivered", "completed"]:
        buttons.append({
            "id": "reorder",
            "title": "🔁 Recommander"
        })

    # Contact support button
    buttons.append({
        "id": "contact_support",
        "title": "💬 Support"
    })

    return {
        "type": "button",
        "body": {"text": "Actions disponibles:"},
        "action": {
            "buttons": [
                {"type": "reply", "reply": btn}
                for btn in buttons[:3]  # Max 3 buttons
            ]
        }
    }
```

### Step 5: Update Cart Handler

Modify [cart_handler.py:260-261](src/ai_companion/interfaces/whatsapp/cart_handler.py:260-261):

```python
if interaction_id == "track_order":
    return "track_order", {}  # Route to dedicated tracking node

if interaction_id == "refresh_tracking":
    return "track_order", {}  # Refresh tracking
```

### Step 6: Update WhatsApp Response Handler

Add to [whatsapp_response.py](src/ai_companion/interfaces/whatsapp/whatsapp_response.py) (around line 500):

```python
elif node_name == "track_order":
    current_state_dict["user_phone"] = from_number
    result = await cart_nodes.track_order_node(current_state_dict)

    # Persist state updates
    await graph.aupdate_state(
        config={"configurable": {"thread_id": session_id}},
        values=result
    )

    message_obj = result.get("messages")
    response_message = message_obj.content if message_obj else "Order tracking"
    interactive_comp = result.get("interactive_component")

    if interactive_comp:
        await send_response(
            from_number, response_message, "interactive_button",
            phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
            interactive_component=interactive_comp
        )
    else:
        await send_response(
            from_number, response_message, "text",
            phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
        )

    return Response(content="Order tracked", status_code=200)
```

---

## API Response Example

### Get Order Response
```json
{
  "type": "1",
  "message": "Order fetched successfully",
  "data": {
    "_id": "order123",
    "orderNumber": "ORD-2024-001234",
    "status": "preparing",
    "total": 45.99,
    "customer": {
      "name": "John Doe",
      "phone": "+51987654321"
    },
    "items": [...],
    "type": "delivery",
    "estimatedTime": 30,
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

### Get Customer Orders Response
```json
{
  "type": "1",
  "message": "Orders fetched successfully",
  "data": [
    {
      "orderNumber": "ORD-2024-001234",
      "status": "delivered",
      "total": 45.99,
      "createdAt": "2024-01-15T10:30:00Z"
    },
    {
      "orderNumber": "ORD-2024-001200",
      "status": "completed",
      "total": 32.50,
      "createdAt": "2024-01-14T19:15:00Z"
    }
  ]
}
```

---

## Benefits of Full Integration

### For Users
- ✅ Real-time order status updates
- ✅ See estimated delivery time
- ✅ Track order progress
- ✅ Quick access to recent orders
- ✅ Easy reordering

### For Business
- ✅ Reduce "where's my order?" support calls
- ✅ Improve customer transparency
- ✅ Enable order analytics
- ✅ Better customer retention

---

## Implementation Checklist

- [ ] Create `track_order_node()` in cart_nodes.py
- [ ] Add tracking message templates
- [ ] Create `format_order_tracking_message()` function
- [ ] Create `create_order_tracking_component()` function
- [ ] Update cart_handler.py routing
- [ ] Add handler in whatsapp_response.py
- [ ] Add OrderStage.TRACKING enum value
- [ ] Test with API
- [ ] Add refresh functionality
- [ ] Add order history view

---

## Current Workaround

**Right now**, when users click "Track Order":
1. Button routes to "conversation"
2. AI receives the request
3. AI can respond conversationally but **cannot fetch real order status**
4. No real-time tracking available

**User sees:** Generic AI response like "Let me check your order..."
**User should see:** Real order status from API with live updates

---

## Recommendation

**Priority: 🟡 Medium**

The API integration is ready and waiting. Implementing the track order node would:
- Enhance user experience significantly
- Reduce support burden
- Leverage existing API capabilities
- Take ~2-3 hours to implement

**Next Steps:**
1. Implement `track_order_node()` (1 hour)
2. Add message formatting (30 min)
3. Update handlers (30 min)
4. Test with API (1 hour)

---

**Status:** ⚠️ Button exists but not connected to API
**API Ready:** ✅ Yes - `get_order()` and `get_customer_orders()` available
**Implementation:** ⏳ Pending
**Estimated Effort:** 2-3 hours
