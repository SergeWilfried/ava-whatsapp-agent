# Migration Plan: Mock Data to CartaAI Menu API

## Executive Summary

This document outlines the migration strategy from hardcoded mock restaurant data to the CartaAI Menu Management API. The migration will enable dynamic menu management, multi-location support, and real-time menu updates.

## Current State Analysis

### Mock Data Location
- **Primary file:** [src/ai_companion/core/schedules.py](../src/ai_companion/core/schedules.py)
- **Data structures:**
  - `RESTAURANT_MENU`: 20 items across 5 categories (pizzas, burgers, sides, drinks, desserts)
  - `BUSINESS_HOURS`: Store hours for each day
  - `RESTAURANT_INFO`: Basic restaurant details (name, contact, delivery info)
  - `SPECIAL_OFFERS`: Combo deals and daily specials

### Files Using Mock Data
1. [src/ai_companion/modules/cart/cart_service.py](../src/ai_companion/modules/cart/cart_service.py) - Menu item lookup and cart operations
2. [src/ai_companion/graph/nodes.py](../src/ai_companion/graph/nodes.py) - Conversation context injection
3. [src/ai_companion/graph/cart_nodes.py](../src/ai_companion/graph/cart_nodes.py) - Menu item search and customization
4. [src/ai_companion/modules/schedules/context_generation.py](../src/ai_companion/modules/schedules/context_generation.py) - Restaurant status and specials
5. [src/ai_companion/interfaces/whatsapp/carousel_components.py](../src/ai_companion/interfaces/whatsapp/carousel_components.py) - Menu display
6. [src/ai_companion/interfaces/whatsapp/image_utils.py](../src/ai_companion/interfaces/whatsapp/image_utils.py) - Menu item images

## Target API Overview

**Base URL:** `http://localhost:3001/api/v1`

### Key Endpoints to Implement

#### 1. Menu Structure Retrieval
- **Endpoint:** `GET /menu2/bot-structure`
- **Parameters:** `subDomain`, `localId` (optional)
- **Use case:** Primary endpoint for WhatsApp bot menu display
- **Returns:** Hierarchical menu structure (categories → products)

#### 2. Product Details
- **Endpoint:** `POST /menu/getProductInMenu/{localId}/{subDomain}`
- **Use case:** Get detailed product info including presentations, modifiers, options
- **Returns:** Full product details with customization options

#### 3. Menu Integration
- **Endpoint:** `GET /menu2/integration/{subDomain}/{businessLocationId}`
- **Use case:** Complete menu data for specific location
- **Returns:** All categories, products, modifiers

## Data Model Mapping

### Current Mock Structure → API Response

| Mock Data | API Equivalent | API Endpoint |
|-----------|----------------|--------------|
| `RESTAURANT_MENU[category][item]` | `BotStructureResponse.data.categories[].products[]` | `/menu2/bot-structure` |
| `item["name"]` | `product.name` | Same |
| `item["price"]` | `product.price` | Same |
| `item["description"]` | `product.description` | Same |
| `category` key | `category.name` | Same |
| N/A | `product._id` | New field (API ID) |
| N/A | `product.presentations[]` | New (size variations) |
| N/A | `product.modifiers[]` | New (customization options) |
| Hardcoded sizes | `presentations[].price` | `/menu/getProductInMenu` |
| `EXTRAS_PRICING` dict | `modifiers[].options[].price` | `/menu/getProductInMenu` |

### New Capabilities from API

1. **Multi-location support:** Different menus per location
2. **Dynamic pricing:** Real-time price updates
3. **Product presentations:** Multiple size/variant options per product
4. **Structured modifiers:** Min/max selections, grouped options
5. **Availability:** `isActive` status per location
6. **Images:** Product and category images from API

## Migration Architecture

### Phase 1: API Client Layer

Create a new service module: `src/ai_companion/services/cartaai/`

```
src/ai_companion/services/cartaai/
├── __init__.py
├── client.py           # HTTP client for CartaAI API
├── models.py           # Pydantic models matching OpenAPI schemas
├── menu_service.py     # High-level menu operations
└── cache.py            # Caching layer for API responses
```

**Key Components:**

1. **CartaAIClient** (`client.py`)
   - Handles authentication (Bearer token)
   - HTTP request/response management
   - Error handling and retries
   - Rate limiting

2. **Data Models** (`models.py`)
   - `Product`: Full product details
   - `Category`: Category with products
   - `Modifier`: Customization group
   - `ModifierOption`: Individual customization option
   - `BotStructure`: Complete bot menu structure
   - `ProductInMenu`: Detailed product view

