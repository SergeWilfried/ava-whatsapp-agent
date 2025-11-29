# How Interactive Messages Work - Complete Explanation

## 🎯 Current State: **Manual Implementation Required**

**Important**: Interactive messages are **implemented and ready to use**, but they are **NOT automatically triggered** by the AI. You must manually create nodes or modify existing nodes to send them.

## 📊 Current Architecture

```
User Message (WhatsApp)
    ↓
[whatsapp_response.py] Receives message
    ↓
    ├─ Text message → Extracted as text
    ├─ Button click → "[Button clicked: Title (ID: id)]"
    ├─ List selection → "[List selection: Item (ID: id)]"
    ├─ Location shared → "[Location shared: Name at (lat,lon)]"
    └─ Contact shared → "[Contact(s) shared: Names]"
    ↓
Message passed to LangGraph workflow
    ↓
Router Node → Determines workflow type
    ↓
Conversation Node → Generates text response
    ↓
[whatsapp_response.py] Checks state for:
    ├─ interactive_component → Send interactive message
    ├─ location_data → Send location
    ├─ contact_data → Send contact
    └─ (none) → Send text message
    ↓
WhatsApp API sends message to user
```

## 🔍 What's Implemented

### 1. **Receiving Side** ✅ Fully Automatic

In [whatsapp_response.py](src/ai_companion/interfaces/whatsapp/whatsapp_response.py), incoming messages are automatically processed:

```python
# Lines 80-101 in whatsapp_response.py

elif message["type"] == "interactive":
    # User clicked a button or selected from list
    content = process_interactive_response(message)
    # Result: "[Button clicked: Yes (ID: yes)]"

elif message["type"] == "location":
    # User shared their location
    content = f"[Location shared: {name} at ({lat}, {lon}) - {address}]"

elif message["type"] == "contacts":
    # User shared a contact
    content = f"[Contact(s) shared: {names}]"
```

**This happens automatically** - no code changes needed to receive interactive responses.

### 2. **Sending Side** ✅ Available but Manual

In [whatsapp_response.py](src/ai_companion/interfaces/whatsapp/whatsapp_response.py), the system checks for interactive components:

```python
# Lines 100-142 in whatsapp_response.py

# Check for interactive components in state
interactive_component = output_state.values.get("interactive_component")
location_data = output_state.values.get("location_data")
contact_data = output_state.values.get("contact_data")

# If any exist, send the appropriate message type
if interactive_component or location_data or contact_data:
    if location_data:
        message_type = "location"
    elif contact_data:
        message_type = "contacts"
    else:
        message_type = "interactive"

    success = await send_response(
        from_number, response_message, message_type,
        interactive_component=interactive_component,
        location_data=location_data,
        contact_data=contact_data
    )
```

**This is automatic too** - it checks the state and sends the right message type.

### 3. **Creation Side** ❌ NOT Implemented (Manual Required)

**The AI does NOT automatically create interactive messages.** You must:
- Create custom nodes, OR
- Modify existing nodes, OR
- Add logic to decide when to send interactive messages

## 🚫 What's NOT Implemented

### No Automatic Interactive Message Generation

The current `conversation_node` only returns text:

```python
# Current conversation_node (lines 37-52 in nodes.py)

async def conversation_node(state: AICompanionState, config: RunnableConfig):
    """Simple conversation node without search tools."""
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))

    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    # ONLY returns text - no interactive components
    return {"messages": AIMessage(content=response)}
```

**Missing**: Logic to decide when/how to create interactive messages.

## 💡 How to Use Interactive Messages

You have **3 options** to send interactive messages:

### Option 1: Create a New Interactive Node

Create a dedicated node that sends interactive messages:

```python
# In nodes.py or a new file

from ai_companion.interfaces.whatsapp.interactive_components import create_reply_buttons

async def interactive_menu_node(state: AICompanionState, config: RunnableConfig):
    """Node that sends interactive menu."""

    user_message = state["messages"][-1].content.lower()

    # Check if user wants a menu
    if "menu" in user_message:
        sections = [
            {
                "title": "Main Dishes",
                "rows": [
                    {"id": "pizza", "title": "Pizza", "description": "$12.99"},
                    {"id": "pasta", "title": "Pasta", "description": "$10.99"}
                ]
            }
        ]

        from ai_companion.interfaces.whatsapp.interactive_components import create_list_message
        interactive = create_list_message(
            body_text="Here's our menu:",
            sections=sections,
            button_text="View Menu"
        )

        return {
            "messages": AIMessage(content="Browse our menu"),
            "interactive_component": interactive
        }

    # Otherwise, respond normally
    return {
        "messages": AIMessage(content="How can I help?")
    }
```

