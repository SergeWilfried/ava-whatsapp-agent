# 🚀 Shopping Cart Quick Start

Get up and running with the shopping cart system in 5 minutes!

## 📦 What Was Built

A complete **WhatsApp-native ordering system** with:

- ✅ Interactive menu browsing (List Messages)
- ✅ Item customization - sizes & extras (Buttons + Lists)
- ✅ Shopping cart management
- ✅ Checkout flow (Delivery + Payment selection)
- ✅ Payment-ready order details (Order Details Message)
- ✅ Order tracking (Order Status Message)
- ✅ Automatic discounts & tax calculation
- ✅ Order persistence to disk

## 🎯 Files Created

```
src/ai_companion/
├── modules/cart/
│   ├── __init__.py           # Module exports
│   ├── models.py             # Data models (CartItem, Order, etc.)
│   └── cart_service.py       # Business logic (add/remove/checkout)
├── graph/
│   ├── state.py              # Updated with cart fields
│   └── cart_nodes.py         # Graph nodes for cart operations
└── interfaces/whatsapp/
    ├── interactive_components.py  # Extended with cart components
    └── cart_handler.py       # Routes interactive button/list replies

docs/
├── SHOPPING_CART_GUIDE.md    # Comprehensive guide
└── SHOPPING_CART_QUICKSTART.md  # This file
```

## 🔌 Integration (Copy & Paste)

### Step 1: Update your webhook handler

In [whatsapp_response.py](../src/ai_companion/interfaces/whatsapp/whatsapp_response.py), replace the interactive handling section (around line 100-115) with:

```python
elif message["type"] == "interactive":
    # Handle button or list reply
    from ai_companion.interfaces.whatsapp.cart_handler import process_cart_interaction
    from ai_companion.graph import cart_nodes

    interactive_data = message.get("interactive", {})
    interaction_type = interactive_data.get("type")  # "button_reply" or "list_reply"

    # Get current state
    output_state = await graph.aget_state(config={"configurable": {"thread_id": session_id}})
    current_state_dict = dict(output_state.values)

    # Process the interaction
    node_name, state_updates, text_repr = process_cart_interaction(
        interaction_type,
        interactive_data,
        current_state_dict
    )

    # Route to appropriate node
    if node_name == "add_to_cart":
        # Update state with the selected item
        current_state_dict.update(state_updates)
        result = await cart_nodes.add_to_cart_node(current_state_dict)
    elif node_name == "view_cart":
        result = await cart_nodes.view_cart_node(current_state_dict)
    elif node_name == "checkout":
        result = await cart_nodes.checkout_node(current_state_dict)
    elif node_name == "clear_cart":
        result = await cart_nodes.clear_cart_node(current_state_dict)
    elif node_name == "handle_size":
        result = await cart_nodes.handle_size_selection_node(current_state_dict)
    elif node_name == "handle_extras":
        result = await cart_nodes.handle_extras_selection_node(current_state_dict)
    elif node_name == "handle_delivery_method":
        result = await cart_nodes.handle_delivery_method_node(current_state_dict)
    elif node_name == "handle_payment_method":
        result = await cart_nodes.handle_payment_method_node(current_state_dict)
    elif node_name == "show_menu":
        # Show menu again
        from ai_companion.interfaces.whatsapp.interactive_components import create_menu_list_from_restaurant_menu
        from ai_companion.core.schedules import RESTAURANT_MENU
        result = {
            "messages": [AIMessage(content="Here's our menu!")],
            "interactive_component": create_menu_list_from_restaurant_menu(RESTAURANT_MENU)
        }
    else:
        # Default to conversation flow
        content = text_repr
        # Continue with normal message processing...
        # (Keep your existing conversation flow here)

    # Send the response
    if result:
        response_message = result.get("messages", [])[-1].content if result.get("messages") else "Processing..."
        interactive_comp = result.get("interactive_component")

        if interactive_comp:
            # Send as interactive message
            message_type = interactive_comp.get("type")
            if message_type == "order_details":
                success = await send_response(
                    from_number, response_message, "interactive",
                    phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                    interactive_component=interactive_comp
                )
            elif message_type == "order_status":
                success = await send_response(
                    from_number, response_message, "interactive",
                    phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                    interactive_component=interactive_comp
                )
            else:
                # Regular interactive (button or list)
                msg_type = "interactive_button" if message_type == "button" else "interactive_list"
                success = await send_response(
                    from_number, response_message, msg_type,
                    phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                    interactive_component=interactive_comp
                )
        else:
            # Send as text
            success = await send_response(
                from_number, response_message, "text",
                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
            )
```

### Step 2: Update send_response function

Add support for order_details and order_status message types:

```python
async def send_response(
    from_number: str,
    response_text: str,
    message_type: str = "text",
    media_content: bytes = None,
    phone_number_id: Optional[str] = None,
    whatsapp_token: Optional[str] = None,
    interactive_component: Optional[Dict] = None,
) -> bool:
    """Send response to user via WhatsApp API."""
    # ... existing code ...

    # Add these new message types:
    elif message_type == "interactive":
        # Generic interactive message (order_details, order_status, etc.)
        json_data = {
            "messaging_product": "whatsapp",
            "to": from_number,
            "type": "interactive",
            "interactive": interactive_component
        }

    # ... rest of existing code ...
```

### Step 3: Create data directory

```bash
mkdir -p data/carts/orders
```

