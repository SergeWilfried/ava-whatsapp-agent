"""Example interactive nodes demonstrating WhatsApp interactive messages.

This module shows practical examples of using interactive components
in your LangGraph workflow nodes.
"""

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from ai_companion.graph.state import AICompanionState
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_reply_buttons,
    create_list_message,
    create_location_request,
    create_location_message,
    create_cta_url_button,
    create_cta_phone_button,
    create_contact_message,
    create_address_message,
    create_yes_no_buttons,
    create_confirmation_buttons,
)


async def tutoring_interactive_node(state: AICompanionState, config: RunnableConfig):
    """Interactive tutoring node with subject selection and quizzes.

    This node demonstrates:
    - List messages for subject selection
    - Button messages for quiz answers
    - CTA buttons for additional resources
    """
    user_message = state["messages"][-1].content.lower()

    # Subject selection with list
    if any(word in user_message for word in ["subject", "topic", "learn", "study"]):
        sections = [
            {
                "title": "Mathematics",
                "rows": [
                    {
                        "id": "algebra",
                        "title": "Algebra",
                        "description": "Equations, polynomials, functions"
                    },
                    {
                        "id": "geometry",
                        "title": "Geometry",
                        "description": "Shapes, angles, proofs"
                    },
                    {
                        "id": "calculus",
                        "title": "Calculus",
                        "description": "Derivatives, integrals, limits"
                    }
                ]
            },
            {
                "title": "Science",
                "rows": [
                    {
                        "id": "physics",
                        "title": "Physics",
                        "description": "Motion, energy, forces"
                    },
                    {
                        "id": "chemistry",
                        "title": "Chemistry",
                        "description": "Elements, compounds, reactions"
                    },
                    {
                        "id": "biology",
                        "title": "Biology",
                        "description": "Life, cells, ecosystems"
                    }
                ]
            },
            {
                "title": "Languages",
                "rows": [
                    {
                        "id": "english",
                        "title": "English",
                        "description": "Grammar, literature, writing"
                    },
                    {
                        "id": "spanish",
                        "title": "Spanish",
                        "description": "Vocabulary, conversation"
                    }
                ]
            }
        ]

        interactive = create_list_message(
            body_text="What would you like to learn today? Choose a subject to get started!",
            sections=sections,
            button_text="Choose Subject",
            header_text="Available Subjects",
            footer_text="Select one to begin"
        )

        return {
            "messages": AIMessage(content="Choose a subject to learn"),
            "interactive_component": interactive
        }

    # Difficulty level selection with buttons
    elif "[List selection:" in user_message:
        # User selected a subject, now ask difficulty
        buttons = [
            {"id": "beginner", "title": "Beginner"},
            {"id": "intermediate", "title": "Intermediate"},
            {"id": "advanced", "title": "Advanced"}
        ]

        interactive = create_reply_buttons(
            body_text="What's your current skill level in this subject?",
            buttons=buttons,
            header_text="Choose Difficulty Level",
            footer_text="This helps us personalize your lessons"
        )

        return {
            "messages": AIMessage(content="Select your skill level"),
            "interactive_component": interactive
        }

    # Quiz question with multiple choice buttons
    elif "quiz" in user_message or "test" in user_message:
        buttons = [
            {"id": "ans_a", "title": "A) 4"},
            {"id": "ans_b", "title": "B) 8"},
            {"id": "ans_c", "title": "C) 16"}
        ]

        interactive = create_reply_buttons(
            body_text="Quick Quiz: What is 2³ (2 to the power of 3)?",
            buttons=buttons,
            header_text="Math Quiz Question 1",
            footer_text="Choose your answer"
        )

        return {
            "messages": AIMessage(content="Answer the quiz question"),
            "interactive_component": interactive
        }

    # Additional resources with CTA button
    elif "help" in user_message or "resources" in user_message:
        interactive = create_cta_url_button(
            body_text="Check out our comprehensive study guides, video tutorials, and practice problems!",
            button_text="View Resources",
            url="https://example.com/study-resources",
            header_text="Additional Learning Materials"
        )

        return {
            "messages": AIMessage(content="Access study resources"),
            "interactive_component": interactive
        }

    # Default response
    return {
        "messages": AIMessage(content="I'm your AI tutor! Ask me to help you choose a subject or take a quiz.")
    }


