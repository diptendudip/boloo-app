"""
Case and CaseEvent models
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, ARRAY, Text, Enum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime, timedelta
import uuid
import enum

from app.database import Base


class CaseStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    MODERATION = "moderation"
    ROUTED = "routed"
    OFFICER_ACCEPTED = "officer_accepted"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    CLOSED = "closed"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    WITHDRAWN = "withdrawn"
    ESCALATED = "escalated"


class CasePriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class CaseKind(str, enum.Enum):
    GRIEVANCE = "grievance"
    COMMUNITY_STORY = "community_story"
    PERSONAL = "personal"


class TriageIntent(str, enum.Enum):
    GRIEVANCE = "grievance"
    COMMUNITY = "community"
    PERSONAL = "personal"
    UNCERTAIN = "uncertain"


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    transcript_text = Column(Text, nullable=True)
    audio_url = Column(String(1000), nullable=True)
    media_urls = Column(ARRAY(String), nullable=True)
    location_point = Column(Geometry("POINT", srid=4326), nullable=True)
    location_text = Column(String(500), nullable=True)
    location_hierarchy = Column(JSON, nullable=True)  # Detailed admin boundaries {village, panchayat, block, district, etc.}
    issue_type = Column(String(100), nullable=True)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=True, index=True)
    status = Column(String(50), default=CaseStatus.DRAFT.value, index=True)
    priority = Column(String(20), default=CasePriority.NORMAL.value)
    sla_due_at = Column(DateTime, nullable=True, index=True)
    is_public = Column(Boolean, default=False, index=True)
    case_metadata = Column("metadata", JSON, nullable=True)

    # 3-way triage fields
    # Use String type since CaseKind inherits from str and has proper values
    # This prevents SQLAlchemy from using the enum NAME instead of VALUE
    kind = Column(String(50), default=CaseKind.GRIEVANCE.value, nullable=True)
    triage_intent = Column(String(50), nullable=True)
    routing_confidence = Column(Float, default=0.0)
    raw_audio_url = Column(Text, nullable=True)
    raw_transcript = Column(Text, nullable=True)
    hindi_transcript = Column(Text, nullable=True)
    formal_summary = Column(Text, nullable=True)
    can_convert_to_grievance = Column(Boolean, default=False)
    reminder_at = Column(DateTime, nullable=True)

    # Reporter personal details (mandatory for grievances)
    reporter_name = Column(Text, nullable=True)
    reporter_phone = Column(Text, nullable=True)
    reporter_address = Column(Text, nullable=True)

    # Slot extraction fields
    when_started = Column(Text, nullable=True)
    scope_affected = Column(Text, nullable=True)
    prior_contact = Column(Text, nullable=True)
    rights_consent = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="cases")
    entity = relationship("Entity", back_populates="cases")
    events = relationship("CaseEvent", back_populates="case", cascade="all, delete-orphan", order_by="CaseEvent.created_at")
    conversations = relationship("Conversation", back_populates="case", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Case {self.id} - {self.status}>"

    def to_dict(self, mask_pii=False):
        """Convert model to dictionary"""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "summary": self.summary,
            "transcript_text": self.transcript_text,
            "audio_url": self.audio_url,
            "media_urls": self.media_urls,
            "location_text": self.location_text,
            "location_hierarchy": self.location_hierarchy,  # Administrative boundaries
            "issue_type": self.issue_type,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "status": self.status,
            "priority": self.priority,
            "sla_due_at": self.sla_due_at.isoformat() if self.sla_due_at else None,
            "is_public": self.is_public,
            "metadata": self.case_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Add location point if exists
        if self.location_point:
            # Extract lat/lng from WKB
            from geoalchemy2.shape import to_shape
            point = to_shape(self.location_point)
            data["location_lat"] = point.y
            data["location_lng"] = point.x
        else:
            data["location_lat"] = None
            data["location_lng"] = None

        # Mask PII for public views
        if mask_pii:
            data["user_id"] = None  # Hide user ID
            # Approximate location to 1km radius
            if data.get("location_lat") and data.get("location_lng"):
                data["location_lat"] = round(data["location_lat"], 2)
                data["location_lng"] = round(data["location_lng"], 2)
            # Keep location_hierarchy district/block level only (remove village/street)
            if self.location_hierarchy:
                masked_hierarchy = {
                    "block": self.location_hierarchy.get("block"),
                    "district": self.location_hierarchy.get("district"),
                    "state": self.location_hierarchy.get("state")
                }
                data["location_hierarchy"] = masked_hierarchy

        return data


class CaseEventType(str, enum.Enum):
    SUBMITTED = "submitted"
    ROUTED = "routed"
    ACCEPTED = "accepted"
    UPDATED = "updated"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"
    VERIFIED = "verified"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    ASSIGNED = "assigned"


class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actor_role = Column(String(50), nullable=True)
    note = Column(Text, nullable=True)
    event_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    case = relationship("Case", back_populates="events")
    actor = relationship("User")

    def __repr__(self):
        return f"<CaseEvent {self.event_type} for Case {self.case_id}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "case_id": str(self.case_id),
            "event_type": self.event_type,
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "actor_role": self.actor_role,
            "note": self.note,
            "metadata": self.event_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
