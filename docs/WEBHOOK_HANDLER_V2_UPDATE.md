# Webhook Handler V2 Updates ✅

## Overview

Updated webhook handlers to support V2 API responses, including presentation IDs, modifier selections, and API product/category IDs.

---

## 📝 Files Updated

### 1. cart_handler.py ✅

**File:** `src/ai_companion/interfaces/whatsapp/cart_handler.py`

**Changes Made:**

#### Added V2 Imports
```python
from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    extract_presentation_id,
    extract_modifier_selections,
)
```

#### Enhanced `is_cart_interaction()` Method
Added support for V2 API interaction patterns:

```python
# V2 API patterns
# Check presentation ID pattern (e.g., "size_pres001", "size_pres002")
if interaction_id.startswith("size_pres"):
    return True

# Check modifier selection pattern (e.g., "mod_mod001_opt001")
if interaction_id.startswith("mod_"):
    return True

# Check product ID pattern from API (e.g., "prod_6748abc123")
if interaction_id.startswith("prod_"):
    return True

# Check category ID pattern from API (e.g., "cat_6748abc123")
if interaction_id.startswith("cat_"):
    return True
```

#### Enhanced `determine_cart_action()` Method
Added V2 routing before legacy patterns:

```python
# V2 API: Category selection from API (e.g., "cat_6748abc123")
if interaction_id.startswith("cat_"):
    return "view_category_carousel", {"selected_category_id": interaction_id}

# V2 API: Product selection from API (e.g., "prod_6748abc123")
if interaction_id.startswith("prod_"):
    return "add_to_cart", {
        "current_item": {"menu_item_id": interaction_id},
        "order_stage": OrderStage.SELECTING.value
    }

# V2 API: Size selection with presentation ID (e.g., "size_pres001")
if interaction_id.startswith("size_"):
    return "handle_size", {}

# V2 API: Modifier selection (e.g., "mod_mod001_opt001")
if interaction_id.startswith("mod_"):
    return "handle_extras", {}
```

#### New Method: `extract_v2_selections()`
Extracts V2 API data from webhook interaction:

```python
@staticmethod
def extract_v2_selections(interaction_data: Dict) -> Dict:
    """Extract V2 API selections from interaction data.

    Handles both single selections (buttons) and multi-select (list).

    Args:
        interaction_data: Interactive component data from webhook

    Returns:
        Dict with extracted V2 data (presentation_id, modifier_selections, etc.)
    """
    result = {}

    # Check for list_reply
    if "list_reply" in interaction_data:
        list_reply = interaction_data["list_reply"]
        interaction_id = list_reply.get("id", "")

        # Extract presentation ID from size selection
        if interaction_id.startswith("size_pres"):
            presentation_id = extract_presentation_id(interaction_id)
            if presentation_id:
                result["presentation_id"] = presentation_id

        # Extract modifier selections
        elif interaction_id.startswith("mod_"):
            result["modifier_ids"] = [interaction_id]

    # Check for button_reply
    elif "button_reply" in interaction_data:
        button_reply = interaction_data["button_reply"]
        interaction_id = button_reply.get("id", "")

        # Extract presentation ID from size button
        if interaction_id.startswith("size_pres"):
            presentation_id = extract_presentation_id(interaction_id)
            if presentation_id:
                result["presentation_id"] = presentation_id

    return result
```

#### Enhanced `process_cart_interaction()` Function
Now extracts and merges V2 data into state updates:

```python
def process_cart_interaction(
    interaction_type: str,
    interaction_data: Dict,
    current_state: Optional[Dict] = None
) -> Tuple[str, Dict, str]:
    handler = CartInteractionHandler()

    # Parse interaction
    action_type, interaction_id, title = handler.parse_interaction(
        interaction_type, interaction_data
    )

    # Extract V2 API selections
    v2_data = handler.extract_v2_selections(interaction_data)
    logger.info(f"Extracted V2 data: {v2_data}")

    # Determine action
    node_name, state_updates = handler.determine_cart_action(interaction_id, current_stage)

    # Merge V2 data into state updates
    if v2_data:
        pending = current_state.get("pending_customization", {}) if current_state else {}

        # Add presentation ID if extracted
        if "presentation_id" in v2_data:
            pending["presentation_id"] = v2_data["presentation_id"]

        # Add modifier IDs if extracted
        if "modifier_ids" in v2_data:
            modifier_selections = extract_modifier_selections(v2_data["modifier_ids"])
            pending["modifier_selections"] = modifier_selections

        # Update state with pending customization
        if pending:
            state_updates["pending_customization"] = pending

    return node_name, state_updates, text_repr
```

