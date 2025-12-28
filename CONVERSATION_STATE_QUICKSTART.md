# Conversation State Integration - Quick Start

## Summary

The Python AI Companion now syncs conversation state with your TypeScript/MongoDB backend using the CartaAI API.

## What Was Created

| File | Purpose |
|------|---------|
| `services/conversation_state_service.py` | HTTP client for conversation API endpoints |
| `services/conversation_state_manager.py` | Bridge between Python graph state and TypeScript API |
| `services/conversation_sync_helper.py` | Simple helper functions for integration |
| `services/conversation_middleware.py` | Advanced decorators and context managers |
| `interfaces/whatsapp/conversation_integration_example.py` | Integration examples |
| `CONVERSATION_STATE_INTEGRATION.md` | Full documentation |

## Quick Setup (3 Steps)

### 1. Configure Environment

Add to `.env`:

```bash
# CartaAI API Configuration (already exists)
CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe/api/v1
CARTAAI_API_KEY=your_api_key_here

# Conversation Sync (new)
ENABLE_CONVERSATION_SYNC=true
CONVERSATION_API_TIMEOUT=10.0
```

### 2. Add to WhatsApp Handler

Add these imports at the top of `whatsapp_response.py`:

```python
from ai_companion.services.conversation_sync_helper import (
    initialize_conversation_for_user,
    sync_graph_state_to_api,
    add_message_to_conversation,
    link_order_to_conversation
)
```

### 3. Initialize Conversation (Around line 110)

```python
# After business lookup and extracting from_number, business_subdomain
conversation_session_id = await initialize_conversation_for_user(
    user_phone=from_number,
    sub_domain=business_subdomain,
    bot_id=bot_id
)
```

## Optional Integration Points

### Track User Messages

```python
# After extracting user message content
if conversation_session_id:
    await add_message_to_conversation(
        session_id=conversation_session_id,
        sub_domain=business_subdomain,
        role="user",
        content=content
    )
```

### Sync State After Cart Updates

```python
# After cart node execution
if conversation_session_id:
    output_state = await graph.aget_state(
        config={"configurable": {"thread_id": session_id}}
    )
    graph_state_dict = dict(output_state.values) if output_state.values else {}

    await sync_graph_state_to_api(
        session_id=conversation_session_id,
        sub_domain=business_subdomain,
        graph_state=graph_state_dict
    )
```

### Track Bot Responses

```python
# After sending response
if conversation_session_id:
    await add_message_to_conversation(
        session_id=conversation_session_id,
        sub_domain=business_subdomain,
        role="bot",
        content=response_message
    )
```

### Link Orders

```python
# In cart_nodes.py, after order creation
if order_id and conversation_session_id:
    await link_order_to_conversation(
        session_id=conversation_session_id,
        sub_domain=business_subdomain,
        order_id=order_id
    )
```

## Testing

1. **Start your CartaAI API server**
2. **Send a WhatsApp message**
3. **Check logs for**: `"Conversation initialized: {session_id}"`
4. **Verify in MongoDB**: Query `ConversationState` collection

## How It Works

```
User Message → WhatsApp Handler → Initialize Conversation
                                        ↓
                                   Track Message
                                        ↓
                                LangGraph Processing
                                        ↓
                                   Sync State
                                        ↓
                                 Send Response
                                        ↓
                                Track Bot Message
                                        ↓
                        MongoDB (ConversationState updated)
```

## State Sync

The integration automatically syncs:

- ✅ Cart items → `context.selectedItems`
- ✅ Order total → `context.orderTotal`
- ✅ Delivery address → `context.deliveryAddress`
- ✅ Payment method → `context.paymentMethod`
- ✅ Customer info → `context.customerName`
- ✅ Order stage → `currentIntent`, `currentStep`
- ✅ Messages → `context.previousMessages`
- ✅ Order IDs → `currentOrderId`, `orderHistory`

## Available API Endpoints

All endpoints are at `CARTAAI_API_BASE_URL/conversations`:

- `POST /api/v1/conversations` - Create/initialize conversation
- `GET /api/v1/conversations/:sessionId` - Get conversation by ID
- `GET /api/v1/conversations/user/:userId` - Get user's active conversation
- `PATCH /api/v1/conversations/:sessionId/intent` - Update intent
- `PATCH /api/v1/conversations/:sessionId/context` - Update context
- `POST /api/v1/conversations/:sessionId/messages` - Add message
- `POST /api/v1/conversations/:sessionId/orders` - Link order
- `POST /api/v1/conversations/:sessionId/reset` - Reset context
- `POST /api/v1/conversations/:sessionId/extend` - Extend expiration
- `POST /api/v1/conversations/:sessionId/end` - End conversation
- `GET /api/v1/conversations` - List active conversations

## Disable Syncing

To disable temporarily:

```bash
ENABLE_CONVERSATION_SYNC=false
```

All sync operations become no-ops. The Python app continues working normally.

## Error Handling

- ✅ API unavailable → Sync skipped, app continues
- ✅ Network errors → Logged, no blocking
- ✅ Timeout → Configurable via `CONVERSATION_API_TIMEOUT`

## Full Documentation

See [CONVERSATION_STATE_INTEGRATION.md](CONVERSATION_STATE_INTEGRATION.md) for:
- Complete API reference
- Advanced usage patterns
- Middleware and decorators
- Troubleshooting guide
- Performance considerations

## Support

1. Check both Python and TypeScript logs
2. Verify `CARTAAI_API_BASE_URL` is accessible
3. Test with `ENABLE_CONVERSATION_SYNC=false` to isolate issues
4. Review MongoDB documents for state consistency

## Next Steps

1. ✅ Services created and configured
2. ⏭️ **Integrate into WhatsApp handler** (see step 2-3 above)
3. ⏭️ **Test with real messages**
4. ⏭️ **Monitor logs and MongoDB**
5. ⏭️ **Optimize based on usage patterns**
