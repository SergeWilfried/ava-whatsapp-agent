# 🛒 Shopping Cart System Guide

This guide explains how to use and integrate the complete shopping cart system for Ava's WhatsApp restaurant ordering.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Integration Steps](#integration-steps)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Overview

The shopping cart system provides a complete e-commerce ordering flow through WhatsApp interactive components:

### Features

✅ **Interactive Menu Browsing** - Scrollable menu with categories
✅ **Item Customization** - Size selection and extras/toppings
✅ **Shopping Cart Management** - Add, view, clear items
✅ **Order Checkout** - Delivery method and payment selection
✅ **Order Details Message** - WhatsApp native payment-ready order summary
✅ **Order Tracking** - Real-time status updates
✅ **Persistent Storage** - Orders saved to disk
✅ **Discount Application** - Automatic special offers

### Components

1. **Data Models** (`modules/cart/models.py`)
   - `CartItem`, `CartItemCustomization`
   - `ShoppingCart`, `Order`
   - Enums: `OrderStatus`, `OrderStage`, `DeliveryMethod`, `PaymentMethod`

2. **Cart Service** (`modules/cart/cart_service.py`)
   - Cart operations (add, remove, update)
   - Menu item lookup
   - Order creation and management
   - Discount application
   - Order persistence

3. **Interactive Components** (`interfaces/whatsapp/interactive_components.py`)
   - Button builders (size selection, cart actions, delivery/payment)
   - List builders (menu, extras, payment methods)
   - Order details message (payment-ready)
   - Order status message (tracking)

4. **Graph Nodes** (`graph/cart_nodes.py`)
   - `add_to_cart_node` - Add items with customization
   - `view_cart_node` - Display cart contents
   - `checkout_node` - Begin checkout flow
   - `handle_delivery_method_node` - Process delivery selection
   - `handle_payment_method_node` - Process payment and show order details
   - `confirm_order_node` - Finalize order

5. **Interaction Handler** (`interfaces/whatsapp/cart_handler.py`)
   - Parse button/list replies
   - Route to appropriate nodes
   - Convert interactions to natural language

## Architecture

```
User Interaction → WhatsApp Webhook → Cart Handler → Graph Nodes → Cart Service
                                                            ↓
                                              Interactive Components
                                                            ↓
                                              WhatsApp Response
```

### Order Flow

```
1. Browse Menu (List Message)
   ↓
2. Select Item
   ↓
3. Customize (Size + Extras) - Button & List Messages
   ↓
4. View Cart - Button Message
   ↓
5. Checkout
   ↓
6. Select Delivery Method - Button Message
   ↓
7. Select Payment Method - List Message
   ↓
8. Review Order Details - Order Details Message (Payment Ready)
   ↓
9. Confirm Order
   ↓
10. Order Tracking - Order Status Message
```

## Integration Steps

### Step 1: Update Webhook Handler

Modify `webhook_endpoint.py` to route cart interactions:

```python
from ai_companion.interfaces.whatsapp.cart_handler import process_cart_interaction
from ai_companion.graph.cart_nodes import (
    add_to_cart_node,
    view_cart_node,
    checkout_node,
    handle_delivery_method_node,
    handle_payment_method_node,
    confirm_order_node,
)

# In your webhook handler:
if message["type"] == "interactive":
    interactive_data = message.get("interactive", {})
    interaction_type = interactive_data.get("type")  # "button_reply" or "list_reply"

    # Get current state
    current_state_dict = output_state.values

    # Process interaction
    node_name, state_updates, text_repr = process_cart_interaction(
        interaction_type,
        interactive_data,
        current_state_dict
    )

    # Update state with any changes
    for key, value in state_updates.items():
        current_state_dict[key] = value

    # Route to appropriate node
    if node_name == "add_to_cart":
        result = await add_to_cart_node(current_state_dict)
    elif node_name == "view_cart":
        result = await view_cart_node(current_state_dict)
    elif node_name == "checkout":
        result = await checkout_node(current_state_dict)
    # ... etc

    # Use text representation for conversation context
    content = text_repr
```

