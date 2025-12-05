"""
AI-powered message generation for interactive components.

This module generates dynamic, context-aware messages for cart operations,
greetings, and confirmations while keeping interactive component structures static.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ai_companion.graph.utils.helpers import get_chat_model
from ai_companion.settings import settings
import logging

logger = logging.getLogger(__name__)

# Message type templates
MESSAGE_TEMPLATES = {
    "greeting": """You are a friendly restaurant assistant. Generate a warm greeting message.
Context: {context}
Language: {language}
Keep it brief (1-2 sentences) and natural. Use appropriate emojis if they fit naturally.
""",

    "item_added": """You are a friendly restaurant assistant.
The customer just added: {item_name} (${price}) to their cart.
Generate a brief, enthusiastic confirmation message.
Language: {language}
Keep it to 1-2 sentences. Use emojis if appropriate.
Example style: "Great choice! {item_name} has been added to your cart 🛒"
""",

    "item_not_found": """You are a friendly restaurant assistant.
The customer tried to select an item that couldn't be found.
Generate a polite apology and encourage them to try selecting from the menu again.
Language: {language}
Keep it brief and helpful (1-2 sentences).
""",

    "item_unavailable": """You are a friendly restaurant assistant.
The item "{item_name}" is currently unavailable.
Generate a polite apology message.
Language: {language}
Keep it brief (1 sentence).
""",

    "size_selected": """You are a friendly restaurant assistant.
The customer selected size: {size_name} for ${price}
Generate a brief confirmation message.
Language: {language}
Keep it to 1 sentence.
""",

    "extra_added": """You are a friendly restaurant assistant.
The customer added an extra: {extra_name}
Generate a brief confirmation message.
Language: {language}
Keep it to 1 sentence.
""",

    "cart_empty": """You are a friendly restaurant assistant.
The customer's cart is empty. Encourage them to browse the menu.
Language: {language}
Keep it friendly and brief (1-2 sentences). Use emojis to make it inviting.
Example style: "🛒 Your cart is empty. Browse our delicious menu to get started!"
""",

    "checkout_start": """You are a friendly restaurant assistant.
The customer is ready to checkout with {item_count} item(s).
Cart total: ${total}
Generate a message to begin the checkout process.
Language: {language}
Keep it brief and professional (1-2 sentences).
Example style: "Great! Let's complete your order."
""",

    "delivery_method_selected": """You are a friendly restaurant assistant.
The customer selected: {delivery_method}
Generate a brief confirmation message.
Language: {language}
Keep it to 1 sentence.
""",

    "order_confirmed": """You are a friendly restaurant assistant.
Generate a warm thank you message for a confirmed order.
Order number: {order_id}
Total: ${total}
Language: {language}
Express gratitude and confirm the order. Keep it warm and professional (2-3 sentences).
Use emojis appropriately.
Example style: "✅ Order confirmed! Thank you for your order. We'll prepare it right away!"
""",

    "request_phone": """You are a friendly restaurant assistant.
Politely ask the customer for their phone number to complete the order.
Language: {language}
Keep it brief and polite (1-2 sentences). Use a phone emoji.
Example style: "To finalize your order, please provide your phone number. 📱"
""",

    "location_received": """You are a friendly restaurant assistant.
The customer shared their delivery location: {location}
Generate a confirmation message before asking for payment method.
Language: {language}
Keep it brief (1 sentence).
Example style: "Great! We'll deliver to: {location}"
""",

    "no_active_order": """You are a friendly restaurant assistant.
The customer wants to track an order but has no active orders.
Generate a brief, helpful message encouraging them to place an order or check their order history.
Language: {language}
Keep it friendly (1-2 sentences).
""",

    "no_orders_found": """You are a friendly restaurant assistant.
The customer has no order history found.
Generate a friendly message encouraging them to place their first order.
Language: {language}
Keep it inviting (1-2 sentences). Use emojis appropriately.
""",

    "tracking_error": """You are a friendly restaurant assistant.
