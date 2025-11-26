"""
ConversationTurn model for individual turns in AI Coach conversations
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_number = Column(Integer, nullable=False)

    # Audio and transcription
    audio_url = Column(String(1000), nullable=True)
    transcript_text = Column(Text, nullable=False)
    language_detected = Column(String(10), nullable=True)

    # AI response
    ai_prompt = Column(Text, nullable=True)
    ai_response = Column(Text, nullable=True)
    ai_question_asked = Column(Text, nullable=True)

    # Analysis
    intent = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    fields_extracted = Column(JSONB, nullable=True)  # {field_name: value}

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="turns")

    # Constraints
    __table_args__ = (
        UniqueConstraint('conversation_id', 'turn_number', name='uq_conversation_turn'),
    )

    def __repr__(self):
        return f"<ConversationTurn {self.id} conv={self.conversation_id} turn={self.turn_number}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "turn_number": self.turn_number,
            "audio_url": self.audio_url,
            "transcript_text": self.transcript_text,
            "language_detected": self.language_detected,
            "ai_prompt": self.ai_prompt,
            "ai_response": self.ai_response,
            "ai_question_asked": self.ai_question_asked,
            "intent": self.intent,
            "confidence": self.confidence,
            "fields_extracted": self.fields_extracted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
