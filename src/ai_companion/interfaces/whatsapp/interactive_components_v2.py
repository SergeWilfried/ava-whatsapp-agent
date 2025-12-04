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
    """Create a button interactive component (up to 3 buttons).

    Args:
        body_text: Main message text (required, max 1024 chars)
        buttons: List of button dicts with 'id' and 'title' keys (max 3 buttons)
        header_text: Optional header text (max 60 chars)
        footer_text: Optional footer text (max 60 chars)

    Returns:
        Interactive component dict ready for WhatsApp API
    """
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
    button_text: str = "Voir le Menu",
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None,
) -> Dict:
    """Create a list interactive component.

    IMPORTANT: WhatsApp limits list messages to:
    - Up to 10 sections
    - Up to 10 rows TOTAL across ALL sections combined

    Args:
        body_text: Main message text
        sections: List of section dicts
        button_text: Text for the list button
        header_text: Optional header text
        footer_text: Optional footer text

    Returns:
        Interactive component dict
    """
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


# ============================================
# SIZE SELECTION - WITH API SUPPORT
# ============================================


def create_product_list(
    products: List[Dict],
    category_name: str,
    header_text: Optional[str] = None,
) -> Dict:
    """Create an interactive list to display products in a category.

    Args:
        products: List of product dicts with id, name, description, basePrice
        category_name: Name of the category
        header_text: Optional header text

    Returns:
        Interactive list component

    Example:
        create_product_list(
            [
                {"id": "prod001", "name": "Bissap", "basePrice": 19.99, "description": "Drink"},
                {"id": "prod002", "name": "Eau Laafi", "basePrice": 500, "description": "Water"}
            ],
            "Drinks"
        )
    """
    # Create rows from products (max 10 rows per WhatsApp limit)
    rows = []
    for product in products[:10]:  # Limit to 10 products
        product_id = product.get("id", "")
        product_name = product.get("name", "Unknown Item")
        price = product.get("basePrice") or product.get("price", 0)
        description = product.get("description", "")

        # Format price
        price_str = f"${price:.2f}" if price < 1000 else f"${price:.0f}"

        rows.append({
            "id": f"add_product_{product_id}",
            "title": f"{product_name} - {price_str}",
            "description": description[:72] if description else f"Price: {price_str}"
        })

    # Create single section with all products
    sections = [
        {
            "title": category_name[:24],
            "rows": rows
        }
    ]

    return create_list_component(
        body_text=f"Choisissez parmi nos  {category_name}:",
        sections=sections,
        button_text="Parcourir le menu",
        header_text=header_text,
        footer_text="Taper pour ajouter au panier"
    )


def create_size_selection_buttons(
    item_name: str,
    base_price: float = None,
    presentations: Optional[List[Dict]] = None,
) -> Dict:
    """Create size selection buttons for menu items.

    Supports both legacy (base_price with multipliers) and API presentations.

    Args:
        item_name: Name of the menu item
        base_price: Base price (legacy mode - medium size)
        presentations: API presentations list with {_id, name, price}

    Returns:
        Interactive button component

    Example with API presentations:
        create_size_selection_buttons(
            "Classic Burger",
            presentations=[
                {"_id": "pres001", "name": "Regular", "price": 15.99},
                {"_id": "pres002", "name": "Large", "price": 18.99}
            ]
        )

    Example with legacy pricing:
        create_size_selection_buttons("Classic Burger", base_price=15.99)
    """
    buttons = []

    if presentations and len(presentations) > 0:
        # Use API presentations
        logger.debug(f"Using API presentations: {len(presentations)} options")

        for pres in presentations[:3]:  # Max 3 buttons
            pres_id = pres.get("_id")
            pres_name = pres.get("name", "Unknown")
            pres_price = pres.get("price", 0.0)

            buttons.append(
                {
                    "id": f"size_{pres_id}",
                    "title": f"{pres_name} ${pres_price:.2f}",
                }
            )

    elif base_price is not None:
        # Use legacy size multipliers
        logger.debug("Using legacy size multipliers")

        small_price = base_price * 0.8
        large_price = base_price * 1.3

        buttons = [
            {"id": "size_small", "title": f"Petit ${small_price:.2f}"},
            {"id": "size_medium", "title": f"Moyen ${base_price:.2f}"},
            {"id": "size_large", "title": f"Grand ${large_price:.2f}"},
        ]

    else:
        # No size selection available
        logger.warning("No presentations or base_price provided, showing single option")
        buttons = [{"id": "size_default", "title": "Taille Standard"}]

    return create_button_component(
        f"Choisissez votre taille pour {item_name}:",
        buttons,
        header_text="🍽️ Sélection de la taille",
    )


