# 🛒 Shopping Cart Module

Complete e-commerce cart and order management system for WhatsApp restaurant ordering.

## Overview

This module provides a full-featured shopping cart system with:

- Cart management (add, remove, update items)
- Item customization (size, extras, special instructions)
- Order creation and tracking
- Automatic pricing calculations (tax, delivery fee, discounts)
- Order persistence

## Quick Example

```python
from ai_companion.modules.cart import CartService, DeliveryMethod, PaymentMethod

# Initialize service
cart_service = CartService()

# Create cart
cart = cart_service.create_cart()

# Add items
cart_service.add_item_to_cart(
    cart,
    menu_item_id="pizzas_0",
    quantity=1,
    size="large",
    extras=["extra_cheese", "mushrooms"]
)

# View cart
print(cart_service.get_cart_summary(cart))
# Output:
# 🛒 *Your Cart:*
#
# • 1x Margherita Pizza (large) - $18.89
#    ↳ _Extras: extra_cheese, mushrooms_
#
# *Subtotal:* $18.89
# *Items:* 1

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

print(f"Order {order.order_id}: ${order.total:.2f}")
# Output: Order ORD-A1B2C3D4: $22.95
```

## Module Structure

```
cart/
├── __init__.py          # Module exports
├── models.py            # Data models
├── cart_service.py      # Business logic
└── README.md            # This file
```

## Data Models

### CartItem

Represents a single item in the cart with optional customizations.

```python
@dataclass
class CartItem:
    id: str                                    # Unique cart item ID
    menu_item_id: str                          # Reference to menu item
    name: str                                  # Item name
    base_price: float                          # Price (after size adjustment)
    quantity: int = 1                          # Quantity
    customization: Optional[CartItemCustomization] = None

    @property
    def item_total(self) -> float:
        """Total price including customizations"""
```

### CartItemCustomization

```python
@dataclass
class CartItemCustomization:
    size: Optional[str] = None                 # "small", "medium", "large"
    extras: List[str] = []                     # ["extra_cheese", "mushrooms"]
    special_instructions: Optional[str] = None # "No onions please"
    price_adjustment: float = 0.0              # Additional cost for extras
```

### ShoppingCart

```python
@dataclass
class ShoppingCart:
    cart_id: str
    items: List[CartItem] = []
    created_at: datetime
    updated_at: datetime

    @property
    def subtotal(self) -> float: ...
    @property
    def item_count(self) -> int: ...
    @property
    def is_empty(self) -> bool: ...

    def add_item(self, item: CartItem) -> None: ...
    def remove_item(self, cart_item_id: str) -> bool: ...
    def update_quantity(self, cart_item_id: str, quantity: int) -> bool: ...
    def clear(self) -> None: ...
```

### Order

Complete order with pricing and delivery information.

```python
@dataclass
class Order:
    order_id: str                              # "ORD-A1B2C3D4"
    cart: ShoppingCart
    status: OrderStatus                        # PENDING, CONFIRMED, etc.
    delivery_method: Optional[DeliveryMethod]  # DELIVERY, PICKUP, DINE_IN
    payment_method: Optional[PaymentMethod]

    # Delivery info
    delivery_address: Optional[str]
    delivery_phone: Optional[str]
    customer_name: Optional[str]

    # Pricing
    subtotal: float
    tax_rate: float = 0.08
    delivery_fee: float = 0.0
    discount: float = 0.0
    discount_description: Optional[str]

    @property
    def tax_amount(self) -> float: ...
    @property
    def total(self) -> float: ...
```

### Enums

```python
class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    PICKED_UP = "picked_up"
    CANCELLED = "cancelled"

class OrderStage(Enum):
    BROWSING = "browsing"
    SELECTING = "selecting"
    CUSTOMIZING = "customizing"
    REVIEWING_CART = "reviewing_cart"
    CHECKOUT = "checkout"
    PAYMENT = "payment"
    CONFIRMED = "confirmed"

class DeliveryMethod(Enum):
    DELIVERY = "delivery"
    PICKUP = "pickup"
    DINE_IN = "dine_in"

class PaymentMethod(Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    MOBILE_PAYMENT = "mobile_payment"
    ONLINE = "online"
```

## CartService API

### Cart Operations

#### `create_cart() -> ShoppingCart`

Create a new empty shopping cart.

```python
cart = cart_service.create_cart()
```

#### `find_menu_item(menu_item_id: str) -> Optional[Dict]`

Find menu item by ID.

```python
item = cart_service.find_menu_item("pizzas_0")
# Returns: {"id": "pizzas_0", "name": "Margherita", "price": 12.99, ...}
```

Menu item IDs follow the pattern: `{category}_{index}`
- `pizzas_0` → First pizza in menu
- `burgers_2` → Third burger in menu

#### `add_item_to_cart(...) -> Tuple[bool, str, Optional[CartItem]]`

Add item to cart with optional customizations.

