"""CartaAI API integration services."""

from .client import CartaAIClient, CartaAIAPIException, CartaAINetworkException, RateLimitStrategy
from .cache import MenuCache
from .menu_service import MenuService
from .order_service import OrderService, build_order_payload

__all__ = [
    "CartaAIClient",
    "CartaAIAPIException",
    "CartaAINetworkException",
    "RateLimitStrategy",
    "MenuCache",
    "MenuService",
    "OrderService",
    "build_order_payload",
]


def get_cartaai_client() -> CartaAIClient:
    """Get or create CartaAI client instance.

    Returns:
        CartaAIClient configured from environment
    """
    from ai_companion.core.config import get_config

    config = get_config()
    return CartaAIClient(
        base_url=config.api_base_url,
        subdomain=config.subdomain,
        local_id=config.local_id,
        api_key=config.api_key,
        timeout=config.timeout,
        max_retries=config.max_retries,
        retry_delay=config.retry_delay,
        max_concurrent_requests=config.max_concurrent_requests,
        enable_logging=config.enable_api_logging,
    )
