"""Updated interactive components with API support.

This module provides backward-compatible interactive component creators
that work with both mock data and API data (presentations and modifiers).
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def create_button_component(
    body_text: str,
    buttons: List[Dict[str, str]],
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None,
) -> Dict:
    """Create a button interactive component (up to 3 buttons)."""
    component = {"type": "button", "body": {"text": body_text[:1024]}}

    if header_text:
        component["header"] = {"type": "text", "text": header_text[:60]}

    if footer_text:
        component["footer"] = {"text": footer_text[:60]}

    # Format buttons (max 3)
    component["action"] = {
        "buttons": [
            {
                "type": "reply",
                "reply": {"id": btn["id"], "title": btn["title"][:20]},
            }
            for btn in buttons[:3]
        ]
    }

    return component


def create_list_component(
    body_text: str,
    sections: List[Dict],
    button_text: str = "Afficher le menu",
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None,
) -> Dict:
    """Create a list interactive component."""
    component = {"type": "list", "body": {"text": body_text[:1024]}}

    if header_text:
        component["header"] = {"type": "text", "text": header_text[:60]}

    if footer_text:
        component["footer"] = {"text": footer_text[:60]}

    # Process sections and enforce row limit
    total_rows = sum(len(section.get("rows", [])) for section in sections)

    if total_rows > 10:
        logger.warning(
            f"Total rows ({total_rows}) exceeds WhatsApp limit of 10, truncating"
        )

    processed_sections = []
    remaining_rows = 10

    for section in sections[:10]:  # Max 10 sections
        if remaining_rows <= 0:
            break

        rows = section.get("rows", [])[:remaining_rows]
        processed_rows = [
            {
                "id": row["id"],
                "title": row["title"][:24],
                "description": row.get("description", "")[:72],
            }
            for row in rows
        ]

        if processed_rows:
            processed_sections.append(
                {"title": section.get("title", "")[:24], "rows": processed_rows}
            )
            remaining_rows -= len(processed_rows)

    component["action"] = {
        "button": button_text[:20],
        "sections": processed_sections,
    }

    return component


def create_product_list(
    products: List[Dict],
    category_name: str,
    header_text: Optional[str] = None,
) -> Dict:
    """Create an interactive list to display products in a category.

    Features:
    - Displays up to 10 products (WhatsApp limit)
    - Shows product name and price in title
    - Shows description in subtitle
    - Each row has ID format: add_product_{product_id}
    - Automatically handles both basePrice and price fields

    Args:
        products: List of product dicts with id, name, basePrice/price, description
        category_name: Name of the category for display
        header_text: Optional custom header (defaults to "{category_name} Menu")

    Returns:
        Interactive list component dict
    """
    if not header_text:
        header_text = f"{category_name} Menu"

    # Build product rows
    rows = []
    for product in products[:10]:  # WhatsApp limit: 10 rows
        product_id = product.get("id", "")
        name = product.get("name", "Unknown Product")

        # Handle both basePrice (API) and price (mock) fields
        price = product.get("basePrice") or product.get("price", 0)

        # Format price
        if price % 1 == 0:  # Whole number
            price_str = f"${int(price)}"
        else:
            price_str = f"${price:.2f}"

        title = f"{name} - {price_str}"
        description = product.get("description", "")

        rows.append({
            "id": f"add_product_{product_id}",
            "title": title[:24],  # WhatsApp limit
            "description": description[:72] if description else f"Price: {price_str}"
        })

    # Create list component
    return create_list_component(
        body_text=f"Choose from our {category_name}:",
        sections=[{
            "title": category_name,
            "rows": rows
        }],
        button_text="Select Item",
        header_text=header_text,
        footer_text="Tap to add to cart"
    )


# ============================================
# SIZE SELECTION - WITH API SUPPORT
# ============================================


def create_size_selection_buttons(
    item_name: str,
    base_price: float = None,
    presentations: Optional[List[Dict]] = None,
) -> Dict:
    """Create size selection buttons for menu items."""
    buttons = []

    if presentations and len(presentations) > 0:
        for pres in presentations[:3]:  # Max 3 buttons
            pres_id = pres.get("_id")
            pres_name = pres.get("name", "Inconnu")
            pres_price = pres.get("price", 0.0)

            buttons.append(
                {
                    "id": f"size_{pres_id}",
                    "title": f"{pres_name} {pres_price:.2f}€",
                }
            )

    elif base_price is not None:
        small_price = base_price * 0.8
        large_price = base_price * 1.3

        buttons = [
            {"id": "size_small", "title": f"Petit {small_price:.2f}€"},
            {"id": "size_medium", "title": f"Moyen {base_price:.2f}€"},
            {"id": "size_large", "title": f"Grand {large_price:.2f}€"},
        ]

    else:
        buttons = [{"id": "size_default", "title": "Taille standard"}]

    return create_button_component(
        f"Choisissez votre taille pour {item_name} :",
        buttons,
        header_text="🍽️ Sélection de taille",
    )


# ============================================
# EXTRAS/MODIFIERS - WITH API SUPPORT
# ============================================


def create_extras_list(
    category: str = "pizza",
    modifiers: Optional[List[Dict]] = None,
    max_selections: int = 10,
) -> Dict:
    """Create list of extras/toppings for customization."""
    sections = []

    if modifiers and len(modifiers) > 0:
        for modifier in modifiers:
            modifier_name = modifier.get("name", "Options")
            options = modifier.get("options", [])

            if not options:
                continue

            rows = []
            for option in options[:10]:
                option_id = option.get("_id")
                option_name = option.get("name", "Inconnu")
                option_price = option.get("price", 0.0)

                price_display = f"+{option_price:.2f}€" if option_price > 0 else "Gratuit"

                rows.append(
                    {
                        "id": f"extra_{option_id}",
                        "title": option_name[:24],
                        "description": price_display,
                    }
                )

            if rows:
                sections.append({"title": modifier_name[:24], "rows": rows})

    else:
        # Legacy extras remain English because they are product names
        if category == "pizza":
            sections = [
                {
                    "title": "🧀 Fromages & Protéines",
                    "rows": [
                        {"id": "extra_cheese", "title": "Extra Cheese", "description": "+2.00€"},
                        {"id": "pepperoni", "title": "Pepperoni", "description": "+2.50€"},
                        {"id": "chicken", "title": "Grilled Chicken", "description": "+3.00€"},
                        {"id": "bacon", "title": "Bacon", "description": "+2.50€"},
                    ],
                },
                {
                    "title": "🥬 Légumes",
                    "rows": [
                        {"id": "mushrooms", "title": "Mushrooms", "description": "+1.50€"},
                        {"id": "olives", "title": "Olives", "description": "+1.00€"},
                    ],
                },
            ]

        elif category == "burger":
            sections = [
                {
                    "title": "🍔 Extras",
                    "rows": [
                        {"id": "extra_cheese", "title": "Extra Cheese", "description": "+2.00€"},
                        {"id": "bacon", "title": "Bacon", "description": "+2.50€"},
                        {"id": "mushrooms", "title": "Mushrooms", "description": "+1.50€"},
                    ],
                },
            ]

        else:
            sections = [
                {
                    "title": "➕ Suppléments",
                    "rows": [
                        {"id": "extra_toppings", "title": "Extra Toppings", "description": "+1.50€"}
                    ],
                }
            ]

    # "No extras" → "Sans extra"
    if sections:
        if len(sections[0].get("rows", [])) < 10:
            sections[0]["rows"].insert(
                0, {"id": "no_extras", "title": "Sans extra", "description": "0.00€"}
            )
        else:
            sections.insert(
                0,
                {
                    "title": "Options",
                    "rows": [{"id": "no_extras", "title": "Sans extra", "description": "0.00€"}],
                },
            )

    return create_list_component(
        f"Choisissez vos extras (jusqu'à {max_selections}) :",
        sections,
        button_text="Ajouter",
        header_text="🎨 Personnaliser",
    )


def create_modifiers_list(
    item_name: str, modifiers: List[Dict], max_total_rows: int = 10
) -> Dict:
    """Create interactive list for API modifiers with validation."""
    sections = []
    total_rows = 0

    for modifier in modifiers:
        if total_rows >= max_total_rows:
            break

        modifier_name = modifier.get("name", "Options")
        min_selections = modifier.get("minSelections", 0)
        max_selections = modifier.get("maxSelections", 1)
        options = modifier.get("options", [])

        if not options:
            continue

        if min_selections > 0:
            title_suffix = " (Obligatoire)"
        elif max_selections > 1:
            title_suffix = f" (Max {max_selections})"
        else:
            title_suffix = ""

        section_title = f"{modifier_name}{title_suffix}"[:24]

        rows = []
        remaining_rows = max_total_rows - total_rows

        for option in options[:remaining_rows]:
            option_id = option.get("_id")
            option_name = option.get("name", "Inconnu")
            option_price = option.get("price", 0.0)

            price_display = f"+{option_price:.2f}€" if option_price > 0 else "Gratuit"

            rows.append(
                {
                    "id": f"mod_{modifier.get('_id')}_{option_id}",
                    "title": option_name[:24],
                    "description": price_display,
                }
            )

        if rows:
            sections.append({"title": section_title, "rows": rows})
            total_rows += len(rows)

    if not sections:
        return None

    return create_list_component(
        f"Personnalisez votre {item_name} :",
        sections,
        button_text="Continuer",
        header_text="🎨 Personnaliser la commande",
    )


# ============================================
# CATEGORY SELECTION - WITH API SUPPORT
# ============================================


def create_category_selection_list(categories: Optional[List[Dict]] = None) -> Dict:
    """Create category selection list."""
    sections = []

    if categories:
        rows = []
        for category in categories[:10]:
            cat_id = category.get("id")
            cat_name = category.get("name", "Inconnu")
            product_count = len(category.get("products", []))

            emoji = _get_category_emoji(cat_name)

            rows.append(
                {
                    "id": f"cat_{cat_id}",
                    "title": f"{emoji} {cat_name}"[:24],
                    "description": f"{product_count} articles",
                }
            )

        if rows:
            sections = [{"title": "Catégories du menu", "rows": rows}]

    else:
        sections = [
            {
                "title": "🍽️ Menu",
                "rows": [
                    {"id": "cat_pizzas", "title": "🍕 Pizzas", "description": "5 articles"},
                    {"id": "cat_burgers", "title": "🍔 Burgers", "description": "4 articles"},
                    {"id": "cat_sides", "title": "🍟 Accompagnements", "description": "4 articles"},
                    {"id": "cat_drinks", "title": "🥤 Boissons", "description": "4 articles"},
                    {"id": "cat_desserts", "title": "🍰 Desserts", "description": "3 articles"},
                ],
            }
        ]

    return create_list_component(
        "Que souhaitez-vous commander ? Consultez notre menu ci-dessous :",
        sections,
        button_text="Afficher le menu",
        header_text="🍽️ Bonjour, que souhaitez-vous commander ?",
    )


def _get_category_emoji(category_name: str) -> str:
    """Get emoji for category name."""
    name_lower = category_name.lower()

    emoji_map = {
        "pizza": "🍕",
        "burger": "🍔",
        "side": "🍟",
        "drink": "🥤",
        "dessert": "🍰",
        "salad": "🥗",
        "pasta": "🍝",
        "soup": "🍜",
        "sandwich": "🥪",
        "chicken": "🍗",
        "seafood": "🦐",
        "breakfast": "🍳",
        "coffee": "☕",
        "ice cream": "🍦",
    }

    for key, emoji in emoji_map.items():
        if key in name_lower:
            return emoji

    return "🍽️"


# ============================================
# HELPER FUNCTIONS
# ============================================


def extract_modifier_selections(selected_ids: List[str]) -> Dict[str, List[str]]:
    """Extract modifier selections from reply IDs."""
    selections = {}

    for reply_id in selected_ids:
        if reply_id.startswith("mod_"):
            parts = reply_id.split("_")
            if len(parts) >= 3:
                modifier_id = parts[1]
                option_id = "_".join(parts[2:])

                if modifier_id not in selections:
                    selections[modifier_id] = []

                selections[modifier_id].append(option_id)

    return selections


def extract_presentation_id(reply_id: str) -> Optional[str]:
    """Extract presentation ID from size selection reply."""
    if reply_id.startswith("size_"):
        return reply_id.replace("size_", "")

    return None
