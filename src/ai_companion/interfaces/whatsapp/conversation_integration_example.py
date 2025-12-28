"""
Example: Conversation State Integration in WhatsApp Handler

This file demonstrates how to integrate conversation state synchronization
into the existing WhatsApp handler workflow.

INTEGRATION POINTS:

1. At the start of message processing (after extracting user_phone and sub_domain)
2. After significant state changes (cart updates, checkout steps)
3. After order creation
4. When recording messages

See the code examples below for specific integration patterns.
"""

from typing import Dict, Any, Optional
import logging

from ai_companion.services.conversation_sync_helper import (
    initialize_conversation_for_user,
    sync_graph_state_to_api,
    add_message_to_conversation,
    link_order_to_conversation
)

logger = logging.getLogger(__name__)


# ============================================================================
# EXAMPLE 1: Initialize conversation at the start of message processing
# ============================================================================

async def example_initialize_conversation(
    from_number: str,
    business_subdomain: str,
    bot_id: Optional[str] = None
) -> Optional[str]:
    """
    Example: Initialize conversation at the start of message processing.

    Add this near the beginning of whatsapp_handler(), after you've extracted
    the user's phone number and business subdomain.

    Location in whatsapp_response.py: Around line 110, after business lookup

    Returns:
        Session ID if successful
    """
    # Initialize or retrieve conversation
    conversation_session_id = await initialize_conversation_for_user(
        user_phone=from_number,
        sub_domain=business_subdomain,
        bot_id=bot_id
    )

    if conversation_session_id:
        logger.info(f"Conversation ready: {conversation_session_id}")
    else:
        logger.warning("Conversation sync unavailable (continuing without sync)")

    return conversation_session_id


# ============================================================================
# EXAMPLE 2: Sync state after cart operations
# ============================================================================

async def example_sync_after_cart_update(
    session_id: str,
    sub_domain: str,
    graph_state: Dict[str, Any]
):
    """
    Example: Sync state after cart operations.

    Add this after cart operations like add_to_cart, view_cart, checkout.

    Location in whatsapp_response.py:
    - After line 305 (add_to_cart_node)
    - After line 335 (view_cart_node)
    - After line 363 (checkout_node)
    - After line 393 (handle_size_selection_node)
    - After line 421 (handle_extras_selection_node)
    - After line 451 (handle_delivery_method_node)
    - After line 481 (handle_payment_method_node)
    """
    # Sync the updated graph state to the conversation API
    await sync_graph_state_to_api(
        session_id=session_id,
        sub_domain=sub_domain,
        graph_state=graph_state
    )


# ============================================================================
# EXAMPLE 3: Record messages in conversation history
# ============================================================================

async def example_record_user_message(
    conversation_session_id: str,
    sub_domain: str,
    user_message: str
):
    """
    Example: Record user message in conversation history.

    Add this after receiving a user message.

    Location in whatsapp_response.py:
    - After line 644 (text message received)
    - After line 125 (audio message transcribed)
    - After line 136 (image message analyzed)
    """
    # Record user message
    await add_message_to_conversation(
        session_id=conversation_session_id,
        sub_domain=sub_domain,
        role="user",
        content=user_message
    )


async def example_record_bot_response(
    conversation_session_id: str,
    sub_domain: str,
    bot_response: str
):
    """
    Example: Record bot response in conversation history.

    Add this after sending a response to the user.

    Location in whatsapp_response.py:
    - After line 913 (send_response called)
    """
    # Record bot response
    await add_message_to_conversation(
        session_id=conversation_session_id,
        sub_domain=sub_domain,
        role="bot",
        content=bot_response
    )


# ============================================================================
# EXAMPLE 4: Link order after successful creation
# ============================================================================

async def example_link_order(
    conversation_session_id: str,
    sub_domain: str,
    order_id: str
):
    """
    Example: Link order to conversation after successful order creation.

    Add this after the order is successfully created in confirm_order_node.

    Location: In cart_nodes.py, after order creation in confirm_order_node
    """
    # Link the order to the conversation
    await link_order_to_conversation(
        session_id=conversation_session_id,
        sub_domain=sub_domain,
        order_id=order_id
    )

    logger.info(f"Order {order_id} linked to conversation {conversation_session_id}")


# ============================================================================
# EXAMPLE 5: Complete integration in WhatsApp handler
# ============================================================================

async def example_complete_integration_flow():
    """
    Example: Complete integration flow showing all integration points.

    This is a pseudo-code example showing where to add sync calls
    in the existing WhatsApp handler flow.
    """

    # --- START OF MESSAGE PROCESSING ---

    # 1. Extract business info and user phone
    from_number = "phone_number"  # Extracted from WhatsApp webhook
    business_subdomain = "my-restaurant"  # From business lookup
    bot_id = "bot_123"  # From business config

    # 2. Initialize conversation (NEW)
    conversation_session_id = await initialize_conversation_for_user(
        user_phone=from_number,
        sub_domain=business_subdomain,
        bot_id=bot_id
    )

    # 3. Record incoming user message (NEW)
    user_message_content = "I want to order a pizza"
    if conversation_session_id:
        await add_message_to_conversation(
            session_id=conversation_session_id,
            sub_domain=business_subdomain,
            role="user",
            content=user_message_content
        )

    # 4. Process through LangGraph (existing code)
    # ... graph.ainvoke() ...
    # ... get state ...

    # 5. Sync state after processing (NEW)
    if conversation_session_id:
        # Assuming you have access to graph state
        output_state = {}  # Get this from graph.aget_state()
        graph_state_dict = dict(output_state.values) if output_state.values else {}

        await sync_graph_state_to_api(
            session_id=conversation_session_id,
            sub_domain=business_subdomain,
            graph_state=graph_state_dict
        )

    # 6. Send response to user (existing code)
    response_message = "Sure! Let me show you our pizza menu."
    # ... send_response() ...

    # 7. Record bot response (NEW)
    if conversation_session_id:
        await add_message_to_conversation(
            session_id=conversation_session_id,
            sub_domain=business_subdomain,
            role="bot",
            content=response_message
        )

    # --- END OF MESSAGE PROCESSING ---


# ============================================================================
# INTEGRATION CHECKLIST
# ============================================================================

"""
INTEGRATION CHECKLIST:

[ ] 1. Add initialize_conversation_for_user() at start of message processing
       Location: whatsapp_response.py, line ~110 (after business lookup)

[ ] 2. Store conversation_session_id in a variable for later use

[ ] 3. Add add_message_to_conversation() for user messages
       Location: After extracting message content from user

[ ] 4. Add sync_graph_state_to_api() after cart operations
       Locations:
       - After add_to_cart_node (line ~305)
       - After view_cart_node (line ~335)
       - After checkout_node (line ~363)
       - After handle_size_selection_node (line ~393)
       - After handle_extras_selection_node (line ~421)
       - After handle_delivery_method_node (line ~451)
       - After handle_payment_method_node (line ~481)

[ ] 5. Add add_message_to_conversation() for bot responses
       Location: After send_response() calls

[ ] 6. Add link_order_to_conversation() after order creation
       Location: In cart_nodes.py, confirm_order_node

[ ] 7. Update .env with conversation API settings:
       CONVERSATION_API_URL=http://localhost:3000
       ENABLE_CONVERSATION_SYNC=true

[ ] 8. Test the integration:
       - Send a message to the WhatsApp bot
       - Check TypeScript API logs for conversation creation
       - Verify state is synced after cart operations
       - Confirm orders are linked to conversations
"""
