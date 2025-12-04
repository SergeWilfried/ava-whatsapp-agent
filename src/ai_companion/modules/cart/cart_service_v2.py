"""Updated Cart Service with API integration support.

This is the updated version of CartService that uses MenuAdapter for API integration.
To migrate, replace imports of CartService with this version.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
import asyncio

from ai_companion.core.schedules import RESTAURANT_INFO
from ai_companion.core.config import get_config
from ai_companion.services.menu_adapter import get_menu_adapter
from ai_companion.services.cartaai.order_service import get_order_service
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
    """Service for managing shopping carts and orders with API integration.

    This updated version uses MenuAdapter to seamlessly switch between
    mock data and CartaAI API based on feature flags.
    """

    # Fallback customization pricing (used if API doesn't provide pricing)
    SIZE_MULTIPLIERS = {
        "small": 0.8,
        "medium": 1.0,
        "large": 1.3,
        "x-large": 1.5,
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
        self.menu_adapter = get_menu_adapter()
        self.order_service = get_order_service()
        self.config = get_config()

    def create_cart(self) -> ShoppingCart:
        """Create a new shopping cart."""
        return ShoppingCart()

    async def find_menu_item(self, menu_item_id: str) -> Optional[Dict]:
        """Find menu item by ID (async version with API support).

        Args:
            menu_item_id: Menu item ID (legacy format or API ID)

        Returns:
            Menu item dict or None if not found
        """
        return await self.menu_adapter.find_menu_item(menu_item_id)

    def find_menu_item_sync(self, menu_item_id: str) -> Optional[Dict]:
        """Find menu item synchronously (for backward compatibility).

        Note: This creates an event loop if needed. Prefer async version.

        Args:
            menu_item_id: Menu item ID

        Returns:
            Menu item dict or None if not found
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.find_menu_item(menu_item_id))

    async def add_item_to_cart(
        self,
        cart: ShoppingCart,
        menu_item_id: str,
        quantity: int = 1,
        size: Optional[str] = None,
        extras: Optional[List[str]] = None,
        special_instructions: Optional[str] = None,
        presentation_id: Optional[str] = None,
        modifier_selections: Optional[Dict] = None,
    ) -> Tuple[bool, str, Optional[CartItem]]:
        """Add item to cart with optional customizations.

        Args:
            cart: Shopping cart to add item to
            menu_item_id: Menu item ID
            quantity: Quantity to add
            size: Size selection (legacy parameter)
            extras: List of extra item IDs (legacy parameter)
            special_instructions: Special preparation instructions
            presentation_id: API presentation ID (for API products)
            modifier_selections: API modifier selections (for API products)

        Returns:
            Tuple of (success, message, cart_item)
        """
        # Find menu item
        menu_item = await self.find_menu_item(menu_item_id)
        if not menu_item:
            return False, f"Menu item '{menu_item_id}' not found", None

        # Calculate price
        base_price, price_adjustment = self._calculate_price(
            menu_item, size, extras, presentation_id, modifier_selections
        )

        # Create customization if any provided
        customization = None
        if size or extras or special_instructions or presentation_id or modifier_selections:
            customization = CartItemCustomization(
                size=size or presentation_id,
                extras=extras or [],
                special_instructions=special_instructions,
                price_adjustment=price_adjustment,
            )

        # Create cart item
        cart_item = CartItem(
            id=str(uuid4()),
            menu_item_id=menu_item_id,
            name=menu_item["name"],
            base_price=base_price,
            quantity=quantity,
            customization=customization,
        )

        # Add to cart
        cart.add_item(cart_item)

        # Build success message
        size_text = f" ({size or presentation_id})" if (size or presentation_id) else ""
        extras_text = f" with {', '.join(extras)}" if extras else ""
        message = f"Added {quantity}x {menu_item['name']}{size_text}{extras_text} to cart (${cart_item.item_total:.2f})"

        return True, message, cart_item

    def _calculate_price(
        self,
        menu_item: Dict,
        size: Optional[str],
        extras: Optional[List[str]],
        presentation_id: Optional[str],
        modifier_selections: Optional[Dict],
    ) -> Tuple[float, float]:
        """Calculate item price with adjustments.

        Args:
            menu_item: Menu item dict
            size: Size selection (legacy)
            extras: Extras list (legacy)
            presentation_id: API presentation ID
            modifier_selections: API modifier selections

        Returns:
            Tuple of (base_price, price_adjustment)
        """
        base_price = menu_item["price"]
        price_adjustment = 0.0

        # Check if product has API presentations
        if menu_item.get("presentations"):
            # Use API presentation pricing
            if presentation_id:
                for pres in menu_item["presentations"]:
                    if pres.get("_id") == presentation_id:
                        base_price = pres.get("price", base_price)
                        break
            elif size:
                # Try to match size name to presentation
                for pres in menu_item["presentations"]:
                    if pres.get("name", "").lower() == size.lower():
                        base_price = pres.get("price", base_price)
                        break
        elif size and size.lower() in self.SIZE_MULTIPLIERS:
            # Use legacy size multipliers
            base_price = menu_item["price"] * self.SIZE_MULTIPLIERS[size.lower()]

        # Check if product has API modifiers
        if menu_item.get("modifiers") and modifier_selections:
            # Use API modifier pricing
            for modifier in menu_item["modifiers"]:
                modifier_id = modifier.get("_id")
                if modifier_id in modifier_selections:
                    selected_options = modifier_selections[modifier_id]
                    for option in modifier.get("options", []):
                        if option.get("_id") in selected_options:
                            price_adjustment += option.get("price", 0.0)
        elif extras:
            # Use legacy extras pricing
            for extra in extras:
                price_adjustment += self.EXTRAS_PRICING.get(extra, 0.0)

        return base_price, price_adjustment

    def remove_item_from_cart(
        self, cart: ShoppingCart, cart_item_id: str
    ) -> Tuple[bool, str]:
        """Remove item from cart.

        Returns:
            Tuple of (success, message)
        """
        if cart.remove_item(cart_item_id):
            return True, "Item removed from cart"
        return False, "Item not found in cart"

    def update_item_quantity(
        self, cart: ShoppingCart, cart_item_id: str, quantity: int
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
            return "🛒 Your cart is empty"

        lines = ["🛒 *Your Cart:*\n"]

        for item in cart.items:
            size_text = (
                f" ({item.customization.size})"
                if item.customization and item.customization.size
                else ""
            )
            extras_text = ""
            if item.customization and item.customization.extras:
                extras_text = (
                    f"\n   ↳ _Extras: {', '.join(item.customization.extras)}_"
                )

            lines.append(
                f"• {item.quantity}x {item.name}{size_text} - ${item.item_total:.2f}{extras_text}"
            )

        lines.append(f"\n*Subtotal:* ${cart.subtotal:.2f}")
        lines.append(f"*Items:* {cart.item_count}")

        return "\n".join(lines)

    async def create_order_from_cart(
        self,
        cart: ShoppingCart,
        delivery_method: DeliveryMethod,
        customer_name: Optional[str] = None,
        delivery_address: Optional[str] = None,
        delivery_phone: Optional[str] = None,
        payment_method: Optional[PaymentMethod] = None,
        special_instructions: Optional[str] = None,
        delivery_instructions: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
    ) -> Order:
        """Create an order from a shopping cart (async with API support).

        Args:
            cart: Shopping cart to convert to order
            delivery_method: How customer wants to receive order
            customer_name: Customer name
            delivery_address: Delivery address (required for delivery)
            delivery_phone: Contact phone
            payment_method: Payment method
            special_instructions: Order-level special instructions
            delivery_instructions: Delivery-specific instructions
            scheduled_time: Optional scheduled time for delivery/pickup

        Returns:
            Created order with API order ID (if enabled)
        """
        # Create base order
        order = Order(
            cart=cart,
            delivery_method=delivery_method,
            payment_method=payment_method or PaymentMethod.CASH,
            delivery_address=delivery_address,
            delivery_phone=delivery_phone,
            customer_name=customer_name,
            special_instructions=special_instructions,
        )

        # Get restaurant info
        restaurant_info = self.menu_adapter.get_restaurant_info()

        # Calculate totals
        order.calculate_totals(
            tax_rate=restaurant_info["tax_rate"],
            delivery_fee=restaurant_info["delivery_fee"],
            free_delivery_minimum=restaurant_info["free_delivery_minimum"],
        )

        # Try to create order via API if enabled
        if self.config.use_cartaai_api and self.config.orders_api_enabled:
            try:
                logger.info("Creating order via CartaAI API")

                api_response = await self.order_service.create_order(
                    cart=cart,
                    customer_name=customer_name or "Guest",
                    customer_phone=delivery_phone or "",
                    delivery_method=delivery_method,
                    payment_method=payment_method or PaymentMethod.CASH,
                    delivery_address=delivery_address,
                    delivery_instructions=delivery_instructions,
                    special_instructions=special_instructions,
                    scheduled_time=scheduled_time,
                )

                # Store API order details
                order_data = api_response.get("data", {})
                order.api_order_id = order_data.get("_id")
                order.api_order_number = order_data.get("orderNumber")

                # Update status from API
                api_status = order_data.get("status", "pending")
                order.status = self._map_api_status_to_internal(api_status)

                logger.info(
                    f"Order created via API: {order.api_order_number} "
                    f"(ID: {order.api_order_id})"
                )

            except Exception as e:
                logger.error(f"Failed to create order via API: {e}")
                logger.info("Falling back to local order creation")
                # Continue with local order (already created above)

        return order

    def _map_api_status_to_internal(self, api_status: str) -> OrderStatus:
        """Map API order status to internal OrderStatus enum.

        Args:
            api_status: Status from API (pending, confirmed, preparing, etc.)

        Returns:
            OrderStatus enum value
        """
        status_map = {
            "pending": OrderStatus.PENDING,
            "confirmed": OrderStatus.CONFIRMED,
            "preparing": OrderStatus.PREPARING,
            "ready": OrderStatus.READY,
            "dispatched": OrderStatus.OUT_FOR_DELIVERY,
            "delivered": OrderStatus.DELIVERED,
            "picked_up": OrderStatus.PICKED_UP,
            "cancelled": OrderStatus.CANCELLED,
        }

        return status_map.get(api_status.lower(), OrderStatus.PENDING)

    def create_order_from_cart_sync(
        self,
        cart: ShoppingCart,
        delivery_method: DeliveryMethod,
        customer_name: Optional[str] = None,
        delivery_address: Optional[str] = None,
        delivery_phone: Optional[str] = None,
        payment_method: Optional[PaymentMethod] = None,
        special_instructions: Optional[str] = None,
        delivery_instructions: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
    ) -> Order:
        """Create order synchronously (for backward compatibility).

        Note: This creates an event loop if needed. Prefer async version.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.create_order_from_cart(
                cart=cart,
                delivery_method=delivery_method,
                customer_name=customer_name,
                delivery_address=delivery_address,
                delivery_phone=delivery_phone,
                payment_method=payment_method,
                special_instructions=special_instructions,
                delivery_instructions=delivery_instructions,
                scheduled_time=scheduled_time,
            )
        )

    def confirm_order(self, order: Order) -> Order:
        """Confirm an order (set status and estimated time).

        Args:
            order: Order to confirm

        Returns:
            Updated order
        """
        order.status = OrderStatus.CONFIRMED
        order.confirmed_at = datetime.now()

        # Set estimated ready time (30-45 minutes from now)
        if order.delivery_method == DeliveryMethod.DELIVERY:
            order.estimated_ready_time = datetime.now() + timedelta(minutes=45)
        else:
            order.estimated_ready_time = datetime.now() + timedelta(minutes=30)

        return order

    def save_order(self, order: Order) -> str:
        """Save order to file storage.

        Args:
            order: Order to save

        Returns:
            File path where order was saved
        """
        order_file = self.orders_path / f"{order.order_id}.json"

        with open(order_file, "w") as f:
            json.dump(order.to_dict(), f, indent=2, default=str)

        logger.info(f"Order {order.order_id} saved to {order_file}")
        return str(order_file)

    def load_order(self, order_id: str) -> Optional[Order]:
        """Load order from file storage.

        Args:
            order_id: Order ID to load

        Returns:
            Order object or None if not found
        """
        order_file = self.orders_path / f"{order_id}.json"

        if not order_file.exists():
            return None

        try:
            with open(order_file, "r") as f:
                order_data = json.load(f)

            return Order.from_dict(order_data)

        except Exception as e:
            logger.error(f"Error loading order {order_id}: {e}")
            return None

    def list_orders(self, limit: int = 10) -> List[Order]:
        """List recent orders.

        Args:
            limit: Maximum number of orders to return

        Returns:
            List of Order objects
        """
        orders = []

        order_files = sorted(
            self.orders_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )

        for order_file in order_files[:limit]:
            try:
                with open(order_file, "r") as f:
                    order_data = json.load(f)
                orders.append(Order.from_dict(order_data))
            except Exception as e:
                logger.error(f"Error loading order from {order_file}: {e}")

        return orders


# Singleton instance
_cart_service: Optional[CartService] = None


def get_cart_service() -> CartService:
    """Get global cart service instance.

    Returns:
        CartService singleton
    """
    global _cart_service
    if _cart_service is None:
        _cart_service = CartService()
    return _cart_service
