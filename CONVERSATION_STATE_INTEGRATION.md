# Conversation State Integration Guide

This guide explains how to integrate the TypeScript ConversationState model with your Python AI Companion.

## Overview

The integration provides bidirectional synchronization between:

1. **Python LangGraph State** (SQLite short-term memory) - AI conversation flow
2. **TypeScript/MongoDB Conversation State** - Persistent conversation management

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WhatsApp Cloud API                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           Python FastAPI (AI Companion)                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  WhatsApp Handler (whatsapp_response.py)           │    │
│  └─────────────┬──────────────────────────────────────┘    │
│                │                                             │
│                ▼                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Conversation Middleware                           │    │
│  │  - Initialize conversation                         │    │
│  │  - Track messages                                  │    │
│  │  - Sync state                                      │    │
│  └─────────────┬──────────────────────────────────────┘    │
│                │                                             │
│                ▼                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  LangGraph (AI Processing)                         │    │
│  │  - SQLite short-term memory                        │    │
│  │  - Cart nodes                                      │    │
│  │  - Conversation flow                               │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP API Calls
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           TypeScript API Server (Node.js)                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Conversation API (/api/v1/conversations)          │    │
│  │  - Create/retrieve conversations                   │    │
│  │  - Update intent & context                         │    │
│  │  - Track message history                           │    │
│  │  - Link orders                                     │    │
│  └─────────────┬──────────────────────────────────────┘    │
│                │                                             │
│                ▼                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  MongoDB (ConversationState Model)                 │    │
│  │  - Session management                              │    │
│  │  - Intent tracking                                 │    │
│  │  - Context storage                                 │    │
│  │  - Order history                                   │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### 1. Configuration

Add these settings to your `.env` file:

```bash
# CartaAI API Configuration (used for conversation state sync)
CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe/api/v1
CARTAAI_API_KEY=your_api_key_here  # Your CartaAI API key

# Conversation State Sync Configuration
ENABLE_CONVERSATION_SYNC=true
CONVERSATION_API_TIMEOUT=10.0
```

The conversation state service uses the same `CARTAAI_API_BASE_URL` that powers your menu and orders API integration.

### 2. Dependencies

The integration uses these Python packages (already in your environment):

- `httpx` - Async HTTP client
- `pydantic` - Data validation

## Components

### 1. ConversationStateService

**Location:** `src/ai_companion/services/conversation_state_service.py`

Low-level HTTP client for the TypeScript Conversation API.

**Key Methods:**
- `create_conversation()` - Initialize new conversation
- `get_conversation()` - Retrieve conversation by session ID
- `get_user_conversation()` - Get active conversation for user
- `update_intent()` - Update conversation intent
- `update_context()` - Update conversation context (cart, delivery, etc.)
- `add_message()` - Record message in history
- `link_order()` - Associate order with conversation
- `reset_conversation()` - Clear conversation context
- `extend_expiration()` - Extend conversation TTL

**Usage:**

```python
from ai_companion.services.conversation_state_service import (
    ConversationStateService,
    ConversationIntent
)
from ai_companion.settings import settings

# Initialize service
async with ConversationStateService(
    api_base_url=settings.CARTAAI_API_BASE_URL,
    api_key=settings.CARTAAI_API_KEY,
    timeout=settings.CONVERSATION_API_TIMEOUT
) as service:
    # Create conversation
    conversation = await service.create_conversation(
        user_id="+1234567890",
        sub_domain="my-restaurant"
    )

    # Update intent
    await service.update_intent(
        session_id=conversation.sessionId,
        sub_domain="my-restaurant",
        intent=ConversationIntent.ORDER,
        step="selecting_items"
    )
```

### 2. ConversationStateManager

**Location:** `src/ai_companion/services/conversation_state_manager.py`

Bridge between Python LangGraph state and TypeScript API.

**Key Methods:**
- `initialize_conversation()` - Create or retrieve conversation
- `sync_from_graph_to_api()` - Convert and sync Python state to API
- `sync_from_api_to_graph()` - Convert and sync API state to Python
- `add_message_to_history()` - Record messages
- `link_order_to_conversation()` - Link orders

**Usage:**

```python
from ai_companion.services.conversation_state_manager import ConversationStateManager

manager = ConversationStateManager(conversation_service)

# Initialize
conversation = await manager.initialize_conversation(
    user_phone="+1234567890",
    sub_domain="my-restaurant"
)

# Sync graph state to API
await manager.sync_from_graph_to_api(
    session_id=conversation.sessionId,
    sub_domain="my-restaurant",
    graph_state={"cart": {...}, "order_stage": "cart"}
)
```

### 3. ConversationSyncHelper

**Location:** `src/ai_companion/services/conversation_sync_helper.py`

High-level helper functions for easy integration.

**Key Functions:**
- `initialize_conversation_for_user()` - One-line conversation init
- `sync_graph_state_to_api()` - One-line state sync
- `add_message_to_conversation()` - One-line message tracking
- `link_order_to_conversation()` - One-line order linking

