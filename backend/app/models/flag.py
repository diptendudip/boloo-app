"""
Flag model for moderation
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Flag(Base):
    __tablename__ = "flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_type = Column(String(50), nullable=False, index=True)  # case, post
    subject_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    reason = Column(String(100), nullable=False)  # duplicate, spam, toxicity, pii_leak
    risk_score = Column(Float, nullable=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="pending", index=True)  # pending, confirmed, dismissed
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    reviewer = relationship("User")

    def __repr__(self):
        return f"<Flag {self.subject_type}:{self.subject_id} - {self.reason}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "subject_type": self.subject_type,
            "subject_id": str(self.subject_id),
            "reason": self.reason,
            "risk_score": self.risk_score,
            "reviewer_id": str(self.reviewer_id) if self.reviewer_id else None,
            "status": self.status,
            "resolution_note": self.resolution_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
