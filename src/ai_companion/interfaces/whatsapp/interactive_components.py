"""WhatsApp Interactive Components Builder.

This module provides utilities to create various WhatsApp interactive message types:
- Reply Buttons (up to 3 buttons)
- List Messages (up to 10 sections, 10 rows each)
- Location Messages (send location)
- Location Request (request user's location)
- Call-to-Action Buttons (phone, URL)
- Single/Multi-product Messages
- Flow Messages
- Polls (single/multiple choice)

Reference: https://developers.facebook.com/docs/whatsapp/cloud-api/messages/interactive-messages
"""

from typing import Dict, List, Optional


def create_reply_buttons(
    body_text: str,
    buttons: List[Dict[str, str]],
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None
) -> Dict:
    """Create reply buttons interactive message (up to 3 buttons).

    Args:
        body_text: Main message text (1-1024 characters)
        buttons: List of button dicts with 'id' and 'title' keys
                 Max 3 buttons, titles up to 20 characters
        header_text: Optional header text (up to 60 characters)
        footer_text: Optional footer text (up to 60 characters)

    Returns:
        Dict with interactive component structure

    Example:
        >>> buttons = [
        ...     {"id": "yes_btn", "title": "Yes"},
        ...     {"id": "no_btn", "title": "No"},
        ...     {"id": "maybe_btn", "title": "Maybe"}
        ... ]
        >>> create_reply_buttons("Do you want to continue?", buttons)
    """
    if len(buttons) > 3:
        raise ValueError("Reply buttons support maximum 3 buttons")

    interactive = {
        "type": "button",
        "body": {"text": body_text},
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": {
                        "id": btn["id"],
                        "title": btn["title"][:20]  # Truncate to 20 chars
                    }
                }
                for btn in buttons
            ]
        }
    }

    if header_text:
        interactive["header"] = {"type": "text", "text": header_text[:60]}

    if footer_text:
        interactive["footer"] = {"text": footer_text[:60]}

    return interactive


def create_list_message(
    body_text: str,
    sections: List[Dict],
    button_text: str = "Choose an option",
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None
) -> Dict:
    """Create list message interactive component.

    Args:
        body_text: Main message text (1-1024 characters)
        sections: List of section dicts with 'title' and 'rows' keys
                  Max 10 sections, each with max 10 rows
        button_text: Text for the list button (1-20 characters)
        header_text: Optional header text (up to 60 characters)
        footer_text: Optional footer text (up to 60 characters)

    Returns:
        Dict with interactive component structure

    Example:
        >>> sections = [
        ...     {
        ...         "title": "Main Courses",
        ...         "rows": [
        ...             {"id": "pizza", "title": "Pizza", "description": "Classic Margherita"},
        ...             {"id": "burger", "title": "Burger", "description": "Beef burger"}
        ...         ]
        ...     },
        ...     {
        ...         "title": "Desserts",
        ...         "rows": [
        ...             {"id": "cake", "title": "Cake", "description": "Chocolate cake"}
        ...         ]
        ...     }
        ... ]
        >>> create_list_message("Our menu:", sections, "View Menu")
    """
    if len(sections) > 10:
        raise ValueError("List messages support maximum 10 sections")

    # Validate and format sections
    formatted_sections = []
    for section in sections:
        rows = section.get("rows", [])
        if len(rows) > 10:
            rows = rows[:10]  # Truncate to 10 rows

        formatted_rows = [
            {
                "id": row["id"],
                "title": row["title"][:24],  # Max 24 chars
                "description": row.get("description", "")[:72]  # Max 72 chars
            }
            for row in rows
        ]

        formatted_sections.append({
            "title": section.get("title", "Options")[:24],
            "rows": formatted_rows
        })

    interactive = {
        "type": "list",
        "body": {"text": body_text},
        "action": {
            "button": button_text[:20],
            "sections": formatted_sections
        }
    }

    if header_text:
        interactive["header"] = {"type": "text", "text": header_text[:60]}

    if footer_text:
        interactive["footer"] = {"text": footer_text[:60]}

    return interactive


def create_location_message(
    latitude: float,
    longitude: float,
    name: Optional[str] = None,
    address: Optional[str] = None
) -> Dict:
    """Create a location message to send a specific location.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        name: Optional location name
        address: Optional location address

    Returns:
        Dict with location message structure

    Example:
        >>> create_location_message(37.7749, -122.4194, "San Francisco", "CA, USA")
    """
    message = {
        "latitude": latitude,
        "longitude": longitude
    }

    if name:
        message["name"] = name

    if address:
        message["address"] = address

    return message


def create_location_request(body_text: str) -> Dict:
    """Create a location request interactive message.

    This requests the user to share their location.

    Args:
        body_text: Message asking for location (1-1024 characters)

    Returns:
        Dict with interactive component structure

    Example:
        >>> create_location_request("Please share your location for delivery")
    """
    return {
        "type": "location_request_message",
        "body": {"text": body_text},
        "action": {
            "name": "send_location"
        }
    }


