"""
Conversation State Manager - Bridge between Python LangGraph state and TypeScript Conversation API

This manager synchronizes conversation state between:
1. Python LangGraph short-term memory (SQLite)
2. TypeScript/MongoDB conversation state API

It provides bidirectional sync to keep both systems in sync.
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

from ai_companion.services.conversation_state_service import (
    ConversationStateService,
    ConversationIntent,
    ConversationState,
    CartItem,
    DeliveryAddress,
    PaymentMethod
)


logger = logging.getLogger(__name__)


class ConversationStateManager:
    """
    Manages synchronization between Python graph state and TypeScript conversation state.

    This class provides:
    - Conversion between Python graph state and TypeScript conversation state
    - Automatic syncing of state changes
    - Conflict resolution
    - Error handling and fallback mechanisms
    """

    def __init__(self, conversation_service: ConversationStateService):
        """
        Initialize the state manager.

        Args:
            conversation_service: ConversationStateService instance
        """
        self.service = conversation_service

    async def initialize_conversation(
        self,
        user_phone: str,
        sub_domain: str,
        local_id: Optional[str] = None,
        bot_id: Optional[str] = None,
        platform: str = "whatsapp"
    ) -> ConversationState:
        """
        Initialize or retrieve a conversation for a user.

        Args:
            user_phone: User's phone number
            sub_domain: Business subdomain
            local_id: Optional business location ID
            bot_id: Optional bot ID
            platform: Platform (default: "whatsapp")

        Returns:
            ConversationState object
        """
        try:
            # Try to get existing active conversation
            conversation = await self.service.get_user_conversation(
                user_id=user_phone,
                sub_domain=sub_domain,
                local_id=local_id
            )

            if conversation:
                logger.info(f"Retrieved existing conversation for {user_phone}: {conversation.sessionId}")
                return conversation

            # Create new conversation
            metadata = {
                "platform": platform,
                "timezone": "America/Lima",  # Could be dynamic based on business
                "language": "auto"
            }

            conversation = await self.service.create_conversation(
                user_id=user_phone,
                sub_domain=sub_domain,
                local_id=local_id,
                bot_id=bot_id,
                metadata=metadata
            )

            logger.info(f"Created new conversation for {user_phone}: {conversation.sessionId}")
            return conversation

        except Exception as e:
            logger.error(f"Error initializing conversation for {user_phone}: {e}", exc_info=True)
            raise

    async def sync_from_graph_to_api(
        self,
        session_id: str,
        sub_domain: str,
        graph_state: Dict[str, Any],
        local_id: Optional[str] = None
    ) -> bool:
        """
        Sync state from Python LangGraph to TypeScript API.

        This converts the Python graph state to the format expected by
        the TypeScript conversation state API and updates it.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            graph_state: Python graph state dictionary
            local_id: Optional business location ID

        Returns:
            True if sync was successful
        """
        try:
            # Extract intent from graph state
            intent = self._extract_intent_from_graph(graph_state)
            step = graph_state.get("order_stage", graph_state.get("current_step", "initial"))

            # Update intent if it changed
            current_intent = graph_state.get("current_intent")
            if current_intent != intent.value:
                await self.service.update_intent(
                    session_id=session_id,
                    sub_domain=sub_domain,
                    intent=intent,
                    step=step,
                    local_id=local_id
                )
                logger.debug(f"Updated intent to {intent.value}, step: {step}")

            # Build context from graph state
            context = self._build_context_from_graph(graph_state)

            # Update context
            await self.service.update_context(
                session_id=session_id,
                sub_domain=sub_domain,
                context=context,
                merge=True,  # Merge with existing context
                local_id=local_id
            )

            logger.debug(f"Synced graph state to API for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error syncing graph state to API: {e}", exc_info=True)
            return False

    async def sync_from_api_to_graph(
        self,
        session_id: str,
        sub_domain: str,
        local_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync state from TypeScript API to Python graph state format.

        This retrieves the conversation state from the API and converts it
        to the format expected by the Python LangGraph.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            local_id: Optional business location ID

        Returns:
            Graph state dictionary
        """
        try:
            # Get conversation from API
            conversation = await self.service.get_conversation(
                session_id=session_id,
                sub_domain=sub_domain,
                local_id=local_id
            )

            if not conversation:
                logger.warning(f"Conversation not found: {session_id}")
                return {}

            # Convert to graph state format
            graph_state = self._build_graph_state_from_api(conversation)

            logger.debug(f"Synced API state to graph for session {session_id}")
            return graph_state

        except Exception as e:
            logger.error(f"Error syncing API state to graph: {e}", exc_info=True)
            return {}

    async def add_message_to_history(
        self,
        session_id: str,
        sub_domain: str,
        role: str,
        content: str,
        local_id: Optional[str] = None
    ) -> bool:
        """
        Add a message to the conversation history.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            role: Message role ('user' or 'bot')
            content: Message content
            local_id: Optional business location ID

        Returns:
            True if message was added successfully
        """
        try:
            await self.service.add_message(
                session_id=session_id,
                sub_domain=sub_domain,
                role=role,
                content=content,
                local_id=local_id
            )

            logger.debug(f"Added {role} message to conversation {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding message to history: {e}", exc_info=True)
            return False

    async def link_order_to_conversation(
        self,
        session_id: str,
        sub_domain: str,
        order_id: str,
        local_id: Optional[str] = None
    ) -> bool:
        """
        Link an order to the conversation.

        Args:
            session_id: Conversation session ID
            sub_domain: Business subdomain
            order_id: Order ID to link
            local_id: Optional business location ID

        Returns:
            True if order was linked successfully
        """
        try:
            await self.service.link_order(
                session_id=session_id,
                sub_domain=sub_domain,
                order_id=order_id,
                local_id=local_id
            )

            logger.info(f"Linked order {order_id} to conversation {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error linking order to conversation: {e}", exc_info=True)
            return False

    def _extract_intent_from_graph(self, graph_state: Dict[str, Any]) -> ConversationIntent:
        """
        Extract conversation intent from graph state.

        Args:
            graph_state: Python graph state dictionary

        Returns:
            ConversationIntent enum
        """
        # Check for explicit intent in graph state
        intent_str = graph_state.get("current_intent", "").lower()

        # Map from graph state patterns
        order_stage = graph_state.get("order_stage", "").lower()
        workflow = graph_state.get("workflow", "").lower()

        # Determine intent from various state indicators
        if intent_str in ["menu", "order", "support", "info", "payment", "delivery"]:
            return ConversationIntent(intent_str)

        # Infer from order stage
        if order_stage in ["cart", "selecting_items", "customizing", "awaiting_size", "awaiting_extras"]:
            return ConversationIntent.ORDER
        elif order_stage in ["checkout", "delivery", "awaiting_location"]:
            return ConversationIntent.DELIVERY
        elif order_stage in ["payment", "awaiting_payment", "awaiting_phone"]:
            return ConversationIntent.PAYMENT

        # Infer from workflow
        if workflow == "menu":
            return ConversationIntent.MENU
        elif workflow == "order":
            return ConversationIntent.ORDER

        # Check cart state
        cart = graph_state.get("cart", {})
        if cart and cart.get("items"):
            return ConversationIntent.ORDER

        # Default to idle
        return ConversationIntent.IDLE

    def _build_context_from_graph(self, graph_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build conversation context from graph state.

        Args:
            graph_state: Python graph state dictionary

        Returns:
            Context dictionary for API
        """
        context = {}

        # Extract cart items
        cart = graph_state.get("cart", {})
        if cart and cart.get("items"):
            selected_items = []
            for item in cart["items"]:
                cart_item = {
                    "id": item.get("id", item.get("name", "")),
                    "name": item.get("name", ""),
                    "quantity": item.get("quantity", 1),
                    "price": float(item.get("price", 0)),
                }
                if item.get("notes"):
                    cart_item["notes"] = item["notes"]

                selected_items.append(cart_item)

            context["selectedItems"] = selected_items
            context["orderTotal"] = float(cart.get("total", 0))

        # Extract delivery information
        user_location = graph_state.get("user_location", {})
        if user_location:
            context["deliveryAddress"] = {
                "street": user_location.get("address", ""),
                "city": user_location.get("name", ""),
                "notes": f"Lat: {user_location.get('latitude')}, Lng: {user_location.get('longitude')}"
            }

        # Extract payment method
        payment_method = graph_state.get("payment_method")
        if payment_method:
            # Map payment method to enum value
            payment_map = {
                "cash": "cash",
                "card": "card",
                "transfer": "transfer",
                "yape": "yape",
                "plin": "plin",
                "mercado_pago": "mercado_pago",
                "bank_transfer": "bank_transfer"
            }
            context["paymentMethod"] = payment_map.get(payment_method.lower(), payment_method)

        # Extract customer information
        customer_name = graph_state.get("customer_name")
        if customer_name:
            context["customerName"] = customer_name

        customer_phone = graph_state.get("customer_phone")
        if customer_phone:
            context["customerPhone"] = customer_phone

        # Extract last user message
        messages = graph_state.get("messages", [])
        if messages:
            # Find last user message
            for msg in reversed(messages):
                if hasattr(msg, "type") and msg.type == "human":
                    context["lastUserMessage"] = msg.content
                    break

        # Link current order
        current_order_id = graph_state.get("current_order_id")
        if current_order_id:
            context["currentOrderId"] = current_order_id

        # Add retry count if present
        retry_count = graph_state.get("retry_count")
        if retry_count is not None:
            context["retryCount"] = retry_count

        return context

    def _build_graph_state_from_api(self, conversation: ConversationState) -> Dict[str, Any]:
        """
        Build graph state from API conversation state.

        Args:
            conversation: ConversationState object from API

        Returns:
            Graph state dictionary
        """
        graph_state = {
            "session_id": conversation.sessionId,
            "user_phone": conversation.userId,
            "current_intent": conversation.currentIntent.value,
            "current_step": conversation.currentStep,
        }

        # Extract context
        ctx = conversation.context

        # Cart items
        if ctx.selectedItems:
            cart_items = []
            for item in ctx.selectedItems:
                cart_items.append({
                    "id": item.id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "price": item.price,
                    "notes": item.notes
                })

            graph_state["cart"] = {
                "items": cart_items,
                "total": ctx.orderTotal or 0
            }

        # Delivery address
        if ctx.deliveryAddress:
            graph_state["user_location"] = {
                "address": ctx.deliveryAddress.street or "",
                "city": ctx.deliveryAddress.city or "",
                "postalCode": ctx.deliveryAddress.postalCode or "",
                "notes": ctx.deliveryAddress.notes or ""
            }

        # Payment method
        if ctx.paymentMethod:
            graph_state["payment_method"] = ctx.paymentMethod.value

        # Customer info
        if ctx.customerName:
            graph_state["customer_name"] = ctx.customerName

        if ctx.customerEmail:
            graph_state["customer_email"] = ctx.customerEmail

        # Order info
        if ctx.currentOrderId:
            graph_state["current_order_id"] = ctx.currentOrderId

        if ctx.orderHistory:
            graph_state["order_history"] = ctx.orderHistory

        # Retry count
        if ctx.retryCount is not None:
            graph_state["retry_count"] = ctx.retryCount

        return graph_state
