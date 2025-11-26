"""
Question Tracking Utility

Tracks which questions have been asked in a conversation to prevent infinite loops.
Fixes Bug #1: System asking same question multiple times.
"""

from typing import Dict, List, Optional, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class QuestionTracker:
    """Tracks questions asked during a conversation"""

    def __init__(self):
        """Initialize empty question tracker"""
        self.questions_asked: Dict[str, List[Dict]] = {}  # field_name -> [{"question": str, "timestamp": datetime, "turn": int}]
        self.fields_asked_about: Set[str] = set()

    def add_question(self, field_name: str, question_text: str, turn_number: int):
        """
        Record that a question was asked about a specific field.

        Args:
            field_name: The field being asked about (e.g., "service_duration")
            question_text: The actual question text
            turn_number: Conversation turn number
        """
        if field_name not in self.questions_asked:
            self.questions_asked[field_name] = []

        self.questions_asked[field_name].append({
            "question": question_text,
            "timestamp": datetime.utcnow(),
            "turn": turn_number
        })

        self.fields_asked_about.add(field_name)

        logger.info(f"[QuestionTracker] Recorded question about '{field_name}' at turn {turn_number}")

    def has_been_asked(self, field_name: str, max_times: int = 1) -> bool:
        """
        Check if a field has already been asked about.

        Args:
            field_name: Field to check
            max_times: Maximum times a field can be asked (default 1)

        Returns:
            True if field has been asked >= max_times
        """
        if field_name not in self.questions_asked:
            return False

        times_asked = len(self.questions_asked[field_name])
        if times_asked >= max_times:
            logger.warning(f"[QuestionTracker] Field '{field_name}' already asked {times_asked} times (max {max_times})")
            return True

        return False

    def get_question_count(self, field_name: str) -> int:
        """Get number of times a field has been asked about"""
        return len(self.questions_asked.get(field_name, []))

    def should_skip_field(self, field_name: str) -> bool:
        """
        Determine if a field should be skipped (already asked once).

        Returns:
            True if field should be skipped
        """
        return self.has_been_asked(field_name, max_times=1)

    def get_all_asked_fields(self) -> Set[str]:
        """Get set of all fields that have been asked about"""
        return self.fields_asked_about.copy()

    def get_last_question(self, field_name: str) -> Optional[Dict]:
        """Get the last question asked about a field"""
        if field_name not in self.questions_asked or not self.questions_asked[field_name]:
            return None
        return self.questions_asked[field_name][-1]

    def detect_loop(self, recent_fields: List[str], window_size: int = 3) -> bool:
        """
        Detect if we're in a question loop (asking same fields repeatedly).

        Args:
            recent_fields: List of field names in order they were asked
            window_size: Number of recent questions to check

        Returns:
            True if loop detected
        """
        if len(recent_fields) < window_size:
            return False

        recent = recent_fields[-window_size:]
        # If same field appears multiple times in recent window
        if len(recent) != len(set(recent)):
            logger.warning(f"[QuestionTracker] LOOP DETECTED: Recent fields {recent}")
            return True

        return False

    def to_dict(self) -> Dict:
        """Convert to dict for storage/serialization"""
        return {
            "questions_asked": {
                field: [
                    {
                        "question": q["question"],
                        "timestamp": q["timestamp"].isoformat(),
                        "turn": q["turn"]
                    }
                    for q in questions
                ]
                for field, questions in self.questions_asked.items()
            },
            "fields_asked_about": list(self.fields_asked_about)
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "QuestionTracker":
        """Create tracker from dict"""
        tracker = cls()

        for field, questions in data.get("questions_asked", {}).items():
            tracker.questions_asked[field] = [
                {
                    "question": q["question"],
                    "timestamp": datetime.fromisoformat(q["timestamp"]),
                    "turn": q["turn"]
                }
                for q in questions
            ]

        tracker.fields_asked_about = set(data.get("fields_asked_about", []))

        return tracker

    @classmethod
    def from_conversation_history(cls, history: List[Dict[str, str]]) -> "QuestionTracker":
        """
        Create tracker by analyzing conversation history.

        Args:
            history: List of {"user": str, "ai": str} dicts

        Returns:
            QuestionTracker with extracted questions
        """
        tracker = cls()

        # Simple heuristic: detect questions about specific fields from AI messages
        field_indicators = {
            "service_duration": ["कब से", "since when", "how long", "कितने दिन", "कितने महीने"],
            "service_frequency": ["कितने घंटे", "how many hours", "hours per day"],
            "reporter_name": ["आपका नाम", "your name", "name kya"],
            "phone": ["phone", "फोन", "contact", "संपर्क"],
            "severity": ["कितना गंभीर", "how serious", "severity"],
            "affected_count": ["कितने लोग", "how many people", "affected"]
        }

        for turn_idx, turn in enumerate(history, start=1):
            ai_message = turn.get("ai", "").lower()

            for field, indicators in field_indicators.items():
                if any(indicator in ai_message for indicator in indicators):
                    tracker.add_question(field, ai_message, turn_idx)
                    break  # Only count first match per message

        return tracker