```python
success, message, cart_item = cart_service.add_item_to_cart(
    cart,
    menu_item_id="pizzas_0",
    quantity=2,
    size="large",                              # Optional
    extras=["extra_cheese", "mushrooms"],      # Optional
    special_instructions="Extra crispy please" # Optional
)

if success:
    print(message)  # "Added 2x Margherita Pizza (large) with extra cheese, mushrooms to cart ($37.78)"
```

**Parameters:**
- `cart`: ShoppingCart instance
- `menu_item_id`: ID from menu (e.g., "pizzas_0")
- `quantity`: Number of items (default: 1)
- `size`: "small", "medium", "large", "x-large" (default: None)
- `extras`: List of extra IDs (default: None)
- `special_instructions`: Text instructions (default: None)

**Returns:**
- `success`: Boolean indicating success
- `message`: Human-readable message
- `cart_item`: Created CartItem or None

#### `remove_item_from_cart(cart, cart_item_id) -> Tuple[bool, str]`

Remove item from cart.

```python
success, message = cart_service.remove_item_from_cart(cart, cart_item.id)
```

#### `update_item_quantity(cart, cart_item_id, quantity) -> Tuple[bool, str]`

Update item quantity. Setting quantity to 0 removes the item.

```python
success, message = cart_service.update_item_quantity(cart, cart_item.id, 3)
```

#### `get_cart_summary(cart) -> str`

Generate formatted text summary of cart.

```python
summary = cart_service.get_cart_summary(cart)
print(summary)
# Output:
# 🛒 *Your Cart:*
#
# • 1x Margherita Pizza (large) - $16.89
#    ↳ _Extras: extra cheese, mushrooms_
# • 2x French Fries - $7.98
#
# *Subtotal:* $24.87
# *Items:* 3
```

### Order Operations

#### `create_order_from_cart(...) -> Order`

Create an order from the shopping cart.

```python
order = cart_service.create_order_from_cart(
    cart,
    delivery_method=DeliveryMethod.DELIVERY,
    customer_name="John Doe",
    delivery_address="123 Main St, Apt 4B",
    delivery_phone="+1234567890",
    payment_method=PaymentMethod.CREDIT_CARD,
    special_instructions="Ring doorbell twice"
)
```

**Parameters:**
- `cart`: ShoppingCart to convert
- `delivery_method`: DeliveryMethod enum
- `customer_name`: Customer name (optional)
- `delivery_address`: Address (required for delivery)
- `delivery_phone`: Contact phone (optional)
- `payment_method`: PaymentMethod enum (optional)
- `special_instructions`: Order notes (optional)

**Automatic Calculations:**
- Subtotal from cart items
- Tax (based on `RESTAURANT_INFO["tax_rate"]`)
- Delivery fee (free if subtotal >= free_delivery_minimum)
- Discounts (from `apply_discounts()`)

#### `confirm_order(order) -> None`

Mark order as confirmed and set estimated ready time.

```python
cart_service.confirm_order(order)
# Sets order.status = CONFIRMED
# Sets order.confirmed_at = now
# Sets order.estimated_ready_time = now + 20-45 minutes (based on delivery method)
```

#### `save_order(order) -> bool`

Persist order to disk at `data/carts/orders/{order_id}.json`.

```python
success = cart_service.save_order(order)
```

#### `load_order(order_id) -> Optional[Order]`

Load order from disk.

```python
order_data = cart_service.load_order("ORD-A1B2C3D4")
```

#### `get_order_status_message(order) -> str`

Generate human-readable status message.

```python
message = cart_service.get_order_status_message(order)
print(message)
# Output: "✅ Order confirmed! Ready by 7:30 PM"
```

### Pricing Configuration

#### Size Multipliers

```python
SIZE_MULTIPLIERS = {
    "small": 0.8,    # 80% of base price
    "medium": 1.0,   # 100% (base price)
    "large": 1.3,    # 130%
    "x-large": 1.5,  # 150%
}
```

Example:
- Medium Margherita: $12.99
- Small Margherita: $12.99 × 0.8 = $10.39
- Large Margherita: $12.99 × 1.3 = $16.89

#### Extras Pricing

```python
EXTRAS_PRICING = {
    "extra_cheese": 2.00,
    "mushrooms": 1.50,
    "olives": 1.00,
    "pepperoni": 2.50,
    "bacon": 2.50,
    "chicken": 3.00,
    "extra_sauce": 0.00,     # Free
    "gluten_free": 3.00,
    "vegan_cheese": 2.50,
    "extra_toppings": 1.50,
}
```

Example:
- Large Margherita: $16.89
- + Extra Cheese: +$2.00
- + Mushrooms: +$1.50
- **Total**: $20.39

## Usage Examples

### Example 1: Simple Order

```python
cart_service = CartService()
cart = cart_service.create_cart()

# Add basic item
cart_service.add_item_to_cart(cart, "drinks_0", quantity=2)

# Create and save order
order = cart_service.create_order_from_cart(
    cart,
    delivery_method=DeliveryMethod.PICKUP,
    customer_name="Jane Smith"
)
cart_service.confirm_order(order)
cart_service.save_order(order)
```

