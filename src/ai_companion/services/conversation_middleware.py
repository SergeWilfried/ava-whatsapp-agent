"""
Conversation Middleware - Automatic state synchronization decorators

This module provides decorators and middleware for automatic conversation state
synchronization, reducing boilerplate code in the WhatsApp handler.
"""

import functools
import logging
from typing import Any, Callable, Dict, Optional

from ai_companion.services.conversation_sync_helper import (
    initialize_conversation_for_user,
    sync_graph_state_to_api,
    add_message_to_conversation,
    link_order_to_conversation
)


logger = logging.getLogger(__name__)


class ConversationContext:
    """
    Context object for conversation state during message processing.

    This object is passed through the message processing pipeline and
    accumulates conversation state for synchronization.
    """

    def __init__(
        self,
        user_phone: str,
        sub_domain: str,
        local_id: Optional[str] = None,
        bot_id: Optional[str] = None
    ):
        """
        Initialize conversation context.

        Args:
            user_phone: User's phone number
            sub_domain: Business subdomain
            local_id: Optional business location ID
            bot_id: Optional bot ID
        """
        self.user_phone = user_phone
        self.sub_domain = sub_domain
        self.local_id = local_id
        self.bot_id = bot_id
        self.session_id: Optional[str] = None
        self.user_messages: list[str] = []
        self.bot_messages: list[str] = []
        self.state_updates: list[Dict[str, Any]] = []
        self.order_ids: list[str] = []

    async def initialize(self) -> bool:
        """
        Initialize the conversation in the backend.

        Returns:
            True if initialization was successful
        """
        try:
            self.session_id = await initialize_conversation_for_user(
                user_phone=self.user_phone,
                sub_domain=self.sub_domain,
                local_id=self.local_id,
                bot_id=self.bot_id
            )

            if self.session_id:
                logger.info(f"Conversation initialized: {self.session_id}")
                return True
            else:
                logger.warning("Could not initialize conversation (sync may be disabled)")
                return False

        except Exception as e:
            logger.error(f"Error initializing conversation: {e}", exc_info=True)
            return False

    async def add_user_message(self, content: str):
        """
        Add a user message to the conversation.

        Args:
            content: Message content
        """
        self.user_messages.append(content)

        if self.session_id:
            await add_message_to_conversation(
                session_id=self.session_id,
                sub_domain=self.sub_domain,
                role="user",
                content=content,
                local_id=self.local_id
            )

    async def add_bot_message(self, content: str):
        """
        Add a bot message to the conversation.

        Args:
            content: Message content
        """
        self.bot_messages.append(content)

        if self.session_id:
            await add_message_to_conversation(
                session_id=self.session_id,
                sub_domain=self.sub_domain,
                role="bot",
                content=content,
                local_id=self.local_id
            )

    async def sync_state(self, graph_state: Dict[str, Any]):
        """
        Sync graph state to the conversation API.

        Args:
            graph_state: Python graph state dictionary
        """
        self.state_updates.append(graph_state)

        if self.session_id:
            await sync_graph_state_to_api(
                session_id=self.session_id,
                sub_domain=self.sub_domain,
                graph_state=graph_state,
                local_id=self.local_id
            )

    async def link_order(self, order_id: str):
        """
        Link an order to the conversation.

        Args:
            order_id: Order ID to link
        """
        self.order_ids.append(order_id)

        if self.session_id:
            await link_order_to_conversation(
                session_id=self.session_id,
                sub_domain=self.sub_domain,
                order_id=order_id,
                local_id=self.local_id
            )


