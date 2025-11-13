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
        "go ahead", "continue with", "finalize",
        "reset memory", "memory reset", "clear memory", "forget everything", "wipe memory"
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

    # Keywords that suggest quiz/assessment
    QUIZ_KEYWORDS = [
        "quiz", "test", "question", "exam", "assessment",
        "evaluate", "check understanding", "multiple choice"
    ]

    # Keywords that suggest course/lesson content
    COURSE_KEYWORDS = [
        "course", "lesson", "module", "chapter", "section",
        "learn", "study", "teach", "explain", "tutorial"
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
    def create_quiz_buttons(
        cls,
        question: str,
        options: List[str],
        header: Optional[str] = None
    ) -> Dict:
        """Create interactive buttons for quiz questions.

        Args:
            question: The quiz question text
            options: List of answer options (2-3 for buttons, 4+ for list)
            header: Optional header text

        Returns:
            Interactive component dict with buttons or list
        """
        # Check if any option exceeds 20 characters - if so, use list instead of buttons
        max_option_length = max(len(opt.strip()) for opt in options) if options else 0

        if len(options) <= 3 and max_option_length <= 20:
            # Use buttons only if we have ≤3 options AND all fit within 20 chars
            buttons = [
                {"id": f"quiz_ans_{i}", "title": opt.strip()}
                for i, opt in enumerate(options)
            ]
            return create_reply_buttons(
                body_text=question,
                buttons=buttons,
                header_text=header or "Quiz Question"
            )
        else:
            # Use list for 4+ options OR if any option is too long
            sections = [{
                "title": "Answer Options",
                "rows": [
                    {
                        "id": f"quiz_ans_{i}",
                        "title": opt.strip()[:24],
                        "description": opt.strip()[24:96] if len(opt.strip()) > 24 else ""
                    }
                    for i, opt in enumerate(options[:10])
                ]
            }]
            return create_list_message(
                body_text=question,
                sections=sections,
                button_text="Choose Answer",
                header_text=header or "Quiz Question"
            )

    @classmethod
    def create_lesson_navigation_buttons(
        cls,
        lesson_number: Optional[int] = None,
        total_lessons: Optional[int] = None,
        include_menu: bool = True
    ) -> Dict:
        """Create navigation buttons for course lessons.

        Args:
            lesson_number: Current lesson number (optional)
            total_lessons: Total number of lessons (optional)
            include_menu: Whether to include "Back to Menu" button

        Returns:
            Interactive component dict with navigation buttons
        """
        buttons = []

        # Add "Next Lesson" button if not at the end
        if total_lessons is None or lesson_number is None or lesson_number < total_lessons:
            buttons.append({"id": "next_lesson", "title": "Next Lesson ▶️"})

        # Add "Previous Lesson" if not at the beginning
        if lesson_number and lesson_number > 1:
            buttons.append({"id": "prev_lesson", "title": "◀️ Previous"})

        # Add "Menu" button if requested
        if include_menu and len(buttons) < 3:
            buttons.append({"id": "course_menu", "title": "📚 Menu"})

        # Ensure we have at least 1 button and at most 3
        if not buttons:
            buttons = [{"id": "course_menu", "title": "Back to Menu"}]
        buttons = buttons[:3]

        body_text = "What would you like to do next?"
        if lesson_number and total_lessons:
            body_text = f"Lesson {lesson_number}/{total_lessons} complete! What next?"

        return create_reply_buttons(
            body_text=body_text,
            buttons=buttons,
            header_text="Navigation"
        )

    @classmethod
    def create_course_list(
        cls,
        courses: List[Dict[str, str]],
        header: str = "Available Courses"
    ) -> Dict:
        """Create interactive list for course selection.

        Args:
            courses: List of course dicts with 'id', 'title', and 'description'
            header: Header text for the list

        Returns:
            Interactive component dict
        """
        # Group courses by category if they have one
        sections = []
        categorized = {}
        uncategorized = []

        for course in courses:
            category = course.get("category", "")
            if category:
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(course)
            else:
                uncategorized.append(course)

        # Create sections for categorized courses
        for category, category_courses in categorized.items():
            sections.append({
                "title": category,
                "rows": [
                    {
                        "id": course["id"],
                        "title": course["title"][:24],
                        "description": course.get("description", "")[:72]
                    }
                    for course in category_courses[:10]
                ]
            })

        # Add uncategorized courses
        if uncategorized:
            sections.append({
                "title": "More Courses",
                "rows": [
                    {
                        "id": course["id"],
                        "title": course["title"][:24],
                        "description": course.get("description", "")[:72]
                    }
                    for course in uncategorized[:10]
                ]
            })

        return create_list_message(
            body_text="Choose a course to get started with your learning journey!",
            sections=sections,
            button_text="Select Course",
            header_text=header
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

        # Pattern 1: Lettered options on separate lines or with commas (a), b), c), d))
        # Match options like "A) answer" or "a) answer" on new lines
        pattern1 = r'^[a-d]\)\s*(.+?)$'
        matches1 = re.findall(pattern1, text, re.IGNORECASE | re.MULTILINE)

        if matches1 and len(matches1) >= 2:
            return [m.strip() for m in matches1]

        # Pattern 2: Numbered options on separate lines (1., 2., 3., 4.)
        pattern2 = r'^\d+\.\s*(.+?)$'
        matches2 = re.findall(pattern2, text, re.MULTILINE)

        if matches2 and len(matches2) >= 2:
            return [m.strip() for m in matches2]

        # Pattern 3: Inline lettered options with commas/semicolons
        pattern3 = r'[a-d]\)\s*([^,;]+?)(?:\s*[,;]|\s*(?=[a-d]\))|$)'
        matches3 = re.findall(pattern3, text, re.IGNORECASE)

        if matches3 and len(matches3) >= 2:
            return [m.strip() for m in matches3]

        # Pattern 4: Comma-separated list with "or"
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

    # PRIORITY 1: Check for quiz questions with multiple choice options
    # Look for quiz patterns like "A)", "B)", "C)" or numbered options
    quiz_patterns = ["a)", "b)", "c)", "d)", "1.", "2.", "3.", "4."]
    quiz_keywords = ["quiz", "question", "answer", "choose", "select", "which of the following"]

    has_quiz_pattern = any(pattern in response_lower for pattern in quiz_patterns)
    has_quiz_keyword = any(keyword in response_lower for keyword in quiz_keywords)

    if has_quiz_pattern or has_quiz_keyword:
        options = InteractiveMessageDecider.extract_options_from_text(response_text)
        if options:
            # Extract the question (everything before the first option)
            lines = response_text.split("\n")
            question_lines = []
            for line in lines:
                # Stop when we hit an option line
                if any(pattern in line.lower() for pattern in quiz_patterns):
                    break
                question_lines.append(line)

            question = "\n".join(question_lines).strip() or "Choose the correct answer:"
            return InteractiveMessageDecider.create_quiz_buttons(
                question=question,
                options=options
            )

    # PRIORITY 2: Check for lesson completion/navigation cues
    navigation_phrases = [
        "next lesson", "continue to", "move on to", "previous lesson",
        "lesson complete", "finished with", "ready for the next"
    ]
    if any(phrase in response_lower for phrase in navigation_phrases):
        # Try to detect lesson numbers
        import re
        lesson_match = re.search(r'lesson\s+(\d+)', response_lower)
        total_match = re.search(r'of\s+(\d+)|/\s*(\d+)', response_lower)

        lesson_num = int(lesson_match.group(1)) if lesson_match else None
        total = int(total_match.group(1) or total_match.group(2)) if total_match else None

        return InteractiveMessageDecider.create_lesson_navigation_buttons(
            lesson_number=lesson_num,
            total_lessons=total
        )

    # PRIORITY 3: Check if response is asking a binary question
    if "?" in response_text:
        # Look for yes/no questions (expanded list)
        yes_no_phrases = [
            "do you want", "would you like", "shall i", "should i",
            "can i help", "need help", "want me to", "shall we",
            "ready to", "interested in"
        ]
        if any(phrase in response_lower for phrase in yes_no_phrases):
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

    # PRIORITY 4: Check if response offers multiple options (generic)
    options = InteractiveMessageDecider.extract_options_from_text(response_text)
    if options:
        # Extract the question part (before the options)
        lines = response_text.split("\n")
        question = lines[0] if lines else "Please choose:"
        return InteractiveMessageDecider.create_choice_response(
            question=question,
            options=options
        )

    # PRIORITY 5: Check if response mentions subjects/topics (for tutoring)
    if any(word in response_lower for word in ["subject", "topic", "learn about", "study"]):
        if "?" in response_text:
            return InteractiveMessageDecider.create_tutoring_subject_list()

    # PRIORITY 6: Check if response asks about difficulty
    if any(word in response_lower for word in ["level", "difficulty", "beginner", "advanced"]):
        if "?" in response_text:
            return InteractiveMessageDecider.create_difficulty_buttons()

    # PRIORITY 7: Check if response asks about learning mode
    if any(word in response_lower for word in ["how would you like to learn", "learning mode", "practice or quiz"]):
        if "?" in response_text:
            return InteractiveMessageDecider.create_learning_mode_buttons()

    return None
