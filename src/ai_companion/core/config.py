"""Configuration settings for the AI Companion application."""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class CartaAIConfig:
    """CartaAI API configuration settings."""

    # API Configuration
    # Note: Base URL should NOT include /api/v1 - individual services add their paths
    api_base_url: str = "https://ssgg.api.cartaai.pe"
    subdomain: Optional[str] = None
    local_id: Optional[str] = None
    api_key: Optional[str] = None

    # Timeout & Retry Settings
    timeout: int = 30  # Request timeout in seconds
    max_retries: int = 3  # Maximum retry attempts
    retry_delay: float = 1.0  # Initial retry delay in seconds

    # Performance Settings
    cache_ttl: int = 900  # Cache TTL in seconds (15 minutes)
    enable_cache: bool = True  # Enable caching
    max_concurrent_requests: int = 10  # Max parallel requests

    # Feature Flags
    use_cartaai_api: bool = False  # Master switch for API usage
    menu_api_enabled: bool = False  # Enable menu API
    orders_api_enabled: bool = False  # Enable orders API
    delivery_api_enabled: bool = False  # Enable delivery API

    # Logging
    enable_api_logging: bool = False  # Enable detailed API logging

    @classmethod
    def from_env(cls) -> "CartaAIConfig":
        """Load configuration from environment variables.

        Returns:
            CartaAIConfig instance with values from environment
        """
        return cls(
            # API Configuration
            api_base_url=os.getenv(
                "CARTAAI_API_BASE_URL", "https://ssgg.api.cartaai.pe"
            ),
            subdomain=os.getenv("CARTAAI_SUBDOMAIN"),
            local_id=os.getenv("CARTAAI_LOCAL_ID"),
            api_key=os.getenv("CARTAAI_API_KEY"),
            # Timeout & Retry
            timeout=int(os.getenv("CARTAAI_TIMEOUT", "30")),
            max_retries=int(os.getenv("CARTAAI_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("CARTAAI_RETRY_DELAY", "1.0")),
            # Performance
            cache_ttl=int(os.getenv("CARTAAI_CACHE_TTL", "900")),
            enable_cache=os.getenv("CARTAAI_ENABLE_CACHE", "true").lower() == "true",
            max_concurrent_requests=int(
                os.getenv("CARTAAI_MAX_CONCURRENT_REQUESTS", "10")
            ),
            # Feature Flags
            use_cartaai_api=os.getenv("USE_CARTAAI_API", "false").lower() == "true",
            menu_api_enabled=os.getenv("CARTAAI_MENU_ENABLED", "false").lower()
            == "true",
            orders_api_enabled=os.getenv("CARTAAI_ORDERS_ENABLED", "false").lower()
            == "true",
            delivery_api_enabled=os.getenv("CARTAAI_DELIVERY_ENABLED", "false").lower()
            == "true",
            # Logging
            enable_api_logging=os.getenv("ENABLE_API_LOGGING", "false").lower()
            == "true",
        )

    def validate(self) -> bool:
        """Validate configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        if self.use_cartaai_api:
            if not self.subdomain:
                return False
            if not self.api_key:
                return False

        return True

    def __repr__(self) -> str:
        """String representation (hides API key)."""
        return (
            f"CartaAIConfig("
            f"subdomain={self.subdomain}, "
            f"local_id={self.local_id}, "
            f"api_enabled={self.use_cartaai_api}, "
            f"menu_api={self.menu_api_enabled}, "
            f"orders_api={self.orders_api_enabled})"
        )


# Global configuration instance
_config: Optional[CartaAIConfig] = None


def get_cartaai_config() -> CartaAIConfig:
    """Get global CartaAI configuration.

    Returns:
        CartaAIConfig instance loaded from environment
    """
    global _config
    if _config is None:
        _config = CartaAIConfig.from_env()
    return _config


def get_config() -> CartaAIConfig:
    """Alias for get_cartaai_config for convenience.

    Returns:
        CartaAIConfig instance loaded from environment
    """
    return get_cartaai_config()


def reset_config():
    """Reset global configuration (useful for testing)."""
    global _config
    _config = None
