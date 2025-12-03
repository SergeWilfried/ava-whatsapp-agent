"""Handler for shopping cart interactive button/list replies from WhatsApp."""
import logging
from typing import Dict, Optional, Tuple
from ai_companion.graph.state import AICompanionState
from ai_companion.modules.cart import OrderStage

logger = logging.getLogger(__name__)


class CartInteractionHandler:
    """Handles interactive component replies related to shopping cart."""

    # Button ID patterns for cart operations
    CART_BUTTON_IDS = {
        "continue_shopping": "continue_shopping",
        "view_cart": "view_cart",
        "checkout": "checkout",
        "clear_cart": "clear_cart",
        "view_menu": "view_menu",

        # Size selections
        "size_small": "size_small",
        "size_medium": "size_medium",
        "size_large": "size_large",

        # Delivery methods
        "delivery": "delivery",
        "pickup": "pickup",
        "dine_in": "dine_in",

        # Payment methods
        "credit_card": "credit_card",
        "debit_card": "debit_card",
        "mobile_payment": "mobile_payment",
        "cash": "cash",

        # Order confirmation
        "confirm_order": "confirm_order",
        "edit_order": "edit_order",
        "cancel_order": "cancel_order",

        # Post-order actions
        "track_order": "track_order",
        "contact_support": "contact_support",
        "contact_us": "contact_us",
        "new_order": "new_order",
    }

    @staticmethod
    def is_cart_interaction(interaction_id: str) -> bool:
        """Check if interaction is cart-related.

        Args:
            interaction_id: The ID from interactive button or list reply

        Returns:
            True if cart-related, False otherwise
        """
        # Check direct button matches
        if interaction_id in CartInteractionHandler.CART_BUTTON_IDS.values():
            return True

        # Check category selection pattern (e.g., "category_pizzas", "category_burgers")
        if interaction_id.startswith("category_"):
            return True

        # Check menu item pattern (e.g., "pizzas_0", "burgers_1")
        if "_" in interaction_id:
            parts = interaction_id.split("_")
            if len(parts) == 2:
                category, idx = parts
                if category in ["pizzas", "burgers", "sides", "drinks", "desserts"]:
                    try:
                        int(idx)
                        return True
                    except ValueError:
                        pass

        # Check add pattern for carousel follow-up buttons (e.g., "add_pizzas_0")
        if interaction_id.startswith("add_"):
            parts = interaction_id.split("_")
            if len(parts) == 3:  # add_category_index
                return True

        # Check extras pattern
        extras = ["extra_cheese", "mushrooms", "olives", "pepperoni", "bacon",
                  "chicken", "gluten_free", "vegan_cheese", "extra_sauce", "extra_toppings"]
        if interaction_id in extras:
            return True

        return False

    @staticmethod
    def parse_interaction(
        interaction_type: str,
        interaction_data: Dict
    ) -> Tuple[str, str, str]:
        """Parse interaction data from WhatsApp.

        Args:
            interaction_type: "button_reply" or "list_reply"
            interaction_data: Interactive component data from webhook

        Returns:
            Tuple of (action, interaction_id, title/label)
        """
        if interaction_type == "button_reply":
            button_id = interaction_data.get("button_reply", {}).get("id", "")
            button_title = interaction_data.get("button_reply", {}).get("title", "")
            return "button", button_id, button_title

        elif interaction_type == "list_reply":
            list_id = interaction_data.get("list_reply", {}).get("id", "")
            list_title = interaction_data.get("list_reply", {}).get("title", "")
            return "list", list_id, list_title

        return "unknown", "", ""

    @staticmethod
    def determine_cart_action(
        interaction_id: str,
        current_stage: Optional[str] = None
    ) -> Tuple[str, Dict]:
        """Determine what cart action to take based on interaction.

        Args:
            interaction_id: ID from interactive reply
            current_stage: Current order stage

        Returns:
            Tuple of (node_name, state_updates)
        """
        # Category selection -> show carousel
        if interaction_id.startswith("category_"):
            category = interaction_id.replace("category_", "")
            return "view_category_carousel", {"selected_category": category}

        # Add item from carousel follow-up buttons (e.g., "add_pizzas_0")
        if interaction_id.startswith("add_"):
            parts = interaction_id.split("_")
            if len(parts) == 3:  # add_category_index
                category, idx = parts[1], parts[2]
                menu_item_id = f"{category}_{idx}"
                return "add_to_cart", {
                    "current_item": {"menu_item_id": menu_item_id},
                    "order_stage": OrderStage.SELECTING.value
                }

        # Menu item selection -> add to cart
        if "_" in interaction_id and any(
            interaction_id.startswith(cat) for cat in ["pizzas", "burgers", "sides", "drinks", "desserts"]
        ):
            return "add_to_cart", {
                "current_item": {"menu_item_id": interaction_id},
                "order_stage": OrderStage.SELECTING.value
            }

        # Cart navigation buttons
        if interaction_id == "view_cart":
            return "view_cart", {}

        if interaction_id == "continue_shopping":
            return "show_menu", {"use_interactive_menu": True}

        if interaction_id == "view_menu":
            return "view_menu", {}

        if interaction_id == "checkout":
            return "checkout", {}

        if interaction_id == "clear_cart":
            return "clear_cart", {}

        # Size selection
        if interaction_id.startswith("size_"):
            return "handle_size", {}

        # Extras selection
        extras = ["extra_cheese", "mushrooms", "olives", "pepperoni", "bacon",
                  "chicken", "gluten_free", "vegan_cheese", "extra_sauce", "extra_toppings"]
        if interaction_id in extras:
            return "handle_extras", {}

        # Delivery method
        if interaction_id in ["delivery", "pickup", "dine_in"]:
            return "handle_delivery_method", {}

        # Payment method
        if interaction_id in ["credit_card", "debit_card", "mobile_payment", "cash"]:
            return "handle_payment_method", {}

        # Order confirmation
        if interaction_id == "confirm_order":
            return "confirm_order", {}

        if interaction_id == "edit_order":
            return "view_cart", {}

        if interaction_id == "cancel_order":
            return "clear_cart", {}

        # Post-order actions
        if interaction_id == "new_order":
            return "show_menu", {"use_interactive_menu": True}

        if interaction_id == "track_order":
            return "conversation", {}  # Let AI handle tracking inquiries

        if interaction_id == "contact_support" or interaction_id == "contact_us":
            return "conversation", {}  # Let AI handle support inquiries

        # Default: conversation
        return "conversation", {}

    @staticmethod
    def create_text_representation(
        interaction_type: str,
        interaction_id: str,
        title: str
    ) -> str:
        """Create a text representation of the interaction for the AI.

        This helps maintain conversation context when users interact with buttons.

        Args:
            interaction_type: "button" or "list"
            interaction_id: Interaction ID
            title: Button/list item title

        Returns:
            Natural language representation
        """
        # Category selection
        if interaction_id.startswith("category_"):
            category = interaction_id.replace("category_", "")
            return f"Show me the {category}"

        # Add item from carousel buttons
        if interaction_id.startswith("add_"):
            return f"I'd like to order the {title.replace('Add ', '')}"

        # Menu item selections
        if "_" in interaction_id and any(
            interaction_id.startswith(cat) for cat in ["pizzas", "burgers", "sides", "drinks", "desserts"]
        ):
            return f"I'd like to order the {title}"

        # Size selections
        if interaction_id.startswith("size_"):
            size = interaction_id.replace("size_", "").title()
            return f"I'll take the {size} size"

        # Extras
        extras_map = {
            "extra_cheese": "add extra cheese",
            "mushrooms": "add mushrooms",
            "olives": "add olives",
            "pepperoni": "add pepperoni",
            "bacon": "add bacon",
            "chicken": "add grilled chicken",
            "gluten_free": "make it gluten-free",
            "vegan_cheese": "use vegan cheese",
            "extra_sauce": "add extra sauce",
            "extra_toppings": "add extra toppings"
        }
        if interaction_id in extras_map:
            return f"Please {extras_map[interaction_id]}"

        # Cart actions
        cart_actions = {
            "view_cart": "Show me my cart",
            "continue_shopping": "I want to add more items",
            "checkout": "I'm ready to checkout",
            "clear_cart": "Clear my cart",
            "view_menu": "Show me the menu"
        }
        if interaction_id in cart_actions:
            return cart_actions[interaction_id]

        # Delivery methods
        delivery_map = {
            "delivery": "I'd like delivery",
            "pickup": "I'll pick it up",
            "dine_in": "I'll dine in"
        }
        if interaction_id in delivery_map:
            return delivery_map[interaction_id]

        # Payment methods
        payment_map = {
            "credit_card": "I'll pay by credit card",
            "debit_card": "I'll pay by debit card",
            "mobile_payment": "I'll use mobile payment",
            "cash": "I'll pay cash"
        }
        if interaction_id in payment_map:
            return payment_map[interaction_id]

        # Order confirmation actions
        confirmation_map = {
            "confirm_order": "Yes, confirm my order",
            "edit_order": "I want to edit my order",
            "cancel_order": "Cancel my order"
        }
        if interaction_id in confirmation_map:
            return confirmation_map[interaction_id]

        # Post-order actions
        post_order_map = {
            "track_order": "I want to track my order",
            "contact_support": "I need help with my order",
            "contact_us": "I need to contact support",
            "new_order": "I want to place a new order"
        }
        if interaction_id in post_order_map:
            return post_order_map[interaction_id]

        # Default: use title
        return title


def process_cart_interaction(
    interaction_type: str,
    interaction_data: Dict,
    current_state: Optional[Dict] = None
) -> Tuple[str, Dict, str]:
    """Process cart interaction and determine routing.

    Args:
        interaction_type: "button_reply" or "list_reply"
        interaction_data: Interactive component data
        current_state: Current graph state dict

    Returns:
        Tuple of (node_to_call, state_updates, text_representation)
    """
    handler = CartInteractionHandler()

    # Parse interaction
    action_type, interaction_id, title = handler.parse_interaction(
        interaction_type, interaction_data
    )

    logger.info(f"Cart interaction: type={interaction_type}, id={interaction_id}, title={title}")

    # Check if this is cart-related
    if not handler.is_cart_interaction(interaction_id):
        return "conversation", {}, title

    # Determine action
    current_stage = current_state.get("order_stage") if current_state else None
    node_name, state_updates = handler.determine_cart_action(interaction_id, current_stage)

    # Create text representation
    text_repr = handler.create_text_representation(action_type, interaction_id, title)

    logger.info(f"Routing to node: {node_name}, text: {text_repr}")

    return node_name, state_updates, text_repr
