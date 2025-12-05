"""Tests for AI-powered message generation."""

import pytest
from ai_companion.graph.utils.message_generator import (
    generate_dynamic_message,
    generate_cart_summary_header,
    _get_fallback_message,
)


class TestMessageGenerator:
    """Test suite for dynamic message generation."""

    @pytest.mark.asyncio
    async def test_item_added_message(self):
        """Test item added message generation."""
        message = await generate_dynamic_message(
            "item_added",
            {"item_name": "Margherita Pizza", "price": 12.99}
        )

        assert message
        assert len(message) > 0
        assert len(message) < 300  # Should be brief
        print(f"✓ Item added message: {message}")

    @pytest.mark.asyncio
    async def test_cart_empty_message(self):
        """Test cart empty message generation."""
        message = await generate_dynamic_message("cart_empty")

        assert message
        assert len(message) > 0
        print(f"✓ Cart empty message: {message}")

    @pytest.mark.asyncio
    async def test_checkout_start_message(self):
        """Test checkout start message generation."""
        message = await generate_dynamic_message(
            "checkout_start",
            {"item_count": 3, "total": 45.50}
        )

        assert message
        assert len(message) > 0
        print(f"✓ Checkout message: {message}")

    @pytest.mark.asyncio
    async def test_order_confirmed_message(self):
        """Test order confirmation message generation."""
        message = await generate_dynamic_message(
            "order_confirmed",
            {"order_id": "12345", "total": 45.50}
        )

        assert message
        assert len(message) > 0
        print(f"✓ Order confirmed message: {message}")

    @pytest.mark.asyncio
    async def test_request_phone_message(self):
        """Test phone request message generation."""
        message = await generate_dynamic_message("request_phone")

        assert message
        assert len(message) > 0
        print(f"✓ Request phone message: {message}")

    @pytest.mark.asyncio
    async def test_size_selected_message(self):
        """Test size selection confirmation."""
        message = await generate_dynamic_message(
            "size_selected",
            {"size_name": "Large", "price": 15.99}
        )

        assert message
        assert len(message) > 0
        print(f"✓ Size selected message: {message}")

    @pytest.mark.asyncio
    async def test_item_not_found_message(self):
        """Test item not found message generation."""
        message = await generate_dynamic_message("item_not_found")

        assert message
        assert len(message) > 0
        print(f"✓ Item not found message: {message}")

    @pytest.mark.asyncio
    async def test_item_unavailable_message(self):
        """Test item unavailable message generation."""
        message = await generate_dynamic_message(
            "item_unavailable",
            {"item_name": "Special Pizza"}
        )

        assert message
        assert len(message) > 0
        print(f"✓ Item unavailable message: {message}")

    @pytest.mark.asyncio
    async def test_cart_summary_header(self):
        """Test cart summary header generation."""
        header = await generate_cart_summary_header(
            item_count=5,
            total=67.89
        )

        assert header
        assert len(header) > 0
        print(f"✓ Cart summary header: {header}")

    @pytest.mark.asyncio
    async def test_unknown_message_type_fallback(self):
        """Test that unknown message types fall back gracefully."""
        message = await generate_dynamic_message("unknown_type")

        assert message
        assert message == "Thank you!"
        print(f"✓ Fallback for unknown type: {message}")

    def test_fallback_messages(self):
        """Test that all fallback messages are defined."""
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
            assert fallback
            assert len(fallback) > 0
            print(f"✓ Fallback for {msg_type}: {fallback}")

    @pytest.mark.asyncio
    async def test_message_consistency(self):
        """Test that repeated calls with same context produce similar messages."""
        context = {"item_name": "Pizza", "price": 12.99}

        # Generate same message twice
        message1 = await generate_dynamic_message("item_added", context)
        message2 = await generate_dynamic_message("item_added", context)

        # Messages should both be valid
        assert message1
        assert message2

        # They may differ slightly due to temperature, but should be similar length
        assert abs(len(message1) - len(message2)) < 100

        print(f"✓ Message 1: {message1}")
        print(f"✓ Message 2: {message2}")


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v", "-s"])