**Usage:**

```python
from ai_companion.services.conversation_sync_helper import (
    initialize_conversation_for_user,
    sync_graph_state_to_api,
    add_message_to_conversation
)

# Initialize conversation
session_id = await initialize_conversation_for_user(
    user_phone="+1234567890",
    sub_domain="my-restaurant"
)

# Track user message
await add_message_to_conversation(
    session_id=session_id,
    sub_domain="my-restaurant",
    role="user",
    content="I want to order a pizza"
)

# Sync state after cart update
await sync_graph_state_to_api(
    session_id=session_id,
    sub_domain="my-restaurant",
    graph_state=graph_state_dict
)
```

### 4. ConversationMiddleware

**Location:** `src/ai_companion/services/conversation_middleware.py`

Advanced: Decorators and context managers for automatic synchronization.

**Features:**
- `ConversationContext` - Context object for tracking conversation state
- `ConversationMiddleware` - Context manager for automatic init/cleanup
- `@auto_sync_state` - Decorator to auto-sync after function execution
- `@track_messages` - Decorator to auto-track messages

**Usage:**

```python
from ai_companion.services.conversation_middleware import ConversationMiddleware

# Context manager approach
async with ConversationMiddleware(user_phone, sub_domain) as conv:
    await conv.add_user_message("I want pizza")
    await conv.sync_state(graph_state)
    await conv.add_bot_message("Added to cart!")
    await conv.link_order("order_123")

# Decorator approach
from ai_companion.services.conversation_middleware import auto_sync_state

@auto_sync_state
async def add_to_cart_node(state: Dict[str, Any]) -> Dict[str, Any]:
    # State automatically synced after execution
    state["cart"]["items"].append(item)
    return state
```

## Integration Guide

### Quick Integration (Recommended)

Use the helper functions for minimal code changes:

#### Step 1: Initialize at Message Start

Add to `whatsapp_response.py` around line 110 (after business lookup):

```python
from ai_companion.services.conversation_sync_helper import (
    initialize_conversation_for_user,
    sync_graph_state_to_api,
    add_message_to_conversation,
    link_order_to_conversation
)

# After extracting business_subdomain and from_number
conversation_session_id = await initialize_conversation_for_user(
    user_phone=from_number,
    sub_domain=business_subdomain,
    bot_id=bot_id
)
```

#### Step 2: Track User Messages

Add after receiving user message content:

```python
# After extracting content from user (line ~644)
if conversation_session_id:
    await add_message_to_conversation(
        session_id=conversation_session_id,
        sub_domain=business_subdomain,
        role="user",
        content=content
    )
```

#### Step 3: Sync State After Cart Operations

Add after each cart node execution:

```python
# After add_to_cart_node, view_cart_node, checkout_node, etc.
if conversation_session_id:
    # Get current graph state
    output_state = await graph.aget_state(
        config={"configurable": {"thread_id": session_id}}
    )
    graph_state_dict = dict(output_state.values) if output_state.values else {}

    # Sync to API
    await sync_graph_state_to_api(
        session_id=conversation_session_id,
        sub_domain=business_subdomain,
        graph_state=graph_state_dict
    )
```

#### Step 4: Track Bot Responses

Add after sending responses:

```python
# After send_response() calls
if conversation_session_id:
    await add_message_to_conversation(
        session_id=conversation_session_id,
        sub_domain=business_subdomain,
        role="bot",
        content=response_message
    )
```

#### Step 5: Link Orders

Add in `cart_nodes.py` after order creation:

```python
# In confirm_order_node, after order is created
from ai_companion.services.conversation_sync_helper import link_order_to_conversation

if order_id and conversation_session_id:
    await link_order_to_conversation(
        session_id=conversation_session_id,
        sub_domain=business_subdomain,
        order_id=order_id
    )
```

### Advanced Integration (Context Manager)

For more structured code, use the ConversationMiddleware:

```python
from ai_companion.services.conversation_middleware import ConversationMiddleware

# In whatsapp_handler
async with ConversationMiddleware(
    user_phone=from_number,
    sub_domain=business_subdomain,
    bot_id=bot_id
) as conv:
    # Track user message
    await conv.add_user_message(content)

    # Process through graph
    await graph.ainvoke(...)

    # Sync state
    output_state = await graph.aget_state(...)
    await conv.sync_state(dict(output_state.values))

    # Track bot response
    await conv.add_bot_message(response_message)

    # Link order if created
    if order_id:
        await conv.link_order(order_id)
```

## State Mapping

### Python → TypeScript

| Python Graph State | TypeScript Context |
|-------------------|-------------------|
| `cart.items` | `context.selectedItems` |
| `cart.total` | `context.orderTotal` |
| `user_location` | `context.deliveryAddress` |
| `payment_method` | `context.paymentMethod` |
| `customer_name` | `context.customerName` |
| `current_order_id` | `context.currentOrderId` |
| `order_stage` | `currentIntent`, `currentStep` |

