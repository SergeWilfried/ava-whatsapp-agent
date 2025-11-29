# WhatsApp Interactive Messages Guide

Complete guide to sending and receiving interactive WhatsApp messages including buttons, lists, locations, contacts, and polls.

## 📱 Supported Message Types

1. **Reply Buttons** - Up to 3 quick reply buttons
2. **List Messages** - Structured lists with up to 10 sections
3. **Location Messages** - Send specific locations
4. **Location Requests** - Request user's current location
5. **Call-to-Action (CTA) Buttons** - Phone call or URL buttons
6. **Contact Messages** - Share contact information
7. **Polls** - Single or multiple choice polls (groups only)

## 🚀 Quick Start

### Import the Module

```python
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_reply_buttons,
    create_list_message,
    create_location_message,
    create_location_request,
    create_cta_url_button,
    create_cta_phone_button,
    create_poll,
    create_contact_message,
    # Helper functions
    create_yes_no_buttons,
    create_confirmation_buttons,
    create_rating_buttons
)
```

## 📚 Message Types in Detail

### 1. Reply Buttons

Create up to 3 quick reply buttons:

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_reply_buttons

# Create buttons
buttons = [
    {"id": "option_a", "title": "Option A"},
    {"id": "option_b", "title": "Option B"},
    {"id": "option_c", "title": "Option C"}
]

interactive = create_reply_buttons(
    body_text="Please choose an option:",
    buttons=buttons,
    header_text="Quick Question",  # Optional
    footer_text="Select one option"  # Optional
)

# Return in node to send via WhatsApp
return {
    "messages": AIMessage(content="Choose an option"),
    "interactive_component": interactive
}
```

**Constraints:**
- Maximum 3 buttons
- Button title: 1-20 characters
- Body text: 1-1024 characters
- Header text: up to 60 characters (optional)
- Footer text: up to 60 characters (optional)

**Helper Functions:**

```python
# Quick Yes/No buttons
interactive = create_yes_no_buttons("Do you want to continue?")

# Confirm/Cancel buttons
interactive = create_confirmation_buttons("Confirm this action?")

# Rating buttons (1-3 stars)
interactive = create_rating_buttons("Rate your experience:")
```

### 2. List Messages

Create structured lists with sections:

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_list_message

# Define sections and rows
sections = [
    {
        "title": "Appetizers",
        "rows": [
            {
                "id": "garlic_bread",
                "title": "Garlic Bread",
                "description": "Toasted bread with garlic butter"
            },
            {
                "id": "soup",
                "title": "Soup of the Day",
                "description": "Chef's special soup"
            }
        ]
    },
    {
        "title": "Main Courses",
        "rows": [
            {
                "id": "pizza",
                "title": "Margherita Pizza",
                "description": "Classic tomato and mozzarella"
            },
            {
                "id": "pasta",
                "title": "Pasta Carbonara",
                "description": "Creamy bacon pasta"
            }
        ]
    }
]

interactive = create_list_message(
    body_text="Browse our menu:",
    sections=sections,
    button_text="View Menu",  # Text on the button
    header_text="Restaurant Menu",  # Optional
    footer_text="Tap to see options"  # Optional
)

return {
    "messages": AIMessage(content="Here's our menu"),
    "interactive_component": interactive
}
```

**Constraints:**
- Maximum 10 sections
- Maximum 10 rows per section
- Row title: up to 24 characters
- Row description: up to 72 characters
- Button text: 1-20 characters

### 3. Location Messages

Send a specific location:

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_location_message

# Send a location
location = create_location_message(
    latitude=37.7749,
    longitude=-122.4194,
    name="Our Restaurant",
    address="123 Main St, San Francisco, CA"
)

return {
    "messages": AIMessage(content="Here's our location"),
    "location_data": location
}
```

### 4. Location Request

Request user's current location:

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_location_request

# Request location
interactive = create_location_request(
    "Please share your location for delivery"
)

return {
    "messages": AIMessage(content="Share location for delivery"),
    "interactive_component": interactive
}
```

**Receiving Location:**

When a user shares their location, you'll receive:

```python
# In whatsapp_response.py, location messages are processed as:
# "[Location shared: Location Name at (lat, lon) - address]"

# The message content will be:
"[Location shared: Home at (37.7749, -122.4194) - 123 Main St]"
```

### 5. Call-to-Action (CTA) Buttons

#### URL Button

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_cta_url_button

interactive = create_cta_url_button(
    body_text="Check out our website for more info!",
    button_text="Visit Website",
    url="https://example.com",
    header_text="Learn More",  # Optional
    footer_text="Click to open"  # Optional
)

return {
    "messages": AIMessage(content="Visit us online"),
    "interactive_component": interactive
}
```

#### Phone Call Button

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_cta_phone_button

interactive = create_cta_phone_button(
    body_text="Call us for immediate assistance!",
    button_text="Call Now",
    phone_number="+1234567890",  # Include country code
    header_text="Customer Support",  # Optional
    footer_text="Available 24/7"  # Optional
)

return {
    "messages": AIMessage(content="Contact us"),
    "interactive_component": interactive
}
```