**Then add it to the graph**:

```python
# In graph.py

graph_builder.add_node("interactive_menu_node", interactive_menu_node)

# Update routing to use it
graph_builder.add_conditional_edges("memory_injection_node", select_workflow)
```

**And update the router**:

```python
# In edges.py

def select_workflow(state: AICompanionState):
    workflow = state["workflow"]

    if workflow == "interactive":
        return "interactive_menu_node"
    elif workflow == "image":
        return "image_node"
    elif workflow == "audio":
        return "audio_node"
    else:
        return "conversation_node"
```

### Option 2: Modify Existing Conversation Node

Add interactive logic directly to the conversation node:

```python
# Modify conversation_node in nodes.py

async def conversation_node(state: AICompanionState, config: RunnableConfig):
    """Conversation node with optional interactive messages."""
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")
    user_message = state["messages"][-1].content.lower()

    # Check for keywords that should trigger interactive messages
    if "menu" in user_message or "order" in user_message:
        # Import at the top of the file
        from ai_companion.interfaces.whatsapp.interactive_components import create_list_message

        sections = [...]  # Your menu structure
        interactive = create_list_message("Browse our menu:", sections, "View Menu")

        return {
            "messages": AIMessage(content="Here's our menu"),
            "interactive_component": interactive
        }

    # Check for yes/no questions
    elif "?" in user_message and any(word in user_message for word in ["agree", "confirm", "want"]):
        from ai_companion.interfaces.whatsapp.interactive_components import create_yes_no_buttons

        interactive = create_yes_no_buttons("Please confirm:")

        return {
            "messages": AIMessage(content="Choose yes or no"),
            "interactive_component": interactive
        }

    # Default: regular text response
    chain = get_character_response_chain(state.get("summary", ""))
    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    return {"messages": AIMessage(content=response)}
```

### Option 3: Use Example Nodes as Templates

We created example nodes in [nodes_interactive_example.py](src/ai_companion/graph/nodes_interactive_example.py):

```python
# Import the example nodes
from ai_companion.graph.nodes_interactive_example import (
    tutoring_interactive_node,    # For tutoring with subject selection
    restaurant_interactive_node,  # For restaurant ordering
    smart_interactive_node        # Auto-selects best message type
)

# Use them in your graph
graph_builder.add_node("interactive_node", smart_interactive_node)
```

## 🔧 Step-by-Step Integration Guide

### Step 1: Choose Your Approach

- **Simple**: Modify conversation_node with keyword triggers
- **Structured**: Create dedicated interactive node
- **Advanced**: Use router to detect intent and route to interactive node

### Step 2: Import Interactive Components

```python
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_reply_buttons,
    create_list_message,
    create_location_request,
    # ... other types
)
```

### Step 3: Create Interactive Components

```python
# For buttons (yes/no, options)
buttons = [
    {"id": "yes", "title": "Yes"},
    {"id": "no", "title": "No"}
]
interactive = create_reply_buttons("Question?", buttons)

# For lists (menus, catalogs)
sections = [
    {
        "title": "Category",
        "rows": [
            {"id": "item1", "title": "Item 1", "description": "Desc"}
        ]
    }
]
interactive = create_list_message("Choose:", sections, "View")

# For location request
interactive = create_location_request("Share your location")
```

### Step 4: Return in State

```python
return {
    "messages": AIMessage(content="Text message"),
    "interactive_component": interactive  # Add this
}
```

### Step 5: Test

Send a message that triggers your keyword/logic and verify the interactive message appears in WhatsApp.

## 📝 Example: Simple Menu Integration

Here's a **complete working example** you can copy-paste:

