"""
Example usage of WhatsApp Carousel Message components.

This example demonstrates how to create and send interactive media carousel
messages using the WhatsApp Business API.
"""

import asyncio
import os
import sys

# Add src directory to path for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_companion.interfaces.whatsapp.carousel_components import (
    create_carousel_card,
    create_carousel_component,
    create_product_carousel,
    create_offer_carousel,
    create_restaurant_menu_carousel
)
from ai_companion.interfaces.whatsapp.whatsapp_response import send_response


async def example_manual_carousel():
    """Example: Creating a carousel manually with individual cards."""

    # Create individual cards
    cards = [
        create_carousel_card(
            card_index=0,
            header_type="image",
            media_link="https://example.com/pizza-margherita.jpg",
            body_text="Margherita Pizza\nFresh mozzarella, basil, tomato sauce\n$12.99",
            button_display_text="Order Now",
            button_url="https://order.example.com/pizza/1"
        ),
        create_carousel_card(
            card_index=1,
            header_type="image",
            media_link="https://example.com/pizza-pepperoni.jpg",
            body_text="Pepperoni Pizza\nLoaded with pepperoni\n$14.99",
            button_display_text="Order Now",
            button_url="https://order.example.com/pizza/2"
        ),
        create_carousel_card(
            card_index=2,
            header_type="image",
            media_link="https://example.com/pizza-veggie.jpg",
            body_text="Veggie Delight\nFresh vegetables, mushrooms, peppers\n$13.99",
            button_display_text="Order Now",
            button_url="https://order.example.com/pizza/3"
        )
    ]

    # Create carousel component
    carousel = create_carousel_component(
        body_text="Check out our delicious pizzas! 🍕",
        cards=cards
    )

    print("Manual Carousel Component:")
    print(carousel)
    print("\n" + "="*80 + "\n")

    return carousel


async def example_product_carousel():
    """Example: Creating a product carousel from product data."""

    products = [
        {
            "name": "Margherita Pizza",
            "description": "Classic cheese pizza with fresh basil",
            "price": 12.99,
            "image_url": "https://example.com/pizza-margherita.jpg",
            "product_url": "https://order.example.com/pizza/1"
        },
        {
            "name": "Pepperoni Pizza",
            "description": "Loaded with premium pepperoni",
            "price": 14.99,
            "image_url": "https://example.com/pizza-pepperoni.jpg",
            "product_url": "https://order.example.com/pizza/2"
        },
        {
            "name": "BBQ Chicken Pizza",
            "description": "Grilled chicken with BBQ sauce",
            "price": 15.99,
            "image_url": "https://example.com/pizza-bbq.jpg",
            "product_url": "https://order.example.com/pizza/3"
        },
        {
            "name": "Hawaiian Pizza",
            "description": "Ham and pineapple classic",
            "price": 13.99,
            "image_url": "https://example.com/pizza-hawaiian.jpg",
            "product_url": "https://order.example.com/pizza/4"
        }
    ]

    carousel = create_product_carousel(
        products=products,
        body_text="Browse our pizza selection! Fresh made daily 🍕",
        button_text="Order Now"
    )

    print("Product Carousel Component:")
    print(carousel)
    print("\n" + "="*80 + "\n")

    return carousel


async def example_offer_carousel():
    """Example: Creating an offers/promotions carousel."""

    offers = [
        {
            "title": "50% Off First Order",
            "description": "New customers only. Use code: FIRST50",
            "image_url": "https://example.com/offers/first-order.jpg",
            "offer_url": "https://shop.example.com/offers/first-order"
        },
        {
            "title": "Free Delivery",
            "description": "Orders over $25. Limited time!",
            "image_url": "https://example.com/offers/free-delivery.jpg",
            "offer_url": "https://shop.example.com/offers/free-delivery"
        },
        {
            "title": "Buy 2 Get 1 Free",
            "description": "On all pizzas this weekend",
            "image_url": "https://example.com/offers/buy2get1.jpg",
            "offer_url": "https://shop.example.com/offers/buy2get1"
        }
    ]

    carousel = create_offer_carousel(
        offers=offers,
        body_text="🎉 Special offers just for you! Don't miss out!",
        button_text="Claim Now"
    )

    print("Offer Carousel Component:")
    print(carousel)
    print("\n" + "="*80 + "\n")

    return carousel


