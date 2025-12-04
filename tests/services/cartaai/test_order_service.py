"""Tests for OrderService and order payload builder."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from ai_companion.services.cartaai.order_service import (
    OrderService,
    build_order_payload,
    build_order_item,
    build_modifiers_from_extras,
    map_delivery_method_to_api,
    map_payment_method_to_api,
)
from ai_companion.modules.cart.models import (
    ShoppingCart,
    CartItem,
    CartItemCustomization,
    DeliveryMethod,
    PaymentMethod,
)


class TestBuildOrderPayload:
    """Test order payload building."""

    def test_basic_payload(self):
        """Test basic order payload with minimal fields."""
        cart = ShoppingCart()
        cart.add_item(
            CartItem(
                id="item1",
                menu_item_id="prod001",
                name="Burger",
                base_price=15.99,
                quantity=2,
            )
        )

        payload = build_order_payload(
            cart=cart,
            customer_name="John Doe",
            customer_phone="+51987654321",
            delivery_method=DeliveryMethod.DELIVERY,
            payment_method=PaymentMethod.CASH,
            delivery_address="123 Main St",
        )

        assert payload["customer"]["name"] == "John Doe"
        assert payload["customer"]["phone"] == "+51987654321"
        assert payload["customer"]["address"]["street"] == "123 Main St"
        assert len(payload["items"]) == 1
        assert payload["items"][0]["productId"] == "prod001"
        assert payload["items"][0]["quantity"] == 2
        assert payload["type"] == "delivery"
        assert payload["paymentMethod"] == "cash"
        assert payload["source"] == "whatsapp"

    def test_payload_with_pickup(self):
        """Test payload for pickup order."""
        cart = ShoppingCart()
        cart.add_item(
            CartItem(
                id="item1",
                menu_item_id="prod001",
                name="Burger",
                base_price=15.99,
                quantity=1,
            )
        )

        payload = build_order_payload(
            cart=cart,
            customer_name="Jane Smith",
            customer_phone="+51987654322",
            delivery_method=DeliveryMethod.PICKUP,
            payment_method=PaymentMethod.CREDIT_CARD,
        )

        assert "address" not in payload["customer"]
        assert payload["type"] == "pickup"
        assert payload["paymentMethod"] == "card"

    def test_payload_with_special_instructions(self):
        """Test payload with special instructions."""
        cart = ShoppingCart()
        cart.add_item(
            CartItem(
                id="item1",
                menu_item_id="prod001",
                name="Burger",
                base_price=15.99,
                quantity=1,
            )
        )

        payload = build_order_payload(
            cart=cart,
            customer_name="Test User",
            customer_phone="+51987654323",
            delivery_method=DeliveryMethod.DELIVERY,
            payment_method=PaymentMethod.CASH,
            delivery_address="456 Oak Ave",
            delivery_instructions="Ring doorbell twice",
            special_instructions="Extra napkins please",
        )

        assert payload["customer"]["address"]["reference"] == "Ring doorbell twice"
        assert payload["notes"] == "Extra napkins please"

    def test_payload_with_scheduled_time(self):
        """Test payload with scheduled delivery."""
        cart = ShoppingCart()
        cart.add_item(
            CartItem(
                id="item1",
                menu_item_id="prod001",
                name="Burger",
                base_price=15.99,
                quantity=1,
            )
        )

        scheduled_time = datetime(2024, 12, 25, 18, 30)

        payload = build_order_payload(
            cart=cart,
            customer_name="Test User",
            customer_phone="+51987654323",
            delivery_method=DeliveryMethod.DELIVERY,
            payment_method=PaymentMethod.CASH,
            delivery_address="789 Elm St",
            scheduled_time=scheduled_time,
        )

        assert payload["type"] == "scheduled_delivery"
        assert payload["scheduledTime"] == scheduled_time.isoformat()


class TestBuildOrderItem:
    """Test building individual order items."""

    def test_basic_item(self):
        """Test basic item without customization."""
        cart_item = CartItem(
            id="item1",
            menu_item_id="prod001",
            name="Classic Burger",
            base_price=15.99,
            quantity=2,
        )

        item_data = build_order_item(cart_item)

        assert item_data["productId"] == "prod001"
        assert item_data["name"] == "Classic Burger"
        assert item_data["quantity"] == 2
        assert item_data["unitPrice"] == 15.99
        assert "presentationId" not in item_data
        assert "modifiers" not in item_data

    def test_item_with_size(self):
        """Test item with size customization."""
        cart_item = CartItem(
            id="item1",
            menu_item_id="prod001",
            name="Classic Burger",
            base_price=18.99,
            quantity=1,
            customization=CartItemCustomization(
                size="pres002",  # API presentation ID
                price_adjustment=0.0,
            ),
        )

        item_data = build_order_item(cart_item)

        assert item_data["presentationId"] == "pres002"

    def test_item_with_special_instructions(self):
        """Test item with special instructions."""
        cart_item = CartItem(
            id="item1",
            menu_item_id="prod001",
            name="Classic Burger",
            base_price=15.99,
            quantity=1,
            customization=CartItemCustomization(
                special_instructions="No onions",
            ),
        )

        item_data = build_order_item(cart_item)

        assert item_data["notes"] == "No onions"

    def test_item_with_extras(self):
        """Test item with extras."""
        cart_item = CartItem(
            id="item1",
            menu_item_id="prod001",
            name="Classic Burger",
            base_price=15.99,
            quantity=1,
            customization=CartItemCustomization(
                extras=["extra_cheese", "bacon"],
                price_adjustment=4.50,
            ),
        )

        item_data = build_order_item(cart_item)

        assert "modifiers" in item_data
        assert len(item_data["modifiers"]) == 1
        assert len(item_data["modifiers"][0]["options"]) == 2


class TestBuildModifiersFromExtras:
    """Test converting extras to modifiers format."""

    def test_legacy_extras(self):
        """Test legacy extras format."""
        extras = ["extra_cheese", "bacon", "mushrooms"]

        modifiers = build_modifiers_from_extras(extras)

        assert len(modifiers) == 1
        assert modifiers[0]["modifierId"] == "legacy_extras"
        assert modifiers[0]["name"] == "Extras"
        assert len(modifiers[0]["options"]) == 3
        assert modifiers[0]["options"][0]["optionId"] == "extra_cheese"

    def test_api_format_extras(self):
        """Test API format extras (mod_{modId}_{optId})."""
        extras = [
            "mod_mod001_opt001",
            "mod_mod001_opt002",
            "mod_mod002_opt005",
        ]

        modifiers = build_modifiers_from_extras(extras)

        assert len(modifiers) == 2
        # Check mod001 has 2 options
        mod001 = next(m for m in modifiers if m["modifierId"] == "mod001")
        assert len(mod001["options"]) == 2
        # Check mod002 has 1 option
        mod002 = next(m for m in modifiers if m["modifierId"] == "mod002")
        assert len(mod002["options"]) == 1

    def test_empty_extras(self):
        """Test empty extras list."""
        modifiers = build_modifiers_from_extras([])

        assert modifiers == []


class TestDeliveryMethodMapping:
    """Test delivery method to API type mapping."""

    def test_immediate_delivery(self):
        """Test immediate delivery mapping."""
        result = map_delivery_method_to_api(DeliveryMethod.DELIVERY)
        assert result == "delivery"

    def test_immediate_pickup(self):
        """Test immediate pickup mapping."""
        result = map_delivery_method_to_api(DeliveryMethod.PICKUP)
        assert result == "pickup"

    def test_dine_in(self):
        """Test dine-in mapping."""
        result = map_delivery_method_to_api(DeliveryMethod.DINE_IN)
        assert result == "on_site"

    def test_scheduled_delivery(self):
        """Test scheduled delivery mapping."""
        scheduled_time = datetime(2024, 12, 25, 18, 30)
        result = map_delivery_method_to_api(DeliveryMethod.DELIVERY, scheduled_time)
        assert result == "scheduled_delivery"

    def test_scheduled_pickup(self):
        """Test scheduled pickup mapping."""
        scheduled_time = datetime(2024, 12, 25, 18, 30)
        result = map_delivery_method_to_api(DeliveryMethod.PICKUP, scheduled_time)
        assert result == "scheduled_pickup"


class TestPaymentMethodMapping:
    """Test payment method to API format mapping."""

    def test_cash(self):
        """Test cash payment mapping."""
        result = map_payment_method_to_api(PaymentMethod.CASH)
        assert result == "cash"

    def test_credit_card(self):
        """Test credit card mapping."""
        result = map_payment_method_to_api(PaymentMethod.CREDIT_CARD)
        assert result == "card"

    def test_debit_card(self):
        """Test debit card mapping."""
        result = map_payment_method_to_api(PaymentMethod.DEBIT_CARD)
        assert result == "card"

    def test_mobile_payment(self):
        """Test mobile payment mapping."""
        result = map_payment_method_to_api(PaymentMethod.MOBILE_PAYMENT)
        assert result == "yape"  # Default for Peru

    def test_online(self):
        """Test online payment mapping."""
        result = map_payment_method_to_api(PaymentMethod.ONLINE)
        assert result == "card"


class TestOrderService:
    """Test OrderService class."""

    @pytest.fixture
    def mock_client(self):
        """Create mock CartaAI client."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def order_service(self, mock_client):
        """Create OrderService with mock client."""
        return OrderService(mock_client)

    @pytest.fixture
    def sample_cart(self):
        """Create sample shopping cart."""
        cart = ShoppingCart()
        cart.add_item(
            CartItem(
                id="item1",
                menu_item_id="prod001",
                name="Burger",
                base_price=15.99,
                quantity=2,
            )
        )
        return cart

    @pytest.mark.asyncio
    async def test_create_order_success(self, order_service, mock_client, sample_cart):
        """Test successful order creation."""
        mock_client.create_order.return_value = {
            "type": "1",
            "message": "Order created successfully",
            "data": {
                "_id": "order123",
                "orderNumber": "ORD-2024-001234",
                "status": "pending",
                "total": 45.99,
            },
        }

        response = await order_service.create_order(
            cart=sample_cart,
            customer_name="John Doe",
            customer_phone="+51987654321",
            delivery_method=DeliveryMethod.DELIVERY,
            payment_method=PaymentMethod.CASH,
            delivery_address="123 Main St",
        )

        assert response["type"] == "1"
        assert response["data"]["_id"] == "order123"
        assert response["data"]["orderNumber"] == "ORD-2024-001234"
        mock_client.create_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_order_empty_cart(self, order_service, sample_cart):
        """Test creating order with empty cart."""
        empty_cart = ShoppingCart()

        with pytest.raises(ValueError, match="Cannot create order from empty cart"):
            await order_service.create_order(
                cart=empty_cart,
                customer_name="John Doe",
                customer_phone="+51987654321",
                delivery_method=DeliveryMethod.DELIVERY,
                payment_method=PaymentMethod.CASH,
                delivery_address="123 Main St",
            )

    @pytest.mark.asyncio
    async def test_create_order_delivery_without_address(
        self, order_service, sample_cart
    ):
        """Test creating delivery order without address."""
        with pytest.raises(
            ValueError, match="Delivery address required for delivery orders"
        ):
            await order_service.create_order(
                cart=sample_cart,
                customer_name="John Doe",
                customer_phone="+51987654321",
                delivery_method=DeliveryMethod.DELIVERY,
                payment_method=PaymentMethod.CASH,
            )

    @pytest.mark.asyncio
    async def test_create_order_api_error(self, order_service, mock_client, sample_cart):
        """Test order creation with API error."""
        mock_client.create_order.return_value = {
            "type": "3",
            "message": "Validation error",
            "data": None,
        }

        with pytest.raises(ValueError, match="Order creation failed"):
            await order_service.create_order(
                cart=sample_cart,
                customer_name="John Doe",
                customer_phone="+51987654321",
                delivery_method=DeliveryMethod.PICKUP,
                payment_method=PaymentMethod.CASH,
            )

    @pytest.mark.asyncio
    async def test_get_order(self, order_service, mock_client):
        """Test getting order by ID."""
        mock_client.get_order.return_value = {
            "type": "1",
            "message": "Order retrieved",
            "data": {
                "_id": "order123",
                "orderNumber": "ORD-2024-001234",
                "status": "preparing",
            },
        }

        response = await order_service.get_order("order123")

        assert response["type"] == "1"
        assert response["data"]["status"] == "preparing"
        mock_client.get_order.assert_called_once_with("order123")

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, order_service, mock_client):
        """Test getting non-existent order."""
        mock_client.get_order.return_value = {
            "type": "3",
            "message": "Order not found",
            "data": None,
        }

        with pytest.raises(ValueError, match="Failed to fetch order"):
            await order_service.get_order("invalid_id")

    @pytest.mark.asyncio
    async def test_get_customer_orders(self, order_service, mock_client):
        """Test getting customer order history."""
        mock_client.get_customer_orders.return_value = {
            "type": "1",
            "message": "Orders retrieved",
            "data": [
                {"_id": "order1", "orderNumber": "ORD-001"},
                {"_id": "order2", "orderNumber": "ORD-002"},
            ],
        }

        orders = await order_service.get_customer_orders("+51987654321")

        assert len(orders) == 2
        assert orders[0]["orderNumber"] == "ORD-001"
        mock_client.get_customer_orders.assert_called_once_with("+51987654321", None)

    @pytest.mark.asyncio
    async def test_get_customer_orders_with_status(self, order_service, mock_client):
        """Test getting customer orders filtered by status."""
        mock_client.get_customer_orders.return_value = {
            "type": "1",
            "message": "Orders retrieved",
            "data": [{"_id": "order1", "status": "pending"}],
        }

        orders = await order_service.get_customer_orders("+51987654321", "pending")

        assert len(orders) == 1
        mock_client.get_customer_orders.assert_called_once_with(
            "+51987654321", "pending"
        )

    @pytest.mark.asyncio
    async def test_get_customer_orders_empty(self, order_service, mock_client):
        """Test getting customer orders when none exist."""
        mock_client.get_customer_orders.return_value = {
            "type": "3",
            "message": "No orders found",
            "data": None,
        }

        orders = await order_service.get_customer_orders("+51987654321")

        assert orders == []
