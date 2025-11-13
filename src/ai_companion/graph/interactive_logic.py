"""Intelligent logic for deciding when and what interactive messages to send.

This module analyzes conversation context and user intent to automatically
determine the most appropriate interactive message type.
"""

from typing import Optional, Dict, List
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_reply_buttons,
    create_list_message,
    create_location_request,
    create_yes_no_buttons,
    create_confirmation_buttons,
)


class InteractiveMessageDecider:
    """Decides when and what type of interactive message to send."""

    # Keywords that suggest binary choices
    BINARY_KEYWORDS = [
        "yes or no", "true or false", "agree or disagree",
        "do you want", "would you like", "are you",
        "can you", "will you", "should i"
    ]

    # Keywords that suggest confirmation is needed
    CONFIRMATION_KEYWORDS = [
        "confirm", "verify", "sure", "certain", "proceed",
        "go ahead", "continue with", "finalize"
    ]

    # Keywords that suggest multiple choice
    CHOICE_KEYWORDS = [
        "choose", "select", "pick", "prefer", "which",
        "option", "alternative"
    ]

    # Keywords that suggest showing a list/menu
    LIST_KEYWORDS = [
        "menu", "list", "show me", "what are", "catalog",
        "browse", "see all", "options", "available",
        "topics", "subjects", "categories"
    ]

    # Keywords that suggest location is needed
    LOCATION_KEYWORDS = [
        "where", "location", "address", "near me",
        "directions", "find", "closest", "nearby"
    ]

    @classmethod
    def should_use_interactive(cls, user_message: str, ai_context: str = "") -> bool:
        """Determine if interactive message would be appropriate.

        Args:
            user_message: The user's message
            ai_context: Context about what the AI is trying to communicate

        Returns:
            True if interactive message would enhance the experience
        """
        message_lower = user_message.lower()

        # Check if message suggests interactive response
        if any(keyword in message_lower for keyword in cls.BINARY_KEYWORDS):
            return True
        if any(keyword in message_lower for keyword in cls.CONFIRMATION_KEYWORDS):
            return True
        if any(keyword in message_lower for keyword in cls.CHOICE_KEYWORDS):
            return True
        if any(keyword in message_lower for keyword in cls.LIST_KEYWORDS):
            return True

        # Check AI context if provided
        if ai_context:
            context_lower = ai_context.lower()
            if any(keyword in context_lower for keyword in cls.CHOICE_KEYWORDS):
                return True
            if "?" in ai_context and len(ai_context) < 200:
                # Short questions are good candidates for buttons
                return True

        return False

    @classmethod
    def detect_intent(cls, user_message: str) -> str:
        """Detect the user's intent to determine interactive message type.

        Args:
            user_message: The user's message

        Returns:
            Intent type: "binary", "confirmation", "choice", "list", "location", "none"
        """
        message_lower = user_message.lower()

        # Check for location intent first (most specific)
        if any(keyword in message_lower for keyword in cls.LOCATION_KEYWORDS):
            return "location"

        # Check for list/menu intent
        if any(keyword in message_lower for keyword in cls.LIST_KEYWORDS):
            return "list"

        # Check for binary choice
        if any(keyword in message_lower for keyword in cls.BINARY_KEYWORDS):
            return "binary"

        # Check for confirmation
        if any(keyword in message_lower for keyword in cls.CONFIRMATION_KEYWORDS):
            return "confirmation"

        # Check for multiple choice
        if any(keyword in message_lower for keyword in cls.CHOICE_KEYWORDS):
            return "choice"

        return "none"

    @classmethod
    def create_binary_response(cls, question: str) -> Dict:
        """Create yes/no button response.

        Args:
            question: The question to ask

        Returns:
            Interactive component dict
        """
        return create_yes_no_buttons(question)

    @classmethod
    def create_confirmation_response(cls, message: str) -> Dict:
        """Create confirmation button response.

        Args:
            message: The message to confirm

        Returns:
            Interactive component dict
        """
        return create_confirmation_buttons(message)

    @classmethod
    def create_choice_response(
        cls,
        question: str,
        options: List[str],
        header: Optional[str] = None
    ) -> Dict:
        """Create choice button/list response.

        Args:
            question: The question or prompt
            options: List of options (if <=3, uses buttons; if >3, uses list)
            header: Optional header text

        Returns:
            Interactive component dict
        """
        if len(options) <= 3:
            # Use buttons for 3 or fewer options
            buttons = [
                {"id": f"opt_{i}", "title": opt[:20]}
                for i, opt in enumerate(options)
            ]
            return create_reply_buttons(
                body_text=question,
                buttons=buttons,
                header_text=header
            )
        else:
            # Use list for more than 3 options
            sections = [{
                "title": header or "Options",
                "rows": [
                    {
                        "id": f"opt_{i}",
                        "title": opt[:24],
                        "description": opt[24:96] if len(opt) > 24 else ""
                    }
                    for i, opt in enumerate(options[:10])  # Max 10 items
                ]
            }]
            return create_list_message(
                body_text=question,
                sections=sections,
                button_text="Choose Option"
            )

    @classmethod
    def create_tutoring_subject_list(cls) -> Dict:
        """Create subject selection list for tutoring.

        Returns:
            Interactive component dict
        """
        sections = [
            {
                "title": "Mathematics",
                "rows": [
                    {"id": "algebra", "title": "Algebra", "description": "Equations, polynomials, functions"},
                    {"id": "geometry", "title": "Geometry", "description": "Shapes, angles, theorems"},
                    {"id": "calculus", "title": "Calculus", "description": "Derivatives, integrals"},
                    {"id": "statistics", "title": "Statistics", "description": "Data analysis, probability"}
                ]
            },
            {
                "title": "Science",
                "rows": [
                    {"id": "physics", "title": "Physics", "description": "Motion, energy, forces"},
                    {"id": "chemistry", "title": "Chemistry", "description": "Elements, reactions"},
                    {"id": "biology", "title": "Biology", "description": "Life sciences, cells"},
                    {"id": "astronomy", "title": "Astronomy", "description": "Space, planets, stars"}
                ]
            },
            {
                "title": "Languages",
                "rows": [
                    {"id": "english", "title": "English", "description": "Grammar, literature, writing"},
                    {"id": "spanish", "title": "Spanish", "description": "Vocabulary, conversation"},
                    {"id": "french", "title": "French", "description": "Basics, pronunciation"}
                ]
            },
            {
                "title": "Other Subjects",
                "rows": [
                    {"id": "history", "title": "History", "description": "World events, civilizations"},
                    {"id": "geography", "title": "Geography", "description": "Countries, maps, cultures"},
                    {"id": "programming", "title": "Programming", "description": "Python, web development"}
                ]
            }
        ]

        return create_list_message(
            body_text="What would you like to learn today? Choose a subject to get started!",
            sections=sections,
            button_text="Choose Subject",
            header_text="Available Subjects"
        )

    @classmethod
    def create_difficulty_buttons(cls) -> Dict:
        """Create difficulty level selection buttons.

        Returns:
            Interactive component dict
        """
        buttons = [
            {"id": "beginner", "title": "Beginner 🌱"},
            {"id": "intermediate", "title": "Intermediate 📚"},
            {"id": "advanced", "title": "Advanced 🚀"}
        ]

        return create_reply_buttons(
            body_text="What's your current skill level?",
            buttons=buttons,
            header_text="Choose Difficulty",
            footer_text="This helps personalize your lessons"
        )

    @classmethod
    def create_learning_mode_buttons(cls) -> Dict:
        """Create learning mode selection buttons.

        Returns:
            Interactive component dict
        """
        buttons = [
            {"id": "practice", "title": "Practice Problems"},
            {"id": "lesson", "title": "Teach Me"},
            {"id": "quiz", "title": "Take a Quiz"}
        ]

        return create_reply_buttons(
            body_text="How would you like to learn?",
            buttons=buttons,
            header_text="Learning Mode"
        )

    @classmethod
    def extract_options_from_text(cls, text: str) -> Optional[List[str]]:
        """Extract multiple choice options from text.

        Looks for patterns like:
        - "a) option 1, b) option 2, c) option 3"
        - "1. option 1, 2. option 2, 3. option 3"
        - "option 1, option 2, option 3"

        Args:
            text: Text potentially containing options

        Returns:
            List of options if found, None otherwise
        """
        import re

        # Pattern 1: Lettered options (a), b), c))
        pattern1 = r'[a-d]\)\s*([^,]+?)(?:\s*[,;]|\s*$)'
        matches1 = re.findall(pattern1, text, re.IGNORECASE)

        if matches1 and len(matches1) >= 2:
            return [m.strip() for m in matches1]

        # Pattern 2: Numbered options (1., 2., 3.)
        pattern2 = r'\d+\.\s*([^,\n]+?)(?:\s*[,;\n]|\s*$)'
        matches2 = re.findall(pattern2, text)

        if matches2 and len(matches2) >= 2:
            return [m.strip() for m in matches2]

        # Pattern 3: Comma-separated list with "or"
        if " or " in text and text.count(",") >= 1:
            # Split by comma and "or"
            parts = re.split(r',\s*|\s+or\s+', text)
            if len(parts) >= 2 and len(parts) <= 5:
                return [p.strip() for p in parts if p.strip()]

        return None


