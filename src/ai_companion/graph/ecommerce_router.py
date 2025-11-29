"""
E-commerce intent router.
Detects e-commerce intents from user messages and interactive responses.
"""
import logging
import re
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage

from ai_companion.graph.state import AICompanionState

logger = logging.getLogger(__name__)


class EcommerceRouter:
    """Router for detecting e-commerce intents"""

    # E-commerce keywords
    CATALOG_KEYWORDS = [
        "menu", "catalog", "products", "browse", "shop", "shopping",
        "what do you have", "what's available", "show me", "ver menu",
        "carta", "productos", "ver productos", "que tienen"
    ]

    CART_KEYWORDS = [
        "cart", "carrito", "my order", "mi pedido", "see cart",
        "ver carrito", "what's in my cart", "show cart"
    ]

    CHECKOUT_KEYWORDS = [
        "checkout", "pay", "pagar", "complete order", "finish order",
        "finalizar", "completar pedido", "place order"
    ]

    ORDER_KEYWORDS = [
        "order", "pedido", "buy", "comprar", "i want", "quiero",
        "i'd like", "me gustaría"
    ]

    @staticmethod
    def detect_intent(state: AICompanionState) -> Optional[str]:
        """
        Detect e-commerce intent from user message or interactive response.

        Args:
            state: Current conversation state

        Returns:
            Intent string: browse_catalog|view_product|view_cart|checkout|None
        """
        try:
            messages = state.get("messages", [])
            if not messages:
                return None

            last_message = messages[-1]

            # Check if it's a human message
            if not isinstance(last_message, HumanMessage):
                return None

            message_text = last_message.content.lower()

            # Check for interactive button/list responses (prefixed format)
            # Format: "[List selection: Category Name (ID: cat:123)]"
            # Format: "[Button: Customize Order (ID: customize:prod_123)]"

            # Check for list selections
            list_match = re.search(r'\[list selection:.*?\(id:\s*([^\)]+)\)\]', message_text, re.IGNORECASE)
            if list_match:
                selection_id = list_match.group(1).strip()
                return EcommerceRouter._parse_selection_id(selection_id, state)

            # Check for button presses
            button_match = re.search(r'\[button:.*?\(id:\s*([^\)]+)\)\]', message_text, re.IGNORECASE)
            if button_match:
                button_id = button_match.group(1).strip()
                return EcommerceRouter._parse_button_id(button_id, state)

            # Check for text-based intents
            if any(keyword in message_text for keyword in EcommerceRouter.CATALOG_KEYWORDS):
                return "browse_catalog"

            if any(keyword in message_text for keyword in EcommerceRouter.CART_KEYWORDS):
                return "view_cart"

            if any(keyword in message_text for keyword in EcommerceRouter.CHECKOUT_KEYWORDS):
                return "checkout"

            # Check if mentioning specific product/order
            if any(keyword in message_text for keyword in EcommerceRouter.ORDER_KEYWORDS):
                # Could be ordering intent, but need more context
                # For now, show catalog
                return "browse_catalog"

            return None

        except Exception as e:
            logger.error(f"Error detecting e-commerce intent: {e}", exc_info=True)
            return None

    @staticmethod
    def _parse_selection_id(selection_id: str, state: AICompanionState) -> Optional[str]:
        """
        Parse selection ID from interactive list response.

        Args:
            selection_id: ID from list selection (e.g., "cat:123", "prod:456")
            state: Current conversation state

        Returns:
            Intent and updates state with context
        """
        try:
            # Category selection
            if selection_id.startswith("cat:"):
                category_id = selection_id[4:]  # Remove "cat:" prefix
                state["selected_category"] = category_id
                state["ecommerce_intent"] = "view_category"
                return "view_category"

            # Product selection
            if selection_id.startswith("prod:"):
                product_id = selection_id[5:]  # Remove "prod:" prefix
                state["product_context"] = {"product_id": product_id}
                state["ecommerce_intent"] = "view_product"
                return "view_product"

            return None

        except Exception as e:
            logger.error(f"Error parsing selection ID: {e}", exc_info=True)
            return None

    @staticmethod
    def _parse_button_id(button_id: str, state: AICompanionState) -> Optional[str]:
        """
        Parse button ID from interactive button response.

        Args:
            button_id: ID from button press (e.g., "customize:prod_123", "checkout:now")
            state: Current conversation state

        Returns:
            Intent and updates state with context
        """
        try:
            # Customize product button
            if button_id.startswith("customize:"):
                product_id = button_id.split(":")[1]
                state["product_context"] = {"product_id": product_id}
                state["flow_action"] = "add_to_cart"
                state["ecommerce_intent"] = "customize_product"
                return "customize_product"

            # Add to cart button (simple products)
            if button_id.startswith("add_cart:"):
                parts = button_id.split(":")
                product_id = parts[1]
                quantity = int(parts[2]) if len(parts) > 2 else 1
                state["product_context"] = {
                    "product_id": product_id,
                    "quantity": quantity
                }
                state["ecommerce_intent"] = "add_to_cart"
                return "add_to_cart"

            # Back to catalog
            if button_id.startswith("back:catalog"):
                state["selected_category"] = None
                state["product_context"] = {}
                return "browse_catalog"

            # Back to cart
            if button_id.startswith("back:cart"):
                return "view_cart"

            # Browse catalog
            if button_id.startswith("browse:catalog"):
                state["selected_category"] = None
                return "browse_catalog"

            # Checkout
            if button_id.startswith("checkout:"):
                state["ecommerce_intent"] = "checkout"
                return "checkout"

            # Clear cart
            if button_id.startswith("clear:cart"):
                state["cart_data"] = {"items": []}
                return "view_cart"

            # Delivery/pickup selection
            if button_id.startswith("delivery:") or button_id.startswith("pickup:"):
                delivery_type = button_id.split(":")[0]
                state["order_data"] = state.get("order_data", {})
                state["order_data"]["type"] = delivery_type
                state["ecommerce_intent"] = "checkout_address"
                return "checkout_address"

            return None

        except Exception as e:
            logger.error(f"Error parsing button ID: {e}", exc_info=True)
            return None

    @staticmethod
    def should_route_to_ecommerce(state: AICompanionState) -> bool:
        """
        Check if message should be routed to e-commerce workflow.

        Args:
            state: Current conversation state

        Returns:
            True if should route to e-commerce
        """
        intent = EcommerceRouter.detect_intent(state)
        return intent is not None

    @staticmethod
    def get_ecommerce_workflow(intent: str) -> str:
        """
        Map intent to workflow node.

        Args:
            intent: Detected e-commerce intent

        Returns:
            Workflow node name
        """
        intent_to_workflow = {
            "browse_catalog": "catalog",
            "view_category": "catalog",
            "view_product": "product_detail",
            "customize_product": "flow_handler",
            "add_to_cart": "cart",
            "view_cart": "cart",
            "checkout": "checkout",
            "checkout_address": "checkout"
        }

        return intent_to_workflow.get(intent, "conversation")
