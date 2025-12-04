"""Order service for CartaAI API integration.

This module provides high-level order management operations including
order creation, tracking, and history retrieval.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ai_companion.modules.cart.models import (
    ShoppingCart,
    CartItem,
    Order,
    DeliveryMethod,
    PaymentMethod,
)
from ai_companion.services.cartaai.client import CartaAIClient

logger = logging.getLogger(__name__)


class OrderService:
    """Service for managing orders via CartaAI API.

    Provides high-level operations for order creation, tracking, and history.
    """

    def __init__(self, client: CartaAIClient):
        """Initialize order service.

        Args:
            client: CartaAI API client
        """
        self.client = client

    async def create_order(
        self,
        cart: ShoppingCart,
        customer_name: str,
        customer_phone: str,
        delivery_method: DeliveryMethod,
        payment_method: PaymentMethod,
        delivery_address: Optional[str] = None,
        delivery_instructions: Optional[str] = None,
        special_instructions: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Create a new order from shopping cart.

        Args:
            cart: Shopping cart with items
            customer_name: Customer full name
            customer_phone: Customer phone number
            delivery_method: Delivery, pickup, or dine-in
            payment_method: Payment method
            delivery_address: Delivery address (required for delivery)
            delivery_instructions: Delivery-specific instructions
            special_instructions: Order-level special instructions
            scheduled_time: Optional scheduled time for delivery/pickup

        Returns:
            API response with order details:
            {
                "type": "1",
                "message": "Order created successfully",
                "data": {
                    "_id": "order123",
                    "orderNumber": "ORD-2024-001234",
                    "status": "pending",
                    "total": 45.99,
                    ...
                }
            }

        Raises:
            CartaAIAPIException: If API returns error
            CartaAINetworkException: If network error occurs
            ValueError: If validation fails
        """
        # Validate inputs
        if cart.is_empty:
            raise ValueError("Cannot create order from empty cart")

        if delivery_method == DeliveryMethod.DELIVERY and not delivery_address:
            raise ValueError("Delivery address required for delivery orders")

        # Build order payload
        order_payload = build_order_payload(
            cart=cart,
            customer_name=customer_name,
            customer_phone=customer_phone,
            delivery_method=delivery_method,
            payment_method=payment_method,
            delivery_address=delivery_address,
            delivery_instructions=delivery_instructions,
            special_instructions=special_instructions,
            scheduled_time=scheduled_time,
        )

        logger.info(f"Creating order for {customer_name} ({customer_phone})")
        logger.debug(f"Order payload: {order_payload}")

        # Create order via API
        try:
            response = await self.client.create_order(order_payload)

            if response.get("type") == "1":
                order_data = response.get("data", {})
                logger.info(
                    f"Order created successfully: {order_data.get('orderNumber')} "
                    f"(ID: {order_data.get('_id')})"
                )
                return response
            else:
                error_msg = response.get("message", "Unknown error")
                logger.error(f"Order creation failed: {error_msg}")
                raise ValueError(f"Order creation failed: {error_msg}")

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details by ID.

        Args:
            order_id: Order ID from create_order response

        Returns:
            API response with order details
        """
        logger.debug(f"Fetching order: {order_id}")
        response = await self.client.get_order(order_id)

        if response.get("type") == "1":
            return response
        else:
            error_msg = response.get("message", "Order not found")
            raise ValueError(f"Failed to fetch order: {error_msg}")

    async def get_customer_orders(
        self,
        phone: str,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """Get customer order history.

        Args:
            phone: Customer phone number
            status: Optional status filter

        Returns:
            List of order objects
        """
        logger.debug(f"Fetching orders for customer: {phone}")
        response = await self.client.get_customer_orders(phone, status)

        if response.get("type") == "1":
            return response.get("data", [])
        else:
            logger.warning(f"Failed to fetch customer orders: {response.get('message')}")
            return []


def build_order_payload(
    cart: ShoppingCart,
    customer_name: str,
    customer_phone: str,
    delivery_method: DeliveryMethod,
    payment_method: PaymentMethod,
    delivery_address: Optional[str] = None,
    delivery_instructions: Optional[str] = None,
    special_instructions: Optional[str] = None,
    scheduled_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build order payload for CartaAI API.

    Converts internal models to API format matching CreateOrderRequest schema.

    Args:
        cart: Shopping cart with items
        customer_name: Customer full name
        customer_phone: Customer phone number
        delivery_method: Delivery, pickup, or dine-in
        payment_method: Payment method
        delivery_address: Delivery address (required for delivery)
        delivery_instructions: Delivery-specific instructions
        special_instructions: Order-level special instructions
        scheduled_time: Optional scheduled time

    Returns:
        Order payload dict ready for API

    Example:
        {
            "customer": {
                "name": "John Doe",
                "phone": "+51987654321",
                "address": {
                    "street": "123 Main St",
                    "reference": "Blue door"
                }
            },
            "items": [
                {
                    "productId": "prod001",
                    "presentationId": "pres001",
                    "name": "Classic Burger",
                    "quantity": 2,
                    "unitPrice": 15.99,
                    "modifiers": [...],
                    "notes": "No onions"
                }
            ],
            "type": "delivery",
            "paymentMethod": "cash",
            "source": "whatsapp",
            "notes": "Special instructions"
        }
    """
    # Build customer info
    customer_data = {
        "name": customer_name,
        "phone": customer_phone,
    }

    # Add address for delivery
    if delivery_address:
        customer_data["address"] = {
            "street": delivery_address,
        }
        if delivery_instructions:
            customer_data["address"]["reference"] = delivery_instructions

    # Convert cart items to API format
    items = []
    for cart_item in cart.items:
        item_data = build_order_item(cart_item)
        items.append(item_data)

    # Map delivery method to API type
    order_type = map_delivery_method_to_api(delivery_method, scheduled_time)

    # Map payment method to API format
    payment_method_str = map_payment_method_to_api(payment_method)

    # Build complete payload
    payload = {
        "customer": customer_data,
        "items": items,
        "type": order_type,
        "paymentMethod": payment_method_str,
        "source": "whatsapp",
    }

    # Add optional fields
    if special_instructions:
        payload["notes"] = special_instructions

    if scheduled_time:
        payload["scheduledTime"] = scheduled_time.isoformat()

    return payload


