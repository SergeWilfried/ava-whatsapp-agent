"""
Example: Creating carousels with your actual restaurant menu and automatic images.

This shows how to integrate carousel messages with your existing RESTAURANT_MENU
data and automatically generated image URLs.
"""

import asyncio
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_companion.core.schedules import RESTAURANT_MENU, SPECIAL_OFFERS
from ai_companion.interfaces.whatsapp.carousel_components import (
    create_restaurant_menu_carousel,
    create_offer_carousel
)
from ai_companion.interfaces.whatsapp.image_utils import (
    prepare_menu_items_for_carousel,
    get_all_menu_items_with_images,
    get_featured_items_with_images
)


def example_pizza_carousel():
    """Create a carousel showing all pizzas with automatic images."""
    print("=" * 80)
    print("EXAMPLE 1: Pizza Menu Carousel")
    print("=" * 80)

    # Get pizzas with automatic image URLs
    pizza_items = prepare_menu_items_for_carousel(
        menu_items=RESTAURANT_MENU["pizzas"],
        category="pizzas",
        base_order_url="https://yourshop.com/order"
    )

    # Create carousel
    carousel = create_restaurant_menu_carousel(
        menu_items=pizza_items,
        body_text="Check out our delicious pizzas! 🍕 Fresh made daily",
        button_text="Order Now"
    )

    print(f"✅ Created carousel with {len(pizza_items)} pizzas")
    print(f"   First item: {pizza_items[0]['name']}")
    print(f"   Image URL: {pizza_items[0]['image_url'][:60]}...")
    print()

    return carousel


def example_mixed_category_carousel():
    """Create a carousel with items from multiple categories."""
    print("=" * 80)
    print("EXAMPLE 2: Mixed Menu Carousel (Top 10 Items)")
    print("=" * 80)

    # Get up to 10 items from all categories
    all_items = get_all_menu_items_with_images(
        menu_dict=RESTAURANT_MENU,
        max_items=10  # Carousel maximum
    )

    carousel = create_restaurant_menu_carousel(
        menu_items=all_items,
        body_text="Browse our full menu! Something for everyone 😋",
        button_text="Order"
    )

    print(f"✅ Created carousel with {len(all_items)} items")
    for item in all_items[:3]:
        print(f"   - {item['name']} (${item['basePrice']})")
    print(f"   ... and {len(all_items) - 3} more")
    print()

    return carousel


def example_featured_items_carousel():
    """Create a carousel with hand-picked featured items."""
    print("=" * 80)
    print("EXAMPLE 3: Featured Items Carousel")
    print("=" * 80)

    # Pick specific items to feature
    featured_names = [
        "Margherita Pizza",
        "BBQ Chicken Pizza",
        "Classic Burger",
        "Bacon Burger",
        "Chocolate Brownie",
        "Cheesecake"
    ]

    featured_items = get_featured_items_with_images(
        menu_dict=RESTAURANT_MENU,
        featured_names=featured_names
    )

    carousel = create_restaurant_menu_carousel(
        menu_items=featured_items,
        body_text="⭐ Staff Picks - Our Most Popular Items!",
        button_text="Order Now"
    )

    print(f"✅ Created carousel with {len(featured_items)} featured items")
    for item in featured_items:
        print(f"   ⭐ {item['name']}")
    print()

    return carousel


def example_category_carousel(category: str = "burgers"):
    """Create a carousel for a specific category."""
    print("=" * 80)
    print(f"EXAMPLE 4: {category.title()} Carousel")
    print("=" * 80)

    items = prepare_menu_items_for_carousel(
        menu_items=RESTAURANT_MENU[category],
        category=category
    )

    carousel = create_restaurant_menu_carousel(
        menu_items=items,
        body_text=f"Try our amazing {category}! 🍔",
        button_text="Order"
    )

    print(f"✅ Created {category} carousel with {len(items)} items")
    print()

    return carousel


