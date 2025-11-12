from datetime import datetime
from typing import Optional

from ai_companion.core.schedules import BUSINESS_HOURS, RESTAURANT_INFO, SPECIAL_OFFERS


class ScheduleContextGenerator:
    """Class to generate context about restaurant status and current offers."""

    @staticmethod
    def _parse_time(time_str: str) -> datetime.time:
        """Parse a time string (e.g., '11:00') into a time object."""
        return datetime.strptime(time_str, "%H:%M").time()

    @classmethod
    def get_current_activity(cls) -> str:
        """Get restaurant's current status (open/closed) and today's special.

        Returns:
            str: Description of current restaurant status and offers
        """
        # Get current time and day of week
        current_datetime = datetime.now()
        current_time = current_datetime.time()
        current_day_name = current_datetime.strftime("%A").lower()

        # Get business hours for today
        hours = BUSINESS_HOURS.get(current_day_name, {})

        # Build restaurant info context
        context = f"Restaurant: {RESTAURANT_INFO['name']}\n"
        context += f"Address: {RESTAURANT_INFO['address']}\n"
        context += f"Phone: {RESTAURANT_INFO['phone']}\n"

        # Check if open
        if hours.get("is_open", False):
            open_time = cls._parse_time(hours["open"])
            close_time = cls._parse_time(hours["close"])

            if open_time <= current_time <= close_time:
                context += f"Status: OPEN (closes at {hours['close']})\n"
            else:
                context += f"Status: CLOSED (opens at {hours['open']})\n"
        else:
            context += "Status: CLOSED today\n"

        # Add delivery/pickup info
        if RESTAURANT_INFO["delivery_available"]:
            context += f"Delivery: Available (${RESTAURANT_INFO['delivery_fee']:.2f} fee, free over ${RESTAURANT_INFO['free_delivery_minimum']:.2f})\n"
        if RESTAURANT_INFO["pickup_available"]:
            context += f"Pickup: Available\n"

        # Add today's special
        if current_day_name in SPECIAL_OFFERS["daily_specials"]:
            context += f"Today's Special: {SPECIAL_OFFERS['daily_specials'][current_day_name]}\n"

        return context
