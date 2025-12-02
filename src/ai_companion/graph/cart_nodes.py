"""Graph nodes for shopping cart operations."""
import logging
from typing import Dict, Optional
from langchain_core.messages import AIMessage
from ai_companion.graph.state import AICompanionState
from ai_companion.modules.cart import (
    CartService,
    ShoppingCart,
    Order,
    OrderStage,
    DeliveryMethod,
    PaymentMethod,
)
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_item_added_buttons,
    create_cart_view_buttons,
    create_size_selection_buttons,
    create_extras_list,
    create_delivery_method_buttons,
    create_payment_method_list,
    create_order_details_message,
    create_order_status_message,
    create_menu_list_from_restaurant_menu,
)
from ai_companion.core.schedules import RESTAURANT_MENU, RESTAURANT_INFO

logger = logging.getLogger(__name__)


def get_or_create_cart(state: AICompanionState) -> ShoppingCart:
    """Get existing cart from state or create new one."""
    cart_service = CartService()

    cart_data = state.get("shopping_cart")
    if cart_data:
        # Reconstruct cart from serialized data
        cart = ShoppingCart(
            cart_id=cart_data["cart_id"],
            items=[],  # Would need full deserialization
        )
        # For now, create new cart if data exists
        # TODO: Implement full cart deserialization
        return cart_service.create_cart()
    else:
        return cart_service.create_cart()


async def add_to_cart_node(state: AICompanionState) -> Dict:
    """Add selected item to shopping cart.

    Triggered when user selects an item from the menu.
    """
    cart_service = CartService()
    cart = get_or_create_cart(state)

    # Extract item selection from last message
    last_message = state["messages"][-1].content
    logger.info(f"Processing add to cart for: {last_message}")

    # Parse item ID from interactive reply or text
    # This would come from webhook handler's processing of interactive replies
    current_item = state.get("current_item", {})
    menu_item_id = current_item.get("menu_item_id")

    if not menu_item_id:
        return {
            "messages": AIMessage(content="I couldn't find that item. Please try selecting from the menu again."),
            "order_stage": OrderStage.BROWSING.value
        }

    # Check if item needs customization (pizzas, burgers)
    menu_item = cart_service.find_menu_item(menu_item_id)
    if not menu_item:
        return {
            "messages": AIMessage(content="Sorry, that item is not available right now."),
            "order_stage": OrderStage.BROWSING.value
        }

    category = menu_item.get("category", "")

    # Items that typically allow customization
    if category in ["pizzas", "burgers"]:
        # Ask for size
        interactive_comp = create_size_selection_buttons(menu_item["name"], menu_item["price"])
        return {
            "messages": AIMessage(content=f"Great choice! {menu_item['name']}"),
            "interactive_component": interactive_comp,
            "order_stage": OrderStage.CUSTOMIZING.value,
            "current_item": menu_item
        }
    else:
        # Add directly to cart without customization
        success, message, cart_item = cart_service.add_item_to_cart(
            cart, menu_item_id, quantity=1
        )

        if success:
            interactive_comp = create_item_added_buttons(
                menu_item["name"],
                cart.subtotal,
                cart.item_count
            )
            return {
                "messages": AIMessage(content=message),
                "interactive_component": interactive_comp,
                "shopping_cart": cart.to_dict(),
                "order_stage": OrderStage.REVIEWING_CART.value
            }
        else:
            return {
                "messages": AIMessage(content=message),
                "order_stage": OrderStage.BROWSING.value
            }


async def handle_size_selection_node(state: AICompanionState) -> Dict:
    """Handle size selection for customizable items."""
    cart_service = CartService()
    current_item = state.get("current_item", {})
    menu_item_id = current_item.get("id")
    category = current_item.get("category", "")

    # Extract size from last message (e.g., "size_medium")
    last_message = state["messages"][-1].content.lower()
    size = None
    if "small" in last_message:
        size = "small"
    elif "medium" in last_message:
        size = "medium"
    elif "large" in last_message:
        size = "large"

    if not size:
        size = "medium"  # Default

    # Store size in pending customization
    pending = state.get("pending_customization", {}) or {}
    pending["size"] = size

    # Ask about extras for pizzas and burgers
    if category in ["pizzas", "burgers"]:
        interactive_comp = create_extras_list(category)
        return {
            "messages": AIMessage(content=f"Perfect! Would you like to add any extras?"),
            "interactive_component": interactive_comp,
            "pending_customization": pending,
            "order_stage": OrderStage.CUSTOMIZING.value
        }
    else:
        # Finalize and add to cart
        return await finalize_customization_node(state)


