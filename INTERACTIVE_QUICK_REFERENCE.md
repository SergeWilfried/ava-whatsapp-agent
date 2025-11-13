# WhatsApp Interactive Messages - Quick Reference

## 🚀 Quick Import

```python
from ai_companion.interfaces.whatsapp.interactive_components import (
    # Button messages
    create_reply_buttons,
    create_yes_no_buttons,
    create_confirmation_buttons,

    # List messages
    create_list_message,

    # Location
    create_location_message,
    create_location_request,

    # Call-to-Action
    create_cta_url_button,
    create_cta_phone_button,

    # Contacts
    create_contact_message,
    create_address_message,

    # Polls
    create_poll
)
```

## 📋 Cheat Sheet

### Send Reply Buttons (1-3 buttons)

```python
buttons = [
    {"id": "yes", "title": "Yes"},
    {"id": "no", "title": "No"}
]

interactive = create_reply_buttons(
    body_text="Question here?",
    buttons=buttons
)

return {
    "messages": AIMessage(content="Choose"),
    "interactive_component": interactive
}
```

### Send List (4+ options)

```python
sections = [
    {
        "title": "Section Name",
        "rows": [
            {"id": "item1", "title": "Item 1", "description": "Desc 1"},
            {"id": "item2", "title": "Item 2", "description": "Desc 2"}
        ]
    }
]

interactive = create_list_message(
    body_text="Choose from menu:",
    sections=sections,
    button_text="View Menu"
)

return {
    "messages": AIMessage(content="Browse"),
    "interactive_component": interactive
}
```

### Request Location

```python
interactive = create_location_request(
    "Please share your location"
)

return {
    "messages": AIMessage(content="Share location"),
    "interactive_component": interactive
}
```

### Send Location

```python
location = create_location_message(
    latitude=37.7749,
    longitude=-122.4194,
    name="Store Name",
    address="123 Main St"
)

return {
    "messages": AIMessage(content="Our location"),
    "location_data": location
}
```

### Send URL Button

```python
interactive = create_cta_url_button(
    body_text="Visit our site!",
    button_text="Open Website",
    url="https://example.com"
)

return {
    "messages": AIMessage(content="Visit us"),
    "interactive_component": interactive
}
```

### Send Phone Button

```python
interactive = create_cta_phone_button(
    body_text="Call us now!",
    button_text="Call",
    phone_number="+1234567890"
)

return {
    "messages": AIMessage(content="Contact"),
    "interactive_component": interactive
}
```

## 📥 Receive Responses

### Check Response Type

```python
user_message = state["messages"][-1].content

if "[Button clicked:" in user_message:
    # Button was clicked
    button_id = extract_button_id(user_message)

elif "[List selection:" in user_message:
    # List item was selected
    item_id = extract_list_selection_id(user_message)

elif "[Location shared:" in user_message:
    # Location was shared
    lat, lon = extract_location_coordinates(user_message)

elif "[Contact(s) shared:" in user_message:
    # Contact was shared
    pass
```

### Helper Functions

```python
from ai_companion.graph.nodes_interactive_example import (
    extract_button_id,
    extract_list_selection_id,
    extract_location_coordinates,
    is_button_response,
    is_list_response,
    is_location_response
)
```

## 🎯 When to Use What

| Situation | Use This |
|-----------|----------|
| Yes/No question | `create_yes_no_buttons()` |
| Confirm action | `create_confirmation_buttons()` |
| 2-3 options | `create_reply_buttons()` |
| 4+ options / Menu | `create_list_message()` |
| Need user location | `create_location_request()` |
| Share your location | `create_location_message()` |
| Open website | `create_cta_url_button()` |
| Make phone call | `create_cta_phone_button()` |
| Share contact info | `create_contact_message()` |
| Poll (groups only) | `create_poll()` |

## ⚡ Common Patterns

### Pattern: Menu → Selection → Confirmation

```python
# Step 1: Show menu
if "menu" in user_message:
    sections = create_menu_sections()
    interactive = create_list_message("Choose item:", sections, "View Menu")
    return {"messages": AIMessage("Browse"), "interactive_component": interactive}

# Step 2: Confirm selection
elif "[List selection:" in user_message:
    item = extract_list_selection_id(user_message)
    interactive = create_confirmation_buttons(f"Confirm {item}?")
    return {"messages": AIMessage("Confirm"), "interactive_component": interactive}

# Step 3: Process
elif "[Button clicked:" in user_message and "confirm" in user_message:
    return {"messages": AIMessage("Order confirmed!")}
```

### Pattern: Request → Receive → Process Location

```python
# Step 1: Request location
if "delivery" in user_message:
    interactive = create_location_request("Share delivery address")
    return {"messages": AIMessage("Share location"), "interactive_component": interactive}

# Step 2: Process location
elif "[Location shared:" in user_message:
    lat, lon = extract_location_coordinates(user_message)
    # Calculate delivery fee, estimate time, etc.
    return {"messages": AIMessage(f"Delivering to ({lat}, {lon})")}
```

### Pattern: Smart Selection

```python
# Auto-choose appropriate interactive type
if "yes or no" in user_message:
    return create_yes_no_buttons("Choose:")

elif word_count(options) <= 3:
    return create_reply_buttons(...)

else:
    return create_list_message(...)
```

## 🎨 Best Practices

✅ **DO**:
- Use clear, action-oriented button text
- Provide context in body text
- Keep titles short (max 20 chars for buttons)
- Use lists for 4+ options
- Always handle responses

❌ **DON'T**:
- Use more than 3 reply buttons
- Forget to set interactive_component in state
- Use vague button text ("OK", "Next")
- Make lists too long (max 10 sections, 10 rows each)
- Assume interactive messages work everywhere (polls = groups only)

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Buttons not showing | Set `interactive_component` in state return |
| List too long | Max 10 sections × 10 rows, split if needed |
| Location not working | Use `create_location_request()` not `create_location_message()` |
| Poll not sending | Polls only work in groups |
| Message appears as text | Check WhatsApp Business API config |

## 📦 State Fields

When returning from nodes:

```python
return {
    "messages": AIMessage(content="..."),
    "interactive_component": {...},  # For buttons, lists, location_request
    "location_data": {...},          # For location messages
    "contact_data": {...}            # For contact messages
}
```

## 🎓 Complete Examples

See full working examples in:
- [nodes_interactive_example.py](src/ai_companion/graph/nodes_interactive_example.py)
  - `tutoring_interactive_node()` - Educational use case
  - `restaurant_interactive_node()` - Restaurant ordering
  - `smart_interactive_node()` - Intelligent message type selection

## 📚 Full Documentation

- [WHATSAPP_INTERACTIVE_MESSAGES_GUIDE.md](WHATSAPP_INTERACTIVE_MESSAGES_GUIDE.md) - Complete guide
- [INTERACTIVE_IMPLEMENTATION_SUMMARY.md](INTERACTIVE_IMPLEMENTATION_SUMMARY.md) - Implementation details

## 🚀 Getting Started

1. Import the functions you need
2. Create interactive components in your nodes
3. Return with appropriate state field
4. Handle responses with helper functions
5. Test with real WhatsApp numbers

```python
# Minimal working example
async def my_node(state: AICompanionState, config: RunnableConfig):
    interactive = create_yes_no_buttons("Continue?")
    return {
        "messages": AIMessage(content="Choose"),
        "interactive_component": interactive
    }
```

---

**Ready to create rich interactive WhatsApp experiences!** 🎉
