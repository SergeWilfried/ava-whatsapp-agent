# Conversation Sync - Ready-to-Use Code Snippets

Copy and paste these snippets directly into your code.

---

## 📍 Location 1: Initialize Conversation

**File**: `src/ai_companion/interfaces/whatsapp/whatsapp_response.py`
**Location**: After line 105 (after business lookup)
**Action**: Add variable to store session ID

### Code to Add:

```python
            if not business:
                logger.error(f"No business found for phone_number_id: {phone_number_id}")
                # Return 200 to prevent Meta from retrying
                return Response(content="OK", status_code=200)

            business_name = business.get("name", "Unknown Business")
            business_subdomain = business.get("subDomain")
            whatsapp_token = business.get("whatsappToken")
            logger.info(f"Handling message for business: {business_name} (subdomain: {business_subdomain})")

            # ============================================================
            # CONVERSATION SYNC: Initialize conversation for this user
            # ============================================================
            conversation_session_id = None
            try:
                conversation_session_id = await initialize_conversation_for_user(
                    user_phone=from_number,
                    sub_domain=business_subdomain,
                    local_id=business.get("localId"),
                    bot_id=business.get("whatsappBotId")
                )
                if conversation_session_id:
                    logger.info(f"Conversation session initialized: {conversation_session_id}")
                else:
                    logger.debug("Conversation sync is disabled or unavailable")
            except Exception as e:
                logger.warning(f"Failed to initialize conversation: {e}")
                # Continue without sync - app should still work
            # ============================================================
```

---

## 📍 Location 2: Track Audio Messages

**File**: `src/ai_companion/interfaces/whatsapp/whatsapp_response.py`
**Location**: After line 132 (after audio transcription)

### Code to Add:

```python
                    transcription = await speech_to_text.transcribe_audio(
                        audio_url=audio_url,
                        phone_number_id=phone_number_id,
                    )
                    logger.info(f"Audio transcription: {transcription}")

                    # ============================================================
                    # CONVERSATION SYNC: Track user audio message
                    # ============================================================
                    if conversation_session_id and transcription:
                        try:
                            await add_message_to_conversation(
                                session_id=conversation_session_id,
                                sub_domain=business_subdomain,
                                role="user",
                                content=f"[Audio message] {transcription}"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to track audio message: {e}")
                    # ============================================================
```

---

## 📍 Location 3: Track Image Messages

**File**: `src/ai_companion/interfaces/whatsapp/whatsapp_response.py`
**Location**: After line 220 (after image analysis)

### Code to Add:

```python
                        image_analysis = await image_to_text.analyze_image(
                            image_bytes=image_bytes,
                            phone_number_id=phone_number_id,
                        )
                        logger.info(f"Image analysis result: {image_analysis}")

                        # ============================================================
                        # CONVERSATION SYNC: Track user image message
                        # ============================================================
                        if conversation_session_id and image_analysis:
                            try:
                                await add_message_to_conversation(
                                    session_id=conversation_session_id,
                                    sub_domain=business_subdomain,
                                    role="user",
                                    content=f"[Image] {image_analysis}"
                                )
                            except Exception as e:
                                logger.warning(f"Failed to track image message: {e}")
                        # ============================================================
```

---

## 📍 Location 4: Track Text Messages

**File**: `src/ai_companion/interfaces/whatsapp/whatsapp_response.py`
**Location**: After line 655 (after extracting text message)

### Code to Add:

```python
                    # Handle text messages (non-interactive)
                    text_body = message["text"]["body"]
                    logger.info(f"Text message received: {text_body}")

                    # ============================================================
                    # CONVERSATION SYNC: Track user text message
                    # ============================================================
                    if conversation_session_id:
                        try:
                            await add_message_to_conversation(
                                session_id=conversation_session_id,
                                sub_domain=business_subdomain,
                                role="user",
                                content=text_body
                            )
                        except Exception as e:
                            logger.warning(f"Failed to track text message: {e}")
                    # ============================================================
```

---

## 📍 Location 5: Sync State After Processing

**File**: `src/ai_companion/interfaces/whatsapp/whatsapp_response.py`
**Location**: After line 710 (after graph.ainvoke)

### Code to Add:

```python
                    # Process with graph
                    output = await graph.ainvoke(
                        {"messages": [HumanMessage(content=text_body)]},
                        config=config,
                    )

                    # ============================================================
                    # CONVERSATION SYNC: Sync graph state to API
                    # ============================================================
                    if conversation_session_id:
                        try:
                            # Get current state from graph
                            output_state = await graph.aget_state(config)
                            if output_state and output_state.values:
                                graph_state_dict = dict(output_state.values)

                                # Sync to conversation API
                                await sync_graph_state_to_api(
                                    session_id=conversation_session_id,
                                    sub_domain=business_subdomain,
                                    graph_state=graph_state_dict
                                )
                                logger.debug(f"Synced state for session {conversation_session_id}")
                        except Exception as e:
                            logger.warning(f"Failed to sync graph state: {e}")
                    # ============================================================
```

