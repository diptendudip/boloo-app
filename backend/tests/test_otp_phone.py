"""
Test OTP Phone Number Integration

Tests that OTP model correctly supports phone_number column
and integrates with MSG91 service.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.otp import OTP
from app.services.msg91_service import MSG91Service, MSG91Error


class TestOTPPhoneNumberColumn:
    """Test OTP model phone_number column"""

    def test_otp_with_phone_number(self, db: Session):
        """Test creating OTP with phone_number"""
        phone = "+919876543210"
        otp_code = OTP.generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        otp = OTP(
            phone_number=phone,
            otp_code=otp_code,
            expires_at=expires_at,
            is_used=False
        )
        db.add(otp)
        db.commit()
        db.refresh(otp)

        assert otp.phone_number == phone
        assert otp.otp_code == otp_code
        assert otp.email is None
        assert otp.is_used is False

    def test_otp_with_email(self, db: Session):
        """Test creating OTP with email (backward compatibility)"""
        email = "test@example.com"
        otp_code = OTP.generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        otp = OTP(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at,
            is_used=False
        )
        db.add(otp)
        db.commit()
        db.refresh(otp)

        assert otp.email == email
        assert otp.otp_code == otp_code
        assert otp.phone_number is None
        assert otp.is_used is False

    def test_otp_with_both_phone_and_email(self, db: Session):
        """Test OTP can have both phone and email"""
        phone = "+919876543210"
        email = "test@example.com"
        otp_code = OTP.generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        otp = OTP(
            phone_number=phone,
            email=email,
            otp_code=otp_code,
            expires_at=expires_at,
            is_used=False
        )
        db.add(otp)
        db.commit()
        db.refresh(otp)

        assert otp.phone_number == phone
        assert otp.email == email
        assert otp.otp_code == otp_code

    def test_otp_repr_with_phone(self, db: Session):
        """Test OTP __repr__ shows phone_number"""
        phone = "+919876543210"
        otp = OTP(
            phone_number=phone,
            otp_code="123456",
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )

        assert phone in repr(otp)
        assert "123456" in repr(otp)

    def test_otp_repr_with_email(self, db: Session):
        """Test OTP __repr__ shows email when no phone"""
        email = "test@example.com"
        otp = OTP(
            email=email,
            otp_code="123456",
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )

        assert email in repr(otp)
        assert "123456" in repr(otp)

    def test_otp_to_dict_includes_phone(self, db: Session):
        """Test to_dict includes phone_number"""
        phone = "+919876543210"
        otp = OTP(
            phone_number=phone,
            otp_code="123456",
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )

        otp_dict = otp.to_dict()
        assert otp_dict["phone_number"] == phone
        assert otp_dict["email"] is None
        assert otp_dict["otp_code"] == "123456"

    def test_otp_query_by_phone_number(self, db: Session):
        """Test querying OTP by phone_number"""
        phone = "+919876543210"
        otp_code = "123456"

        otp = OTP(
            phone_number=phone,
            otp_code=otp_code,
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            is_used=False
        )
        db.add(otp)
        db.commit()

        # Query by phone_number
        found_otp = db.query(OTP).filter(
            OTP.phone_number == phone,
            OTP.otp_code == otp_code,
            OTP.is_used == False
        ).first()

        assert found_otp is not None
        assert found_otp.phone_number == phone
        assert found_otp.otp_code == otp_code


class TestMSG91ServiceIntegration:
    """Test MSG91 service with phone_number column"""

    @pytest.mark.asyncio
    async def test_send_otp_creates_phone_record(self, db: Session):
        """Test that send_otp creates OTP with phone_number"""
        service = MSG91Service()
        phone = "+919876543210"

        # Send OTP (will use dev mode)
        result = await service.send_otp(phone, db)

        assert result["type"] == "success"
        assert phone in result["message"]

        # Verify OTP record in database
        otp_record = db.query(OTP).filter(
            OTP.phone_number == phone
        ).order_by(OTP.created_at.desc()).first()

        assert otp_record is not None
        assert otp_record.phone_number == phone
        assert otp_record.email is None
        assert len(otp_record.otp_code) == 6
        assert otp_record.is_used is False

    @pytest.mark.asyncio
    async def test_verify_otp_with_phone_number(self, db: Session):
        """Test OTP verification with phone_number"""
        service = MSG91Service()
        phone = "+919876543210"

        # Send OTP
        send_result = await service.send_otp(phone, db)

        # Get OTP code from database
        otp_record = db.query(OTP).filter(
            OTP.phone_number == phone
        ).order_by(OTP.created_at.desc()).first()

        assert otp_record is not None
        otp_code = otp_record.otp_code

        # Verify OTP
        verify_result = await service.verify_otp(phone, otp_code, db)

        assert verify_result["type"] == "success"
        assert "verified" in verify_result["message"].lower()

        # Check OTP is marked as used
        db.refresh(otp_record)
        assert otp_record.is_used is True

    @pytest.mark.asyncio
    async def test_resend_otp_creates_new_phone_record(self, db: Session):
        """Test resend OTP creates new record with phone_number"""
        service = MSG91Service()
        phone = "+919876543210"

        # Send initial OTP
        await service.send_otp(phone, db)

        # Wait a bit to avoid rate limit (in test we can mock this)
        import asyncio
        await asyncio.sleep(1.1)

        # Resend OTP
        resend_result = await service.resend_otp(phone, db, retry_type="text")

        assert resend_result["type"] == "success"

        # Verify multiple OTP records exist for same phone
        otp_records = db.query(OTP).filter(
            OTP.phone_number == phone
        ).order_by(OTP.created_at.desc()).all()

        assert len(otp_records) >= 2
        assert all(record.phone_number == phone for record in otp_records)

    @pytest.mark.asyncio
    async def test_voice_otp_creates_phone_record(self, db: Session):
        """Test voice OTP creates record with phone_number"""
        service = MSG91Service()
        phone = "+919876543210"

        # Send initial OTP first
        await service.send_otp(phone, db)

        # Wait to avoid rate limit
        import asyncio
        await asyncio.sleep(1.1)

        # Resend via voice
        voice_result = await service.resend_otp(phone, db, retry_type="voice")

        assert voice_result["type"] == "success"
        assert "voice" in voice_result["message"].lower()

        # Verify OTP record with phone_number
        otp_record = db.query(OTP).filter(
            OTP.phone_number == phone
        ).order_by(OTP.created_at.desc()).first()

        assert otp_record is not None
        assert otp_record.phone_number == phone


class TestOTPValidation:
    """Test OTP validation with phone_number"""

    def test_is_valid_with_phone_number(self, db: Session):
        """Test is_valid method works with phone_number"""
        phone = "+919876543210"

        # Valid OTP
        valid_otp = OTP(
            phone_number=phone,
            otp_code="123456",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            is_used=False
        )
        assert valid_otp.is_valid() is True

        # Expired OTP
        expired_otp = OTP(
            phone_number=phone,
            otp_code="123456",
            expires_at=datetime.utcnow() - timedelta(minutes=5),
            is_used=False
        )
        assert expired_otp.is_valid() is False

        # Used OTP
        used_otp = OTP(
            phone_number=phone,
            otp_code="123456",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            is_used=True
        )
        assert used_otp.is_valid() is False

    def test_generate_code_format(self):
        """Test OTP code generation"""
        code = OTP.generate_code()

        assert len(code) == 6
        assert code.isdigit()
        assert 100000 <= int(code) <= 999999


# Fixtures
@pytest.fixture
def db():
    """Database session fixture"""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
        db.rollback()
    finally:
        db.close()
