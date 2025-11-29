"""
E-commerce nodes for LangGraph workflow.
Handles catalog browsing, product viewing, cart management, and checkout.
"""
import logging
from typing import Dict, Any, List
from langchain_core.messages import AIMessage

from ai_companion.graph.state import AICompanionState
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_list_message,
    create_reply_buttons
)
from ai_companion.services.product_service import get_product_service
from ai_companion.services.business_service_optimized import get_optimized_business_service

logger = logging.getLogger(__name__)


async def catalog_node(state: AICompanionState) -> Dict[str, Any]:
    """
    Show product catalog using interactive lists.

    This node displays categories or products based on the current context.
    Uses WhatsApp interactive list messages for browsing.

    Args:
        state: Current conversation state

    Returns:
        Updated state with interactive_component
    """
    try:
        # Get business and product services
        business_service = await get_optimized_business_service()
        product_service = await get_product_service(business_service.db)

        sub_domain = state.get("sub_domain")
        local_id = state.get("local_id")
        selected_category = state.get("selected_category")

        if not sub_domain:
            return {
                "messages": [AIMessage(content="I need to know which business you're shopping with.")],
                "workflow": "conversation"
            }

        # If no category selected, show categories
        if not selected_category:
            categories = await product_service.get_categories(sub_domain, local_id)

            if not categories:
                return {
                    "messages": [AIMessage(content="Sorry, no products are available right now.")],
                    "workflow": "conversation"
                }

            # Build category list
            sections = [{
                "title": "Categories",
                "rows": [
                    {
                        "id": f"cat:{cat.r_id}",
                        "title": cat.name[:24],  # WhatsApp limit
                        "description": cat.description[:72] if cat.description else "View products"
                    }
                    for cat in categories
                ]
            }]

            interactive = create_list_message(
                header="Browse Our Menu",
                body="Select a category to view products:",
                sections=sections,
                button_text="View Categories"
            )

            return {
                "messages": [AIMessage(content="Here's our menu! Select a category:")],
                "interactive_component": interactive,
                "workflow": "catalog"
            }

        # Show products in selected category
        products = await product_service.get_products_by_category(
            sub_domain=sub_domain,
            category_id=selected_category,
            local_id=local_id,
            limit=10
        )

        if not products:
            return {
                "messages": [AIMessage(content="No products found in this category.")],
                "workflow": "conversation",
                "selected_category": None  # Reset category
            }

        # Build product list
        sections = [{
            "title": "Products",
            "rows": [
                {
                    "id": f"prod:{p.r_id}",
                    "title": p.name[:24],
                    "description": f"${p.base_price:.2f} - {p.description[:50] if p.description else ''}"[:72]
                }
                for p in products
            ]
        }]

        interactive = create_list_message(
            header="Products",
            body="Select a product to view details:",
            sections=sections,
            button_text="View Products"
        )

        return {
            "messages": [AIMessage(content="Here are the products:")],
            "interactive_component": interactive,
            "workflow": "catalog"
        }

    except Exception as e:
        logger.error(f"Catalog node error: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="Sorry, I had trouble loading the catalog. Please try again.")],
            "workflow": "conversation"
        }


async def product_detail_node(state: AICompanionState) -> Dict[str, Any]:
    """
    Show product details and customization options.

    For products with presentations or modifiers, this triggers a WhatsApp Flow.
    For simple products, shows quick add-to-cart buttons.

    Args:
        state: Current conversation state

    Returns:
        Updated state with product details
    """
    try:
        # Get services
        business_service = await get_optimized_business_service()
        product_service = await get_product_service(business_service.db)

        product_context = state.get("product_context", {})
        product_id = product_context.get("product_id")
        sub_domain = state.get("sub_domain")

        if not product_id or not sub_domain:
            return {
                "messages": [AIMessage(content="Please select a product first.")],
                "workflow": "conversation"
            }

        # Get product details
        product = await product_service.get_product_by_id(product_id, sub_domain)

        if not product:
            return {
                "messages": [AIMessage(content="Product not found.")],
                "workflow": "conversation"
            }

        # Check if product has customization options
        presentations = await product_service.get_presentations_for_product(product_id, sub_domain)
        modifiers = await product_service.get_modifiers_for_product(product_id, sub_domain)

        has_customization = len(presentations) > 0 or len(modifiers) > 0

        # Build product description
        description_parts = [
            f"*{product.name}*",
            f"",
            product.description or "",
            f"",
            f"💰 Price: ${product.base_price:.2f}"
        ]

        if product.preparation_time:
            description_parts.append(f"⏱️ Prep time: {product.preparation_time} min")

        if product.allergens:
            description_parts.append(f"⚠️ Allergens: {', '.join(product.allergens)}")

        description = "\n".join(description_parts)

        if has_customization:
            # Product needs customization - show flow trigger button
            interactive = create_reply_buttons(
                body=description,
                buttons=[
                    {"id": f"customize:{product_id}", "title": "Customize Order"},
                    {"id": "back:catalog", "title": "Back to Menu"}
                ]
            )

            return {
                "messages": [AIMessage(content="This product has customization options:")],
                "interactive_component": interactive,
                "workflow": "catalog",
                "flow_action": "add_to_cart"  # Prepare for flow
            }
        else:
            # Simple product - direct add to cart
            interactive = create_reply_buttons(
                body=description,
                buttons=[
                    {"id": f"add_cart:{product_id}:1", "title": "Add to Cart"},
                    {"id": "back:catalog", "title": "Back to Menu"}
                ]
            )

            return {
                "messages": [AIMessage(content="Product details:")],
                "interactive_component": interactive,
                "workflow": "catalog"
            }

    except Exception as e:
        logger.error(f"Product detail node error: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="Sorry, I had trouble loading the product details.")],
            "workflow": "conversation"
        }