async def handle_extras_selection_node(state: AICompanionState) -> Dict:
    """Handle extras/toppings selection."""
    # Extract extras from last message
    last_message = state["messages"][-1].content.lower()

    pending = state.get("pending_customization", {}) or {}
    extras = pending.get("extras", [])

    # Parse extra selection (would come from interactive list reply)
    # For now, we'll extract from the message content
    extra_options = ["extra_cheese", "mushrooms", "olives", "pepperoni", "bacon", "chicken"]
    for extra in extra_options:
        if extra.replace("_", " ") in last_message:
            if extra not in extras:
                extras.append(extra)

    pending["extras"] = extras

    # Finalize and add to cart
    return await finalize_customization_node(state)


async def finalize_customization_node(state: AICompanionState) -> Dict:
    """Finalize customization and add item to cart."""
    cart_service = CartService()
    cart = get_or_create_cart(state)

    current_item = state.get("current_item", {})
    menu_item_id = current_item.get("id")
    pending = state.get("pending_customization", {}) or {}

    size = pending.get("size")
    extras = pending.get("extras", [])

    # Add to cart with customizations
    success, message, cart_item = cart_service.add_item_to_cart(
        cart,
        menu_item_id,
        quantity=1,
        size=size,
        extras=extras
    )

    if success:
        interactive_comp = create_item_added_buttons(
            current_item["name"],
            cart.subtotal,
            cart.item_count
        )
        return {
            "messages": AIMessage(content=message),
            "interactive_component": interactive_comp,
            "shopping_cart": cart.to_dict(),
            "order_stage": OrderStage.REVIEWING_CART.value,
            "pending_customization": None,
            "current_item": None
        }
    else:
        return {
            "messages": AIMessage(content=message),
            "order_stage": OrderStage.BROWSING.value
        }


async def view_cart_node(state: AICompanionState) -> Dict:
    """Display cart contents with action buttons."""
    cart = get_or_create_cart(state)
    cart_service = CartService()

    if cart.is_empty:
        # Show menu instead
        interactive_comp = create_menu_list_from_restaurant_menu(RESTAURANT_MENU)
        return {
            "messages": AIMessage(content="Your cart is empty. Let's browse the menu!"),
            "interactive_component": interactive_comp,
            "order_stage": OrderStage.BROWSING.value
        }

    # Generate cart summary
    summary = cart_service.get_cart_summary(cart)

    # Create action buttons
    interactive_comp = create_cart_view_buttons(cart.subtotal, cart.item_count)

    return {
        "messages": AIMessage(content=summary),
        "interactive_component": interactive_comp,
        "order_stage": OrderStage.REVIEWING_CART.value
    }


async def clear_cart_node(state: AICompanionState) -> Dict:
    """Clear all items from cart."""
    cart = get_or_create_cart(state)
    cart.clear()

    return {
        "messages": AIMessage(content="🗑️ Cart cleared! Ready to start a new order?"),
        "shopping_cart": cart.to_dict(),
        "order_stage": OrderStage.BROWSING.value,
        "use_interactive_menu": True
    }


async def checkout_node(state: AICompanionState) -> Dict:
    """Begin checkout process."""
    cart = get_or_create_cart(state)

    if cart.is_empty:
        return {
            "messages": AIMessage(content="Your cart is empty. Add some items first!"),
            "order_stage": OrderStage.BROWSING.value,
            "use_interactive_menu": True
        }

    # Ask for delivery method
    interactive_comp = create_delivery_method_buttons()

    return {
        "messages": AIMessage(content="Great! Let's complete your order."),
        "interactive_component": interactive_comp,
        "order_stage": OrderStage.CHECKOUT.value
    }


