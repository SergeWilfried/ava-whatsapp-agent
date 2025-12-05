"""Order confirmation messages and formatters."""

from typing import Optional
from datetime import datetime

from ai_companion.modules.cart.models import Order, OrderStatus, DeliveryMethod


def format_order_confirmation(order: Order) -> str:
    """Format order confirmation message for WhatsApp.

    Args:
        order: Order to format

    Returns:
        Formatted confirmation message
    """
    lines = ["✅ *Commande Confirmée!*\n"]

    # Order number (prefer API order number if available)
    if order.api_order_number:
        lines.append(f"📋 Votre Commande: *{order.api_order_number}*")
    else:
        lines.append(f"📋 Votre Commande: *{order.order_id}*")

    lines.append("")

    # Customer info
    if order.customer_name:
        lines.append(f"👤 Client: {order.customer_name}")

    if order.customer_phone:
        lines.append(f"📞 Phone: {order.customer_phone}")

    lines.append("")

    # Order items
    lines.append("🛒 *Votre Commande:*")
    for item in order.cart.items:
        size_text = (
            f" ({item.customization.size})"
            if item.customization and item.customization.size
            else ""
        )
        extras_text = ""
        if item.customization and item.customization.extras:
            extras_count = len(item.customization.extras)
            extras_text = f" + {extras_count} extra(s)"

        lines.append(
            f"  • {item.quantity}x {item.name}{size_text}{extras_text}"
        )
        lines.append(f"    ${item.item_total:.2f}")

    lines.append("")

    # Pricing
    lines.append(f"Sous Total: ${order.subtotal:.2f}")

    if order.delivery_fee > 0:
        lines.append(f"Livraison: ${order.delivery_fee:.2f}")
    elif order.discount_description:
        lines.append(f"Livraison: Gratuit ✨")

    lines.append(f"Taxes: ${order.tax_amount:.2f}")

    if order.discount > 0:
        lines.append(f"Rabais: -${order.discount:.2f}")

    lines.append(f"*Total: ${order.total:.2f}*")

    lines.append("")

    # Delivery info
    if order.delivery_method == DeliveryMethod.DELIVERY:
        lines.append(f"🚚 *Adresse de livraison:*")
        lines.append(f"{order.delivery_address}")

        if order.estimated_ready_time:
            estimated_time = order.estimated_ready_time.strftime("%I:%M %p")
            lines.append(f"\n⏰ Livraison estimée: {estimated_time}")

    elif order.delivery_method == DeliveryMethod.PICKUP:
        lines.append(f"🏪 *Retrait*")

        if order.estimated_ready_time:
            estimated_time = order.estimated_ready_time.strftime("%I:%M %p")
            lines.append(f"\n⏰ Prêt pour enlèvement: {estimated_time}")

    # Payment method
    if order.payment_method:
        payment_name = order.payment_method.value.replace("_", " ").title()
        lines.append(f"\n💳 Methode de paiement: {payment_name}")

    # Special instructions
    if order.special_instructions:
        lines.append(f"\n📝 Note: {order.special_instructions}")

    lines.append("")
    lines.append("Merci pour votre commande! 🙏")

    # Add API tracking info if available
    if order.api_order_id:
        lines.append(f"\n_Suivez votre commande: {order.api_order_id}_")

    return "\n".join(lines)


def format_order_status_update(
    order: Order,
    new_status: OrderStatus,
    message: Optional[str] = None
) -> str:
    """Format order status update message.

    Args:
        order: Order being updated
        new_status: New order status
        message: Optional custom message

    Returns:
        Formatted status update message
    """
    # Status emoji mapping
    status_emojis = {
        OrderStatus.PENDING: "⏳",
        OrderStatus.CONFIRMED: "✅",
        OrderStatus.PREPARING: "👨‍🍳",
        OrderStatus.READY: "✅",
        OrderStatus.OUT_FOR_DELIVERY: "🚚",
        OrderStatus.DELIVERED: "📦",
        OrderStatus.PICKED_UP: "✅",
        OrderStatus.CANCELLED: "❌",
    }

    emoji = status_emojis.get(new_status, "📋")

    # Order number
    order_num = order.api_order_number or order.order_id

    lines = [f"{emoji} *Order Update*\n"]
    lines.append(f"📋 Order: *{order_num}*")

    # Status-specific messages
    if new_status == OrderStatus.CONFIRMED:
        lines.append("\n✅ Your order has been confirmed!")
        lines.append("We're preparing it now...")

    elif new_status == OrderStatus.PREPARING:
        lines.append("\n👨‍🍳 Your order is being prepared!")
        if order.estimated_ready_time:
            estimated_time = order.estimated_ready_time.strftime("%I:%M %p")
            lines.append(f"Estimated ready: {estimated_time}")

    elif new_status == OrderStatus.READY:
        if order.delivery_method == DeliveryMethod.PICKUP:
            lines.append("\n✅ Your order is ready for pickup!")
        else:
            lines.append("\n✅ Your order is ready!")
            lines.append("Driver will arrive shortly...")

    elif new_status == OrderStatus.OUT_FOR_DELIVERY:
        lines.append("\n🚚 Your order is out for delivery!")
        lines.append(f"Delivering to: {order.delivery_address}")

    elif new_status == OrderStatus.DELIVERED:
        lines.append("\n📦 Your order has been delivered!")
        lines.append("Enjoy your meal! 🍽️")

    elif new_status == OrderStatus.PICKED_UP:
        lines.append("\n✅ Order picked up!")
        lines.append("Enjoy your meal! 🍽️")

    elif new_status == OrderStatus.CANCELLED:
        lines.append("\n❌ Your order has been cancelled.")
        if message:
            lines.append(f"Reason: {message}")

    # Add custom message if provided
    if message and new_status != OrderStatus.CANCELLED:
        lines.append(f"\n{message}")

    return "\n".join(lines)


def format_order_summary(order: Order) -> str:
    """Format brief order summary for display.

    Args:
        order: Order to summarize

    Returns:
        Brief order summary
    """
    order_num = order.api_order_number or order.order_id

    lines = [f"📋 *Order {order_num}*"]
    lines.append(f"Status: {order.status.value.title()}")
    lines.append(f"Items: {order.cart.item_count}")
    lines.append(f"Total: ${order.total:.2f}")

    if order.delivery_method == DeliveryMethod.DELIVERY:
        lines.append("Type: Livraison 🚚")
    elif order.delivery_method == DeliveryMethod.PICKUP:
        lines.append("Type: Retrait 🏪")

    if order.estimated_ready_time:
        estimated_time = order.estimated_ready_time.strftime("%I:%M %p")
        lines.append(f"Pret: {estimated_time}")

    return "\n".join(lines)


def format_order_error(error_message: str, order_id: Optional[str] = None) -> str:
    """Format order error message.

    Args:
        error_message: Error description
        order_id: Optional order ID

    Returns:
        Formatted error message
    """
    lines = ["❌ *Order Error*\n"]

    if order_id:
        lines.append(f"Order: {order_id}\n")

    lines.append(f"{error_message}")
    lines.append("\nPlease try again or contact support if the issue persists.")

    return "\n".join(lines)