### Step 2: Add Cart Nodes to Graph

In `graph/graph.py`, add cart nodes:

```python
from ai_companion.graph.cart_nodes import (
    add_to_cart_node,
    view_cart_node,
    checkout_node,
    clear_cart_node,
    handle_size_selection_node,
    handle_extras_selection_node,
    handle_delivery_method_node,
    handle_payment_method_node,
    confirm_order_node,
)

# Add nodes to graph builder
graph_builder.add_node("add_to_cart", add_to_cart_node)
graph_builder.add_node("view_cart", view_cart_node)
graph_builder.add_node("checkout", checkout_node)
graph_builder.add_node("clear_cart", clear_cart_node)
graph_builder.add_node("handle_size", handle_size_selection_node)
graph_builder.add_node("handle_extras", handle_extras_selection_node)
graph_builder.add_node("handle_delivery_method", handle_delivery_method_node)
graph_builder.add_node("handle_payment_method", handle_payment_method_node)
graph_builder.add_node("confirm_order", confirm_order_node)
```

### Step 3: Initialize State

Ensure state is initialized with cart fields:

```python
initial_state = {
    "messages": [],
    "shopping_cart": None,
    "order_stage": "browsing",
    "current_item": None,
    "pending_customization": None,
    "delivery_method": None,
    "payment_method": None,
    "active_order_id": None,
}
```

### Step 4: Create Data Directory

```bash
mkdir -p data/carts/orders
```

## Usage Examples

### Example 1: Simple Order Flow

```python
from ai_companion.modules.cart import CartService, DeliveryMethod, PaymentMethod

# Initialize
cart_service = CartService()
cart = cart_service.create_cart()

# Add items
cart_service.add_item_to_cart(cart, "pizzas_0", quantity=1, size="large")
cart_service.add_item_to_cart(cart, "sides_0", quantity=2)

# View cart
print(cart_service.get_cart_summary(cart))

# Create order
order = cart_service.create_order_from_cart(
    cart,
    delivery_method=DeliveryMethod.DELIVERY,
    payment_method=PaymentMethod.CREDIT_CARD,
    customer_name="John Doe",
    delivery_address="123 Main St",
    delivery_phone="+1234567890"
)

# Confirm and save
cart_service.confirm_order(order)
cart_service.save_order(order)

print(f"Order {order.order_id} created: ${order.total:.2f}")
```

### Example 2: Creating Interactive Components

```python
from ai_companion.interfaces.whatsapp.interactive_components import *

# Menu list
menu_component = create_menu_list_from_restaurant_menu(RESTAURANT_MENU)

# Size selection
size_buttons = create_size_selection_buttons("Margherita Pizza", 12.99)

# Cart view
cart_buttons = create_cart_view_buttons(cart_total=25.50, item_count=3)

# Delivery method
delivery_buttons = create_delivery_method_buttons()

# Order details (payment-ready)
order_details = create_order_details_message({
    "order_id": "ORD-12345678",
    "items": [{"menu_item_id": "pizzas_0", "name": "Margherita", "base_price": 12.99, "quantity": 1, "item_total": 12.99}],
    "subtotal": 12.99,
    "tax_amount": 1.04,
    "tax_rate": 0.08,
    "delivery_fee": 0.00,
    "discount": 0.00,
    "total": 14.03,
    "estimated_time": "30-45 minutes"
})
```

### Example 3: Handling Interactive Replies

```python
from ai_companion.interfaces.whatsapp.cart_handler import CartInteractionHandler

handler = CartInteractionHandler()

# Check if interaction is cart-related
is_cart = handler.is_cart_interaction("pizzas_0")  # True
is_cart = handler.is_cart_interaction("random_text")  # False

# Parse interaction
action_type, interaction_id, title = handler.parse_interaction(
    "list_reply",
    {"list_reply": {"id": "pizzas_0", "title": "🍕 Margherita"}}
)
# Returns: ("list", "pizzas_0", "🍕 Margherita")

# Determine action
node_name, state_updates = handler.determine_cart_action("pizzas_0")
# Returns: ("add_to_cart", {"current_item": {"menu_item_id": "pizzas_0"}, ...})

# Create text representation
text = handler.create_text_representation("list", "pizzas_0", "Margherita")
# Returns: "I'd like to order the Margherita"
```

