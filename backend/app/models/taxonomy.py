"""
Taxonomy model (Issue types, Topics, Languages)
"""

from sqlalchemy import Column, String, Boolean, DateTime, JSON, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.database import Base


class TaxonomyType(str, enum.Enum):
    ISSUE = "issue"
    TOPIC = "topic"
    LANGUAGE = "language"


class Taxonomy(Base):
    __tablename__ = "taxonomies"
    __table_args__ = (UniqueConstraint("type", "key", name="unique_taxonomy"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)
    label_en = Column(String(255), nullable=True)
    label_hi = Column(String(255), nullable=True)
    parent_key = Column(String(100), nullable=True)
    taxonomy_metadata = Column("metadata", JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Taxonomy {self.type}:{self.key}>"

    def to_dict(self, language="en"):
        """Convert model to dictionary"""
        label = self.label_en if language == "en" else self.label_hi
        return {
            "id": str(self.id),
            "type": self.type,
            "key": self.key,
            "label": label or self.label_en,  # Fallback to English
            "label_en": self.label_en,
            "label_hi": self.label_hi,
            "parent_key": self.parent_key,
            "metadata": self.taxonomy_metadata,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
