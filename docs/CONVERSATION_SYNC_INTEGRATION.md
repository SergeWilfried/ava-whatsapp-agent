# Conversation Sync API Integration Guide

This guide explains how to integrate the conversation sync endpoints into your WhatsApp agent application.

## Overview

The conversation sync system synchronizes state between:
1. **Python LangGraph Agent** (this app) - Processes messages and manages conversation flow
2. **TypeScript API Server** - Stores conversation state in MongoDB and handles multi-tenant routing

## Problem Solved

When WhatsApp webhook events arrive, they contain:
- ✅ **User phone number** (who sent the message)
- ✅ **Business phone_number_id** (which WhatsApp Business Account)
- ❌ **Subdomain/tenant** (which restaurant/business in your system)

The conversation sync API solves this by providing tenant lookup and state synchronization.

---

## Architecture Flow

```
WhatsApp Webhook → Python Agent → TypeScript API
                       ↓              ↑
                   LangGraph      MongoDB
                   (SQLite)    (Conversation State)
                       ↓              ↑
                       └──────────────┘
                     Bidirectional Sync
```

### Flow Steps:

1. **WhatsApp Message Arrives** → Contains phone number but no subdomain
2. **Lookup Tenant** → Use phone number to find subdomain and session
3. **Process with Agent** → LangGraph processes message with context
4. **Sync State** → Update conversation state in TypeScript API
5. **Record Messages** → Track user and bot messages in history
6. **Link Orders** → Associate orders with conversation

---

## API Endpoints Implemented

### Service Layer: `conversation_state_service.py`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `lookup_tenant_by_phone()` | `GET /api/v1/whatsapp/lookup/tenant/:phoneNumber` | Find subdomain by phone |
| `get_conversation_by_phone()` | `GET /api/v1/whatsapp/lookup/conversation/:phoneNumber` | Get full conversation by phone |
| `sync_conversation_from_agent()` | `PUT /api/v1/whatsapp/agent/conversations/:sessionId/sync` | Unified state sync from agent |
| `add_message_from_agent()` | `POST /api/v1/whatsapp/agent/conversations/:sessionId/messages` | Add message from agent |

### Legacy Methods (Still Supported)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `create_conversation()` | `POST /api/v1/conversations` | Create new conversation |
| `get_conversation()` | `GET /api/v1/conversations/:sessionId` | Get by session ID |
| `update_intent()` | `PATCH /api/v1/conversations/:sessionId/intent` | Update intent/step |
| `update_context()` | `PATCH /api/v1/conversations/:sessionId/context` | Update context |
| `add_message()` | `POST /api/v1/conversations/:sessionId/messages` | Add message (with subdomain) |

---

## Integration Patterns

### Pattern 1: Simple Integration (Recommended)

Use the helper functions in `conversation_sync_helper.py`:

```python
from ai_companion.services.conversation_sync_helper import (
    initialize_conversation_for_user,
    sync_graph_state_to_api,
    add_message_to_conversation,
    link_order_to_conversation
)

async def process_whatsapp_message(phone_number: str, message_text: str):
    # 1. Initialize conversation
    session_id = await initialize_conversation_for_user(
        user_phone=phone_number,
        sub_domain="restaurant-abc",  # From business lookup
        local_id="branch01",
        bot_id="bot123"
    )

    # 2. Add user message
    if session_id:
        await add_message_to_conversation(
            session_id=session_id,
            sub_domain="restaurant-abc",
            role="user",
            content=message_text
        )

    # 3. Process with your agent
    graph_state = await your_agent.process(message_text)

    # 4. Sync state
    if session_id:
        await sync_graph_state_to_api(
            session_id=session_id,
            sub_domain="restaurant-abc",
            graph_state=graph_state
        )

    # 5. Add bot response
    if session_id:
        await add_message_to_conversation(
            session_id=session_id,
            sub_domain="restaurant-abc",
            role="bot",
            content=graph_state["response"]
        )

    # 6. Link order (if created)
    if session_id and graph_state.get("order_id"):
        await link_order_to_conversation(
            session_id=session_id,
            sub_domain="restaurant-abc",
            order_id=graph_state["order_id"]
        )
```

### Pattern 2: Middleware Pattern (Cleaner)

Use the context manager in `conversation_middleware.py`:

