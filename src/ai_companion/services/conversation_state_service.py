"""
Conversation State Service - Python client for TypeScript Conversation API

This service provides a Python interface to the TypeScript/MongoDB conversation state API,
enabling the Python AI companion to read and update conversation state managed by the
TypeScript backend.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

import httpx
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class ConversationIntent(str, Enum):
    """Conversation intent types matching TypeScript model."""
    MENU = "menu"
    ORDER = "order"
    SUPPORT = "support"
    INFO = "info"
    PAYMENT = "payment"
    DELIVERY = "delivery"
    IDLE = "idle"


class PaymentMethod(str, Enum):
    """Payment method types."""
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    YAPE = "yape"
    PLIN = "plin"
    MERCADO_PAGO = "mercado_pago"
    BANK_TRANSFER = "bank_transfer"


class CartItem(BaseModel):
    """Cart item model."""
    id: str
    name: str
    quantity: int
    price: float
    notes: Optional[str] = None


class DeliveryAddress(BaseModel):
    """Delivery address model."""
    street: Optional[str] = None
    city: Optional[str] = None
    postalCode: Optional[str] = None
    notes: Optional[str] = None


class ConversationMessage(BaseModel):
    """Conversation message model."""
    role: str  # 'user' or 'bot'
    content: str
    timestamp: datetime


class ConversationContext(BaseModel):
    """Conversation context matching TypeScript interface."""
    selectedItems: Optional[List[CartItem]] = None
    deliveryAddress: Optional[DeliveryAddress] = None
    orderTotal: Optional[float] = None
    paymentMethod: Optional[PaymentMethod] = None
    customerName: Optional[str] = None
    customerEmail: Optional[str] = None
    previousMessages: Optional[List[ConversationMessage]] = None
    lastUserMessage: Optional[str] = None
    retryCount: Optional[int] = None
    currentOrderId: Optional[str] = None
    orderHistory: Optional[List[str]] = None
    # Allow additional custom fields
    extra: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"


class ConversationMetadata(BaseModel):
    """Conversation metadata."""
    language: Optional[str] = None
    timezone: Optional[str] = None
    userAgent: Optional[str] = None
    platform: Optional[str] = None
    # Allow additional custom fields
    extra: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"


class ConversationState(BaseModel):
    """Full conversation state model."""
    sessionId: str
    userId: str  # Phone number
    botId: Optional[str] = None
    subDomain: str
    currentIntent: ConversationIntent = ConversationIntent.IDLE
    currentStep: str = "initial"
    previousIntent: Optional[ConversationIntent] = None
    previousStep: Optional[str] = None
    context: ConversationContext = Field(default_factory=ConversationContext)
    metadata: ConversationMetadata = Field(default_factory=ConversationMetadata)
    isActive: bool = True
    lastActivity: datetime
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    expiresAt: Optional[datetime] = None
    currentOrderId: Optional[str] = None
    orderHistory: Optional[List[str]] = None


class ConversationStateService:
    """
    Service for interacting with the TypeScript Conversation State API.

    Provides methods to create, retrieve, update, and manage conversation state
    stored in MongoDB via the TypeScript backend API.
    """

    def __init__(
        self,
        api_base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 10.0
    ):
        """
        Initialize the conversation state service.

        Args:
            api_base_url: Base URL of the TypeScript API (e.g., "http://localhost:3000")
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.api_base_url,
                headers=headers,
                timeout=self.timeout
            )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle API response and extract data.

        Args:
            response: HTTP response object

        Returns:
            Response data dictionary

        Raises:
            httpx.HTTPStatusError: If response indicates an error
        """
        response.raise_for_status()
        result = response.json()

        # API returns: {"type": "1", "message": "...", "data": {...}}
        # type "1" = success, "3" = error
        if result.get("type") == "3":
            error_msg = result.get("message", "Unknown error")
            logger.error(f"API error: {error_msg}")
            raise Exception(f"API error: {error_msg}")

        return result.get("data", {})

    async def create_conversation(
        self,
        user_id: str,
        sub_domain: str,
        local_id: Optional[str] = None,
        bot_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationState:
        """
        Create a new conversation or retrieve existing active session.

        Args:
            user_id: User's phone number in E.164 format
            sub_domain: Business subdomain
            local_id: Optional business location ID
            bot_id: Optional WhatsApp bot ID
            metadata: Optional metadata (language, timezone, platform, etc.)

        Returns:
            ConversationState object
        """
        await self._ensure_client()

        payload = {
            "userId": user_id,
            "subDomain": sub_domain
        }

        if local_id:
            payload["localId"] = local_id
        if bot_id:
            payload["botId"] = bot_id
        if metadata:
            payload["metadata"] = metadata

        response = await self._client.post(
            "/api/v1/conversations",
            json=payload
        )

        data = self._handle_response(response)
        return ConversationState(**data)

    async def get_conversation(
        self,
        session_id: str,
        sub_domain: str,
        local_id: Optional[str] = None
    ) -> Optional[ConversationState]:
        """
        Get conversation state by session ID.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            local_id: Optional business location ID

        Returns:
            ConversationState object or None if not found
        """
        await self._ensure_client()

        params = {"subDomain": sub_domain}
        if local_id:
            params["localId"] = local_id

        try:
            response = await self._client.get(
                f"/api/v1/conversations/{session_id}",
                params=params
            )

            data = self._handle_response(response)
            return ConversationState(**data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Conversation not found: {session_id}")
                return None
            raise

    async def get_user_conversation(
        self,
        user_id: str,
        sub_domain: str,
        local_id: Optional[str] = None
    ) -> Optional[ConversationState]:
        """
        Get active conversation for a specific user (phone number).

        Args:
            user_id: User's phone number
            sub_domain: Business subdomain
            local_id: Optional business location ID

        Returns:
            ConversationState object or None if not found
        """
        await self._ensure_client()

        params = {"subDomain": sub_domain}
        if local_id:
            params["localId"] = local_id

        try:
            response = await self._client.get(
                f"/api/v1/conversations/user/{user_id}",
                params=params
            )

            data = self._handle_response(response)
            return ConversationState(**data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"No active conversation for user: {user_id}")
                return None
            raise

    async def update_intent(
        self,
        session_id: str,
        sub_domain: str,
        intent: ConversationIntent,
        step: Optional[str] = None,
        local_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update conversation intent and step.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            intent: New conversation intent
            step: Optional new step
            local_id: Optional business location ID

        Returns:
            Updated conversation data
        """
        await self._ensure_client()

        payload = {
            "subDomain": sub_domain,
            "intent": intent.value
        }

        if local_id:
            payload["localId"] = local_id
        if step:
            payload["step"] = step

        response = await self._client.patch(
            f"/api/v1/conversations/{session_id}/intent",
            json=payload
        )

        return self._handle_response(response)

    async def update_context(
        self,
        session_id: str,
        sub_domain: str,
        context: Dict[str, Any],
        merge: bool = True,
        local_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update conversation context.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            context: Context updates (cart items, delivery info, etc.)
            merge: Whether to merge with existing context (default: True)
            local_id: Optional business location ID

        Returns:
            Updated conversation data
        """
        await self._ensure_client()

        payload = {
            "subDomain": sub_domain,
            "context": context,
            "merge": merge
        }

        if local_id:
            payload["localId"] = local_id

        response = await self._client.patch(
            f"/api/v1/conversations/{session_id}/context",
            json=payload
        )

        return self._handle_response(response)

    async def add_message(
        self,
        session_id: str,
        sub_domain: str,
        role: str,
        content: str,
        local_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a message to conversation history.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            role: Message role ('user' or 'bot')
            content: Message content
            local_id: Optional business location ID

        Returns:
            Updated conversation data
        """
        await self._ensure_client()

        payload = {
            "subDomain": sub_domain,
            "role": role,
            "content": content
        }

        if local_id:
            payload["localId"] = local_id

        response = await self._client.post(
            f"/api/v1/conversations/{session_id}/messages",
            json=payload
        )

        return self._handle_response(response)

    async def reset_conversation(
        self,
        session_id: str,
        sub_domain: str,
        keep_history: bool = False,
        local_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reset conversation context.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            keep_history: Whether to keep message history
            local_id: Optional business location ID

        Returns:
            Reset confirmation data
        """
        await self._ensure_client()

        payload = {
            "subDomain": sub_domain,
            "keepHistory": keep_history
        }

        if local_id:
            payload["localId"] = local_id

        response = await self._client.post(
            f"/api/v1/conversations/{session_id}/reset",
            json=payload
        )

        return self._handle_response(response)

    async def extend_expiration(
        self,
        session_id: str,
        sub_domain: str,
        hours: int = 24,
        local_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extend conversation expiration time.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            hours: Hours to extend (default: 24)
            local_id: Optional business location ID

        Returns:
            Updated expiration data
        """
        await self._ensure_client()

        payload = {
            "subDomain": sub_domain,
            "hours": hours
        }

        if local_id:
            payload["localId"] = local_id

        response = await self._client.post(
            f"/api/v1/conversations/{session_id}/extend",
            json=payload
        )

        return self._handle_response(response)

    async def link_order(
        self,
        session_id: str,
        sub_domain: str,
        order_id: str,
        local_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Link an order to the conversation.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            order_id: Order ID to link
            local_id: Optional business location ID

        Returns:
            Updated order data
        """
        await self._ensure_client()

        payload = {
            "subDomain": sub_domain,
            "orderId": order_id
        }

        if local_id:
            payload["localId"] = local_id

        response = await self._client.post(
            f"/api/v1/conversations/{session_id}/orders",
            json=payload
        )

        return self._handle_response(response)

    async def get_conversation_orders(
        self,
        session_id: str,
        sub_domain: str,
        local_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get orders associated with the conversation.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            local_id: Optional business location ID

        Returns:
            Order data
        """
        await self._ensure_client()

        params = {"subDomain": sub_domain}
        if local_id:
            params["localId"] = local_id

        response = await self._client.get(
            f"/api/v1/conversations/{session_id}/orders",
            params=params
        )

        return self._handle_response(response)

    async def end_conversation(
        self,
        session_id: str,
        sub_domain: str,
        local_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark conversation as inactive.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            local_id: Optional business location ID

        Returns:
            End confirmation data
        """
        await self._ensure_client()

        payload = {"subDomain": sub_domain}
        if local_id:
            payload["localId"] = local_id

        response = await self._client.post(
            f"/api/v1/conversations/{session_id}/end",
            json=payload
        )

        return self._handle_response(response)

    async def list_conversations(
        self,
        sub_domain: str,
        local_id: Optional[str] = None,
        bot_id: Optional[str] = None,
        intent: Optional[ConversationIntent] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List active conversations.

        Args:
            sub_domain: Business subdomain
            local_id: Optional business location ID
            bot_id: Optional bot ID filter
            intent: Optional intent filter
            limit: Number of results (default: 50)
            offset: Pagination offset (default: 0)

        Returns:
            Conversations list data
        """
        await self._ensure_client()

        params = {
            "subDomain": sub_domain,
            "limit": limit,
            "offset": offset
        }

        if local_id:
            params["localId"] = local_id
        if bot_id:
            params["botId"] = bot_id
        if intent:
            params["intent"] = intent.value

        response = await self._client.get(
            "/api/v1/conversations",
            params=params
        )

        return self._handle_response(response)
