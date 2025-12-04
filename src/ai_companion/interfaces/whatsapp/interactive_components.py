"""Helper functions for creating WhatsApp interactive components."""
from typing import List, Dict, Optional


def create_button_component(
    body_text: str,
    buttons: List[Dict[str, str]],
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None
) -> Dict:
    """Create a button interactive component (up to 3 buttons).

    Args:
        body_text: Main message text (required, max 1024 chars)
        buttons: List of button dicts with 'id' and 'title' keys (max 3 buttons)
        header_text: Optional header text (max 60 chars)
        footer_text: Optional footer text (max 60 chars)

    Returns:
        Interactive component dict ready for WhatsApp API

    Example:
        create_button_component(
            "Would you like delivery or pickup?",
            [
                {"id": "delivery", "title": "Delivery 🚗"},
                {"id": "pickup", "title": "Pickup 🏃"},
            ]
        )
    """
    component = {
        "type": "button",
        "body": {"text": body_text[:1024]}
    }

    if header_text:
        component["header"] = {"type": "text", "text": header_text[:60]}

    if footer_text:
        component["footer"] = {"text": footer_text[:60]}

    # Format buttons (max 3)
    component["action"] = {
        "buttons": [
            {
                "type": "reply",
                "reply": {
                    "id": btn["id"],
                    "title": btn["title"][:20]  # Max 20 chars for button title
                }
            }
            for btn in buttons[:3]
        ]
    }

    return component


def create_list_component(
    body_text: str,
    sections: List[Dict],
    button_text: str = "View Menu",
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None
) -> Dict:
    """Create a list interactive component.

    IMPORTANT: WhatsApp limits list messages to:
    - Up to 10 sections
    - Up to 10 rows TOTAL across ALL sections combined
    - Each row: title max 24 chars, description max 72 chars

    Args:
        body_text: Main message text (required, max 1024 chars)
        sections: List of section dicts with 'title' and 'rows' keys
        button_text: Text for the list button (max 20 chars)
        header_text: Optional header text (max 60 chars)
        footer_text: Optional footer text (max 60 chars)

    Returns:
        Interactive component dict ready for WhatsApp API

    Example:
        create_list_component(
            "Check out our menu!",
            [
                {
                    "title": "Pizzas",
                    "rows": [
                        {"id": "pizza_1", "title": "Margherita", "description": "$12.99"},
                        {"id": "pizza_2", "title": "Pepperoni", "description": "$14.99"},
                    ]
                },
                {
                    "title": "Burgers",
                    "rows": [
                        {"id": "burger_1", "title": "Cheeseburger", "description": "$10.99"},
                    ]
                }
            ],
            button_text="View Menu"
        )
    """
    component = {
        "type": "list",
        "body": {"text": body_text[:1024]}
    }

    if header_text:
        component["header"] = {"type": "text", "text": header_text[:60]}

    if footer_text:
        component["footer"] = {"text": footer_text[:60]}

    # Format sections and rows with TOTAL row limit of 10
    formatted_sections = []
    total_rows = 0
    max_total_rows = 10

    for section in sections[:10]:  # Max 10 sections
        if total_rows >= max_total_rows:
            break

        section_rows = section.get("rows", [])
        remaining_rows = max_total_rows - total_rows

        formatted_rows = [
            {
                "id": row["id"],
                "title": row["title"][:24],  # Max 24 chars
                "description": row.get("description", "")[:72]  # Max 72 chars
            }
            for row in section_rows[:remaining_rows]  # Limit to remaining quota
        ]

        if formatted_rows:
            formatted_sections.append({
                "title": section["title"][:24],
                "rows": formatted_rows
            })
            total_rows += len(formatted_rows)

    component["action"] = {
        "button": button_text[:20],
        "sections": formatted_sections
    }

    return component


def create_menu_list_from_restaurant_menu(restaurant_menu: Dict, max_items: int = 10) -> Dict:
    """Create a WhatsApp list component from restaurant menu data.

    IMPORTANT: WhatsApp limits list messages to 10 rows total.
    This function automatically limits items to fit within this constraint.

    Args:
        restaurant_menu: Restaurant menu dict with categories and items
        max_items: Maximum total items to show (default 10, WhatsApp's limit)

    Returns:
        Interactive list component with up to 10 items total

    Note:
        For large menus, consider creating multiple list messages or
        using category-specific menus (e.g., "View Pizzas", "View Burgers")
    """
    sections = []

    # Map emoji icons for each category
    category_icons = {
        "pizzas": "🍕",
        "burgers": "🍔",
        "sides": "🍟",
        "drinks": "🥤",
        "desserts": "🍰"
    }

    total_items = 0

    # Distribute items across categories, prioritizing first categories
    for category, items in restaurant_menu.items():
        if total_items >= max_items:
            break

        icon = category_icons.get(category, "•")
        rows = []

        # Calculate how many items we can add from this category
        remaining_slots = max_items - total_items
        items_to_add = min(len(items), remaining_slots)

        for idx in range(items_to_add):
            item = items[idx]
            rows.append({
                "id": f"{category}_{idx}",
                "title": f"{icon} {item['name'][:18]}",  # Leave room for emoji
                "description": f"${item['basePrice']:.2f} - {item['description'][:50]}"
            })
            total_items += 1

        if rows:
            sections.append({
                "title": category.title(),
                "rows": rows
            })

    return create_list_component(
        "Browse our delicious menu! 😋",
        sections,
        button_text="View Menu",
        footer_text="Tap an item to add to your order"
    )


