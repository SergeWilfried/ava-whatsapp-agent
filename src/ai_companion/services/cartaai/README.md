# CartaAI API Client

Python async HTTP client for the CartaAI restaurant management API.

## Features

- ✅ **Authentication** - X-Service-API-Key header support
- ✅ **Retry Logic** - Automatic retry with exponential backoff
- ✅ **Rate Limiting** - Handles 429 responses with retry-after
- ✅ **Error Handling** - Detailed exceptions for API and network errors
- ✅ **Metrics** - Built-in request/response tracking
- ✅ **Connection Pooling** - Efficient connection reuse
- ✅ **Async/Await** - Full asyncio support
- ✅ **Type Hints** - Complete type annotations
- ✅ **Logging** - Configurable request/response logging

## Installation

The client is part of the `ai_companion` package. No additional installation required.

## Quick Start

```python
import asyncio
from ai_companion.services.cartaai import CartaAIClient

async def main():
    # Create client with context manager (recommended)
    async with CartaAIClient(
        base_url="https://ssgg.api.cartaai.pe/api/v1",
        subdomain="my-restaurant",
        local_id="branch-01",
        api_key="your_api_key_here"
    ) as client:
        # Fetch menu structure
        menu = await client.get_menu_structure()
        print(f"Categories: {len(menu['data']['categories'])}")

        # Get product details
        products = await client.get_product_details(["prod001", "prod002"])
        print(f"Products: {len(products['data'])}")

        # Create order
        order_data = {
            "customer": {
                "name": "John Doe",
                "phone": "+51987654321"
            },
            "items": [...],
            "type": "delivery",
            "paymentMethod": "cash",
            "source": "whatsapp"
        }
        order = await client.create_order(order_data)
        print(f"Order created: {order['data']['orderNumber']}")

        # Track order
        order_status = await client.get_order(order['data']['_id'])
        print(f"Order status: {order_status['data']['status']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

### Basic Configuration

```python
client = CartaAIClient(
    base_url="https://ssgg.api.cartaai.pe/api/v1",
    subdomain="restaurant-name",
    local_id="branch-001",  # Optional
    api_key="your_api_key"
)
```

### Advanced Configuration

```python
from ai_companion.services.cartaai import CartaAIClient, RateLimitStrategy

client = CartaAIClient(
    base_url="https://ssgg.api.cartaai.pe/api/v1",
    subdomain="restaurant",
    local_id="branch-01",
    api_key="your_api_key",

    # Timeout settings
    timeout=30,  # Request timeout in seconds

    # Retry settings
    max_retries=3,  # Maximum retry attempts
    retry_delay=1.0,  # Initial retry delay in seconds

    # Rate limiting strategy
    rate_limit_strategy=RateLimitStrategy.EXPONENTIAL_BACKOFF,
    # Options: EXPONENTIAL_BACKOFF, FIXED_DELAY, ADAPTIVE

    # Connection pooling
    max_concurrent_requests=10,  # Max parallel requests

    # Logging
    enable_logging=True  # Enable request/response logs
)
```

## API Methods

### Menu Endpoints

#### Get Menu Structure
```python
menu = await client.get_menu_structure()
# Returns: {"type": "1", "data": {"categories": [...]}}
```

#### Get All Categories
```python
categories = await client.get_all_categories()
# Returns: {"type": "1", "data": [...]}
```

#### Get Product Details
```python
products = await client.get_product_details(["prod001", "prod002"])
# Returns: {"success": true, "data": [...]}
```

#### Get All Products
```python
products = await client.get_all_products(category_id="cat001")
# Returns: {"type": "1", "data": [...]}
```

### Order Endpoints

#### Create Order
```python
order_data = {
    "customer": {...},
    "items": [...],
    "type": "delivery",
    "paymentMethod": "cash",
    "source": "whatsapp"
}
order = await client.create_order(order_data)
# Returns: {"type": "1", "data": {"_id": "order123", ...}}
```

#### Get Order
```python
order = await client.get_order("order123")
# Returns: {"type": "1", "data": {...}}
```

#### Get Customer Orders
```python
orders = await client.get_customer_orders(
    phone="+51987654321",
    status="pending"  # Optional
)
# Returns: {"type": "1", "data": [...]}
```

### Delivery Endpoints

#### Get Delivery Zones
```python
zones = await client.get_delivery_zones()
# Returns: {"type": "1", "data": [...]}
```

#### Get Available Drivers
```python
drivers = await client.get_available_drivers()
# Returns: {"type": "1", "data": [...]}
```

## Error Handling

### API Exceptions

```python
from ai_companion.services.cartaai import CartaAIAPIException, CartaAINetworkException

try:
    menu = await client.get_menu_structure()
except CartaAIAPIException as e:
    # Handle API errors (4xx, 5xx)
    print(f"API Error {e.status_code}: {e.message}")
    print(f"Response data: {e.data}")
except CartaAINetworkException as e:
    # Handle network/connection errors
    print(f"Network Error: {e.message}")
