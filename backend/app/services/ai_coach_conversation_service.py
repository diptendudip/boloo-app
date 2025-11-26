"""
AI Coach Conversation Service for multi-turn interactions.

Manages conversation sessions, turns, and completeness tracking for the AI Coach
training mode system.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.conversation_turn import ConversationTurn
from app.models.user import User
from app.models.case import Case

logger = logging.getLogger(__name__)


class AICoachConversationServiceError(Exception):
    """Base exception for AI Coach conversation service errors"""
    pass


class AICoachConversationService:
    """
    Manages AI Coach conversation sessions and turns.

    Handles:
    - Creating new conversation sessions
    - Adding conversation turns
    - Updating completeness scores
    - Completing conversations
    - Retrieving conversation history
    """

    def __init__(self, db: Session):
        """
        Initialize AI Coach conversation service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.max_turns = None  # No turn limit for chat-based conversation

    def create_conversation(
        self,
        user_id: uuid.UUID,
        case_id: Optional[uuid.UUID] = None
    ) -> Conversation:
        """
        Create a new conversation session.

        Args:
            user_id: User UUID
            case_id: Optional associated case UUID

        Returns:
            Newly created Conversation instance
        """
        conversation = Conversation(
            id=uuid.uuid4(),
            user_id=user_id,
            case_id=case_id,
            turn_count=0,
            is_complete=False,
            completeness_score=0.0,
            collected_fields=[],
            missing_fields=[],
            created_at=datetime.utcnow()
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        logger.info(f"Created AI Coach conversation {conversation.id} for user {user_id}")
        return conversation

    def add_turn(
        self,
        conversation_id: uuid.UUID,
        transcript_text: str,
        audio_url: Optional[str] = None,
        language_detected: Optional[str] = None,
        ai_prompt: Optional[str] = None,
        ai_response: Optional[str] = None,
        ai_question_asked: Optional[str] = None,
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
        fields_extracted: Optional[Dict[str, Any]] = None
    ) -> ConversationTurn:
        """
        Add a new turn to the conversation.

        Args:
            conversation_id: Conversation UUID
            transcript_text: Transcribed text from user
            audio_url: Optional URL to audio recording
            language_detected: Detected language (hi/en)
            ai_prompt: Prompt sent to AI
            ai_response: AI's response
            ai_question_asked: Follow-up question asked by AI
            intent: Detected intent
            confidence: Confidence score
            fields_extracted: Extracted field data

        Returns:
            Newly created ConversationTurn instance
        """
        # Get conversation
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            raise AICoachConversationServiceError(f"Conversation {conversation_id} not found")

        # Increment turn count
        conversation.turn_count += 1
        turn_number = conversation.turn_count

        # Create turn
        turn = ConversationTurn(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            turn_number=turn_number,
            audio_url=audio_url,
            transcript_text=transcript_text,
            language_detected=language_detected,
            ai_prompt=ai_prompt,
            ai_response=ai_response,
            ai_question_asked=ai_question_asked,
            intent=intent,
            confidence=confidence,
            fields_extracted=fields_extracted or {},
            created_at=datetime.utcnow()
        )

        self.db.add(turn)
        self.db.commit()
        self.db.refresh(turn)

        logger.info(
            f"Added turn {turn_number} to AI Coach conversation {conversation_id}"
        )

        return turn

    def update_completeness(
        self,
        conversation_id: uuid.UUID,
        completeness_score: float,
        collected_fields: List[str],
        missing_fields: List[Dict[str, Any]],
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Update conversation completeness information.

        STATEFUL: Stores merged extracted data from all turns.

        Args:
            conversation_id: Conversation UUID
            completeness_score: Completeness score (0.0-1.0)
            collected_fields: List of field names that have been collected
            missing_fields: List of missing field dictionaries
            extracted_data: Merged extracted data (old + new fields)

        Returns:
            Updated Conversation instance
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            raise AICoachConversationServiceError(f"Conversation {conversation_id} not found")

        conversation.completeness_score = completeness_score
        conversation.collected_fields = collected_fields
        conversation.missing_fields = missing_fields

        # Store merged extracted data (critical for stateful conversation)
        if extracted_data is not None:
            conversation.extracted_data = extracted_data
            logger.info(f"Updated extracted_data for conversation {conversation_id}: {list(extracted_data.keys())}")

        # Check if complete
        if completeness_score >= 0.8:
            conversation.is_complete = True
            if not conversation.completed_at:
                conversation.completed_at = datetime.utcnow()
                logger.info(f"AI Coach conversation {conversation_id} marked complete")

        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    def complete_conversation(
        self,
        conversation_id: uuid.UUID
    ) -> Conversation:
        """
        Mark conversation as complete.

        This can be called when:
        - Completeness threshold reached (>= 0.8)
        - Max turns reached
        - User manually completes

        Args:
            conversation_id: Conversation UUID

        Returns:
            Updated Conversation instance
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            raise AICoachConversationServiceError(f"Conversation {conversation_id} not found")

        if conversation.is_complete:
            logger.warning(f"AI Coach conversation {conversation_id} already complete")
            return conversation

        conversation.is_complete = True
        conversation.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(conversation)

        logger.info(
            f"Completed AI Coach conversation {conversation_id} "
            f"with {conversation.turn_count} turns"
        )

        return conversation

    def get_conversation(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        """
        Get conversation by ID with all turns loaded.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Conversation instance or None if not found
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        return conversation

    def get_user_conversations(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
        include_incomplete: bool = True
    ) -> List[Conversation]:
        """
        Get user's conversation history.

        Args:
            user_id: User UUID
            limit: Maximum number of conversations to return
            include_incomplete: Whether to include incomplete conversations

        Returns:
            List of Conversation instances
        """
        query = self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        )

        if not include_incomplete:
            query = query.filter(Conversation.is_complete == True)

        conversations = query.order_by(
            Conversation.created_at.desc()
        ).limit(limit).all()

        logger.debug(f"Found {len(conversations)} AI Coach conversations for user {user_id}")
        return conversations

    def get_conversation_history_for_ai(
        self,
        conversation_id: uuid.UUID
    ) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for AI context.

        Returns previous turns in a format suitable for passing to
        completeness analyzer or AI services.

        Args:
            conversation_id: Conversation UUID

        Returns:
            List of dicts with 'user' and 'ai' keys
        """
        conversation = self.get_conversation(conversation_id)

        if not conversation:
            return []

        history = []
        for turn in conversation.turns:
            history.append({
                "user": turn.transcript_text,
                "ai": turn.ai_question_asked or turn.ai_response or ""
            })

        return history

    def should_continue_conversation(
        self,
        conversation_id: uuid.UUID
    ) -> bool:
        """
        Determine if conversation should continue with follow-up questions.

        Args:
            conversation_id: Conversation UUID

        Returns:
            True if should ask follow-up, False if should end

        Logic:
            - Don't continue if completeness >= 0.8
            - Continue otherwise (no turn limit for chat-based conversation)
        """
        conversation = self.get_conversation(conversation_id)

        if not conversation:
            raise AICoachConversationServiceError(f"Conversation {conversation_id} not found")

        # Check if complete
        if conversation.is_complete or conversation.completeness_score >= 0.8:
            logger.debug(f"AI Coach conversation {conversation_id} complete, not continuing")
            return False

        logger.debug(f"AI Coach conversation {conversation_id} should continue")
        return True

    def generate_greeting(self, language: str = "hi") -> Dict[str, str]:
        """
        Generate greeting message for new conversation.

        Args:
            language: Language code (hi/en)

        Returns:
            Dict with 'hi' and 'en' greeting messages
        """
        greetings = {
            "hi": "नमस्ते! मैं आपकी मदद के लिए यहाँ हूँ। कृपया अपनी समस्या के बारे में विस्तार से बताएं - क्या हुआ, कहाँ हुआ, कब हुआ, और इससे किसे प्रभावित हुआ?",
            "en": "Hello! I'm here to help you. Please tell me about your issue in detail - what happened, where it happened, when it happened, and who was affected?"
        }

        logger.info(f"Generated greeting in {language}")
        return greetings

    def generate_summary_confirmation(
        self,
        conversation_id: uuid.UUID,
        case_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate summary confirmation message before submission.

        Args:
            conversation_id: Conversation UUID
            case_details: Optional case details for summary

        Returns:
            Dict with 'hi' and 'en' summary messages
        """
        conversation = self.get_conversation(conversation_id)

        if not conversation:
            raise AICoachConversationServiceError(f"Conversation {conversation_id} not found")

        # Build summary from conversation history
        collected = conversation.collected_fields or []
        missing = conversation.missing_fields or []

        # Generate summary messages
        summary_hi = "मैंने आपकी जानकारी एकत्र की है:\n\n"
        summary_en = "I have collected your information:\n\n"

        # Add collected fields
        if collected:
            summary_hi += "✅ प्राप्त जानकारी: " + ", ".join(collected) + "\n\n"
            summary_en += "✅ Collected information: " + ", ".join(collected) + "\n\n"

        # Add missing fields if any
        if missing:
            summary_hi += "⚠️ अधिक जानकारी की आवश्यकता: "
            summary_en += "⚠️ Additional information needed: "
            missing_names = [m.get('field', '') for m in missing if isinstance(m, dict)]
            summary_hi += ", ".join(missing_names) + "\n\n"
            summary_en += ", ".join(missing_names) + "\n\n"

        # Add confirmation prompt
        summary_hi += "क्या यह जानकारी सही है और मैं इसे जमा कर दूं?"
        summary_en += "Is this information correct and should I submit it?"

        logger.info(f"Generated summary confirmation for conversation {conversation_id}")

        return {
            "hi": summary_hi,
            "en": summary_en
        }

    def get_active_conversation_for_user(
        self,
        user_id: uuid.UUID
    ) -> Optional[Conversation]:
        """
        Get user's most recent incomplete conversation, if any.

        Args:
            user_id: User UUID

        Returns:
            Active Conversation or None
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_complete == False
        ).order_by(Conversation.created_at.desc()).first()

        if conversation:
            logger.debug(f"Found active AI Coach conversation {conversation.id} for user {user_id}")
        else:
            logger.debug(f"No active AI Coach conversation for user {user_id}")

        return conversation


def get_ai_coach_conversation_service(db: Session) -> AICoachConversationService:
    """
    Factory function to create AICoachConversationService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        AICoachConversationService instance
    """
    return AICoachConversationService(db)
