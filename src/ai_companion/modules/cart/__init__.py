"""Shopping cart module for restaurant ordering."""
from ai_companion.modules.cart.models import (
    CartItem,
    CartItemCustomization,
    ShoppingCart,
    Order,
    OrderStatus,
    OrderStage,
    DeliveryMethod,
    PaymentMethod,
)
# Export v2 by default (with API support)
from ai_companion.modules.cart.cart_service_v2 import CartService, get_cart_service
# Legacy service still available
from ai_companion.modules.cart.cart_service import CartService as CartServiceLegacy
# Order messages
from ai_companion.modules.cart.order_messages import (
    format_order_confirmation,
    format_order_status_update,
    format_order_summary,
    format_order_error,
)

__all__ = [
    "CartItem",
    "CartItemCustomization",
    "ShoppingCart",
    "Order",
    "OrderStatus",
    "OrderStage",
    "DeliveryMethod",
    "PaymentMethod",
    "CartService",  # V2 by default
    "get_cart_service",
    "CartServiceLegacy",  # For backward compatibility
    "format_order_confirmation",
    "format_order_status_update",
    "format_order_summary",
    "format_order_error",
]