That's it! 🎉

## 🧪 Quick Test

1. **Start your Ava agent**
   ```bash
   python -m ai_companion.interfaces.whatsapp.webhook_endpoint
   ```

2. **Send "menu" to your WhatsApp bot**
   - You should see an interactive list with categories

3. **Tap a menu item (e.g., "🍕 Margherita")**
   - Bot asks for size selection

4. **Select size, add extras**
   - Bot confirms addition to cart

5. **Tap "View Cart" then "Checkout"**
   - Complete the flow: delivery → payment → order confirmation

## 📊 Order Flow Visualization

```
┌─────────────────┐
│   Browse Menu   │ ← List Message (categories & items)
└────────┬────────┘
         ↓
┌─────────────────┐
│  Select Item    │ ← User taps list item
└────────┬────────┘
         ↓
┌─────────────────┐
│  Choose Size    │ ← Button Message (Small/Medium/Large)
└────────┬────────┘
         ↓
┌─────────────────┐
│   Add Extras    │ ← List Message (toppings, add-ons)
└────────┬────────┘
         ↓
┌─────────────────┐
│  Item Added!    │ ← Button Message (Add More/View Cart/Checkout)
└────────┬────────┘
         ↓
┌─────────────────┐
│   View Cart     │ ← Shows cart summary + buttons
└────────┬────────┘
         ↓
┌─────────────────┐
│    Checkout     │ ← Button Message (Delivery/Pickup/Dine-In)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Select Payment  │ ← List Message (Card/Cash/Mobile)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Order Details   │ ← Order Details Message (PAYMENT READY!)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Order Confirmed │ ← Order Status Message (tracking)
└─────────────────┘
```

## 💡 Pro Tips

### Tip 1: Customize Menu Icons

Edit `interactive_components.py`:
```python
category_icons = {
    "pizzas": "🍕",
    "burgers": "🍔",
    "sides": "🍟",
    "drinks": "🥤",
    "desserts": "🍰",
    "salads": "🥗",  # Add your categories
}
```

### Tip 2: Adjust Pricing

Edit `cart_service.py`:
```python
SIZE_MULTIPLIERS = {
    "small": 0.8,    # 80% of base price
    "medium": 1.0,   # 100% (default)
    "large": 1.3,    # 130%
    "x-large": 1.5,  # 150%
}

EXTRAS_PRICING = {
    "extra_cheese": 2.00,
    "mushrooms": 1.50,
    # Add more extras...
}
```

### Tip 3: Add Daily Specials

Already implemented! Edit `core/schedules.py`:
```python
SPECIAL_OFFERS = {
    "daily_specials": {
        "monday": "10% off all pizzas",
        "tuesday": "Buy 1 Burger, Get 1 50% off",
        # ...
    }
}
```

### Tip 4: Track Order Analytics

Orders are saved to `data/carts/orders/{ORDER-ID}.json`:
```python
from pathlib import Path
import json

orders_path = Path("data/carts/orders")
total_revenue = 0

for order_file in orders_path.glob("*.json"):
    with open(order_file) as f:
        order = json.load(f)
        total_revenue += order["total"]

print(f"Total revenue: ${total_revenue:.2f}")
```

## 🐛 Common Issues

### Issue: "Item not found"
**Fix**: Ensure menu item IDs match the pattern `{category}_{index}` (e.g., `pizzas_0`)

### Issue: Interactive component not showing
**Fix**: Check you're using `message_type="interactive"` and passing the component dict

### Issue: Order total is wrong
**Fix**: Verify tax rate in `RESTAURANT_INFO["tax_rate"]` (default: 0.08 = 8%)

### Issue: Payment button doesn't work
**Fix**: Order Details messages require Meta Business Manager payment setup. For testing, use simulated responses.

## 📚 Next Steps

1. **Read the full guide**: [SHOPPING_CART_GUIDE.md](SHOPPING_CART_GUIDE.md)
2. **Integrate payment provider**: Stripe, Razorpay, Square
3. **Add order tracking**: Real-time status updates
4. **Build analytics dashboard**: Track popular items, conversion rates
5. **Implement loyalty program**: Reward repeat customers

## 🎨 Example Components

### Show Menu
```python
from ai_companion.interfaces.whatsapp.interactive_components import create_menu_list_from_restaurant_menu
from ai_companion.core.schedules import RESTAURANT_MENU

menu_component = create_menu_list_from_restaurant_menu(RESTAURANT_MENU)
```

### Cart Summary
```python
from ai_companion.modules.cart import CartService

cart_service = CartService()
summary = cart_service.get_cart_summary(cart)
# Returns formatted text with items and totals
```

### Order Status Update
```python
from ai_companion.interfaces.whatsapp.interactive_components import create_order_status_message

status_component = create_order_status_message(
    order_id="ORD-12345678",
    status="out_for_delivery",
    message="🚗 Your driver Sarah is 5 minutes away!"
)
```

## 🆘 Need Help?

- **Full Guide**: [SHOPPING_CART_GUIDE.md](SHOPPING_CART_GUIDE.md)
- **Meta API Docs**: [meta-api.yaml](meta-api.yaml)
- **Interactive Components**: [interactive_components.py](../src/ai_companion/interfaces/whatsapp/interactive_components.py)
- **Cart Service**: [cart_service.py](../src/ai_companion/modules/cart/cart_service.py)

---

**Built with ❤️ for Ava WhatsApp Agent**
