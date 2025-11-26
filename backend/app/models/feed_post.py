"""
Feed post model for social feed functionality
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class FeedVisibility(str, enum.Enum):
    """Visibility options for feed posts"""
    public = "public"
    friends = "friends"
    private = "private"


class FeedPost(Base):
    """Social feed posts linked to cases"""
    __tablename__ = "feed_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    content = Column(Text, nullable=False)
    visibility = Column(SQLEnum(FeedVisibility), default=FeedVisibility.public, nullable=False)

    # Location (duplicated from case for feed convenience)
    location_latitude = Column(String, nullable=True)
    location_longitude = Column(String, nullable=True)
    location_address = Column(Text, nullable=True)

    # Soft delete support
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("Case", backref="feed_post", uselist=False)
    user = relationship("User", backref="feed_posts")
    likes = relationship("FeedLike", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("FeedComment", back_populates="post", cascade="all, delete-orphan")
    shares = relationship("FeedShare", back_populates="post", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "case_id": str(self.case_id),
            "user_id": str(self.user_id),
            "content": self.content,
            "visibility": self.visibility.value,
            "location": {
                "latitude": self.location_latitude,
                "longitude": self.location_longitude,
                "address": self.location_address,
            } if self.location_latitude else None,
            "likes_count": len([like for like in self.likes if not like.is_deleted]) if self.likes else 0,
            "comments_count": len([comment for comment in self.comments if not comment.is_deleted]) if self.comments else 0,
            "shares_count": len([share for share in self.shares if not share.is_deleted]) if self.shares else 0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