3. **MenuService** (`menu_service.py`)
   - High-level operations (get_menu, find_product, search_products)
   - Data transformation (API format → app format)
   - Backward compatibility layer

4. **CacheManager** (`cache.py`)
   - In-memory caching with TTL
   - Cache invalidation strategies
   - Optional Redis support for production

### Phase 2: Configuration

Add to `src/ai_companion/core/config.py`:

```python
class CartaAISettings:
    api_base_url: str = "https://ssgg.api.cartaai.pe/api/v1"
    api_token: str  # From environment variable
    subdomain: str  # Restaurant subdomain
    local_id: Optional[str] = None  # Branch/location ID
    cache_ttl: int = 300  # 5 minutes
    enable_cache: bool = True
```

**Environment variables:**
- `CARTAAI_API_TOKEN`: JWT Bearer token
- `CARTAAI_SUBDOMAIN`: Restaurant subdomain
- `CARTAAI_LOCAL_ID`: Location identifier (optional)

### Phase 3: Service Layer Refactoring

#### 3.1 Update CartService

Modify [cart_service.py](../src/ai_companion/modules/cart/cart_service.py):

**Before:**
```python
from ai_companion.core.schedules import RESTAURANT_MENU

def find_menu_item(self, menu_item_id: str) -> Optional[Dict]:
    parts = menu_item_id.split("_")
    category = parts[0]
    index = int(parts[1])
    item = RESTAURANT_MENU[category][index]
```

**After:**
```python
from ai_companion.services.cartaai.menu_service import MenuService

def find_menu_item(self, product_id: str) -> Optional[Dict]:
    return self.menu_service.get_product_details(product_id)
```

#### 3.2 Update Graph Nodes

Modify [graph/nodes.py](../src/ai_companion/graph/nodes.py):

- Replace direct imports from `schedules.py`
- Inject menu data via MenuService
- Update prompt generation with dynamic menu data

#### 3.3 Update Context Generation

Modify [modules/schedules/context_generation.py](../src/ai_companion/modules/schedules/context_generation.py):

- Fetch menu structure from API
- Generate context from live data
- Maintain same output format for compatibility

### Phase 4: Customization Migration

**Current System:**
- Hardcoded `SIZE_MULTIPLIERS` and `EXTRAS_PRICING` in CartService
- Manual price calculation

**New System:**
- Use API's `presentations[]` for size variations
- Use API's `modifiers[].options[]` for extras
- Prices come directly from API

**Migration steps:**
1. Map current size names to API presentation names
2. Replace `EXTRAS_PRICING` with modifier option lookup
3. Update price calculation to use API values
4. Handle min/max selections from modifier rules

### Phase 5: Image Management

**Current System:**
- Static Unsplash URLs in `image_utils.py`
- Hardcoded mappings

**New System:**
- Product images from API (`product.imageUrl`)
- Category images from API
- Fallback to current Unsplash images if API has no image
- Upload endpoint: `POST /menu-pic` for custom images

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Scope:** API client and models

- [ ] Create `services/cartaai/` module structure
- [ ] Implement `CartaAIClient` with authentication
- [ ] Define Pydantic models matching OpenAPI schemas
- [ ] Add configuration settings
- [ ] Write unit tests for client
- [ ] Test against CartaAI API staging environment

**Deliverables:**
- Working API client
- Complete data models
- Unit tests with 80%+ coverage

### Phase 2: Service Layer (Week 2)
**Scope:** MenuService and caching

- [ ] Implement `MenuService` class
- [ ] Add caching layer (in-memory + optional Redis)
- [ ] Create backward compatibility adapter
- [ ] Implement data transformation utilities
- [ ] Add comprehensive error handling
- [ ] Write integration tests

**Deliverables:**
- MenuService with full CRUD operations
- Cache implementation with TTL
- Integration test suite

### Phase 3: Cart Integration (Week 3)
**Scope:** Update CartService

- [ ] Refactor `cart_service.py` to use MenuService
- [ ] Update `find_menu_item()` method
- [ ] Migrate customization pricing to API data
- [ ] Update cart item validation
- [ ] Add presentation/modifier support
- [ ] Update tests

**Deliverables:**
- Refactored CartService
- Updated cart functionality
- Passing test suite

### Phase 4: Graph & Context (Week 4)
**Scope:** Update graph nodes and context generation