def should_send_interactive_after_response(response_text: str) -> Optional[Dict]:
    """Check if response warrants a follow-up interactive message.

    This analyzes the AI's response and determines if adding
    interactive buttons/lists would improve the experience.

    Args:
        response_text: The AI's generated response

    Returns:
        Interactive component dict if appropriate, None otherwise
    """
    response_lower = response_text.lower()

    # Check if response is asking a binary question
    if "?" in response_text:
        # Look for yes/no questions
        if any(phrase in response_lower for phrase in ["do you want", "would you like", "shall i", "should i"]):
            # Extract the question
            sentences = response_text.split("?")
            question = sentences[0].strip() + "?"
            if len(question) < 150:
                return create_yes_no_buttons(question)

        # Look for confirmation questions
        if any(phrase in response_lower for phrase in ["are you sure", "confirm", "ready to"]):
            question = response_text.split("?")[0].strip() + "?"
            if len(question) < 150:
                return create_confirmation_buttons(question)

    # Check if response offers multiple options
    options = InteractiveMessageDecider.extract_options_from_text(response_text)
    if options:
        # Extract the question part (before the options)
        lines = response_text.split("\n")
        question = lines[0] if lines else "Please choose:"
        return InteractiveMessageDecider.create_choice_response(
            question=question,
            options=options
        )

    # Check if response mentions subjects/topics (for tutoring)
    if any(word in response_lower for word in ["subject", "topic", "learn about", "study"]):
        if "?" in response_text:
            return InteractiveMessageDecider.create_tutoring_subject_list()

    # Check if response asks about difficulty
    if any(word in response_lower for word in ["level", "difficulty", "beginner", "advanced"]):
        if "?" in response_text:
            return InteractiveMessageDecider.create_difficulty_buttons()

    return None
