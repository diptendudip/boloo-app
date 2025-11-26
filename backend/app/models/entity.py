"""
Entity model (Government offices: Districts, Blocks, GPs, Departments)
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class EntityType(str, enum.Enum):
    DISTRICT = "district"
    BLOCK = "block"
    GP = "gp"
    DEPT = "dept"


class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)
    escalation_parent_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=True)
    coverage_geojson = Column(JSON, nullable=True)  # GeoJSON polygon
    entity_metadata = Column("metadata", JSON, nullable=True)  # Using name parameter to avoid conflict
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    escalation_parent = relationship("Entity", remote_side=[id], backref="children")
    cases = relationship("Case", back_populates="entity")

    def __repr__(self):
        return f"<Entity {self.name} ({self.type})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.type,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "escalation_parent_id": str(self.escalation_parent_id) if self.escalation_parent_id else None,
            "coverage_geojson": self.coverage_geojson,
            "metadata": self.entity_metadata,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