```python
from ai_companion.services.conversation_middleware import ConversationMiddleware

async def process_whatsapp_message(phone_number: str, message_text: str):
    async with ConversationMiddleware(
        user_phone=phone_number,
        sub_domain="restaurant-abc",
        local_id="branch01"
    ) as conv:
        # Track user message
        await conv.add_user_message(message_text)

        # Process with agent
        graph_state = await your_agent.process(message_text)

        # Sync state
        await conv.sync_state(graph_state)

        # Track bot response
        await conv.add_bot_message(graph_state["response"])

        # Link order
        if graph_state.get("order_id"):
            await conv.link_order(graph_state["order_id"])
```

### Pattern 3: Direct Service Usage (Advanced)

Use the service directly for custom implementations:

```python
from ai_companion.services.conversation_state_service import ConversationStateService

async with ConversationStateService(
    api_base_url="https://ssgg.api.cartaai.pe",
    api_key="your-api-key"
) as service:
    # Lookup tenant
    tenant_info = await service.lookup_tenant_by_phone("+51999999999")

    if tenant_info:
        session_id = tenant_info["sessionId"]
        subdomain = tenant_info["subDomain"]

        # Process message
        # ...

        # Sync using unified endpoint
        await service.sync_conversation_from_agent(
            session_id=session_id,
            intent="payment",
            step="processing_payment",
            context={
                "selectedItems": [...],
                "orderTotal": 50.00,
                "paymentMethod": "yape"
            },
            metadata={
                "agentProcessedAt": datetime.utcnow().isoformat(),
                "agentVersion": "1.0.0"
            }
        )

        # Add message using agent endpoint
        await service.add_message_from_agent(
            session_id=session_id,
            role="bot",
            content="¡Perfecto! Tu pedido está confirmado."
        )
```

---

## WhatsApp Handler Integration

### Current Flow in `whatsapp_response.py`

Location: `src/ai_companion/interfaces/whatsapp/whatsapp_response.py`

```python
# Line 83: Extract phone_number_id from webhook
phone_number_id = change_value.get("metadata", {}).get("phone_number_id")

# Line 91-98: Lookup business by phone_number_id
if phone_number_id == "709970042210245":
    # Use environment variables
    business_subdomain = "default"
else:
    # Lookup from database
    business = await business_service.get_business_by_phone_number_id(phone_number_id)
    business_subdomain = business.get("subDomain")
```

### Add Conversation Sync (After Line 99)

```python
# Import at top of file
from ai_companion.services.conversation_sync_helper import (
    initialize_conversation_for_user,
    add_message_to_conversation,
    sync_graph_state_to_api,
    link_order_to_conversation
)

# After business lookup (line 99+)
conversation_session_id = None
if business_subdomain:
    conversation_session_id = await initialize_conversation_for_user(
        user_phone=from_number,
        sub_domain=business_subdomain,
        local_id=business.get("localId"),
        bot_id=business.get("whatsappBotId")
    )
    logger.info(f"Conversation initialized: {conversation_session_id}")
```

### Add Message Tracking (After Message Processing)

```python
# After extracting user message content (line 125+, 136+, 644+)
if conversation_session_id:
    await add_message_to_conversation(
        session_id=conversation_session_id,
        sub_domain=business_subdomain,
        role="user",
        content=user_message_content
    )
```

### Add State Sync (After Graph Processing)

```python
# After graph.ainvoke() (line 700+)
if conversation_session_id:
    # Get current state
    output_state = await graph.aget_state(config)
    graph_state_dict = dict(output_state.values) if output_state.values else {}

    # Sync to API
    await sync_graph_state_to_api(
        session_id=conversation_session_id,
        sub_domain=business_subdomain,
        graph_state=graph_state_dict
    )
```

### Add Bot Response Tracking (After Sending Response)

```python
# After send_response() (line 913+)
if conversation_session_id:
    await add_message_to_conversation(
        session_id=conversation_session_id,
        sub_domain=business_subdomain,
        role="bot",
        content=response_text
    )
```

---

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Conversation State Sync Configuration
ENABLE_CONVERSATION_SYNC=true
CONVERSATION_API_TIMEOUT=10.0

# CartaAI API Configuration
CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe
CARTAAI_SUBDOMAIN=your-subdomain
CARTAAI_LOCAL_ID=your-local-id
CARTAAI_API_KEY=your-api-key
USE_CARTAAI_API=true
```

### Settings

Already configured in `settings.py`:

```python
class Settings(BaseSettings):
    # Conversation State Sync Configuration
    ENABLE_CONVERSATION_SYNC: bool = True
    CONVERSATION_API_TIMEOUT: float = 10.0

    # CartaAI API Configuration
    CARTAAI_API_BASE_URL: str = "https://ssgg.api.cartaai.pe"
    CARTAAI_SUBDOMAIN: str | None = None
    CARTAAI_LOCAL_ID: str | None = None
    CARTAAI_API_KEY: str | None = None
    USE_CARTAAI_API: bool = False
