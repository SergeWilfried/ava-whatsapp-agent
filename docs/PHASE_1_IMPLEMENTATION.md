## Phase 1 Implementation: Menu Structure API Integration

## ✅ Implementation Complete

**Status:** ✅ Complete
**Date:** 2025-12-04
**Duration:** 1 day

---

## 📦 Components Implemented

### 1. Product ID Mapper ✅

**File:** [src/ai_companion/services/cartaai/product_mapper.py](../src/ai_companion/services/cartaai/product_mapper.py)

**Purpose:** Bidirectional mapping between legacy IDs (`"pizzas_0"`) and API IDs (`"prod001"`)

**Features:**
- ✅ Legacy ID → API ID mapping
- ✅ API ID → Legacy ID reverse mapping
- ✅ Category ID mapping
- ✅ Automatic mapping generation from menu structures
- ✅ Name-based product matching
- ✅ Global singleton pattern

**Usage:**
```python
from ai_companion.services.cartaai.product_mapper import get_product_mapper

mapper = get_product_mapper()
mapper.build_from_menu_structure(api_menu, legacy_menu)

# Legacy to API
api_id = mapper.get_api_id("pizzas_0")  # → "prod001"

# API to Legacy
legacy_id = mapper.get_legacy_id("prod001")  # → "pizzas_0"
```

### 2. Configuration System ✅

**File:** [src/ai_companion/core/config.py](../src/ai_companion/core/config.py)

**Features:**
- ✅ Feature flags for gradual rollout
- ✅ Environment variable configuration
- ✅ Performance settings
- ✅ Validation

**Feature Flags:**
```bash
# Master switch
USE_CARTAAI_API=true              # Enable API integration

# Individual features
CARTAAI_MENU_ENABLED=true         # Menu API
CARTAAI_ORDERS_ENABLED=false      # Orders API (Phase 3)
CARTAAI_DELIVERY_ENABLED=false    # Delivery API (Phase 4)
```

**Configuration:**
```python
from ai_companion.core.config import get_cartaai_config

config = get_cartaai_config()
if config.use_cartaai_api and config.menu_api_enabled:
    # Use API
else:
    # Use mock data
```

### 3. Menu Adapter ✅

**File:** [src/ai_companion/services/menu_adapter.py](../src/ai_companion/services/menu_adapter.py)

**Purpose:** Unified interface for menu data with automatic API/mock fallback

**Features:**
- ✅ Seamless API/mock data switching
- ✅ Automatic ID mapping
- ✅ Product search
- ✅ Error handling with fallback
- ✅ Singleton pattern
- ✅ Legacy format compatibility

**Usage:**
```python
from ai_companion.services.menu_adapter import get_menu_adapter

adapter = get_menu_adapter()

# Works with both legacy and API IDs
item = await adapter.find_menu_item("pizzas_0")

# Search products
results = await adapter.search_products("burger")

# Get menu structure
menu = await adapter.get_menu_structure()
```

### 4. Updated CartService ✅

**File:** [src/ai_companion/modules/cart/cart_service_v2.py](../src/ai_companion/modules/cart/cart_service_v2.py)

**Features:**
- ✅ Async `find_menu_item()` method
- ✅ Sync fallback for backward compatibility
- ✅ API presentation pricing support
- ✅ API modifier pricing support
- ✅ Automatic price calculation
- ✅ Maintains existing interface

**Changes from Original:**
- `find_menu_item()` is now async (uses MenuAdapter)
- Added `find_menu_item_sync()` for backward compatibility
- `add_item_to_cart()` now async
- Supports both legacy and API pricing
- Added `presentation_id` and `modifier_selections` parameters

**Migration:**
```python
# Old (sync)
item = cart_service.find_menu_item("pizzas_0")

# New (async - preferred)
item = await cart_service.find_menu_item("pizzas_0")

# New (sync - backward compatible)
item = cart_service.find_menu_item_sync("pizzas_0")
```

### 5. Test Suite ✅

**Files:**
- [tests/services/cartaai/test_product_mapper.py](../tests/services/cartaai/test_product_mapper.py) - 12 tests
- [tests/services/test_menu_adapter.py](../tests/services/test_menu_adapter.py) - 11 tests

**Total:** 23 new test cases

---

## 📂 File Structure

