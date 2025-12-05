"""Manual test script for AI-powered message generation.

Run this script to verify that the message generator is working correctly.
Usage: python test_manual_messages.py
"""

import asyncio
from ai_companion.graph.utils.message_generator import (
    generate_dynamic_message,
    generate_cart_summary_header,
    _get_fallback_message,
)


async def test_all_messages():
    """Test all message types."""
    print("=" * 60)
    print("Testing AI-Powered Message Generation")
    print("=" * 60)

    # Test 1: Item Added
    print("\n1. Testing 'item_added' message...")
    try:
        message = await generate_dynamic_message(
            "item_added",
            {"item_name": "Margherita Pizza", "price": 12.99}
        )
        print(f"   ✓ {message}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 2: Cart Empty
    print("\n2. Testing 'cart_empty' message...")
    try:
        message = await generate_dynamic_message("cart_empty")
        print(f"   ✓ {message}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 3: Checkout Start
    print("\n3. Testing 'checkout_start' message...")
    try:
        message = await generate_dynamic_message(
            "checkout_start",
            {"item_count": 3, "total": 45.50}
        )
        print(f"   ✓ {message}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 4: Order Confirmed
    print("\n4. Testing 'order_confirmed' message...")
    try:
        message = await generate_dynamic_message(
            "order_confirmed",
            {"order_id": "12345", "total": 45.50}
        )
        print(f"   ✓ {message}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 5: Request Phone
    print("\n5. Testing 'request_phone' message...")
    try:
        message = await generate_dynamic_message("request_phone")
        print(f"   ✓ {message}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 6: Size Selected
    print("\n6. Testing 'size_selected' message...")
    try:
        message = await generate_dynamic_message(
            "size_selected",
            {"size_name": "Large", "price": 15.99}
        )
        print(f"   ✓ {message}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 7: Item Not Found
    print("\n7. Testing 'item_not_found' message...")
    try:
        message = await generate_dynamic_message("item_not_found")
        print(f"   ✓ {message}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 8: Item Unavailable
    print("\n8. Testing 'item_unavailable' message...")
    try:
        message = await generate_dynamic_message(
            "item_unavailable",
            {"item_name": "Special Pizza"}
        )
        print(f"   ✓ {message}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 9: Cart Summary Header
    print("\n9. Testing 'cart_summary_header'...")
    try:
        header = await generate_cart_summary_header(
            item_count=5,
            total=67.89
        )
        print(f"   ✓ {header}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 10: Unknown Type (Fallback)
    print("\n10. Testing unknown message type (fallback)...")
    try:
        message = await generate_dynamic_message("unknown_type")
        print(f"   ✓ {message}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test 11: Fallback Messages
    print("\n11. Testing fallback messages...")
    fallback_types = [
        "greeting",
        "item_added",
        "cart_empty",
        "checkout_start",
        "order_confirmed",
        "request_phone",
    ]

    for msg_type in fallback_types:
        fallback = _get_fallback_message(msg_type, {})
        print(f"   ✓ {msg_type}: {fallback}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_all_messages())
