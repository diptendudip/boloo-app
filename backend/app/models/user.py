"""
User model
"""

from sqlalchemy import Column, String, Boolean, Integer, ARRAY, DateTime, Enum, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    CITIZEN = "citizen"
    MODERATOR = "moderator"
    OFFICER = "officer"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)  # Full address for grievance reporting (legacy field)
    languages = Column(ARRAY(String), default=["en", "hi"])
    is_first_timer = Column(Boolean, default=True)
    reputation_score = Column(Integer, default=0)
    role = Column(String(50), default=UserRole.CITIZEN.value)
    is_active = Column(Boolean, default=True)

    # Hierarchical location fields (captured during signup)
    location_street = Column(String(255), nullable=True)  # Street/mohalla level address
    location_village = Column(String(255), nullable=True, index=True)  # Village/town
    location_panchayat = Column(String(255), nullable=True)  # Gram panchayat
    location_block = Column(String(255), nullable=True, index=True)  # Block/Tehsil
    location_subdivision = Column(String(255), nullable=True)  # Subdivision (if applicable)
    location_district = Column(String(255), nullable=True, index=True)  # District
    location_state = Column(String(255), nullable=True)  # State
    location_lat = Column(Float, nullable=True)  # GPS latitude
    location_lng = Column(Float, nullable=True)  # GPS longitude
    location_metadata = Column(JSON, nullable=True)  # Additional location data (source, confidence, etc.)
    location_formatted_address = Column(String(1000), nullable=True)  # Human-readable full address

    # AI Coach Training State (Phase 2D)
    training_reports_count = Column(Integer, default=0)
    training_completed = Column(Boolean, default=False)
    training_mode_enabled = Column(Boolean, default=True)

    # OTP Verification State (Production Mode)
    phone_verified = Column(Boolean, default=False, nullable=False)
    phone_verified_at = Column(DateTime, nullable=True)
    last_otp_verified_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cases = relationship("Case", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "phone": self.phone,
            "email": self.email,
            "name": self.name,
            "address": self.address,  # Legacy field
            "languages": self.languages,
            "is_first_timer": self.is_first_timer,
            "reputation_score": self.reputation_score,
            "role": self.role,
            "is_active": self.is_active,
            "training_reports_count": self.training_reports_count,
            "training_completed": self.training_completed,
            "training_mode_enabled": self.training_mode_enabled,
            # OTP Verification State
            "phone_verified": self.phone_verified,
            "phone_verified_at": self.phone_verified_at.isoformat() if self.phone_verified_at else None,
            "last_otp_verified_at": self.last_otp_verified_at.isoformat() if self.last_otp_verified_at else None,
            # Hierarchical location
            "location": {
                "street": self.location_street,
                "village": self.location_village,
                "panchayat": self.location_panchayat,
                "block": self.location_block,
                "subdivision": self.location_subdivision,
                "district": self.location_district,
                "state": self.location_state,
                "lat": self.location_lat,
                "lng": self.location_lng,
                "formatted_address": self.location_formatted_address,
                "metadata": self.location_metadata
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