```
src/ai_companion/
├── core/
│   └── config.py                    # NEW: Configuration with feature flags
├── services/
│   ├── cartaai/
│   │   └── product_mapper.py        # NEW: ID mapping
│   └── menu_adapter.py              # NEW: Unified menu interface
└── modules/cart/
    ├── cart_service.py              # EXISTING: Original service
    └── cart_service_v2.py           # NEW: Updated with API support

tests/
├── services/
│   ├── cartaai/
│   │   └── test_product_mapper.py   # NEW: Mapper tests
│   └── test_menu_adapter.py         # NEW: Adapter tests
```

---

## 🔄 Migration Path

### Option 1: Gradual Migration (Recommended)

Keep both versions, gradually migrate code:

```python
# In new code, use v2
from ai_companion.modules.cart.cart_service_v2 import get_cart_service

cart_service = get_cart_service()
item = await cart_service.find_menu_item("pizzas_0")
```

### Option 2: Direct Replacement

Replace original CartService:
```bash
# Backup original
mv src/ai_companion/modules/cart/cart_service.py \
   src/ai_companion/modules/cart/cart_service_old.py

# Use v2 as main
mv src/ai_companion/modules/cart/cart_service_v2.py \
   src/ai_companion/modules/cart/cart_service.py
```

---

## 🚀 Enabling API Integration

### Step 1: Set Environment Variables

```bash
# .env file
CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe/api/v1
CARTAAI_SUBDOMAIN=your-restaurant
CARTAAI_LOCAL_ID=branch-01
CARTAAI_API_KEY=your_api_key

# Enable API (start with menu only)
USE_CARTAAI_API=true
CARTAAI_MENU_ENABLED=true
CARTAAI_ORDERS_ENABLED=false
CARTAAI_DELIVERY_ENABLED=false

# Performance
CARTAAI_CACHE_TTL=900
ENABLE_API_LOGGING=true
```

### Step 2: Initialize on Startup

```python
from ai_companion.services.menu_adapter import initialize_menu_adapter

# In your app startup
async def startup():
    await initialize_menu_adapter()
    logger.info("Menu adapter initialized")
```

### Step 3: Test

```python
from ai_companion.services.menu_adapter import get_menu_adapter

async def test_api():
    adapter = get_menu_adapter()

    # Should use API if enabled
    menu = await adapter.get_menu_structure()
    print(f"Categories: {len(menu['data']['categories'])}")
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all Phase 1 tests
pytest tests/services/cartaai/test_product_mapper.py -v
pytest tests/services/test_menu_adapter.py -v

# With coverage
pytest tests/services/ --cov=ai_companion.services --cov-report=html
```

### Manual Testing

```python
import asyncio
from ai_companion.services.menu_adapter import get_menu_adapter

async def test():
    adapter = get_menu_adapter()

    # Test menu fetch
    menu = await adapter.get_menu_structure()
    print(f"✓ Menu: {len(menu['data']['categories'])} categories")

    # Test product lookup
    item = await adapter.find_menu_item("pizzas_0")
    print(f"✓ Item: {item['name']} - ${item['price']}")

    # Test search
    results = await adapter.search_products("burger")
    print(f"✓ Search: {len(results)} burgers found")

asyncio.run(test())
```

---

## 🔀 Data Flow

### Before (Mock Data):
```
CartService.find_menu_item()
    ↓
RESTAURANT_MENU[category][index]
    ↓
Return menu item dict
```

### After (With API):
```
CartService.find_menu_item()
    ↓
MenuAdapter.find_menu_item()
    ↓
Check feature flags
    ↓
[API Enabled] → MenuService.get_product_by_id()
    │             ↓
    │          ProductIDMapper (map legacy ID)
    │             ↓
    │          CartaAIClient.get_product_details()
    │             ↓
    │          Convert API format → legacy format
    │
[API Disabled] → Mock RESTAURANT_MENU lookup
    ↓
Return menu item dict (compatible format)
```

---

## ✅ Backward Compatibility

### Interface Compatibility

All existing code continues to work:

| Original | v2 | Compatible? |
|----------|-----|-------------|
| `find_menu_item("pizzas_0")` | `find_menu_item_sync("pizzas_0")` | ✅ Yes |
| `add_item_to_cart(...)` | `await add_item_to_cart(...)` | ⚠️ Needs async |
| `create_cart()` | `create_cart()` | ✅ Yes |
| `get_cart_summary()` | `get_cart_summary()` | ✅ Yes |

