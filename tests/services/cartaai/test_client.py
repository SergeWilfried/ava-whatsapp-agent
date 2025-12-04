"""Unit tests for CartaAI API client."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession, ClientResponse, ClientError
from aiohttp.test_utils import make_mocked_coro
import aioresponses

from ai_companion.services.cartaai.client import (
    CartaAIClient,
    CartaAIAPIException,
    CartaAINetworkException,
    RateLimitStrategy,
)


@pytest.fixture
def client_config():
    """Default client configuration."""
    return {
        "base_url": "https://api.test.com/api/v1",
        "subdomain": "test-restaurant",
        "local_id": "branch-01",
        "api_key": "test_api_key_123",
        "timeout": 10,
        "max_retries": 3,
        "enable_logging": False,
    }


@pytest.fixture
async def client(client_config):
    """Create CartaAI client for testing."""
    async with CartaAIClient(**client_config) as client:
        yield client


class TestCartaAIClientInitialization:
    """Test client initialization and configuration."""

    def test_init_with_required_params(self):
        """Test initialization with required parameters only."""
        client = CartaAIClient(
            base_url="https://api.test.com",
            subdomain="test",
        )
        assert client.base_url == "https://api.test.com"
        assert client.subdomain == "test"
        assert client.local_id is None
        assert client.api_key is None

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        client = CartaAIClient(
            base_url="https://api.test.com/",  # With trailing slash
            subdomain="test",
            local_id="loc01",
            api_key="key123",
            timeout=30,
            max_retries=5,
            retry_delay=2.0,
            rate_limit_strategy=RateLimitStrategy.FIXED_DELAY,
            max_concurrent_requests=20,
            enable_logging=True,
        )
        assert client.base_url == "https://api.test.com"  # Trailing slash removed
        assert client.subdomain == "test"
        assert client.local_id == "loc01"
        assert client.api_key == "key123"
        assert client.max_retries == 5
        assert client.retry_delay == 2.0
        assert client.rate_limit_strategy == RateLimitStrategy.FIXED_DELAY
        assert client.max_concurrent_requests == 20
        assert client.enable_logging is True


class TestCartaAIClientHeaders:
    """Test HTTP header generation."""

    def test_headers_without_api_key(self):
        """Test headers when no API key provided."""
        client = CartaAIClient(base_url="https://api.test.com", subdomain="test")
        headers = client._get_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert "X-Service-API-Key" not in headers

    def test_headers_with_api_key(self):
        """Test headers with API key authentication."""
        client = CartaAIClient(
            base_url="https://api.test.com",
            subdomain="test",
            api_key="my_secret_key",
        )
        headers = client._get_headers()

        assert headers["X-Service-API-Key"] == "my_secret_key"
        assert headers["Content-Type"] == "application/json"


class TestCartaAIClientParameters:
    """Test parameter handling."""

    def test_add_default_params_empty(self):
        """Test adding default params when none provided."""
        client = CartaAIClient(
            base_url="https://api.test.com",
            subdomain="test-sub",
            local_id="loc01",
        )
        params = client._add_default_params(None, "/menu2/bot-structure")

        assert params["subDomain"] == "test-sub"
        assert params["localId"] == "loc01"

    def test_add_default_params_with_existing(self):
        """Test adding default params with existing params."""
        client = CartaAIClient(
            base_url="https://api.test.com",
            subdomain="test-sub",
            local_id="loc01",
        )
        existing_params = {"custom": "value"}
        params = client._add_default_params(existing_params, "/menu2/bot-structure")

        assert params["subDomain"] == "test-sub"
        assert params["localId"] == "loc01"
        assert params["custom"] == "value"

    def test_skip_params_in_url_path(self):
        """Test that params are not added if in URL path."""
        client = CartaAIClient(
            base_url="https://api.test.com",
            subdomain="test-sub",
            local_id="loc01",
        )
        # Endpoint has {subdomain} in path
        params = client._add_default_params(None, "/order/{subdomain}/{localId}")

        # Should not add subDomain or localId to params
        assert "subDomain" not in params
        assert "localId" not in params


class TestCartaAIClientRetryLogic:
    """Test retry logic and backoff strategies."""

    def test_calculate_retry_delay_exponential(self):
        """Test exponential backoff calculation."""
        client = CartaAIClient(
            base_url="https://api.test.com",
            subdomain="test",
            retry_delay=1.0,
            rate_limit_strategy=RateLimitStrategy.EXPONENTIAL_BACKOFF,
        )

        assert client._calculate_retry_delay(0) == 1.0  # 2^0 = 1
        assert client._calculate_retry_delay(1) == 2.0  # 2^1 = 2
        assert client._calculate_retry_delay(2) == 4.0  # 2^2 = 4
        assert client._calculate_retry_delay(3) == 8.0  # 2^3 = 8

    def test_calculate_retry_delay_fixed(self):
        """Test fixed delay calculation."""
        client = CartaAIClient(
            base_url="https://api.test.com",
            subdomain="test",
            retry_delay=2.5,
            rate_limit_strategy=RateLimitStrategy.FIXED_DELAY,
        )

        assert client._calculate_retry_delay(0) == 2.5
        assert client._calculate_retry_delay(1) == 2.5
        assert client._calculate_retry_delay(2) == 2.5

    def test_calculate_retry_delay_adaptive(self):
        """Test adaptive delay with jitter."""
        client = CartaAIClient(
            base_url="https://api.test.com",
            subdomain="test",
            retry_delay=1.0,
            rate_limit_strategy=RateLimitStrategy.ADAPTIVE,
        )

        # Adaptive adds jitter, so check range
        delay = client._calculate_retry_delay(1)
        assert 2.0 <= delay <= 2.2  # 2^1 = 2, plus up to 10% jitter


@pytest.mark.asyncio
class TestCartaAIClientRequests:
    """Test HTTP request methods."""

    async def test_get_menu_structure_success(self, client_config):
        """Test successful menu structure retrieval."""
        mock_response = {
            "type": "1",
            "message": "Menu structure retrieved",
            "data": {
                "categories": [
                    {
                        "id": "cat001",
                        "name": "Burgers",
                        "products": [],
                    }
                ]
            },
        }

        with aioresponses.aioresponses() as m:
            m.get(
                "https://api.test.com/api/v1/menu2/bot-structure",
                payload=mock_response,
                status=200,
            )

            async with CartaAIClient(**client_config) as client:
                result = await client.get_menu_structure()

                assert result["type"] == "1"
                assert result["message"] == "Menu structure retrieved"
                assert len(result["data"]["categories"]) == 1
                assert result["data"]["categories"][0]["name"] == "Burgers"

    async def test_get_product_details_success(self, client_config):
        """Test successful product details retrieval."""
        mock_response = {
            "success": True,
            "message": "Products retrieved",
            "data": [
                {
                    "_id": "prod001",
                    "name": "Classic Burger",
                    "price": 15.99,
                    "presentations": [],
                    "modifiers": [],
                }
            ],
        }

        with aioresponses.aioresponses() as m:
            m.post(
                f"https://api.test.com/api/v1/menu/getProductInMenu/{client_config['local_id']}/{client_config['subdomain']}",
                payload=mock_response,
                status=200,
            )

            async with CartaAIClient(**client_config) as client:
                result = await client.get_product_details(["prod001"])

                assert result["success"] is True
                assert len(result["data"]) == 1
                assert result["data"][0]["name"] == "Classic Burger"

    async def test_create_order_success(self, client_config):
        """Test successful order creation."""
        order_data = {
            "customer": {"name": "John Doe", "phone": "+51987654321"},
            "items": [],
            "type": "delivery",
            "paymentMethod": "cash",
            "source": "whatsapp",
        }

        mock_response = {
            "type": "1",
            "message": "Order created successfully",
            "data": {
                "_id": "order123",
                "orderNumber": "ORD-2024-001234",
                "status": "pending",
                "total": 45.99,
            },
        }

        with aioresponses.aioresponses() as m:
            m.post(
                "https://api.test.com/api/v1/order",
                payload=mock_response,
                status=201,
            )

            async with CartaAIClient(**client_config) as client:
                result = await client.create_order(order_data)

                assert result["type"] == "1"
                assert result["data"]["_id"] == "order123"
                assert result["data"]["orderNumber"] == "ORD-2024-001234"

    async def test_get_order_success(self, client_config):
        """Test successful order retrieval."""
        mock_response = {
            "type": "1",
            "message": "Order retrieved",
            "data": {
                "_id": "order123",
                "status": "preparing",
            },
        }

        with aioresponses.aioresponses() as m:
            m.get(
                "https://api.test.com/api/v1/order/get-order/order123",
                payload=mock_response,
                status=200,
            )

            async with CartaAIClient(**client_config) as client:
                result = await client.get_order("order123")

                assert result["type"] == "1"
                assert result["data"]["status"] == "preparing"


@pytest.mark.asyncio
class TestCartaAIClientErrorHandling:
    """Test error handling and exceptions."""

    async def test_api_error_400(self, client_config):
        """Test handling of 400 Bad Request error."""
        mock_response = {
            "type": "3",
            "message": "Invalid request parameters",
        }

        with aioresponses.aioresponses() as m:
            m.get(
                "https://api.test.com/api/v1/menu2/bot-structure",
                payload=mock_response,
                status=400,
            )

            async with CartaAIClient(**client_config) as client:
                with pytest.raises(CartaAIAPIException) as exc_info:
                    await client.get_menu_structure()

                assert exc_info.value.status_code == 400
                assert "Invalid request parameters" in exc_info.value.message

    async def test_api_error_404(self, client_config):
        """Test handling of 404 Not Found error."""
        mock_response = {
            "type": "3",
            "message": "Resource not found",
        }

        with aioresponses.aioresponses() as m:
            m.get(
                "https://api.test.com/api/v1/order/get-order/invalid_id",
                payload=mock_response,
                status=404,
            )

            async with CartaAIClient(**client_config) as client:
                with pytest.raises(CartaAIAPIException) as exc_info:
                    await client.get_order("invalid_id")

                assert exc_info.value.status_code == 404

    async def test_api_error_500_with_retry(self, client_config):
        """Test handling of 500 error with retry logic."""
        client_config["max_retries"] = 2
        client_config["retry_delay"] = 0.1  # Fast retry for testing

        mock_response = {
            "type": "3",
            "message": "Internal server error",
        }

        with aioresponses.aioresponses() as m:
            # First attempt: 500 error
            m.get(
                "https://api.test.com/api/v1/menu2/bot-structure",
                payload=mock_response,
                status=500,
            )
            # Second attempt: 500 error
            m.get(
                "https://api.test.com/api/v1/menu2/bot-structure",
                payload=mock_response,
                status=500,
            )
            # Third attempt: success
            m.get(
                "https://api.test.com/api/v1/menu2/bot-structure",
                payload={"type": "1", "data": {}},
                status=200,
            )

            async with CartaAIClient(**client_config) as client:
                result = await client.get_menu_structure()

                assert result["type"] == "1"
                # Check metrics
                metrics = client.get_metrics()
                assert metrics["retried_requests"] == 2

    async def test_rate_limit_429_with_retry(self, client_config):
        """Test handling of 429 rate limit with retry."""
        client_config["max_retries"] = 1
        client_config["retry_delay"] = 0.1

        with aioresponses.aioresponses() as m:
            # First attempt: rate limited
            m.get(
                "https://api.test.com/api/v1/menu2/bot-structure",
                payload={"error": "Rate limit exceeded"},
                status=429,
                headers={"Retry-After": "1"},
            )
            # Second attempt: success
            m.get(
                "https://api.test.com/api/v1/menu2/bot-structure",
                payload={"type": "1", "data": {}},
                status=200,
            )

            async with CartaAIClient(**client_config) as client:
                result = await client.get_menu_structure()

                assert result["type"] == "1"
                metrics = client.get_metrics()
                assert metrics["rate_limited_requests"] == 1


@pytest.mark.asyncio
class TestCartaAIClientMetrics:
    """Test metrics tracking."""

    async def test_metrics_initialization(self, client_config):
        """Test that metrics are initialized correctly."""
        async with CartaAIClient(**client_config) as client:
            metrics = client.get_metrics()

            assert metrics["total_requests"] == 0
            assert metrics["successful_requests"] == 0
            assert metrics["failed_requests"] == 0
            assert metrics["success_rate"] == 0
            assert metrics["average_response_time"] == 0

    async def test_metrics_after_successful_request(self, client_config):
        """Test metrics after successful request."""
        with aioresponses.aioresponses() as m:
            m.get(
                "https://api.test.com/api/v1/menu2/bot-structure",
                payload={"type": "1", "data": {}},
                status=200,
            )

            async with CartaAIClient(**client_config) as client:
                await client.get_menu_structure()

                metrics = client.get_metrics()
                assert metrics["total_requests"] == 1
                assert metrics["successful_requests"] == 1
                assert metrics["failed_requests"] == 0
                assert metrics["success_rate"] == 100.0

    async def test_metrics_reset(self, client_config):
        """Test metrics reset functionality."""
        with aioresponses.aioresponses() as m:
            m.get(
                "https://api.test.com/api/v1/menu2/bot-structure",
                payload={"type": "1", "data": {}},
                status=200,
            )

            async with CartaAIClient(**client_config) as client:
                await client.get_menu_structure()

                # Verify metrics recorded
                metrics = client.get_metrics()
                assert metrics["total_requests"] == 1

                # Reset metrics
                client.reset_metrics()

                # Verify reset
                metrics = client.get_metrics()
                assert metrics["total_requests"] == 0
                assert metrics["successful_requests"] == 0


@pytest.mark.asyncio
class TestCartaAIClientContextManager:
    """Test context manager functionality."""

    async def test_context_manager_creates_session(self, client_config):
        """Test that context manager creates session."""
        async with CartaAIClient(**client_config) as client:
            assert client.session is not None
            assert not client.session.closed

    async def test_context_manager_closes_session(self, client_config):
        """Test that context manager closes session on exit."""
        client = CartaAIClient(**client_config)
        async with client:
            session = client.session
            assert session is not None

        # Session should be closed after exiting context
        assert session.closed or client.session is None


@pytest.mark.asyncio
class TestCartaAIClientDeliveryEndpoints:
    """Test delivery-related endpoints."""

    async def test_get_delivery_zones_success(self, client_config):
        """Test successful delivery zones retrieval."""
        mock_response = {
            "type": "1",
            "message": "Delivery zones retrieved",
            "data": [
                {
                    "_id": "zone001",
                    "zoneName": "Downtown",
                    "deliveryCost": 5.00,
                    "minimumOrder": 20.00,
                }
            ],
        }

        with aioresponses.aioresponses() as m:
            m.get(
                f"https://api.test.com/api/v1/delivery/zones/{client_config['subdomain']}/{client_config['local_id']}",
                payload=mock_response,
                status=200,
            )

            async with CartaAIClient(**client_config) as client:
                result = await client.get_delivery_zones()

                assert result["type"] == "1"
                assert len(result["data"]) == 1
                assert result["data"][0]["zoneName"] == "Downtown"

    async def test_get_available_drivers_success(self, client_config):
        """Test successful available drivers retrieval."""
        mock_response = {
            "type": "1",
            "message": "Drivers retrieved",
            "data": [{"_id": "driver1", "name": "John", "status": "available"}],
        }

        with aioresponses.aioresponses() as m:
            m.get(
                f"https://api.test.com/api/v1/delivery/drivers/available/{client_config['subdomain']}/{client_config['local_id']}",
                payload=mock_response,
                status=200,
            )

            async with CartaAIClient(**client_config) as client:
                result = await client.get_available_drivers()

                assert result["type"] == "1"
                assert len(result["data"]) == 1
                assert result["data"][0]["name"] == "John"