```

---

## Error Handling

All methods implement graceful degradation:

```python
try:
    session_id = await initialize_conversation_for_user(...)
    if session_id:
        logger.info(f"Conversation initialized: {session_id}")
    else:
        logger.warning("Conversation sync unavailable")
        # Continue without sync - app still works!
except Exception as e:
    logger.error(f"Conversation sync error: {e}", exc_info=True)
    # Continue processing - don't block user
```

**Key Principle**: Conversation sync failures should **never** prevent message processing.

---

## Testing

### 1. Test Tenant Lookup

```python
from ai_companion.services.conversation_state_service import ConversationStateService

async def test_tenant_lookup():
    async with ConversationStateService(
        api_base_url="https://ssgg.api.cartaai.pe",
        api_key="your-api-key"
    ) as service:
        tenant_info = await service.lookup_tenant_by_phone("+51999999999")

        assert tenant_info is not None
        assert tenant_info["subDomain"] == "restaurant-abc"
        assert "sessionId" in tenant_info

        print(f"✅ Tenant lookup successful: {tenant_info}")
```

### 2. Test Conversation Creation

```python
async def test_conversation_creation():
    from ai_companion.services.conversation_sync_helper import (
        initialize_conversation_for_user
    )

    session_id = await initialize_conversation_for_user(
        user_phone="+51999999999",
        sub_domain="restaurant-abc",
        local_id="branch01"
    )

    assert session_id is not None
    print(f"✅ Conversation created: {session_id}")
```

### 3. Test State Sync

```python
async def test_state_sync():
    from ai_companion.services.conversation_sync_helper import (
        sync_graph_state_to_api
    )

    success = await sync_graph_state_to_api(
        session_id="existing-session-id",
        sub_domain="restaurant-abc",
        graph_state={
            "current_intent": "order",
            "order_stage": "cart",
            "cart": {
                "items": [{"name": "Pizza", "quantity": 1, "price": 15.00}],
                "total": 15.00
            }
        }
    )

    assert success is True
    print("✅ State sync successful")
```

### 4. End-to-End Test

```python
async def test_full_flow():
    phone_number = "+51999999999"
    subdomain = "restaurant-abc"

    # 1. Initialize
    session_id = await initialize_conversation_for_user(
        user_phone=phone_number,
        sub_domain=subdomain
    )

    # 2. Add user message
    await add_message_to_conversation(
        session_id=session_id,
        sub_domain=subdomain,
        role="user",
        content="Quiero una pizza"
    )

    # 3. Sync state
    await sync_graph_state_to_api(
        session_id=session_id,
        sub_domain=subdomain,
        graph_state={"current_intent": "order", "order_stage": "selecting"}
    )

    # 4. Add bot response
    await add_message_to_conversation(
        session_id=session_id,
        sub_domain=subdomain,
        role="bot",
        content="¡Perfecto! Te muestro nuestro menú de pizzas"
    )

    print("✅ Full flow test passed")
```

---

## Troubleshooting

### Issue: "No tenant found for phone"

**Cause**: No active conversation exists for this phone number.

**Solution**:
1. Check if conversation was created via webhook
2. Verify phone number format (E.164: `+51999999999`)
3. Check conversation hasn't expired (default: 24 hours)

### Issue: "Conversation sync disabled"

**Cause**: `ENABLE_CONVERSATION_SYNC=false` in settings.

**Solution**: Set `ENABLE_CONVERSATION_SYNC=true` in `.env`

### Issue: "Connection refused to API"

**Cause**: API server not running or wrong URL.

**Solution**:
1. Verify `CARTAAI_API_BASE_URL` in `.env`
2. Check API server is running
3. Test with: `curl https://ssgg.api.cartaai.pe/health`

### Issue: "State sync failing silently"

**Cause**: Errors are caught for graceful degradation.

**Solution**: Check logs with:
```bash
grep "conversation sync error" logs/app.log
```

---

## Best Practices

### 1. Always Initialize Early