### Intent Mapping

| Python State | TypeScript Intent |
|-------------|------------------|
| `workflow="menu"` | `currentIntent="menu"` |
| `order_stage="cart"` | `currentIntent="order"` |
| `order_stage="checkout"` | `currentIntent="delivery"` |
| `order_stage="payment"` | `currentIntent="payment"` |

## Testing

### 1. Start CartaAI API Server

Ensure your CartaAI API server (TypeScript backend) is running:

```bash
cd your-cartaai-api
npm run dev
```

### 2. Configure Python App

Update `.env`:

```bash
CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe/api/v1
CARTAAI_API_KEY=your_api_key
ENABLE_CONVERSATION_SYNC=true
```

### 3. Test Message Flow

Send a WhatsApp message and verify:

1. **Conversation Created:**
   - Check TypeScript API logs for conversation creation
   - Query MongoDB for new conversation document

2. **Messages Tracked:**
   - Verify `context.previousMessages` array is populated
   - Check `lastUserMessage` is updated

3. **State Synced:**
   - Add item to cart
   - Verify `context.selectedItems` is updated in MongoDB

4. **Order Linked:**
   - Complete an order
   - Verify `currentOrderId` and `orderHistory` are updated

### 4. Test API Endpoints

Use curl or Postman:

```bash
# Get user's active conversation
curl "https://ssgg.api.cartaai.pe/api/v1/conversations/user/+1234567890?subDomain=my-restaurant" \
  -H "X-Service-API-Key: your_api_key"

# Get conversation by session ID
curl "https://ssgg.api.cartaai.pe/api/v1/conversations/SESSION_ID?subDomain=my-restaurant" \
  -H "X-Service-API-Key: your_api_key"
```

## Error Handling

The integration is designed to fail gracefully:

1. **API Unavailable:** Syncing is skipped, Python app continues normally
2. **Network Errors:** Logged but don't block message processing
3. **Sync Disabled:** All sync operations are no-ops when `ENABLE_CONVERSATION_SYNC=false`

To disable syncing temporarily:

```bash
ENABLE_CONVERSATION_SYNC=false
```

## Performance Considerations

1. **Async Operations:** All API calls are async and don't block message processing
2. **Timeout:** Configure `CONVERSATION_API_TIMEOUT` based on your network
3. **Batching:** Messages are added individually (future: batch updates)
4. **Caching:** The service reuses HTTP client connections

## Monitoring

Add logging to track sync operations:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_companion.services.conversation_state_service")
logger.setLevel(logging.DEBUG)
```

Log messages to watch for:

- `"Conversation initialized: {session_id}"` - New conversation
- `"Synced graph state to API for {session_id}"` - State synced
- `"Added {role} message to conversation"` - Message tracked
- `"Linked order {order_id} to conversation"` - Order linked

## Troubleshooting

### Issue: Conversations not syncing

**Check:**
1. `ENABLE_CONVERSATION_SYNC=true` in `.env`
2. TypeScript API is running and accessible
3. `CONVERSATION_API_URL` is correct
4. Check Python logs for errors

### Issue: State not updating in MongoDB

**Check:**
1. Verify `subDomain` matches between Python and TypeScript
2. Check if `session_id` is being passed correctly
3. Verify state mapping in `_build_context_from_graph()`
4. Check MongoDB for document updates

### Issue: Messages not tracked

**Check:**
1. `add_message_to_conversation()` is called after message processing
2. `session_id` is valid
3. Message content is not empty
4. Check `context.previousMessages` in MongoDB

## Examples

See complete examples in:

- [conversation_integration_example.py](src/ai_companion/interfaces/whatsapp/conversation_integration_example.py) - Integration patterns
- [conversation_middleware.py](src/ai_companion/services/conversation_middleware.py) - Advanced usage

## API Reference

### ConversationStateService

Full API documentation: See docstrings in `conversation_state_service.py`

**Constructor:**
```python
ConversationStateService(
    api_base_url: str,
    api_key: Optional[str] = None,
    timeout: float = 10.0
)
```

**Methods:** See source file for complete list

### ConversationStateManager

Full API documentation: See docstrings in `conversation_state_manager.py`

**Constructor:**
```python
ConversationStateManager(conversation_service: ConversationStateService)
```

**Methods:** See source file for complete list

## Next Steps

1. ✅ Integration services created
2. ✅ Configuration added to settings
3. ⏭️ **Integrate into WhatsApp handler** (see Quick Integration above)
4. ⏭️ **Test with real WhatsApp messages**
5. ⏭️ **Monitor and optimize**
6. ⏭️ **Optional: Add decorators for automatic sync**

## Support

For issues or questions:

1. Check logs in both Python and TypeScript apps
2. Verify API endpoints are accessible
3. Test with `ENABLE_CONVERSATION_SYNC=false` to isolate issues
4. Review MongoDB documents for state consistency

## License

Same as parent project.