---

## 📍 Location 6: Track Bot Responses

**File**: `src/ai_companion/interfaces/whatsapp/whatsapp_response.py`
**Location**: After line 925 (after sending response)

### Helper Function to Add (at top level, around line 980):

```python
async def track_bot_response(
    conversation_session_id: Optional[str],
    business_subdomain: str,
    response_text: str
) -> None:
    """
    Track bot response in conversation history.

    Args:
        conversation_session_id: Session ID (None if sync disabled)
        business_subdomain: Business subdomain
        response_text: Bot's response text
    """
    if not conversation_session_id:
        return

    try:
        await add_message_to_conversation(
            session_id=conversation_session_id,
            sub_domain=business_subdomain,
            role="bot",
            content=response_text
        )
        logger.debug(f"Tracked bot response for session {conversation_session_id}")
    except Exception as e:
        logger.warning(f"Failed to track bot response: {e}")
```

### Usage (after each send_response call):

```python
                    # Send response
                    await send_response(
                        recipient_phone_number=from_number,
                        message_text=response_text,
                        phone_number_id=phone_number_id,
                        whatsapp_token=whatsapp_token
                    )

                    # Track bot response
                    await track_bot_response(
                        conversation_session_id,
                        business_subdomain,
                        response_text
                    )
```

---

## 📍 Location 7: Link Orders (Optional)

**File**: `src/ai_companion/graph/cart_nodes.py`
**Location**: In `confirm_order_node` function, after order creation

### Add Import at Top:

```python
from ai_companion.services.conversation_sync_helper import link_order_to_conversation
```

### Code to Add in confirm_order_node:

```python
async def confirm_order_node(state: OrderState) -> OrderState:
    """Confirm and submit order to restaurant API."""

    logger.info("=== CONFIRM ORDER NODE ===")
    cart = state.get("cart", {})
    items = cart.get("items", [])

    if not items:
        logger.error("Cannot confirm order: cart is empty")
        state["order_status"] = "failed"
        return state

    # ... existing order creation code ...

    try:
        # Create order via API
        order_response = await create_order_via_api(order_data)

        if order_response and order_response.get("_id"):
            order_id = order_response["_id"]
            order_number = order_response.get("orderNumber", "N/A")

            logger.info(f"✅ Order created successfully: {order_number} (ID: {order_id})")

            # ============================================================
            # CONVERSATION SYNC: Link order to conversation
            # ============================================================
            session_id = state.get("session_id")
            sub_domain = state.get("sub_domain")

            if session_id and sub_domain and order_id:
                try:
                    await link_order_to_conversation(
                        session_id=session_id,
                        sub_domain=sub_domain,
                        order_id=order_id
                    )
                    logger.info(f"Linked order {order_id} to conversation {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to link order to conversation: {e}")
            # ============================================================

            # Update state
            state["order_id"] = order_id
            state["order_number"] = order_number
            state["order_status"] = "confirmed"
        else:
            logger.error("Order creation failed: no response from API")
            state["order_status"] = "failed"

    except Exception as e:
        logger.error(f"Error creating order: {e}", exc_info=True)
        state["order_status"] = "failed"

    return state
```

---

## 🔧 Environment Variables

**File**: `.env`

```bash
# ============================================================
# Conversation State Sync Configuration
# ============================================================
ENABLE_CONVERSATION_SYNC=true
CONVERSATION_API_TIMEOUT=10.0

# ============================================================
# CartaAI API Configuration (for conversation state)
# ============================================================
CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe
CARTAAI_SUBDOMAIN=your-restaurant-subdomain
CARTAAI_LOCAL_ID=your-location-id
CARTAAI_API_KEY=your-api-key
USE_CARTAAI_API=true
```

---

## 📊 Validation Script

Save as `scripts/test_conversation_sync.py`:

