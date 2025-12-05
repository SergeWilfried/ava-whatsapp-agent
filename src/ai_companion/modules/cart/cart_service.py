"""Cart management service for handling shopping cart operations."""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from ai_companion.core.schedules import RESTAURANT_MENU, RESTAURANT_INFO, SPECIAL_OFFERS
from ai_companion.modules.cart.models import (
    CartItem,
    CartItemCustomization,
    ShoppingCart,
    Order,
    OrderStatus,
    DeliveryMethod,
    PaymentMethod,
)

logger = logging.getLogger(__name__)


class CartService:
    """Service for managing shopping carts and orders."""

    # Customization pricing
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
        "extra_toppings": 1.50,
    }

    def __init__(self, cart_storage_path: str = "data/carts"):
        """Initialize cart service with storage path."""
        self.storage_path = Path(cart_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.orders_path = self.storage_path / "orders"
        self.orders_path.mkdir(exist_ok=True)

    def create_cart(self) -> ShoppingCart:
        """Create a new shopping cart."""
        return ShoppingCart()

    def find_menu_item(self, menu_item_id: str) -> Optional[Dict]:
        """Find menu item by ID in the restaurant menu.

        Args:
            menu_item_id: ID in format "category_index" (e.g., "pizzas_0")

        Returns:
            Menu item dict or None if not found
        """
        try:
            parts = menu_item_id.split("_")
            if len(parts) >= 2:
                category = parts[0]
                index = int(parts[1])

                if category in RESTAURANT_MENU and index < len(RESTAURANT_MENU[category]):
                    item = RESTAURANT_MENU[category][index]
                    return {
                        "id": menu_item_id,
                        "name": item["name"],
                        "price": item["price"],
                        "description": item["description"],
                        "category": category
                    }
        except (ValueError, IndexError, KeyError) as e:
            logger.error(f"Error finding menu item {menu_item_id}: {e}")

        return None

    def add_item_to_cart(
        self,
        cart: ShoppingCart,
        menu_item_id: str,
        quantity: int = 1,
        size: Optional[str] = None,
        extras: Optional[List[str]] = None,
        special_instructions: Optional[str] = None
    ) -> Tuple[bool, str, Optional[CartItem]]:
        """Add item to cart with optional customizations.

        Args:
            cart: Shopping cart to add item to
            menu_item_id: Menu item ID
            quantity: Quantity to add
            size: Size selection (small, medium, large)
            extras: List of extra item IDs
            special_instructions: Special preparation instructions

        Returns:
            Tuple of (success, message, cart_item)
        """
        # Find menu item
        menu_item = self.find_menu_item(menu_item_id)
        if not menu_item:
            return False, f"Menu item '{menu_item_id}' not found", None

        # Calculate price adjustments
        base_price = menu_item["price"]
        price_adjustment = 0.0

        # Apply size adjustment
        if size and size.lower() in self.SIZE_MULTIPLIERS:
            base_price = menu_item["price"] * self.SIZE_MULTIPLIERS[size.lower()]

        # Apply extras pricing
        if extras:
            for extra in extras:
                price_adjustment += self.EXTRAS_PRICING.get(extra, 0.0)

        # Create customization if any provided
        customization = None
        if size or extras or special_instructions:
            customization = CartItemCustomization(
                size=size,
                extras=extras or [],
                special_instructions=special_instructions,
                price_adjustment=price_adjustment
            )

        # Create cart item
        cart_item = CartItem(
            id=str(uuid4()),
            menu_item_id=menu_item_id,
            name=menu_item["name"],
            base_price=base_price,
            quantity=quantity,
            customization=customization
        )

        # Add to cart
        cart.add_item(cart_item)

        # Build success message
        size_text = f" ({size})" if size else ""
        extras_text = f" with {', '.join(extras)}" if extras else ""
        message = f"Added {quantity}x {menu_item['name']}{size_text}{extras_text} to cart (${cart_item.item_total:.2f})"

        return True, message, cart_item

    def remove_item_from_cart(self, cart: ShoppingCart, cart_item_id: str) -> Tuple[bool, str]:
        """Remove item from cart.

        Returns:
            Tuple of (success, message)
        """
        if cart.remove_item(cart_item_id):
            return True, "Item removed from cart"
        return False, "Item not found in cart"

    def update_item_quantity(
        self,
        cart: ShoppingCart,
        cart_item_id: str,
        quantity: int
    ) -> Tuple[bool, str]:
        """Update quantity of item in cart.

        Returns:
            Tuple of (success, message)
        """
        if quantity <= 0:
            return self.remove_item_from_cart(cart, cart_item_id)

        if cart.update_quantity(cart_item_id, quantity):
            return True, f"Quantity updated to {quantity}"
        return False, "Item not found in cart"

    def get_cart_summary(self, cart: ShoppingCart) -> str:
        """Generate a text summary of the cart contents.

        Returns:
            Formatted cart summary string
        """
        if cart.is_empty:
            return "🛒 Votre panier est vide"

        lines = ["🛒 *Votre panier:*\n"]

        for item in cart.items:
            size_text = f" ({item.customization.size})" if item.customization and item.customization.size else ""
            extras_text = ""
            if item.customization and item.customization.extras:
                extras_text = f"\n   ↳ _Extras: {', '.join(item.customization.extras)}_"

            lines.append(
                f"• {item.quantity}x {item.name}{size_text} - ${item.item_total:.2f}{extras_text}"
            )

        lines.append(f"\n*Sous Total:* ${cart.subtotal:.2f}")
        lines.append(f"*Articles:* {cart.item_count}")

        return "\n".join(lines)

    def create_order_from_cart(
        self,
        cart: ShoppingCart,
        delivery_method: DeliveryMethod,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        delivery_address: Optional[str] = None,
        payment_method: Optional[PaymentMethod] = None,
        special_instructions: Optional[str] = None
    ) -> Order:
        """Create an order from a shopping cart.

        Args:
            cart: Shopping cart to convert to order
            delivery_method: How customer wants to receive order
            customer_name: Customer name
            customer_phone: Customer contact phone (required for all order types)
            delivery_address: Delivery address (required for delivery)
            payment_method: Payment method
            special_instructions: Order-level special instructions

        Returns:
            Created order
        """
        order = Order(
            cart=cart,
            delivery_method=delivery_method,
            payment_method=payment_method,
            delivery_address=delivery_address,
            customer_phone=customer_phone,
            customer_name=customer_name,
            special_instructions=special_instructions
        )

        # Calculate totals
        order.calculate_totals(
            tax_rate=RESTAURANT_INFO["tax_rate"],
            delivery_fee=RESTAURANT_INFO["delivery_fee"],
            free_delivery_minimum=RESTAURANT_INFO["free_delivery_minimum"]
        )

        # Apply any applicable discounts
        discount_info = self.apply_discounts(order)
        if discount_info:
            order.discount = discount_info["amount"]
            order.discount_description = discount_info["description"]

        return order

    def apply_discounts(self, order: Order) -> Optional[Dict]:
        """Apply applicable discounts to order.

        Returns:
            Dict with discount info or None
        """
        # Check for free delivery discount
        if order.subtotal >= RESTAURANT_INFO["free_delivery_minimum"] and order.delivery_fee > 0:
            return {
                "amount": RESTAURANT_INFO["delivery_fee"],
                "description": "Free delivery on orders over $25"
            }

        # Check day-of-week specials
        day_name = datetime.now().strftime("%A").lower()
        if day_name in SPECIAL_OFFERS["daily_specials"]:
            special = SPECIAL_OFFERS["daily_specials"][day_name]
            # Could implement more complex discount logic here
            logger.info(f"Today's special: {special}")

        return None

    def confirm_order(self, order: Order) -> None:
        """Mark order as confirmed and set timestamps."""
        order.status = OrderStatus.CONFIRMED
        order.confirmed_at = datetime.now()

        # Estimate ready time based on delivery method
        if order.delivery_method == DeliveryMethod.PICKUP:
            minutes = 20  # 15-20 minutes for pickup
        elif order.delivery_method == DeliveryMethod.DELIVERY:
            minutes = 40  # 30-45 minutes for delivery
        else:
            minutes = 25  # 20-30 minutes for dine-in

        order.estimated_ready_time = datetime.now() + timedelta(minutes=minutes)

    def save_order(self, order: Order) -> bool:
        """Persist order to storage.

        Args:
            order: Order to save

        Returns:
            Success status
        """
        try:
            order_file = self.orders_path / f"{order.order_id}.json"
            with open(order_file, "w") as f:
                json.dump(order.to_dict(), f, indent=2)
            logger.info(f"Saved order {order.order_id} to {order_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save order {order.order_id}: {e}")
            return False

    def load_order(self, order_id: str) -> Optional[Order]:
        """Load order from storage.

        Args:
            order_id: Order ID to load

        Returns:
            Order object or None if not found
        """
        try:
            order_file = self.orders_path / f"{order_id}.json"
            if not order_file.exists():
                return None

            with open(order_file, "r") as f:
                data = json.load(f)

            # Reconstruct order (simplified - would need full deserialization)
            logger.info(f"Loaded order {order_id}")
            return data  # Returns dict for now
        except Exception as e:
            logger.error(f"Failed to load order {order_id}: {e}")
            return None

    def get_order_status_message(self, order: Order) -> str:
        """Generate status message for order.

        Returns:
            Formatted status message
        """
        status_emoji = {
            OrderStatus.PENDING: "⏳",
            OrderStatus.CONFIRMED: "✅",
            OrderStatus.PREPARING: "👨‍🍳",
            OrderStatus.READY: "🎉",
            OrderStatus.OUT_FOR_DELIVERY: "🚗",
            OrderStatus.DELIVERED: "✅",
            OrderStatus.PICKED_UP: "✅",
            OrderStatus.CANCELLED: "❌"
        }

        emoji = status_emoji.get(order.status, "📦")

        if order.status == OrderStatus.CONFIRMED:
            time_str = order.estimated_ready_time.strftime("%I:%M %p") if order.estimated_ready_time else "soon"
            return f"{emoji} Order confirmed! Ready by {time_str}"
        elif order.status == OrderStatus.PREPARING:
            return f"{emoji} Your order is being prepared..."
        elif order.status == OrderStatus.READY:
            if order.delivery_method == DeliveryMethod.PICKUP:
                return f"{emoji} Your order is ready for pickup!"
            return f"{emoji} Your order is ready!"
        elif order.status == OrderStatus.OUT_FOR_DELIVERY:
            return f"{emoji} Your order is on the way!"
        elif order.status == OrderStatus.DELIVERED:
            return f"{emoji} Order delivered! Enjoy your meal!"
        elif order.status == OrderStatus.PICKED_UP:
            return f"{emoji} Order picked up! Enjoy your meal!"
        else:
            return f"{emoji} Order status: {order.status.value}"


# Singleton instance
_cart_service: Optional[CartService] = None


def get_cart_service() -> CartService:
    """Get or create cart service singleton."""
    global _cart_service
    if _cart_service is None:
        _cart_service = CartService()
    return _cart_service
