"""
Business Service - Handles business credential lookup from MongoDB
"""
import logging
import os
from typing import Optional, Dict, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from cryptography.fernet import Fernet
import base64
import hashlib

logger = logging.getLogger(__name__)


class BusinessService:
    """Service to interact with Business collection in MongoDB"""

    def __init__(self):
        self.mongo_uri = os.getenv("MONGODB_URI")
        if not self.mongo_uri:
            raise ValueError("MONGODB_URI environment variable is not set")

        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.encryption_key = self._get_encryption_key()

    def _get_encryption_key(self) -> bytes:
        """
        Get or generate encryption key for token decryption.
        This should match the encryption key used in your Node.js backend.
        """
        encryption_secret = os.getenv("ENCRYPTION_SECRET")
        if not encryption_secret:
            raise ValueError("ENCRYPTION_SECRET environment variable is not set")

        # Create a 32-byte key from the secret (same as Node.js crypto key derivation)
        key = hashlib.sha256(encryption_secret.encode()).digest()
        return base64.urlsafe_b64encode(key)

    async def connect(self):
        """Connect to MongoDB"""
        if self.client is None:
            self.client = AsyncIOMotorClient(self.mongo_uri)
            # Extract database name from URI or use default
            db_name = os.getenv("MONGODB_DB_NAME", "your_database_name")
            self.db = self.client[db_name]
            logger.info("Connected to MongoDB")

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("Disconnected from MongoDB")

    def decrypt_token(self, encrypted_token: str) -> Optional[str]:
        """
        Decrypt WhatsApp access token using Fernet encryption.

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

            # Create Fernet cipher
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
        Find business by WhatsApp phone number ID.

        Args:
            phone_number_id: WhatsApp Business Phone Number ID from webhook

        Returns:
            Business document with decrypted credentials or None if not found
        """
        if not self.db:
            await self.connect()

        try:
            # Query business by phone number ID
            business = await self.db.businesses.find_one({
                "whatsappPhoneNumberIds": phone_number_id,
                "whatsappEnabled": True,
                "isActive": True
            })

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

            return business

        except Exception as e:
            logger.error(f"Error querying business by phone number ID: {e}", exc_info=True)
            return None

    async def get_business_by_subdomain(self, subdomain: str) -> Optional[Dict]:
        """
        Find business by subdomain.

        Args:
            subdomain: Business subdomain

        Returns:
            Business document with decrypted credentials or None if not found
        """
        if not self.db:
            await self.connect()

        try:
            business = await self.db.businesses.find_one({
                "subDomain": subdomain,
                "isActive": True
            })

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

            return business

        except Exception as e:
            logger.error(f"Error querying business by subdomain: {e}", exc_info=True)
            return None

    async def list_businesses_with_whatsapp(self) -> List[Dict]:
        """
        List all businesses with WhatsApp enabled.

        Returns:
            List of business documents with decrypted credentials
        """
        if not self.db:
            await self.connect()

        try:
            cursor = self.db.businesses.find({
                "whatsappEnabled": True,
                "isActive": True
            })

            businesses = []
            async for business in cursor:
                # Decrypt tokens
                encrypted_token = business.get("whatsappAccessToken")
                if encrypted_token:
                    business["decryptedAccessToken"] = self.decrypt_token(encrypted_token)

                businesses.append(business)

            logger.info(f"Found {len(businesses)} businesses with WhatsApp enabled")
            return businesses

        except Exception as e:
            logger.error(f"Error listing businesses: {e}", exc_info=True)
            return []

    async def update_token_expiry(self, business_id: str, expires_at: datetime):
        """
        Update token expiration time for a business.

        Args:
            business_id: MongoDB ObjectId of the business
            expires_at: New expiration datetime
        """
        if not self.db:
            await self.connect()

        try:
            from bson import ObjectId
            await self.db.businesses.update_one(
                {"_id": ObjectId(business_id)},
                {"$set": {"whatsappTokenExpiresAt": expires_at}}
            )
            logger.info(f"Updated token expiry for business {business_id}")
        except Exception as e:
            logger.error(f"Error updating token expiry: {e}", exc_info=True)


# Global instance
_business_service: Optional[BusinessService] = None


def get_business_service() -> BusinessService:
    """Get or create global BusinessService instance"""
    global _business_service
    if _business_service is None:
        _business_service = BusinessService()
    return _business_service
