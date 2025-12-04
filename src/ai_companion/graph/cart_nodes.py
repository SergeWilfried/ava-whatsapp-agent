"""Graph nodes for shopping cart operations."""
import logging
from typing import Dict, Optional
from langchain_core.messages import AIMessage
from ai_companion.graph.state import AICompanionState
from ai_companion.modules.cart import (
    ShoppingCart,
    Order,
    OrderStage,
    DeliveryMethod,
    PaymentMethod,
)
# Use v2 cart service with API support
from ai_companion.modules.cart.cart_service_v2 import CartService
# Use v2 interactive components with API support
from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    create_size_selection_buttons,
    create_extras_list,
    create_modifiers_list,
    create_category_selection_list,
)
# Legacy components (will be migrated to v2)
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_item_added_buttons,
    create_cart_view_buttons,
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
        try:
            return ShoppingCart.from_dict(cart_data)
        except Exception as e:
            logger.error(f"Error deserializing cart: {e}")
            # If deserialization fails, create new cart
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
    current_item = state.get("current_item") or {}
    menu_item_id = current_item.get("menu_item_id")

    if not menu_item_id:
        return {
            "messages": AIMessage(content="I couldn't find that item. Please try selecting from the menu again."),
            "order_stage": OrderStage.BROWSING.value
        }

    # Check if item needs customization (pizzas, burgers) - ASYNC
    menu_item = await cart_service.find_menu_item(menu_item_id)
    if not menu_item:
        return {
            "messages": AIMessage(content="Sorry, that item is not available right now."),
            "order_stage": OrderStage.BROWSING.value
        }

    category = menu_item.get("category", "")

    # Items that typically allow customization
    if category in ["pizzas", "burgers"]:
        # Ask for size - use API presentations if available
        presentations = menu_item.get("presentations")
        if presentations:
            interactive_comp = create_size_selection_buttons(
                menu_item["name"],
                presentations=presentations
            )
        else:
            # Fallback to legacy pricing
            interactive_comp = create_size_selection_buttons(
                menu_item["name"],
                base_price=menu_item.get("price", 0.0)
            )

        return {
            "messages": AIMessage(content=f"Great choice! {menu_item['name']}"),
            "interactive_component": interactive_comp,
            "order_stage": OrderStage.CUSTOMIZING.value,
            "current_item": menu_item
        }
    else:
        # Add directly to cart without customization - ASYNC
        success, message, cart_item = await cart_service.add_item_to_cart(
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
    current_item = state.get("current_item") or {}
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
    pending = state.get("pending_customization") or {}
    pending["size"] = size

    # Ask about extras for pizzas and burgers
    if category in ["pizzas", "burgers"]:
        # Use API modifiers if available, otherwise fallback to legacy
        modifiers = current_item.get("modifiers")
        if modifiers:
            interactive_comp = create_modifiers_list(
                current_item.get("name", "item"),
                modifiers=modifiers
            )
        else:
            # Fallback to legacy extras
            interactive_comp = create_extras_list(category=category)

        return {
            "messages": AIMessage(content=f"Perfect! Would you like to add any extras?"),
            "interactive_component": interactive_comp,
            "pending_customization": pending,
            "order_stage": OrderStage.CUSTOMIZING.value
        }
    else:
        # Update state with pending customization before finalizing
        state["pending_customization"] = pending
        # Finalize and add to cart
        return await finalize_customization_node(state)


async def handle_extras_selection_node(state: AICompanionState) -> Dict:
    """Handle extras/toppings selection."""
    # Extract extras from last message
    last_message = state["messages"][-1].content.lower()

    pending = state.get("pending_customization") or {}
    extras = pending.get("extras", [])

    # Parse extra selection (would come from interactive list reply)
    # For now, we'll extract from the message content
    extra_options = ["extra_cheese", "mushrooms", "olives", "pepperoni", "bacon", "chicken"]
    for extra in extra_options:
        if extra.replace("_", " ") in last_message:
            if extra not in extras:
                extras.append(extra)

    pending["extras"] = extras

    # Update state with pending customization before finalizing
    state["pending_customization"] = pending

    # Finalize and add to cart
    return await finalize_customization_node(state)


async def finalize_customization_node(state: AICompanionState) -> Dict:
    """Finalize customization and add item to cart."""
    cart_service = CartService()
    cart = get_or_create_cart(state)

    current_item = state.get("current_item") or {}
    menu_item_id = current_item.get("id")
    pending = state.get("pending_customization") or {}

    size = pending.get("size")
    extras = pending.get("extras", [])
    presentation_id = pending.get("presentation_id")  # From V2 size selection
    modifier_selections = pending.get("modifier_selections")  # From V2 modifiers

    # Add to cart with customizations - ASYNC with V2 support
    success, message, cart_item = await cart_service.add_item_to_cart(
        cart=cart,
        menu_item_id=menu_item_id,
        quantity=1,
        size=size if not presentation_id else None,  # Legacy size
        extras=extras if not modifier_selections else None,  # Legacy extras
        presentation_id=presentation_id,  # V2 presentation
        modifier_selections=modifier_selections,  # V2 modifiers
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
        # Don't show category selection if already browsing
        # Just inform user cart is empty
        from ai_companion.interfaces.whatsapp.interactive_components import (
            create_quick_actions_buttons,
        )
        interactive_comp = create_quick_actions_buttons()
        return {
            "messages": AIMessage(content="🛒 Your cart is empty.\n\nBrowse the menu to add items!"),
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
    # Check if we have the button ID from the interactive component
    selected_delivery_method = state.get("selected_delivery_method")

    if selected_delivery_method:
        # Use button ID directly (more reliable than text parsing)
        logger.info(f"Delivery method from button ID: {selected_delivery_method}")

        if selected_delivery_method == "delivery":
            delivery_method = DeliveryMethod.DELIVERY.value
            # ALWAYS request location for delivery orders (don't reuse old location)
            logger.info("Delivery selected, requesting fresh location for this order")
            return await request_delivery_location_node(state)

        elif selected_delivery_method == "pickup":
            delivery_method = DeliveryMethod.PICKUP.value
            next_message = f"Great! You can pick up from {RESTAURANT_INFO['address']}"

        elif selected_delivery_method == "dine_in":
            delivery_method = DeliveryMethod.DINE_IN.value
            next_message = "Wonderful! We'll have your table ready."

        else:
            # Unknown button ID, default to delivery
            delivery_method = DeliveryMethod.DELIVERY.value
            logger.warning(f"Unknown delivery method button ID: {selected_delivery_method}, defaulting to delivery")
            return await request_delivery_location_node(state)

    else:
        # Fallback: parse from text message (for backward compatibility or text input)
        last_message = state["messages"][-1].content.lower()
        logger.info(f"Delivery method from text parsing: {last_message}")

        if "pickup" in last_message or "pick" in last_message:
            delivery_method = DeliveryMethod.PICKUP.value
            next_message = f"Great! You can pick up from {RESTAURANT_INFO['address']}"
        elif "dine" in last_message or "dine-in" in last_message:
            delivery_method = DeliveryMethod.DINE_IN.value
            next_message = "Wonderful! We'll have your table ready."
        elif "delivery" in last_message:
            delivery_method = DeliveryMethod.DELIVERY.value
            logger.info("Delivery selected, requesting fresh location for this order")
            return await request_delivery_location_node(state)
        else:
            # Default to delivery
            delivery_method = DeliveryMethod.DELIVERY.value
            logger.info("Delivery selected (default), requesting fresh location for this order")
            return await request_delivery_location_node(state)

    # Ask for payment method (only for pickup/dine-in)
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

    # Create order preview from cart
    delivery_method_str = state.get("delivery_method", DeliveryMethod.DELIVERY.value)
    delivery_method = DeliveryMethod(delivery_method_str)
    delivery_address = state.get("delivery_address")
    delivery_phone = state.get("delivery_phone")
    customer_name = state.get("customer_name", "Customer")
    # Use WhatsApp phone number as fallback for delivery_phone
    user_phone = state.get("user_phone")
    if not delivery_phone and user_phone:
        delivery_phone = user_phone

    # Create order - ASYNC with V2 API support
    order = await cart_service.create_order_from_cart(
        cart=cart,
        delivery_method=delivery_method,
        payment_method=PaymentMethod(payment_method),
        customer_name=customer_name,
        delivery_address=delivery_address,
        delivery_phone=delivery_phone,
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
        "active_order_id": order.api_order_id or order.order_id,
        "order_stage": OrderStage.CONFIRMED.value
    }


async def confirm_order_node(state: AICompanionState) -> Dict:
    """Confirm and finalize the order."""
    from ai_companion.modules.cart import format_order_confirmation

    cart_service = CartService()
    cart = get_or_create_cart(state)

    # Create final order - ASYNC with V2 API support
    delivery_method_str = state.get("delivery_method", DeliveryMethod.DELIVERY.value)
    payment_method_str = state.get("payment_method", PaymentMethod.CASH.value)
    delivery_address = state.get("delivery_address")
    delivery_phone = state.get("delivery_phone")
    customer_name = state.get("customer_name", "Customer")

    order = await cart_service.create_order_from_cart(
        cart=cart,
        delivery_method=DeliveryMethod(delivery_method_str),
        payment_method=PaymentMethod(payment_method_str),
        customer_name=customer_name,
        delivery_address=delivery_address,
        delivery_phone=delivery_phone,
    )

    # Confirm order
    cart_service.confirm_order(order)

    # Save order (local backup)
    cart_service.save_order(order)

    # Use V2 order confirmation message
    confirmation_message = format_order_confirmation(order)

    # Create order status interactive component (legacy)
    interactive_comp = create_order_status_message(
        order.api_order_number or order.order_id,  # Use API number if available
        order.status.value,
        confirmation_message
    )

    # Clear cart after confirmation
    cart.clear()

    return {
        "messages": AIMessage(content=confirmation_message),
        "interactive_component": interactive_comp,
        "shopping_cart": cart.to_dict(),
        "order_stage": OrderStage.CONFIRMED.value,
        "active_order_id": order.api_order_id or order.order_id
    }


async def request_delivery_location_node(state: AICompanionState) -> Dict:
    """Request user's delivery location during checkout.

    This node is triggered when the user selects delivery as the delivery method
    and needs to provide their location for delivery.

    Returns:
        Dict: State updates with location request message and interactive component
    """
    from ai_companion.interfaces.whatsapp.location_components import create_location_request_component

    logger.info("Requesting delivery location from user")

    # Create location request interactive component
    interactive_comp = create_location_request_component(
        body_text="📍  Veuillez indiquer votre lieu de livraison afin que nous puissions confirmer la livraison dans votre zone.\n\n"
                  "Vous pouvez soit:\n"
                  "• Partager votre position actuelle\n"
                  "• Saisir une adresse manuellement"
    )

    return {
        "messages": AIMessage(content="location_request"),
        "interactive_component": interactive_comp,
        "awaiting_location": True,
        "order_stage": OrderStage.AWAITING_LOCATION.value
    }
