"""
Conversation Sync Helper - Integration utilities for WhatsApp handler

This module provides helper functions to integrate conversation state synchronization
into the WhatsApp message handler workflow.
"""

import logging
from typing import Any, Dict, Optional

from ai_companion.services.conversation_state_service import ConversationStateService
from ai_companion.services.conversation_state_manager import ConversationStateManager
from ai_companion.settings import settings


logger = logging.getLogger(__name__)


# Global service instances (lazy loaded)
_conversation_service: Optional[ConversationStateService] = None
_conversation_manager: Optional[ConversationStateManager] = None


def get_conversation_service() -> Optional[ConversationStateService]:
    """
    Get or create the global ConversationStateService instance.

    Returns:
        ConversationStateService instance or None if sync is disabled
    """
    global _conversation_service

    if not settings.ENABLE_CONVERSATION_SYNC:
        return None

    if _conversation_service is None:
        _conversation_service = ConversationStateService(
            api_base_url=settings.CARTAAI_API_BASE_URL,
            api_key=settings.CARTAAI_API_KEY,
            timeout=settings.CONVERSATION_API_TIMEOUT
        )

    return _conversation_service


def get_conversation_manager() -> Optional[ConversationStateManager]:
    """
    Get or create the global ConversationStateManager instance.

    Returns:
        ConversationStateManager instance or None if sync is disabled
    """
    global _conversation_manager

    if not settings.ENABLE_CONVERSATION_SYNC:
        return None

    service = get_conversation_service()
    if service is None:
        return None

    if _conversation_manager is None:
        _conversation_manager = ConversationStateManager(service)

    return _conversation_manager


async def initialize_conversation_for_user(
    user_phone: str,
    sub_domain: str,
    local_id: Optional[str] = None,
    bot_id: Optional[str] = None
) -> Optional[str]:
    """
    Initialize or retrieve conversation for a user.

    This should be called at the start of message processing to ensure
    the conversation exists in the TypeScript backend.

    Args:
        user_phone: User's phone number
        sub_domain: Business subdomain
        local_id: Optional business location ID
        bot_id: Optional bot ID

    Returns:
        Session ID if successful, None otherwise
    """
    manager = get_conversation_manager()
    if not manager:
        logger.debug("Conversation sync is disabled")
        return None

    try:
        conversation = await manager.initialize_conversation(
            user_phone=user_phone,
            sub_domain=sub_domain,
            local_id=local_id,
            bot_id=bot_id
        )

        logger.info(f"Initialized conversation {conversation.sessionId} for user {user_phone}")
        return conversation.sessionId

    except Exception as e:
        logger.error(f"Failed to initialize conversation for {user_phone}: {e}", exc_info=True)
        return None


async def sync_graph_state_to_api(
    session_id: str,
    sub_domain: str,
    graph_state: Dict[str, Any],
    local_id: Optional[str] = None
) -> bool:
    """
    Sync Python graph state to TypeScript API.

    This should be called after significant state updates (e.g., after cart changes,
    after order creation, after checkout steps).

    Args:
        session_id: Conversation session ID
        sub_domain: Business subdomain
        graph_state: Python graph state dictionary
        local_id: Optional business location ID

    Returns:
        True if sync was successful
    """
    manager = get_conversation_manager()
    if not manager:
        return False

    try:
        success = await manager.sync_from_graph_to_api(
            session_id=session_id,
            sub_domain=sub_domain,
            graph_state=graph_state,
            local_id=local_id
        )

        if success:
            logger.debug(f"Successfully synced graph state to API for {session_id}")
        else:
            logger.warning(f"Failed to sync graph state to API for {session_id}")

        return success

    except Exception as e:
        logger.error(f"Error syncing graph state to API: {e}", exc_info=True)
        return False


async def sync_api_state_to_graph(
    session_id: str,
    sub_domain: str,
    local_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sync TypeScript API state to Python graph format.

    This can be used to restore state from the API or resolve conflicts.

    Args:
        session_id: Conversation session ID
        sub_domain: Business subdomain
        local_id: Optional business location ID

    Returns:
        Graph state dictionary (empty if sync failed)
    """
    manager = get_conversation_manager()
    if not manager:
        return {}

    try:
        graph_state = await manager.sync_from_api_to_graph(
            session_id=session_id,
            sub_domain=sub_domain,
            local_id=local_id
        )

        if graph_state:
            logger.debug(f"Successfully synced API state to graph for {session_id}")
        else:
            logger.warning(f"No state retrieved from API for {session_id}")

        return graph_state

    except Exception as e:
        logger.error(f"Error syncing API state to graph: {e}", exc_info=True)
        return {}


async def add_message_to_conversation(
    session_id: str,
    sub_domain: str,
    role: str,
    content: str,
    local_id: Optional[str] = None
) -> bool:
    """
    Add a message to the conversation history in the API.

    Args:
        session_id: Conversation session ID
        sub_domain: Business subdomain
        role: Message role ('user' or 'bot')
        content: Message content
        local_id: Optional business location ID

    Returns:
        True if message was added successfully
    """
    manager = get_conversation_manager()
    if not manager:
        return False

    try:
        success = await manager.add_message_to_history(
            session_id=session_id,
            sub_domain=sub_domain,
            role=role,
            content=content,
            local_id=local_id
        )

        if success:
            logger.debug(f"Added {role} message to conversation {session_id}")

        return success

    except Exception as e:
        logger.error(f"Error adding message to conversation: {e}", exc_info=True)
        return False


async def link_order_to_conversation(
    session_id: str,
    sub_domain: str,
    order_id: str,
    local_id: Optional[str] = None
) -> bool:
    """
    Link an order to the conversation.

    This should be called after an order is successfully created.

    Args:
        session_id: Conversation session ID
        sub_domain: Business subdomain
        order_id: Order ID to link
        local_id: Optional business location ID

    Returns:
        True if order was linked successfully
    """
    manager = get_conversation_manager()
    if not manager:
        return False

    try:
        success = await manager.link_order_to_conversation(
            session_id=session_id,
            sub_domain=sub_domain,
            order_id=order_id,
            local_id=local_id
        )

        if success:
            logger.info(f"Linked order {order_id} to conversation {session_id}")

        return success

    except Exception as e:
        logger.error(f"Error linking order to conversation: {e}", exc_info=True)
        return False


async def cleanup_conversation_service():
    """
    Cleanup and close the conversation service connections.

    This should be called during application shutdown.
    """
    global _conversation_service

    if _conversation_service:
        try:
            await _conversation_service.close()
            logger.info("Closed conversation service connections")
        except Exception as e:
            logger.error(f"Error closing conversation service: {e}", exc_info=True)
        finally:
            _conversation_service = None