async def restaurant_interactive_node(state: AICompanionState, config: RunnableConfig):
    """Interactive restaurant ordering node.

    Demonstrates:
    - Menu browsing with lists
    - Order confirmation with buttons
    - Location request for delivery
    - Contact sharing
    """
    user_message = state["messages"][-1].content.lower()

    # Show menu with list
    if any(word in user_message for word in ["menu", "order", "food", "eat"]):
        sections = [
            {
                "title": "🍕 Pizzas",
                "rows": [
                    {
                        "id": "margherita",
                        "title": "Margherita Pizza",
                        "description": "$12.99 - Classic tomato & mozzarella"
                    },
                    {
                        "id": "pepperoni",
                        "title": "Pepperoni Pizza",
                        "description": "$14.99 - Loaded with pepperoni"
                    },
                    {
                        "id": "veggie",
                        "title": "Veggie Supreme",
                        "description": "$13.99 - Fresh vegetables"
                    }
                ]
            },
            {
                "title": "🍝 Pasta",
                "rows": [
                    {
                        "id": "carbonara",
                        "title": "Pasta Carbonara",
                        "description": "$14.99 - Creamy bacon pasta"
                    },
                    {
                        "id": "bolognese",
                        "title": "Spaghetti Bolognese",
                        "description": "$13.99 - Meat sauce classic"
                    }
                ]
            },
            {
                "title": "🥗 Salads",
                "rows": [
                    {
                        "id": "caesar",
                        "title": "Caesar Salad",
                        "description": "$8.99 - Romaine, croutons, parmesan"
                    },
                    {
                        "id": "greek",
                        "title": "Greek Salad",
                        "description": "$9.99 - Feta, olives, cucumber"
                    }
                ]
            },
            {
                "title": "🍰 Desserts",
                "rows": [
                    {
                        "id": "tiramisu",
                        "title": "Tiramisu",
                        "description": "$6.99 - Classic Italian dessert"
                    },
                    {
                        "id": "cheesecake",
                        "title": "Cheesecake",
                        "description": "$5.99 - New York style"
                    }
                ]
            }
        ]

        interactive = create_list_message(
            body_text="Browse our delicious menu! Tap an item to add it to your order.",
            sections=sections,
            button_text="View Menu",
            header_text="Our Menu 🍽️",
            footer_text="Fresh ingredients, made to order"
        )

        return {
            "messages": AIMessage(content="Browse our menu"),
            "interactive_component": interactive
        }

    # Confirm order after selection
    elif "[List selection:" in user_message and "delivery" not in user_message:
        # Extract item from selection
        interactive = create_confirmation_buttons(
            "Your item has been added to cart. Would you like to proceed with checkout?"
        )

        return {
            "messages": AIMessage(content="Confirm your order"),
            "interactive_component": interactive
        }

    # Request delivery location
    elif "[Button clicked:" in user_message and "confirm" in user_message:
        interactive = create_location_request(
            "Please share your delivery location so we can calculate delivery time and fees."
        )

        return {
            "messages": AIMessage(content="Share delivery location"),
            "interactive_component": interactive
        }

    # Delivery or pickup choice
    elif "delivery" in user_message or "pickup" in user_message:
        buttons = [
            {"id": "delivery", "title": "🚗 Delivery"},
            {"id": "pickup", "title": "🏃 Pickup"}
        ]

        interactive = create_reply_buttons(
            body_text="How would you like to receive your order?",
            buttons=buttons,
            header_text="Delivery Options"
        )

        return {
            "messages": AIMessage(content="Choose delivery method"),
            "interactive_component": interactive
        }

    # Show restaurant location for pickup
    elif "[Button clicked:" in user_message and "pickup" in user_message:
        location = create_location_message(
            latitude=37.7749,
            longitude=-122.4194,
            name="Our Restaurant - Downtown",
            address="123 Main Street, San Francisco, CA 94102"
        )

        return {
            "messages": AIMessage(content="Here's our location for pickup:"),
            "location_data": location
        }

    # Contact us with CTA phone button
    elif "contact" in user_message or "call" in user_message or "phone" in user_message:
        interactive = create_cta_phone_button(
            body_text="Call us directly for special requests, catering, or immediate assistance!",
            button_text="📞 Call Now",
            phone_number="+1234567890",
            header_text="Customer Support",
            footer_text="Available Mon-Sun 10AM-10PM"
        )

        return {
            "messages": AIMessage(content="Contact us"),
            "interactive_component": interactive
        }

    # Share contact information
    elif "info" in user_message or "details" in user_message:
        contacts = [
            {
                "name": {
                    "formatted_name": "Restaurant Customer Service",
                    "first_name": "Customer",
                    "last_name": "Service"
                },
                "phones": [
                    {"phone": "+1234567890", "type": "WORK"},
                    {"phone": "+1234567891", "type": "CELL"}
                ],
                "emails": [
                    {"email": "orders@restaurant.com", "type": "WORK"}
                ],
                "org": {
                    "company": "Great Restaurant",
                    "title": "Customer Support"
                },
                "urls": [
                    {"url": "https://restaurant.com", "type": "WORK"}
                ],
                "addresses": [
                    create_address_message(
                        street="123 Main Street",
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
            "messages": AIMessage(content="Here's our complete contact information:"),
            "contact_data": contact_data
        }

    # Default response
    return {
        "messages": AIMessage(content="Welcome! Say 'menu' to see what we offer or 'contact' to reach us.")
    }


async def smart_interactive_node(state: AICompanionState, config: RunnableConfig):
    """Smart node that automatically chooses the best interactive message type.

    This node analyzes the conversation context and user intent to select
    the most appropriate interactive message format.
    """
    user_message = state["messages"][-1].content.lower()

    # Detect intent and respond with appropriate interactive message

    # Binary questions → Yes/No buttons
    if any(phrase in user_message for phrase in ["yes or no", "true or false", "agree or disagree"]):
        interactive = create_yes_no_buttons(
            "Please choose your answer:"
        )
        return {
            "messages": AIMessage(content="Choose yes or no"),
            "interactive_component": interactive
        }

    # Confirmation needed → Confirmation buttons
    elif any(word in user_message for word in ["confirm", "verify", "sure", "certain"]):
        interactive = create_confirmation_buttons(
            "Please confirm your choice to proceed."
        )
        return {
            "messages": AIMessage(content="Confirm action"),
            "interactive_component": interactive
        }

    # Multiple options (3 or fewer) → Reply buttons
    elif "choose" in user_message or "select" in user_message or "pick" in user_message:
        # Example: present 3 options
        buttons = [
            {"id": "opt1", "title": "Option 1"},
            {"id": "opt2", "title": "Option 2"},
            {"id": "opt3", "title": "Option 3"}
        ]

        interactive = create_reply_buttons(
            body_text="Please choose one of the following options:",
            buttons=buttons,
            header_text="Selection Required"
        )

        return {
            "messages": AIMessage(content="Select an option"),
            "interactive_component": interactive
        }

    # Many options / catalog / menu → List message
    elif any(word in user_message for word in ["menu", "list", "catalog", "browse", "options", "categories"]):
        # Create a sample list
        sections = [
            {
                "title": "Category A",
                "rows": [
                    {"id": "a1", "title": "Item A1", "description": "Description A1"},
                    {"id": "a2", "title": "Item A2", "description": "Description A2"}
                ]
            },
            {
                "title": "Category B",
                "rows": [
                    {"id": "b1", "title": "Item B1", "description": "Description B1"},
                    {"id": "b2", "title": "Item B2", "description": "Description B2"}
                ]
            }
        ]

        interactive = create_list_message(
            body_text="Browse through our available options:",
            sections=sections,
            button_text="View All"
        )

        return {
            "messages": AIMessage(content="Browse options"),
            "interactive_component": interactive
        }

    # Location related → Location request
    elif any(word in user_message for word in ["where", "location", "address", "delivery", "directions"]):
        interactive = create_location_request(
            "Please share your location"
        )

        return {
            "messages": AIMessage(content="Share your location"),
            "interactive_component": interactive
        }

    # External link / website → CTA URL button
    elif any(word in user_message for word in ["website", "link", "url", "online", "visit"]):
        interactive = create_cta_url_button(
            body_text="Visit our website for more information!",
            button_text="Visit Site",
            url="https://example.com"
        )

        return {
            "messages": AIMessage(content="Visit website"),
            "interactive_component": interactive
        }

    # Contact / call → CTA phone button
    elif any(word in user_message for word in ["call", "phone", "contact", "speak", "talk"]):
        interactive = create_cta_phone_button(
            body_text="Call us for immediate assistance!",
            button_text="Call Now",
            phone_number="+1234567890"
        )

        return {
            "messages": AIMessage(content="Contact us"),
            "interactive_component": interactive
        }

    # Default: regular text response
    return {
        "messages": AIMessage(
            content="I can help you with various options! Try asking about menus, locations, or making a choice."
        )
    }


# Helper functions for processing interactive responses

def extract_button_id(message: str) -> str:
    """Extract button ID from processed interactive response.

    Args:
        message: Formatted message like "[Button clicked: Title (ID: button_id)]"

    Returns:
        The button ID or empty string if not found
    """
    try:
        start = message.find("ID: ") + 4
        end = message.find(")", start)
        return message[start:end] if start > 3 and end > start else ""
    except Exception:
        return ""


def extract_list_selection_id(message: str) -> str:
    """Extract list selection ID from processed interactive response.

    Args:
        message: Formatted message like "[List selection: Title (ID: item_id) - Description]"

    Returns:
        The selection ID or empty string if not found
    """
    try:
        start = message.find("ID: ") + 4
        end = message.find(")", start)
        return message[start:end] if start > 3 and end > start else ""
    except Exception:
        return ""


def extract_location_coordinates(message: str) -> tuple[float, float]:
    """Extract latitude and longitude from location message.

    Args:
        message: Formatted message like "[Location shared: Name at (lat, lon) - address]"

    Returns:
        Tuple of (latitude, longitude) or (0.0, 0.0) if not found
    """
    try:
        start = message.find("(") + 1
        end = message.find(")", start)
        coords = message[start:end].split(", ")
        return float(coords[0]), float(coords[1])
    except Exception:
        return 0.0, 0.0


def is_button_response(message: str) -> bool:
    """Check if message is a button click response."""
    return "[Button clicked:" in message


def is_list_response(message: str) -> bool:
    """Check if message is a list selection response."""
    return "[List selection:" in message


def is_location_response(message: str) -> bool:
    """Check if message is a location share response."""
    return "[Location shared:" in message


def is_contact_response(message: str) -> bool:
    """Check if message is a contact share response."""
    return "[Contact(s) shared:" in message