async def handle_delivery_method_node(state: AICompanionState) -> Dict:
    """Handle delivery method selection."""
    last_message = state["messages"][-1].content.lower()

    # Parse delivery method
    if "delivery" in last_message:
        delivery_method = DeliveryMethod.DELIVERY.value
        next_message = "Perfect! We'll deliver to your address."
    elif "pickup" in last_message:
        delivery_method = DeliveryMethod.PICKUP.value
        next_message = f"Great! You can pick up from {RESTAURANT_INFO['address']}"
    elif "dine" in last_message or "dine-in" in last_message:
        delivery_method = DeliveryMethod.DINE_IN.value
        next_message = "Wonderful! We'll have your table ready."
    else:
        delivery_method = DeliveryMethod.DELIVERY.value
        next_message = "We'll deliver to your address."

    # Ask for payment method
    interactive_comp = create_payment_method_list()

    return {
        "messages": AIMessage(content=next_message),
        "interactive_component": interactive_comp,
        "delivery_method": delivery_method,
        "order_stage": OrderStage.PAYMENT.value
    }


async def handle_payment_method_node(state: AICompanionState) -> Dict:
    """Handle payment method selection and show order details."""
    cart_service = CartService()
    cart = get_or_create_cart(state)

    last_message = state["messages"][-1].content.lower()

    # Parse payment method
    payment_method = PaymentMethod.CASH.value
    if "credit" in last_message:
        payment_method = PaymentMethod.CREDIT_CARD.value
    elif "debit" in last_message:
        payment_method = PaymentMethod.DEBIT_CARD.value
    elif "mobile" in last_message or "apple" in last_message or "google" in last_message:
        payment_method = PaymentMethod.MOBILE_PAYMENT.value

    # Create order from cart
    delivery_method_str = state.get("delivery_method", DeliveryMethod.DELIVERY.value)
    delivery_method = DeliveryMethod(delivery_method_str)

    order = cart_service.create_order_from_cart(
        cart,
        delivery_method=delivery_method,
        payment_method=PaymentMethod(payment_method),
        customer_name="Customer",  # Would get from user profile
    )

    # Generate order details interactive message
    order_dict = order.to_dict()
    order_dict["items"] = [item.to_dict() for item in cart.items]
    order_dict["estimated_time"] = RESTAURANT_INFO.get(
        "estimated_delivery_time" if delivery_method == DeliveryMethod.DELIVERY
        else "estimated_pickup_time",
        "30-45 minutes"
    )

    interactive_comp = create_order_details_message(order_dict)

    return {
        "messages": AIMessage(content=f"Here's your order summary:"),
        "interactive_component": interactive_comp,
        "payment_method": payment_method,
        "active_order_id": order.order_id,
        "order_stage": OrderStage.CONFIRMED.value
    }


async def confirm_order_node(state: AICompanionState) -> Dict:
    """Confirm and finalize the order."""
    cart_service = CartService()
    cart = get_or_create_cart(state)

    # Create final order
    delivery_method_str = state.get("delivery_method", DeliveryMethod.DELIVERY.value)
    payment_method_str = state.get("payment_method", PaymentMethod.CASH.value)

    order = cart_service.create_order_from_cart(
        cart,
        delivery_method=DeliveryMethod(delivery_method_str),
        payment_method=PaymentMethod(payment_method_str),
        customer_name="Customer",
    )

    # Confirm order
    cart_service.confirm_order(order)

    # Save order
    cart_service.save_order(order)

    # Get status message
    status_message = cart_service.get_order_status_message(order)

    # Create order status interactive component
    interactive_comp = create_order_status_message(
        order.order_id,
        order.status.value,
        status_message
    )

    # Clear cart after confirmation
    cart.clear()

    return {
        "messages": AIMessage(content=f"✅ Order confirmed! {status_message}"),
        "interactive_component": interactive_comp,
        "shopping_cart": cart.to_dict(),
        "order_stage": OrderStage.CONFIRMED.value,
        "active_order_id": order.order_id
    }
