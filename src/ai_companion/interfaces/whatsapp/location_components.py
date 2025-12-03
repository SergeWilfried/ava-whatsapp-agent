"""
Location message components for WhatsApp Business API.

This module provides helper functions to create location-related message payloads
for sending locations and requesting user locations.
"""

from typing import Optional


def create_location_request_component(body_text: str) -> dict:
    """
    Create an interactive component to request user's location.

    This creates a location_request_message interactive type that displays
    a "Send Location" button to the user. When tapped, it opens WhatsApp's
    location sharing interface.

    Args:
        body_text: Message asking for location. Supports URLs and markdown.
                  Maximum 1024 characters.
                  Example: "📍 Please share your delivery location"

    Returns:
        dict: Interactive component structure for location request

    Example:
        >>> component = create_location_request_component(
        ...     "Please share your location for delivery"
        ... )
        >>> # Use in send_response with message_type="interactive"
    """
    return {
        "type": "location_request_message",
        "body": {
            "text": body_text
        },
        "action": {
            "name": "send_location"
        }
    }


def create_location_message_payload(
    latitude: float,
    longitude: float,
    name: Optional[str] = None,
    address: Optional[str] = None
) -> dict:
    """
    Create a location message payload for sending a specific location.

    Sends a location pin that users can tap to view in their maps app.

    Args:
        latitude: Latitude in decimal degrees (e.g., 37.4847)
        longitude: Longitude in decimal degrees (e.g., -122.1486)
        name: Optional location name (e.g., "Meta HQ")
        address: Optional address (e.g., "1 Hacker Way, Menlo Park, CA 94025")

    Returns:
        dict: Location object for WhatsApp message payload

    Example:
        >>> location = create_location_message_payload(
        ...     latitude=37.4847,
        ...     longitude=-122.1486,
        ...     name="Meta HQ",
        ...     address="1 Hacker Way, Menlo Park, CA"
        ... )
    """
    location_data = {
        "latitude": str(latitude),
        "longitude": str(longitude)
    }

    if name:
        location_data["name"] = name

    if address:
        location_data["address"] = address

    return location_data


def format_location_for_display(
    latitude: float,
    longitude: float,
    name: Optional[str] = None,
    address: Optional[str] = None
) -> str:
    """
    Format location data into a human-readable string.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        name: Optional location name
        address: Optional address

    Returns:
        str: Formatted location string for display

    Example:
        >>> format_location_for_display(37.4847, -122.1486, "Meta HQ")
        "📍 Meta HQ (37.4847, -122.1486)"
    """
    parts = ["📍"]

    if name:
        parts.append(name)

    if address:
        parts.append(f"- {address}")

    parts.append(f"({latitude}, {longitude})")

    return " ".join(parts)