```python
# Add this to nodes.py

from ai_companion.interfaces.whatsapp.interactive_components import (
    create_list_message,
    create_yes_no_buttons
)

async def conversation_node(state: AICompanionState, config: RunnableConfig):
    """Conversation node with interactive menu support."""
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")
    user_message = state["messages"][-1].content.lower()

    # INTERACTIVE: Show menu when user asks
    if "menu" in user_message or "food" in user_message or "order" in user_message:
        sections = [
            {
                "title": "Main Dishes",
                "rows": [
                    {"id": "pizza", "title": "Pizza Margherita", "description": "$12.99"},
                    {"id": "pasta", "title": "Pasta Carbonara", "description": "$14.99"},
                    {"id": "burger", "title": "Classic Burger", "description": "$11.99"}
                ]
            },
            {
                "title": "Desserts",
                "rows": [
                    {"id": "cake", "title": "Chocolate Cake", "description": "$6.99"},
                    {"id": "ice_cream", "title": "Ice Cream", "description": "$4.99"}
                ]
            }
        ]

        interactive = create_list_message(
            body_text="Here's our menu! Choose what you'd like to order:",
            sections=sections,
            button_text="View Menu"
        )

        return {
            "messages": AIMessage(content="Browse our menu"),
            "interactive_component": interactive
        }

    # INTERACTIVE: Handle list selections
    elif "[List selection:" in user_message:
        # User selected something from the menu
        interactive = create_yes_no_buttons("Would you like to confirm this order?")

        return {
            "messages": AIMessage(content="Confirm your order"),
            "interactive_component": interactive
        }

    # INTERACTIVE: Handle button clicks
    elif "[Button clicked:" in user_message and "yes" in user_message:
        return {
            "messages": AIMessage(content="✓ Order confirmed! We'll prepare it right away.")
        }

    # DEFAULT: Regular text response
    chain = get_character_response_chain(state.get("summary", ""))
    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    return {"messages": AIMessage(content=response)}
```

## 🎯 Current Limitations

1. **No AI Decision Making** - You must manually code when to send interactive messages
2. **Keyword-Based** - Currently relies on keyword matching (e.g., "menu", "order")
3. **No Router Integration** - Router doesn't have "interactive" workflow type yet
4. **Manual Testing** - Must test with real WhatsApp numbers

## 🔮 Future Enhancements (Not Implemented)

To make the AI **automatically** decide when to send interactive messages, you would need:

1. **Update Router Prompt** to detect when interactive messages are appropriate
2. **Add "interactive" workflow** to router response types
3. **Create intelligent interactive node** that uses AI to generate buttons/lists
4. **Train/prompt the AI** to output structured data for interactive components

This would require significant work and is currently NOT implemented.

## 📚 Quick Reference

### Send Buttons
```python
from ai_companion.interfaces.whatsapp.interactive_components import create_reply_buttons

buttons = [{"id": "yes", "title": "Yes"}, {"id": "no", "title": "No"}]
interactive = create_reply_buttons("Question?", buttons)
return {"messages": AIMessage(...), "interactive_component": interactive}
```

### Send List
```python
from ai_companion.interfaces.whatsapp.interactive_components import create_list_message

sections = [{"title": "Cat", "rows": [{"id": "i1", "title": "Item", "description": "Desc"}]}]
interactive = create_list_message("Choose:", sections, "View")
return {"messages": AIMessage(...), "interactive_component": interactive}
```

### Send Location Request
```python
from ai_companion.interfaces.whatsapp.interactive_components import create_location_request

interactive = create_location_request("Share your location")
return {"messages": AIMessage(...), "interactive_component": interactive}
```

### Receive Button Click
```python
# In your node, check the user message:
if "[Button clicked:" in user_message:
    if "yes" in user_message:
        # User clicked yes
    elif "no" in user_message:
        # User clicked no
```

### Receive List Selection
```python
if "[List selection:" in user_message:
    # Extract ID from: "[List selection: Pizza (ID: pizza) - $12.99]"
    # User selected something from the list
```

---

## ✅ Summary

**What's Working**:
- ✅ Receiving interactive responses (automatic)
- ✅ Sending interactive messages (when you create them)
- ✅ State handling (automatic)
- ✅ WhatsApp API integration (automatic)

**What's Missing**:
- ❌ Automatic generation of interactive messages
- ❌ AI deciding when to use interactive vs text
- ❌ Router detection of interactive intent
- ❌ Pre-built interactive workflows

**To Use Interactive Messages**: You must manually add logic to create and return interactive components in your nodes.

---

**The infrastructure is ready - you just need to add the business logic!** 🚀