```

### Retry Logic

The client automatically retries:
- **5xx errors** - Server errors with exponential backoff
- **429 errors** - Rate limiting with Retry-After header
- **Network errors** - Connection failures

```python
# Configure retry behavior
client = CartaAIClient(
    base_url="...",
    subdomain="...",
    api_key="...",
    max_retries=5,  # Retry up to 5 times
    retry_delay=2.0,  # Start with 2 second delay
    rate_limit_strategy=RateLimitStrategy.EXPONENTIAL_BACKOFF
)
```

### Rate Limiting Strategies

#### Exponential Backoff (Default)
```python
# Delays: 1s, 2s, 4s, 8s, ...
rate_limit_strategy=RateLimitStrategy.EXPONENTIAL_BACKOFF
```

#### Fixed Delay
```python
# Delays: 2s, 2s, 2s, ...
retry_delay=2.0,
rate_limit_strategy=RateLimitStrategy.FIXED_DELAY
```

#### Adaptive (with Jitter)
```python
# Delays: 1s + jitter, 2s + jitter, 4s + jitter, ...
rate_limit_strategy=RateLimitStrategy.ADAPTIVE
```

## Metrics

Track client performance and request statistics:

```python
async with CartaAIClient(...) as client:
    # Make some requests
    await client.get_menu_structure()
    await client.get_product_details(["prod001"])

    # Get metrics
    metrics = client.get_metrics()
    print(metrics)
    # {
    #   "total_requests": 2,
    #   "successful_requests": 2,
    #   "failed_requests": 0,
    #   "retried_requests": 0,
    #   "rate_limited_requests": 0,
    #   "success_rate": 100.0,
    #   "average_response_time": 0.234
    # }

    # Reset metrics
    client.reset_metrics()
```

## Logging

Enable detailed logging:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_companion.services.cartaai")

# Create client with logging enabled
client = CartaAIClient(
    base_url="...",
    subdomain="...",
    api_key="...",
    enable_logging=True
)

# Logs will show:
# INFO: API Request [0/3]: GET https://api.../menu2/bot-structure | Params: {...}
# INFO: API Response: 200 | Time: 0.234s | Type: 1
```

## Context Manager

Always use the context manager for proper session handling:

```python
# ✅ Recommended: Context manager
async with CartaAIClient(...) as client:
    await client.get_menu_structure()
# Session automatically closed

# ❌ Not recommended: Manual session management
client = CartaAIClient(...)
await client._ensure_session()
try:
    await client.get_menu_structure()
finally:
    await client.close()
```

## Environment Variables

Configure via environment variables:

```bash
# .env file
CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe/api/v1
CARTAAI_SUBDOMAIN=my-restaurant
CARTAAI_LOCAL_ID=branch-01
CARTAAI_API_KEY=your_api_key
CARTAAI_TIMEOUT=30
CARTAAI_MAX_RETRIES=3
```

```python
import os
from ai_companion.services.cartaai import CartaAIClient

client = CartaAIClient(
    base_url=os.getenv("CARTAAI_API_BASE_URL"),
    subdomain=os.getenv("CARTAAI_SUBDOMAIN"),
    local_id=os.getenv("CARTAAI_LOCAL_ID"),
    api_key=os.getenv("CARTAAI_API_KEY"),
    timeout=int(os.getenv("CARTAAI_TIMEOUT", "30")),
    max_retries=int(os.getenv("CARTAAI_MAX_RETRIES", "3"))
)
```

## Testing

Run unit tests:

```bash
# Run all tests
pytest tests/services/cartaai/

# Run with coverage
pytest tests/services/cartaai/ --cov=ai_companion.services.cartaai

# Run specific test
pytest tests/services/cartaai/test_client.py::TestCartaAIClientRequests::test_get_menu_structure_success
```

## Best Practices

### 1. Use Context Manager
Always use `async with` to ensure proper session cleanup:
```python
async with CartaAIClient(...) as client:
    await client.get_menu_structure()
```

### 2. Handle Exceptions
Always catch and handle exceptions:
```python
try:
    menu = await client.get_menu_structure()
except CartaAIAPIException as e:
    logger.error(f"API error: {e}")
except CartaAINetworkException as e:
    logger.error(f"Network error: {e}")
```

### 3. Configure Timeouts
Set appropriate timeouts for your use case:
```python
client = CartaAIClient(..., timeout=30)  # 30 seconds
```

### 4. Monitor Metrics
Track performance and error rates:
```python
metrics = client.get_metrics()
if metrics["success_rate"] < 95:
    logger.warning("API success rate below 95%")
```

### 5. Enable Logging in Development
```python
client = CartaAIClient(..., enable_logging=True)
```

## Troubleshooting

### Connection Timeouts
```python
# Increase timeout
client = CartaAIClient(..., timeout=60)
```

### Rate Limiting
```python
# Reduce concurrent requests
client = CartaAIClient(..., max_concurrent_requests=5)
```

### Retry Exhausted
```python
# Increase retries
client = CartaAIClient(..., max_retries=5, retry_delay=2.0)
```

### Authentication Errors
```python
# Verify API key
client = CartaAIClient(..., api_key="correct_key")

# Check headers
headers = client._get_headers()
print(headers["X-Service-API-Key"])
```

## API Documentation

Full API documentation: [docs/api/CHATBOT_INTEGRATION.md](../../../../docs/api/CHATBOT_INTEGRATION.md)

## Support

For issues or questions:
- API Support: support@cartaai.pe
- GitHub Issues: [Report Issue](https://github.com/your-repo/issues)
- Documentation: [API Integration Guide](../../../../docs/api/CHATBOT_INTEGRATION.md)
