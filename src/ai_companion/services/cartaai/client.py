"""CartaAI API HTTP client with authentication, retry logic, and rate limiting."""

import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    EXPONENTIAL_BACKOFF = "exponential"
    FIXED_DELAY = "fixed"
    ADAPTIVE = "adaptive"


class CartaAIClient:
    """Async HTTP client for CartaAI API with authentication and error handling.

    Features:
    - Authentication via X-Service-API-Key header
    - Automatic retry with exponential backoff
    - Rate limiting with multiple strategies
    - Request/response logging
    - Connection pooling
    - Timeout handling

    Example:
        async with CartaAIClient(
            base_url="https://ssgg.api.cartaai.pe/api/v1",
            subdomain="restaurant",
            local_id="branch01",
            api_key="your_api_key"
        ) as client:
            menu = await client.get_menu_structure()
    """

    def __init__(
        self,
        base_url: str,
        subdomain: str,
        local_id: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_strategy: RateLimitStrategy = RateLimitStrategy.EXPONENTIAL_BACKOFF,
        max_concurrent_requests: int = 10,
        enable_logging: bool = True,
    ):
        """Initialize CartaAI API client.

        Args:
            base_url: Base API URL (e.g., "https://ssgg.api.cartaai.pe/api/v1")
            subdomain: Business subdomain identifier
            local_id: Branch/location identifier (optional)
            api_key: API authentication key for X-Service-API-Key header
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
            rate_limit_strategy: Strategy for handling rate limits
            max_concurrent_requests: Maximum concurrent requests allowed
            enable_logging: Enable request/response logging
        """
        self.base_url = base_url.rstrip('/')
        self.subdomain = subdomain
        self.local_id = local_id
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_strategy = rate_limit_strategy
        self.max_concurrent_requests = max_concurrent_requests
        self.enable_logging = enable_logging

        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()

        # Rate limiting
        self._rate_limit_semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._last_request_time: Optional[datetime] = None
        self._rate_limit_reset_time: Optional[datetime] = None
        self._request_count = 0
        self._rate_limit_lock = asyncio.Lock()

        # Metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retried_requests": 0,
            "rate_limited_requests": 0,
            "total_response_time": 0.0,
        }

    async def __aenter__(self):
        """Context manager entry - creates session."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes session."""
        await self.close()

    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self.session is None or self.session.closed:
            async with self._session_lock:
                if self.session is None or self.session.closed:
                    connector = aiohttp.TCPConnector(
                        limit=self.max_concurrent_requests,
                        limit_per_host=self.max_concurrent_requests,
                        ttl_dns_cache=300,  # 5 minutes DNS cache
                    )
                    self.session = aiohttp.ClientSession(
                        timeout=self.timeout,
                        connector=connector,
                    )
                    if self.enable_logging:
                        logger.info("CartaAI API session created")

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            if self.enable_logging:
                logger.info("CartaAI API session closed")
            self.session = None

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers with authentication.

        Returns:
            Dictionary of HTTP headers including X-Service-API-Key authentication
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.api_key:
            headers["X-Service-API-Key"] = self.api_key

        return headers

    def _add_default_params(self, params: Optional[Dict] = None, endpoint: str = "") -> Dict[str, Any]:
        """Add default subdomain/localId parameters if not in endpoint path.

        Args:
            params: Existing query parameters
            endpoint: API endpoint path

        Returns:
            Parameters with subdomain/localId added if needed
        """
        if params is None:
            params = {}

        # Only add params if not already in URL path
        if "{subdomain}" not in endpoint and "{subDomain}" not in endpoint:
            params.setdefault("subDomain", self.subdomain)

        if "{localId}" not in endpoint and self.local_id:
            params.setdefault("localId", self.local_id)

        return params

    async def _apply_rate_limiting(self):
        """Apply rate limiting strategy before making request."""
        async with self._rate_limit_lock:
            # Check if we're within rate limit reset period
            if self._rate_limit_reset_time and datetime.now() < self._rate_limit_reset_time:
                wait_time = (self._rate_limit_reset_time - datetime.now()).total_seconds()
                if self.enable_logging:
                    logger.warning(f"Rate limit active, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self._rate_limit_reset_time = None

    async def _handle_rate_limit_response(self, response: aiohttp.ClientResponse):
        """Handle rate limit response (429 status).

        Args:
            response: HTTP response with 429 status code
        """
        self.metrics["rate_limited_requests"] += 1

        # Try to get Retry-After header
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                wait_time = int(retry_after)
            except ValueError:
                # Retry-After might be HTTP-date format
                wait_time = 60
        else:
            # Default wait time if no Retry-After header
            wait_time = 60

        async with self._rate_limit_lock:
            self._rate_limit_reset_time = datetime.now() + timedelta(seconds=wait_time)

        if self.enable_logging:
            logger.warning(f"Rate limited by API, retry after {wait_time}s")

        await asyncio.sleep(wait_time)

    def _calculate_retry_delay(self, retry_count: int) -> float:
        """Calculate delay before next retry based on strategy.

        Args:
            retry_count: Current retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        if self.rate_limit_strategy == RateLimitStrategy.EXPONENTIAL_BACKOFF:
            # Exponential backoff: 1s, 2s, 4s, 8s, ...
            return self.retry_delay * (2 ** retry_count)

        elif self.rate_limit_strategy == RateLimitStrategy.FIXED_DELAY:
            # Fixed delay between retries
            return self.retry_delay

        elif self.rate_limit_strategy == RateLimitStrategy.ADAPTIVE:
            # Adaptive: exponential but with jitter
            import random
            base_delay = self.retry_delay * (2 ** retry_count)
            jitter = random.uniform(0, base_delay * 0.1)  # Add up to 10% jitter
            return base_delay + jitter

        return self.retry_delay

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Any] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Generic request method with retry logic and rate limiting.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON request body
            retry_count: Current retry attempt (internal use)

        Returns:
            Parsed JSON response

        Raises:
            CartaAIAPIException: For API errors (4xx, 5xx)
            CartaAINetworkException: For network/connection errors
        """
        await self._ensure_session()

        # Build URL
        url = f"{self.base_url}{endpoint}"

        # Add default parameters
        params = self._add_default_params(params, endpoint)

        # Apply rate limiting
        await self._apply_rate_limiting()

        # Acquire semaphore for concurrent request limiting
        async with self._rate_limit_semaphore:
            start_time = datetime.now()

            try:
                self.metrics["total_requests"] += 1

                if self.enable_logging:
                    logger.info(
                        f"API Request [{retry_count}/{self.max_retries}]: "
                        f"{method} {url} | Params: {params}"
                    )

                async with self.session.request(
                    method,
                    url,
                    headers=self._get_headers(),
                    params=params,
                    json=json_data,
                ) as response:
                    # Calculate response time
                    response_time = (datetime.now() - start_time).total_seconds()
                    self.metrics["total_response_time"] += response_time

                    # Try to parse JSON response
                    try:
                        response_data = await response.json()
                    except aiohttp.ContentTypeError:
                        # Handle non-JSON responses
                        response_text = await response.text()
                        response_data = {"error": "Non-JSON response", "content": response_text}

                    if self.enable_logging:
                        logger.info(
                            f"API Response: {response.status} | "
                            f"Time: {response_time:.3f}s | "
                            f"Type: {response_data.get('type', 'N/A')}"
                        )

                    # Handle rate limiting (429)
                    if response.status == 429:
                        if retry_count < self.max_retries:
                            await self._handle_rate_limit_response(response)
                            self.metrics["retried_requests"] += 1
                            return await self._request(method, endpoint, params, json_data, retry_count + 1)
                        else:
                            raise CartaAIAPIException(
                                status_code=429,
                                message="Rate limit exceeded and max retries reached",
                                data=response_data,
                            )

                    # Handle client errors (4xx)
                    if 400 <= response.status < 500:
                        self.metrics["failed_requests"] += 1
                        logger.error(f"API Client Error {response.status}: {response_data}")
                        raise CartaAIAPIException(
                            status_code=response.status,
                            message=response_data.get("message", "API client error"),
                            data=response_data,
                        )

                    # Handle server errors (5xx) with retry
                    if response.status >= 500:
                        logger.error(f"API Server Error {response.status}: {response_data}")

                        if retry_count < self.max_retries:
                            delay = self._calculate_retry_delay(retry_count)
                            if self.enable_logging:
                                logger.info(f"Retrying after {delay:.2f}s...")

                            await asyncio.sleep(delay)
                            self.metrics["retried_requests"] += 1
                            return await self._request(method, endpoint, params, json_data, retry_count + 1)
                        else:
                            self.metrics["failed_requests"] += 1
                            raise CartaAIAPIException(
                                status_code=response.status,
                                message=response_data.get("message", "API server error"),
                                data=response_data,
                            )

                    # Success (2xx)
                    self.metrics["successful_requests"] += 1
                    return response_data

            except aiohttp.ClientError as e:
                # Network/connection errors
                logger.error(f"Network error: {str(e)}")

                if retry_count < self.max_retries:
                    delay = self._calculate_retry_delay(retry_count)
                    if self.enable_logging:
                        logger.info(f"Retrying after network error in {delay:.2f}s...")

                    await asyncio.sleep(delay)
                    self.metrics["retried_requests"] += 1
                    return await self._request(method, endpoint, params, json_data, retry_count + 1)
                else:
                    self.metrics["failed_requests"] += 1
                    raise CartaAINetworkException(str(e))

            except asyncio.TimeoutError:
                logger.error(f"Request timeout after {self.timeout.total}s")

                if retry_count < self.max_retries:
                    delay = self._calculate_retry_delay(retry_count)
                    if self.enable_logging:
                        logger.info(f"Retrying after timeout in {delay:.2f}s...")

                    await asyncio.sleep(delay)
                    self.metrics["retried_requests"] += 1
                    return await self._request(method, endpoint, params, json_data, retry_count + 1)
                else:
                    self.metrics["failed_requests"] += 1
                    raise CartaAINetworkException("Request timeout")

    # ============================================
    # MENU ENDPOINTS
    # ============================================

    async def get_menu_structure(self) -> Dict[str, Any]:
        """Get complete menu structure for bot navigation.

        Primary endpoint for displaying menu in WhatsApp bot.

        Returns:
            {
                "type": "1",
                "message": "Menu structure retrieved",
                "data": {
                    "categories": [
                        {
                            "id": "cat123",
                            "name": "Burgers",
                            "products": [...]
                        }
                    ]
                }
            }
        """
        return await self._request("GET", "/menu2/bot-structure")

    async def get_all_categories(self) -> Dict[str, Any]:
        """Get all menu categories for a location.

        Returns:
            {
                "type": "1",
                "message": "Categories retrieved",
                "data": [
                    {"_id": "cat123", "name": "Burgers", ...}
                ]
            }
        """
        endpoint = f"/api/v1/categories/get-all/{self.subdomain}/{self.local_id}"
        return await self._request("GET", endpoint)

    async def get_product_details(self, product_ids: List[str]) -> Dict[str, Any]:
        """Get detailed product information with presentations and modifiers.

        Args:
            product_ids: List of product IDs to fetch

        Returns:
            {
                "success": true,
                "message": "Products retrieved",
                "data": [
                    {
                        "_id": "prod001",
                        "name": "Classic Burger",
                        "presentations": [...],
                        "modifiers": [...]
                    }
                ]
            }
        """
        endpoint = f"/api/v1/menu/getProductInMenu/{self.local_id}/{self.subdomain}"
        return await self._request("POST", endpoint, json_data=product_ids)

    async def get_all_products(self, category_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all products for a location, optionally filtered by category.

        Args:
            category_id: Optional category ID to filter products

        Returns:
            {
                "type": "1",
                "message": "Products retrieved",
                "data": [...]
            }
        """
        endpoint = f"/api/v1/products/get-all/{self.subdomain}/{self.local_id}"
        params = {}
        if category_id:
            params["categoryId"] = category_id
        return await self._request("GET", endpoint, params=params)

    # ============================================
    # ORDER ENDPOINTS
    # ============================================

    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order.

        Args:
            order_data: Order request matching CreateOrderRequest schema
                {
                    "customer": {...},
                    "items": [...],
                    "type": "delivery",
                    "paymentMethod": "cash",
                    "source": "whatsapp"
                }

        Returns:
            {
                "type": "1",
                "message": "Order created successfully",
                "data": {
                    "_id": "order123",
                    "orderNumber": "ORD-2024-001234",
                    "status": "pending",
                    "total": 45.99
                }
            }
        """
        return await self._request("POST", "/api/v1/order", json_data=order_data)

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details and status.

        Args:
            order_id: Order ID returned from create_order

        Returns:
            {
                "type": "1",
                "message": "Order retrieved",
                "data": {
                    "_id": "order123",
                    "orderNumber": "ORD-2024-001234",
                    "status": "preparing",
                    ...
                }
            }
        """
        endpoint = f"/api/v1/order/get-order/{order_id}"
        return await self._request("GET", endpoint)

    async def get_customer_orders(
        self,
        phone: str,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get customer order history.

        Args:
            phone: Customer phone number
            status: Optional status filter (pending, confirmed, preparing, etc.)

        Returns:
            {
                "type": "1",
                "message": "Orders retrieved",
                "data": [...]
            }
        """
        endpoint = f"/api/v1/order/filled-orders/{self.subdomain}/{self.local_id}"
        params = {"phone": phone}
        if status:
            params["status"] = status
        return await self._request("GET", endpoint, params=params)

    # ============================================
    # DELIVERY ENDPOINTS
    # ============================================

    async def get_delivery_zones(self) -> Dict[str, Any]:
        """Get delivery zones with fees and requirements.

        Returns:
            {
                "type": "1",
                "message": "Delivery zones retrieved",
                "data": [
                    {
                        "_id": "zone001",
                        "zoneName": "Downtown",
                        "deliveryCost": 5.00,
                        "minimumOrder": 20.00,
                        ...
                    }
                ]
            }
        """
        endpoint = f"/api/v1/delivery/zones/{self.subdomain}/{self.local_id}"
        return await self._request("GET", endpoint)

    async def get_available_drivers(self) -> Dict[str, Any]:
        """Get currently available delivery drivers.

        Returns:
            {
                "type": "1",
                "message": "Drivers retrieved",
                "data": [
                    {"_id": "driver1", "name": "John", "status": "available"}
                ]
            }
        """
        endpoint = f"/api/v1/delivery/drivers/available/{self.subdomain}/{self.local_id}"
        return await self._request("GET", endpoint)

    # ============================================
    # UTILITY METHODS
    # ============================================

    def get_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics.

        Returns:
            Dictionary with request statistics and performance metrics
        """
        total_requests = self.metrics["total_requests"]
        avg_response_time = (
            self.metrics["total_response_time"] / total_requests
            if total_requests > 0
            else 0
        )

        return {
            "total_requests": total_requests,
            "successful_requests": self.metrics["successful_requests"],
            "failed_requests": self.metrics["failed_requests"],
            "retried_requests": self.metrics["retried_requests"],
            "rate_limited_requests": self.metrics["rate_limited_requests"],
            "success_rate": (
                self.metrics["successful_requests"] / total_requests * 100
                if total_requests > 0
                else 0
            ),
            "average_response_time": avg_response_time,
        }

    def reset_metrics(self):
        """Reset all metrics to zero."""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retried_requests": 0,
            "rate_limited_requests": 0,
            "total_response_time": 0.0,
        }


# ============================================
# EXCEPTIONS
# ============================================

class CartaAIAPIException(Exception):
    """Exception for API errors (4xx, 5xx responses)."""

    def __init__(self, status_code: int, message: str, data: Any = None):
        self.status_code = status_code
        self.message = message
        self.data = data
        super().__init__(f"API Error {status_code}: {message}")


class CartaAINetworkException(Exception):
    """Exception for network/connection errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Network Error: {message}")