```python
# ✅ GOOD: Initialize at start of message processing
session_id = await initialize_conversation_for_user(...)
# ... rest of processing ...

# ❌ BAD: Initialize later, might miss context
# ... process message ...
session_id = await initialize_conversation_for_user(...)
```

### 2. Sync After Significant Changes

```python
# ✅ GOOD: Sync after cart changes, checkout steps
await add_to_cart(...)
await sync_graph_state_to_api(...)

# ❌ BAD: Only sync at end
await add_to_cart(...)
await update_delivery(...)
await sync_graph_state_to_api(...)  # Lost intermediate state
```

### 3. Use Caching for Tenant Lookups

```python
from cachetools import TTLCache

tenant_cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour

async def get_tenant_cached(phone: str):
    if phone not in tenant_cache:
        tenant_cache[phone] = await service.lookup_tenant_by_phone(phone)
    return tenant_cache[phone]
```

### 4. Implement Idempotency

```python
processed_events = set()  # or use Redis

async def process_webhook(event_id: str, phone: str, message: str):
    if event_id in processed_events:
        logger.info(f"Event {event_id} already processed")
        return

    # Process message
    await process_message(phone, message)

    # Mark as processed
    processed_events.add(event_id)
```

### 5. Monitor Sync Health

```python
import time

class SyncMetrics:
    def __init__(self):
        self.total_syncs = 0
        self.failed_syncs = 0
        self.avg_sync_time = 0

    async def sync_with_metrics(self, *args, **kwargs):
        start = time.time()
        try:
            result = await sync_graph_state_to_api(*args, **kwargs)
            self.total_syncs += 1
            self.avg_sync_time = (
                (self.avg_sync_time * (self.total_syncs - 1) + (time.time() - start))
                / self.total_syncs
            )
            return result
        except Exception as e:
            self.failed_syncs += 1
            raise
```

---

## API Response Examples

### Tenant Lookup Response

```json
{
  "type": "1",
  "message": "Tenant information retrieved successfully",
  "data": {
    "subDomain": "restaurant-abc",
    "botId": "67890abcdef",
    "sessionId": "bot123_51999999999_1234567890_xyz",
    "isActive": true
  }
}
```

### Conversation Sync Response

```json
{
  "type": "1",
  "message": "Conversation synced successfully from agent",
  "data": {
    "sessionId": "bot123_51999999999_1234567890_xyz",
    "currentIntent": "payment",
    "currentStep": "processing_payment",
    "context": {
      "selectedItems": [...],
      "orderTotal": 50.00,
      "paymentMethod": "yape"
    },
    "lastActivity": "2025-12-29T10:06:00.000Z"
  }
}
```

### Message Add Response

```json
{
  "type": "1",
  "message": "Message added successfully",
  "data": {
    "sessionId": "bot123_51999999999_1234567890_xyz",
    "context": {
      "previousMessages": [
        {
          "role": "user",
          "content": "Quiero una pizza",
          "timestamp": "2025-12-29T10:00:00.000Z"
        },
        {
          "role": "bot",
          "content": "¡Perfecto! Tu pedido está confirmado.",
          "timestamp": "2025-12-29T10:06:00.000Z"
        }
      ],
      "lastUserMessage": "Quiero una pizza"
    }
  }
}
```

---

## Summary

### ✅ Implemented

- `lookup_tenant_by_phone()` - Find tenant by phone number
- `get_conversation_by_phone()` - Get full conversation by phone
- `sync_conversation_from_agent()` - Unified state sync endpoint
- `add_message_from_agent()` - Agent-specific message endpoint
- Helper functions for easy integration
- Middleware and decorators for clean code
- Graceful error handling and degradation

### 📋 Next Steps

1. Wire up helper functions in WhatsApp handler
2. Test with real WhatsApp messages
3. Monitor sync performance and errors
4. Add caching for tenant lookups
5. Implement webhook idempotency

### 📚 Related Files

- Service: [conversation_state_service.py](../src/ai_companion/services/conversation_state_service.py)
- Manager: [conversation_state_manager.py](../src/ai_companion/services/conversation_state_manager.py)
- Helper: [conversation_sync_helper.py](../src/ai_companion/services/conversation_sync_helper.py)
- Middleware: [conversation_middleware.py](../src/ai_companion/services/conversation_middleware.py)
- Settings: [settings.py](../src/ai_companion/settings.py)
- WhatsApp Handler: [whatsapp_response.py](../src/ai_companion/interfaces/whatsapp/whatsapp_response.py)