- [ ] Update `graph/nodes.py` menu injection
- [ ] Refactor `graph/cart_nodes.py`
- [ ] Update `context_generation.py`
- [ ] Migrate prompt templates
- [ ] Update WhatsApp carousel components
- [ ] End-to-end testing

**Deliverables:**
- Fully integrated graph system
- Updated context generation
- E2E test scenarios

### Phase 5: Images & Polish (Week 5)
**Scope:** Image handling and final touches

- [ ] Integrate API product images
- [ ] Update `image_utils.py` with fallbacks
- [ ] Add image upload support
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] Production deployment prep

**Deliverables:**
- Complete image integration
- Performance benchmarks
- Deployment guide

## Backward Compatibility Strategy

### Dual-Mode Operation

Support both mock and API modes during transition:

```python
class MenuProvider:
    def __init__(self, mode: str = "api"):
        self.mode = mode  # "mock" or "api"

    def get_menu(self):
        if self.mode == "mock":
            return self._get_mock_menu()
        else:
            return self._get_api_menu()
```

**Configuration flag:**
```python
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
```

### Data Adapter Pattern

Create adapter to maintain current interfaces:

```python
class MenuAdapter:
    """Adapts API responses to mock data format."""

    @staticmethod
    def api_to_mock_format(api_product: Product) -> Dict:
        """Convert API product to mock menu item format."""
        return {
            "name": api_product.name,
            "price": api_product.price,
            "description": api_product.description,
        }
```

## Risk Mitigation

### Risk 1: API Availability
**Impact:** High
**Mitigation:**
- Implement robust caching (5-15 min TTL)
- Fallback to last cached data if API down
- Health check endpoint monitoring
- Circuit breaker pattern for API calls

### Risk 2: Data Format Mismatches
**Impact:** Medium
**Mitigation:**
- Strong typing with Pydantic models
- Comprehensive validation
- Unit tests for all transformations
- Schema version checking

### Risk 3: Performance Degradation
**Impact:** Medium
**Mitigation:**
- Aggressive caching strategy
- Async API calls where possible
- Connection pooling
- Load testing before production

### Risk 4: Authentication Issues
**Impact:** High
**Mitigation:**
- Token refresh mechanism
- Secure token storage
- Multiple auth fallback strategies
- Monitoring and alerting

## Testing Strategy

### Unit Tests
- API client methods
- Data model validation
- Cache operations
- Data transformations

### Integration Tests
- End-to-end API calls
- Cache integration
- Service layer operations
- Error handling scenarios

### E2E Tests
- Complete cart flow with API data
- WhatsApp conversation with menu
- Order placement with API products
- Multi-location scenarios

### Load Tests
- API call performance
- Cache effectiveness
- Concurrent user scenarios
- Peak load handling

## Rollback Plan

If critical issues arise:

1. **Immediate:** Set `USE_MOCK_DATA=true` environment variable
2. **Short-term:** Deploy previous version from git
3. **Investigation:** Analyze logs and error reports
4. **Fix:** Address issues in development environment
5. **Gradual rollout:** Canary deployment to subset of users

## Monitoring & Observability

### Metrics to Track
- API response times (p50, p95, p99)
- Cache hit/miss rates
- API error rates by endpoint
- Menu data freshness
- Cart conversion rates

### Logging
- API request/response logs
- Cache operations
- Error traces with context
- Performance bottlenecks

### Alerts
- API downtime > 1 minute
- Error rate > 5%
- Response time > 2 seconds
- Cache failures

## Success Criteria

### Technical
- [ ] All 6 modules using mock data migrated to API
- [ ] Cache hit rate > 80%
- [ ] API response time < 500ms (p95)
- [ ] Zero data loss in cart operations
- [ ] 100% test coverage for new code

### Business
- [ ] Support multiple restaurant locations
- [ ] Real-time menu updates (< 5 min)
- [ ] No user-facing disruption during migration
- [ ] Improved menu management workflows
- [ ] Reduced manual menu update time

## Post-Migration Tasks

1. **Remove mock data:**
   - Delete or archive `RESTAURANT_MENU` from [schedules.py](../src/ai_companion/core/schedules.py)
   - Remove `image_utils.py` mappings
   - Clean up example files

2. **Documentation:**
   - Update README with API configuration
   - Document environment variables
   - Create API troubleshooting guide
   - Update architecture diagrams

3. **Optimization:**
   - Analyze cache patterns
   - Optimize API call frequency
   - Implement predictive prefetching
   - Add Redis for distributed caching