There was an error fetching the order status: {error}
Generate a polite apology and suggest trying again or contacting support.
Language: {language}
Keep it brief and helpful (1-2 sentences).
""",
}

async def generate_dynamic_message(
    message_type: str,
    context: dict = None,
    temperature: float = 0.5
) -> str:
    """
    Generate AI-powered messages for interactive components.

    Args:
        message_type: One of MESSAGE_TEMPLATES keys (e.g., "item_added", "greeting")
        context: Dictionary with context variables (item_name, price, total, etc.)
        temperature: LLM temperature (0.3-0.7 recommended for consistency)

    Returns:
        Generated message string

    Example:
        >>> await generate_dynamic_message("item_added", {"item_name": "Pizza", "price": 12.99})
        "Great choice! Pizza has been added to your cart 🛒"
    """
    if message_type not in MESSAGE_TEMPLATES:
        logger.warning(f"Unknown message type: {message_type}, using fallback")
        return _get_fallback_message(message_type, context or {})

    try:
        # Get template and prepare context
        template = MESSAGE_TEMPLATES[message_type]
        ctx = context or {}

        # Add language context
        language = settings.LANGUAGE or "auto"
        if language == "auto":
            language = "auto-detect from context (default to English if unclear)"
        ctx["language"] = language

        # Create prompt and chain
        prompt = ChatPromptTemplate.from_template(template)
        llm = get_chat_model(temperature=temperature)
        chain = prompt | llm | StrOutputParser()

        # Generate message
        message = await chain.ainvoke(ctx)
        return message.strip()

    except Exception as e:
        logger.error(f"Error generating message for type '{message_type}': {e}", exc_info=True)
        # Fallback to static message
        return _get_fallback_message(message_type, context or {})


def _get_fallback_message(message_type: str, context: dict) -> str:
    """
    Fallback messages in case AI generation fails.
    These ensure the system always returns a message even if the LLM is unavailable.
    """
    fallbacks = {
        "greeting": "Welcome! How can I help you today? 👋",
        "item_added": f"Added {context.get('item_name', 'item')} to your cart! 🛒",
        "item_not_found": "I couldn't find that item. Please try selecting from the menu again.",
        "item_unavailable": f"Sorry, {context.get('item_name', 'that item')} is not available right now.",
        "size_selected": f"{context.get('size_name', 'Size')} selected!",
        "extra_added": f"Added {context.get('extra_name', 'extra')} to your order!",
        "cart_empty": "🛒 Your cart is empty. Browse the menu to add items!",
        "checkout_start": "Great! Let's complete your order.",
        "delivery_method_selected": f"{context.get('delivery_method', 'Delivery method')} selected!",
        "order_confirmed": f"✅ Order confirmed! Thank you for your order #{context.get('order_id', '')}.",
        "request_phone": "To finalize your order, please provide your phone number. 📱",
        "location_received": f"Great! We'll deliver to: {context.get('location', 'your location')}",
    }
    return fallbacks.get(message_type, "Thank you!")


async def generate_cart_summary_header(item_count: int, total: float) -> str:
    """
    Generate a dynamic header for cart summary.

    Args:
        item_count: Number of items in cart
        total: Cart total amount

    Returns:
        Generated header message
    """
    try:
        prompt = ChatPromptTemplate.from_template("""
You are a friendly restaurant assistant. Generate a cart summary header.

Items in cart: {item_count}
Total: ${total}
Language: {language}

Generate a brief, friendly header for the cart summary (1 sentence).
Use appropriate emojis.
Example styles:
- "🛒 Your Cart (3 items - $24.99)"
- "Here's what you're ordering:"
""")

        llm = get_chat_model(temperature=0.4)
        chain = prompt | llm | StrOutputParser()

        message = await chain.ainvoke({
            "item_count": item_count,
            "total": f"{total:.2f}",
            "language": settings.LANGUAGE or "auto-detect"
        })

        return message.strip()

    except Exception as e:
        logger.error(f"Error generating cart summary header: {e}", exc_info=True)
        return f"🛒 Your Cart ({item_count} {'item' if item_count == 1 else 'items'} - ${total:.2f})"
