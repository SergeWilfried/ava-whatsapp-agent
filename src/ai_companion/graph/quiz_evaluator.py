"""Quiz evaluation and management system.

This module handles quiz answer validation, scoring, and progression logic.
"""

from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class QuizQuestion:
    """Represents a single quiz question."""
    question: str
    options: List[str]
    correct_answer_index: int
    explanation: Optional[str] = None
    topic: Optional[str] = None


@dataclass
class QuizSession:
    """Represents an active quiz session."""
    questions: List[QuizQuestion]
    current_question_index: int = 0
    score: int = 0
    answers: List[Tuple[int, bool]] = None  # (selected_index, is_correct)
    started_at: Optional[datetime] = None

    def __post_init__(self):
        if self.answers is None:
            self.answers = []
        if self.started_at is None:
            self.started_at = datetime.now()

    @property
    def current_question(self) -> Optional[QuizQuestion]:
        """Get the current question."""
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None

    @property
    def is_complete(self) -> bool:
        """Check if quiz is complete."""
        return self.current_question_index >= len(self.questions)

    @property
    def progress(self) -> str:
        """Get progress string."""
        return f"{self.current_question_index + 1}/{len(self.questions)}"

    @property
    def percentage_score(self) -> float:
        """Get percentage score."""
        if not self.questions:
            return 0.0
        return (self.score / len(self.questions)) * 100


class QuizEvaluator:
    """Handles quiz answer evaluation and progression."""

    # In-memory storage for active quiz sessions (user_id -> QuizSession)
    # In production, this should use Redis or database
    active_sessions: Dict[str, QuizSession] = {}

    @classmethod
    def start_quiz(
        cls,
        user_id: str,
        questions: List[QuizQuestion]
    ) -> QuizSession:
        """Start a new quiz session.

        Args:
            user_id: Unique user identifier
            questions: List of quiz questions

        Returns:
            New QuizSession instance
        """
        session = QuizSession(questions=questions)
        cls.active_sessions[user_id] = session
        return session

    @classmethod
    def get_session(cls, user_id: str) -> Optional[QuizSession]:
        """Get active quiz session for user.

        Args:
            user_id: Unique user identifier

        Returns:
            QuizSession if active, None otherwise
        """
        return cls.active_sessions.get(user_id)

    @classmethod
    def evaluate_answer(
        cls,
        user_id: str,
        selected_index: int
    ) -> Dict:
        """Evaluate user's answer and prepare feedback.

        Args:
            user_id: Unique user identifier
            selected_index: Index of selected answer option

        Returns:
            Dict with evaluation results:
            {
                "is_correct": bool,
                "correct_answer": str,
                "selected_answer": str,
                "explanation": str,
                "score": int,
                "progress": str,
                "is_quiz_complete": bool,
                "percentage": float
            }
        """
        session = cls.get_session(user_id)
        if not session:
            return {
                "error": "No active quiz session found",
                "is_correct": False
            }

        question = session.current_question
        if not question:
            return {
                "error": "No current question",
                "is_correct": False
            }

        # Check if answer is correct
        is_correct = selected_index == question.correct_answer_index

        # Update score
        if is_correct:
            session.score += 1

        # Record answer
        session.answers.append((selected_index, is_correct))

        # Prepare feedback
        result = {
            "is_correct": is_correct,
            "selected_answer": question.options[selected_index] if 0 <= selected_index < len(question.options) else "Invalid",
            "correct_answer": question.options[question.correct_answer_index],
            "explanation": question.explanation or "",
            "score": session.score,
            "total_questions": len(session.questions),
            "progress": session.progress,
            "percentage": session.percentage_score,
            "is_quiz_complete": False
        }

        # Move to next question
        session.current_question_index += 1

        # Check if quiz is complete
        if session.is_complete:
            result["is_quiz_complete"] = True
            result["final_score"] = f"{session.score}/{len(session.questions)}"
            result["final_percentage"] = session.percentage_score
            # Don't end session yet - allow review

        return result

    @classmethod
    def end_session(cls, user_id: str) -> Optional[QuizSession]:
        """End and remove quiz session.

        Args:
            user_id: Unique user identifier

        Returns:
            The ended session, or None if not found
        """
        return cls.active_sessions.pop(user_id, None)

    @classmethod
    def has_active_quiz(cls, user_id: str) -> bool:
        """Check if user has an active quiz session.

        Args:
            user_id: Unique user identifier

        Returns:
            True if active quiz exists
        """
        return user_id in cls.active_sessions

    @classmethod
    def parse_quiz_response(cls, message_content: str) -> Optional[int]:
        """Extract quiz answer index from interactive button response.

        Args:
            message_content: Message content like "[Button clicked: Paris (ID: quiz_ans_1)]"

        Returns:
            Answer index (0-based) or None if not a quiz response
        """
        import re

        # Look for quiz_ans_{index} pattern
        match = re.search(r'quiz_ans_(\d+)', message_content)
        if match:
            return int(match.group(1))

        return None

    @classmethod
    def create_feedback_message(cls, evaluation: Dict) -> str:
        """Create formatted feedback message.

        Args:
            evaluation: Evaluation result dict

        Returns:
            Formatted feedback message
        """
        if evaluation.get("error"):
            return f"Error: {evaluation['error']}"

        is_correct = evaluation["is_correct"]

        # Emoji and feedback based on correctness
        if is_correct:
            emoji = "✅"
            feedback = "Correct! Well done!"
        else:
            emoji = "❌"
            feedback = f"Not quite. The correct answer is: {evaluation['correct_answer']}"

        # Build message
        message_parts = [
            f"{emoji} {feedback}"
        ]

        # Add explanation if available
        if evaluation.get("explanation"):
            message_parts.append(f"\n💡 {evaluation['explanation']}")

        # Add progress
        if not evaluation.get("is_quiz_complete"):
            message_parts.append(f"\n📊 Score: {evaluation['score']}/{evaluation['total_questions']}")

        return "".join(message_parts)

    @classmethod
    def create_completion_message(cls, evaluation: Dict) -> str:
        """Create quiz completion message.

        Args:
            evaluation: Evaluation result dict

        Returns:
            Formatted completion message
        """
        percentage = evaluation["final_percentage"]
        score = evaluation["final_score"]

        # Determine grade emoji
        if percentage >= 90:
            grade_emoji = "🌟"
            grade_text = "Excellent!"
        elif percentage >= 80:
            grade_emoji = "🎉"
            grade_text = "Great job!"
        elif percentage >= 70:
            grade_emoji = "👍"
            grade_text = "Good work!"
        elif percentage >= 60:
            grade_emoji = "📚"
            grade_text = "Not bad!"
        else:
            grade_emoji = "💪"
            grade_text = "Keep practicing!"

        return (
            f"{grade_emoji} Quiz Complete! {grade_text}\n\n"
            f"Final Score: {score} ({percentage:.0f}%)\n\n"
            f"Ready for the next lesson?"
        )
