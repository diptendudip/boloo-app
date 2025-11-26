"""
Conversation model for AI Coach multi-turn interactions
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, ForeignKey, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)

    turn_count = Column(Integer, default=1)
    is_complete = Column(Boolean, default=False)
    completeness_score = Column(Float, default=0.0)

    # Track what fields have been collected
    collected_fields = Column(ARRAY(String), default=[])
    missing_fields = Column(JSONB, default=[])  # Array of {field, importance, prompt_hi, prompt_en}

    # STATEFUL: Store merged extracted data from all turns
    extracted_data = Column(JSONB, default={})  # Merged field values: {field_name: value, ...}

    # Metadata for storing session-specific information (e.g., location confirmation state)
    session_metadata = Column(JSONB, default={})  # Session metadata: {profile_location_available, location_data, etc.}

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    case = relationship("Case", back_populates="conversations")
    turns = relationship("ConversationTurn", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationTurn.turn_number")

    def __repr__(self):
        return f"<Conversation {self.id} user={self.user_id} turns={self.turn_count} complete={self.is_complete}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "case_id": str(self.case_id) if self.case_id else None,
            "turn_count": self.turn_count,
            "is_complete": self.is_complete,
            "completeness_score": self.completeness_score,
            "collected_fields": self.collected_fields,
            "missing_fields": self.missing_fields,
            "extracted_data": self.extracted_data,
            "session_metadata": self.session_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