def create_category_menu_buttons(available_categories: List[str] = None) -> Dict:
    """Create buttons for selecting menu categories.

    Use this when the full menu has too many items (>10) to fit in one list.
    Users can select a category, then see items from that category only.

    Args:
        available_categories: List of category names to show (default: all)

    Returns:
        Interactive button component

    Example:
        create_category_menu_buttons(["pizzas", "burgers", "sides"])
    """
    if available_categories is None:
        available_categories = ["pizzas", "burgers", "sides"]

    # Map categories to display names with emojis
    category_display = {
        "pizzas": "🍕 Pizzas",
        "burgers": "🍔 Burgers",
        "sides": "🍟 Sides",
        "drinks": "🥤 Drinks",
        "desserts": "🍰 Desserts"
    }

    buttons = [
        {"id": f"category_{cat}", "title": category_display.get(cat, cat.title())}
        for cat in available_categories[:3]  # Max 3 buttons
    ]

    return create_button_component(
        "What would you like to browse?",
        buttons,
        header_text="Catégories du menu"
    )


def create_category_specific_menu(category: str, items: List[Dict]) -> Dict:
    """Create a menu list for a specific category.

    Args:
        category: Category name (e.g., "pizzas")
        items: List of menu items in this category

    Returns:
        Interactive list component with up to 10 items from the category
    """
    category_icons = {
        "pizzas": "🍕",
        "burgers": "🍔",
        "sides": "🍟",
        "drinks": "🥤",
        "desserts": "🍰"
    }

    icon = category_icons.get(category, "•")
    rows = []

    for idx, item in enumerate(items[:10]):  # Max 10 items
        rows.append({
            "id": f"{category}_{idx}",
            "title": f"{icon} {item['name'][:18]}",
            "description": f"${item['basePrice']:.2f} - {item['description'][:50]}"
        })

    return create_list_component(
        f"Choose from our {category.title()}:",
        [{"title": category.title(), "rows": rows}],
        button_text="Select Item",
        footer_text="Tap to add to cart"
    )


def create_order_confirmation_buttons(order_total: float) -> Dict:
    """Create confirmation buttons for an order.

    Args:
        order_total: Total order amount

    Returns:
        Interactive button component
    """
    return create_button_component(
        f"Your order total is ${order_total:.2f}. How would you like to receive it?",
        [
            {"id": "confirm_delivery", "title": "Delivery 🚗"},
            {"id": "confirm_pickup", "title": "Pickup 🏃"},
            {"id": "cancel_order", "title": "Annuler ❌"}
        ],
        header_text="Confirmation de commande"
    )


def create_quick_actions_buttons() -> Dict:
    """Create quick action buttons for common restaurant tasks.

    Returns:
        Interactive button component
    """
    return create_button_component(
        "What would you like to do?",
        [
            {"id": "view_menu", "title": "📋 View Menu"},
            {"id": "track_order", "title": "📦 Track Order"},
            {"id": "contact_us", "title": "📞 Contact Us"}
        ],
        header_text="Bonjour, Comment Puis je vous aider aujourdhui ?"
    )


def create_item_added_buttons(item_name: str, cart_total: float, item_count: int) -> Dict:
    """Create buttons after adding item to cart.

    Args:
        item_name: Name of item that was added
        cart_total: Current cart total
        item_count: Number of items in cart

    Returns:
        Interactive button component
    """
    return create_button_component(
        f"Added {item_name} to your cart!",
        [
            {"id": "continue_shopping", "title": "➕ Ajouter"},
            {"id": "view_cart", "title": "🛒 Voir Mon Panier"},
            {"id": "checkout", "title": "✅ Commander"}
        ],
        footer_text=f"{item_count} articles • ${cart_total:.2f}"
    )