```python
#!/usr/bin/env python3
"""
Test script for conversation sync integration.
Run with: python scripts/test_conversation_sync.py
"""

import asyncio
import logging
from ai_companion.services.conversation_sync_helper import (
    initialize_conversation_for_user,
    add_message_to_conversation,
    sync_graph_state_to_api,
)
from ai_companion.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_conversation_sync():
    """Test conversation sync integration."""

    # Test phone number
    test_phone = "+51999999999"
    test_subdomain = settings.CARTAAI_SUBDOMAIN

    if not test_subdomain:
        logger.error("CARTAAI_SUBDOMAIN not set in .env")
        return

    logger.info("=" * 60)
    logger.info("Testing Conversation Sync Integration")
    logger.info("=" * 60)

    # Test 1: Initialize conversation
    logger.info("\n1. Testing conversation initialization...")
    session_id = await initialize_conversation_for_user(
        user_phone=test_phone,
        sub_domain=test_subdomain,
        local_id=settings.CARTAAI_LOCAL_ID
    )

    if session_id:
        logger.info(f"✅ Conversation initialized: {session_id}")
    else:
        logger.warning("⚠️  Conversation sync appears to be disabled")
        return

    # Test 2: Add user message
    logger.info("\n2. Testing message tracking...")
    try:
        await add_message_to_conversation(
            session_id=session_id,
            sub_domain=test_subdomain,
            role="user",
            content="Test message from integration script"
        )
        logger.info("✅ User message tracked")
    except Exception as e:
        logger.error(f"❌ Failed to track user message: {e}")

    # Test 3: Sync state
    logger.info("\n3. Testing state sync...")
    try:
        success = await sync_graph_state_to_api(
            session_id=session_id,
            sub_domain=test_subdomain,
            graph_state={
                "current_intent": "order",
                "order_stage": "test",
                "cart": {
                    "items": [{"name": "Test Item", "quantity": 1, "price": 10.0}],
                    "total": 10.0
                }
            }
        )
        if success:
            logger.info("✅ State synced successfully")
        else:
            logger.warning("⚠️  State sync returned False")
    except Exception as e:
        logger.error(f"❌ Failed to sync state: {e}")

    # Test 4: Add bot response
    logger.info("\n4. Testing bot response tracking...")
    try:
        await add_message_to_conversation(
            session_id=session_id,
            sub_domain=test_subdomain,
            role="bot",
            content="Test response from integration script"
        )
        logger.info("✅ Bot response tracked")
    except Exception as e:
        logger.error(f"❌ Failed to track bot response: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("✅ All tests completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_conversation_sync())
```

**Run the test:**

```bash
python scripts/test_conversation_sync.py
```

---

## ✅ Integration Checklist

Print this and check off as you go:

```
Conversation Sync Integration Checklist
========================================

[ ] 1. Verify imports in whatsapp_response.py (line 17-21)
       ✓ initialize_conversation_for_user
       ✓ sync_graph_state_to_api
       ✓ add_message_to_conversation
       ✓ link_order_to_conversation

[ ] 2. Add conversation initialization (after line 105)
       ✓ Initialize conversation_session_id variable
       ✓ Call initialize_conversation_for_user()
       ✓ Add error handling (try/except)
       ✓ Add logging

[ ] 3. Track user messages
       [ ] Audio messages (after line 132)
       [ ] Image messages (after line 220)
       [ ] Text messages (after line 655)

[ ] 4. Sync state after processing (after line 710)
       ✓ Get output_state from graph
       ✓ Convert to dict
       ✓ Call sync_graph_state_to_api()
       ✓ Add error handling

[ ] 5. Track bot responses
       ✓ Add track_bot_response() helper function
       ✓ Call after each send_response()
       ✓ Add error handling

[ ] 6. Link orders (optional)
       [ ] Import link_order_to_conversation in cart_nodes.py
       [ ] Add call in confirm_order_node
       [ ] Get session_id and sub_domain from state

[ ] 7. Configuration
       [ ] Update .env with ENABLE_CONVERSATION_SYNC=true
       [ ] Set CARTAAI_API_BASE_URL
       [ ] Set CARTAAI_SUBDOMAIN
       [ ] Set CARTAAI_API_KEY

[ ] 8. Testing
       [ ] Run test script: python scripts/test_conversation_sync.py
       [ ] Send WhatsApp message and check logs
       [ ] Verify conversation created in API
       [ ] Check state sync in API
       [ ] Verify message history

[ ] 9. Monitoring
       [ ] Add logging for sync events
       [ ] Monitor error rates
       [ ] Check API response times
```

---

## 🎯 Expected Results

After integration, you should see in logs:

```
INFO - Handling message for business: Restaurant ABC (subdomain: restaurant-abc)
INFO - Conversation session initialized: bot123_51999999999_1234567890_xyz
DEBUG - Added user message to conversation bot123_51999999999_1234567890_xyz
DEBUG - Synced state for session bot123_51999999999_1234567890_xyz
DEBUG - Tracked bot response for session bot123_51999999999_1234567890_xyz
```

If sync is disabled:

```
DEBUG - Conversation sync is disabled or unavailable
```

If sync fails (should not affect app):

```
WARNING - Failed to sync graph state: Connection refused
```

---

## 📖 Documentation Links

- [Full Integration Guide](./CONVERSATION_SYNC_INTEGRATION.md)
- [Quick Start Guide](./QUICK_START_CONVERSATION_SYNC.md)
- [API Documentation](../README.md)

---

**Questions?** Check logs with:
```bash
grep -i "conversation" logs/app.log | tail -50
```
