# Quick Start: Conversation Sync Integration

This is a quick reference for integrating conversation sync into your WhatsApp handler.

## ⚡ 5-Minute Integration

### Step 1: Import Helper Functions

Add to top of `whatsapp_response.py` (line 17):

```python
from ai_companion.services.conversation_sync_helper import (
    initialize_conversation_for_user,
    sync_graph_state_to_api,
    add_message_to_conversation,
    link_order_to_conversation
)
```

✅ **Already imported!** (lines 17-21)

---

### Step 2: Initialize Conversation

Add after business lookup (around line 105):

```python
# After: business = await business_service.get_business_by_phone_number_id(phone_number_id)
# Add this:

conversation_session_id = None
if business:
    conversation_session_id = await initialize_conversation_for_user(
        user_phone=from_number,
        sub_domain=business.get("subDomain"),
        local_id=business.get("localId"),
        bot_id=business.get("whatsappBotId")
    )
    logger.info(f"Conversation session: {conversation_session_id}")
```

---

### Step 3: Track User Messages

Add after extracting user message content:

#### For Text Messages (line 650+)

```python
# After: text_body = message["text"]["body"]
if conversation_session_id:
    await add_message_to_conversation(
        session_id=conversation_session_id,
        sub_domain=business.get("subDomain"),
        role="user",
        content=text_body
    )
```

#### For Audio Messages (line 130+)

```python
# After: transcription = await speech_to_text.transcribe_audio(...)
if conversation_session_id:
    await add_message_to_conversation(
        session_id=conversation_session_id,
        sub_domain=business.get("subDomain"),
        role="user",
        content=transcription
    )
```

#### For Image Messages (line 145+)

```python
# After: image_analysis = await image_to_text.analyze_image(...)
if conversation_session_id:
    await add_message_to_conversation(
        session_id=conversation_session_id,
        sub_domain=business.get("subDomain"),
        role="user",
        content=image_analysis
    )
```

---

### Step 4: Sync State After Processing

Add after LangGraph processing (line 705+):

```python
# After: output = await graph.ainvoke(...)
if conversation_session_id:
    # Get current state
    output_state = await graph.aget_state(config)
    if output_state and output_state.values:
        graph_state_dict = dict(output_state.values)

        # Sync to API
        await sync_graph_state_to_api(
            session_id=conversation_session_id,
            sub_domain=business.get("subDomain"),
            graph_state=graph_state_dict
        )
```

---

### Step 5: Track Bot Responses

Add after sending response (line 920+):

```python
# After: await send_response(...)
if conversation_session_id and response_text:
    await add_message_to_conversation(
        session_id=conversation_session_id,
        sub_domain=business.get("subDomain"),
        role="bot",
        content=response_text
    )
```

---

### Step 6: Link Orders (Optional)

If you create orders in your cart nodes, add in `cart_nodes.py`:

```python
# In confirm_order_node, after order creation:
from ai_companion.services.conversation_sync_helper import link_order_to_conversation

async def confirm_order_node(state: OrderState) -> OrderState:
    # ... existing order creation code ...

    # After order is created successfully
    if order_id and session_id:
        await link_order_to_conversation(
            session_id=session_id,
            sub_domain=business_subdomain,
            order_id=order_id
        )

    return state
```

---

## 🔧 Configuration

### Update `.env`

```bash
# Enable conversation sync
ENABLE_CONVERSATION_SYNC=true
CONVERSATION_API_TIMEOUT=10.0

# CartaAI API (if not already set)
CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe
CARTAAI_SUBDOMAIN=your-subdomain
CARTAAI_LOCAL_ID=your-local-id
CARTAAI_API_KEY=your-api-key
USE_CARTAAI_API=true
```

---

## ✅ Testing Checklist

1. **Send a WhatsApp message** to your bot
2. **Check logs** for: `Conversation session: <session_id>`
3. **Verify in API** that conversation was created
4. **Check state sync** after cart operations
5. **Verify message history** in conversation

---

## 🐛 Debugging

### Enable detailed logging:

```python
import logging

# Add to top of whatsapp_response.py
logging.getLogger("ai_companion.services.conversation_state_service").setLevel(logging.DEBUG)
logging.getLogger("ai_companion.services.conversation_sync_helper").setLevel(logging.DEBUG)
```

### Check logs:

```bash
# Search for conversation sync events
grep "conversation" logs/app.log | grep -i "session\|sync\|tenant"

# Check for errors
grep "ERROR.*conversation" logs/app.log
```

---

## 📊 Expected Log Output

### Successful Integration:

```
INFO - Conversation session: bot123_51999999999_1234567890_xyz
DEBUG - Added user message to conversation bot123_51999999999_1234567890_xyz
DEBUG - Successfully synced graph state to API for bot123_51999999999_1234567890_xyz
DEBUG - Added bot message to conversation bot123_51999999999_1234567890_xyz
```

### If Sync is Disabled:

```
DEBUG - Conversation sync is disabled
```

### If Sync Fails (Graceful):

```
WARNING - Failed to sync graph state to API for bot123_51999999999_1234567890_xyz
```

**Note**: Sync failures should NOT prevent message processing!

---

## 🚀 Advanced: Using Middleware

For cleaner code, use the middleware pattern:

```python
from ai_companion.services.conversation_middleware import ConversationMiddleware

async def whatsapp_handler(request: Request) -> Response:
    # ... existing setup ...

    # Use middleware for automatic sync
    async with ConversationMiddleware(
        user_phone=from_number,
        sub_domain=business.get("subDomain"),
        local_id=business.get("localId"),
        bot_id=business.get("whatsappBotId")
    ) as conv:
        # Track user message
        await conv.add_user_message(text_body)

        # Process with graph
        output = await graph.ainvoke(...)

        # Get state and sync
        output_state = await graph.aget_state(config)
        if output_state and output_state.values:
            await conv.sync_state(dict(output_state.values))

        # Track bot response
        await conv.add_bot_message(response_text)

        # Link order (if applicable)
        if order_id:
            await conv.link_order(order_id)
```

---

## 📖 Full Documentation

For complete details, see: [CONVERSATION_SYNC_INTEGRATION.md](./CONVERSATION_SYNC_INTEGRATION.md)

---

## 🎯 Summary

**What you need to do:**

1. ✅ Imports already added
2. ✅ Services already implemented
3. ⚠️ **Add 5 code snippets** to `whatsapp_response.py`:
   - Initialize conversation (after business lookup)
   - Track user messages (3 places: text, audio, image)
   - Sync state (after graph processing)
   - Track bot responses (after sending)
4. ⚠️ **Update `.env`** with conversation sync settings
5. ✅ Test with a WhatsApp message

**Time estimate**: 15-30 minutes

**Risk**: Low (graceful degradation on errors)