def create_cart_view_buttons(cart_total: float, item_count: int) -> Dict:
    """Create buttons for cart view.

    Args:
        cart_total: Current cart total
        item_count: Number of items in cart

    Returns:
        Interactive button component
    """
    return create_button_component(
        f"Votre panier a {item_count} article{'s' if item_count != 1 else ''}",
        [
            {"id": "checkout", "title": "✅ Commander"},
            {"id": "continue_shopping", "title": "➕ Ajouter"},
            {"id": "clear_cart", "title": "🗑️ Vider le Panier"}
        ],
        header_text=f"Total: ${cart_total:.2f}"
    )


def create_size_selection_buttons(item_name: str, base_price: float) -> Dict:
    """Create size selection buttons for menu items.

    Args:
        item_name: Name of the menu item
        base_price: Base price (medium size)

    Returns:
        Interactive button component
    """
    small_price = base_price * 0.8
    large_price = base_price * 1.3

    return create_button_component(
        "Choose your size:",
        [
            {"id": "size_small", "title": f"Small ${small_price:.2f}"},
            {"id": "size_medium", "title": f"Medium ${base_price:.2f}"},
            {"id": "size_large", "title": f"Large ${large_price:.2f}"}
        ],
        header_text=item_name
    )


def create_extras_list(category: str = "pizza") -> Dict:
    """Create list of extras/toppings for customization.

    Args:
        category: Menu item category (pizza, burger, etc.)

    Returns:
        Interactive list component
    """
    if category == "pizza":
        sections = [
            {
                "title": "🧀 Cheese & Protein",
                "rows": [
                    {"id": "extra_cheese", "title": "Extra Cheese", "description": "+$2.00"},
                    {"id": "pepperoni", "title": "Pepperoni", "description": "+$2.50"},
                    {"id": "chicken", "title": "Grilled Chicken", "description": "+$3.00"},
                    {"id": "bacon", "title": "Bacon", "description": "+$2.50"}
                ]
            },
            {
                "title": "🥬 Veggies",
                "rows": [
                    {"id": "mushrooms", "title": "Mushrooms", "description": "+$1.50"},
                    {"id": "olives", "title": "Black Olives", "description": "+$1.00"},
                    {"id": "extra_toppings", "title": "Mixed Veggies", "description": "+$1.50"}
                ]
            },
            {
                "title": "🌟 Special Options",
                "rows": [
                    {"id": "gluten_free", "title": "Gluten-Free Crust", "description": "+$3.00"},
                    {"id": "vegan_cheese", "title": "Vegan Cheese", "description": "+$2.50"},
                    {"id": "extra_sauce", "title": "Extra Sauce", "description": "Free"}
                ]
            }
        ]
    elif category == "burger":
        sections = [
            {
                "title": "🧀 Add-ons",
                "rows": [
                    {"id": "extra_cheese", "title": "Extra Cheese", "description": "+$2.00"},
                    {"id": "bacon", "title": "Bacon", "description": "+$2.50"},
                    {"id": "mushrooms", "title": "Sautéed Mushrooms", "description": "+$1.50"}
                ]
            }
        ]
    else:
        sections = [
            {
                "title": "Extras",
                "rows": [
                    {"id": "extra_toppings", "title": "Extra Toppings", "description": "+$1.50"}
                ]
            }
        ]

    return create_list_component(
        "Customize your order with extras:",
        sections,
        button_text="Add Extras",
        footer_text="Tap to add, or skip to continue"
    )


def create_delivery_method_buttons() -> Dict:
    """Create delivery method selection buttons.

    Returns:
        Interactive button component
    """
    return create_button_component(
        "Comment souhaitez-vous recevoir votre commande ?",
        [
            {"id": "delivery", "title": "🚗 Livraison"},
            {"id": "pickup", "title": "🏃 Retrait"},
            {"id": "dine_in", "title": "🍽️ Sur Place"}
        ],
        header_text="Methode de Livraison"
    )


def create_payment_method_list() -> Dict:
    """Create payment method selection list.

    Returns:
        Interactive list component
    """
    sections = [
        {
            "title": "💳 Payer maintenant ",
            "rows": [
                {"id": "credit_card", "title": "Carte Bancaire", "description": "Visa, Mastercard, Amex"},
                {"id": "debit_card", "title": "Wave", "description": "Wave Mobile Money"},
                {"id": "p2p", "title": "PII", "description": "P2P"},
                {"id": "mobile_payment", "title": "Mobile Money", "description": "Orane Money, MoMo"}
            ]
        },
        {
            "title": "💵 Cash",
            "rows": [
                {"id": "cash", "title": "Paiement à la livraison", "description": " Payez à la réception"}
            ]
        }
    ]

    return create_list_component(
        "Choisissez votre mode de paiement :",
        sections,
        button_text="Payer",
        header_text="Paiement"
    )


