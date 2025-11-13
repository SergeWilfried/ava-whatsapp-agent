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
    """Create a list interactive component (up to 10 rows per section).

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

    # Format sections and rows
    formatted_sections = []
    for section in sections[:10]:  # Max 10 sections
        formatted_rows = [
            {
                "id": row["id"],
                "title": row["title"][:24],  # Max 24 chars
                "description": row.get("description", "")[:72]  # Max 72 chars
            }
            for row in section.get("rows", [])[:10]  # Max 10 rows per section
        ]

        if formatted_rows:
            formatted_sections.append({
                "title": section["title"][:24],
                "rows": formatted_rows
            })

    component["action"] = {
        "button": button_text[:20],
        "sections": formatted_sections
    }

    return component


def create_menu_list_from_restaurant_menu(restaurant_menu: Dict) -> Dict:
    """Create a WhatsApp list component from restaurant menu data.

    Args:
        restaurant_menu: Restaurant menu dict with categories and items

    Returns:
        Interactive list component
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

    for category, items in restaurant_menu.items():
        icon = category_icons.get(category, "•")
        rows = []

        for idx, item in enumerate(items[:10]):  # Max 10 items per section
            rows.append({
                "id": f"{category}_{idx}",
                "title": f"{icon} {item['name'][:20]}",
                "description": f"${item['price']:.2f} - {item['description'][:50]}"
            })

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
            {"id": "cancel_order", "title": "Cancel ❌"}
        ],
        header_text="Order Confirmation"
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
        header_text="Quick Actions"
    )
