"""
CaseSLATracking model - Tracks SLA and escalations
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class CaseSLATracking(Base):
    __tablename__ = "case_sla_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    responsible_entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=True)
    sla_hours = Column(Integer, nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    escalation_level = Column(Integer, default=0)
    who_has_ball = Column(String(50), nullable=False)  # citizen/moderator/officer/system
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    case = relationship("Case")
    entity = relationship("Entity")

    def __repr__(self):
        return f"<CaseSLATracking {self.case_id} - Level {self.escalation_level}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "case_id": str(self.case_id),
            "responsible_entity_id": str(self.responsible_entity_id) if self.responsible_entity_id else None,
            "sla_hours": self.sla_hours,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "escalated_at": self.escalated_at.isoformat() if self.escalated_at else None,
            "escalation_level": self.escalation_level,
            "who_has_ball": self.who_has_ball,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
