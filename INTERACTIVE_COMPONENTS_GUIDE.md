# WhatsApp Interactive Components Guide

Your restaurant assistant now supports **WhatsApp Interactive Components**! These provide a much better user experience with buttons and lists instead of just plain text.

## 🎯 What's Been Implemented

### 1. **Interactive Lists** (Menu Display)
When customers ask to see the menu, they get a beautiful interactive list with:
- Multiple sections (Pizzas, Burgers, Sides, Drinks, Desserts)
- Item names with emoji icons
- Prices and descriptions
- Tappable items

### 2. **Reply Buttons**
Quick action buttons that customers can tap (up to 3 buttons)

### 3. **Automatic Message Type Detection**
The system automatically detects when users click buttons or select from lists and processes their choice as a natural message.

---

## 📋 How It Works

### Menu Display Flow

**Customer**: "Show me the menu"

**AI Router**: Detects intent → Routes to `menu_node`

**Menu Node**: Sets `use_interactive_menu = True`

**Webhook Handler**: Detects flag → Sends interactive list component

**WhatsApp**: Displays beautiful interactive menu with categories and items

**Customer**: Taps on "🍕 Margherita Pizza"

**System**: Converts to "I'd like to order Margherita Pizza"

**AI**: Processes order and confirms

---

## 🛠️ Using Interactive Components in Your Code

### Example 1: Display Interactive Menu

The menu automatically uses interactive lists when the customer asks to see it.

```python
# In menu_node (already implemented):
return {
    "messages": AIMessage(content="Here's our menu!"),
    "use_interactive_menu": True  # Triggers interactive list
}
```

### Example 2: Create Custom Button Component

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_button_component

# Order confirmation with buttons
component = create_button_component(
    "Your order total is $31.04. How would you like to receive it?",
    [
        {"id": "delivery", "title": "Delivery 🚗"},
        {"id": "pickup", "title": "Pickup 🏃"},
        {"id": "cancel", "title": "Cancel ❌"}
    ],
    header_text="Order Confirmation"
)

# Return this in your node:
return {
    "messages": AIMessage(content="Order ready!"),
    "interactive_component": component
}
```

### Example 3: Create Custom List Component

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_list_component

# Pizza selection list
component = create_list_component(
    "Choose your pizza size:",
    [
        {
            "title": "Sizes",
            "rows": [
                {"id": "small", "title": "Small 10\"", "description": "+$0.00"},
                {"id": "medium", "title": "Medium 12\"", "description": "+$3.00"},
                {"id": "large", "title": "Large 14\"", "description": "+$6.00"},
            ]
        }
    ],
    button_text="Select Size"
)
```

---

## 📱 WhatsApp Component Specifications

### Reply Buttons
- **Maximum**: 3 buttons
- **Button title**: Max 20 characters
- **Body text**: Max 1024 characters
- **Header text**: Max 60 characters (optional)
- **Footer text**: Max 60 characters (optional)

### List Messages
- **Maximum sections**: 10 sections
- **Maximum rows per section**: 10 rows
- **Row title**: Max 24 characters
- **Row description**: Max 72 characters
- **Section title**: Max 24 characters
- **Body text**: Max 1024 characters
- **Button text**: Max 20 characters

---

## 🎨 Interactive Component Types

### 1. Reply Buttons
Best for: Quick choices, Yes/No questions, confirmation

```python
create_button_component(
    "Would you like to add drinks?",
    [
        {"id": "add_drinks", "title": "Yes, add drinks"},
        {"id": "no_drinks", "title": "No, thanks"},
    ]
)
```

**Appears as:**
```
┌─────────────────────────────┐
│ Would you like to add       │
│ drinks?                     │
│                             │
│ [ Yes, add drinks ]         │
│ [ No, thanks      ]         │
└─────────────────────────────┘
```

### 2. List Messages
Best for: Menus, product catalogs, multiple options