def build_order_item(cart_item: CartItem) -> Dict[str, Any]:
    """Build order item payload from cart item.

    Args:
        cart_item: Cart item to convert

    Returns:
        Order item dict for API
    """
    item_data = {
        "productId": cart_item.menu_item_id,
        "name": cart_item.name,
        "quantity": cart_item.quantity,
        "unitPrice": cart_item.base_price,
    }

    # Add customization if present
    if cart_item.customization:
        # Add presentation ID (size)
        if cart_item.customization.size:
            item_data["presentationId"] = cart_item.customization.size

        # Add special instructions
        if cart_item.customization.special_instructions:
            item_data["notes"] = cart_item.customization.special_instructions

        # Convert extras to modifiers format
        # Note: For legacy extras, we need to convert them to modifier format
        # For API modifiers, they should already be in the correct format
        if cart_item.customization.extras:
            modifiers = build_modifiers_from_extras(cart_item.customization.extras)
            if modifiers:
                item_data["modifiers"] = modifiers

    return item_data


def build_modifiers_from_extras(extras: List[str]) -> List[Dict]:
    """Convert legacy extras to modifiers format.

    Args:
        extras: List of extra IDs (e.g., ["extra_cheese", "bacon"])

    Returns:
        List of modifier objects for API

    Note:
        This is for backward compatibility with legacy extras.
        When using API modifiers directly, they should already be in correct format.
    """
    # For legacy extras, group them into a single modifier
    if not extras:
        return []

    # Check if extras are already in API format (start with "extra_")
    # vs new format (start with "mod_")
    if any(extra.startswith("mod_") for extra in extras):
        # Parse API format: mod_{modifierId}_{optionId}
        modifiers_dict = {}

        for extra_id in extras:
            if extra_id.startswith("mod_"):
                parts = extra_id.split("_")
                if len(parts) >= 3:
                    modifier_id = parts[1]
                    option_id = "_".join(parts[2:])

                    if modifier_id not in modifiers_dict:
                        modifiers_dict[modifier_id] = {
                            "modifierId": modifier_id,
                            "name": "Extras",  # Placeholder name
                            "options": []
                        }

                    modifiers_dict[modifier_id]["options"].append({
                        "optionId": option_id,
                        "name": option_id,  # Placeholder name
                        "price": 0.0,  # Price already included in cart
                        "quantity": 1
                    })

        return list(modifiers_dict.values())

    else:
        # Legacy format: create a single modifier with all extras
        return [{
            "modifierId": "legacy_extras",
            "name": "Extras",
            "options": [
                {
                    "optionId": extra_id,
                    "name": extra_id.replace("_", " ").title(),
                    "price": 0.0,  # Price already calculated
                    "quantity": 1
                }
                for extra_id in extras
            ]
        }]


def map_delivery_method_to_api(
    delivery_method: DeliveryMethod,
    scheduled_time: Optional[datetime] = None
) -> str:
    """Map internal delivery method to API order type.

    Args:
        delivery_method: Internal delivery method enum
        scheduled_time: Optional scheduled time

    Returns:
        API order type string
    """
    if scheduled_time:
        # Scheduled orders
        if delivery_method == DeliveryMethod.DELIVERY:
            return "scheduled_delivery"
        elif delivery_method == DeliveryMethod.PICKUP:
            return "scheduled_pickup"

    # Immediate orders
    if delivery_method == DeliveryMethod.DELIVERY:
        return "delivery"
    elif delivery_method == DeliveryMethod.PICKUP:
        return "pickup"
    elif delivery_method == DeliveryMethod.DINE_IN:
        return "on_site"

    # Default
    return "delivery"


def map_payment_method_to_api(payment_method: PaymentMethod) -> str:
    """Map internal payment method to API format.

    Args:
        payment_method: Internal payment method enum

    Returns:
        API payment method string
    """
    mapping = {
        PaymentMethod.CASH: "cash",
        PaymentMethod.CREDIT_CARD: "card",
        PaymentMethod.DEBIT_CARD: "card",
        PaymentMethod.MOBILE_PAYMENT: "yape",  # Default mobile to Yape for Peru
        PaymentMethod.ONLINE: "card",
    }

    return mapping.get(payment_method, "cash")


# Singleton instance
_order_service: Optional[OrderService] = None


def get_order_service(client: Optional[CartaAIClient] = None) -> OrderService:
    """Get global order service instance.

    Args:
        client: Optional CartaAI client (uses default if not provided)

    Returns:
        OrderService singleton
    """
    global _order_service

    if _order_service is None:
        if client is None:
            from ai_companion.services.cartaai import get_cartaai_client
            client = get_cartaai_client()
        _order_service = OrderService(client)

    return _order_service


def reset_order_service():
    """Reset global order service (for testing)."""
    global _order_service
    _order_service = None
