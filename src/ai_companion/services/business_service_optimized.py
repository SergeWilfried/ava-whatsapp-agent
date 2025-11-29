"""
Production-ready Business Service with connection pooling, caching, and optimization
Designed to handle 500+ concurrent requests across multiple businesses
"""
import logging
import os
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from cryptography.fernet import Fernet
import base64
import hashlib
import asyncio
from functools import lru_cache
import time

logger = logging.getLogger(__name__)


class BusinessCache:
    """In-memory LRU cache for business credentials with TTL"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[Dict, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Dict]:
        """Get cached business data if not expired"""
        async with self._lock:
            if key in self._cache:
                data, timestamp = self._cache[key]
                if time.time() - timestamp < self.ttl_seconds:
                    logger.debug(f"Cache HIT for key: {key}")
                    return data
                else:
                    # Expired, remove from cache
                    del self._cache[key]
                    logger.debug(f"Cache EXPIRED for key: {key}")
        return None

    async def set(self, key: str, value: Dict):
        """Set cache entry with current timestamp"""
        async with self._lock:
            # Simple LRU: if cache is full, remove oldest entry
            if len(self._cache) >= self.max_size:
                oldest_key = min(self._cache.items(), key=lambda x: x[1][1])[0]
                del self._cache[oldest_key]

            self._cache[key] = (value, time.time())
            logger.debug(f"Cache SET for key: {key}")

    async def invalidate(self, key: str):
        """Invalidate specific cache entry"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache INVALIDATED for key: {key}")

    async def clear(self):
        """Clear entire cache"""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache CLEARED")


