# Category Selection API Integration Fix

## Issue Identified

When the bot receives the first message and shows the menu categories, it was **always using mock data** instead of fetching categories from the CartaAI API, even when the API is enabled.

---

## Root Cause

In [whatsapp_response.py:177](../src/ai_companion/interfaces/whatsapp/whatsapp_response.py#L177), the `view_menu` handler was calling:

```python
interactive_comp = create_category_selection_list()  # No API categories passed!
```

The `create_category_selection_list()` function accepts an optional `categories` parameter:
- **With categories:** Uses API data
- **Without categories:** Falls back to hardcoded mock data

Since no categories were being passed, it always used mock data regardless of API configuration.

---

## Solution Applied

### 1. Import MenuAdapter

Added import to fetch menu data:

```python
from ai_companion.services.menu_adapter import MenuAdapter
```

### 2. Updated view_menu Handler

Modified the handler to fetch categories from API before creating the list:

```python
elif node_name == "view_menu":
    # User selected "View Menu" - show category selection
    # Fetch categories from API (or use mock data as fallback)
    menu_adapter = MenuAdapter()
    try:
        menu_structure = await menu_adapter.get_menu_structure()
        categories = menu_structure.get("categories", [])
        logger.info(f"Fetched {len(categories)} categories for menu display")
        interactive_comp = create_category_selection_list(categories)
    except Exception as e:
        logger.error(f"Error fetching menu structure: {e}, using mock data")
        interactive_comp = create_category_selection_list()

    success = await send_response(
        from_number,
        "Browse our menu by category:",
        "interactive_list",
        phone_number_id=phone_number_id,
        whatsapp_token=whatsapp_token,
        interactive_component=interactive_comp
    )
```

---

## How It Works Now

### API Enabled Flow

1. User sends first message or clicks "View Menu"
2. `view_menu` handler is triggered
3. MenuAdapter fetches menu structure from CartaAI API
4. API returns categories with structure:
   ```json
   {
     "categories": [
       {
         "id": "cat001",
         "name": "Burgers",
         "products": [...]
       },
       {
         "id": "cat002",
         "name": "Pizza",
         "products": [...]
       }
     ]
   }
   ```
5. Categories are passed to `create_category_selection_list(categories)`
6. List is generated with API category IDs like `cat_cat001`, `cat_cat002`
7. WhatsApp displays the list to user

### Mock Data Fallback Flow

If API is disabled or fails:

1. MenuAdapter returns mock menu structure
2. Mock categories are passed to `create_category_selection_list()`
3. List is generated with mock IDs like `cat_pizzas`, `cat_burgers`
4. Everything works as before with hardcoded data

---

## Expected Logs (API Enabled)

When working correctly with API enabled, you should see:

```
============================================================
MenuAdapter initialization check:
  use_cartaai_api: True
  menu_api_enabled: True
  ...
============================================================
🔵 Using API to get menu structure
INFO - CartaAI API session created
INFO - API Request [0/3]: GET https://ssgg.api.cartaai.pe/api/v1/menu2/bot-structure
INFO - API Response: 200 | Time: 0.345s
INFO - Fetched 5 categories for menu display
```

---

## Expected Logs (Mock Data Fallback)

When API is disabled or fails:

```
🟡 Using MOCK data to get menu structure
  Reason: use_cartaai_api=False, menu_api_enabled=False, menu_service=NOT SET
INFO - Fetched 5 categories for menu display
```

---

## Category ID Patterns

### API Categories
- Format: `cat_<api_category_id>`
- Example: `cat_cat001`, `cat_cat002`
- Generated from API response

### Mock Categories (Legacy)
- Format: `cat_<category_key>`
- Example: `cat_pizzas`, `cat_burgers`
- Hardcoded in `create_category_selection_list()`

Both patterns are recognized by `cart_handler.py` which strips the `cat_` prefix.

---

## Testing

### Test with API Enabled

1. Set environment variables in `.env`:
   ```bash
   USE_CARTAAI_API="true"
   CARTAAI_MENU_ENABLED="true"
   CARTAAI_SUBDOMAIN="your-subdomain"
   CARTAAI_API_KEY="your-api-key"
   ENABLE_API_LOGGING="true"
   ```

2. Restart application

3. Send a message to the bot or click "View Menu"

4. Check logs for:
   - "🔵 Using API to get menu structure"
   - "API Request [0/3]: GET https://..."
   - "Fetched X categories for menu display"

5. Verify WhatsApp shows categories from your CartaAI menu

### Test with Mock Data (Fallback)

1. Set in `.env`:
   ```bash
   USE_CARTAAI_API="false"
   ```

2. Restart application

3. Send a message to the bot

4. Check logs for:
   - "🟡 Using MOCK data to get menu structure"
   - "Fetched 5 categories for menu display"

5. Verify WhatsApp shows mock categories (Pizzas, Burgers, Sides, Drinks, Desserts)

---

## Files Modified

### src/ai_companion/interfaces/whatsapp/whatsapp_response.py

**Added import:**
```python
from ai_companion.services.menu_adapter import MenuAdapter
```

**Updated handler (lines 176-197):**
- Creates MenuAdapter instance
- Fetches menu structure with `await menu_adapter.get_menu_structure()`
- Extracts categories from response
- Passes categories to `create_category_selection_list(categories)`
- Gracefully falls back to mock data on error

---

## Related Documentation

- [CartaAI API Setup Guide](./CARTAAI_API_SETUP.md) - How to configure API
- [Webhook Handler V2 Update](./WEBHOOK_HANDLER_V2_UPDATE.md) - Cart handler V2 support
- [V2 Components Summary](./V2_COMPONENTS_SUMMARY.md) - Component features

---

## Summary

**Before:** Category selection always used mock data, API was never called

**After:** Category selection fetches from CartaAI API when enabled, falls back to mock data when disabled or on error

**Impact:** Users will now see real menu categories from the API instead of hardcoded mock categories

---

**Status:** ✅ **Fixed - Category selection now uses API data!**

**Date:** 2024-12-04