async def cart_node(state: AICompanionState) -> Dict[str, Any]:
    """
    Show shopping cart and manage items.

    Displays current cart items and provides options to:
    - Continue shopping
    - Proceed to checkout
    - Remove items

    Args:
        state: Current conversation state

    Returns:
        Updated state with cart display
    """
    try:
        cart_data = state.get("cart_data", {})
        items = cart_data.get("items", [])

        if not items:
            interactive = create_reply_buttons(
                body="Your cart is empty. Start shopping!",
                buttons=[
                    {"id": "browse:catalog", "title": "Browse Menu"}
                ]
            )

            return {
                "messages": [AIMessage(content="🛒 Your cart is empty")],
                "interactive_component": interactive,
                "workflow": "cart"
            }

        # Build cart summary
        cart_lines = ["🛒 *Your Cart*\n"]
        subtotal = 0.0

        for i, item in enumerate(items, 1):
            item_total = item.get("total_price", 0)
            subtotal += item_total

            cart_lines.append(
                f"{i}. {item.get('name')} x{item.get('quantity', 1)}\n"
                f"   ${item_total:.2f}"
            )

            # Show modifiers if any
            modifiers = item.get("modifiers", [])
            if modifiers:
                for mod in modifiers:
                    for opt in mod.get("options", []):
                        cart_lines.append(f"   + {opt.get('name')}")

        cart_lines.append(f"\n*Subtotal: ${subtotal:.2f}*")
        cart_summary = "\n".join(cart_lines)

        # Show cart actions
        interactive = create_reply_buttons(
            body=cart_summary,
            buttons=[
                {"id": "checkout:now", "title": "Checkout"},
                {"id": "browse:catalog", "title": "Add More Items"},
                {"id": "clear:cart", "title": "Clear Cart"}
            ]
        )

        return {
            "messages": [AIMessage(content="Here's your cart:")],
            "interactive_component": interactive,
            "workflow": "cart"
        }

    except Exception as e:
        logger.error(f"Cart node error: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="Sorry, I had trouble loading your cart.")],
            "workflow": "conversation"
        }


async def checkout_node(state: AICompanionState) -> Dict[str, Any]:
    """
    Handle checkout process.

    Collects delivery information and payment method.
    For complex checkout, triggers WhatsApp Flow.

    Args:
        state: Current conversation state

    Returns:
        Updated state with checkout flow
    """
    try:
        cart_data = state.get("cart_data", {})
        items = cart_data.get("items", [])

        if not items:
            return {
                "messages": [AIMessage(content="Your cart is empty. Add items first!")],
                "workflow": "conversation"
            }

        # Start checkout flow
        # For now, ask for delivery type
        interactive = create_reply_buttons(
            body="How would you like to receive your order?",
            buttons=[
                {"id": "delivery:home", "title": "🚚 Delivery"},
                {"id": "pickup:store", "title": "🏪 Pickup"},
                {"id": "back:cart", "title": "Back to Cart"}
            ]
        )

        return {
            "messages": [AIMessage(content="Let's complete your order:")],
            "interactive_component": interactive,
            "workflow": "checkout"
        }

    except Exception as e:
        logger.error(f"Checkout node error: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="Sorry, I had trouble starting checkout.")],
            "workflow": "conversation"
        }


async def flow_handler_node(state: AICompanionState) -> Dict[str, Any]:
    """
    Prepare and trigger WhatsApp Flow.

    This node generates Flow JSON and triggers the flow for:
    - Product customization (presentations + modifiers)
    - Checkout (address + payment)

    Args:
        state: Current conversation state

    Returns:
        Updated state with flow_component
    """
    try:
        flow_action = state.get("flow_action")

        if flow_action == "add_to_cart":
            # Generate product customization flow
            product_context = state.get("product_context", {})
            product_id = product_context.get("product_id")
            sub_domain = state.get("sub_domain")

            if not product_id:
                return {
                    "messages": [AIMessage(content="Please select a product first.")],
                    "workflow": "conversation"
                }

            # Build flow message
            # Note: Actual Flow is triggered via WhatsApp Cloud API, not through message
            flow_message = (
                f"Tap below to customize your order:\n"
                f"Flow endpoint: /flows/product/{product_id}/{sub_domain}"
            )

            return {
                "messages": [AIMessage(content=flow_message)],
                "workflow": "flow",
                "flow_component": {
                    "type": "product_customization",
                    "product_id": product_id,
                    "endpoint": f"/flows/product/{product_id}/{sub_domain}"
                }
            }

        elif flow_action == "checkout":
            # Generate checkout flow
            sub_domain = state.get("sub_domain")

            flow_message = (
                "Tap below to complete your order:\n"
                f"Flow endpoint: /flows/checkout/{sub_domain}"
            )

            return {
                "messages": [AIMessage(content=flow_message)],
                "workflow": "flow",
                "flow_component": {
                    "type": "checkout",
                    "endpoint": f"/flows/checkout/{sub_domain}"
                }
            }

        else:
            return {
                "messages": [AIMessage(content="Unknown flow action.")],
                "workflow": "conversation"
            }

    except Exception as e:
        logger.error(f"Flow handler node error: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="Sorry, I had trouble preparing the customization form.")],
            "workflow": "conversation"
        }
