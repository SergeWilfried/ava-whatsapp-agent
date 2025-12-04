"""WhatsApp interface module - V2 components with API support."""

# Export V2 components by default
from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    create_size_selection_buttons,
    create_extras_list,
    create_modifiers_list,
    create_category_selection_list,
    create_button_component,
    create_list_component,
    extract_modifier_selections,
    extract_presentation_id,
)

from ai_companion.interfaces.whatsapp.carousel_components_v2 import (
    create_carousel_card,
    create_carousel_component,
    create_product_carousel,
    create_api_menu_carousel,
    create_category_products_carousel,
    create_offer_carousel,
)

# Legacy components still available for backward compatibility
from ai_companion.interfaces.whatsapp import interactive_components as interactive_components_legacy
from ai_companion.interfaces.whatsapp import carousel_components as carousel_components_legacy

__all__ = [
    # V2 Interactive Components
    "create_size_selection_buttons",
    "create_extras_list",
    "create_modifiers_list",
    "create_category_selection_list",
    "create_button_component",
    "create_list_component",
    "extract_modifier_selections",
    "extract_presentation_id",
    # V2 Carousel Components
    "create_carousel_card",
    "create_carousel_component",
    "create_product_carousel",
    "create_api_menu_carousel",
    "create_category_products_carousel",
    "create_offer_carousel",
    # Legacy modules
    "interactive_components_legacy",
    "carousel_components_legacy",
]