## API Reference

### CartService

#### Methods

- `create_cart() -> ShoppingCart` - Create new cart
- `find_menu_item(menu_item_id: str) -> Optional[Dict]` - Lookup menu item
- `add_item_to_cart(cart, menu_item_id, quantity, size, extras, special_instructions) -> Tuple[bool, str, CartItem]` - Add item with customizations
- `remove_item_from_cart(cart, cart_item_id) -> Tuple[bool, str]` - Remove item
- `update_item_quantity(cart, cart_item_id, quantity) -> Tuple[bool, str]` - Update quantity
- `get_cart_summary(cart) -> str` - Generate text summary
- `create_order_from_cart(cart, delivery_method, **kwargs) -> Order` - Create order
- `confirm_order(order) -> None` - Mark order confirmed
- `save_order(order) -> bool` - Persist to disk
- `load_order(order_id) -> Optional[Order]` - Load from disk
- `get_order_status_message(order) -> str` - Generate status text

#### Customization Pricing

```python
SIZE_MULTIPLIERS = {
    "small": 0.8,
    "medium": 1.0,
    "large": 1.3,
    "x-large": 1.5
}

EXTRAS_PRICING = {
    "extra_cheese": 2.00,
    "mushrooms": 1.50,
    "olives": 1.00,
    "pepperoni": 2.50,
    "bacon": 2.50,
    "chicken": 3.00,
    "extra_sauce": 0.00,  # Free
    "gluten_free": 3.00,
    "vegan_cheese": 2.50,
}
```

### Interactive Components

All functions return a `Dict` ready for WhatsApp API:

- `create_button_component(body_text, buttons, header_text, footer_text)` - Generic button builder
- `create_list_component(body_text, sections, button_text, header_text, footer_text)` - Generic list builder
- `create_menu_list_from_restaurant_menu(restaurant_menu)` - Full menu
- `create_item_added_buttons(item_name, cart_total, item_count)` - Post-add actions
- `create_cart_view_buttons(cart_total, item_count)` - Cart management
- `create_size_selection_buttons(item_name, base_price)` - Size picker
- `create_extras_list(category)` - Extras/toppings picker
- `create_delivery_method_buttons()` - Delivery options
- `create_payment_method_list()` - Payment options
- `create_order_details_message(order_data)` - Payment-ready order summary
- `create_order_status_message(order_id, status, message)` - Order tracking

### State Fields

```python
shopping_cart: Optional[Dict]  # Serialized ShoppingCart
order_stage: str  # "browsing", "selecting", "customizing", "reviewing_cart", "checkout", "payment", "confirmed"
current_item: Optional[Dict]  # Item being customized
pending_customization: Optional[Dict]  # {"size": "large", "extras": ["extra_cheese"]}
delivery_method: Optional[str]  # "delivery", "pickup", "dine_in"
payment_method: Optional[str]  # "credit_card", "debit_card", "mobile_payment", "cash"
active_order_id: Optional[str]  # Order reference ID
```

## Testing

### Manual Testing Flow

1. **Start Conversation**
   ```
   User: "Hi"
   Bot: Sends welcome buttons [Order Now, View Menu, Track Order]
   ```

2. **Browse Menu**
   ```
   User: Taps "View Menu"
   Bot: Sends menu list with categories (Pizzas, Burgers, Sides, etc.)
   ```

3. **Select Item**
   ```
   User: Taps "🍕 Margherita - $12.99"
   Bot: Sends size selection buttons [Small $10.39, Medium $12.99, Large $16.89]
   ```

4. **Choose Size**
   ```
   User: Taps "Large $16.89"
   Bot: Sends extras list (Cheese & Protein, Veggies, Special Options)
   ```

