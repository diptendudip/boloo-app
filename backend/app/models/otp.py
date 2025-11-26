"""
OTP model for authentication
"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta
import uuid
import random

from app.database import Base


class OTP(Base):
    __tablename__ = "otps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=True, index=True)  # Made nullable - phone_number is alternative
    phone_number = Column(String(20), nullable=True, index=True)  # Support phone-based OTP
    otp_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        identifier = self.phone_number or self.email
        return f"<OTP {identifier} - {self.otp_code}>"

    def is_valid(self):
        """Check if OTP is still valid"""
        return not self.is_used and datetime.utcnow() < self.expires_at

    @staticmethod
    def generate_code():
        """Generate a 6-digit OTP code"""
        return str(random.randint(100000, 999999))

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "email": self.email,
            "phone_number": self.phone_number,
            "otp_code": self.otp_code,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_used": self.is_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
