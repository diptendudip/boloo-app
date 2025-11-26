"""
Metric model for analytics
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid

from app.database import Base


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    value = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    date = Column(Date, default=date.today, index=True)

    # Relationships
    entity = relationship("Entity")
    user = relationship("User")

    def __repr__(self):
        return f"<Metric {self.metric_type} - {self.date}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "metric_type": self.metric_type,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "value": self.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "date": self.date.isoformat() if self.date else None,
        }