class OptimizedBusinessService:
    """
    Production-ready business service with:
    - Connection pooling
    - In-memory caching with TTL
    - Query optimization with indexes
    - Timeout handling
    - Graceful error handling
    """

    def __init__(
        self,
        cache_ttl: int = 300,  # 5 minutes
        cache_size: int = 1000,
        max_pool_size: int = 100,
        min_pool_size: int = 10,
        connection_timeout_ms: int = 5000,
        server_selection_timeout_ms: int = 5000,
    ):
        self.mongo_uri = os.getenv("MONGODB_URI")
        if not self.mongo_uri:
            raise ValueError("MONGODB_URI environment variable is not set")

        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.encryption_key = self._get_encryption_key()

        # Cache configuration
        self.cache = BusinessCache(max_size=cache_size, ttl_seconds=cache_ttl)

        # Connection pool settings
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.connection_timeout_ms = connection_timeout_ms
        self.server_selection_timeout_ms = server_selection_timeout_ms

        # Connection lock to prevent race conditions
        self._connect_lock = asyncio.Lock()
        self._is_connected = False

    @lru_cache(maxsize=1)
    def _get_encryption_key(self) -> bytes:
        """
        Get or generate encryption key for token decryption (cached).
        This should match the encryption key used in your Node.js backend.
        """
        encryption_secret = os.getenv("ENCRYPTION_SECRET")
        if not encryption_secret:
            raise ValueError("ENCRYPTION_SECRET environment variable is not set")

        # Create a 32-byte key from the secret (same as Node.js crypto key derivation)
        key = hashlib.sha256(encryption_secret.encode()).digest()
        return base64.urlsafe_b64encode(key)

    async def connect(self):
        """
        Connect to MongoDB with connection pooling.
        Thread-safe with connection lock.
        """
        if self._is_connected and self.client is not None:
            return

        async with self._connect_lock:
            # Double-check after acquiring lock
            if self._is_connected and self.client is not None:
                return

            try:
                logger.info("Initializing MongoDB connection pool...")

                self.client = AsyncIOMotorClient(
                    self.mongo_uri,
                    maxPoolSize=self.max_pool_size,
                    minPoolSize=self.min_pool_size,
                    connectTimeoutMS=self.connection_timeout_ms,
                    serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                    # Additional production settings
                    maxIdleTimeMS=60000,  # 1 minute
                    waitQueueTimeoutMS=10000,  # 10 seconds
                    retryWrites=True,
                    retryReads=True,
                )

                # Extract database name from URI or use env var
                db_name = os.getenv("MONGODB_DB_NAME", "your_database_name")
                self.db = self.client[db_name]

                # Verify connection with a ping
                await self.client.admin.command('ping')

                self._is_connected = True
                logger.info(f"MongoDB connection pool initialized (pool size: {self.min_pool_size}-{self.max_pool_size})")

            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}", exc_info=True)
                self._is_connected = False
                raise

    async def disconnect(self):
        """Disconnect from MongoDB and cleanup connection pool"""
        async with self._connect_lock:
            if self.client:
                self.client.close()
                self.client = None
                self.db = None
                self._is_connected = False
                logger.info("Disconnected from MongoDB")

    @lru_cache(maxsize=10000)
    def decrypt_token(self, encrypted_token: str) -> Optional[str]:
        """
        Decrypt WhatsApp access token using Fernet encryption.
        Results are cached with LRU for performance.

        Args:
            encrypted_token: Hex-encoded encrypted token from MongoDB

        Returns:
            Decrypted token string or None if decryption fails
        """
        if not encrypted_token:
            return None

        try:
            # Convert hex string to bytes
            encrypted_bytes = bytes.fromhex(encrypted_token)

            # Create Fernet cipher (reuse encryption_key from instance)
            fernet = Fernet(self.encryption_key)

            # Decrypt
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            decrypted_token = decrypted_bytes.decode('utf-8')

            # Validate it looks like a valid token
            if len(decrypted_token) > 400 or not decrypted_token.strip():
                logger.error(f"Decrypted token appears invalid (length: {len(decrypted_token)})")
                return None

            return decrypted_token

        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}")

            # Check if it might be stored in plain text (fallback)
            if len(encrypted_token) < 64 or not all(c in '0123456789abcdefABCDEF' for c in encrypted_token):
                logger.warning("Token appears to be in plain text format")
                return encrypted_token

            return None

    async def get_business_by_phone_number_id(self, phone_number_id: str) -> Optional[Dict]:
        """
        Find business by WhatsApp phone number ID with caching.

        Args:
            phone_number_id: WhatsApp Business Phone Number ID from webhook

        Returns:
            Business document with decrypted credentials or None if not found
        """
            
        # Check cache first
        cache_key = f"phone:{phone_number_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Ensure connected
        if not self._is_connected:
            await self.connect()

        try:
            # Query business by phone number ID with projection to reduce data transfer
            business = await self.db.businesses.find_one(
                {
                    "whatsappPhoneNumberIds": phone_number_id,
                    "whatsappEnabled": True,
                    "isActive": True
                },
                {
                    "_id": 1,
                    "name": 1,
                    "subDomain": 1,
                    "wabaId": 1,
                    "whatsappPhoneNumberIds": 1,
                    "whatsappAccessToken": 1,
                    "whatsappRefreshToken": 1,
                    "whatsappTokenExpiresAt": 1,
                }
            )

            if not business:
                logger.warning(f"No active business found for phone number ID: {phone_number_id}")
                return None

            # Decrypt access token
            encrypted_token = business.get("whatsappAccessToken")
            if encrypted_token:
                decrypted_token = self.decrypt_token(encrypted_token)
                business["decryptedAccessToken"] = decrypted_token
            else:
                logger.warning(f"No WhatsApp access token found for business: {business.get('name')}")
                business["decryptedAccessToken"] = None

            # Decrypt refresh token if present
            encrypted_refresh = business.get("whatsappRefreshToken")
            if encrypted_refresh:
                decrypted_refresh = self.decrypt_token(encrypted_refresh)
                business["decryptedRefreshToken"] = decrypted_refresh

            logger.info(f"Found business: {business.get('name')} (subdomain: {business.get('subDomain')})")

            # Cache the result
            await self.cache.set(cache_key, business)

            return business

        except Exception as e:
            logger.error(f"Error querying business by phone number ID: {e}", exc_info=True)
            return None

    async def get_business_by_subdomain(self, subdomain: str) -> Optional[Dict]:
        """
        Find business by subdomain with caching.

        Args:
            subdomain: Business subdomain

        Returns:
            Business document with decrypted credentials or None if not found
        """
        # Check cache first
        cache_key = f"subdomain:{subdomain}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        if not self._is_connected:
            await self.connect()

        try:
            business = await self.db.businesses.find_one(
                {"subDomain": subdomain, "isActive": True},
                {
                    "_id": 1,
                    "name": 1,
                    "subDomain": 1,
                    "wabaId": 1,
                    "whatsappPhoneNumberIds": 1,
                    "whatsappAccessToken": 1,
                    "whatsappRefreshToken": 1,
                    "whatsappTokenExpiresAt": 1,
                }
            )

            if not business:
                logger.warning(f"No business found for subdomain: {subdomain}")
                return None

            # Decrypt tokens
            encrypted_token = business.get("whatsappAccessToken")
            if encrypted_token:
                business["decryptedAccessToken"] = self.decrypt_token(encrypted_token)

            encrypted_refresh = business.get("whatsappRefreshToken")
            if encrypted_refresh:
                business["decryptedRefreshToken"] = self.decrypt_token(encrypted_refresh)

            # Cache the result
            await self.cache.set(cache_key, business)

            return business

        except Exception as e:
            logger.error(f"Error querying business by subdomain: {e}", exc_info=True)
            return None

    async def invalidate_cache(self, phone_number_id: Optional[str] = None, subdomain: Optional[str] = None):
        """Invalidate cache for specific business"""
        if phone_number_id:
            await self.cache.invalidate(f"phone:{phone_number_id}")
        if subdomain:
            await self.cache.invalidate(f"subdomain:{subdomain}")

    async def clear_cache(self):
        """Clear entire business cache"""
        await self.cache.clear()

    async def warmup_cache(self, limit: int = 100):
        """
        Pre-warm cache with most active businesses.
        Call this on application startup.
        """
        logger.info(f"Warming up business cache (limit: {limit})...")

        if not self._is_connected:
            await self.connect()

        try:
            cursor = self.db.businesses.find(
                {"whatsappEnabled": True, "isActive": True}
            ).limit(limit)

            count = 0
            async for business in cursor:
                phone_ids = business.get("whatsappPhoneNumberIds", [])
                for phone_id in phone_ids:
                    # Trigger cache population
                    await self.get_business_by_phone_number_id(phone_id)
                    count += 1

            logger.info(f"Cache warmed up with {count} businesses")

        except Exception as e:
            logger.error(f"Error warming up cache: {e}", exc_info=True)


# Global instance with singleton pattern
_optimized_business_service: Optional[OptimizedBusinessService] = None
_service_lock = asyncio.Lock()


async def get_optimized_business_service() -> OptimizedBusinessService:
    """
    Get or create global OptimizedBusinessService instance.
    Thread-safe with asyncio lock.
    """
    global _optimized_business_service

    if _optimized_business_service is not None:
        return _optimized_business_service

    async with _service_lock:
        # Double-check after acquiring lock
        if _optimized_business_service is not None:
            return _optimized_business_service

        _optimized_business_service = OptimizedBusinessService(
            cache_ttl=int(os.getenv("BUSINESS_CACHE_TTL", "300")),  # 5 minutes default
            cache_size=int(os.getenv("BUSINESS_CACHE_SIZE", "1000")),
            max_pool_size=int(os.getenv("MONGODB_MAX_POOL_SIZE", "100")),
            min_pool_size=int(os.getenv("MONGODB_MIN_POOL_SIZE", "10")),
        )

        # Connect immediately
        await _optimized_business_service.connect()

        # Optional: warmup cache
        if os.getenv("WARMUP_CACHE", "true").lower() == "true":
            await _optimized_business_service.warmup_cache()

        return _optimized_business_service