async def example_restaurant_menu_carousel():
    """Example: Creating a restaurant menu carousel."""

    menu_items = [
        {
            "name": "Cheeseburger",
            "description": "Angus beef, cheddar, lettuce, tomato",
            "price": 11.99,
            "image_url": "https://example.com/burgers/cheeseburger.jpg",
            "order_url": "https://order.example.com/burger/1"
        },
        {
            "name": "Bacon Burger",
            "description": "Double bacon, crispy fried onions",
            "price": 13.99,
            "image_url": "https://example.com/burgers/bacon.jpg",
            "order_url": "https://order.example.com/burger/2"
        },
        {
            "name": "Veggie Burger",
            "description": "Plant-based patty, avocado, sprouts",
            "price": 10.99,
            "image_url": "https://example.com/burgers/veggie.jpg",
            "order_url": "https://order.example.com/burger/3"
        }
    ]

    carousel = create_restaurant_menu_carousel(
        menu_items=menu_items,
        body_text="Try our famous burgers! 🍔 Made fresh daily",
        button_text="Order Now"
    )

    print("Restaurant Menu Carousel Component:")
    print(carousel)
    print("\n" + "="*80 + "\n")

    return carousel


async def example_send_carousel_message():
    """Example: Sending a carousel message to a user."""

    # Note: You need valid WhatsApp credentials to actually send
    recipient_number = os.getenv("TEST_WHATSAPP_NUMBER", "1234567890")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_token = os.getenv("WHATSAPP_TOKEN")

    if not phone_number_id or not whatsapp_token:
        print("⚠️  WhatsApp credentials not found in environment variables.")
        print("Set WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_TOKEN to send messages.")
        return

    # Create a product carousel
    products = [
        {
            "name": "Summer Special Pizza",
            "description": "Fresh tomatoes and herbs",
            "price": 16.99,
            "image_url": "https://example.com/pizza-summer.jpg",
            "product_url": "https://order.example.com/specials/1"
        },
        {
            "name": "Winter Comfort Pizza",
            "description": "Rich and hearty toppings",
            "price": 17.99,
            "image_url": "https://example.com/pizza-winter.jpg",
            "product_url": "https://order.example.com/specials/2"
        }
    ]

    carousel = create_product_carousel(
        products=products,
        body_text="Check out our seasonal specials! Limited time only 🎉",
        button_text="Order"
    )

    # Send the carousel message
    success = await send_response(
        from_number=recipient_number,
        response_text="",  # Body text is in the carousel component
        message_type="interactive_carousel",
        phone_number_id=phone_number_id,
        whatsapp_token=whatsapp_token,
        interactive_component=carousel
    )

    if success:
        print(f"✅ Carousel message sent successfully to {recipient_number}")
    else:
        print(f"❌ Failed to send carousel message to {recipient_number}")


async def example_video_carousel():
    """Example: Creating a carousel with video headers instead of images."""

    cards = [
        create_carousel_card(
            card_index=0,
            header_type="video",
            media_link="https://example.com/videos/pizza-making.mp4",
            body_text="See how we make our pizzas!\nFresh ingredients daily",
            button_display_text="Watch More",
            button_url="https://example.com/videos/kitchen"
        ),
        create_carousel_card(
            card_index=1,
            header_type="video",
            media_link="https://example.com/videos/delivery.mp4",
            body_text="Fast delivery to your door\n30 min or less guaranteed",
            button_display_text="Order Now",
            button_url="https://order.example.com"
        )
    ]

    carousel = create_carousel_component(
        body_text="Experience our restaurant! 🎥",
        cards=cards
    )

    print("Video Carousel Component:")
    print(carousel)
    print("\n" + "="*80 + "\n")

    return carousel


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("WhatsApp Carousel Message Examples")
    print("="*80 + "\n")

    # Run all examples
    await example_manual_carousel()
    await example_product_carousel()
    await example_offer_carousel()
    await example_restaurant_menu_carousel()
    await example_video_carousel()

    # Uncomment to actually send a message (requires credentials)
    # await example_send_carousel_message()

    print("\n✅ All examples completed!")
    print("\nTo send carousel messages:")
    print("1. Set WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_TOKEN environment variables")
    print("2. Uncomment the example_send_carousel_message() call in main()")
    print("3. Update TEST_WHATSAPP_NUMBER with a valid recipient number")


if __name__ == "__main__":
    asyncio.run(main())
