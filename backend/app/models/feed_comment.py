"""
Feed comment model for social feed functionality
"""

from sqlalchemy import Column, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class FeedComment(Base):
    """Comments on feed posts"""
    __tablename__ = "feed_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("feed_posts.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    comment_text = Column(Text, nullable=False)

    # Soft delete support
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    post = relationship("FeedPost", back_populates="comments")
    user = relationship("User", backref="feed_comments")

    def to_dict(self):
        return {
            "id": str(self.id),
            "post_id": str(self.post_id),
            "user_id": str(self.user_id),
            "comment_text": self.comment_text,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