# ============================================
# EXTRAS/MODIFIERS - WITH API SUPPORT
# ============================================


def create_extras_list(
    category: str = "pizza",
    modifiers: Optional[List[Dict]] = None,
    max_selections: int = 10,
) -> Dict:
    """Create list of extras/toppings for customization.

    Supports both legacy (hardcoded extras) and API modifiers.

    Args:
        category: Menu item category (legacy mode)
        modifiers: API modifiers list with {_id, name, options[]}
        max_selections: Maximum selections allowed

    Returns:
        Interactive list component

    Example with API modifiers:
        create_extras_list(
            modifiers=[
                {
                    "_id": "mod001",
                    "name": "Toppings",
                    "options": [
                        {"_id": "opt001", "name": "Extra Cheese", "price": 2.00},
                        {"_id": "opt002", "name": "Bacon", "price": 3.00}
                    ]
                }
            ]
        )

    Example with legacy:
        create_extras_list(category="pizza")
    """
    sections = []

    if modifiers and len(modifiers) > 0:
        # Use API modifiers
        logger.debug(f"Using API modifiers: {len(modifiers)} groups")

        for modifier in modifiers:
            modifier_name = modifier.get("name", "Options")
            options = modifier.get("options", [])

            if not options:
                continue

            # Create rows for this modifier group
            rows = []
            for option in options[:10]:  # Limit to 10 options per modifier
                option_id = option.get("_id")
                option_name = option.get("name", "Unknown")
                option_price = option.get("price", 0.0)

                # Format price display
                price_display = f"+${option_price:.2f}" if option_price > 0 else "Free"

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
        # Use legacy hardcoded extras
        logger.debug(f"Using legacy extras for category: {category}")

        if category == "pizza":
            sections = [
                {
                    "title": "🧀 Cheese & Protein",
                    "rows": [
                        {
                            "id": "extra_cheese",
                            "title": "Extra Cheese",
                            "description": "+$2.00",
                        },
                        {
                            "id": "pepperoni",
                            "title": "Pepperoni",
                            "description": "+$2.50",
                        },
                        {
                            "id": "chicken",
                            "title": "Grilled Chicken",
                            "description": "+$3.00",
                        },
                        {"id": "bacon", "title": "Bacon", "description": "+$2.50"},
                    ],
                },
                {
                    "title": "🥬 Vegetables",
                    "rows": [
                        {
                            "id": "mushrooms",
                            "title": "Mushrooms",
                            "description": "+$1.50",
                        },
                        {"id": "olives", "title": "Olives", "description": "+$1.00"},
                    ],
                },
            ]

        elif category == "burger":
            sections = [
                {
                    "title": "🍔 Extras",
                    "rows": [
                        {
                            "id": "extra_cheese",
                            "title": "Extra Cheese",
                            "description": "+$2.00",
                        },
                        {"id": "bacon", "title": "Bacon", "description": "+$2.50"},
                        {
                            "id": "mushrooms",
                            "title": "Mushrooms",
                            "description": "+$1.50",
                        },
                    ],
                },
            ]

        else:
            # Generic extras
            sections = [
                {
                    "title": "➕ Add-ons",
                    "rows": [
                        {
                            "id": "extra_toppings",
                            "title": "Extra Toppings",
                            "description": "+$1.50",
                        }
                    ],
                }
            ]

    # Add "No extras" option
    if sections:
        # Add to first section or create new one
        if len(sections[0].get("rows", [])) < 10:
            sections[0]["rows"].insert(
                0, {"id": "no_extras", "title": "No extras", "description": "$0.00"}
            )
        else:
            sections.insert(
                0,
                {
                    "title": "Options",
                    "rows": [
                        {
                            "id": "no_extras",
                            "title": "Pas de suppléments",
                            "description": "$0.00",
                        }
                    ],
                },
            )

    return create_list_component(
        f"Choisissez vos suppléments (jusqua to {max_selections}):",
        sections,
        button_text="Ajouter Suppléments",
        header_text="🎨 Personnaliser",
    )


