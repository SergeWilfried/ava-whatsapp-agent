# WhatsApp Interactive Messages - Implementation Summary

## ✅ What Was Implemented

Successfully added comprehensive WhatsApp interactive message capabilities including:
- **Reply Buttons** (up to 3 buttons)
- **List Messages** (structured menus/catalogs)
- **Location Messages** (send specific locations)
- **Location Requests** (request user's location)
- **Call-to-Action Buttons** (phone & URL)
- **Contact Messages** (share contact info)
- **Polls** (single/multiple choice - groups only)

## 📝 Files Created/Modified

### 1. Created: [interactive_components.py](src/ai_companion/interfaces/whatsapp/interactive_components.py)

**Purpose**: Factory functions for creating all WhatsApp interactive message types

**Key Functions**:
```python
# Button messages
create_reply_buttons(body_text, buttons, header_text, footer_text)
create_yes_no_buttons(question)
create_confirmation_buttons(message)
create_rating_buttons(prompt)

# List messages
create_list_message(body_text, sections, button_text, header_text, footer_text)

# Location
create_location_message(latitude, longitude, name, address)
create_location_request(body_text)

# Call-to-Action
create_cta_url_button(body_text, button_text, url, ...)
create_cta_phone_button(body_text, button_text, phone_number, ...)

# Contacts
create_contact_message(contacts)
create_address_message(street, city, state, zip_code, country, ...)

# Polls (groups only)
create_poll(poll_question, options, allow_multiple_answers)
```

### 2. Modified: [whatsapp_response.py](src/ai_companion/interfaces/whatsapp/whatsapp_response.py)

**Added Receiving Capability**:
```python
# Handle incoming interactive responses
elif message["type"] == "interactive":
    content = process_interactive_response(message)

# Handle location sharing
elif message["type"] == "location":
    location = message["location"]
    content = f"[Location shared: {name} at ({lat}, {lon}) - {address}]"

# Handle contact sharing
elif message["type"] == "contacts":
    contacts = message["contacts"]
    content = f"[Contact(s) shared: {names}]"
```

**Added Sending Capability**:
```python
async def send_response(
    from_number: str,
    response_text: str,
    message_type: str = "text",
    media_content: bytes = None,
    phone_number_id: Optional[str] = None,
    whatsapp_token: Optional[str] = None,
    interactive_component: Optional[Dict] = None,  # NEW
    location_data: Optional[Dict] = None,          # NEW
    contact_data: Optional[Dict] = None,           # NEW
) -> bool:
```

**New Helper Function**:
```python
def process_interactive_response(message: Dict) -> str:
    """Process button clicks and list selections."""
    # Returns formatted strings like:
    # "[Button clicked: Yes (ID: yes)]"
    # "[List selection: Pizza (ID: pizza) - Classic Margherita]"
```

**Updated Message Handler**:
```python
# Check state for interactive components
interactive_component = output_state.values.get("interactive_component")
location_data = output_state.values.get("location_data")
contact_data = output_state.values.get("contact_data")

# Send appropriate message type
if interactive_component or location_data or contact_data:
    if location_data:
        message_type = "location"
    elif contact_data:
        message_type = "contacts"
    else:
        message_type = "interactive"
```

### 3. Modified: [state.py](src/ai_companion/graph/state.py)

**Added New State Fields**:
```python
class AICompanionState(MessagesState):
    # ... existing fields ...
    interactive_component: dict  # Interactive component data
    interactive_type: str        # Type of interactive message
    location_data: dict          # Location data for messages
    contact_data: dict           # Contact data for messages
```

### 4. Created: [WHATSAPP_INTERACTIVE_MESSAGES_GUIDE.md](WHATSAPP_INTERACTIVE_MESSAGES_GUIDE.md)

**Complete documentation including**:
- Detailed API reference for all message types
- Code examples for each type
- Best practices
- Integration guide
- Common issues & solutions
- Complete working examples

## 🚀 How to Use

### Basic Example: Send Reply Buttons

```python
from ai_companion.graph.state import AICompanionState
from langchain_core.messages import AIMessage
from ai_companion.interfaces.whatsapp.interactive_components import create_reply_buttons

async def some_node(state: AICompanionState, config: RunnableConfig):
    """Node that sends interactive buttons."""

    buttons = [
        {"id": "yes", "title": "Yes ✓"},
        {"id": "no", "title": "No ✗"}
    ]

    interactive = create_reply_buttons(
        body_text="Do you want to continue?",
        buttons=buttons,
        header_text="Confirmation Required"
    )

    return {
        "messages": AIMessage(content="Please confirm"),
        "interactive_component": interactive
    }
```

### Example: Send List Menu

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_list_message

async def menu_node(state: AICompanionState, config: RunnableConfig):
    """Send menu as interactive list."""

    sections = [
        {
            "title": "Starters",
            "rows": [
                {"id": "salad", "title": "Caesar Salad", "description": "Fresh romaine lettuce"},
                {"id": "soup", "title": "Tomato Soup", "description": "Homemade tomato soup"}
            ]
        },
        {
            "title": "Main Course",
            "rows": [
                {"id": "pizza", "title": "Margherita Pizza", "description": "$12.99"},
                {"id": "pasta", "title": "Carbonara Pasta", "description": "$14.99"}
            ]
        }
    ]

    interactive = create_list_message(
        body_text="What would you like to order?",
        sections=sections,
        button_text="View Menu",
        header_text="Our Menu"
    )

    return {
        "messages": AIMessage(content="Browse our menu"),
        "interactive_component": interactive
    }
```

### Example: Request Location

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_location_request

async def delivery_node(state: AICompanionState, config: RunnableConfig):
    """Request user's location for delivery."""

    interactive = create_location_request(
        "Please share your delivery location so we can calculate the delivery fee"
    )

    return {
        "messages": AIMessage(content="Share your location"),
        "interactive_component": interactive
    }
```

### Example: Send Location

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_location_message

async def store_location_node(state: AICompanionState, config: RunnableConfig):
    """Send store location to user."""

    location = create_location_message(
        latitude=37.7749,
        longitude=-122.4194,
        name="Our Restaurant",
        address="123 Main St, San Francisco, CA 94102"
    )

    return {
        "messages": AIMessage(content="Here's our location"),
        "location_data": location
    }
```

### Example: Send CTA Button

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_cta_url_button

async def website_node(state: AICompanionState, config: RunnableConfig):
    """Send website link with CTA button."""

    interactive = create_cta_url_button(
        body_text="Visit our website to see the full menu and place online orders!",
        button_text="Visit Website",
        url="https://restaurant.com",
        header_text="Order Online"
    )

    return {
        "messages": AIMessage(content="Visit our website"),
        "interactive_component": interactive
    }
```

### Example: Share Contact

```python
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_contact_message,
    create_address_message
)

async def contact_node(state: AICompanionState, config: RunnableConfig):
    """Share business contact information."""

    contacts = [
        {
            "name": {
                "formatted_name": "Customer Support",
                "first_name": "Customer",
                "last_name": "Support"
            },
            "phones": [
                {"phone": "+1234567890", "type": "CELL"}
            ],
            "emails": [
                {"email": "support@restaurant.com", "type": "WORK"}
            ],
            "org": {
                "company": "Great Restaurant",
                "title": "Support Team"
            },
            "addresses": [
                create_address_message(
                    street="123 Main St",
                    city="San Francisco",
                    state="CA",
                    zip_code="94102",
                    country="United States"
                )
            ]
        }
    ]

    contact_data = create_contact_message(contacts)

    return {
        "messages": AIMessage(content="Here's our contact info"),
        "contact_data": contact_data
    }
```

## 📥 Handling User Responses

When users interact with your messages, responses are automatically processed:

### Button Click
```python
# User clicks "Yes" button
# Your conversation receives:
"[Button clicked: Yes ✓ (ID: yes)]"

# You can check in your node:
if "[Button clicked:" in user_message:
    if "ID: yes" in user_message:
        # User clicked yes
        pass
```

### List Selection
```python
# User selects "Pizza" from list
# Your conversation receives:
"[List selection: Margherita Pizza (ID: pizza) - $12.99]"

# You can parse this:
if "[List selection:" in user_message:
    # Extract the ID to process the selection
    if "ID: pizza" in user_message:
        # User selected pizza
        pass
```

### Location Shared
```python
# User shares location
# Your conversation receives:
"[Location shared: Home at (37.7749, -122.4194) - 123 Main St]"

# You can extract coordinates and process delivery
```

## 🎯 Integration Patterns

### Pattern 1: Smart Interactive Responses

Create a node that automatically decides when to use interactive messages:

```python
async def smart_interactive_node(state: AICompanionState, config: RunnableConfig):
    """Intelligently choose interactive message type based on context."""

    user_message = state["messages"][-1].content.lower()

    # Use buttons for binary choices
    if any(word in user_message for word in ["yes or no", "confirm", "agree"]):
        interactive = create_yes_no_buttons("Please confirm:")
        return {
            "messages": AIMessage(content="Choose an option"),
            "interactive_component": interactive
        }

    # Use lists for menus/catalogs
    elif any(word in user_message for word in ["menu", "options", "catalog", "list"]):
        # Create menu sections...
        interactive = create_list_message(...)
        return {
            "messages": AIMessage(content="Browse options"),
            "interactive_component": interactive
        }

    # Request location for delivery
    elif any(word in user_message for word in ["delivery", "ship", "send"]):
        interactive = create_location_request("Share your delivery address")
        return {
            "messages": AIMessage(content="Share location"),
            "interactive_component": interactive
        }

    # Default text response
    return {
        "messages": AIMessage(content="How can I help you?")
    }
```

### Pattern 2: Multi-Step Interactive Flow

```python
async def order_flow_node(state: AICompanionState, config: RunnableConfig):
    """Multi-step ordering process with interactive messages."""

    user_message = state["messages"][-1].content

    # Step 1: Show menu (list)
    if "order" in user_message and "[List selection:" not in user_message:
        sections = create_menu_sections()
        interactive = create_list_message("What would you like?", sections, "Order Now")
        return {
            "messages": AIMessage(content="Choose an item"),
            "interactive_component": interactive
        }

    # Step 2: Confirm order (buttons)
    elif "[List selection:" in user_message:
        item_id = extract_id(user_message)
        buttons = [
            {"id": "confirm_order", "title": "Confirm Order"},
            {"id": "cancel_order", "title": "Cancel"}
        ]
        interactive = create_reply_buttons(
            f"Confirm your order: {item_id}?",
            buttons
        )
        return {
            "messages": AIMessage(content="Confirm order"),
            "interactive_component": interactive
        }

    # Step 3: Request delivery location
    elif "[Button clicked:" in user_message and "confirm_order" in user_message:
        interactive = create_location_request("Share delivery location")
        return {
            "messages": AIMessage(content="Share location for delivery"),
            "interactive_component": interactive
        }

    # Step 4: Process delivery
    elif "[Location shared:" in user_message:
        # Process delivery with location
        return {
            "messages": AIMessage(content="Order confirmed! Delivering soon.")
        }
```

### Pattern 3: Context-Aware Helper Functions

```python
def should_use_buttons(message: str) -> bool:
    """Check if buttons are appropriate for this message."""
    button_keywords = ["yes or no", "confirm", "choose", "select", "pick"]
    return any(kw in message.lower() for kw in button_keywords)

def should_use_list(message: str) -> bool:
    """Check if list is appropriate for this message."""
    list_keywords = ["menu", "options", "catalog", "browse", "see all"]
    return any(kw in message.lower() for kw in list_keywords)

def should_request_location(message: str) -> bool:
    """Check if location request is needed."""
    location_keywords = ["delivery", "where", "address", "location"]
    return any(kw in message.lower() for kw in location_keywords)
```

## 🎨 Best Practices

### 1. **Progressive Disclosure**
Start simple, add complexity as needed:
```python
# First: Simple buttons
buttons = create_yes_no_buttons("Continue?")

# Then: More options
buttons = [
    {"id": "opt1", "title": "Option 1"},
    {"id": "opt2", "title": "Option 2"},
    {"id": "opt3", "title": "Option 3"}
]

# Finally: Full list for many items
sections = create_detailed_list()
```

### 2. **Clear Action Verbs**
Use action-oriented button text:
```python
# Good
{"id": "confirm", "title": "Confirm Order"}
{"id": "view", "title": "View Details"}
{"id": "call", "title": "Call Now"}

# Avoid
{"id": "ok", "title": "OK"}
{"id": "next", "title": "Next"}
```

### 3. **Provide Context**
Always include body text explaining the choice:
```python
interactive = create_reply_buttons(
    body_text="You're about to place an order for $25.99. Please confirm:",
    buttons=[...],
    header_text="Order Confirmation"
)
```

### 4. **Handle All Response Types**
```python
async def handle_response(state: AICompanionState, config: RunnableConfig):
    user_message = state["messages"][-1].content

    if "[Button clicked:" in user_message:
        # Handle button response
        pass
    elif "[List selection:" in user_message:
        # Handle list selection
        pass
    elif "[Location shared:" in user_message:
        # Handle location
        pass
    else:
        # Handle regular text
        pass
```

### 5. **Fallback to Text**
Always provide a text alternative:
```python
try:
    return {
        "messages": AIMessage(content="Choose:"),
        "interactive_component": interactive
    }
except Exception as e:
    # Fallback to text
    return {
        "messages": AIMessage(content="Reply with: 1 for Yes, 2 for No")
    }
```

## 🔍 Testing Interactive Messages

### Test Sending

```python
# Test each message type independently
from ai_companion.interfaces.whatsapp.interactive_components import *

# Test buttons
buttons = create_yes_no_buttons("Test question?")
print(buttons)

# Test list
sections = [{
    "title": "Test",
    "rows": [{"id": "test", "title": "Test Item", "description": "Test"}]
}]
list_msg = create_list_message("Test list", sections)
print(list_msg)

# Test location
location = create_location_message(37.7749, -122.4194, "Test Location")
print(location)
```

### Test Receiving

```python
# Simulate button click response
test_message = {
    "type": "interactive",
    "interactive": {
        "type": "button_reply",
        "button_reply": {
            "id": "yes",
            "title": "Yes ✓"
        }
    }
}

result = process_interactive_response(test_message)
print(result)  # "[Button clicked: Yes ✓ (ID: yes)]"
```

## 📊 Message Type Decision Tree

```
User Message
    │
    ├── Binary Choice (yes/no, confirm/cancel)
    │   └── Use: create_reply_buttons() with 2 buttons
    │
    ├── 2-3 Options
    │   └── Use: create_reply_buttons() with 2-3 buttons
    │
    ├── 4+ Options (menu, catalog)
    │   └── Use: create_list_message() with sections
    │
    ├── Need User Location
    │   └── Use: create_location_request()
    │
    ├── Share Your Location
    │   └── Use: create_location_message()
    │
    ├── External Action (website, call)
    │   └── Use: create_cta_url_button() or create_cta_phone_button()
    │
    ├── Share Contact Info
    │   └── Use: create_contact_message()
    │
    └── Poll/Survey (groups only)
        └── Use: create_poll()
```

## 🎉 Benefits

✅ **Rich User Experience** - Interactive buttons and lists
✅ **Reduced Errors** - Structured input vs free text
✅ **Faster Responses** - One tap instead of typing
✅ **Better Conversion** - Clear call-to-action
✅ **Location Sharing** - Easy delivery/directions
✅ **Professional Look** - Branded, polished appearance

## 📚 Next Steps

1. **Test each message type** with real WhatsApp numbers
2. **Create interactive flows** for your use case
3. **Monitor user engagement** with interactive vs text
4. **Optimize button/list content** based on analytics
5. **Add analytics** to track which message types perform best

---

**Your WhatsApp AI can now send professional interactive messages!** 📱✨