### Example 2: Customized Order

```python
cart_service = CartService()
cart = cart_service.create_cart()

# Add customized pizza
cart_service.add_item_to_cart(
    cart,
    "pizzas_0",
    quantity=1,
    size="large",
    extras=["extra_cheese", "pepperoni", "mushrooms"],
    special_instructions="Well done, please"
)

# Add sides
cart_service.add_item_to_cart(cart, "sides_0", quantity=1)  # Fries

# View cart
print(cart_service.get_cart_summary(cart))

# Create order with delivery
order = cart_service.create_order_from_cart(
    cart,
    delivery_method=DeliveryMethod.DELIVERY,
    customer_name="Bob Johnson",
    delivery_address="456 Oak Ave",
    delivery_phone="+1555123456",
    payment_method=PaymentMethod.CREDIT_CARD
)

cart_service.confirm_order(order)
print(f"Order total: ${order.total:.2f}")
print(f"Ready by: {order.estimated_ready_time.strftime('%I:%M %p')}")
```

### Example 3: Cart Management

```python
cart_service = CartService()
cart = cart_service.create_cart()

# Add items
success, _, item1 = cart_service.add_item_to_cart(cart, "pizzas_0")
success, _, item2 = cart_service.add_item_to_cart(cart, "burgers_1", quantity=2)

print(f"Cart has {cart.item_count} items, total: ${cart.subtotal:.2f}")

# Update quantity
cart_service.update_item_quantity(cart, item2.id, 3)

# Remove item
cart_service.remove_item_from_cart(cart, item1.id)

# Clear cart
cart.clear()
print(f"Cart empty: {cart.is_empty}")  # True
```

## Integration with Graph Nodes

The cart service is used by graph nodes in `graph/cart_nodes.py`:

```python
from ai_companion.modules.cart import CartService

async def add_to_cart_node(state: AICompanionState) -> Dict:
    cart_service = CartService()
    cart = get_or_create_cart(state)

    # Add item from state
    menu_item_id = state["current_item"]["menu_item_id"]
    success, message, cart_item = cart_service.add_item_to_cart(
        cart, menu_item_id, quantity=1
    )

    return {
        "messages": AIMessage(content=message),
        "shopping_cart": cart.to_dict()
    }
```

## Storage

Orders are saved as JSON files in `data/carts/orders/`:

```json
{
  "order_id": "ORD-A1B2C3D4",
  "status": "confirmed",
  "cart": {
    "cart_id": "...",
    "items": [
      {
        "id": "...",
        "menu_item_id": "pizzas_0",
        "name": "Margherita Pizza",
        "base_price": 16.89,
        "quantity": 1,
        "item_total": 20.39,
        "customization": {
          "size": "large",
          "extras": ["extra_cheese", "mushrooms"],
          "special_instructions": null,
          "price_adjustment": 3.50
        }
      }
    ],
    "subtotal": 20.39,
    "item_count": 1
  },
  "delivery_method": "delivery",
  "payment_method": "credit_card",
  "delivery_address": "123 Main St",
  "customer_name": "John Doe",
  "subtotal": 20.39,
  "tax_rate": 0.08,
  "tax_amount": 1.63,
  "delivery_fee": 0.00,
  "discount": 0.00,
  "total": 22.02,
  "created_at": "2025-12-02T15:30:00",
  "confirmed_at": "2025-12-02T15:32:00"
}
```

## Testing

```python
import pytest
from ai_companion.modules.cart import CartService

def test_cart_creation():
    service = CartService()
    cart = service.create_cart()
    assert cart.is_empty
    assert cart.subtotal == 0

def test_add_item():
    service = CartService()
    cart = service.create_cart()

    success, message, item = service.add_item_to_cart(
        cart, "pizzas_0", quantity=1
    )

    assert success
    assert cart.item_count == 1
    assert item.name == "Margherita Pizza"

def test_size_pricing():
    service = CartService()
    cart = service.create_cart()

    # Small pizza (80% of base)
    service.add_item_to_cart(cart, "pizzas_0", size="small")
    assert cart.items[0].base_price == 12.99 * 0.8

def test_extras_pricing():
    service = CartService()
    cart = service.create_cart()

    success, _, item = service.add_item_to_cart(
        cart, "pizzas_0",
        extras=["extra_cheese", "mushrooms"]
    )

    assert item.customization.price_adjustment == 3.50  # $2.00 + $1.50
```

## Next Steps

- **Inventory Management**: Track item availability
- **Order Tracking**: Real-time status updates
- **Payment Integration**: Stripe, Razorpay, etc.
- **Analytics**: Popular items, conversion rates
- **Recommendations**: Suggest items based on order history

## See Also

- [Shopping Cart Guide](../../../../docs/SHOPPING_CART_GUIDE.md)
- [Quick Start](../../../../docs/SHOPPING_CART_QUICKSTART.md)
- [Interactive Components](../../interfaces/whatsapp/interactive_components.py)
- [Cart Nodes](../../graph/cart_nodes.py)