### 6. Contact Messages

Share contact information:

```python
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_contact_message,
    create_address_message
)

# Define contacts
contacts = [
    {
        "name": {
            "formatted_name": "John Doe",
            "first_name": "John",
            "last_name": "Doe"
        },
        "phones": [
            {
                "phone": "+1234567890",
                "type": "CELL"
            }
        ],
        "emails": [
            {
                "email": "john@example.com",
                "type": "WORK"
            }
        ],
        "org": {
            "company": "Example Corp",
            "department": "Sales",
            "title": "Sales Manager"
        },
        "urls": [
            {
                "url": "https://example.com",
                "type": "WORK"
            }
        ],
        "addresses": [
            create_address_message(
                street="123 Main St",
                city="San Francisco",
                state="CA",
                zip_code="94102",
                country="United States",
                country_code="US"
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

### 7. Polls (Groups Only)

**Note:** Polls only work in WhatsApp groups, not in individual chats.

```python
from ai_companion.interfaces.whatsapp.interactive_components import create_poll

# Single choice poll
poll = create_poll(
    poll_question="What's your favorite cuisine?",
    options=["Italian", "Chinese", "Mexican", "Japanese"],
    allow_multiple_answers=False
)

# Multiple choice poll
poll = create_poll(
    poll_question="Which features do you want?",
    options=["Feature A", "Feature B", "Feature C", "Feature D"],
    allow_multiple_answers=True
)

# Note: Poll sending requires special handling in WhatsApp API
```

**Constraints:**
- Only works in groups
- 2-12 options required
- Question: 1-255 characters
- Each option: 1-100 characters

## 🎯 Using Interactive Messages in Nodes

### Example: Create Interactive Node

```python
from ai_companion.graph.state import AICompanionState
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_reply_buttons,
    create_list_message
)

async def interactive_node(state: AICompanionState, config: RunnableConfig):
    """Node that sends interactive messages based on context."""

    user_message = state["messages"][-1].content.lower()

    # Send buttons for simple choices
    if "yes or no" in user_message or "confirm" in user_message:
        buttons = [
            {"id": "yes", "title": "Yes ✓"},
            {"id": "no", "title": "No ✗"}
        ]
        interactive = create_reply_buttons(
            body_text="Please confirm your choice:",
            buttons=buttons
        )

        return {
            "messages": AIMessage(content="Choose yes or no"),
            "interactive_component": interactive
        }

    # Send list for menu/catalog
    elif "menu" in user_message or "options" in user_message:
        sections = [
            {
                "title": "Category 1",
                "rows": [
                    {"id": "item1", "title": "Item 1", "description": "Description 1"},
                    {"id": "item2", "title": "Item 2", "description": "Description 2"}
                ]
            }
        ]
        interactive = create_list_message(
            body_text="Here are your options:",
            sections=sections,
            button_text="View Options"
        )

        return {
            "messages": AIMessage(content="Browse options"),
            "interactive_component": interactive
        }

    # Send location request for delivery
    elif "delivery" in user_message or "location" in user_message:
        from ai_companion.interfaces.whatsapp.interactive_components import create_location_request

        interactive = create_location_request(
            "Please share your delivery location"
        )

        return {
            "messages": AIMessage(content="Share your location"),
            "interactive_component": interactive
        }

    # Default text response
    return {
        "messages": AIMessage(content="How can I help you?")
    }
```

## 📥 Receiving Interactive Responses

When users interact with buttons or lists, responses are automatically processed:

### Button Click Response

```python
# User clicks button with ID "yes" and title "Yes ✓"
# Processed as:
"[Button clicked: Yes ✓ (ID: yes)]"
```

### List Selection Response

```python
# User selects list item
# Processed as:
"[List selection: Pizza (ID: pizza) - Classic Margherita]"
```

### Location Response

```python
# User shares location
# Processed as:
"[Location shared: Home at (37.7749, -122.4194) - 123 Main St]"
```

### Contact Response

```python
# User shares contact(s)
# Processed as:
"[Contact(s) shared: John Doe, Jane Smith]"
```

## 🔧 Integration with Graph Workflow

### Update Router to Handle Interactive Messages

```python
# In prompts.py, update ROUTER_PROMPT

ROUTER_PROMPT = """
...
Route to 'interactive' when:
- User asks for options, menu, or choices
- User needs to make a selection
- You want to provide structured options
- You need to request location
- You want to share contact information
...
"""
```

### Add Interactive Workflow to Edges

```python
# In edges.py

def select_workflow(
    state: AICompanionState,
) -> Literal["conversation_node", "interactive_node", "image_node", "audio_node"]:
    workflow = state["workflow"]

    if workflow == "interactive":
        return "interactive_node"
    elif workflow == "image":
        return "image_node"
    elif workflow == "audio":
        return "audio_node"
    else:
        return "conversation_node"
