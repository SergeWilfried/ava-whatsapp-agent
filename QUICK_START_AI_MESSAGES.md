# Quick Start: AI-Generated Messages

## What Was Implemented

The WhatsApp agent now uses **AI-generated messages** for conversational responses while keeping interactive button/list components static for optimal performance.

## Files Created/Modified

### ✅ Created
1. **[src/ai_companion/graph/utils/message_generator.py](src/ai_companion/graph/utils/message_generator.py)** - Core AI message generation
2. **[tests/test_message_generator.py](tests/test_message_generator.py)** - Automated tests
3. **[test_manual_messages.py](test_manual_messages.py)** - Manual testing script

### ✅ Modified
1. **[src/ai_companion/graph/cart_nodes.py](src/ai_companion/graph/cart_nodes.py)** - Updated 6 cart operation nodes
2. **[src/ai_companion/modules/cart/order_messages.py](src/ai_companion/modules/cart/order_messages.py)** - Added async confirmation generator

## How It Works

### Before (Static)
```python
return {
    "messages": AIMessage(content="Great choice! Pizza"),
}
```

### After (AI-Generated)
```python
message = await generate_dynamic_message(
    "item_added",
    {"item_name": "Pizza", "price": 12.99}
)
return {
    "messages": AIMessage(content=message),
}
```

## Available Message Types

| Type | Use Case | Example Output |
|------|----------|----------------|
| `item_added` | Item selected | "Great choice! Pizza has been added 🛒" |
| `cart_empty` | Empty cart | "🛒 Your cart is empty. Browse our menu!" |
| `checkout_start` | Begin checkout | "Perfect! Let's complete your order." |
| `order_confirmed` | Order placed | "✅ Order #12345 confirmed! Thank you!" |
| `request_phone` | Need phone | "Please provide your phone number 📱" |
| `size_selected` | Size chosen | "Large selected! Would you like extras?" |
| `item_not_found` | Error | "I couldn't find that item. Try again?" |
| `item_unavailable` | Out of stock | "Sorry, that item isn't available now." |
| `delivery_method_selected` | Delivery chosen | "Great! We'll deliver to your location." |
| `location_received` | Location shared | "Perfect! We'll deliver to Main St." |

## Testing

### Manual Test
```bash
python test_manual_messages.py
```

Expected output: 11 test messages showing AI-generated and fallback messages

### Check Logs
Messages are logged during generation:
```
INFO - Processing add to cart for: Pizza
INFO - Generated message: Great choice! Pizza has been added to your cart
```

## Configuration

### Language
Edit `src/ai_companion/settings.py`:
```python
LANGUAGE = "en"  # English
LANGUAGE = "fr"  # French
LANGUAGE = "auto"  # Auto-detect
```

### Temperature (Creativity)
In `message_generator.py`:
```python
await generate_dynamic_message("item_added", context, temperature=0.5)
# 0.3 = More consistent
# 0.7 = More creative
```

## Performance

- **AI Message Generation:** ~100-200ms
- **Fallback (if error):** ~0ms
- **Interactive Components:** ~0ms (stay static)
- **Total Added Latency:** ~100-200ms per message

## Error Handling

All message types have **automatic fallbacks**:
- If AI generation fails → Uses static fallback message
- If LLM is down → System continues working
- No breaking changes → Graceful degradation

## Example Usage

### Adding a New Message Type

1. Add template in [message_generator.py](src/ai_companion/graph/utils/message_generator.py):
```python
MESSAGE_TEMPLATES = {
    "new_message": """You are a friendly restaurant assistant.
Context: {context}
Language: {language}
Generate a brief message for...
"""
}
```

2. Add fallback:
```python
def _get_fallback_message(message_type, context):
    fallbacks = {
        "new_message": "Default message here",
    }
```

3. Use in code:
```python
message = await generate_dynamic_message("new_message", {"key": "value"})
```

## Monitoring

### Check if AI Generation is Working
Look for these log entries:
```
✓ INFO - Generated message: [AI-generated text]
✗ ERROR - Error generating message: [error] (using fallback)
```

### Fallback Rate
If you see many fallback errors, check:
1. Groq API key is valid (`settings.GROQ_API_KEY`)
2. Model name is correct (`settings.TEXT_MODEL_NAME`)
3. Network connectivity

## Rollback

If you need to disable AI messages:

**Quick Rollback:**
In `message_generator.py`, change line 79:
```python
async def generate_dynamic_message(message_type, context=None, temperature=0.5):
    # Quick disable: always use fallback
    return _get_fallback_message(message_type, context or {})
```

## What's Next?

Potential enhancements:
1. ✨ **Message Caching** - Cache common messages
2. 📊 **A/B Testing** - Compare AI vs static engagement
3. 🎨 **Custom Personalities** - Restaurant-specific tones
4. 🌍 **More Languages** - Add Spanish, Italian, etc.
5. 💾 **Context Memory** - Reference previous messages

## Support

- **Documentation:** [HYBRID_AI_MESSAGES_IMPLEMENTATION.md](HYBRID_AI_MESSAGES_IMPLEMENTATION.md)
- **Code:** [message_generator.py](src/ai_companion/graph/utils/message_generator.py)
- **Tests:** [test_message_generator.py](tests/test_message_generator.py)

## Success! 🎉

Your WhatsApp agent now generates natural, context-aware messages using AI while maintaining fast performance and reliability.