---

## 🎯 What This Enables

### V2 API Pattern Recognition

**Presentation IDs (Sizes with API pricing)**
- ✅ Recognizes `size_pres001`, `size_pres002`, etc.
- ✅ Extracts presentation ID using `extract_presentation_id()`
- ✅ Stores in `pending_customization["presentation_id"]`

**Modifier Selections (API extras/toppings)**
- ✅ Recognizes `mod_mod001_opt001`, `mod_mod002_opt003`, etc.
- ✅ Extracts modifier selections using `extract_modifier_selections()`
- ✅ Stores in `pending_customization["modifier_selections"]`

**Product IDs (Direct from API)**
- ✅ Recognizes `prod_6748abc123`, `prod_6748abc456`, etc.
- ✅ Routes to `add_to_cart` node
- ✅ Passes menu_item_id to cart nodes

**Category IDs (Direct from API)**
- ✅ Recognizes `cat_6748abc123`, `cat_6748abc456`, etc.
- ✅ Routes to `view_category_carousel` node
- ✅ Passes category ID to display handler

### Backward Compatibility

**Legacy Patterns Still Work**
- ✅ `category_pizzas`, `category_burgers` (hardcoded categories)
- ✅ `pizzas_0`, `burgers_1` (hardcoded menu items)
- ✅ `size_small`, `size_medium`, `size_large` (multiplier-based sizing)
- ✅ `extra_cheese`, `mushrooms`, `olives` (hardcoded extras)

---

## 🔄 Data Flow

### Example: User Selects Size with V2 Presentation

1. **User clicks size button** → WhatsApp sends webhook
   ```json
   {
     "interactive": {
       "type": "button_reply",
       "button_reply": {
         "id": "size_pres002",
         "title": "Medium - $15.99"
       }
     }
   }
   ```

2. **cart_handler.py processes** → Extracts V2 data
   ```python
   v2_data = {
     "presentation_id": "pres002"
   }
   ```

3. **State updates with V2 data**
   ```python
   state_updates = {
     "pending_customization": {
       "presentation_id": "pres002"
     }
   }
   ```

4. **Cart node receives state** → Uses presentation ID
   ```python
   presentation_id = pending.get("presentation_id")  # "pres002"
   success, msg, item = await cart_service.add_item_to_cart(
       cart=cart,
       menu_item_id=menu_item_id,
       presentation_id=presentation_id,  # V2!
       quantity=1
   )
   ```

### Example: User Selects Modifiers with V2 API

1. **User selects modifiers** → WhatsApp sends webhook
   ```json
   {
     "interactive": {
       "type": "list_reply",
       "list_reply": {
         "id": "mod_mod001_opt001",
         "title": "Extra Cheese - $2.00"
       }
     }
   }
   ```

2. **cart_handler.py processes** → Extracts V2 data
   ```python
   v2_data = {
     "modifier_ids": ["mod_mod001_opt001"]
   }
   modifier_selections = extract_modifier_selections(v2_data["modifier_ids"])
   # Returns: {"mod001": ["opt001"]}
   ```

3. **State updates with V2 data**
   ```python
   state_updates = {
     "pending_customization": {
       "modifier_selections": {
         "mod001": ["opt001"]
       }
     }
   }
   ```

4. **Cart node receives state** → Uses modifier selections
   ```python
   modifier_selections = pending.get("modifier_selections")  # {"mod001": ["opt001"]}
   success, msg, item = await cart_service.add_item_to_cart(
       cart=cart,
       menu_item_id=menu_item_id,
       modifier_selections=modifier_selections,  # V2!
       quantity=1
   )
   ```

---

## 🧪 Testing

### Test V2 Presentation ID Recognition