5. **Add Extras**
   ```
   User: Taps "Extra Cheese +$2.00"
   Bot: "Added Large Margherita Pizza with extra cheese to cart ($18.89)"
        Sends buttons [➕ Add More, 🛒 View Cart, ✅ Checkout]
   ```

6. **View Cart**
   ```
   User: Taps "View Cart"
   Bot: Shows cart summary with buttons [✅ Checkout, ➕ Add More, 🗑️ Clear Cart]
   ```

7. **Checkout**
   ```
   User: Taps "Checkout"
   Bot: Sends delivery method buttons [🚗 Delivery, 🏃 Pickup, 🍽️ Dine-In]
   ```

8. **Choose Delivery**
   ```
   User: Taps "Delivery"
   Bot: Sends payment method list [Credit Card, Debit Card, Mobile Payment, Cash]
   ```

9. **Choose Payment**
   ```
   User: Taps "Credit Card"
   Bot: Sends Order Details interactive message (payment-ready)
        Shows items, subtotal, tax, delivery fee, total
   ```

10. **Order Confirmed**
    ```
    Bot: Sends Order Status message
         "✅ Order confirmed! Ready by 7:30 PM"
    ```

### Unit Testing

```python
import pytest
from ai_companion.modules.cart import CartService, ShoppingCart

def test_add_item_to_cart():
    cart_service = CartService()
    cart = cart_service.create_cart()

    success, message, item = cart_service.add_item_to_cart(
        cart, "pizzas_0", quantity=1
    )

    assert success
    assert cart.item_count == 1
    assert cart.subtotal > 0

def test_size_customization():
    cart_service = CartService()
    cart = cart_service.create_cart()

    # Add large pizza
    success, _, _ = cart_service.add_item_to_cart(
        cart, "pizzas_0", quantity=1, size="large"
    )

    assert success
    # Large should be 1.3x base price
    assert cart.items[0].base_price == 12.99 * 1.3

def test_extras_pricing():
    cart_service = CartService()
    cart = cart_service.create_cart()

    success, _, item = cart_service.add_item_to_cart(
        cart, "pizzas_0", quantity=1, extras=["extra_cheese", "mushrooms"]
    )

    assert success
    # Should add $2.00 + $1.50 = $3.50
    assert item.customization.price_adjustment == 3.50
```

## Troubleshooting

### Issue: Interactive components not appearing

**Solution**: Check that you're sending the correct message type:
```python
# Send interactive message
json_data = {
    "messaging_product": "whatsapp",
    "to": from_number,
    "type": "interactive",  # Important!
    "interactive": interactive_component
}
```

### Issue: Order Details message fails

**Possible causes**:
1. Payment configuration not set up in Meta Business Manager
2. Incorrect amount formatting (must use offset: 100 for cents)
3. Missing required fields (reference_id, payment_type, currency)

**Solution**: Verify all fields are present and amounts are in cents:
```python
"total_amount": {"value": int(total * 100), "offset": 100}  # $25.99 → 2599
```

### Issue: Cart state not persisting between messages

**Solution**: Ensure you're using the correct thread_id:
```python
config = {"configurable": {"thread_id": f"{business_subdomain}:{from_number}"}}
```

### Issue: Interactive replies not routing correctly

**Solution**: Add logging to see what IDs are being received:
```python
logger.info(f"Received interaction: type={interaction_type}, id={interaction_id}")
```

## Next Steps

1. **Integrate Payment Provider** - Connect Stripe, Razorpay, or other payment service
2. **Add Order Tracking** - Real-time status updates via cron job or webhook
3. **Implement Inventory** - Track item availability
4. **Add Recommendations** - Suggest items based on order history
5. **Multi-language Support** - Translate components
6. **Analytics Dashboard** - Track conversion rates, popular items
7. **Loyalty Program** - Reward frequent customers

## Support

For issues or questions:
- Check the [main README](../README.md)
- Review the [Meta API documentation](../docs/meta-api.yaml)
- Open an issue on GitHub