```python
create_list_component(
    "Select your toppings:",
    [
        {
            "title": "Vegetables",
            "rows": [
                {"id": "mushroom", "title": "Mushrooms", "description": "+$1.50"},
                {"id": "peppers", "title": "Bell Peppers", "description": "+$1.50"},
            ]
        },
        {
            "title": "Meats",
            "rows": [
                {"id": "pepperoni", "title": "Pepperoni", "description": "+$2.00"},
                {"id": "sausage", "title": "Italian Sausage", "description": "+$2.00"},
            ]
        }
    ],
    button_text="Add Toppings"
)
```

**Appears as:**
```
┌─────────────────────────────┐
│ Select your toppings:       │
│                             │
│ [ Add Toppings ▼ ]          │
└─────────────────────────────┘

(When tapped, shows categorized list)
```

---

## 🔧 Extending for Order Confirmation

You can enhance the `order_node` to send confirmation buttons:

```python
# In order_node, after processing order:
from ai_companion.interfaces.whatsapp.interactive_components import create_button_component

# Calculate total
total = 31.04

# Create confirmation buttons
confirmation_component = create_button_component(
    f"Your order total is ${total:.2f}. How would you like to receive it?",
    [
        {"id": "confirm_delivery", "title": "Delivery 🚗"},
        {"id": "confirm_pickup", "title": "Pickup 🏃"},
        {"id": "cancel_order", "title": "Cancel ❌"}
    ],
    header_text="Order Confirmation",
    footer_text=f"Estimated time: 30-45 mins"
)

return {
    "messages": AIMessage(content="Order summary: 2 Pizzas, 1 Coke"),
    "interactive_component": confirmation_component
}
```

Then update the webhook handler to check for `interactive_component` in state:

```python
# In webhook_endpoint.py
interactive_comp = output_state.values.get("interactive_component")

if interactive_comp:
    success = await send_response(
        from_number, response_message, "interactive_button",
        phone_number_id=phone_number_id,
        whatsapp_token=whatsapp_token,
        interactive_component=interactive_comp
    )
```

---

## 🎯 Example Customer Journey

### Journey 1: Ordering with Interactive Menu

1. **Customer**: "What's on the menu?"
2. **Assistant**: Sends interactive list with all menu items organized by category
3. **Customer**: Taps "🍕 Pepperoni Pizza - $14.99"
4. **System**: Converts to "I'd like to order Pepperoni Pizza"
5. **Assistant**: "Great choice! Would you like delivery or pickup?" (with buttons)
6. **Customer**: Taps "Delivery 🚗"
7. **Assistant**: Confirms order with estimated delivery time

### Journey 2: Quick Actions

1. **Customer**: "Hi"
2. **Assistant**: Sends buttons:
   - 📋 View Menu
   - 📦 Track Order
   - 📞 Contact Us
3. **Customer**: Taps "📋 View Menu"
4. **Assistant**: Sends interactive menu list

---

## 📊 Benefits of Interactive Components

✅ **Better UX** - Customers can tap instead of typing
✅ **Fewer Errors** - No typos when selecting menu items
✅ **Faster Ordering** - Quick selections with one tap
✅ **Visual Appeal** - Professional, app-like experience
✅ **Higher Conversion** - Easier path to order completion
✅ **Accessibility** - Works great on all devices

---

## 🔍 Debugging Interactive Components

### Check WhatsApp API Response

```python
# In send_response function
logger.debug(f"Interactive component: {json_data}")
```

### Common Issues

1. **Buttons not showing**: Check that you have max 3 buttons
2. **List empty**: Ensure each section has at least 1 row
3. **Text too long**: Check character limits (see specifications above)
4. **Interactive not supported**: Customer's WhatsApp version might be outdated

---

## 🚀 Next Steps

1. **Test the interactive menu** - Ask "Show me the menu" in WhatsApp
2. **Add confirmation buttons** - Enhance order_node with buttons
3. **Create quick actions** - Add quick reply buttons for common tasks
4. **Track user selections** - Log which items are most popular
5. **A/B test** - Compare interactive vs text-only conversion rates

---

## 📚 References

- [WhatsApp Business API - Interactive Messages](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages#interactive-messages)
- [Interactive Components Examples](https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages#interactive-object)

---

**Your restaurant assistant is now fully equipped with interactive components!** 🎉
