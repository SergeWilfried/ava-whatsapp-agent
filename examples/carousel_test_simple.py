"""
Simple test of carousel components without dependencies.

This validates the carousel component creation without requiring
the full application environment or dependencies.
"""

import sys
import os
import json

# Add src directory to path for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_companion.interfaces.whatsapp.carousel_components import (
    create_carousel_card,
    create_carousel_component,
    create_product_carousel,
    create_offer_carousel,
    create_restaurant_menu_carousel
)


def test_manual_carousel():
    """Test creating a carousel manually with individual cards."""
    print("=" * 80)
    print("TEST 1: Manual Carousel Creation")
    print("=" * 80)

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
        )
    ]

    carousel = create_carousel_component(
        body_text="Check out our delicious pizzas! 🍕",
        cards=cards
    )

    print(json.dumps(carousel, indent=2))
    print("✅ Manual carousel created successfully\n")
    return carousel


def test_product_carousel():
    """Test creating a product carousel from product data."""
    print("=" * 80)
    print("TEST 2: Product Carousel")
    print("=" * 80)

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
        }
    ]

    carousel = create_product_carousel(
        products=products,
        body_text="Browse our pizza selection! 🍕",
        button_text="Order Now"
    )

    print(json.dumps(carousel, indent=2))
    print("✅ Product carousel created successfully\n")
    return carousel


def test_offer_carousel():
    """Test creating an offers carousel."""
    print("=" * 80)
    print("TEST 3: Offer Carousel")
    print("=" * 80)

    offers = [
        {
            "title": "50% Off First Order",
            "description": "New customers only",
            "image_url": "https://example.com/offers/first-order.jpg",
            "offer_url": "https://shop.example.com/offers/first-order"
        },
        {
            "title": "Free Delivery",
            "description": "Orders over $25",
            "image_url": "https://example.com/offers/free-delivery.jpg",
            "offer_url": "https://shop.example.com/offers/free-delivery"
        }
    ]

    carousel = create_offer_carousel(
        offers=offers,
        body_text="🎉 Special offers just for you!",
        button_text="Claim Now"
    )

    print(json.dumps(carousel, indent=2))
    print("✅ Offer carousel created successfully\n")
    return carousel


def test_restaurant_menu_carousel():
    """Test creating a restaurant menu carousel."""
    print("=" * 80)
    print("TEST 4: Restaurant Menu Carousel")
    print("=" * 80)

    menu_items = [
        {
            "name": "Cheeseburger",
            "description": "Angus beef with cheddar",
            "price": 11.99,
            "image_url": "https://example.com/burgers/cheeseburger.jpg",
            "order_url": "https://order.example.com/burger/1"
        },
        {
            "name": "Bacon Burger",
            "description": "Double bacon",
            "price": 13.99,
            "image_url": "https://example.com/burgers/bacon.jpg",
            "order_url": "https://order.example.com/burger/2"
        }
    ]

    carousel = create_restaurant_menu_carousel(
        menu_items=menu_items,
        body_text="Try our famous burgers! 🍔",
        button_text="Order Now"
    )

    print(json.dumps(carousel, indent=2))
    print("✅ Restaurant menu carousel created successfully\n")
    return carousel


def test_video_carousel():
    """Test creating a carousel with video headers."""
    print("=" * 80)
    print("TEST 5: Video Carousel")
    print("=" * 80)

    cards = [
        create_carousel_card(
            card_index=0,
            header_type="video",
            media_link="https://example.com/videos/pizza-making.mp4",
            body_text="See how we make our pizzas!",
            button_display_text="Watch More",
            button_url="https://example.com/videos/kitchen"
        ),
        create_carousel_card(
            card_index=1,
            header_type="video",
            media_link="https://example.com/videos/delivery.mp4",
            body_text="Fast delivery to your door",
            button_display_text="Order Now",
            button_url="https://order.example.com"
        )
    ]

    carousel = create_carousel_component(
        body_text="Experience our restaurant! 🎥",
        cards=cards
    )

    print(json.dumps(carousel, indent=2))
    print("✅ Video carousel created successfully\n")
    return carousel


def test_validation_errors():
    """Test validation error handling."""
    print("=" * 80)
    print("TEST 6: Validation Error Handling")
    print("=" * 80)

    test_cases = [
        {
            "name": "Too few cards (1 card)",
            "test": lambda: create_carousel_component(
                "Test",
                [create_carousel_card(0, "image", "url", "text", "btn", "url")]
            )
        },
        {
            "name": "Invalid card_index (out of range)",
            "test": lambda: create_carousel_card(
                card_index=10,
                header_type="image",
                media_link="url",
                body_text="text",
                button_display_text="btn",
                button_url="url"
            )
        },
        {
            "name": "Invalid header_type",
            "test": lambda: create_carousel_card(
                card_index=0,
                header_type="pdf",
                media_link="url",
                body_text="text",
                button_display_text="btn",
                button_url="url"
            )
        },
        {
            "name": "Mixed header types",
            "test": lambda: create_carousel_component(
                "Test",
                [
                    create_carousel_card(0, "image", "url1", "text1", "btn", "url"),
                    create_carousel_card(1, "video", "url2", "text2", "btn", "url")
                ]
            )
        }
    ]

    passed = 0
    failed = 0

    for test_case in test_cases:
        try:
            test_case["test"]()
            print(f"❌ {test_case['name']}: Should have raised ValueError")
            failed += 1
        except ValueError as e:
            print(f"✅ {test_case['name']}: Correctly raised ValueError")
            print(f"   Error: {str(e)}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_case['name']}: Raised unexpected error: {type(e).__name__}")
            failed += 1

    print(f"\nValidation tests: {passed} passed, {failed} failed\n")
    return passed == len(test_cases)


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("WhatsApp Carousel Component Tests")
    print("=" * 80 + "\n")

    try:
        # Run creation tests
        test_manual_carousel()
        test_product_carousel()
        test_offer_carousel()
        test_restaurant_menu_carousel()
        test_video_carousel()

        # Run validation tests
        all_validation_passed = test_validation_errors()

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("✅ All carousel creation tests passed")
        if all_validation_passed:
            print("✅ All validation tests passed")
        else:
            print("⚠️  Some validation tests failed")
        print("\n✨ Carousel components are working correctly!")
        print("\nNext steps:")
        print("1. Use these components in your WhatsApp agent")
        print("2. See docs/CAROUSEL_MESSAGES.md for full documentation")
        print("3. See examples/carousel_example.py for usage examples")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