def auto_sync_state(func: Callable) -> Callable:
    """
    Decorator to automatically sync graph state after a function execution.

    Usage:
        @auto_sync_state
        async def add_to_cart_node(state: Dict[str, Any]) -> Dict[str, Any]:
            # ... cart logic ...
            return updated_state

    The decorated function should:
    1. Accept state as first parameter
    2. Return updated state dictionary
    3. Have conversation_context available in state (optional)
    """

    @functools.wraps(func)
    async def wrapper(state: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
        # Execute the original function
        result = await func(state, *args, **kwargs)

        # Try to sync state if conversation context is available
        try:
            # Check if conversation context is in the state
            conv_context = state.get("conversation_context")

            if conv_context and isinstance(conv_context, ConversationContext):
                # Sync the updated state
                await conv_context.sync_state(result)
                logger.debug(f"Auto-synced state after {func.__name__}")

        except Exception as e:
            logger.error(f"Error in auto_sync_state for {func.__name__}: {e}", exc_info=True)

        return result

    return wrapper


def track_messages(role: str):
    """
    Decorator to automatically track messages in conversation history.

    Usage:
        @track_messages(role="user")
        async def process_user_input(state: Dict[str, Any], content: str) -> Dict[str, Any]:
            # ... processing logic ...
            return updated_state

        @track_messages(role="bot")
        async def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
            # ... response logic ...
            state["response"] = "Here is your response"
            return state

    Args:
        role: Message role ('user' or 'bot')
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(state: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
            # Execute the original function
            result = await func(state, *args, **kwargs)

            # Try to track message if conversation context is available
            try:
                conv_context = state.get("conversation_context")

                if conv_context and isinstance(conv_context, ConversationContext):
                    # Extract message content based on role
                    if role == "user":
                        # Try to get user message from various places
                        content = (
                            kwargs.get("content")
                            or state.get("user_message")
                            or state.get("last_user_message")
                        )
                        if content:
                            await conv_context.add_user_message(content)

                    elif role == "bot":
                        # Try to get bot response from various places
                        content = (
                            result.get("response")
                            or result.get("bot_message")
                            or (result.get("messages", [{}])[-1].content if result.get("messages") else None)
                        )
                        if content:
                            await conv_context.add_bot_message(content)

                    logger.debug(f"Tracked {role} message in {func.__name__}")

            except Exception as e:
                logger.error(f"Error in track_messages for {func.__name__}: {e}", exc_info=True)

            return result

        return wrapper

    return decorator


class ConversationMiddleware:
    """
    Middleware class for conversation state synchronization.

    This can be used in a more structured way with FastAPI middleware
    or as a context manager for message processing.
    """

    def __init__(
        self,
        user_phone: str,
        sub_domain: str,
        local_id: Optional[str] = None,
        bot_id: Optional[str] = None
    ):
        """
        Initialize conversation middleware.

        Args:
            user_phone: User's phone number
            sub_domain: Business subdomain
            local_id: Optional business location ID
            bot_id: Optional bot ID
        """
        self.context = ConversationContext(
            user_phone=user_phone,
            sub_domain=sub_domain,
            local_id=local_id,
            bot_id=bot_id
        )

    async def __aenter__(self):
        """
        Async context manager entry - initialize conversation.
        """
        await self.context.initialize()
        return self.context

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit - final sync if needed.
        """
        # Could perform final cleanup or sync here if needed
        if exc_type is not None:
            logger.error(f"Error during conversation processing: {exc_val}")

        return False  # Don't suppress exceptions


# ============================================================================
# Usage Example with Context Manager
# ============================================================================

async def example_usage_with_context_manager():
    """
    Example: Using ConversationMiddleware as a context manager.
    """
    user_phone = "+1234567890"
    sub_domain = "my-restaurant"

    # Use context manager for automatic initialization
    async with ConversationMiddleware(user_phone, sub_domain) as conv:
        # conv is now a ConversationContext with initialized session

        # Track user message
        await conv.add_user_message("I want to order a pizza")

        # Simulate some processing...
        graph_state = {
            "cart": {"items": [{"name": "Pizza", "price": 15.0}]},
            "order_stage": "cart"
        }

        # Sync state
        await conv.sync_state(graph_state)

        # Track bot response
        await conv.add_bot_message("Great! I've added a pizza to your cart.")

        # Link order if created
        # await conv.link_order("order_123")


# ============================================================================
# Usage Example with Decorators
# ============================================================================

@auto_sync_state
async def example_cart_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example: Using @auto_sync_state decorator on a cart node.

    The state will be automatically synced after this function executes.
    """
    # Add item to cart
    state["cart"]["items"].append({"name": "Pizza", "price": 15.0})
    state["order_stage"] = "cart"

    return state


@track_messages(role="bot")
async def example_response_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example: Using @track_messages decorator to track bot responses.

    The bot message will be automatically recorded in conversation history.
    """
    state["response"] = "Your order has been confirmed!"

    return state