def create_modifiers_list(
    item_name: str, modifiers: List[Dict], max_total_rows: int = 10
) -> Dict:
    """Create interactive list for API modifiers with validation.

    This is a more advanced version specifically for API modifiers that
    respects min/max selection rules.

    Args:
        item_name: Name of the item being customized
        modifiers: API modifiers list
        max_total_rows: Maximum total rows to display (WhatsApp limit: 10)

    Returns:
        Interactive list component with modifier sections
    """
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

        # Add requirement info to section title
        if min_selections > 0:
            title_suffix = f" (Required)"
        elif max_selections > 1:
            title_suffix = f" (Max {max_selections})"
        else:
            title_suffix = ""

        section_title = f"{modifier_name}{title_suffix}"[:24]

        # Create rows
        rows = []
        remaining_rows = max_total_rows - total_rows

        for option in options[:remaining_rows]:
            option_id = option.get("_id")
            option_name = option.get("name", "Unknown")
            option_price = option.get("price", 0.0)

            price_display = f"+${option_price:.2f}" if option_price > 0 else "Free"

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
        # No modifiers, skip customization
        return None

    return create_list_component(
        f"Personnaliser votre {item_name}:",
        sections,
        button_text="poursuivre",
        header_text="🎨 Personnaliser la commande",
    )


# ============================================
# CATEGORY SELECTION - WITH API SUPPORT
# ============================================


def create_category_selection_list(categories: Optional[List[Dict]] = None) -> Dict:
    """Create category selection list.

    Supports both mock data and API categories.

    Args:
        categories: API categories list with {id, name, products[]}
                   If None, uses mock categories

    Returns:
        Interactive list component

    Example with API:
        create_category_selection_list([
            {"id": "cat001", "name": "Burgers", "products": [...]},
            {"id": "cat002", "name": "Pizza", "products": [...]}
        ])
    """
    sections = []

    if categories:
        # Use API categories
        logger.debug(f"Using API categories: {len(categories)}")

        rows = []
        for category in categories[:10]:
            cat_id = category.get("id")
            cat_name = category.get("name", "Unknown")
            product_count = len(category.get("products", []))

            # Add emoji based on category name
            emoji = _get_category_emoji(cat_name)

            rows.append(
                {
                    "id": f"cat_{cat_id}",
                    "title": f"{emoji} {cat_name}"[:24],
                    "description": f"{product_count} items",
                }
            )

        if rows:
            sections = [{"title": "Menu Categories", "rows": rows}]

    else:
        # Use mock categories (legacy)
        logger.debug("Using mock categories")

        sections = [
            {
                "title": "🍽️ Menu",
                "rows": [
                    {"id": "cat_pizzas", "title": "🍕 Pizzas", "description": "5 items"},
                    {
                        "id": "cat_burgers",
                        "title": "🍔 Burgers",
                        "description": "4 items",
                    },
                    {"id": "cat_sides", "title": "🍟 Sides", "description": "4 items"},
                    {"id": "cat_drinks", "title": "🥤 Drinks", "description": "4 items"},
                    {
                        "id": "cat_desserts",
                        "title": "🍰 Desserts",
                        "description": "3 items",
                    },
                ],
            }
        ]

    return create_list_component(
        "Que souhaitez-vous commander ? Consultez notre menu ci-dessous :",
        sections,
        button_text="Voir le Menu",
        header_text="🍽️ Notre Menu",
    )


def _get_category_emoji(category_name: str) -> str:
    """Get emoji for category name.

    Args:
        category_name: Category name

    Returns:
        Emoji string
    """
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

    return "🍽️"  # Default


# ============================================
# HELPER FUNCTIONS
# ============================================


def extract_modifier_selections(selected_ids: List[str]) -> Dict[str, List[str]]:
    """Extract modifier selections from reply IDs.

    Converts list of IDs like ["mod_mod001_opt001", "mod_mod001_opt002"]
    to grouped dict: {"mod001": ["opt001", "opt002"]}

    Args:
        selected_ids: List of selected reply IDs

    Returns:
        Dict mapping modifier ID to list of option IDs
    """
    selections = {}

    for reply_id in selected_ids:
        if reply_id.startswith("mod_"):
            # Format: mod_{modifier_id}_{option_id}
            parts = reply_id.split("_")
            if len(parts) >= 3:
                modifier_id = parts[1]
                option_id = "_".join(parts[2:])  # Handle IDs with underscores

                if modifier_id not in selections:
                    selections[modifier_id] = []

                selections[modifier_id].append(option_id)

    return selections


def extract_presentation_id(reply_id: str) -> Optional[str]:
    """Extract presentation ID from size selection reply.

    Args:
        reply_id: Reply ID from size selection (e.g., "size_pres001")

    Returns:
        Presentation ID or None
    """
    if reply_id.startswith("size_"):
        return reply_id.replace("size_", "")

    return None