### Data Format Compatibility

API products are converted to legacy format:

```python
# API Format (internal)
{
    "_id": "prod001",
    "name": "Classic Burger",
    "price": 15.99,
    "presentations": [...],
    "modifiers": [...]
}

# Legacy Format (returned)
{
    "id": "pizzas_0",
    "api_id": "prod001",  # NEW: for reference
    "name": "Classic Burger",
    "price": 15.99,
    "description": "...",
    "category": "burgers",
    "is_available": True,
    "presentations": [...],  # NEW: API data
    "modifiers": [...]       # NEW: API data
}
```

---

## 📊 Feature Flags Strategy

### Rollout Plan

**Week 1: Internal Testing**
```bash
USE_CARTAAI_API=true
CARTAAI_MENU_ENABLED=true
# Test with development team
```

**Week 2: Beta Testing**
```bash
# Enable for 10% of users (A/B test)
# Monitor error rates
```

**Week 3: Gradual Rollout**
```bash
# 25% → 50% → 75% → 100%
# Monitor performance metrics
```

### Rollback

If issues occur:
```bash
# Instant rollback (no deployment needed)
USE_CARTAAI_API=false

# Or keep API but disable menu
CARTAAI_MENU_ENABLED=false
```

---

## 🐛 Known Limitations

1. **Async Migration:** New `find_menu_item()` is async. Use `find_menu_item_sync()` for backward compatibility (creates event loop internally).

2. **ID Format:** Legacy IDs must still be used in existing code. Mapper handles conversion automatically.

3. **Pricing Logic:** Falls back to `SIZE_MULTIPLIERS` if API doesn't provide presentation pricing.

4. **Order Persistence:** Still uses JSON files. API order creation in Phase 3.

---

## 📈 Performance Expectations

| Metric | Mock (Before) | API (After) | Notes |
|--------|--------------|-------------|-------|
| Menu lookup | <1ms | 10-300ms | Cached: ~10ms, API: ~300ms |
| First load | <1ms | 300-500ms | Cache miss |
| Subsequent loads | <1ms | 5-10ms | Cache hit |
| Search | <1ms | 5-10ms | Cached |

**Optimization:** Menu is cached for 15 minutes, so most requests hit cache.

---

## 🎯 Phase 1 Achievements

- ✅ Product ID mapping system
- ✅ Feature flag configuration
- ✅ Menu adapter with API integration
- ✅ Updated CartService (v2)
- ✅ Backward compatibility maintained
- ✅ Comprehensive test coverage
- ✅ Graceful fallback to mock data
- ✅ ID format conversion
- ✅ API/mock data format unification

---

## 🚀 Next Steps (Phase 2)

**Phase 2: Product Details & Modifiers**

1. Update interactive components
   - `create_size_selection_buttons()` → use API presentations
   - `create_extras_list()` → use API modifiers

2. Test presentation pricing
   - Replace `SIZE_MULTIPLIERS` with API prices

3. Test modifier pricing
   - Replace `EXTRAS_PRICING` with API prices

4. Integration testing
   - Full order flow with API data

**Target Duration:** 2-3 days

---

## 📝 Migration Checklist

**Pre-Migration:**
- [ ] Set up API credentials
- [ ] Configure environment variables
- [ ] Test API connection
- [ ] Review feature flags

**Migration:**
- [ ] Deploy new code (v2 services)
- [ ] Enable `USE_CARTAAI_API=true` for test users
- [ ] Monitor logs for errors
- [ ] Check menu loads correctly

**Post-Migration:**
- [ ] Verify product lookups work
- [ ] Test search functionality
- [ ] Check pricing calculations
- [ ] Monitor cache hit rates
- [ ] Gradual rollout to all users

---

## 📞 Support

**Issues:** Check logs for errors
**Rollback:** Set `USE_CARTAAI_API=false`
**Questions:** See [COMPREHENSIVE_MIGRATION_PLAN.md](./COMPREHENSIVE_MIGRATION_PLAN.md)

---

**Phase 1 Status:** ✅ **COMPLETE AND TESTED**

Next: [Phase 2 - Product Details & Modifiers](./COMPREHENSIVE_MIGRATION_PLAN.md#phase-2-product-details-api-2-3-days)
