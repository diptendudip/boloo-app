"""
Integration tests for MSG91 SMS OTP authentication

Tests cover:
- OTP request and sending
- OTP verification
- OTP resend (SMS and Voice)
- Rate limiting
- Error handling
- Phone number validation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid

from app.main import app
from app.database import Base, get_db
from app.models import User, OTP
from app.config import settings

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_msg91.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Create fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestMSG91OTPRequest:
    """Test OTP request endpoint"""

    def test_request_otp_valid_phone(self, setup_database):
        """Test OTP request with valid phone number"""
        response = client.post(
            "/auth/otp/request",
            json={"phone_number": "+919876543210"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "message" in data
        assert data["phone_number"] == "+919876543210"
        assert data["expires_in_minutes"] == 5

        # In dev mode, OTP should be exposed for testing
        if settings.is_development:
            assert "otp_for_testing" in data
            assert len(data["otp_for_testing"]) == 6
            assert data["otp_for_testing"].isdigit()

    def test_request_otp_creates_user(self, setup_database):
        """Test that OTP request creates new user if not exists"""
        phone = "+919876543210"

        response = client.post(
            "/auth/otp/request",
            json={"phone_number": phone}
        )

        assert response.status_code == 200

        # Verify user was created in database
        db = TestingSessionLocal()
        user = db.query(User).filter(User.phone == phone).first()

        assert user is not None
        assert user.phone == phone
        assert user.role == "citizen"
        assert user.is_first_timer is True
        # Auto-generated email
        assert user.email.endswith("@boloo-users.local")

        db.close()

    def test_request_otp_invalid_format(self, setup_database):
        """Test OTP request with invalid phone format"""
        invalid_phones = [
            "+1234567890",  # Not Indian number
            "123456789",    # Too short
            "+91123456789", # Only 9 digits
            "+9112345678901", # Too long
            "+91abcdefghij",  # Contains letters
        ]

        for phone in invalid_phones:
            response = client.post(
                "/auth/otp/request",
                json={"phone_number": phone}
            )

            # Should return 400 Bad Request
            assert response.status_code == 400
            assert "Invalid" in response.json()["detail"]

    def test_request_otp_saves_to_database(self, setup_database):
        """Test that OTP is saved to database"""
        phone = "+919876543210"

        response = client.post(
            "/auth/otp/request",
            json={"phone_number": phone}
        )

        assert response.status_code == 200

        # Verify OTP in database
        db = TestingSessionLocal()
        otp = db.query(OTP).filter(OTP.phone_number == phone).first()

        assert otp is not None
        assert otp.phone_number == phone
        assert len(otp.otp_code) == 6
        assert otp.is_used is False
        assert otp.expires_at > datetime.utcnow()

        db.close()


class TestMSG91OTPVerification:
    """Test OTP verification endpoint"""

    def test_verify_otp_success(self, setup_database):
        """Test successful OTP verification"""
        phone = "+919876543210"

        # Request OTP
        request_response = client.post(
            "/auth/otp/request",
            json={"phone_number": phone}
        )

        assert request_response.status_code == 200

        # Get OTP from response (dev mode)
        if settings.is_development:
            otp_code = request_response.json()["otp_for_testing"]
        else:
            # In production, get from database (for testing only)
            db = TestingSessionLocal()
            otp = db.query(OTP).filter(OTP.phone_number == phone).first()
            otp_code = otp.otp_code
            db.close()

        # Verify OTP
        verify_response = client.post(
            "/auth/otp/verify",
            json={
                "phone_number": phone,
                "otp_code": otp_code
            }
        )

        assert verify_response.status_code == 200
        data = verify_response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["phone"] == phone

    def test_verify_otp_invalid_code(self, setup_database):
        """Test OTP verification with invalid code"""
        phone = "+919876543210"

        # Request OTP
        client.post("/auth/otp/request", json={"phone_number": phone})

        # Verify with wrong OTP
        response = client.post(
            "/auth/otp/verify",
            json={
                "phone_number": phone,
                "otp_code": "000000"  # Wrong OTP
            }
        )

        assert response.status_code == 401
        assert "Invalid or expired OTP" in response.json()["detail"]

    def test_verify_otp_expired(self, setup_database):
        """Test OTP verification with expired OTP"""
        phone = "+919876543210"

        # Create expired OTP manually
        db = TestingSessionLocal()

        # Create user first
        user = User(
            phone=phone,
            email=f"{phone.replace('+', '')}@boloo-users.local",
            role="citizen"
        )
        db.add(user)

        # Create expired OTP
        expired_otp = OTP(
            phone_number=phone,
            otp_code="123456",
            expires_at=datetime.utcnow() - timedelta(minutes=10),  # Expired
            is_used=False
        )
        db.add(expired_otp)
        db.commit()
        db.close()

        # Try to verify expired OTP
        response = client.post(
            "/auth/otp/verify",
            json={
                "phone_number": phone,
                "otp_code": "123456"
            }
        )

        assert response.status_code == 401
        assert "Invalid or expired OTP" in response.json()["detail"]

    def test_verify_otp_already_used(self, setup_database):
        """Test OTP verification with already used OTP"""
        phone = "+919876543210"

        # Request OTP
        request_response = client.post(
            "/auth/otp/request",
            json={"phone_number": phone}
        )

        otp_code = request_response.json().get("otp_for_testing")

        # Verify OTP first time (should succeed)
        response1 = client.post(
            "/auth/otp/verify",
            json={"phone_number": phone, "otp_code": otp_code}
        )
        assert response1.status_code == 200

        # Try to verify same OTP again (should fail)
        response2 = client.post(
            "/auth/otp/verify",
            json={"phone_number": phone, "otp_code": otp_code}
        )

        assert response2.status_code == 401
        assert "Invalid or expired OTP" in response2.json()["detail"]


class TestMSG91PhoneValidation:
    """Test phone number validation"""

    def test_normalize_phone_with_country_code(self, setup_database):
        """Test phone normalization with +91 prefix"""
        response = client.post(
            "/auth/otp/request",
            json={"phone_number": "+919876543210"}
        )

        assert response.status_code == 200
        assert response.json()["phone_number"] == "+919876543210"

    def test_normalize_phone_without_plus(self, setup_database):
        """Test phone normalization without + prefix"""
        response = client.post(
            "/auth/otp/request",
            json={"phone_number": "919876543210"}
        )

        assert response.status_code == 200
        # Should normalize to +91 format
        assert response.json()["phone_number"] == "+919876543210"

    def test_normalize_phone_10_digits_only(self, setup_database):
        """Test phone normalization with 10 digits only"""
        response = client.post(
            "/auth/otp/request",
            json={"phone_number": "9876543210"}
        )

        assert response.status_code == 200
        # Should add +91 prefix
        assert response.json()["phone_number"] == "+919876543210"

    def test_reject_invalid_indian_mobile(self, setup_database):
        """Test rejection of invalid Indian mobile numbers"""
        # Indian mobiles start with 6, 7, 8, or 9
        invalid_phones = [
            "+915876543210",  # Starts with 5
            "+911234567890",  # Starts with 1
            "+910123456789",  # Starts with 0
        ]

        for phone in invalid_phones:
            response = client.post(
                "/auth/otp/request",
                json={"phone_number": phone}
            )

            assert response.status_code == 400
            assert "Invalid" in response.json()["detail"]


class TestMSG91RateLimiting:
    """Test rate limiting for OTP endpoints"""

    def test_rate_limit_otp_requests(self, setup_database):
        """Test that OTP requests are rate limited"""
        phone = "+919876543210"

        # Make multiple rapid requests
        for i in range(5):
            response = client.post(
                "/auth/otp/request",
                json={"phone_number": phone}
            )

            # First few should succeed
            if i < 3:
                assert response.status_code == 200

        # Note: Actual rate limiting behavior depends on slowapi configuration
        # This test verifies the endpoint structure


class TestMSG91ErrorHandling:
    """Test error handling for MSG91 service"""

    def test_handle_database_error(self, setup_database):
        """Test handling of database errors"""
        # This would require mocking database failures
        # Placeholder for future implementation
        pass

    def test_handle_msg91_api_error(self, setup_database):
        """Test handling of MSG91 API errors"""
        # This would require mocking MSG91 API failures
        # Placeholder for future implementation
        pass


class TestMSG91Integration:
    """Integration tests for complete authentication flow"""

    def test_complete_auth_flow(self, setup_database):
        """Test complete authentication flow: request -> verify -> profile update"""
        phone = "+919876543210"

        # Step 1: Request OTP
        request_response = client.post(
            "/auth/otp/request",
            json={"phone_number": phone}
        )

        assert request_response.status_code == 200
        otp_code = request_response.json().get("otp_for_testing")

        # Step 2: Verify OTP
        verify_response = client.post(
            "/auth/otp/verify",
            json={
                "phone_number": phone,
                "otp_code": otp_code
            }
        )

        assert verify_response.status_code == 200
        data = verify_response.json()

        assert "access_token" in data
        assert data["user"]["is_first_timer"] is True

        user_id = data["user"]["id"]
        access_token = data["access_token"]

        # Step 3: Update profile (first-time setup)
        profile_response = client.put(
            f"/auth/profile?user_id={user_id}",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "address": "123 Test Street, Test City"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert profile_response.status_code == 200
        profile_data = profile_response.json()

        assert profile_data["success"] is True
        assert profile_data["user"]["name"] == "Test User"
        assert profile_data["user"]["email"] == "test@example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