```python
from ai_companion.interfaces.whatsapp.cart_handler import CartInteractionHandler

handler = CartInteractionHandler()

# Test presentation ID pattern
assert handler.is_cart_interaction("size_pres001") == True
assert handler.is_cart_interaction("size_pres002") == True

# Test extraction
interaction_data = {
    "button_reply": {
        "id": "size_pres002",
        "title": "Medium - $15.99"
    }
}
v2_data = handler.extract_v2_selections(interaction_data)
assert v2_data["presentation_id"] == "pres002"
```

### Test V2 Modifier Recognition

```python
# Test modifier pattern
assert handler.is_cart_interaction("mod_mod001_opt001") == True
assert handler.is_cart_interaction("mod_mod002_opt003") == True

# Test extraction
interaction_data = {
    "list_reply": {
        "id": "mod_mod001_opt001",
        "title": "Extra Cheese - $2.00"
    }
}
v2_data = handler.extract_v2_selections(interaction_data)
assert "modifier_ids" in v2_data
assert v2_data["modifier_ids"] == ["mod_mod001_opt001"]
```

### Test V2 Product/Category IDs

```python
# Test product ID pattern
assert handler.is_cart_interaction("prod_6748abc123") == True

# Test category ID pattern
assert handler.is_cart_interaction("cat_6748abc123") == True

# Test routing
node_name, state_updates = handler.determine_cart_action("prod_6748abc123")
assert node_name == "add_to_cart"
assert state_updates["current_item"]["menu_item_id"] == "prod_6748abc123"
```

### Test Legacy Pattern Compatibility

```python
# Test legacy patterns still work
assert handler.is_cart_interaction("category_pizzas") == True
assert handler.is_cart_interaction("pizzas_0") == True
assert handler.is_cart_interaction("size_small") == True
assert handler.is_cart_interaction("extra_cheese") == True
```

---

## 📊 Pattern Recognition Summary

| Pattern | Example | Type | Action | State Updates |
|---------|---------|------|--------|---------------|
| `cat_*` | `cat_6748abc123` | V2 Category | `view_category_carousel` | `selected_category_id` |
| `prod_*` | `prod_6748abc123` | V2 Product | `add_to_cart` | `current_item.menu_item_id` |
| `size_pres*` | `size_pres002` | V2 Presentation | `handle_size` | `pending_customization.presentation_id` |
| `mod_*` | `mod_mod001_opt001` | V2 Modifier | `handle_extras` | `pending_customization.modifier_selections` |
| `category_*` | `category_pizzas` | Legacy Category | `view_category_carousel` | `selected_category` |
| `*_[0-9]` | `pizzas_0` | Legacy Item | `add_to_cart` | `current_item.menu_item_id` |
| `size_*` | `size_medium` | Legacy Size | `handle_size` | (legacy size handling) |
| extras | `extra_cheese` | Legacy Extra | `handle_extras` | (legacy extras handling) |

---

## 🚀 Next Steps

### Completed ✅
- [x] Update cart_handler.py to recognize V2 patterns
- [x] Extract V2 presentation IDs from interactions
- [x] Extract V2 modifier selections from interactions
- [x] Merge V2 data into state updates
- [x] Maintain backward compatibility with legacy patterns

### Pending ⏳
- [ ] Update whatsapp_response.py to use V2 menu API
- [ ] Update carousel generation to use V2 API products
- [ ] Update category browsing to use V2 API categories
- [ ] Integration testing with real webhook data
- [ ] End-to-end testing with WhatsApp Business API

---

## ⚠️ Breaking Changes

**None!** All changes are backward compatible:
- ✅ Legacy patterns still recognized and routed correctly
- ✅ V2 patterns added alongside legacy patterns
- ✅ Automatic detection of V2 vs legacy based on ID format
- ✅ Graceful handling when V2 data not present

---

## 📚 Related Documentation

- [Async Migration Complete](./ASYNC_MIGRATION_COMPLETE.md) - Cart node async updates
- [Import Migration Status](./IMPORT_MIGRATION_STATUS.md) - Overall migration tracking
- [Phase 3 Implementation](./PHASE_3_IMPLEMENTATION.md) - Order API integration
- [V2 Quick Reference](./V2_QUICK_REFERENCE.md) - V2 usage examples

---

**Status:** ✅ **Webhook handlers updated to support V2 API responses!**

**Date:** 2025-12-04