def create_cta_url_button(
    body_text: str,
    button_text: str,
    url: str,
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None
) -> Dict:
    """Create Call-to-Action URL button.

    Args:
        body_text: Main message text (1-1024 characters)
        button_text: Button text (1-20 characters)
        url: URL to open (must be valid URL)
        header_text: Optional header text
        footer_text: Optional footer text

    Returns:
        Dict with interactive component structure

    Example:
        >>> create_cta_url_button(
        ...     "Check our website!",
        ...     "Visit Site",
        ...     "https://example.com"
        ... )
    """
    interactive = {
        "type": "cta_url",
        "body": {"text": body_text},
        "action": {
            "name": "cta_url",
            "parameters": {
                "display_text": button_text[:20],
                "url": url
            }
        }
    }

    if header_text:
        interactive["header"] = {"type": "text", "text": header_text[:60]}

    if footer_text:
        interactive["footer"] = {"text": footer_text[:60]}

    return interactive


def create_cta_phone_button(
    body_text: str,
    button_text: str,
    phone_number: str,
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None
) -> Dict:
    """Create Call-to-Action phone call button.

    Args:
        body_text: Main message text (1-1024 characters)
        button_text: Button text (1-20 characters)
        phone_number: Phone number with country code (e.g., "+1234567890")
        header_text: Optional header text
        footer_text: Optional footer text

    Returns:
        Dict with interactive component structure

    Example:
        >>> create_cta_phone_button(
        ...     "Call us for support!",
        ...     "Call Now",
        ...     "+1234567890"
        ... )
    """
    interactive = {
        "type": "cta_call",
        "body": {"text": body_text},
        "action": {
            "name": "cta_call",
            "parameters": {
                "display_text": button_text[:20],
                "phone_number": phone_number
            }
        }
    }

    if header_text:
        interactive["header"] = {"type": "text", "text": header_text[:60]}

    if footer_text:
        interactive["footer"] = {"text": footer_text[:60]}

    return interactive


def create_poll(
    poll_question: str,
    options: List[str],
    allow_multiple_answers: bool = False
) -> Dict:
    """Create a poll message.

    Note: Polls are only supported in groups, not in individual chats.

    Args:
        poll_question: The poll question (1-255 characters)
        options: List of poll options (2-12 options, each 1-100 characters)
        allow_multiple_answers: Whether to allow multiple selections

    Returns:
        Dict with poll message structure

    Example:
        >>> create_poll(
        ...     "What's your favorite cuisine?",
        ...     ["Italian", "Chinese", "Mexican", "Japanese"],
        ...     allow_multiple_answers=True
        ... )
    """
    if len(options) < 2 or len(options) > 12:
        raise ValueError("Polls must have between 2 and 12 options")

    return {
        "name": poll_question[:255],
        "options": [opt[:100] for opt in options],
        "selectableCount": len(options) if allow_multiple_answers else 1
    }


def create_contact_message(
    contacts: List[Dict[str, any]]
) -> Dict:
    """Create a contact message to share contact(s).

    Args:
        contacts: List of contact dictionaries with details

    Returns:
        Dict with contact message structure

    Example:
        >>> contacts = [{
        ...     "name": {"formatted_name": "John Doe", "first_name": "John"},
        ...     "phones": [{"phone": "+1234567890", "type": "CELL"}],
        ...     "emails": [{"email": "john@example.com", "type": "WORK"}]
        ... }]
        >>> create_contact_message(contacts)
    """
    return {"contacts": contacts}


def create_address_message(
    street: str,
    city: str,
    state: str,
    zip_code: str,
    country: str,
    country_code: str = "US"
) -> Dict:
    """Create an address object for contact messages.

    Args:
        street: Street address
        city: City name
        state: State/province
        zip_code: ZIP/postal code
        country: Country name
        country_code: Two-letter country code

    Returns:
        Dict with address structure
    """
    return {
        "street": street,
        "city": city,
        "state": state,
        "zip": zip_code,
        "country": country,
        "country_code": country_code,
        "type": "WORK"
    }


# Helper functions for common use cases

def create_yes_no_buttons(question: str) -> Dict:
    """Quick helper to create Yes/No buttons.

    Args:
        question: The question to ask

    Returns:
        Interactive component with Yes/No buttons
    """
    buttons = [
        {"id": "yes", "title": "Yes ✓"},
        {"id": "no", "title": "No ✗"}
    ]
    return create_reply_buttons(question, buttons)


def create_confirmation_buttons(message: str) -> Dict:
    """Quick helper to create Confirm/Cancel buttons.

    Args:
        message: The confirmation message

    Returns:
        Interactive component with Confirm/Cancel buttons
    """
    buttons = [
        {"id": "confirm", "title": "Confirm ✓"},
        {"id": "cancel", "title": "Cancel ✗"}
    ]
    return create_reply_buttons(message, buttons)


def create_rating_buttons(prompt: str = "How would you rate your experience?") -> Dict:
    """Quick helper to create rating buttons (1-3 stars).

    Args:
        prompt: The rating prompt

    Returns:
        Interactive component with rating buttons
    """
    buttons = [
        {"id": "rating_1", "title": "⭐"},
        {"id": "rating_2", "title": "⭐⭐"},
        {"id": "rating_3", "title": "⭐⭐⭐"}
    ]
    return create_reply_buttons(prompt, buttons)
