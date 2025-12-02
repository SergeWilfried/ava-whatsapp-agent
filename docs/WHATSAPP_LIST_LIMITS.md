# WhatsApp List Message Limits - Critical Information

## 🚨 Important Constraint

**WhatsApp List Messages have a limit of 10 rows TOTAL across ALL sections combined.**

This is a critical constraint from Meta's WhatsApp Cloud API that affects how you structure your menus.

## Official Limits

According to Meta's API specification:

- ✅ **Up to 10 sections** maximum
- ✅ **Up to 10 rows TOTAL** across all sections combined
- ✅ Each row title: **24 characters** maximum
- ✅ Each row description: **72 characters** maximum
- ✅ Section title: **24 characters** maximum

### Example: Valid List Message

```python
{
    "sections": [
        {
            "title": "Pizzas",
            "rows": [
                {"id": "pizza_0", "title": "Margherita", "description": "$12.99"},
                {"id": "pizza_1", "title": "Pepperoni", "description": "$14.99"},
                {"id": "pizza_2", "title": "BBQ Chicken", "description": "$15.99"}
            ]
        },
        {
            "title": "Burgers",
            "rows": [
                {"id": "burger_0", "title": "Classic", "description": "$9.99"},
                {"id": "burger_1", "title": "Cheeseburger", "description": "$10.99"}
            ]
        },
        {
            "title": "Sides",
            "rows": [
                {"id": "side_0", "title": "Fries", "description": "$3.99"},
                {"id": "side_1", "title": "Onion Rings", "description": "$4.49"},
                {"id": "side_2", "title": "Salad", "description": "$6.99"},
                {"id": "side_3", "title": "Wings", "description": "$8.99"}
            ]
        },
        {
            "title": "Drinks",
            "rows": [
                {"id": "drink_0", "title": "Coke", "description": "$2.50"}
            ]
        }
    ]
}
```

**Total rows: 3 + 2 + 4 + 1 = 10 ✅**

### Example: INVALID List Message

```python
{
    "sections": [
        {
            "title": "Pizzas",
            "rows": [
                # 5 pizza items
            ]
        },
        {
            "title": "Burgers",
            "rows": [
                # 4 burger items
            ]
        },
        {
            "title": "Sides",
            "rows": [
                # 6 side items
            ]
        }
    ]
}
```

**Total rows: 5 + 4 + 6 = 15 ❌ EXCEEDS LIMIT**

This will result in an API error from WhatsApp.

## How Our Implementation Handles This

### 1. Automatic Row Limiting

The `create_list_component()` function automatically enforces the 10-row limit:

```python
def create_list_component(body_text, sections, ...):
    formatted_sections = []
    total_rows = 0
    max_total_rows = 10  # WhatsApp's limit

    for section in sections[:10]:  # Max 10 sections
        if total_rows >= max_total_rows:
            break

        section_rows = section.get("rows", [])
        remaining_rows = max_total_rows - total_rows

        # Only add rows up to the remaining quota
        formatted_rows = [
            {...}
            for row in section_rows[:remaining_rows]
        ]

        if formatted_rows:
            formatted_sections.append({...})
            total_rows += len(formatted_rows)
```

### 2. Menu Handling Strategy

For restaurant menus with many items, we use two approaches:

#### Approach A: Truncated Full Menu (Default)

Show first 10 items across all categories:

```python
create_menu_list_from_restaurant_menu(RESTAURANT_MENU)
# Returns: 3 pizzas, 2 burgers, 3 sides, 2 drinks = 10 items total
```

**Pros:**
- Single interaction to see variety
- Good for small menus (<10 items)

**Cons:**
- Large menus get truncated
- Users might miss items

#### Approach B: Category-Based Navigation (Recommended for Large Menus)

1. Show category selection buttons first:
```python
create_category_menu_buttons(["pizzas", "burgers", "sides"])
# User taps "🍕 Pizzas"
```

2. Then show full category list:
```python
create_category_specific_menu("pizzas", pizza_items)
# Shows all pizzas (up to 10)
```

**Pros:**
- Users can see all items in each category
- Better for menus with >10 items
- More organized browsing experience

**Cons:**
- Requires extra tap (category → items)
- Slightly longer order flow

## Implementation Examples

### Example 1: Small Menu (≤10 items)

```python
SMALL_MENU = {
    "pizzas": [
        {"name": "Margherita", "price": 12.99, "description": "Classic"},
        {"name": "Pepperoni", "price": 14.99, "description": "Spicy"}
    ],
    "burgers": [
        {"name": "Classic", "price": 9.99, "description": "Beef patty"}
    ],
    "sides": [
        {"name": "Fries", "price": 3.99, "description": "Crispy"}
    ]
}

# Total: 2 + 1 + 1 = 4 items → Use direct menu
menu = create_menu_list_from_restaurant_menu(SMALL_MENU)
```

### Example 2: Large Menu (>10 items)

```python
LARGE_MENU = {
    "pizzas": [
        # 5 pizza items
    ],
    "burgers": [
        # 4 burger items
    ],
    "sides": [
        # 4 side items
    ],
    "drinks": [
        # 4 drink items
    ],
    "desserts": [
        # 3 dessert items
    ]
}

# Total: 5 + 4 + 4 + 4 + 3 = 20 items → Use category navigation

# Step 1: Show categories
categories = create_category_menu_buttons(["pizzas", "burgers", "sides"])

# Step 2: User taps "Pizzas" → Show pizza list
pizza_menu = create_category_specific_menu("pizzas", LARGE_MENU["pizzas"])
```