```

## 🎨 Best Practices

### 1. **Use Appropriate Message Types**

- **Buttons**: For simple yes/no or 2-3 options
- **Lists**: For catalogs, menus, or many options
- **Location**: For delivery, directions, or store locator
- **CTA**: For external links or phone calls
- **Contacts**: For sharing business contact info

### 2. **Keep Text Concise**

- Button titles: Short and clear (max 20 chars)
- List descriptions: Brief but informative (max 72 chars)
- Body text: Clear and to the point

### 3. **Provide Context**

- Use header text to set context
- Use footer text for additional instructions
- Make button/option purposes obvious

### 4. **Handle Responses Properly**

```python
# Check for interactive responses in conversation
if "[Button clicked:" in user_message:
    # Extract button ID
    button_id = extract_button_id(user_message)
    # Process based on button ID

elif "[List selection:" in user_message:
    # Extract selection ID
    selection_id = extract_selection_id(user_message)
    # Process based on selection
```

### 5. **Fallback to Text**

Always provide text alternative if interactive fails:

```python
try:
    return {
        "messages": AIMessage(content="Choose an option"),
        "interactive_component": interactive
    }
except Exception as e:
    # Fallback to text
    return {
        "messages": AIMessage(content="Please reply with: A, B, or C")
    }
```

## 🐛 Common Issues & Solutions

### Issue 1: Buttons Not Showing

**Problem**: Interactive message appears as text

**Solutions**:
- Ensure `interactive_component` is set in state
- Check WhatsApp Business API is properly configured
- Verify message structure matches API specs
- Ensure recipient can receive interactive messages

### Issue 2: Location Request Not Working

**Problem**: Location request doesn't prompt user

**Solutions**:
- Use `create_location_request()`, not `create_location_message()`
- Ensure user has location services enabled
- Check WhatsApp permissions on user's device

### Issue 3: List Too Long

**Problem**: List truncated or not displaying

**Solutions**:
- Maximum 10 sections
- Maximum 10 rows per section
- Split into multiple messages if needed
- Consider using buttons for fewer options

### Issue 4: Poll Not Sending

**Problem**: Polls don't appear

**Solutions**:
- Polls only work in groups, not individual chats
- Ensure 2-12 options provided
- Check API version supports polls

## 📊 Complete Example

Here's a complete example of an interactive tutoring session:

```python
async def tutoring_interactive_node(state: AICompanionState, config: RunnableConfig):
    """Interactive tutoring node with various message types."""

    user_message = state["messages"][-1].content.lower()

    # Topic selection with list
    if "choose topic" in user_message:
        sections = [
            {
                "title": "Mathematics",
                "rows": [
                    {"id": "algebra", "title": "Algebra", "description": "Linear equations, polynomials"},
                    {"id": "geometry", "title": "Geometry", "description": "Shapes, angles, theorems"},
                    {"id": "calculus", "title": "Calculus", "description": "Derivatives, integrals"}
                ]
            },
            {
                "title": "Science",
                "rows": [
                    {"id": "physics", "title": "Physics", "description": "Motion, energy, forces"},
                    {"id": "chemistry", "title": "Chemistry", "description": "Elements, reactions"},
                    {"id": "biology", "title": "Biology", "description": "Life sciences, cells"}
                ]
            }
        ]

        interactive = create_list_message(
            body_text="What would you like to learn today?",
            sections=sections,
            button_text="Choose Topic",
            header_text="Available Subjects"
        )

        return {
            "messages": AIMessage(content="Select a topic"),
            "interactive_component": interactive
        }

    # Difficulty level with buttons
    elif "difficulty" in user_message:
        buttons = [
            {"id": "easy", "title": "Beginner"},
            {"id": "medium", "title": "Intermediate"},
            {"id": "hard", "title": "Advanced"}
        ]

        interactive = create_reply_buttons(
            body_text="What's your skill level?",
            buttons=buttons,
            header_text="Choose Difficulty"
        )

        return {
            "messages": AIMessage(content="Select difficulty"),
            "interactive_component": interactive
        }

    # Quiz answer with buttons
    elif "quiz" in user_message:
        buttons = [
            {"id": "ans_a", "title": "Answer A"},
            {"id": "ans_b", "title": "Answer B"},
            {"id": "ans_c", "title": "Answer C"}
        ]

        interactive = create_reply_buttons(
            body_text="What is 2 + 2?",
            buttons=buttons,
            footer_text="Choose your answer"
        )

        return {
            "messages": AIMessage(content="Quiz question"),
            "interactive_component": interactive
        }

    # Help/Support with CTA
    elif "help" in user_message:
        interactive = create_cta_url_button(
            body_text="Need more help? Visit our support page!",
            button_text="Get Help",
            url="https://example.com/support"
        )

        return {
            "messages": AIMessage(content="Get support"),
            "interactive_component": interactive
        }

    # Default response
    return {
        "messages": AIMessage(content="How can I help you learn today?")
    }
```

## 📚 Additional Resources

- [WhatsApp Cloud API - Interactive Messages](https://developers.facebook.com/docs/whatsapp/cloud-api/messages/interactive-messages)
- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
- [Message Templates](https://developers.facebook.com/docs/whatsapp/message-templates)

---

**Your AI can now send rich, interactive WhatsApp messages!** 📱✨