def create_order_details_message(order_data: Dict) -> Dict:
    """Create WhatsApp order details interactive message for payment.

    Note: WhatsApp Cloud API only supports 'button', 'list', 'product', and 'product_list' types.
    The 'order_details' type is not supported, so we use buttons for order confirmation instead.

    Args:
        order_data: Order information dict with items, totals, etc.

    Returns:
        Interactive button component for order confirmation
    """
    # Build order summary text
    items_list = []
    for item in order_data.get("items", []):
        size_text = f" ({item.get('size', 'medium')})" if item.get('size') else ""
        extras_text = ""
        if item.get('extras'):
            extras_text = f" + {', '.join(item['extras'])}"
        items_list.append(f"• {item['name']}{size_text}{extras_text} x{item['quantity']} - ${item['item_total']:.2f}")

    items_text = "\n".join(items_list)

    subtotal = order_data.get("subtotal", 0.0)
    tax = order_data.get("tax_amount", 0.0)
    delivery_fee = order_data.get("delivery_fee", 0.0)
    total = order_data.get("total", 0.0)

    payment_method = order_data.get("payment_method", "Cash on Delivery")
    delivery_method = order_data.get("delivery_method", "Delivery")

    order_summary = f"""📦 Votre Commande:

{items_text}

💰 Récapitulatif de la commande :
Sous-total : ${subtotal:.2f} FCFA
Taxes : ${tax:.2f} FCFA
Livraison : ${delivery_fee:.2f} FCFA
────────────────────────────────────
Total : ${total:.2f} FCFA

🚚 Livraison: {delivery_method}
💳 Paiment: {payment_method}"""

    # Create confirmation buttons
    return create_button_component(
        order_summary,
        [
            {"id": "confirm_order", "title": "✅ Confirmer"},
            {"id": "edit_order", "title": "✏️ Modifier"},
            {"id": "cancel_order", "title": "❌ Annuler"}
        ],
        header_text=f"Commande #{order_data.get('order_id', 'unknown')[:8]}",
        footer_text=f"Temps Est.: {order_data.get('estimated_time', '30-45 min')}"
    )


def create_category_selection_list() -> Dict:
    """Create interactive list for selecting menu categories.

    Shows all menu categories with item counts for users to browse.

    Returns:
        Interactive list component for category selection

    Example:
        >>> component = create_category_selection_list()
        >>> # Use in send_response with message_type="interactive_list"
    """
    from ai_companion.core.schedules import RESTAURANT_MENU

    # Map categories to display info
    category_info = {
        "pizzas": {"emoji": "🍕", "name": "Pizzas"},
        "burgers": {"emoji": "🍔", "name": "Burgers"},
        "sides": {"emoji": "🍟", "name": "Sides"},
        "drinks": {"emoji": "🥤", "name": "Drinks"},
        "desserts": {"emoji": "🍰", "name": "Desserts"}
    }

    # Build rows from actual menu
    rows = []
    for category, items in RESTAURANT_MENU.items():
        info = category_info.get(category, {"emoji": "•", "name": category.title()})
        item_count = len(items)

        rows.append({
            "id": f"category_{category}",
            "title": f"{info['emoji']} {info['name']}",
            "description": f"{item_count} items available"
        })

    return create_list_component(
        body_text="Que souhaitez-vous commander aujourdhui ? 😋",
        sections=[{
            "title": "Menu Categories",
            "rows": rows
        }],
        button_text="Parcourir le menu",
        header_text="Notre Menu",
        footer_text="Tap to see items"
    )


def create_order_status_message(order_id: str, status: str, message: str) -> Dict:
    """Create order status tracking message.

    Note: WhatsApp Cloud API only supports 'button', 'list', 'product', and 'product_list' types.
    The 'order_status' type is not supported, so we use buttons for order tracking instead.

    Args:
        order_id: Order reference ID
        status: Order status (pending, processing, completed, etc.)
        message: Status message to display

    Returns:
        Interactive button component for order status
    """
    status_emojis = {
        "pending": "⏳",
        "confirmed": "✅",
        "preparing": "👨‍🍳",
        "ready": "🎉",
        "out_for_delivery": "🚗",
        "delivered": "✅",
        "completed": "✅",
        "cancelled": "❌"
    }

    emoji = status_emojis.get(status, "📦")

    return create_button_component(
        f"{emoji} {message}",
        [
            {"id": "track_order", "title": "📍 Suivre Commande"},
            {"id": "contact_support", "title": "💬 Nous Contacter"},
            {"id": "new_order", "title": "🛒 Nouvelle Commande"}
        ],
        header_text=f"Commande #{order_id[:8]}",
        footer_text=f"Status: {status.replace('_', ' ').title()}"
    )
