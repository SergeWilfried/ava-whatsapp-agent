"""Information Collection System using Interactive Components.

This module provides intelligent information collection patterns using
WhatsApp interactive components: quick replies, lists, location requests,
and event scheduling.
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_reply_buttons,
    create_list_message,
    create_location_request,
    create_yes_no_buttons,
)


class InformationCollector:
    """Collects user information using interactive components."""

    # Keywords that indicate information is being collected
    ASKING_KEYWORDS = [
        "what is your", "tell me your", "what's your", "your name",
        "your email", "your phone", "your address", "your age",
        "how old", "where do you", "when do you", "which do you"
    ]

    # Keywords for scheduling/events
    SCHEDULING_KEYWORDS = [
        "schedule", "book", "appointment", "meeting", "session",
        "reserve", "reservation", "when can", "available time",
        "prefer", "convenient", "hard stop"
    ]

    # Keywords for location
    LOCATION_KEYWORDS = [
        "where are you", "your location", "your address",
        "where do you live", "delivery address", "pick up location",
        "current location", "send location"
    ]

    # Keywords for preferences/choices
    PREFERENCE_KEYWORDS = [
        "prefer", "like better", "choose between", "pick",
        "which one", "favorite", "would you rather"
    ]

    @classmethod
    def detect_collection_intent(cls, message: str) -> str:
        """Detect what type of information is being collected.

        Args:
            message: The conversation message

        Returns:
            Intent type: "scheduling", "location", "preference", "binary", "text", "none"
        """
        message_lower = message.lower()

        # Check for scheduling/event booking
        if any(keyword in message_lower for keyword in cls.SCHEDULING_KEYWORDS):
            return "scheduling"

        # Check for location request
        if any(keyword in message_lower for keyword in cls.LOCATION_KEYWORDS):
            return "location"

        # Check for preferences/choices
        if any(keyword in message_lower for keyword in cls.PREFERENCE_KEYWORDS):
            return "preference"

        # Check for yes/no questions
        if any(word in message_lower for word in ["yes or no", "do you want", "would you like"]):
            return "binary"

        # Check for general information request
        if any(keyword in message_lower for keyword in cls.ASKING_KEYWORDS):
            return "text"

        return "none"

    @classmethod
    def create_time_slot_list(
        cls,
        title: str = "Choose a time slot",
        date: Optional[datetime] = None,
        duration_minutes: int = 60
    ) -> Dict:
        """Create time slot selection list for scheduling.

        Args:
            title: Title for the selection
            date: Date to show slots for (default: tomorrow)
            duration_minutes: Duration of each slot

        Returns:
            Interactive list component
        """
        if date is None:
            date = datetime.now() + timedelta(days=1)

        # Generate time slots
        morning_slots = []
        afternoon_slots = []
        evening_slots = []

        # Morning slots (9 AM - 12 PM)
        for hour in range(9, 12):
            time_str = f"{hour:02d}:00"
            slot_id = f"{date.strftime('%Y%m%d')}_{hour}00"
            morning_slots.append({
                "id": slot_id,
                "title": f"{time_str} - {hour+1:02d}:00",
                "description": f"{duration_minutes} min session"
            })

        # Afternoon slots (1 PM - 5 PM)
        for hour in range(13, 17):
            time_str = f"{hour:02d}:00"
            slot_id = f"{date.strftime('%Y%m%d')}_{hour}00"
            afternoon_slots.append({
                "id": slot_id,
                "title": f"{time_str} - {hour+1:02d}:00",
                "description": f"{duration_minutes} min session"
            })

        # Evening slots (6 PM - 8 PM)
        for hour in range(18, 20):
            time_str = f"{hour:02d}:00"
            slot_id = f"{date.strftime('%Y%m%d')}_{hour}00"
            evening_slots.append({
                "id": slot_id,
                "title": f"{time_str} - {hour+1:02d}:00",
                "description": f"{duration_minutes} min session"
            })

        sections = []
        if morning_slots:
            sections.append({"title": "Morning ☀️", "rows": morning_slots})
        if afternoon_slots:
            sections.append({"title": "Afternoon 🌤️", "rows": afternoon_slots})
        if evening_slots:
            sections.append({"title": "Evening 🌙", "rows": evening_slots})

        return create_list_message(
            body_text=f"Available time slots for {date.strftime('%B %d, %Y')}:",
            sections=sections,
            button_text="Choose Time",
            header_text=title
        )

    @classmethod
    def create_date_selection_list(
        cls,
        title: str = "Choose a date",
        days_ahead: int = 7
    ) -> Dict:
        """Create date selection list.

        Args:
            title: Title for the selection
            days_ahead: Number of days to show

        Returns:
            Interactive list component
        """
        sections = [{
            "title": "Available Dates",
            "rows": []
        }]

        today = datetime.now()
        for i in range(days_ahead):
            date = today + timedelta(days=i+1)
            day_name = date.strftime("%A")
            date_str = date.strftime("%B %d, %Y")

            sections[0]["rows"].append({
                "id": f"date_{date.strftime('%Y%m%d')}",
                "title": f"{day_name}",
                "description": date_str
            })

        return create_list_message(
            body_text="When would you like to schedule?",
            sections=sections,
            button_text="Select Date",
            header_text=title
        )

    @classmethod
    def create_duration_buttons(cls) -> Dict:
        """Create session duration selection buttons.

        Returns:
            Interactive button component
        """
        buttons = [
            {"id": "duration_30", "title": "30 minutes"},
            {"id": "duration_60", "title": "1 hour"},
            {"id": "duration_90", "title": "1.5 hours"}
        ]

        return create_reply_buttons(
            body_text="How long would you like the session?",
            buttons=buttons,
            header_text="Session Duration"
        )

    @classmethod
    def create_confirmation_with_details(cls, details: Dict[str, str]) -> Dict:
        """Create confirmation buttons with booking details.

        Args:
            details: Dictionary with booking details (date, time, duration, etc.)

        Returns:
            Interactive button component
        """
        details_text = "Please confirm your booking:\n\n"
        for key, value in details.items():
            details_text += f"• {key}: {value}\n"

        buttons = [
            {"id": "confirm_booking", "title": "✓ Confirm"},
            {"id": "cancel_booking", "title": "✗ Cancel"}
        ]

        return create_reply_buttons(
            body_text=details_text,
            buttons=buttons,
            header_text="Booking Confirmation"
        )

    @classmethod
    def create_preference_list(
        cls,
        question: str,
        options: List[Dict[str, str]],
        category: str = "Options"
    ) -> Dict:
        """Create preference selection list.

        Args:
            question: Question to ask
            options: List of options with id, title, description
            category: Category name for the section

        Returns:
            Interactive list component
        """
        sections = [{
            "title": category,
            "rows": options[:10]  # Max 10 items
        }]

        return create_list_message(
            body_text=question,
            sections=sections,
            button_text="Choose",
            header_text="Your Preference"
        )

    @classmethod
    def create_rating_buttons(cls, item: str = "experience") -> Dict:
        """Create rating selection buttons.

        Args:
            item: What is being rated

        Returns:
            Interactive button component
        """
        buttons = [
            {"id": "rating_good", "title": "😊 Good"},
            {"id": "rating_ok", "title": "😐 OK"},
            {"id": "rating_bad", "title": "😞 Not Good"}
        ]

        return create_reply_buttons(
            body_text=f"How would you rate your {item}?",
            buttons=buttons,
            header_text="Quick Feedback"
        )

    @classmethod
    def create_contact_method_buttons(cls) -> Dict:
        """Create contact method selection buttons.

        Returns:
            Interactive button component
        """
        buttons = [
            {"id": "contact_whatsapp", "title": "📱 WhatsApp"},
            {"id": "contact_email", "title": "📧 Email"},
            {"id": "contact_phone", "title": "☎️ Phone Call"}
        ]

        return create_reply_buttons(
            body_text="How would you like us to contact you?",
            buttons=buttons,
            header_text="Contact Preference"
        )

    @classmethod
    def parse_time_slot_id(cls, slot_id: str) -> Dict[str, Any]:
        """Parse time slot ID into components.

        Args:
            slot_id: Slot ID in format "YYYYMMDD_HHMM"

        Returns:
            Dict with date and time components
        """
        try:
            date_part, time_part = slot_id.split("_")
            date = datetime.strptime(date_part, "%Y%m%d")
            hour = int(time_part[:2])
            minute = int(time_part[2:])

            return {
                "date": date,
                "time": f"{hour:02d}:{minute:02d}",
                "datetime": date.replace(hour=hour, minute=minute)
            }
        except Exception:
            return {}

    @classmethod
    def extract_booking_info(cls, conversation_history: List[str]) -> Dict[str, str]:
        """Extract booking information from conversation history.

        Args:
            conversation_history: List of messages in conversation

        Returns:
            Dict with extracted booking details
        """
        booking_info = {}

        for message in conversation_history:
            # Extract date selection
            if "[List selection:" in message and "date_" in message:
                # Extract date ID
                import re
                match = re.search(r'date_(\d{8})', message)
                if match:
                    date_str = match.group(1)
                    date = datetime.strptime(date_str, "%Y%m%d")
                    booking_info["Date"] = date.strftime("%B %d, %Y")

            # Extract time slot
            if "[List selection:" in message and any(x in message for x in ["Morning", "Afternoon", "Evening"]):
                # Extract time from message
                import re
                match = re.search(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})', message)
                if match:
                    booking_info["Time"] = match.group(1)

            # Extract duration
            if "[Button clicked:" in message and "duration_" in message:
                if "30" in message:
                    booking_info["Duration"] = "30 minutes"
                elif "60" in message:
                    booking_info["Duration"] = "1 hour"
                elif "90" in message:
                    booking_info["Duration"] = "1.5 hours"

            # Extract location
            if "[Location shared:" in message:
                import re
                match = re.search(r'at \(([^)]+)\)', message)
                if match:
                    booking_info["Location"] = match.group(1)

        return booking_info


class ConversationContext:
    """Tracks conversation context for multi-step information collection."""

    def __init__(self):
        self.state = "initial"
        self.collected_data = {}
        self.current_step = None

    def update_state(self, new_state: str, data: Dict[str, Any] = None):
        """Update conversation state.

        Args:
            new_state: New state name
            data: Data to store
        """
        self.state = new_state
        if data:
            self.collected_data.update(data)

    def get_next_step(self) -> Optional[str]:
        """Get next step in information collection flow.

        Returns:
            Next step name or None if complete
        """
        # Define collection flow
        flow = {
            "initial": "ask_date",
            "ask_date": "ask_time",
            "ask_time": "ask_duration",
            "ask_duration": "ask_location",
            "ask_location": "confirm",
            "confirm": None
        }

        return flow.get(self.state)

    def is_complete(self) -> bool:
        """Check if information collection is complete.

        Returns:
            True if all required information collected
        """
        required_fields = ["date", "time"]
        return all(field in self.collected_data for field in required_fields)


def create_tutoring_session_flow(step: str, context: Dict = None) -> Dict:
    """Create interactive component for tutoring session booking flow.

    Args:
        step: Current step in the flow
        context: Conversation context with collected data

    Returns:
        Interactive component for the step
    """
    context = context or {}

    if step == "ask_date":
        return InformationCollector.create_date_selection_list(
            title="Schedule Tutoring Session"
        )

    elif step == "ask_time":
        date_str = context.get("date")
        date = datetime.strptime(date_str, "%Y%m%d") if date_str else None
        return InformationCollector.create_time_slot_list(
            title="Choose Time Slot",
            date=date
        )

    elif step == "ask_duration":
        return InformationCollector.create_duration_buttons()

    elif step == "ask_location":
        return create_location_request(
            "Please share your location for the session (or type your address)"
        )

    elif step == "confirm":
        details = InformationCollector.extract_booking_info(
            context.get("messages", [])
        )
        return InformationCollector.create_confirmation_with_details(details)

    return None