### Example 3: Dynamic Menu Selection

```python
def get_menu_for_user(menu: Dict) -> Dict:
    """Smart menu selection based on total items."""
    total_items = sum(len(items) for items in menu.values())

    if total_items <= 10:
        # Small menu: show everything in one list
        return create_menu_list_from_restaurant_menu(menu)
    else:
        # Large menu: show category buttons first
        return create_category_menu_buttons(list(menu.keys()))
```

## Testing Your Lists

### Quick Test Function

```python
def validate_list_message(sections: List[Dict]) -> Tuple[bool, str]:
    """Validate that list message complies with WhatsApp limits.

    Returns:
        (is_valid, message)
    """
    total_rows = sum(len(section.get("rows", [])) for section in sections)

    if total_rows > 10:
        return False, f"Too many rows: {total_rows} (max 10)"

    if len(sections) > 10:
        return False, f"Too many sections: {len(sections)} (max 10)"

    # Check row title lengths
    for section in sections:
        for row in section.get("rows", []):
            if len(row.get("title", "")) > 24:
                return False, f"Row title too long: '{row['title']}' (max 24 chars)"
            if len(row.get("description", "")) > 72:
                return False, f"Description too long (max 72 chars)"

    return True, "Valid list message"


# Usage
component = create_menu_list_from_restaurant_menu(RESTAURANT_MENU)
sections = component["action"]["sections"]
is_valid, message = validate_list_message(sections)
print(f"Valid: {is_valid} - {message}")
```

## Best Practices

### ✅ DO

1. **Count total rows** across all sections before sending
2. **Use category buttons** for menus with >10 items
3. **Prioritize popular items** when truncating
4. **Test with production data** to ensure limits aren't exceeded
5. **Monitor API errors** for limit violations

### ❌ DON'T

1. **Assume 10 rows per section** - it's 10 total!
2. **Hardcode large menus** into single lists
3. **Skip validation** - WhatsApp will reject invalid lists
4. **Ignore section limits** - max 10 sections
5. **Exceed character limits** - titles and descriptions have limits too

## API Error Messages

If you exceed limits, WhatsApp API returns:

```json
{
  "error": {
    "message": "Message failed to send because more than 10 rows were provided in the list message",
    "type": "OAuthException",
    "code": 100,
    "error_subcode": 2388091,
    "fbtrace_id": "..."
  }
}
```

## Workarounds for Large Menus

### Option 1: Multiple List Messages

Send category by category:

```
Bot: "What would you like?"
User: Taps "Pizzas"
Bot: [List with all pizzas]

User: "Show burgers"
Bot: [List with all burgers]
```

### Option 2: Paginated Lists

For categories with >10 items:

```
Bot: [Pizzas 1-10] + "See more..." button
User: Taps "See more"
Bot: [Pizzas 11-20]
```

### Option 3: Search/Filter

Add conversational search:

```
User: "Show me vegetarian pizzas"
Bot: [Filtered list with only vegetarian options]
```

### Option 4: Favorites/Recommendations

Prioritize based on popularity:

```
Bot: [10 most popular items across all categories]
     + "Browse by category" button
```

## Real-World Example: Your Restaurant Menu

Current menu from `core/schedules.py`:

```python
RESTAURANT_MENU = {
    "pizzas": [5 items],
    "burgers": [4 items],
    "sides": [4 items],
    "drinks": [4 items],
    "desserts": [3 items]
}
```

**Total: 20 items**

### Current Implementation

The `create_menu_list_from_restaurant_menu()` function will show:
- First 5 pizzas (all)
- First 4 burgers (all)
- First 1 side (truncated!)
- 0 drinks (truncated!)
- 0 desserts (truncated!)

**Total shown: 10 items**

### Recommended Solution

Use category navigation:

```python
# In your webhook handler
if user_wants_menu:
    # Show category buttons first
    component = create_category_menu_buttons(
        ["pizzas", "burgers", "sides", "drinks", "desserts"]
    )

elif user_selected_category:
    # Show items from selected category
    category = extract_category(user_message)
    items = RESTAURANT_MENU[category]
    component = create_category_specific_menu(category, items)
```

This way users can browse all 20 items without hitting the limit!

## Summary

- ✅ WhatsApp limit: **10 rows total** (not per section)
- ✅ Our code automatically enforces this limit
- ✅ For large menus (>10 items), use category navigation
- ✅ Always validate your lists before sending
- ✅ Test with production data to catch limit violations

## Quick Reference

| Component | Limit | Enforced By |
|-----------|-------|-------------|
| Total rows | 10 | `create_list_component()` |
| Sections | 10 | `create_list_component()` |
| Row title | 24 chars | `[:24]` truncation |
| Row description | 72 chars | `[:72]` truncation |
| Section title | 24 chars | `[:24]` truncation |
| Button text | 20 chars | `[:20]` truncation |

---

**Remember: It's 10 rows TOTAL, not 10 per section!**