def example_daily_specials_carousel():
    """Create a carousel from special offers."""
    print("=" * 80)
    print("EXAMPLE 5: Daily Specials Carousel")
    print("=" * 80)

    # Create offers from combo deals
    offers = []
    for combo in SPECIAL_OFFERS["combo_deals"]:
        offers.append({
            "title": combo["name"],
            "description": f"{', '.join(combo['items'])} - Save ${combo['savings']}!",
            "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800&h=600&fit=crop",
            "offer_url": f"https://yourshop.com/specials/{combo['name'].lower().replace(' ', '-')}"
        })

    # Add a few daily specials
    for day, special in list(SPECIAL_OFFERS["daily_specials"].items())[:3]:
        offers.append({
            "title": f"{day.title()}'s Special",
            "description": special,
            "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&h=600&fit=crop",
            "offer_url": f"https://yourshop.com/specials/{day}"
        })

    carousel = create_offer_carousel(
        offers=offers[:10],  # Max 10 cards
        body_text="🎉 Limited Time Offers - Don't Miss Out!",
        button_text="Claim Deal"
    )

    print(f"✅ Created specials carousel with {len(offers[:10])} offers")
    print()

    return carousel


def example_usage_in_agent():
    """
    Example: How to use carousels in your agent graph nodes.
    """
    print("=" * 80)
    print("EXAMPLE 6: Usage in Agent Node")
    print("=" * 80)

    example_code = '''
# In your graph node (e.g., in graph.py or cart_nodes.py)

from ai_companion.core.schedules import RESTAURANT_MENU
from ai_companion.interfaces.whatsapp.carousel_components import create_restaurant_menu_carousel
from ai_companion.interfaces.whatsapp.image_utils import prepare_menu_items_for_carousel

async def show_menu_carousel_node(state):
    """Node that shows menu as a carousel instead of a list."""

    # Get the category user wants (or show all)
    category = state.get("selected_category", None)

    if category and category in RESTAURANT_MENU:
        # Show specific category
        items = prepare_menu_items_for_carousel(
            RESTAURANT_MENU[category],
            category
        )
        body_text = f"Here are our {category}! 😋"
    else:
        # Show mixed menu (top 10)
        from ai_companion.interfaces.whatsapp.image_utils import get_all_menu_items_with_images
        items = get_all_menu_items_with_images(RESTAURANT_MENU, max_items=10)
        body_text = "Browse our menu! 😋"

    # Create carousel
    carousel = create_restaurant_menu_carousel(
        menu_items=items,
        body_text=body_text,
        button_text="Order"
    )

    return {
        "messages": [AIMessage(content="Here's our menu!")],
        "interactive_component": carousel,
        "message_type": "interactive_carousel"
    }


# In your webhook handler (whatsapp_response.py)

if node_name == "show_menu_carousel":
    result = await show_menu_carousel_node(current_state_dict)

    await graph.aupdate_state(
        config={"configurable": {"thread_id": session_id}},
        values=result
    )

    message_obj = result.get("messages")
    response_message = message_obj.content if message_obj else "Menu"
    carousel = result.get("interactive_component")

    success = await send_response(
        from_number,
        response_message,
        "interactive_carousel",
        phone_number_id=phone_number_id,
        whatsapp_token=whatsapp_token,
        interactive_component=carousel
    )

    return Response(content="Carousel sent", status_code=200)
'''

    print(example_code)
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("WhatsApp Carousel with Real Menu Data")
    print("=" * 80 + "\n")

    # Run examples
    example_pizza_carousel()
    example_mixed_category_carousel()
    example_featured_items_carousel()
    example_category_carousel("burgers")
    example_daily_specials_carousel()
    example_usage_in_agent()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✅ All examples completed successfully!")
    print()
    print("Key Features:")
    print("• Automatic image URLs from Unsplash (no API key needed)")
    print("• Item-specific images matched by name")
    print("• Category fallbacks for unlisted items")
    print("• Easy integration with existing RESTAURANT_MENU")
    print("• Ready to use in production!")
    print()
    print("Next Steps:")
    print("1. Use these patterns in your agent nodes")
    print("2. Test with actual WhatsApp sending (set credentials)")
    print("3. Optionally replace with your own hosted images")
    print()
    print("Image URLs are from Unsplash and ready to use immediately!")


if __name__ == "__main__":
    main()