4. **Feature expansion:**
   - Menu image parsing integration
   - Excel import for bulk updates
   - Multi-language menu support
   - Dynamic pricing/promotions

## Appendix A: API Response Examples

### Bot Structure Response
```json
{
  "type": "1",
  "message": "Success",
  "data": {
    "categories": [
      {
        "id": "cat123",
        "name": "Pizzas",
        "products": [
          {
            "id": "prod456",
            "name": "Margherita Pizza",
            "price": 12.99,
            "description": "Classic tomato sauce, fresh mozzarella, basil",
            "imageUrl": "https://example.com/margherita.jpg",
            "isActive": true
          }
        ]
      }
    ]
  }
}
```

### Product Details Response
```json
{
  "success": true,
  "message": "Product details retrieved successfully",
  "data": [
    {
      "_id": "prod456",
      "name": "Margherita Pizza",
      "description": "Classic tomato sauce, fresh mozzarella, basil",
      "price": 12.99,
      "categoryId": "cat123",
      "category": {
        "_id": "cat123",
        "name": "Pizzas",
        "position": 1
      },
      "presentations": [
        {"_id": "pres1", "name": "Small", "price": 10.99},
        {"_id": "pres2", "name": "Medium", "price": 12.99},
        {"_id": "pres3", "name": "Large", "price": 15.99}
      ],
      "modifiers": [
        {
          "_id": "mod1",
          "name": "Extra Toppings",
          "minSelections": 0,
          "maxSelections": 5,
          "options": [
            {"_id": "opt1", "name": "Extra Cheese", "price": 2.00},
            {"_id": "opt2", "name": "Mushrooms", "price": 1.50}
          ]
        }
      ]
    }
  ]
}
```

## Appendix B: Environment Configuration

### Development `.env`
```bash
# CartaAI API Configuration
CARTAAI_API_TOKEN=your_dev_token_here
CARTAAI_SUBDOMAIN=dev-restaurant
CARTAAI_LOCAL_ID=loc001
CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe/api/v1
CARTAAI_CACHE_TTL=300
CARTAAI_ENABLE_CACHE=true

# Feature Flags
USE_MOCK_DATA=false
ENABLE_API_LOGGING=true
```

### Production `.env`
```bash
# CartaAI API Configuration
CARTAAI_API_TOKEN=${SECRET_API_TOKEN}
CARTAAI_SUBDOMAIN=restaurant-prod
CARTAAI_LOCAL_ID=main-location
CARTAAI_API_BASE_URL=https://ssgg.api.cartaai.pe/api/v1
CARTAAI_CACHE_TTL=600
CARTAAI_ENABLE_CACHE=true

# Feature Flags
USE_MOCK_DATA=false
ENABLE_API_LOGGING=false
```

## Appendix C: Code Examples

### Example: MenuService Usage

```python
from ai_companion.services.cartaai.menu_service import MenuService

# Initialize service
menu_service = MenuService()

# Get complete menu for bot
menu = await menu_service.get_bot_structure(
    subdomain="restaurant",
    local_id="loc001"
)

# Find specific product
product = await menu_service.get_product_details(
    product_id="prod456",
    subdomain="restaurant",
    local_id="loc001"
)

# Search products by name
results = await menu_service.search_products(
    query="margherita",
    category="pizzas"
)
```

### Example: Cart Integration

```python
from ai_companion.modules.cart.cart_service import CartService

cart_service = CartService()
cart = cart_service.create_cart()

# Add item with API product ID
success, message, cart_item = cart_service.add_item_to_cart(
    cart=cart,
    product_id="prod456",  # API product ID instead of "pizzas_0"
    quantity=1,
    presentation_id="pres2",  # Medium size
    modifier_selections={
        "mod1": ["opt1", "opt2"]  # Extra cheese + mushrooms
    }
)
```

## Questions & Clarifications Needed

Before starting implementation, please clarify:

1. **API Access:**
   - Do we have API credentials for development/staging?
   - What are rate limits for the API?
   - Is there a sandbox environment?

2. **Business Logic:**
   - Should we maintain backward compatibility with mock data?
   - How long should we cache menu data?
   - How to handle multi-location scenarios?

3. **Data:**
   - Which `subDomain` and `localId` should we use?
   - Are there test accounts available?
   - How often does menu data change?

4. **Timeline:**
   - What's the target completion date?
   - Are there any hard deadlines?
   - Phased rollout vs big bang deployment?

---

**Document Version:** 1.0
**Last Updated:** 2025-12-03
**Author:** Claude Code
**Status:** Draft - Pending Review
