"""
CommunityPost model - For community stories, songs, traditions
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime
import uuid

from app.database import Base


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    transcript_text = Column(Text, nullable=True)
    audio_url = Column(String(1000), nullable=True)
    media_urls = Column(ARRAY(String), nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    location_point = Column("location_point", Geometry("POINT", srid=4326), nullable=True)
    location_text = Column(String(500), nullable=True)
    status = Column(String(50), default="draft", index=True)  # draft/submitted/moderation/published/featured/rejected
    views_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    post_metadata = Column("metadata", Text, nullable=True)  # JSONB in database - use alias to avoid SQLAlchemy reserved name
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<CommunityPost {self.id} - {self.title}>"

    def to_dict(self, mask_pii=False):
        """Convert model to dictionary"""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id) if not mask_pii else None,
            "title": self.title,
            "summary": self.summary,
            "transcript_text": self.transcript_text,
            "audio_url": self.audio_url,
            "media_urls": self.media_urls,
            "tags": self.tags,
            "location_text": self.location_text,
            "status": self.status,
            "views_count": self.views_count,
            "shares_count": self.shares_count,
            "metadata": self.post_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Add location point if exists
        if self.location_point:
            from geoalchemy2.shape import to_shape
            point = to_shape(self.location_point)
            data["location_lat"] = point.y
            data["location_lng"] = point.x

            # Approximate location for privacy if needed
            if mask_pii:
                data["location_lat"] = round(point.y, 2)
                data["location_lng"] = round(point.x, 2)
        else:
            data["location_lat"] = None
            data["location_lng"] = None

        return data
