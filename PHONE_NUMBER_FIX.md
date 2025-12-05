# Phone Number Fix - Customer Phone Missing Issue

## Problem

The order creation API was failing with "missing customer phone" error because:

1. `user_phone` (WhatsApp sender phone) was being set in `whatsapp_response.py`
2. BUT cart nodes weren't **persisting** it in their return values
3. When state was updated via `graph.aupdate_state()`, `user_phone` was lost
4. When `handle_payment_method_node` tried to use it as fallback, it was `None`

## Root Cause

Cart nodes receive `user_phone` in the state dict, but when they return their result, they don't include `user_phone` in the returned dictionary. This causes it to be dropped from the state.

### Example of the Bug

**Before Fix:**
```python
# whatsapp_response.py sets user_phone
current_state_dict["user_phone"] = from_number  # ✅ Set
result = await cart_nodes.handle_delivery_method_node(current_state_dict)

# BUT handle_delivery_method_node returns:
return {
    "messages": AIMessage(...),
    "delivery_method": delivery_method,
    # ❌ user_phone NOT included!
    "order_stage": OrderStage.PAYMENT.value
}

# When state is updated:
await graph.aupdate_state(values=result)  # ❌ user_phone is lost!

# Later, in handle_payment_method_node:
user_phone = state.get("user_phone")  # ❌ Returns None!
```

## Solution

Added `user_phone` and `customer_phone` to return dictionaries of cart nodes to ensure they persist through the state flow.

## Files Changed

### 1. [cart_nodes.py:415](src/ai_companion/graph/cart_nodes.py:415) - `handle_delivery_method_node`

**Before:**
```python
return {
    "messages": AIMessage(content=next_message),
    "interactive_component": interactive_comp,
    "delivery_method": delivery_method,
    "order_stage": OrderStage.PAYMENT.value
}
```

**After:**
```python
return {
    "messages": AIMessage(content=next_message),
    "interactive_component": interactive_comp,
    "delivery_method": delivery_method,
    "user_phone": state.get("user_phone"),  # ✅ Persist user_phone
    "order_stage": OrderStage.PAYMENT.value
}
```

### 2. [cart_nodes.py:456](src/ai_companion/graph/cart_nodes.py:456) - Phone request in `handle_payment_method_node`

**Before:**
```python
return {
    "messages": [AIMessage(content=message)],
    "order_stage": OrderStage.AWAITING_PHONE.value,
}
```

**After:**
```python
return {
    "messages": [AIMessage(content=message)],
    "user_phone": state.get("user_phone"),  # ✅ Keep user_phone in state
    "order_stage": OrderStage.AWAITING_PHONE.value,
}
```

### 3. [cart_nodes.py:483](src/ai_companion/graph/cart_nodes.py:483) - Order creation in `handle_payment_method_node`

**Before:**
```python
return {
    "messages": AIMessage(content=f"Here's your order summary:"),
    "interactive_component": interactive_comp,
    "payment_method": payment_method,
    "active_order_id": order.api_order_id or order.order_id,
    "order_stage": OrderStage.CONFIRMED.value
}
```

**After:**
```python
return {
    "messages": AIMessage(content=f"Here's your order summary:"),
    "interactive_component": interactive_comp,
    "payment_method": payment_method,
    "customer_phone": customer_phone,  # ✅ Persist customer_phone
    "active_order_id": order.api_order_id or order.order_id,
    "order_stage": OrderStage.CONFIRMED.value
}
```

### 4. [cart_nodes.py:504-506](src/ai_companion/graph/cart_nodes.py:504-506) - Fallback in `confirm_order_node`

**Added:**
```python
# Fallback to user_phone if customer_phone not set
if not customer_phone:
    customer_phone = state.get("user_phone")
    logger.info(f"confirm_order_node: Using user_phone as fallback: {customer_phone}")
```

## How It Works Now

### Flow 1: Using WhatsApp Phone Number (Pickup/Dine-in)

```
1. User clicks "Checkout"
   ↓
2. whatsapp_response.py: current_state_dict["user_phone"] = from_number
   ↓
3. checkout_node(): Passes through state
   ↓
4. handle_delivery_method_node():
   - Returns user_phone in state ✅
   ↓
5. State persisted: user_phone = "+1234567890"
   ↓
6. handle_payment_method_node():
   - customer_phone = state.get("customer_phone")  # None
   - user_phone = state.get("user_phone")  # "+1234567890" ✅
   - customer_phone = user_phone  # Uses fallback ✅
   - Creates order with customer_phone ✅
```

### Flow 2: User Provides Phone Number

```
1. handle_payment_method_node():
   - No customer_phone, no user_phone
   - Shows phone request message ✅
   - Returns user_phone in state (even if None)
   ↓
2. User types phone number: "5551234567"
   ↓
3. whatsapp_response.py detects AWAITING_PHONE:
   - Sets customer_phone = "5551234567"
   - Sets user_phone = from_number
   ↓
4. Retries payment method handler:
   - customer_phone = "5551234567" ✅
   - Creates order successfully ✅
```

## Testing Checklist

- [x] Fix applied to all relevant cart nodes
- [x] Added fallback to user_phone in confirm_order_node
- [x] user_phone persisted through delivery method selection
- [x] customer_phone persisted after order creation
- [x] Phone request flow includes user_phone

## Expected Behavior

### Scenario 1: WhatsApp Number Used
- User proceeds through checkout
- System uses WhatsApp phone number automatically
- No phone request shown
- Order created successfully ✅

### Scenario 2: Phone Request Needed
- System detects missing phone
- Shows AI-generated message: "To finalize your order, please provide your phone number 📱"
- User provides phone
- Order created with provided phone ✅

### Scenario 3: Phone Already in State
- Customer phone was set earlier (e.g., from profile)
- System uses existing customer_phone
- No phone request shown ✅

## Logs to Look For

### Success Logs:
```
INFO - Order creation - customer_phone: None, user_phone: +1234567890
INFO - Using user_phone as customer_phone: +1234567890
INFO - Order created successfully
```

### Phone Request Logs:
```
WARNING - No customer_phone or user_phone available - requesting from user
INFO - Received phone number from user: 5551234567
INFO - Order creation - customer_phone: 5551234567, user_phone: +1234567890
```

### Fallback Logs:
```
INFO - confirm_order_node: Using user_phone as fallback: +1234567890
```

## Related Files

- [cart_nodes.py](src/ai_companion/graph/cart_nodes.py) - Cart operation nodes
- [whatsapp_response.py](src/ai_companion/interfaces/whatsapp/whatsapp_response.py) - Webhook handler
- [message_generator.py](src/ai_companion/graph/utils/message_generator.py) - AI message generation

## Impact

- ✅ **Fixed:** Order creation no longer fails due to missing customer_phone
- ✅ **Improved:** Phone number request now uses AI-generated message
- ✅ **Maintained:** Backward compatibility with existing flows
- ✅ **Added:** Multiple fallback strategies for phone number

## Deployment Notes

1. Deploy this fix immediately - it's a critical bug fix
2. Monitor logs for "Order creation - customer_phone:" messages
3. Track phone request rate (should be low if WhatsApp numbers work)
4. No database migrations needed
5. No configuration changes required

---

**Status:** ✅ Fixed and Ready for Deployment
**Priority:** 🔴 Critical
**Tested:** ⏳ Needs Production Validation
